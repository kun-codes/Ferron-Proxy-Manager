import base64
from datetime import datetime, timezone
from io import BytesIO

from extract_favicon import generate_favicon
from extract_favicon.config import Favicon
from extract_favicon.main_async import get_best_favicon
from PIL import Image

from src.fpm.constants import FAVICON_STRATEGY


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def build_target_url(virtual_host_name: str) -> str:
    return f"https://{virtual_host_name}"


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


async def fetch_favicon_payload(virtual_host_name: str) -> tuple[str, bool]:
    target_url = build_target_url(virtual_host_name)
    favicon = await get_best_favicon(target_url, strategy=FAVICON_STRATEGY, include_fallbacks=True)
    is_placeholder = favicon is None or favicon.image is None

    if is_placeholder:
        favicon = generate_favicon(target_url)

    return encode_favicon_image(favicon), is_placeholder
