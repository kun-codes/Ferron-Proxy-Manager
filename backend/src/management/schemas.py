from pydantic import BaseModel

from src.management.types import SemanticVersion


class VersionResponse(BaseModel):
    version: SemanticVersion


class LatestVersionResponse(BaseModel):
    version: SemanticVersion
    release_url: str | None = None


class UpdateAvailableResponse(BaseModel):
    update_available: bool
    current_version: SemanticVersion
    latest_version: SemanticVersion
    release_url: str | None = None
