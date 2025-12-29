import pytest

from src.ferron.constants import (
    DEFAULT_CACHE_MAX_AGE,
    DEFAULT_COMPRESSED,
    DEFAULT_DIRECTORY_LISTING,
    DEFAULT_PRECOMPRESSED,
    DEFAULT_USE_SPA,
    TemplateType,
)
from src.ferron.exceptions import TemplateConfigAndTemplateTypeMismatch
from src.ferron.schemas import TemplateConfig, UpdateStaticFileConfig
from src.ferron.utils import render_template


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "template_type, template_config, expected_text",
    [
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(id=1, virtual_host_name="static.example.com", static_files_dir="/var/www/html"),
            """
static.example.com {

    root /var/www/html

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1, virtual_host_name="spa.example.com", static_files_dir="/var/www/spa", use_spa=True
            ),
            """
spa.example.com {

    root /var/www/spa

    rewrite "^/.*" "/" directory=#false file=#false last=#true

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1, virtual_host_name="uncompressed.example.com", static_files_dir="/var/www/site", compressed=False
            ),
            """
uncompressed.example.com {

    root /var/www/site

    compressed #false

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1, virtual_host_name="listing.example.com", static_files_dir="/var/www/files", directory_listing=True
            ),
            """
listing.example.com {

    root /var/www/files

    directory_listing

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="cached.example.com",
                static_files_dir="/var/www/cached",
                cache=True,
                cache_max_age=7200,
            ),
            """
cached.example.com {

    root /var/www/cached

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age=7200"

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="cached-default.example.com",
                static_files_dir="/var/www/default-cache",
                cache=True,
                cache_max_age=DEFAULT_CACHE_MAX_AGE,
            ),
            f"""
cached-default.example.com {{

    root /var/www/default-cache

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age={DEFAULT_CACHE_MAX_AGE}"

}}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="precompressed.example.com",
                static_files_dir="/var/www/precompressed",
                precompressed=True,
            ),
            """
precompressed.example.com {

    root /var/www/precompressed

    precompressed

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="spa-uncompressed.example.com",
                static_files_dir="/var/www/spa-app",
                use_spa=True,
                compressed=False,
            ),
            """
spa-uncompressed.example.com {

    root /var/www/spa-app

    rewrite "^/.*" "/" directory=#false file=#false last=#true

    compressed #false

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="spa-cached.example.com",
                static_files_dir="/var/www/spa-cached",
                use_spa=True,
                cache=True,
                cache_max_age=1800,
            ),
            """
spa-cached.example.com {

    root /var/www/spa-cached

    rewrite "^/.*" "/" directory=#false file=#false last=#true

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age=1800"

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="listing-precompressed.example.com",
                static_files_dir="/var/www/files-compressed",
                directory_listing=True,
                precompressed=True,
            ),
            """
listing-precompressed.example.com {

    root /var/www/files-compressed

    directory_listing

    precompressed

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="cached-precompressed.example.com",
                static_files_dir="/var/www/optimized",
                cache=True,
                cache_max_age=600,
                precompressed=True,
            ),
            """
cached-precompressed.example.com {

    root /var/www/optimized

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age=600"

    precompressed

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=42,
                virtual_host_name="full-featured.example.com",
                static_files_dir="/var/www/full",
                use_spa=True,
                compressed=False,
                directory_listing=True,
                cache=True,
                cache_max_age=300,
                precompressed=True,
            ),
            """
full-featured.example.com {

    root /var/www/full

    rewrite "^/.*" "/" directory=#false file=#false last=#true

    compressed #false

    directory_listing

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age=300"

    precompressed

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1, virtual_host_name="*.wildcard.example.com", static_files_dir="/var/www/wildcard"
            ),
            """
*.wildcard.example.com {

    root /var/www/wildcard

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="docs.example.com",
                static_files_dir="/usr/share/docs",
                directory_listing=True,
                cache=True,
                cache_max_age=86400,
            ),
            """
docs.example.com {

    root /usr/share/docs

    directory_listing

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age=86400"

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="app.example.com",
                static_files_dir="/opt/app/dist",
                use_spa=True,
                cache=True,
                cache_max_age=3600,
                precompressed=True,
            ),
            """
app.example.com {

    root /opt/app/dist

    rewrite "^/.*" "/" directory=#false file=#false last=#true

    // for in memory caching to speed up websites
    cache
    file_cache_control "max-age=3600"

    precompressed

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="blog.example.com",
                static_files_dir="/var/www/blog",
                compressed=True,
                directory_listing=False,
                cache=False,
            ),
            """
blog.example.com {

    root /var/www/blog

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="default-spa.example.com",
                static_files_dir="/var/www/default-spa",
                use_spa=DEFAULT_USE_SPA,
            ),
            """
default-spa.example.com {

    root /var/www/default-spa

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="default-compressed.example.com",
                static_files_dir="/var/www/default-compressed",
                compressed=DEFAULT_COMPRESSED,
            ),
            """
default-compressed.example.com {

    root /var/www/default-compressed

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="default-listing.example.com",
                static_files_dir="/var/www/default-listing",
                directory_listing=DEFAULT_DIRECTORY_LISTING,
            ),
            """
default-listing.example.com {

    root /var/www/default-listing

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="default-precompressed.example.com",
                static_files_dir="/var/www/default-precompressed",
                precompressed=DEFAULT_PRECOMPRESSED,
            ),
            """
default-precompressed.example.com {

    root /var/www/default-precompressed

}""",
        ),
        (
            TemplateType.STATIC_FILE_CONFIG,
            UpdateStaticFileConfig(
                id=1,
                virtual_host_name="all-defaults.example.com",
                static_files_dir="/var/www/all-defaults",
                use_spa=DEFAULT_USE_SPA,
                compressed=DEFAULT_COMPRESSED,
                directory_listing=DEFAULT_DIRECTORY_LISTING,
                precompressed=DEFAULT_PRECOMPRESSED,
                cache=False,
            ),
            """
all-defaults.example.com {

    root /var/www/all-defaults

}""",
        ),
    ],
)
async def test_render_static_file_template(
    template_type: TemplateType, template_config: TemplateConfig, expected_text: str
) -> None:
    assert await render_template(template_type, template_config) == expected_text


@pytest.mark.asyncio
async def test_render_static_file_template_type_mismatch() -> None:
    invalid_config = TemplateConfig()

    with pytest.raises(TemplateConfigAndTemplateTypeMismatch) as exc_info:
        await render_template(TemplateType.STATIC_FILE_CONFIG, invalid_config)

    # Verify the exception details
    assert exc_info.value.status_code == 500
    assert "template_config_and_template_type_mismatch" in str(exc_info.value.detail)
