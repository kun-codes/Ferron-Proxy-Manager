import pytest

from src.ferron.constants import (
    DEFAULT_CACHE_MAX_ENTRIES,
    DEFAULT_HTTP_PORT,
    DEFAULT_HTTPS_PORT,
    DEFAULT_TIMEOUT,
    TemplateType,
)
from src.ferron.exceptions import TemplateConfigAndTemplateTypeMismatch
from src.ferron.schemas import GlobalTemplateConfig, TemplateConfig
from src.ferron.utils import render_template


@pytest.mark.asyncio
@pytest.mark.parametrize("template_type, template_config, expected_text", [
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(),
        f"""
* {{

    default_http_port {DEFAULT_HTTP_PORT}

    default_https_port {DEFAULT_HTTPS_PORT}

    protocols "h1" "h2"

    timeout {DEFAULT_TIMEOUT}

    cache_max_entries {DEFAULT_CACHE_MAX_ENTRIES}
}}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            default_http_port=8080,
            default_https_port=8443,
        ),
        f"""
* {{

    default_http_port 8080

    default_https_port 8443

    protocols "h1" "h2"

    timeout {DEFAULT_TIMEOUT}

    cache_max_entries {DEFAULT_CACHE_MAX_ENTRIES}
}}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            is_h1_protocol_enabled=True,
            is_h2_protocol_enabled=True,
            is_h3_protocol_enabled=True,
        ),
        f"""
* {{

    default_http_port {DEFAULT_HTTP_PORT}

    default_https_port {DEFAULT_HTTPS_PORT}

    protocols "h1" "h2" "h3"

    timeout {DEFAULT_TIMEOUT}

    cache_max_entries {DEFAULT_CACHE_MAX_ENTRIES}
}}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            timeout=60000,
            cache_max_entries=512,
        ),
        f"""
* {{

    default_http_port {DEFAULT_HTTP_PORT}

    default_https_port {DEFAULT_HTTPS_PORT}

    protocols "h1" "h2"

    timeout 60000

    cache_max_entries 512
}}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            is_h1_protocol_enabled=False,
            is_h2_protocol_enabled=False,
            is_h3_protocol_enabled=False,
        ),
        f"""
* {{

    default_http_port {DEFAULT_HTTP_PORT}

    default_https_port {DEFAULT_HTTPS_PORT}

    timeout {DEFAULT_TIMEOUT}

    cache_max_entries {DEFAULT_CACHE_MAX_ENTRIES}
}}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            is_h1_protocol_enabled=True,
            is_h2_protocol_enabled=False,
            is_h3_protocol_enabled=False,
        ),
        f"""
* {{

    default_http_port {DEFAULT_HTTP_PORT}

    default_https_port {DEFAULT_HTTPS_PORT}

    protocols "h1"

    timeout {DEFAULT_TIMEOUT}

    cache_max_entries {DEFAULT_CACHE_MAX_ENTRIES}
}}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            is_h1_protocol_enabled=False,
            is_h2_protocol_enabled=True,
            is_h3_protocol_enabled=False,
        ),
        f"""
* {{

    default_http_port {DEFAULT_HTTP_PORT}

    default_https_port {DEFAULT_HTTPS_PORT}

    protocols "h2"

    timeout {DEFAULT_TIMEOUT}

    cache_max_entries {DEFAULT_CACHE_MAX_ENTRIES}
}}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            is_h1_protocol_enabled=False,
            is_h2_protocol_enabled=False,
            is_h3_protocol_enabled=True,
        ),
        f"""
* {{

    default_http_port {DEFAULT_HTTP_PORT}

    default_https_port {DEFAULT_HTTPS_PORT}

    protocols "h3"

    timeout {DEFAULT_TIMEOUT}

    cache_max_entries {DEFAULT_CACHE_MAX_ENTRIES}
}}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            is_h1_protocol_enabled=True,
            is_h2_protocol_enabled=False,
            is_h3_protocol_enabled=True,
        ),
        f"""
* {{

    default_http_port {DEFAULT_HTTP_PORT}

    default_https_port {DEFAULT_HTTPS_PORT}

    protocols "h1" "h3"

    timeout {DEFAULT_TIMEOUT}

    cache_max_entries {DEFAULT_CACHE_MAX_ENTRIES}
}}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            is_h1_protocol_enabled=False,
            is_h2_protocol_enabled=True,
            is_h3_protocol_enabled=True,
        ),
        f"""
* {{

    default_http_port {DEFAULT_HTTP_PORT}

    default_https_port {DEFAULT_HTTPS_PORT}

    protocols "h2" "h3"

    timeout {DEFAULT_TIMEOUT}

    cache_max_entries {DEFAULT_CACHE_MAX_ENTRIES}
}}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            default_http_port=3000,
            default_https_port=3443,
            is_h1_protocol_enabled=True,
            is_h2_protocol_enabled=False,
            is_h3_protocol_enabled=True,
            timeout=120000,
            cache_max_entries=2048
        ),
        """
* {

    default_http_port 3000

    default_https_port 3443

    protocols "h1" "h3"

    timeout 120000

    cache_max_entries 2048
}"""
    ),
    (
        TemplateType.GLOBAL_CONFIG,
        GlobalTemplateConfig(
            default_http_port=1,
            default_https_port=65535,
            is_h1_protocol_enabled=True,
            is_h2_protocol_enabled=True,
            is_h3_protocol_enabled=True,
            timeout=1,
            cache_max_entries=1
        ),
        """
* {

    default_http_port 1

    default_https_port 65535

    protocols "h1" "h2" "h3"

    timeout 1

    cache_max_entries 1
}"""
    ),
])
async def test_render_template(
    template_type: TemplateType, 
    template_config: TemplateConfig, 
    expected_text: str
) -> None:
    assert await render_template(template_type, template_config) == expected_text


@pytest.mark.asyncio
async def test_render_template_type_mismatch() -> None:
    invalid_config = TemplateConfig()

    with pytest.raises(TemplateConfigAndTemplateTypeMismatch) as exc_info:
        await render_template(TemplateType.GLOBAL_CONFIG, invalid_config)

    # Verify the excetion details
    assert exc_info.value.status_code == 500
    assert "template_config_and_template_type_mismatch" in str(exc_info.value.detail)
