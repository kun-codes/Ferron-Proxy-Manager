from fastapi import HTTPException, status


class AuthException(HTTPException):
    def __init__(self, detail: str | dict, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(status_code=status_code, detail=detail)


class InvalidCredentialsException(AuthException):
    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(
            detail={"error_code": "invalid_credentials", "message": message},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class UserAlreadyExistsException(AuthException):
    def __init__(self, message: str = "User already exists") -> None:
        super().__init__(
            detail={"error_code": "user_already_exists", "message": message},
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidTokenException(AuthException):
    def __init__(self, message: str = "Could not validate token") -> None:
        super().__init__(
            detail={"error_code": "invalid_token", "message": message},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class UserNotFoundException(AuthException):
    def __init__(self, message: str = "User not found") -> None:
        super().__init__(
            detail={"error_code": "user_not_found", "message": message},
            status_code=status.HTTP_404_NOT_FOUND,
        )
