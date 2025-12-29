import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any

import aiofiles
from fastapi import Depends, FastAPI, status
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.auth import schemas
from src.auth.dependencies import get_current_user
from src.auth.router import router as auth_router
from src.config import settings
from src.database import create_db_and_tables
from src.ferron.constants import ConfigFileLocation
from src.ferron.router import router as config_router
from src.service import rate_limiter


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    # have to create it since main.kdl is expected to be present on every start
    # this won't modify the file if it already exists
    async with aiofiles.open(ConfigFileLocation.MAIN_CONFIG.value, "a"):
        pass

    # permissions are being set to 644 so that ferron can read the config files
    await asyncio.to_thread(os.chmod, ConfigFileLocation.MAIN_CONFIG.value, 0o644)

    # include the main config file in /etc/ferron.kdl if it hasn't been included already
    async with aiofiles.open("/etc/ferron.kdl", "r") as f:
        content = await f.read()

    has_included_main_config = False
    for line in content.splitlines():
        if line.strip() == f'include "{ConfigFileLocation.MAIN_CONFIG.value}"':
            has_included_main_config = True
            break

    if not has_included_main_config:
        async with aiofiles.open("/etc/ferron.kdl", "a") as f:
            await f.write(f'include "{ConfigFileLocation.MAIN_CONFIG.value}"\n')

    await create_db_and_tables()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)
app.state.limiter = rate_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# override the default exception handler to return a custom response
# from: https://thedkpatel.medium.com/rate-limiting-with-fastapi-an-in-depth-guide-c4d64a776b83
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error_code": "rate_limit_exceeded",
            "message": "Please slow down and try again later.",
        },
    )


app.include_router(auth_router)
app.include_router(config_router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to Ferron Proxy Manager API"}


@app.get("/protected")
async def protected_route(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
) -> dict[str, Any]:
    return {
        "message": "This is a protected route",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
        },
    }
