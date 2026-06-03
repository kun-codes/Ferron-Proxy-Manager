from datetime import timedelta

FAVICON_REFRESH_TTL = timedelta(hours=6)
# https://alexmili.github.io/extract_favicon/#get-the-best-favicon-available
CONTENT_ONLY_STRATEGY = ["content"]  # used for specifying extract_favicon on how to get the favicon
