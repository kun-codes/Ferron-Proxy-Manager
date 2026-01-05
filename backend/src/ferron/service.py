from typing import Annotated

import sqlalchemy.exc
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import get_session
from src.ferron import exceptions, models, schemas
from src.ferron.exceptions import VirtualHostNameAlreadyExists
from src.ferron.utils import (
    delete_load_balancer_config_from_file,
    delete_reverse_proxy_config_from_file,
    delete_static_file_config_from_file,
    reload_ferron_service,
    write_global_config_to_file,
    write_load_balancer_config_to_file,
    write_reverse_proxy_config_to_file,
    write_static_file_config_to_file,
)


def _reverse_proxy_to_schema(config: models.ReverseProxyConfig) -> schemas.UpdateReverseProxyConfig:
    return schemas.UpdateReverseProxyConfig.model_validate(config, from_attributes=True)


def _load_balancer_to_schema(config: models.LoadBalancerConfig) -> schemas.UpdateLoadBalancerConfig:
    return schemas.UpdateLoadBalancerConfig.model_validate(config, from_attributes=True)


def _static_file_to_schema(config: models.StaticFileConfig) -> schemas.UpdateStaticFileConfig:
    return schemas.UpdateStaticFileConfig.model_validate(config, from_attributes=True)


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

        await reload_ferron_service()

        return global_config_schema
    else:
        raise exceptions.GlobalConfigAlreadyExists()


async def update_global_config(
    global_config_data: schemas.GlobalTemplateConfig, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.GlobalTemplateConfig:
    statement = select(models.GlobalConfig).where(models.GlobalConfig.id == 1)
    result = await session.exec(statement)
    existing_config = result.scalar_one_or_none()

    if not existing_config:
        raise exceptions.ConfigNotFound(config_type="global configuration")

    update_data = global_config_data.model_dump(exclude_defaults=True)
    for field, value in update_data.items():
        setattr(existing_config, field, value)

    existing_config_schema = schemas.GlobalTemplateConfig.model_validate(existing_config)
    await write_global_config_to_file(existing_config_schema)

    await session.commit()

    await reload_ferron_service()

    return existing_config_schema


async def read_global_config(session: Annotated[AsyncSession, Depends(get_session)]) -> schemas.GlobalTemplateConfig:
    statement = select(models.GlobalConfig).where(models.GlobalConfig.id == 1)

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="global configuration")

    config_schema = schemas.GlobalTemplateConfig.model_validate(config)
    return config_schema


async def create_reverse_proxy_config(
    create_reverse_proxy_config_data: schemas.CreateReverseProxyConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateReverseProxyConfig:
    existing_virtual_host_stmt = select(models.VirtualHost).where(
        models.VirtualHost.virtual_host_name == create_reverse_proxy_config_data.virtual_host_name
    )
    existing_virtual_host = (await session.exec(existing_virtual_host_stmt)).scalar_one_or_none()

    if existing_virtual_host:
        raise VirtualHostNameAlreadyExists(virtual_host_name=create_reverse_proxy_config_data.virtual_host_name)

    virtual_host = models.VirtualHost(virtual_host_name=create_reverse_proxy_config_data.virtual_host_name)

    reverse_proxy_data = create_reverse_proxy_config_data.model_dump(
        exclude_defaults=True, exclude={"virtual_host_name"}
    )
    reverse_proxy_config = models.ReverseProxyConfig(virtual_host=virtual_host, **reverse_proxy_data)

    session.add(virtual_host)
    session.add(reverse_proxy_config)
    # have to flush to get id of the new reverse proxy config without committing it to the db
    try:
        await session.flush()
    except sqlalchemy.exc.IntegrityError:
        raise VirtualHostNameAlreadyExists(virtual_host_name=create_reverse_proxy_config_data.virtual_host_name)

    reverse_proxy_config_schema = _reverse_proxy_to_schema(reverse_proxy_config)

    await write_reverse_proxy_config_to_file(reverse_proxy_config_schema)

    await session.commit()

    await reload_ferron_service()

    return reverse_proxy_config_schema


async def update_reverse_proxy_config(
    reverse_proxy_config_data: schemas.UpdateReverseProxyConfig, session: Annotated[AsyncSession, Depends(get_session)]
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
            raise VirtualHostNameAlreadyExists(virtual_host_name=reverse_proxy_config_data.virtual_host_name)

        existing_config.virtual_host.virtual_host_name = reverse_proxy_config_data.virtual_host_name

    update_data = reverse_proxy_config_data.model_dump(exclude_defaults=True, exclude={"virtual_host_name", "id"})
    for field, value in update_data.items():
        setattr(existing_config, field, value)

    try:
        await session.flush()
    except sqlalchemy.exc.IntegrityError:
        raise VirtualHostNameAlreadyExists(virtual_host_name=reverse_proxy_config_data.virtual_host_name)

    existing_config_schema = _reverse_proxy_to_schema(existing_config)
    await write_reverse_proxy_config_to_file(existing_config_schema)

    await session.commit()

    await reload_ferron_service()

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
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[schemas.UpdateReverseProxyConfig]:
    statement = select(models.ReverseProxyConfig).options(selectinload(models.ReverseProxyConfig.virtual_host))

    result = await session.exec(statement)
    configs = result.scalars().all()

    return [_reverse_proxy_to_schema(config) for config in configs]


async def delete_reverse_proxy_config(
    reverse_proxy_id: int, session: Annotated[AsyncSession, Depends(get_session)]
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

    await reload_ferron_service()

    return _reverse_proxy_to_schema(config)


async def create_load_balancer_config(
    create_load_balancer_config_data: schemas.CreateLoadBalancerConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateLoadBalancerConfig:
    existing_virtual_host_stmt = select(models.VirtualHost).where(
        models.VirtualHost.virtual_host_name == create_load_balancer_config_data.virtual_host_name
    )
    existing_virtual_host = (await session.exec(existing_virtual_host_stmt)).scalar_one_or_none()

    if existing_virtual_host:
        raise VirtualHostNameAlreadyExists(virtual_host_name=create_load_balancer_config_data.virtual_host_name)

    virtual_host = models.VirtualHost(virtual_host_name=create_load_balancer_config_data.virtual_host_name)

    load_balancer_data = create_load_balancer_config_data.model_dump(
        exclude_defaults=True, exclude={"virtual_host_name", "backend_urls"}
    )
    load_balancer_config = models.LoadBalancerConfig(virtual_host=virtual_host, **load_balancer_data)

    session.add(virtual_host)
    session.add(load_balancer_config)

    try:
        await session.flush()
    except sqlalchemy.exc.IntegrityError:
        raise VirtualHostNameAlreadyExists(virtual_host_name=create_load_balancer_config_data.virtual_host_name)

    # Add backend URLs
    for backend_url in create_load_balancer_config_data.backend_urls:
        backend_record = models.LoadBalancerBackendURL(
            virtual_host=virtual_host, used_in_load_balancer=load_balancer_config.id, backend_url=backend_url
        )
        session.add(backend_record)

    await session.flush()

    # backend_urls is a property of the LoadBalancerConfig model that relies on a relationship,
    # have to refresh to get the backend_urls_relationship loaded.
    await session.refresh(load_balancer_config, attribute_names=["backend_urls_relationship", "virtual_host"])

    load_balancer_config_schema = _load_balancer_to_schema(load_balancer_config)

    await write_load_balancer_config_to_file(load_balancer_config_schema)

    await session.commit()

    await reload_ferron_service()

    return load_balancer_config_schema


async def update_load_balancer_config(
    load_balancer_config_data: schemas.UpdateLoadBalancerConfig, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateLoadBalancerConfig:
    statement = (
        select(models.LoadBalancerConfig)
        .options(
            selectinload(models.LoadBalancerConfig.virtual_host),
            selectinload(models.LoadBalancerConfig.backend_urls_relationship),
        )
        .where(models.LoadBalancerConfig.id == load_balancer_config_data.id)
    )

    result = await session.exec(statement)
    existing_config = result.scalar_one_or_none()

    if not existing_config:
        raise exceptions.ConfigNotFound(config_type="load balancer configuration")

    if not existing_config.virtual_host:
        raise exceptions.ConfigNotFound(config_type="load balancer configuration")

    if load_balancer_config_data.virtual_host_name != existing_config.virtual_host.virtual_host_name:
        conflicting_virtual_host_stmt = select(models.VirtualHost).where(
            models.VirtualHost.virtual_host_name == load_balancer_config_data.virtual_host_name
        )
        conflicting_virtual_host = (await session.exec(conflicting_virtual_host_stmt)).scalar_one_or_none()

        if conflicting_virtual_host and conflicting_virtual_host.id != existing_config.virtual_host.id:
            raise VirtualHostNameAlreadyExists(virtual_host_name=load_balancer_config_data.virtual_host_name)

        existing_config.virtual_host.virtual_host_name = load_balancer_config_data.virtual_host_name

    update_data = load_balancer_config_data.model_dump(
        exclude_defaults=True, exclude={"virtual_host_name", "id", "backend_urls"}
    )
    for field, value in update_data.items():
        setattr(existing_config, field, value)

    # Update backend URLs - delete existing and create new ones
    for backend in existing_config.backend_urls_relationship:
        await session.delete(backend)

    await session.flush()

    for backend_url in load_balancer_config_data.backend_urls:
        backend_record = models.LoadBalancerBackendURL(
            virtual_host=existing_config.virtual_host, used_in_load_balancer=existing_config.id, backend_url=backend_url
        )
        session.add(backend_record)

    try:
        await session.flush()
    except sqlalchemy.exc.IntegrityError:
        raise VirtualHostNameAlreadyExists(virtual_host_name=load_balancer_config_data.virtual_host_name)

    existing_config_schema = _load_balancer_to_schema(existing_config)
    await write_load_balancer_config_to_file(existing_config_schema)

    await session.commit()

    await reload_ferron_service()

    return existing_config_schema


async def read_load_balancer_config(
    load_balancer_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateLoadBalancerConfig:
    statement = (
        select(models.LoadBalancerConfig)
        .options(
            selectinload(models.LoadBalancerConfig.virtual_host),
            selectinload(models.LoadBalancerConfig.backend_urls_relationship),
        )
        .where(models.LoadBalancerConfig.id == load_balancer_id)
    )

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="load balancer configuration")

    config_schema = _load_balancer_to_schema(config)
    return config_schema


async def read_all_load_balancer_config(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[schemas.UpdateLoadBalancerConfig]:
    statement = select(models.LoadBalancerConfig).options(
        selectinload(models.LoadBalancerConfig.virtual_host),
        selectinload(models.LoadBalancerConfig.backend_urls_relationship),
    )

    result = await session.exec(statement)
    configs = result.scalars().all()

    return [_load_balancer_to_schema(config) for config in configs]


async def delete_load_balancer_config(
    load_balancer_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateLoadBalancerConfig:
    statement = (
        select(models.LoadBalancerConfig)
        .options(
            selectinload(models.LoadBalancerConfig.virtual_host),
            selectinload(models.LoadBalancerConfig.backend_urls_relationship),
        )
        .where(models.LoadBalancerConfig.id == load_balancer_id)
    )

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="load balancer configuration")

    if config.virtual_host:
        await session.delete(config.virtual_host)
    else:
        await session.delete(config)

    await session.commit()
    await delete_load_balancer_config_from_file(load_balancer_id)

    await reload_ferron_service()

    return _load_balancer_to_schema(config)


async def create_static_file_config(
    create_static_file_config_data: schemas.CreateStaticFileConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateStaticFileConfig:
    existing_virtual_host_stmt = select(models.VirtualHost).where(
        models.VirtualHost.virtual_host_name == create_static_file_config_data.virtual_host_name
    )
    existing_virtual_host = (await session.exec(existing_virtual_host_stmt)).scalar_one_or_none()

    if existing_virtual_host:
        raise VirtualHostNameAlreadyExists(virtual_host_name=create_static_file_config_data.virtual_host_name)

    virtual_host = models.VirtualHost(virtual_host_name=create_static_file_config_data.virtual_host_name)

    static_file_data = create_static_file_config_data.model_dump(exclude_defaults=True, exclude={"virtual_host_name"})
    static_file_config = models.StaticFileConfig(virtual_host=virtual_host, **static_file_data)

    session.add(virtual_host)
    session.add(static_file_config)

    # have to flush to get id of the new static file config without committing it to the db
    try:
        await session.flush()
    except sqlalchemy.exc.IntegrityError:
        raise VirtualHostNameAlreadyExists(virtual_host_name=create_static_file_config_data.virtual_host_name)

    static_file_config_schema = _static_file_to_schema(static_file_config)

    await write_static_file_config_to_file(static_file_config_schema)

    await session.commit()

    await reload_ferron_service()

    return static_file_config_schema


async def update_static_file_config(
    static_file_config_data: schemas.UpdateStaticFileConfig, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateStaticFileConfig:
    statement = (
        select(models.StaticFileConfig)
        .options(selectinload(models.StaticFileConfig.virtual_host))
        .where(models.StaticFileConfig.id == static_file_config_data.id)
    )

    result = await session.exec(statement)
    existing_config = result.scalar_one_or_none()

    if not existing_config:
        raise exceptions.ConfigNotFound(config_type="static file configuration")

    if not existing_config.virtual_host:
        raise exceptions.ConfigNotFound(config_type="static file configuration")

    if static_file_config_data.virtual_host_name != existing_config.virtual_host.virtual_host_name:
        conflicting_virtual_host_stmt = select(models.VirtualHost).where(
            models.VirtualHost.virtual_host_name == static_file_config_data.virtual_host_name
        )
        conflicting_virtual_host = (await session.exec(conflicting_virtual_host_stmt)).scalar_one_or_none()

        if conflicting_virtual_host and conflicting_virtual_host.id != existing_config.virtual_host.id:
            raise VirtualHostNameAlreadyExists(virtual_host_name=static_file_config_data.virtual_host_name)

        existing_config.virtual_host.virtual_host_name = static_file_config_data.virtual_host_name

    update_data = static_file_config_data.model_dump(exclude_defaults=True, exclude={"virtual_host_name", "id"})
    for field, value in update_data.items():
        setattr(existing_config, field, value)

    try:
        await session.flush()
    except sqlalchemy.exc.IntegrityError:
        raise VirtualHostNameAlreadyExists(virtual_host_name=static_file_config_data.virtual_host_name)

    existing_config_schema = _static_file_to_schema(existing_config)
    await write_static_file_config_to_file(existing_config_schema)

    await session.commit()

    await reload_ferron_service()

    return existing_config_schema


async def read_static_file_config(
    static_file_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateStaticFileConfig:
    statement = (
        select(models.StaticFileConfig)
        .options(selectinload(models.StaticFileConfig.virtual_host))
        .where(models.StaticFileConfig.id == static_file_id)
    )

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="static file configuration")

    config_schema = _static_file_to_schema(config)
    return config_schema


async def read_all_static_file_config(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[schemas.UpdateStaticFileConfig]:
    statement = select(models.StaticFileConfig).options(selectinload(models.StaticFileConfig.virtual_host))

    result = await session.exec(statement)
    configs = result.scalars().all()

    return [_static_file_to_schema(config) for config in configs]


async def delete_static_file_config(
    static_file_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateStaticFileConfig:
    statement = (
        select(models.StaticFileConfig)
        # lazy=selectin because https://stackoverflow.com/a/74256068
        # selectinload because https://stackoverflow.com/a/74256068
        .options(selectinload(models.StaticFileConfig.virtual_host))
        .where(models.StaticFileConfig.id == static_file_id)
    )

    result = await session.exec(statement)
    config = result.scalar_one_or_none()

    if not config:
        raise exceptions.ConfigNotFound(config_type="static file configuration")

    if config.virtual_host:
        await session.delete(config.virtual_host)
    else:
        await session.delete(config)

    # delete config file only after successfully deleted from db
    await session.commit()
    await delete_static_file_config_from_file(static_file_id)

    await reload_ferron_service()

    return _static_file_to_schema(config)
