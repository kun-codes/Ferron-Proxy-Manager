from fastapi import HTTPException, status


class AuthException(HTTPException):

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class InvalidCredentialsException(AuthException):
    def __init__(self, detail: str = "Invalid username or password"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        self.headers = {"WWW-Authenticate": "Bearer"}


class UserAlreadyExistsException(AuthException):
    def __init__(self, detail: str = "User already exists"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidTokenException(AuthException):
    def __init__(self, detail: str = "Could not validate token"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
        self.headers = {"WWW-Authenticate": "Bearer"}


class UserNotFoundException(AuthException):
    def __init__(self, detail: str = "User not found"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
        )
