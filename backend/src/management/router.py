from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.exceptions import InvalidTokenException
from src.management import schemas, service
from src.management.exceptions import GitHubAPIException, VersionParseException
from src.utils import generate_error_response, merge_responses

router = APIRouter(
    prefix="/management",
    tags=["management"],
    dependencies=[Depends(get_current_user)],
    responses=generate_error_response(InvalidTokenException),
)

version_router = APIRouter(
    prefix="/version",
    tags=["management-version"],
)


@version_router.get(
    "",
    response_model=schemas.VersionResponse,
    responses=generate_error_response(VersionParseException),
)
async def get_current_version() -> schemas.VersionResponse:
    return service.get_current_version()


@version_router.get(
    "/latest",
    response_model=schemas.LatestVersionResponse,
    responses=merge_responses(
        generate_error_response(GitHubAPIException),
        generate_error_response(VersionParseException),
    ),
)
async def get_latest_version() -> schemas.LatestVersionResponse:
    return await service.get_latest_version_from_github()


@version_router.get(
    "/check",
    response_model=schemas.UpdateAvailableResponse,
    responses=merge_responses(
        generate_error_response(GitHubAPIException),
        generate_error_response(VersionParseException),
    ),
)
async def check_update_available() -> schemas.UpdateAvailableResponse:
    return await service.check_update_available()


router.include_router(version_router)
