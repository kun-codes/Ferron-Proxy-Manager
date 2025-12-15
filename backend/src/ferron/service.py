from typing import Annotated

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from src.ferron import models, schemas, exceptions
from src.database import get_session
from src.ferron.constants import TemplateType, ConfigFileLocation
from src.ferron.utils import render_template, write_config, read_config


async def create_global_config(
    global_config_data: schemas.GlobalTemplateConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> models.GlobalConfig:
    try:
        _existing_config = await read_global_config(session)
    except exceptions.ConfigNotFound:
        # committing to db
        global_config = models.GlobalConfig(**global_config_data.model_dump(exclude_defaults=True))
        session.add(global_config)

        # writing to config files
        main_config_text = await read_config(ConfigFileLocation.MAIN_CONFIG.value)

        ## writing to global config
        rendered_config = await render_template(
            TemplateType.GLOBAL_CONFIG, global_config_data
        )

        await write_config(ConfigFileLocation.GLOBAL_CONFIG.value, rendered_config)

        ## checking if main config has include statement for global config
        has_include_statement = False
        for line in main_config_text.splitlines():
            if line.strip() == f"include \"{ConfigFileLocation.GLOBAL_CONFIG.value}\"":
                has_include_statement = True
                break

        if not has_include_statement:
            new_main_config_text = main_config_text + f"\ninclude \"{ConfigFileLocation.GLOBAL_CONFIG.value}\""
            await write_config(ConfigFileLocation.MAIN_CONFIG.value, new_main_config_text)

        # committing at last so that if any error happens in file operations, database doesn't have false data
        await session.commit()
        await session.refresh(global_config)

        return global_config
    else:
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
