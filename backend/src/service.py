from typing import Annotated

from fastapi import Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
from src.ferron import models, schemas, service

rate_limiter = Limiter(key_func=get_remote_address)


async def create_ferron_global_config(session: Annotated[AsyncSession, Depends(get_session)]) -> None:
    # have to write this function again instead of reusing read_global_config() from src/ferron/service.py because
    # it throws an exception if no global configuration is present, which is not desirable here
    statement = select(models.GlobalConfig).where(models.GlobalConfig.id == 1)
    result = await session.exec(statement)
    existing_config = result.scalar_one_or_none()

    if not existing_config:
        await service.create_global_config(schemas.GlobalTemplateConfig(), session)
