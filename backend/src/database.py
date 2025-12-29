from typing import AsyncGenerator

from sqlalchemy import event
from sqlalchemy.dialects.sqlite.aiosqlite import AsyncAdapt_aiosqlite_connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool.base import _ConnectionRecord
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

from src.config import settings

database_url = settings.database_url

engine = create_async_engine(
    database_url,
    echo=settings.database_echo,
)


# enable foreign keys for on delete cascade
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(
    # I got types for these two parameters by debug printing them
    dbapi_conn: AsyncAdapt_aiosqlite_connection,
    _connection_record: _ConnectionRecord,
) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async def create_db_and_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[SQLModelAsyncSession, None]:
    async with SQLModelAsyncSession(engine) as session:
        yield session
