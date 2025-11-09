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

@pytest.mark.parametrize("node_name, directive_name, is_snippet, expected", [
    ("*", "protocols", False, [ckdl.Node(None, "protocols", "h1", "h2")]),
    ("*", "h2_initial_window_size", False, [ckdl.Node(None, "h2_initial_window_size", 65536)]),
    ("*", "listen_ip", False, [ckdl.Node(None, "listen_ip", "0.0.0.0")]),
    ("*", "ocsp_stapling", False, [ckdl.Node(None, "ocsp_stapling")]),
    ("*", "log", False, [ckdl.Node(None, "log", "/var/log/ferron/access.log")]),
    ("*", "default_http_port", False, [ckdl.Node(None, "default_http_port", 80)]),
    ("*", "tls_cipher_suite", False, [ckdl.Node(None, "tls_cipher_suite", "TLS_AES_256_GCM_SHA384", "TLS_AES_128_GCM_SHA256")]),
    ("*", "compressed", False, [ckdl.Node(None, "compressed")]),
    ("security_headers", "header", True, [
        ckdl.Node(None, "header", "X-Frame-Options", "DENY"),
        ckdl.Node(None, "header", "X-Content-Type-Options", "nosniff"),
        ckdl.Node(None, "header", "X-XSS-Protection", "1; mode=block"),
        ckdl.Node(None, "header", "Referrer-Policy", "strict-origin-when-cross-origin"),
    ]),
    ("static_caching", "file_cache_control", True, [ckdl.Node(None, "file_cache_control", "public, max-age=31536000, immutable")]),
    ("static_caching", "compressed", True, [ckdl.Node(None, "compressed")]),
    ("static_caching", "etag", True, [ckdl.Node(None, "etag")]),
    ("admin_protection", "status", True, [
        ckdl.Node(None, "status", 401, realm="Admin Area", users="admin,superuser"),
    ]),
    ("admin_protection", "users", True, [
        ckdl.Node(None, "users", "admin", "$2b$10$hashedpassword12345"),
        ckdl.Node(None, "users", "superuser", "$2b$10$anotherhashpassword67890"),
    ]),
    ("admin_protection", "limit", True, [ckdl.Node(None, "limit", rate=10, burst=20)]),
    ("mobile_condition", "condition", True, [
        ckdl.Node(None, "condition", "is_mobile",
                  ckdl.Node(None, "is_regex", "{header:User-Agent}", "(Mobile|Android|iPhone|iPad)", case_insensitive=True)),
    ]),
    ("admin_ip_condition", "condition", True, [
        ckdl.Node(None, "condition", "is_admin_ip",
                  ckdl.Node(None, "is_remote_ip", "192.168.1.10", "10.0.0.5")),
    ]),
    ("static_asset_condition", "condition", True, [
        ckdl.Node(None, "condition", "is_static_asset",
                  ckdl.Node(None, "is_regex", "{path}", "\\.(css|js|png|jpg|jpeg|gif|svg|woff|woff2|ttf|eot|ico)(?:$|[?#])", case_insensitive=True)),
    ]),
    ("example.com", "tls", False, [ckdl.Node(None, "tls", "/etc/ssl/certs/example.com.crt", "/etc/ssl/private/example.com.key")]),
    ("example.com", "auto_tls_contact", False, [ckdl.Node(None, "auto_tls_contact", "admin@example.com")]),
    ("example.com", "use", False, [
        ckdl.Node(None, "use", "security_headers"),
        ckdl.Node(None, "use", "mobile_condition"),
        ckdl.Node(None, "use", "admin_ip_condition"),
        ckdl.Node(None, "use", "api_request_condition"),
        ckdl.Node(None, "use", "static_asset_condition"),
        ckdl.Node(None, "use", "development_condition"),
    ]),
    ("example.com", "if", False, [
        ckdl.Node(None, "if", "is_mobile",
                  ckdl.Node(None, "use", "security_headers"),
                  ckdl.Node(None, "header", "Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
                  ckdl.Node(None, "header", "X-Mobile-Detected", "true"),
                  ckdl.Node(None, "root", "/var/www/example.com/mobile"),
                  ckdl.Node(None, "limit", rate=50, burst=100)),
        ckdl.Node(None, "if", "is_admin_ip",
                  ckdl.Node(None, "use", "security_headers"),
                  ckdl.Node(None, "header", "Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
                  ckdl.Node(None, "limit", False),
                  ckdl.Node(None, "header", "X-Admin-Access", "true"),
                  ckdl.Node(None, "header", "X-Client-IP", "{client_ip}"),
                  ckdl.Node(None, "log", "/var/log/ferron/admin-access.log")),
        ckdl.Node(None, "if", "is_development",
                  ckdl.Node(None, "use", "security_headers"),
                  ckdl.Node(None, "header", "Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
                  ckdl.Node(None, "header", "X-Environment", "development"),
                  ckdl.Node(None, "header", "X-Debug-Mode", "enabled"),
                  ckdl.Node(None, "header", "Cache-Control", "no-cache, no-store, must-revalidate"),
                  ckdl.Node(None, "header", "Pragma", "no-cache"),
                  ckdl.Node(None, "header", "Expires", "0")),
    ]),
    ("example.com", "if_not", False, [
        ckdl.Node(None, "if_not", "is_mobile",
                  ckdl.Node(None, "use", "security_headers"),
                  ckdl.Node(None, "header", "Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
                  ckdl.Node(None, "header", "X-Mobile-Detected", "false"),
                  ckdl.Node(None, "limit", rate=100, burst=200)),
        ckdl.Node(None, "if_not", "is_development",
                  ckdl.Node(None, "use", "security_headers"),
                  ckdl.Node(None, "header", "Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
                  ckdl.Node(None, "cache"),
                  ckdl.Node(None, "cache_vary", "Accept-Encoding", "Accept-Language"),
                  ckdl.Node(None, "file_cache_control", "public, max-age=3600")),
    ]),
    ("example.com", "error_page", False, [
        ckdl.Node(None, "error_page", 404, "/var/www/errors/404.html"),
        ckdl.Node(None, "error_page", 500, "/var/www/errors/500.html"),
    ]),
    ("example.com", "location", False, [
        ckdl.Node(None, "location", "/assets",
                  ckdl.Node(None, "root", "/var/www/assets"),
                  ckdl.Node(None, "if", "is_static_asset",
                            ckdl.Node(None, "use", "security_headers"),
                            ckdl.Node(None, "header", "Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
                            ckdl.Node(None, "use", "static_caching")),
                  ckdl.Node(None, "if_not", "is_static_asset",
                            ckdl.Node(None, "use", "security_headers"),
                            ckdl.Node(None, "header", "Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
                            ckdl.Node(None, "header", "Access-Control-Allow-Origin", "*")),
                  remove_base=True),
        ckdl.Node(None, "location", "/api",
                  ckdl.Node(None, "if", "is_api_request",
                            ckdl.Node(None, "use", "security_headers"),
                            ckdl.Node(None, "header", "Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
                            ckdl.Node(None, "use", "cors_headers"),
                            ckdl.Node(None, "limit", rate=1000, burst=2000),
                            ckdl.Node(None, "proxy", "http://api-backend:8080"),
                            ckdl.Node(None, "proxy_request_header_replace", "X-Real-IP", "{client_ip}"),
                            ckdl.Node(None, "proxy_request_header", "X-Forwarded-Proto", "{scheme}"))),
        ckdl.Node(None, "location", "/admin",
                  ckdl.Node(None, "if", "is_admin_ip",
                            ckdl.Node(None, "use", "security_headers"),
                            ckdl.Node(None, "header", "Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
                            ckdl.Node(None, "root", "/var/www/admin"),
                            ckdl.Node(None, "header", "X-Admin-Direct-Access", "true")),
                  ckdl.Node(None, "if_not", "is_admin_ip",
                            ckdl.Node(None, "use", "security_headers"),
                            ckdl.Node(None, "header", "Strict-Transport-Security", "max-age=31536000; includeSubDomains"),
                            ckdl.Node(None, "use", "admin_protection"))),
    ]),
    ("dev.example.com", "if", False, [
        ckdl.Node(None, "if", "is_hot_reload",
                  ckdl.Node(None, "use", "security_headers"),
                  ckdl.Node(None, "header", "X-Frame-Options", "SAMEORIGIN"),
                  ckdl.Node(None, "proxy", "http://dev-hmr:3001"),
                  ckdl.Node(None, "proxy_request_header", "Connection", "Upgrade"),
                  ckdl.Node(None, "proxy_request_header", "Upgrade", "websocket"),
                  ckdl.Node(None, "header", "Cache-Control", "no-cache")),
        ckdl.Node(None, "if", "is_source_map",
                  ckdl.Node(None, "if", "is_admin_ip",
                            ckdl.Node(None, "root", "/var/www/dev/sourcemaps")),
                  ckdl.Node(None, "if_not", "is_admin_ip",
                            ckdl.Node(None, "status", 404, body="Not found"))),
        ckdl.Node(None, "if", "is_admin_ip",
                  ckdl.Node(None, "status", 200, url="/test", body="Development server is working (Admin Access)"),
                  ckdl.Node(None, "status", 200, url="/debug", body="{\"client_ip\":\"{client_ip}\",\"method\":\"{method}\",\"path\":\"{path}\"}")),
    ]),
    ("rego.example.com", "condition", False, [
    ckdl.Node(None, "condition", "DENY_CURL",
          ckdl.Node(None, "is_rego", "package ferron\n\n"
                                     "default pass := false\n\n"
                                     "pass := true if {\n"
                                     "  input.headers[\"user-agent\"][0] == \"curl\"\n"
                                     "}\n\n"
                                     "pass := true if {\n"
                                     "  startswith(input.headers[\"user-agent\"][0], \"curl/\")\n"
                                     "}"
                    )),
    ]),
    ("non_existent_node", "non_existent_directive", False, []),
    ("non_existent_snippet", "non_existent_directive", True, []),
    ("example.com", "non_existent_directive", False, []),
    ("development_condition", "non_existent_directive", True, []),
    ("example.com", "block", False, []),  # block is valid directive but not present in example.com
])
def test_get_node_directive(ferron_config_manager, node_name: str, directive_name: str, is_snippet: bool, expected):
    actual = ferron_config_manager.get_node_directive(node_name, directive_name, is_snippet)

    assert expected == actual

@pytest.mark.parametrize("node_name, directive_name, is_snippet, expected", [
    ("*", "protocols", False, [["h1", "h2"]]),
    ("*", "h2_initial_window_size", False, [[65536]]),
    ("*", "tls_cipher_suite", False, [["TLS_AES_256_GCM_SHA384", "TLS_AES_128_GCM_SHA256"]]),
    ("security_headers", "header", True, [
        ["X-Frame-Options", "DENY"],
        ["X-Content-Type-Options", "nosniff"],
        ["X-XSS-Protection", "1; mode=block"],
        ["Referrer-Policy", "strict-origin-when-cross-origin"],
    ]),
    ("admin_protection", "users", True, [
        ["admin", "$2b$10$hashedpassword12345"],
        ["superuser", "$2b$10$anotherhashpassword67890"],
    ]),
    ("admin_protection", "status", True, [
        [401],
    ]),
    ("static_asset_condition", "condition", True, [["is_static_asset"]]),
    ("example.com", "use", False, [
        ["security_headers"],
        ["mobile_condition"],
        ["admin_ip_condition"],
        ["api_request_condition"],
        ["static_asset_condition"],
        ["development_condition"],
    ]),
    ("example.com", "if", False, [["is_mobile"], ["is_admin_ip"], ["is_development"]]),
    ("example.com", "if_not", False, [["is_mobile"], ["is_development"]]),
    ("example.com", "error_page", False, [[404, "/var/www/errors/404.html"], [500, "/var/www/errors/500.html"]]),
    ("api.example.com", "tls", False, [["/etc/ssl/certs/api.example.com.crt", "/etc/ssl/private/api.example.com.key"]]),
])
def test_get_directive_arguments(ferron_config_manager, node_name: str, directive_name: str, is_snippet: bool, expected):
    actual = ferron_config_manager.get_directive_arguments(node_name, directive_name, is_snippet)

    assert expected == actual