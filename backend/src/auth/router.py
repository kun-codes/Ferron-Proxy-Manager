from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import schemas, service
from src.auth.dependencies import get_current_user
from src.database import get_session


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def signup(
    user_create: schemas.UserCreate,
    db: Annotated[AsyncSession, Depends(get_session)],
):
    user = await service.create_user(db, user_create)
    return user


@router.post("/login", response_model=schemas.Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_session)],
):
    user = await service.authenticate_user(db, form_data.username, form_data.password)
    return service.create_token_for_user(user)


@router.get("/me", response_model=schemas.User)
async def get_current_user_info(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    return current_user
