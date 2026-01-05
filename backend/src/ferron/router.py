from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.config import settings
from src.database import get_session
from src.ferron import schemas, service
from src.ferron.exceptions import (
    ConfigNotFound,
    FerronContainerNotFoundException,
    GlobalConfigAlreadyExists,
    VirtualHostNameAlreadyExists,
)
from src.utils import generate_error_response, merge_responses

router = APIRouter(prefix="/configs", tags=["ferron-config"], dependencies=[Depends(get_current_user)])


@router.get("/global", responses=generate_error_response(ConfigNotFound, "global configuration"))
async def read_global_config(session: Annotated[AsyncSession, Depends(get_session)]) -> schemas.GlobalTemplateConfig:
    config = await service.read_global_config(session)
    return config


@router.post(
    "/global",
    responses=merge_responses(
        generate_error_response(GlobalConfigAlreadyExists),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def create_global_config(
    global_config_data: schemas.GlobalTemplateConfig, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.GlobalTemplateConfig:
    config = await service.create_global_config(global_config_data, session)
    return config


@router.patch(
    "/global",
    responses=merge_responses(
        generate_error_response(ConfigNotFound, "global configuration"),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def update_global_config(
    global_config_data: schemas.GlobalTemplateConfig, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.GlobalTemplateConfig:
    config = await service.update_global_config(global_config_data, session)
    return config


@router.post(
    "/reverse-proxy",
    responses=merge_responses(
        generate_error_response(VirtualHostNameAlreadyExists),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def create_reverse_proxy_config(
    create_reverse_proxy_config_data: schemas.CreateReverseProxyConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateReverseProxyConfig:
    config = await service.create_reverse_proxy_config(create_reverse_proxy_config_data, session)
    return config


@router.patch(
    "/reverse-proxy",
    responses=merge_responses(
        generate_error_response(ConfigNotFound, "reverse proxy configuration"),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def update_reverse_proxy_config(
    update_reverse_proxy_config_data: schemas.UpdateReverseProxyConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateReverseProxyConfig:
    config = await service.update_reverse_proxy_config(update_reverse_proxy_config_data, session)
    return config


@router.get("/reverse-proxy", responses=generate_error_response(ConfigNotFound, "reverse proxy configuration"))
async def read_reverse_proxy_config(
    reverse_proxy_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateReverseProxyConfig:
    config = await service.read_reverse_proxy_config(reverse_proxy_id, session)
    return config


@router.get(
    "/reverse-proxy/all",
)
async def read_all_reverse_proxy_config(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[schemas.UpdateReverseProxyConfig]:
    return await service.read_all_reverse_proxy_config(session=session)


@router.delete(
    "/reverse-proxy",
    responses=merge_responses(
        generate_error_response(ConfigNotFound, "reverse proxy configuration"),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def delete_reverse_proxy_config(
    reverse_proxy_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateReverseProxyConfig:
    config = await service.delete_reverse_proxy_config(reverse_proxy_id, session)
    return config


@router.post(
    "/load-balancer",
    responses=merge_responses(
        generate_error_response(VirtualHostNameAlreadyExists),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def create_load_balancer_config(
    create_load_balancer_config_data: schemas.CreateLoadBalancerConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateLoadBalancerConfig:
    config = await service.create_load_balancer_config(create_load_balancer_config_data, session)
    return config


@router.patch(
    "/load-balancer",
    responses=merge_responses(
        generate_error_response(ConfigNotFound, "load balancer configuration"),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def update_load_balancer_config(
    update_load_balancer_config_data: schemas.UpdateLoadBalancerConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateLoadBalancerConfig:
    config = await service.update_load_balancer_config(update_load_balancer_config_data, session)
    return config


@router.get("/load-balancer", responses=generate_error_response(ConfigNotFound, "load balancer configuration"))
async def read_load_balancer_config(
    load_balancer_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateLoadBalancerConfig:
    config = await service.read_load_balancer_config(load_balancer_id, session)
    return config


@router.get(
    "/load-balancer/all",
)
async def read_all_load_balancer_config(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[schemas.UpdateLoadBalancerConfig]:
    return await service.read_all_load_balancer_config(session=session)


@router.delete(
    "/load-balancer",
    responses=merge_responses(
        generate_error_response(ConfigNotFound, "load balancer configuration"),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def delete_load_balancer_config(
    load_balancer_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateLoadBalancerConfig:
    config = await service.delete_load_balancer_config(load_balancer_id, session)
    return config


@router.post(
    "/static-file",
    responses=merge_responses(
        generate_error_response(VirtualHostNameAlreadyExists),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def create_static_file_config(
    create_static_file_config_data: schemas.CreateStaticFileConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateStaticFileConfig:
    config = await service.create_static_file_config(create_static_file_config_data, session)
    return config


@router.patch(
    "/static-file",
    responses=merge_responses(
        generate_error_response(ConfigNotFound, "static file configuration"),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def update_static_file_config(
    update_static_file_config_data: schemas.UpdateStaticFileConfig,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.UpdateStaticFileConfig:
    config = await service.update_static_file_config(update_static_file_config_data, session)
    return config


@router.get("/static-file", responses=generate_error_response(ConfigNotFound, "static file configuration"))
async def read_static_file_config(
    static_file_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateStaticFileConfig:
    config = await service.read_static_file_config(static_file_id, session)
    return config


@router.get(
    "/static-file/all",
)
async def read_all_static_file_config(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[schemas.UpdateStaticFileConfig]:
    return await service.read_all_static_file_config(session=session)


@router.delete(
    "/static-file",
    responses=merge_responses(
        generate_error_response(ConfigNotFound, "static file configuration"),
        generate_error_response(FerronContainerNotFoundException, settings.ferron_container_name),
    ),
)
async def delete_static_file_config(
    static_file_id: int, session: Annotated[AsyncSession, Depends(get_session)]
) -> schemas.UpdateStaticFileConfig:
    config = await service.delete_static_file_config(static_file_id, session)
    return config
