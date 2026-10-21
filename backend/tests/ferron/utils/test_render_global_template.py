import textwrap

import pytest

from src.ferron.constants import TemplateType
from src.ferron.exceptions import TemplateConfigAndTemplateTypeMismatch
from src.ferron.schemas import GlobalTemplateConfig, TemplateConfig
from src.ferron.utils import render_template


def normalize_config(text: str) -> list[str]:
    """
    ignores blank lines and indentation, but keeps the content and internal spacing
    """
    return [line.strip() for line in text.splitlines() if line.strip()]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "template_type, template_config, expected_text",
    [
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(),
            textwrap.dedent(
                """\
                {
                    default_http_port 80
                    default_https_port 443

                    http {
                        protocols  "h1" "h2"
                        timeout 300
                    }

                    cache {
                        max_entries 1024
                    }
                }"""
            ),
        ),
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(
                default_http_port=8080,
                default_https_port=8443,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 8080
                    default_https_port 8443

                    http {
                        protocols  "h1" "h2"
                        timeout 300
                    }

                    cache {
                        max_entries 1024
                    }
                }"""
            ),
        ),
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(
                is_h1_protocol_enabled=True,
                is_h2_protocol_enabled=True,
                is_h3_protocol_enabled=True,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 80
                    default_https_port 443

                    http {
                        protocols  "h1" "h2" "h3"
                        timeout 300
                    }

                    cache {
                        max_entries 1024
                    }
                }"""
            ),
        ),
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(
                timeout=60,
                cache_max_entries=512,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 80
                    default_https_port 443

                    http {
                        protocols  "h1" "h2"
                        timeout 60
                    }

                    cache {
                        max_entries 512
                    }
                }"""
            ),
        ),
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(
                is_h1_protocol_enabled=False,
                is_h2_protocol_enabled=False,
                is_h3_protocol_enabled=False,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 80
                    default_https_port 443

                    http {
                        timeout 300
                    }

                    cache {
                        max_entries 1024
                    }
                }"""
            ),
        ),
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(
                is_h1_protocol_enabled=True,
                is_h2_protocol_enabled=False,
                is_h3_protocol_enabled=False,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 80
                    default_https_port 443

                    http {
                        protocols  "h1"
                        timeout 300
                    }

                    cache {
                        max_entries 1024
                    }
                }"""
            ),
        ),
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(
                is_h1_protocol_enabled=False,
                is_h2_protocol_enabled=True,
                is_h3_protocol_enabled=False,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 80
                    default_https_port 443

                    http {
                        protocols  "h2"
                        timeout 300
                    }

                    cache {
                        max_entries 1024
                    }
                }"""
            ),
        ),
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(
                is_h1_protocol_enabled=False,
                is_h2_protocol_enabled=False,
                is_h3_protocol_enabled=True,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 80
                    default_https_port 443

                    http {
                        protocols  "h3"
                        timeout 300
                    }

                    cache {
                        max_entries 1024
                    }
                }"""
            ),
        ),
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(
                is_h1_protocol_enabled=True,
                is_h2_protocol_enabled=False,
                is_h3_protocol_enabled=True,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 80
                    default_https_port 443

                    http {
                        protocols  "h1" "h3"
                        timeout 300
                    }

                    cache {
                        max_entries 1024
                    }
                }"""
            ),
        ),
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(
                is_h1_protocol_enabled=False,
                is_h2_protocol_enabled=True,
                is_h3_protocol_enabled=True,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 80
                    default_https_port 443

                    http {
                        protocols  "h2" "h3"
                        timeout 300
                    }

                    cache {
                        max_entries 1024
                    }
                }"""
            ),
        ),
        (
            TemplateType.GLOBAL_CONFIG,
            GlobalTemplateConfig(
                default_http_port=3000,
                default_https_port=3443,
                is_h1_protocol_enabled=True,
                is_h2_protocol_enabled=False,
                is_h3_protocol_enabled=True,
                timeout=120,
                cache_max_entries=2048,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 3000
                    default_https_port 3443

                    http {
                        protocols  "h1" "h3"
                        timeout 120
                    }

                    cache {
                        max_entries 2048
                    }
                }"""
            ),
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
                cache_max_entries=1,
            ),
            textwrap.dedent(
                """\
                {
                    default_http_port 1
                    default_https_port 65535

                    http {
                        protocols  "h1" "h2" "h3"
                        timeout 1
                    }

                    cache {
                        max_entries 1
                    }
                }"""
            ),
        ),
    ],
)
async def test_render_template(
    template_type: TemplateType, template_config: TemplateConfig, expected_text: str
) -> None:
    rendered = await render_template(template_type, template_config)

    assert normalize_config(rendered) == normalize_config(expected_text)


@pytest.mark.asyncio
async def test_render_template_type_mismatch() -> None:
    invalid_config = TemplateConfig()

    with pytest.raises(TemplateConfigAndTemplateTypeMismatch) as exc_info:
        await render_template(TemplateType.GLOBAL_CONFIG, invalid_config)

    # Verify the exception details
    assert exc_info.value.status_code == 500
    assert "template_config_and_template_type_mismatch" in str(exc_info.value.detail)
