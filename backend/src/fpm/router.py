from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.database import get_session
from src.exceptions import InvalidTokenException
from src.ferron.exceptions import ConfigNotFound
from src.fpm import schemas, service
from src.utils import generate_error_response

router = APIRouter(
    prefix="/fpm",
    tags=["fpm"],
    dependencies=[Depends(get_current_user)],
    responses=generate_error_response(InvalidTokenException),
)


@router.get("/dashboard")
async def read_dashboard_hosts(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[schemas.DashboardHost]:
    return await service.read_dashboard_hosts(session)


@router.get(
    "/dashboard/{virtual_host_name}/favicon",
    response_model=schemas.DashboardHost,
    responses=generate_error_response(ConfigNotFound, "virtual host"),
)
async def read_host_favicon(
    virtual_host_name: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> schemas.DashboardHost:
    return await service.read_host_favicon(session, virtual_host_name)
