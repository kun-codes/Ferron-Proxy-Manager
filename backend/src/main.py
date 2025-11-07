from typing import Annotated

from fastapi import Depends, FastAPI
from contextlib import asynccontextmanager

from src.auth import schemas
from src.auth.dependencies import get_current_user
from src.auth.router import router as auth_router
from src.config import settings
from src.database import create_db_and_tables


@asynccontextmanager
async def lifespan(_app: FastAPI):
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
