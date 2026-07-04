import asyncio
import base64
import warnings
from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import urlparse, urlunparse

import httpx
from extract_favicon import generate_favicon
from extract_favicon.config import Favicon
from extract_favicon.main import from_html
from extract_favicon.main_async import get_best_favicon
from loguru import logger
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from src.config import settings
from src.ferron.constants import DEFAULT_HTTPS_PORT
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
        https_port = global_config.default_https_port if global_config else DEFAULT_HTTPS_PORT
        url = f"https://{settings.ferron_container_name}:{https_port}/"
        logger.info(
            "resolve_local_favicon_url: vh='{}' is static-file -> local_url={} (port={})",
            vh.virtual_host_name,
            url,
            https_port,
        )
        return url

    logger.warning("resolve_local_favicon_url: vh_id={} has no recognized config, returning None", virtual_host_id)
    return None


async def wait_for_url(url: str, headers: dict[str, str] | None = None, verify: bool = True) -> bool:
    start = asyncio.get_event_loop().time()

    logger.debug("wait_for_url: starting wait for {} (headers={}, verify={})", url, headers, verify)

    with warnings.catch_warnings():
        if verify is False:
            warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        async with httpx.AsyncClient(timeout=5.0, verify=verify) as client:
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


async def _fetch_static_favicon(virtual_host_name: str, target_url: str) -> tuple[str, bool]:
    """
    this implements the equivalent of curl's --resolve flag:
    curl -vk https://st.website.com/ --resolve st.website.com:443:127.0.0.1
    """
    headers = {"Host": virtual_host_name}
    extensions = {"sni_hostname": virtual_host_name}

    logger.info(f"_fetch_static_favicon: vh='{virtual_host_name}', target_url={target_url}")

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.get(target_url, headers=headers, extensions=extensions)
        html_content = response.text

    root_url = f"https://{virtual_host_name}"
    favicons = from_html(html_content, root_url=root_url, include_fallbacks=True)

    if favicons:
        favicon = favicons.pop()
        is_placeholder = False
    else:
        logger.warning(f"_fetch_static_favicon: no favicon found for '{virtual_host_name}', generating placeholder")
        favicon = generate_favicon(root_url)
        is_placeholder = True

    encoded = encode_favicon_image(favicon)

    logger.debug(
        f"_fetch_static_favicon: final data_url length={len(encoded)}, "
        f"is_placeholder={is_placeholder} for '{virtual_host_name}'"
    )

    return encoded, is_placeholder


async def fetch_favicon_payload(virtual_host_name: str, local_url: str | None = None) -> tuple[str, bool]:
    target_url = local_url if local_url else build_target_url(virtual_host_name)
    logger.info(f"fetch_favicon_payload: vh='{virtual_host_name}', target_url={target_url}, local_url={local_url}")

    if local_url is not None:
        parsed = urlparse(local_url)
        if parsed.hostname == settings.ferron_container_name:
            # now we know that it is a static config
            https_port = parsed.port or 443
            target_url = f"https://127.0.0.1:{https_port}/"
            await wait_for_url(target_url, headers={"Host": virtual_host_name}, verify=False)
            return await _fetch_static_favicon(virtual_host_name, target_url)

    await wait_for_url(target_url)

    favicon = await get_best_favicon(
        target_url,
        strategy=CONTENT_ONLY_STRATEGY,
        include_fallbacks=True,
    )
    logger.info(
        f"get_best_favicon for '{virtual_host_name}': "
        f"favicon={favicon is not None and favicon.image is not None}, "
        f"format={favicon.format if favicon else 'N/A'}, "
        f"size={favicon.width if favicon else 0}x{favicon.height if favicon else 0}"
    )

    is_placeholder = favicon is None or favicon.image is None

    if is_placeholder:
        logger.warning(f"fetch_favicon_payload: no favicon found for '{virtual_host_name}', generating placeholder")
        favicon = generate_favicon(build_target_url(virtual_host_name))

    encoded = encode_favicon_image(favicon)
    logger.debug(
        f"fetch_favicon_payload: final data_url length={len(encoded)}, "
        f"is_placeholder={is_placeholder} for '{virtual_host_name}'"
    )
    return encoded, is_placeholder
