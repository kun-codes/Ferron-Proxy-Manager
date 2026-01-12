"""
Global exceptions for the application.
"""

from fastapi import HTTPException, status


class RateLimitExceededCustomException(HTTPException):
    """
    Exception raised when a user exceeds the rate limit.
    """

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error_code": "rate_limit_exceeded",
                "msg": "Please slow down and try again later.",
            },
        )


class InvalidTokenException(HTTPException):
    def __init__(self, message: str = "Could not validate token") -> None:
        super().__init__(
            detail={"error_code": "invalid_token", "msg": message},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
