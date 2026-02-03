from pydantic import BaseModel, ConfigDict, Field

from src.ferron.constants import (
    DEFAULT_CACHE_ENABLED,
    DEFAULT_CACHE_MAX_AGE,
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_COMPRESSED,
    DEFAULT_DIRECTORY_LISTING,
    DEFAULT_HTTP_PORT,
    DEFAULT_HTTPS_PORT,
    DEFAULT_IS_H1_PROTOCOL_ENABLED,
    DEFAULT_IS_H2_PROTOCOL_ENABLED,
    DEFAULT_IS_H3_PROTOCOL_ENABLED,
    DEFAULT_LB_HEALTH_CHECK,
    DEFAULT_LB_HEALTH_CHECK_MAX_FAILS,
    DEFAULT_LB_HEALTH_CHECK_WINDOW,
    DEFAULT_PRECOMPRESSED,
    DEFAULT_PRESERVE_HOST_HEADER,
    DEFAULT_TIMEOUT,
    DEFAULT_USE_SPA,
    DEFAULT_USE_UNIX_SOCKET,
)


class TemplateConfig(BaseModel):
    pass


class GlobalTemplateConfig(TemplateConfig):
    model_config = ConfigDict(from_attributes=True)

    default_http_port: int = Field(default=DEFAULT_HTTP_PORT, ge=1, le=65535)
    default_https_port: int = Field(default=DEFAULT_HTTPS_PORT, ge=1, le=65535)
    is_h1_protocol_enabled: bool = DEFAULT_IS_H1_PROTOCOL_ENABLED
    is_h2_protocol_enabled: bool = DEFAULT_IS_H2_PROTOCOL_ENABLED
    is_h3_protocol_enabled: bool = DEFAULT_IS_H3_PROTOCOL_ENABLED
    timeout: int = Field(default=DEFAULT_TIMEOUT, ge=0)
    cache_max_entries: int = DEFAULT_CACHE_MAX_ENTRIES


class BaseVirtualHost(TemplateConfig):
    model_config = ConfigDict(from_attributes=True)

    virtual_host_name: str


class Cache(TemplateConfig):
    cache: bool = DEFAULT_CACHE_ENABLED
    cache_max_age: int = DEFAULT_CACHE_MAX_AGE


class CommonReverseProxyConfig(BaseVirtualHost, Cache):
    preserve_host_header: bool = DEFAULT_PRESERVE_HOST_HEADER


class CreateReverseProxyConfig(CommonReverseProxyConfig):
    backend_url: str
    use_unix_socket: bool = DEFAULT_USE_UNIX_SOCKET
    unix_socket_path: str | None = None


class UpdateReverseProxyConfig(CreateReverseProxyConfig):
    id: int


class CreateLoadBalancerConfig(CommonReverseProxyConfig):
    backend_urls: list[str]
    lb_health_check: bool = DEFAULT_LB_HEALTH_CHECK
    lb_health_check_max_fails: int = DEFAULT_LB_HEALTH_CHECK_MAX_FAILS
    lb_health_check_window: int = DEFAULT_LB_HEALTH_CHECK_WINDOW


class UpdateLoadBalancerConfig(CreateLoadBalancerConfig):
    id: int


class CreateStaticFileConfig(BaseVirtualHost, Cache):
    static_files_dir: str
    use_spa: bool = DEFAULT_USE_SPA
    compressed: bool = DEFAULT_COMPRESSED
    directory_listing: bool = DEFAULT_DIRECTORY_LISTING
    precompressed: bool = DEFAULT_PRECOMPRESSED


class UpdateStaticFileConfig(CreateStaticFileConfig):
    id: int
