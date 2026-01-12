from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import EmailStr
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import models, schemas
from src.auth.config import auth_settings
from src.auth.constants import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, REFRESH_TOKEN_EXPIRE_MINUTES
from src.auth.exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from src.auth.utils import create_access_token, create_refresh_token, get_password_hash, verify_password
from src.exceptions import InvalidTokenException


async def get_user_by_username(db: AsyncSession, username: str) -> models.User | None:
    statement = select(models.User).where(models.User.username == username)
    result = await db.exec(statement)
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: EmailStr) -> models.User | None:
    statement = select(models.User).where(models.User.email == email)
    result = await db.exec(statement)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_create: schemas.UserCreate) -> schemas.User:
    # Check if user already exists
    if await get_user_by_username(db, user_create.username):
        raise UserAlreadyExistsException("User with same credentials already exists")

    if await get_user_by_email(db, user_create.email):
        raise UserAlreadyExistsException("User with same credentials already exists")

    hashed_password = get_password_hash(user_create.password.get_secret_value())

    db_user = models.User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    db_user_schema = schemas.User.model_validate(db_user)
    return db_user_schema


async def authenticate_user(db: AsyncSession, username: str, password: str) -> models.User:
    user = await get_user_by_username(db, username)
    if not user:
        raise InvalidCredentialsException("Invalid username or password")
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsException("Invalid username or password")
    return user


async def create_token_for_user(db: AsyncSession, user: models.User) -> schemas.Token:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    db_refresh_token = models.RefreshToken(
        token=refresh_token, user_id=user.id, expires_at=datetime.now(timezone.utc) + refresh_token_expires
    )
    db.add(db_refresh_token)
    await db.commit()

    return schemas.Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


async def get_user_from_token(db: AsyncSession, token: str) -> models.User:
    try:
        payload = jwt.decode(token, auth_settings.secret_key, algorithms=[ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("type")

        if username is None:
            raise InvalidTokenException("Invalid token payload")

        if token_type != "access":
            raise InvalidTokenException("Invalid token type. Expected access token")

    except InvalidTokenError:
        raise InvalidTokenException("Could not validate token")

    user = await get_user_by_username(db, username)
    if user is None:
        raise UserNotFoundException("User not found")
    return user


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> schemas.Token:
    """refreshes access token and returns new access and refresh token after refresh token rotation"""
    try:
        payload = jwt.decode(refresh_token, auth_settings.refresh_secret_key, algorithms=[ALGORITHM])
        username = payload.get("sub")
        token_type = payload.get("type")

        if username is None:
            raise InvalidTokenException("Invalid refresh token payload")

        if token_type != "refresh":
            raise InvalidTokenException("Invalid token type. Expected refresh token")

    except InvalidTokenError:
        raise InvalidTokenException("Invalid refresh token")

    statement = select(models.RefreshToken).where(models.RefreshToken.token == refresh_token)
    result = await db.exec(statement)
    token_in_db = result.scalar_one_or_none()

    if not token_in_db:
        raise InvalidTokenException("Refresh token not found or already revoked")

    expires_at = token_in_db.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        await db.delete(token_in_db)
        await db.commit()
        raise InvalidTokenException("Refresh token has expired")

    user = await get_user_by_username(db, username)
    if not user:
        raise UserNotFoundException("User not found")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    new_refresh_token = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    # token rotation
    await db.delete(token_in_db)
    db_refresh_token = models.RefreshToken(
        token=new_refresh_token, user_id=user.id, expires_at=datetime.now(timezone.utc) + refresh_token_expires
    )
    db.add(db_refresh_token)
    await db.commit()

    return schemas.Token(access_token=new_access_token, refresh_token=new_refresh_token, token_type="bearer")


async def revoke_user_refresh_token(db: AsyncSession, user_id: int, refresh_token: str) -> None:
    statement = select(models.RefreshToken).where(
        models.RefreshToken.token == refresh_token, models.RefreshToken.user_id == user_id
    )
    result = await db.exec(statement)
    token_in_db = result.scalar_one_or_none()

    if not token_in_db:
        raise InvalidTokenException("Refresh token not found or does not belong to this user")

    await db.delete(token_in_db)
    await db.commit()


async def revoke_all_user_tokens(db: AsyncSession, user_id: int) -> None:
    statement = select(models.RefreshToken).where(models.RefreshToken.user_id == user_id)
    result = await db.exec(statement)
    tokens = result.scalars().all()

    for token in tokens:
        await db.delete(token)

    await db.commit()
