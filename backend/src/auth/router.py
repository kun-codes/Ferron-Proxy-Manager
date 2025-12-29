from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.requests import Request

from src.auth import schemas, service, models
from src.auth.dependencies import get_current_user
from src.auth.exceptions import UserAlreadyExistsException, InvalidCredentialsException, InvalidTokenException, UserNotFoundException
from src.database import get_session
from src.service import rate_limiter
from src.utils import generate_error_response, merge_responses

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    responses=generate_error_response(UserAlreadyExistsException, "User with same credentials already exists")
)
@rate_limiter.limit("3/15minute")
async def signup(
    user_create: schemas.UserCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
    request: Request
) -> schemas.User:
    user = await service.create_user(db, user_create)
    return user


@router.post(
    "/login",
    response_model=schemas.Token,
    responses=generate_error_response(InvalidCredentialsException, "Invalid username or password")
)
@rate_limiter.limit("5/15minute")
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_session)],
    request: Request
) -> schemas.Token:
    user = await service.authenticate_user(db, form_data.username, form_data.password)
    return await service.create_token_for_user(db, user)


@router.get(
    "/me",
    response_model=schemas.User,
    responses=generate_error_response(InvalidTokenException)
)
async def get_current_user_info(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
) -> schemas.User:
    return current_user


@router.post(
    "/token/refresh",
    response_model=schemas.Token,
    responses=merge_responses(
        generate_error_response(InvalidTokenException),
        generate_error_response(UserNotFoundException, "User not found")
    )
)
@rate_limiter.limit("10/15minute")
async def refresh_token(
    refresh_data: schemas.RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    request: Request
) -> schemas.Token:
    """
    refresh access token using a valid refresh token and implements token rotation
    """
    return await service.refresh_access_token(db, refresh_data.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=generate_error_response(InvalidTokenException, "Refresh token not found or does not belong to this user")
)
async def logout(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    refresh_data: schemas.RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """
    Logs out from current session by revoking the refresh token

    Takes:
    - Access token from Authorization header
    - Refresh token from request body
    """
    await service.revoke_user_refresh_token(db, current_user.id, refresh_data.refresh_token)


@router.post(
    "/logout/all",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=generate_error_response(InvalidTokenException)
)
async def logout_all_devices(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """
    logs out from all devices by revoking all refresh tokens for the user
    
    takes:
    - Access token only from Authorization header
    """
    await service.revoke_all_user_tokens(db, current_user.id)
