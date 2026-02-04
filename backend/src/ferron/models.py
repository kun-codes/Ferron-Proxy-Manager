from typing import List, Optional

from sqlalchemy import Column, ForeignKey, Integer
from sqlmodel import Field, Relationship, SQLModel

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


# TODO: limit this table to only 1 row
class GlobalConfig(SQLModel, table=True):
    __tablename__ = "ferron_global_config"

    id: int = Field(default=None, primary_key=True)
    default_http_port: int = Field(default=DEFAULT_HTTP_PORT)
    default_https_port: int = Field(default=DEFAULT_HTTPS_PORT)
    is_h1_protocol_enabled: bool = Field(default=DEFAULT_IS_H1_PROTOCOL_ENABLED)
    is_h2_protocol_enabled: bool = Field(default=DEFAULT_IS_H2_PROTOCOL_ENABLED)
    is_h3_protocol_enabled: bool = Field(default=DEFAULT_IS_H3_PROTOCOL_ENABLED)
    timeout: int = Field(default=DEFAULT_TIMEOUT)
    cache_max_entries: int = Field(default=DEFAULT_CACHE_MAX_ENTRIES)


class VirtualHost(SQLModel, table=True):
    __tablename__ = "ferron_virtual_host"

    id: int = Field(default=None, primary_key=True)
    virtual_host_name: str = Field(unique=True)

    reverse_proxy_config: Optional["ReverseProxyConfig"] = Relationship(
        back_populates="virtual_host",
        # uselist=False because one-to-one relationship
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False},
    )
    static_file_config: Optional["StaticFileConfig"] = Relationship(
        back_populates="virtual_host", sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False}
    )
    load_balancer_config: Optional["LoadBalancerConfig"] = Relationship(
        back_populates="virtual_host", sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False}
    )
    load_balancer_backends: List["LoadBalancerBackendURL"] = Relationship(
        back_populates="virtual_host", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Cache(SQLModel):
    cache: bool = Field(default=DEFAULT_CACHE_ENABLED)
    cache_max_age: int = Field(default=DEFAULT_CACHE_MAX_AGE)


class StaticFileConfig(Cache, SQLModel, table=True):
    __tablename__ = "ferron_static_file_config"

    id: int = Field(default=None, primary_key=True)
    virtual_host_id: int = Field(
        sa_column=Column(Integer, ForeignKey("ferron_virtual_host.id", ondelete="CASCADE"), nullable=False)
    )
    virtual_host: VirtualHost = Relationship(
        back_populates="static_file_config",
        # uselist=False because one-to-one relationship
        # lazy=selectin because https://stackoverflow.com/a/74256068
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )
    static_files_dir: str = Field(default=None)
    use_spa: bool = Field(default=DEFAULT_USE_SPA)
    compressed: bool = Field(default=DEFAULT_COMPRESSED)
    directory_listing: bool = Field(default=DEFAULT_DIRECTORY_LISTING)
    precompressed: bool = Field(default=DEFAULT_PRECOMPRESSED)

    @property
    def virtual_host_name(self) -> Optional[str]:
        return self.virtual_host.virtual_host_name if self.virtual_host else None


class CommonReverseProxyConfig(Cache):
    preserve_host_header: bool = Field(default=DEFAULT_PRESERVE_HOST_HEADER)


class ReverseProxyConfig(CommonReverseProxyConfig, SQLModel, table=True):
    __tablename__ = "ferron_reverse_proxy_config"

    id: int = Field(default=None, primary_key=True)
    virtual_host_id: int = Field(
        sa_column=Column(Integer, ForeignKey("ferron_virtual_host.id", ondelete="CASCADE"), nullable=False)
    )
    virtual_host: VirtualHost = Relationship(
        back_populates="reverse_proxy_config",
        # uselist=False because one-to-one relationship
        # lazy=selectin because https://stackoverflow.com/a/74256068
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )
    backend_url: str = Field(default=None)
    use_unix_socket: bool = Field(default=DEFAULT_USE_UNIX_SOCKET)
    unix_socket_path: str = Field(default="")

    @property
    def virtual_host_name(self) -> Optional[str]:
        return self.virtual_host.virtual_host_name if self.virtual_host else None


class LoadBalancerBackendURL(SQLModel, table=True):
    __tablename__ = "ferron_load_balancer_backend_url"

    id: int = Field(default=None, primary_key=True)
    virtual_host_id: int = Field(
        sa_column=Column(Integer, ForeignKey("ferron_virtual_host.id", ondelete="CASCADE"), nullable=False)
    )
    virtual_host: VirtualHost = Relationship(
        back_populates="load_balancer_backends",
        # uselist=False because one-to-one relationship
        # lazy=selectin because https://stackoverflow.com/a/74256068
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )
    used_in_load_balancer: int = Field(
        sa_column=Column(Integer, ForeignKey("ferron_load_balancer_config.id", ondelete="CASCADE"), nullable=False)
    )
    backend_url: str = Field(default=None)

    load_balancer_relationship: "LoadBalancerConfig" = Relationship(back_populates="backend_urls_relationship")


class LoadBalancerConfig(CommonReverseProxyConfig, SQLModel, table=True):
    __tablename__ = "ferron_load_balancer_config"

    id: int = Field(default=None, primary_key=True)
    virtual_host_id: int = Field(
        sa_column=Column(Integer, ForeignKey("ferron_virtual_host.id", ondelete="CASCADE"), nullable=False)
    )
    virtual_host: VirtualHost = Relationship(
        back_populates="load_balancer_config",
        # uselist=False because one-to-one relationship
        # lazy=selectin because https://stackoverflow.com/a/74256068
        sa_relationship_kwargs={"lazy": "selectin", "uselist": False},
    )
    backend_urls_relationship: List[LoadBalancerBackendURL] = Relationship(
        back_populates="load_balancer_relationship",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "lazy": "selectin"},
    )
    lb_health_check: bool = Field(default=DEFAULT_LB_HEALTH_CHECK)
    lb_health_check_max_fails: int = Field(default=DEFAULT_LB_HEALTH_CHECK_MAX_FAILS)
    lb_health_check_window: int = Field(default=DEFAULT_LB_HEALTH_CHECK_WINDOW)

    @property
    def virtual_host_name(self) -> Optional[str]:
        return self.virtual_host.virtual_host_name if self.virtual_host else None

    @property
    def backend_urls(self) -> List[str]:
        return [backend.backend_url for backend in self.backend_urls_relationship]
