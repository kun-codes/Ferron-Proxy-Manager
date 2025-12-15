from typing import Annotated

from fastapi import Depends
from loguru import logger
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from src.ferron import models, schemas, exceptions
from src.database import get_session


async def create_global_config(
    global_config_data: schemas.GlobalTemplateConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> models.GlobalConfig:
    try:
        _existing_config = await read_global_config(session)
    except exceptions.ConfigNotFound:
        global_config = models.GlobalConfig(**global_config_data.model_dump(exclude_defaults=True))
        session.add(global_config)
        await session.commit()
        await session.refresh(global_config)

        return global_config
    else:
        logger.warning("GlobalConfig already exists. Creation skipped.")
        raise exceptions.GlobalConfigAlreadyExists()

async def update_global_config(
        global_config_data: schemas.GlobalTemplateConfig,
        session: Annotated[AsyncSession, Depends(get_session)]
) -> models.GlobalConfig:
    existing_config = await read_global_config(session)

    update_data = global_config_data.model_dump(exclude_defaults=True)
    for field, value  in update_data.items():
        setattr(existing_config, field, value)

    session.add(existing_config)
    await session.commit()
    await session.refresh(existing_config)

    return existing_config

async def read_global_config(
        session: Annotated[AsyncSession, Depends(get_session)]
) -> models.GlobalConfig | None:
    statement = select(models.GlobalConfig).where(models.GlobalConfig.id == 1)

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="global configuration")
    return config
