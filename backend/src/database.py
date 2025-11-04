from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from src.config import settings


database_url = settings.database_url

engine = create_async_engine(
    database_url,
    echo=settings.database_echo,
)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[SQLModelAsyncSession, None]:
    async with SQLModelAsyncSession(engine) as session:
        yield session
