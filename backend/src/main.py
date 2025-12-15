from typing import Annotated

import aiofiles
from fastapi import Depends, FastAPI
from contextlib import asynccontextmanager

from src.auth import schemas
from src.auth.dependencies import get_current_user
from src.auth.router import router as auth_router
from src.config import settings
from src.database import create_db_and_tables


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # have to create it since main.kdl is expected to be present on every start
    # this won't modify the file if it already exists
    async with aiofiles.open(ConfigFileLocation.MAIN_CONFIG.value, "a"):
        pass

    # include the main config file in /etc/ferron.kdl if it hasn't been included already
    async with aiofiles.open("/etc/ferron.kdl", "r") as f:
        content = await f.read()

    has_included_main_config = False
    for line in content.splitlines():
        if line.strip() == f"include \"{ConfigFileLocation.MAIN_CONFIG.value}\"":
            has_included_main_config = True
            break

    if not has_included_main_config:
        async with aiofiles.open("/etc/ferron.kdl", "a") as f:
            await f.write(f"include \"{ConfigFileLocation.MAIN_CONFIG.value}\"\n")

    await create_db_and_tables()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)


app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "Welcome to Ferron Proxy Manager API"}


@app.get("/protected")
async def protected_route(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    return {
        "message": "This is a protected route",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
        },
    }
