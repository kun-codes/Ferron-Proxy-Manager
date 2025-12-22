import shutil
import tempfile
import textwrap
from pathlib import Path

import ckdl
import pytest

from src.ferron.service import FerronConfig

source_file = Path("tests/ferron/ferron.kdl")

@pytest.fixture
def ferron_config_manager():
    destination_file = Path(tempfile.gettempdir()) / "ferron.kdl"
    # destination_file = Path("tests/ferron/test_ferron.kdl")
    shutil.copy2(source_file, destination_file)

    try:
        yield FerronConfig(destination_file)
    finally:
        try:
            pass
            # os.remove(destination_file)
        except OSError:
            pass


temp_ferron_config_manager = FerronConfig(source_file)
global_block = temp_ferron_config_manager.get_config_block("*")
global_block_in_text = global_block.__str__()  # the global block in string form



@pytest.mark.parametrize("config_block_name, node, is_snippet, expected", [
    (
        "*",
        ckdl.Node(
        None, "*", children=[
            ckdl.Node(None, "protocols", "h1", "h2"),
        ]
        ),
        False,
        """
        * {
            protocols h1 h2
        }
        """
    ),
    (
        "*",
        ckdl.Node(
            None, "*", children=[
                ckdl.Node(None, "protocols", "h1", "h2"),
                ckdl.Node(None, "h2_initial_window_size", 65536),
                ckdl.Node(None, "listen_ip", "0.0.0.0"),
                ckdl.Node(None, "tls_cipher_suite", "TLS_AES_256_GCM_SHA384", "TLS_AES_128_GCM_SHA256"),
                ckdl.Node(None, "ocsp_stapling"),
            ]
        ),
        False,
        """
        * {
            protocols h1 h2
            h2_initial_window_size 65536
            listen_ip "0.0.0.0"
            tls_cipher_suite TLS_AES_256_GCM_SHA384 TLS_AES_128_GCM_SHA256
            ocsp_stapling
        }
        """
    ),
    (
        "security_headers",
        ckdl.Node(None, "snippet", args=["security_headers"], children=[
                  ckdl.Node(None, "header", "X-Frame-Options", "DENY"),
                  ckdl.Node(None, "header", "X-Content-Type-Options", "nosniff"),
            ]
        ),
        True,
        """
        snippet security_headers {
            header X-Frame-Options DENY
            header X-Content-Type-Options nosniff
        }
        """
    ),
    (
        "api_request_condition",
        ckdl.Node(None, "snippet", args=["api_request_condition"], children=[
            ckdl.Node(None, "condition", args=["is_api_request"], children=[
                ckdl.Node(None, "is_regex", "{path}", "^/api/v2"),  # changed the regex to ^/api/v2
            ])
        ]),
        True,
        """
        snippet api_request_condition {
            condition is_api_request {
                is_regex "{path}" "^/api/v2"
            }
        }
        """
    ),
    (
        "example.com",
        ckdl.Node(None, "example.com", children=[
            ckdl.Node(None, "root", "/var/www/example.com"),
            ckdl.Node(None, "use", "security_headers"),
            ckdl.Node(None, "if", "is_mobile", children=[
                ckdl.Node(None, "limit", rate=50, burst=100),
            ])
        ]),
        False,
        """
        example.com {
            root "/var/www/example.com"
            use security_headers
            if is_mobile {
                limit rate=50 burst=100
            }
        }
        """
    ),
    (
        "rego.example.com",
        ckdl.Node(None, "rego.example.com", children=[
            ckdl.Node(None, "condition", "DENY_CURL", children=[
                ckdl.Node
                (
                    None,
                    "is_rego",
                    textwrap.dedent("""
                        package ferron
                        
                        default pass := false
                        
                        pass := true if {
                        input.headers["user-agent"][0] == "curl"
                        }
                    """)
                )
            ])
        ]),
        False,
        """
        rego.example.com {
            condition "DENY_CURL" {
                is_rego \"\"\"
                
                package ferron
                
                default pass := false
                
                pass := true if {
                input.headers["user-agent"][0] == "curl"
                }
                
                \"\"\"
            }
        }
        """
    )
])
def test_set_config_block(ferron_config_manager, config_block_name: str, node: ckdl.Node, is_snippet: bool, expected: str) -> None:
    """
    - Takes a FerronConfig instance and sets a config block.
    - Saves the config to a temporary file.
    - Rereads the config from the temporary file
    - Parses expected value string into a ckdl.Document object
    - Compares the first node of above ckdl.Document object to the required node of the FerronConfig instance

    Logic: Despite how identifiers are quoted in the expected string, the document structure parsed by ckdl should
    be the same
    """
    ferron_config_manager.set_config_block(config_block_name, node, is_snippet=is_snippet)
    ferron_config_manager.save()

    # loading from file again to simulate a freshly parsed config
    ferron_config_manager.load_from_file()

    # despite differences in how identifiers are quoted, the document structure parsed by ckdl should be the same
    expected_ferron_config_document = ckdl.parse(expected, version=2)
    expected_block = expected_ferron_config_document.nodes[0]

    actual_block = ferron_config_manager.get_config_block(config_block_name, is_snippet=is_snippet)

    assert actual_block == expected_block