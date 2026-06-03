from datetime import timedelta

FAVICON_REFRESH_TTL = timedelta(hours=6)
# https://alexmili.github.io/extract_favicon/#get-the-best-favicon-available
CONTENT_ONLY_STRATEGY = ["content"]  # used for specifying extract_favicon on how to get the favicon
_LOCALHOST_ALIASES = frozenset({"localhost", "127.0.0.1", "::1"})
FAVICON_WAIT_TIMEOUT = 30.0  # in seconds
FAVICON_WAIT_INTERVAL = 2.0  # in seconds
