from typing import Annotated

import sqlalchemy.exc

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.ferron import models, schemas, exceptions
from src.database import get_session
from src.ferron.exceptions import VirtualHostNameAlreadyExists
from src.ferron.utils import write_global_config_to_file, write_reverse_proxy_config_to_file, \
    delete_reverse_proxy_config_from_file


def _reverse_proxy_to_schema(config: models.ReverseProxyConfig) -> schemas.UpdateReverseProxyConfig:
    # Use Pydantic's ORM mode to map the already-loaded model (including its virtual_host) into the schema.
    return schemas.UpdateReverseProxyConfig.model_validate(config, from_attributes=True)


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
    existing_virtual_host_stmt = select(models.VirtualHost).where(
        models.VirtualHost.virtual_host_name == create_reverse_proxy_config_data.virtual_host_name
    )
    existing_virtual_host = (await session.exec(existing_virtual_host_stmt)).scalar_one_or_none()

    if existing_virtual_host:
        raise VirtualHostNameAlreadyExists(
            virtual_host_name=create_reverse_proxy_config_data.virtual_host_name
        )

    virtual_host = models.VirtualHost(virtual_host_name=create_reverse_proxy_config_data.virtual_host_name)

    reverse_proxy_data = create_reverse_proxy_config_data.model_dump(exclude_defaults=True, exclude={"virtual_host_name"})
    reverse_proxy_config = models.ReverseProxyConfig(
        virtual_host=virtual_host,
        **reverse_proxy_data
    )

    session.add(virtual_host)
    session.add(reverse_proxy_config)
    # have to flush to get id of the new reverse proxy config without committing it to the db
    try:
        await session.flush()
    except sqlalchemy.exc.IntegrityError:
        raise VirtualHostNameAlreadyExists(
            virtual_host_name=create_reverse_proxy_config_data.virtual_host_name
        )

    reverse_proxy_config_schema = _reverse_proxy_to_schema(reverse_proxy_config)

    await write_reverse_proxy_config_to_file(reverse_proxy_config_schema)

    await session.commit()

    return reverse_proxy_config_schema

async def update_reverse_proxy_config(
        reverse_proxy_config_data: schemas.UpdateReverseProxyConfig,
        session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateReverseProxyConfig:
    # have to do this to check if id specified in reverse_proxy_config_data exists
    statement = (
        select(models.ReverseProxyConfig)
        .options(selectinload(models.ReverseProxyConfig.virtual_host))
        .where(models.ReverseProxyConfig.id == reverse_proxy_config_data.id)
    )

    result = await session.exec(statement)
    existing_config = result.scalar_one_or_none()

    if not existing_config:
        raise exceptions.ConfigNotFound(config_type="reverse proxy configuration")

    if not existing_config.virtual_host:
        raise exceptions.ConfigNotFound(config_type="reverse proxy configuration")

    if reverse_proxy_config_data.virtual_host_name != existing_config.virtual_host.virtual_host_name:
        conflicting_virtual_host_stmt = select(models.VirtualHost).where(
            models.VirtualHost.virtual_host_name == reverse_proxy_config_data.virtual_host_name
        )
        conflicting_virtual_host = (await session.exec(conflicting_virtual_host_stmt)).scalar_one_or_none()

        if conflicting_virtual_host and conflicting_virtual_host.id != existing_config.virtual_host.id:
            raise VirtualHostNameAlreadyExists(
                virtual_host_name=reverse_proxy_config_data.virtual_host_name
            )

        existing_config.virtual_host.virtual_host_name = reverse_proxy_config_data.virtual_host_name

    update_data = reverse_proxy_config_data.model_dump(exclude_defaults=True, exclude={"virtual_host_name", "id"})
    for field, value in update_data.items():
        setattr(existing_config, field, value)

    session.add(existing_config)

    try:
        await session.flush()
    except sqlalchemy.exc.IntegrityError:
        raise VirtualHostNameAlreadyExists(
            virtual_host_name=reverse_proxy_config_data.virtual_host_name
        )

    existing_config_schema = _reverse_proxy_to_schema(existing_config)
    await write_reverse_proxy_config_to_file(existing_config_schema)

    await session.commit()

    return existing_config_schema

async def read_reverse_proxy_config(
        reverse_proxy_id: int,
        session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateReverseProxyConfig:
    statement = (
        select(models.ReverseProxyConfig)
        .options(selectinload(models.ReverseProxyConfig.virtual_host))
        .where(models.ReverseProxyConfig.id == reverse_proxy_id)
    )

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="reverse proxy configuration")

    config_schema = _reverse_proxy_to_schema(config)
    return config_schema

async def read_all_reverse_proxy_config(
        session: Annotated[AsyncSession, Depends(get_session)]
) -> list[models.ReverseProxyConfig]:
    statement = select(models.ReverseProxyConfig).options(selectinload(models.ReverseProxyConfig.virtual_host))

    result = await session.exec(statement)
    configs = result.all()

    return [_reverse_proxy_to_schema(config) for config in configs]


async def delete_reverse_proxy_config(
        reverse_proxy_id: int,
        session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateReverseProxyConfig:
    statement = (
        select(models.ReverseProxyConfig)
        # lazy=selectin because https://stackoverflow.com/a/74256068
        # selectinload because https://stackoverflow.com/a/74256068
        .options(selectinload(models.ReverseProxyConfig.virtual_host))
        .where(models.ReverseProxyConfig.id == reverse_proxy_id)
    )

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="reverse proxy configuration")

    if config.virtual_host:
        await session.delete(config.virtual_host)
    else:
        await session.delete(config)

    # delete config file only after successfully deleted from db
    await session.commit()
    await delete_reverse_proxy_config_from_file(reverse_proxy_id)

    return _reverse_proxy_to_schema(config)
