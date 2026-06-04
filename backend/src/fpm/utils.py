import asyncio
import base64
from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import urlparse, urlunparse

import httpx
from extract_favicon import generate_favicon
from extract_favicon.config import Favicon
from extract_favicon.main_async import get_best_favicon
from loguru import logger
from PIL import Image
from reachable.client import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import settings
from src.ferron.constants import DEFAULT_HTTP_PORT
from src.ferron.models import GlobalConfig, VirtualHost
from src.fpm.constants import (
    _LOCALHOST_ALIASES,
    CONTENT_ONLY_STRATEGY,
    FAVICON_WAIT_INTERVAL,
    FAVICON_WAIT_TIMEOUT,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def build_target_url(virtual_host_name: str) -> str:
    return f"https://{virtual_host_name}"


def _force_http(url_str: str) -> str:
    parsed = urlparse(url_str)
    if parsed.scheme == "https":
        parsed = parsed._replace(scheme="http")
    return urlunparse(parsed)


def _replace_localhost(url_str: str) -> str:
    parsed = urlparse(url_str)
    hostname = parsed.hostname or ""

    if hostname in _LOCALHOST_ALIASES:
        if parsed.port is not None:
            new_netloc = f"host.docker.internal:{parsed.port}"
        else:
            new_netloc = "host.docker.internal"
        parsed = parsed._replace(scheme="http", netloc=new_netloc)

    return urlunparse(parsed)


async def resolve_local_favicon_url(session: AsyncSession, virtual_host_id: int) -> str | None:
    vh_result = await session.exec(
        select(VirtualHost)
        .where(VirtualHost.id == virtual_host_id)
        .options(
            selectinload(VirtualHost.reverse_proxy_config),
            selectinload(VirtualHost.static_file_config),
            selectinload(VirtualHost.load_balancer_config),
            # eagerly load backend URLs because we need the first one for the local target URL
            selectinload(VirtualHost.load_balancer_backends),
        )
    )
    vh = vh_result.scalar_one_or_none()

    if vh is None:
        logger.warning("resolve_local_favicon_url: VirtualHost id={} not found", virtual_host_id)
        return None

    if vh.reverse_proxy_config is not None:
        url = _force_http(_replace_localhost(str(vh.reverse_proxy_config.backend_url)))
        logger.debug("resolve_local_favicon_url: vh='{}' is reverse-proxy -> local_url={}", vh.virtual_host_name, url)
        return url

    # load balancer config means we use the first backend URL which is sorted by id
    if vh.load_balancer_config is not None and vh.load_balancer_backends:
        sorted_backends = sorted(vh.load_balancer_backends, key=lambda b: b.id)
        url = _force_http(_replace_localhost(str(sorted_backends[0].backend_url)))
        logger.debug("resolve_local_favicon_url: vh='{}' is load-balancer -> local_url={}", vh.virtual_host_name, url)
        return url

    # static file config means we use the local Ferron container's URL so we don't go over the internet
    if vh.static_file_config is not None:
        global_config = await session.get(GlobalConfig, 1)
        http_port = global_config.default_http_port if global_config else DEFAULT_HTTP_PORT
        url = f"http://{settings.ferron_container_name}:{http_port}/"
        logger.info(
            "resolve_local_favicon_url: vh='{}' is static-file -> local_url={} (port={})",
            vh.virtual_host_name,
            url,
            http_port,
        )
        return url

    logger.warning("resolve_local_favicon_url: vh_id={} has no recognized config, returning None", virtual_host_id)
    return None


async def wait_for_url(url: str, headers: dict[str, str] | None = None) -> bool:
    start = asyncio.get_event_loop().time()

    logger.debug("wait_for_url: starting wait for {} (headers={})", url, headers)

    async with httpx.AsyncClient(timeout=5.0) as client:
        while asyncio.get_event_loop().time() - start < FAVICON_WAIT_TIMEOUT:
            try:
                resp = await client.get(url, headers=headers or {})
                if resp.status_code < 400:
                    logger.debug("wait_for_url: {} responded with status={}, reachable", url, resp.status_code)
                    return True
            except httpx.ConnectError:
                logger.trace("wait_for_url: ConnectError for {}", url)
            except httpx.ConnectTimeout:
                logger.trace("wait_for_url: ConnectTimeout for {}", url)
            except httpx.ReadTimeout:
                logger.trace("wait_for_url: ReadTimeout for {}", url)

            await asyncio.sleep(FAVICON_WAIT_INTERVAL)

    logger.warning("wait_for_url: timed out for {} after {}s", url, FAVICON_WAIT_TIMEOUT)
    return False


def _mime_type_for_format(image_format: str | None) -> str:
    normalized_format = (image_format or "png").lower()

    return {
        "svg": "image/svg+xml",
        "ico": "image/x-icon",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
    }.get(normalized_format, "image/png")


def _pillow_format(image_format: str | None) -> str:
    normalized_format = (image_format or "png").lower()

    return {
        "ico": "ICO",
        "jpg": "JPEG",
        "jpeg": "JPEG",
        "png": "PNG",
        "gif": "GIF",
        "webp": "WEBP",
        "bmp": "BMP",
    }.get(normalized_format, "PNG")


def encode_favicon_image(favicon: Favicon) -> str:
    image = favicon.image
    image_format = favicon.format
    mime_type = _mime_type_for_format(image_format)

    if isinstance(image, bytes):  # only for svg, which is returned as bytes by extract_favicon
        encoded = base64.b64encode(image).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    if isinstance(image, Image.Image):  # for raster formats, which are returned as PIL Image objects by extract_favicon
        buffer = BytesIO()
        save_format = _pillow_format(image_format)
        image.save(buffer, format=save_format)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    raise ValueError("Unsupported favicon image payload")


async def fetch_favicon_payload(virtual_host_name: str, local_url: str | None = None) -> tuple[str, bool]:
    target_url = local_url if local_url else build_target_url(virtual_host_name)
    logger.info("fetch_favicon_payload: vh='{}', target_url={}, local_url={}", virtual_host_name, target_url, local_url)

    custom_client: AsyncClient | None = None
    host_headers: dict[str, str] | None = None

    if local_url is not None:
        parsed = urlparse(local_url)
        if parsed.hostname == settings.ferron_container_name:  # only true for static configs as
            # local_url is http://{ferron_container_name}
            host_headers = {"Host": virtual_host_name}  # this is how ferron will know which static site to serve
            # this header is set in a browser as well
            logger.info(
                "fetch_favicon_payload: creating custom AsyncClient with Host='{}' for {}",
                virtual_host_name,
                target_url,
            )
            custom_client = AsyncClient(headers=host_headers)
            await custom_client.open()

    try:
        if custom_client is not None:  # static configs
            await wait_for_url(target_url, headers=host_headers)
        else:  # others like reverse proxy configs and load balancer configs
            await wait_for_url(target_url)

        favicon = await get_best_favicon(
            target_url,
            strategy=CONTENT_ONLY_STRATEGY,
            include_fallbacks=True,
            client=custom_client,  # default for client is None so its not a problem if custom_client is None when
            # passed
        )
        logger.info(
            "get_best_favicon for '{}': favicon={}, format={}, size={}x{}",
            virtual_host_name,
            favicon is not None and favicon.image is not None,
            favicon.format if favicon else "N/A",
            favicon.width if favicon else 0,
            favicon.height if favicon else 0,
        )
    finally:
        if custom_client is not None:
            logger.debug("fetch_favicon_payload: closing custom AsyncClient for '{}'", virtual_host_name)
            await custom_client.close()

    is_placeholder = favicon is None or favicon.image is None

    if is_placeholder:
        logger.warning("fetch_favicon_payload: no favicon found for '{}', generating placeholder", virtual_host_name)
        favicon = generate_favicon(build_target_url(virtual_host_name))

    encoded = encode_favicon_image(favicon)
    logger.debug(
        "fetch_favicon_payload: final data_url length={}, is_placeholder={} for '{}'",
        len(encoded),
        is_placeholder,
        virtual_host_name,
    )
    return encoded, is_placeholder
