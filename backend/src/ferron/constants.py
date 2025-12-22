from enum import Enum

DEFAULT_HTTP_PORT = 80
DEFAULT_HTTPS_PORT = 443
DEFAULT_IS_H1_PROTOCOL_ENABLED = True
DEFAULT_IS_H2_PROTOCOL_ENABLED = True
DEFAULT_IS_H3_PROTOCOL_ENABLED = False
DEFAULT_TIMEOUT = 300000
DEFAULT_CACHE_MAX_ENTRIES = 1024

DEFAULT_CACHE_ENABLED = False
DEFAULT_CACHE_MAX_AGE = 3600

DEFAULT_PRESERVE_HOST_HEADER = False

DEFAULT_USE_UNIX_SOCKET = False


class TemplateType(Enum):
    GLOBAL_CONFIG = "global.j2"
    LOAD_BALANCER_CONFIG = "load_balancer.j2"
    REVERSE_PROXY_CONFIG = "reverse_proxy.j2"
    STATIC_FILE_CONFIG = "static_file.j2"

SUB_CONFIG_PATH = "/etc/ferron-proxy-manager"
class ConfigFileLocation(Enum):
    # this is where all configs for global and other virtual hosts are included using include statement
    MAIN_CONFIG = f"{SUB_CONFIG_PATH}/main.kdl"
    GLOBAL_CONFIG = f"{SUB_CONFIG_PATH}/global.kdl"

