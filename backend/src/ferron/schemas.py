from pydantic import BaseModel, Field

from src.ferron.constants import (
    DEFAULT_HTTP_PORT,
    DEFAULT_HTTPS_PORT,
    DEFAULT_IS_H1_PROTOCOL_ENABLED,
    DEFAULT_IS_H2_PROTOCOL_ENABLED,
    DEFAULT_IS_H3_PROTOCOL_ENABLED,
    DEFAULT_TIMEOUT,
    DEFAULT_CACHE_MAX_ENTRIES,
)

class TemplateConfig(BaseModel):
    pass

class GlobalTemplateConfig(TemplateConfig):
    default_http_port: int = Field(default=DEFAULT_HTTP_PORT, ge=1, le=65535)
    default_https_port: int = Field(default=DEFAULT_HTTPS_PORT, ge=1, le=65535)
    is_h1_protocol_enabled: bool = DEFAULT_IS_H1_PROTOCOL_ENABLED
    is_h2_protocol_enabled: bool = DEFAULT_IS_H2_PROTOCOL_ENABLED
    is_h3_protocol_enabled: bool = DEFAULT_IS_H3_PROTOCOL_ENABLED
    timeout: int = DEFAULT_TIMEOUT
    cache_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES
