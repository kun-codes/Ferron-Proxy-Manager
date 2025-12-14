from typing import List

from sqlalchemy import Column, Integer, ForeignKey
from sqlmodel import Field, SQLModel, Relationship


# TODO: limit this table to only 1 row
class GlobalConfig(SQLModel, table=True):
    __tablename__ = "ferron_global_config"

    id: int = Field(default=None, primary_key=True)
    default_http_port: int = Field(default=80)
    default_https_port: int = Field(default=443)
    is_h1_protocol_enabled: bool = Field(default=True)
    is_h2_protocol_enabled: bool = Field(default=True)
    is_h3_protocol_enabled: bool = Field(default=False)
    timeout: int = Field(default=300000)
    cache_max_entries: int = Field(default=1024)


class BaseVirtualHost(SQLModel):
    id: int = Field(default=None, primary_key=True)
    virtual_host_name: str = Field(unique=True)

class Cache(SQLModel):
    cache: bool = Field(default=False)
    cache_max_age: int = Field(default=3600)

class StaticFileConfig(BaseVirtualHost, Cache, table=True):
    __tablename__ = "ferron_static_file_config"

    static_files_dir: str = Field(default=None)
    use_spa: bool = Field(default=False)
    compressed: bool = Field(default=False)
    directory_listing: bool = Field(default=False)
    precompressed: bool = Field(default=False)


class CommonReverseProxyConfig(BaseVirtualHost, Cache):
    preserve_host_header: bool = Field(default=False)


class ReverseProxyConfig(CommonReverseProxyConfig, table=True):
    __tablename__ = "ferron_reverse_proxy_config"

    backend_url: str = Field(default=None)
    use_unix_socket: bool = Field(default=False)
    unix_socket_path: str = Field(default=None)


class LoadBalancerBackendURL(SQLModel, table=True):
    __tablename__ = "ferron_load_balancer_backend_url"

    id: int = Field(default=None, primary_key=True)
    backend_url: str = Field(default=None)
    used_in_load_balancer: int = Field(
        sa_column=Column(Integer, ForeignKey("ferron_load_balancer_config.id", ondelete="CASCADE"), nullable=False)
    )

    load_balancer_relationship: "LoadBalancerConfig" = Relationship(back_populates="backend_urls_relationship")


class LoadBalancerConfig(CommonReverseProxyConfig, table=True):
    __tablename__ = "ferron_load_balancer_config"

    backend_urls_relationship: List[LoadBalancerBackendURL] = Relationship(
        back_populates="load_balancer_relationship",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
