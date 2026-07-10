import asyncio
import base64
import socket
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from io import BytesIO
from typing import Any
from urllib.parse import urlparse, urlunparse

import aiodocker
import httpx
from extract_favicon import generate_favicon
from extract_favicon.config import Favicon
from extract_favicon.main_async import get_best_favicon
from PIL import Image
from reachable.client import AsyncClient
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

# this lock is required to serialise static config favicon fetches because refresh_all_stale_favicons() of
# service.py runs favicon fetches concurrently. Each static config favicon fetch patches the global
# `socket.getaddrinfo`, so if run concurrently they would overwrite each other's patches mid fetch
#
# we can maintain a dict of hostname -> IP overrides which would eliminate this lock. Just store the original
# `socket.getaddrinfo` at start of the script. If a static favicon is to be fetched then insert the hostname -> IP
# pair in the dict and do the favicon fetching. Once it is done, remove the entry from the dict. If dict is now empty
# then restore it to the original `socket.getaddrinfo`. This way multiple overrides can exist at once in that dict
# I am not doing it at this time because it is a lot of work to maintain in this codebase
_static_favicon_lock = asyncio.Lock()


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


async def _get_ferron_container_ip() -> str:
    docker = aiodocker.Docker()
    try:
        container = await docker.containers.get(settings.ferron_container_name)
        data = await container.show()
        for net_config in data["NetworkSettings"]["Networks"].values():
            ip = net_config.get("IPAddress")
            if ip:
                return ip
        raise RuntimeError(f"No IP address found for container '{settings.ferron_container_name}'")
    finally:
        await docker.close()


@contextmanager
def _dns_override(hostname: str, ip: str) -> Iterator[None]:
    """
    This function will temporarily override DNS resolution for a specific hostname to a specific IP address
    It will restore the original DNS resolution after the context is exited
    """
    original_getaddrinfo = socket.getaddrinfo

    def patched_getaddrinfo(host: str | bytes | None, *args: Any, **kwargs: Any) -> list[tuple[Any, ...]]:
        if host == hostname:
            return original_getaddrinfo(ip, *args, **kwargs)
        return original_getaddrinfo(host, *args, **kwargs)

    socket.getaddrinfo = patched_getaddrinfo
    try:
        yield
    finally:
        socket.getaddrinfo = original_getaddrinfo


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

    local_url: str | None = None

    if vh.reverse_proxy_config is not None:
        local_url = _force_http(_replace_localhost(str(vh.reverse_proxy_config.backend_url)))

    # load balancer config means we use the first backend URL which is sorted by id
    elif vh.load_balancer_config is not None and vh.load_balancer_backends:
        sorted_backends = sorted(vh.load_balancer_backends, key=lambda b: b.id)
        local_url = _force_http(_replace_localhost(str(sorted_backends[0].backend_url)))

    # static file config means we use the local Ferron container's URL so we don't go over the internet
    # URL hostname is the virtual host name so SNI matches ferron's tls certificate
    elif vh.static_file_config is not None:
        global_config = await session.get(GlobalConfig, 1)
        https_port = global_config.default_https_port if global_config else DEFAULT_HTTPS_PORT
        local_url = f"https://{vh.virtual_host_name}:{https_port}/"

    return local_url


async def wait_for_url(url: str, headers: dict[str, str] | None = None) -> bool:
    start = asyncio.get_event_loop().time()

    async with httpx.AsyncClient(timeout=5.0) as client:
        while asyncio.get_event_loop().time() - start < FAVICON_WAIT_TIMEOUT:
            try:
                resp = await client.get(url, headers=headers or {})
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

    # static configs use https://{virtual_host_name}/ as local_url, so the hostname matches the virtual host name
    is_static = False
    if local_url is not None:
        parsed = urlparse(local_url)
        if parsed.hostname == virtual_host_name:
            is_static = True

    if is_static:
        await wait_for_url(target_url)

        # actual fetch uses DNS override to resolve the virtual host to ferron's container IP,
        # keeping the connection within docker networking
        async with _static_favicon_lock:
            ferron_ip = await _get_ferron_container_ip()

            with _dns_override(virtual_host_name, ferron_ip):
                host_headers = {"Host": virtual_host_name}
                custom_client = AsyncClient(headers=host_headers)
                custom_client.transport = httpx.AsyncHTTPTransport(retries=2, verify=False, http2=True)
                await custom_client.open()

                try:
                    favicon = await get_best_favicon(
                        target_url,
                        strategy=CONTENT_ONLY_STRATEGY,
                        include_fallbacks=True,
                        client=custom_client,
                    )
                finally:
                    await custom_client.close()
    else:
        await wait_for_url(target_url)

        favicon = await get_best_favicon(
            target_url,
            strategy=CONTENT_ONLY_STRATEGY,
            include_fallbacks=True,
        )

    is_placeholder = favicon is None or favicon.image is None

    if is_placeholder:
        favicon = generate_favicon(build_target_url(virtual_host_name))

    return encode_favicon_image(favicon), is_placeholder
