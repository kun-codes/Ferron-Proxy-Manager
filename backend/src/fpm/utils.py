import asyncio
import base64
from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import urlparse, urlunparse

import httpx
from extract_favicon import generate_favicon
from extract_favicon.config import Favicon
from extract_favicon.main_async import get_best_favicon
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from src.ferron.models import VirtualHost
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
        return None

    if vh.reverse_proxy_config is not None:
        return _force_http(_replace_localhost(str(vh.reverse_proxy_config.backend_url)))

    # load balancer config means we use the first backend URL which is sorted by id
    if vh.load_balancer_config is not None and vh.load_balancer_backends:
        sorted_backends = sorted(vh.load_balancer_backends, key=lambda b: b.id)
        return _force_http(_replace_localhost(str(sorted_backends[0].backend_url)))

    # static file config means fall back to internet url
    return None


async def wait_for_url(url: str) -> bool:
    start = asyncio.get_event_loop().time()

    async with httpx.AsyncClient(timeout=5.0) as client:
        while asyncio.get_event_loop().time() - start < FAVICON_WAIT_TIMEOUT:
            try:
                resp = await client.get(url)
                if resp.status_code < 400:
                    return True
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
                pass

            await asyncio.sleep(FAVICON_WAIT_INTERVAL)

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

    await wait_for_url(target_url)

    favicon = await get_best_favicon(target_url, strategy=CONTENT_ONLY_STRATEGY, include_fallbacks=True)
    is_placeholder = favicon is None or favicon.image is None

    if is_placeholder:
        favicon = generate_favicon(build_target_url(virtual_host_name))

    return encode_favicon_image(favicon), is_placeholder
