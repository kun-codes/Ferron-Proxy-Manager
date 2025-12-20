from typing import Annotated


from aiofiles import os as aiofiles_os

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select

from src.ferron import models, schemas, exceptions
from src.database import get_session
from src.ferron.constants import TemplateType, ConfigFileLocation, SUB_CONFIG_PATH
from src.ferron.utils import render_template, write_config, read_config, write_global_config_to_file


async def create_global_config(
    global_config_data: schemas.GlobalTemplateConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.GlobalTemplateConfig:
    try:
        _existing_config = await read_global_config(session)
    except exceptions.ConfigNotFound:
        # committing to db
        global_config = models.GlobalConfig(**global_config_data.model_dump(exclude_defaults=True))
        session.add(global_config)

        await write_global_config_to_file(global_config_data)

        # committing at last so that if any error happens in file operations, database doesn't have false data
        await session.commit()
        await session.refresh(global_config)

        global_config_schema = schemas.GlobalTemplateConfig.model_validate(global_config)

        return global_config_schema
    else:
        raise exceptions.GlobalConfigAlreadyExists()

async def update_global_config(
        global_config_data: schemas.GlobalTemplateConfig,
        session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.GlobalTemplateConfig:
    statement = select(models.GlobalConfig).where(models.GlobalConfig.id == 1)
    result = await session.exec(statement)
    existing_config = result.scalar_one_or_none()

    if not existing_config:
        raise exceptions.ConfigNotFound(config_type="global configuration")

    update_data = global_config_data.model_dump(exclude_defaults=True)
    for field, value  in update_data.items():
        setattr(existing_config, field, value)

    session.add(existing_config)

    existing_config_schema = schemas.GlobalTemplateConfig.model_validate(existing_config)
    await write_global_config_to_file(existing_config_schema)

    await session.commit()
    await session.refresh(existing_config)

    return existing_config_schema

async def read_global_config(
        session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.GlobalTemplateConfig:
    statement = select(models.GlobalConfig).where(models.GlobalConfig.id == 1)

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="global configuration")

    config_schema = schemas.GlobalTemplateConfig.model_validate(config)
    return config_schema

async def create_reverse_proxy_config(
        create_reverse_proxy_config_data: schemas.CreateReverseProxyConfig,
        session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateReverseProxyConfig:
    reverse_proxy_config = models.ReverseProxyConfig(**create_reverse_proxy_config_data.model_dump(exclude_defaults=True))

    session.add(reverse_proxy_config)
    # have to flush to get id of the new reverse proxy config without committing it to the db
    await session.flush()
    id_no = reverse_proxy_config.id

    # this has id too which is used by write_reverse_proxy_config_to_file to name the file which the config would be
    # written to
    reverse_proxy_config_to_file = schemas.UpdateReverseProxyConfig(id=id_no, **create_reverse_proxy_config_data.model_dump())

    await write_reverse_proxy_config_to_file(reverse_proxy_config_to_file)

    await session.commit()
    await session.refresh(reverse_proxy_config)

    # using UpdateReverseProxyConfig because returning id of new reverse proxy config too
    reverse_proxy_config_schema = schemas.UpdateReverseProxyConfig.model_validate(reverse_proxy_config_to_file)

    return reverse_proxy_config_schema

async def update_reverse_proxy_config(
        reverse_proxy_config_data: schemas.UpdateReverseProxyConfig,
        session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateReverseProxyConfig:
    # have to do this to check if id specified in reverse_proxy_config_data exists
    statement = select(models.ReverseProxyConfig).where(models.ReverseProxyConfig.id == reverse_proxy_config_data.id)

    result = await session.exec(statement)
    existing_config = result.scalar_one_or_none()

    if not existing_config:
        raise exceptions.ConfigNotFound(config_type="reverse proxy configuration")

    update_data = reverse_proxy_config_data.model_dump(exclude_defaults=True)
    for field, value  in update_data.items():
        setattr(existing_config, field, value)

    session.add(existing_config)

    existing_config_schema = schemas.UpdateReverseProxyConfig.model_validate(existing_config)
    await write_reverse_proxy_config_to_file(existing_config_schema)

    await session.commit()
    await session.refresh(existing_config)

    return existing_config_schema

async def write_reverse_proxy_config_to_file(reverse_proxy_config_data: schemas.UpdateReverseProxyConfig) -> None:
    """
    helper function to write reverse proxy config to config file
    """
    main_config_text = await read_config(ConfigFileLocation.MAIN_CONFIG.value)

    rendered_config = await render_template(
        TemplateType.REVERSE_PROXY_CONFIG, reverse_proxy_config_data
    )

    await write_config(
        f"{SUB_CONFIG_PATH}/{reverse_proxy_config_data.id}_reverse_proxy.kdl",
        rendered_config
    )

    has_include_statement = False
    for line in main_config_text.splitlines():
        if line.strip() == f"include \"{SUB_CONFIG_PATH}/{reverse_proxy_config_data.id}_reverse_proxy.kdl\"":
            has_include_statement = True
            break

    if not has_include_statement:
        new_main_config_text = main_config_text + f"\ninclude \"{SUB_CONFIG_PATH}/{reverse_proxy_config_data.id}_reverse_proxy.kdl\""
        await write_config(ConfigFileLocation.MAIN_CONFIG.value, new_main_config_text)


async def read_reverse_proxy_config(
        reverse_proxy_id: int,
        session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateReverseProxyConfig:
    statement = select(models.ReverseProxyConfig).where(models.ReverseProxyConfig.id == reverse_proxy_id)

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="reverse proxy configuration")

    config_schema = schemas.UpdateReverseProxyConfig.model_validate(config)
    return config_schema

async def read_all_reverse_proxy_config(
        session: Annotated[AsyncSession, Depends(get_session)]
) -> list[models.ReverseProxyConfig]:
    statement = select(models.ReverseProxyConfig)

    result = await session.exec(statement)
    configs = result.all()

    return list(configs)


async def delete_reverse_proxy_config(
        reverse_proxy_id: int,
        session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateReverseProxyConfig:
    statement = select(models.ReverseProxyConfig).where(models.ReverseProxyConfig.id == reverse_proxy_id)

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="reverse proxy configuration")

    await session.delete(config)

    # delete config file only after successfully deleted from db
    await session.commit()
    await delete_reverse_proxy_config_from_file(reverse_proxy_id)

    config_schema = schemas.UpdateReverseProxyConfig.model_validate(config)
    return config_schema

async def delete_reverse_proxy_config_from_file(reverse_proxy_id: int) -> None:
    main_config_text = await read_config(ConfigFileLocation.MAIN_CONFIG.value)

    new_main_config_text = main_config_text.replace(f"include \"{SUB_CONFIG_PATH}/{reverse_proxy_id}_reverse_proxy.kdl\"", "")
    await write_config(ConfigFileLocation.MAIN_CONFIG.value, new_main_config_text)

    await aiofiles_os.remove(f"{SUB_CONFIG_PATH}/{reverse_proxy_id}_reverse_proxy.kdl")
