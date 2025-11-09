import textwrap
from pathlib import Path

import ckdl
import pytest

from src.ferron.service import FerronConfig


@pytest.fixture
def ferron_config_manager():
    return FerronConfig(Path("tests/ferron/ferron.kdl"))

@pytest.mark.parametrize("node_name, is_snippet, expected", [
    ("*", False, """
    * {
        protocols h1 h2
        h2_initial_window_size 65536
        h2_max_concurrent_streams 100
        timeout 300000
        listen_ip "0.0.0.0"
        default_http_port 80
        default_https_port 443
        tls_cipher_suite TLS_AES_256_GCM_SHA384 TLS_AES_128_GCM_SHA256
        ocsp_stapling
        block "192.168.1.100"
        cache_max_entries 1024
        lb_health_check_window 5000
        log "/var/log/ferron/access.log"
        error_log "/var/log/ferron/error.log"
        compressed
        etag
    }
    """),
    ("security_headers", True, """
    snippet security_headers {
        header X-Frame-Options DENY
        header X-Content-Type-Options nosniff
        header X-XSS-Protection "1; mode=block"
        header Referrer-Policy strict-origin-when-cross-origin
    }
    """),
    ("mobile_condition", True, """
    snippet mobile_condition {
        condition is_mobile {
            is_regex "{header:User-Agent}" "(Mobile|Android|iPhone|iPad)" case_insensitive=#true
        }
    }
    """),
    ("example.com", False, """
    example.com {
        tls "/etc/ssl/certs/example.com.crt" "/etc/ssl/private/example.com.key"
        auto_tls_contact admin@example.com
        root "/var/www/example.com"
        server_administrator_email admin@example.com
        use security_headers
        use mobile_condition
        use admin_ip_condition
        use api_request_condition
        use static_asset_condition
        use development_condition
        header Strict-Transport-Security "max-age=31536000; includeSubDomains"
        if is_mobile {
            use security_headers
            header Strict-Transport-Security "max-age=31536000; includeSubDomains"
            header X-Mobile-Detected true
            root "/var/www/example.com/mobile"
            limit rate=50 burst=100
        }
        if_not is_mobile {
            use security_headers
            header Strict-Transport-Security "max-age=31536000; includeSubDomains"
            header X-Mobile-Detected false
            limit rate=100 burst=200
        }
        if is_admin_ip {
            use security_headers
            header Strict-Transport-Security "max-age=31536000; includeSubDomains"
            limit #false
            header X-Admin-Access true
            header X-Client-IP "{client_ip}"
            log "/var/log/ferron/admin-access.log"
        }
        if is_development {
            use security_headers
            header Strict-Transport-Security "max-age=31536000; includeSubDomains"
            header X-Environment development
            header X-Debug-Mode enabled
            header Cache-Control "no-cache, no-store, must-revalidate"
            header Pragma no-cache
            header Expires "0"
        }
        if_not is_development {
            use security_headers
            header Strict-Transport-Security "max-age=31536000; includeSubDomains"
            cache
            cache_vary Accept-Encoding Accept-Language
            file_cache_control "public, max-age=3600"
        }
        rewrite "^/old-section/(.*)" "/new-section/$1" last=#true
        error_page 404 "/var/www/errors/404.html"
        error_page 500 "/var/www/errors/500.html"
        location "/assets" remove_base=#true {
            root "/var/www/assets"
            if is_static_asset {
                use security_headers
                header Strict-Transport-Security "max-age=31536000; includeSubDomains"
                use static_caching
            }
            if_not is_static_asset {
                use security_headers
                header Strict-Transport-Security "max-age=31536000; includeSubDomains"
                header Access-Control-Allow-Origin *
            }
        }
        location "/api" {
            if is_api_request {
                use security_headers
                header Strict-Transport-Security "max-age=31536000; includeSubDomains"
                use cors_headers
                limit rate=1000 burst=2000
                proxy "http://api-backend:8080"
                proxy_request_header_replace X-Real-IP "{client_ip}"
                proxy_request_header X-Forwarded-Proto "{scheme}"
            }
        }
        location "/admin" {
            if is_admin_ip {
                use security_headers
                header Strict-Transport-Security "max-age=31536000; includeSubDomains"
                root "/var/www/admin"
                header X-Admin-Direct-Access true
            }
            if_not is_admin_ip {
                use security_headers
                header Strict-Transport-Security "max-age=31536000; includeSubDomains"
                use admin_protection
            }
        }
        fcgi_php "tcp://localhost:9000/"
    }
    """),
    ("non_existent_snippet", True, None),
    ("non_existent_node", False, None),
])
def test_find_node(ferron_config_manager, node_name: str, is_snippet: bool, expected: str | None):
    if type(expected) is str:
        expected = textwrap.dedent(expected).strip()

    actual = ferron_config_manager.find_node(node_name, is_snippet)
    if type(actual) is ckdl.Node:
        actual = actual.__str__().strip()

    assert expected == actual
