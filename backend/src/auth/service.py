from datetime import timedelta

import jwt
from jwt.exceptions import InvalidTokenError
from pydantic import EmailStr
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import models, schemas
from src.auth.config import auth_settings
from src.auth.constants import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM
from src.auth.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from src.auth.utils import create_access_token, get_password_hash, verify_password


async def get_user_by_username(db: AsyncSession, username: str) -> models.User | None:
    statement = select(models.User).where(models.User.username == username)
    result = await db.exec(statement)
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: EmailStr) -> models.User | None:
    statement = select(models.User).where(models.User.email == email)
    result = await db.exec(statement)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_create: schemas.UserCreate) -> models.User:
    # Check if user already exists
    if await get_user_by_username(db, user_create.username):
        raise UserAlreadyExistsException("User with same credentials already exists")
    
    if await get_user_by_email(db, user_create.email):
        raise UserAlreadyExistsException("User with same credentials already exists")
    
    hashed_password = get_password_hash(user_create.password)
    db_user = models.User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> models.User:
    user = await get_user_by_username(db, username)
    if not user:
        raise InvalidCredentialsException("Invalid username or password")
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsException("Invalid username or password")
    return user


def create_token_for_user(user: models.User) -> schemas.Token:
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return schemas.Token(access_token=access_token, token_type="bearer")


async def get_user_from_token(db: AsyncSession, token: str) -> models.User:
    try:
        payload = jwt.decode(token, auth_settings.secret_key, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise InvalidTokenException("Invalid token payload")
    except InvalidTokenError:
        raise InvalidTokenException("Could not validate token")
    
    user = await get_user_by_username(db, username)
    if user is None:
        raise UserNotFoundException("User not found")
    return user
