from fastapi import Cookie, Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.auth import schemas, service
from src.auth.exceptions import InvalidTokenException
from src.database import get_session


async def get_current_user(
    access_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_session),
) -> schemas.User:
    if not access_token:
        raise InvalidTokenException("Access token not found in cookies")

    user = await service.get_user_from_token(db, access_token)
    return schemas.User.model_validate(user)
