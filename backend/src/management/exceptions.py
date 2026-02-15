from fastapi import HTTPException, status


class ManagementException(HTTPException):
    pass


class GitHubAPIException(ManagementException):
    def __init__(self, message: str = "Failed to fetch version from GitHub API") -> None:
        super().__init__(
            detail={"error_code": "github_api_error", "msg": message},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class VersionParseException(ManagementException):
    def __init__(self, message: str = "Failed to parse version") -> None:
        super().__init__(
            detail={"error_code": "version_parse_error", "msg": message},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
