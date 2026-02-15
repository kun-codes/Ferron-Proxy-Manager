from datetime import datetime, timedelta, timezone

import httpx
from semver import Version

from src.config import settings
from src.management import schemas
from src.management.constants import GITHUB_API_URL, VERSION_CACHE_DURATION_MINUTES
from src.management.exceptions import GitHubAPIException, VersionParseException

_latest_version_cache: tuple[datetime, schemas.LatestVersionResponse] | None = None


def get_current_version() -> schemas.VersionResponse:
    try:
        version = Version.parse(settings.app_version)
    except ValueError as e:
        raise VersionParseException(f"Failed to parse current version '{settings.app_version}': {e}") from e

    return schemas.VersionResponse(version=version)


async def get_latest_version() -> schemas.LatestVersionResponse:
    global _latest_version_cache

    if _latest_version_cache is not None:
        cached_time, cached_response = _latest_version_cache
        cache_age = datetime.now(timezone.utc) - cached_time
        if cache_age < timedelta(minutes=VERSION_CACHE_DURATION_MINUTES):
            return cached_response

    # is only run when cache is stale or doesn't exist
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GITHUB_API_URL,
                headers={"Accept": "application/vnd.github+json"},  # this specific header is because of
                # https://docs.github.com/en/rest/releases/releases?apiVersion=2022-11-28#get-the-latest-release--parameters
                timeout=2.0,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        raise GitHubAPIException(f"GitHub API returned status {e.response.status_code}") from e
    except httpx.RequestError as e:
        raise GitHubAPIException(f"Failed to connect to GitHub API: {e}") from e

    tag_name = data.get("tag_name", "")
    release_url = data.get("html_url")  # returns github.com link of the latest release

    # remove 'v' prefix if present (e.g., "v1.0.0" -> "1.0.0")
    version_str = tag_name.lstrip("v")

    try:
        version = Version.parse(version_str)
    except ValueError as e:
        raise VersionParseException(f"Failed to parse GitHub release version '{tag_name}': {e}") from e

    latest_version_response = schemas.LatestVersionResponse(version=version, release_url=release_url)

    _latest_version_cache = (datetime.now(timezone.utc), latest_version_response)

    return latest_version_response


async def check_update_available() -> schemas.UpdateAvailableResponse:
    current_version_response = get_current_version()
    latest_version_response = await get_latest_version()

    update_available = latest_version_response.version > current_version_response.version

    return schemas.UpdateAvailableResponse(
        update_available=update_available,
        current_version=current_version_response.version,
        latest_version=latest_version_response.version,
    )
