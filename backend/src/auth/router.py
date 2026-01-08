from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.requests import Request

from src.auth import schemas, service
from src.auth.constants import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_MINUTES
from src.auth.dependencies import get_current_user
from src.auth.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from src.database import get_session
from src.exceptions import RateLimitExceededCustomException
from src.service import rate_limiter
from src.utils import generate_error_response, merge_responses

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    responses=merge_responses(
        generate_error_response(UserAlreadyExistsException, "User with same credentials already exists"),
        generate_error_response(RateLimitExceededCustomException),
    ),
)
@rate_limiter.limit("3/15minute")
async def signup(
    user_create: schemas.UserCreate, db: Annotated[AsyncSession, Depends(get_session)], request: Request
) -> schemas.User:
    user = await service.create_user(db, user_create)
    return user


@router.post(
    "/login",
    response_model=schemas.AuthResponse,
    responses=merge_responses(
        generate_error_response(InvalidCredentialsException, "Invalid username or password"),
        generate_error_response(RateLimitExceededCustomException),
    ),
)
@rate_limiter.limit("5/15minute")
async def login(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_session)],
    request: Request,
) -> schemas.AuthResponse:
    user = await service.authenticate_user(db, form_data.username, form_data.password)
    token = await service.create_token_for_user(db, user)

    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
    )

    return schemas.AuthResponse(msg="Login successful")


@router.get("/me", response_model=schemas.User, responses=generate_error_response(InvalidTokenException))
async def get_current_user_info(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
) -> schemas.User:
    return current_user


@router.post(
    "/token/refresh",
    response_model=schemas.AuthResponse,
    responses=merge_responses(
        generate_error_response(InvalidTokenException),
        generate_error_response(UserNotFoundException, "User not found"),
        generate_error_response(RateLimitExceededCustomException),
    ),
)
@rate_limiter.limit("10/15minute")
async def refresh_token(
    response: Response,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.AuthResponse:
    """
    refresh access token using a valid refresh token and implements token rotation
    """
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise InvalidTokenException("Refresh token not found in cookies")

    token = await service.refresh_access_token(db, refresh_token_value)

    response.set_cookie(
        key="access_token",
        value=token.access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=REFRESH_TOKEN_EXPIRE_MINUTES * 60,
    )

    return schemas.AuthResponse(msg="Token refreshed successfully")


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=generate_error_response(InvalidTokenException, "Refresh token not found or does not belong to this user"),
)
async def logout(
    response: Response,
    request: Request,
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """
    Logs out from current session by revoking the refresh token

    Takes:
    - Access token from cookies
    - Refresh token from cookies
    """
    refresh_token_value = request.cookies.get("refresh_token")
    if refresh_token_value:
        await service.revoke_user_refresh_token(db, current_user.id, refresh_token_value)

    response.delete_cookie(key="access_token", secure=True, samesite="strict", httponly=True)
    response.delete_cookie(key="refresh_token", secure=True, samesite="strict", httponly=True)


@router.post(
    "/logout/all", status_code=status.HTTP_204_NO_CONTENT, responses=generate_error_response(InvalidTokenException)
)
async def logout_all_devices(
    response: Response,
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """
    logs out from all devices by revoking all refresh tokens for the user

    takes:
    - Access token from cookies
    """
    await service.revoke_all_user_tokens(db, current_user.id)

    # Clear cookies
    response.delete_cookie(key="access_token", secure=True, samesite="strict", httponly=True)
    response.delete_cookie(key="refresh_token", secure=True, samesite="strict", httponly=True)
