from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.database import get_session
from src.ferron import service
from src.ferron import schemas

router = APIRouter(
    prefix="/configs",
    tags=["ferron-config"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/global")
async def read_global_config(
        session: Annotated[AsyncSession, Depends(get_session)]
):
    config = await service.read_global_config(session)
    return config

@router.post("/global")
async def create_global_config(
        global_config_data: schemas.GlobalTemplateConfig,
        session: Annotated[AsyncSession, Depends(get_session)]
):
    config = await service.create_global_config(global_config_data, session)
    return config

@router.patch("/global")
async def update_global_config(
        global_config_data: schemas.GlobalTemplateConfig,
        session: Annotated[AsyncSession, Depends(get_session)]
):
    config = await service.update_global_config(global_config_data, session)
    return config

