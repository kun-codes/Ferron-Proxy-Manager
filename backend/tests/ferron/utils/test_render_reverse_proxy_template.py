import pytest

from src.ferron.constants import (
    DEFAULT_CACHE_MAX_AGE,
    TemplateType,
)
from src.ferron.exceptions import TemplateConfigAndTemplateTypeMismatch
from src.ferron.schemas import TemplateConfig, UpdateReverseProxyConfig
from src.ferron.utils import render_template


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "template_type, template_config, expected_text",
    [
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(id=1, virtual_host_name="example.com", backend_url="http://localhost:8080"),
            """
example.com {

    proxy http://localhost:8080

}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=1,
                virtual_host_name="api.example.com",
                backend_url="http://localhost:8080",
                use_unix_socket=True,
                unix_socket_path="/var/run/app.sock",
            ),
            """
api.example.com {

    proxy http://localhost:8080 unix="/var/run/app.sock"

}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=1, virtual_host_name="app.example.com", backend_url="http://backend:3000", preserve_host_header=True
            ),
            """
app.example.com {

    proxy http://backend:3000

    proxy_request_header_replace "Host" "{header:Host}"

}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=1,
                virtual_host_name="cached.example.com",
                backend_url="http://backend:8080",
                cache=True,
                cache_max_age=7200,
            ),
            """
cached.example.com {

    proxy http://backend:8080

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age=7200"

}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=1,
                virtual_host_name="cached-default.example.com",
                backend_url="http://backend:8080",
                cache=True,
                cache_max_age=DEFAULT_CACHE_MAX_AGE,
            ),
            f"""
cached-default.example.com {{

    proxy http://backend:8080

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age={DEFAULT_CACHE_MAX_AGE}"

}}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=42,
                virtual_host_name="full.example.com",
                backend_url="http://backend:9000",
                use_unix_socket=True,
                unix_socket_path="/var/run/full.sock",
                preserve_host_header=True,
                cache=True,
                cache_max_age=1800,
            ),
            """
full.example.com {

    proxy http://backend:9000 unix="/var/run/full.sock"

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age=1800"

    proxy_request_header_replace "Host" "{header:Host}"

}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=1, virtual_host_name="secure.example.com", backend_url="https://secure-backend:443"
            ),
            """
secure.example.com {

    proxy https://secure-backend:443

}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=1, virtual_host_name="*.wildcard.example.com", backend_url="http://backend:8080"
            ),
            """
*.wildcard.example.com {

    proxy http://backend:8080

}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=1,
                virtual_host_name="multi.example.com",
                backend_url="http://backend:5000",
                preserve_host_header=True,
                cache=True,
                cache_max_age=600,
            ),
            """
multi.example.com {

    proxy http://backend:5000

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age=600"

    proxy_request_header_replace "Host" "{header:Host}"

}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=1,
                virtual_host_name="unix-preserve.example.com",
                backend_url="http://localhost:3000",
                use_unix_socket=True,
                unix_socket_path="/tmp/app.sock",
                preserve_host_header=True,
            ),
            """
unix-preserve.example.com {

    proxy http://localhost:3000 unix="/tmp/app.sock"

    proxy_request_header_replace "Host" "{header:Host}"

}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=1,
                virtual_host_name="unix-cache.example.com",
                backend_url="http://backend:8000",
                use_unix_socket=True,
                unix_socket_path="/var/run/backend.sock",
                cache=True,
                cache_max_age=300,
            ),
            """
unix-cache.example.com {

    proxy http://backend:8000 unix="/var/run/backend.sock"

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age=300"

}""",
        ),
        (
            TemplateType.REVERSE_PROXY_CONFIG,
            UpdateReverseProxyConfig(
                id=1, virtual_host_name="custom-port.example.com", backend_url="http://app-backend:9090"
            ),
            """
custom-port.example.com {

    proxy http://app-backend:9090

}""",
        ),
    ],
)
async def test_render_reverse_proxy_template(
    template_type: TemplateType, template_config: TemplateConfig, expected_text: str
) -> None:
    assert await render_template(template_type, template_config) == expected_text


@pytest.mark.asyncio
async def test_render_reverse_proxy_template_type_mismatch() -> None:
    invalid_config = TemplateConfig()

    with pytest.raises(TemplateConfigAndTemplateTypeMismatch) as exc_info:
        await render_template(TemplateType.REVERSE_PROXY_CONFIG, invalid_config)

    # Verify the exception details
    assert exc_info.value.status_code == 500
    assert "template_config_and_template_type_mismatch" in str(exc_info.value.detail)
