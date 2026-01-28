import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aiofiles
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.auth.router import router as auth_router
from src.config import settings
from src.database import engine, run_migrations
from src.exceptions import RateLimitExceededCustomException
from src.ferron.constants import ConfigFileLocation
from src.ferron.router import router as config_router
from src.service import create_ferron_global_config, rate_limiter


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

    await asyncio.to_thread(run_migrations)

    # check if ferron global configuration exists, if not then create a default one
    async with SQLModelAsyncSession(engine) as session:
        await create_ferron_global_config(session)

    yield


origins = ["http://localhost:5173", "http://localhost:3000"]
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=not settings.production,
    lifespan=lifespan,
    # all urls useful in dev setup
    docs_url=None if settings.production else "/docs",
    redoc_url=None if settings.production else "/redoc",
    openapi_url=None if settings.production else "/openapi.json",
)
app.state.limiter = rate_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(_request: Request, _exc: RateLimitExceeded) -> JSONResponse:
    raise RateLimitExceededCustomException()


api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(config_router)
app.include_router(api_router)
