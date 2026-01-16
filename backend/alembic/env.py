from logging.config import fileConfig
from typing import Any

from alembic.autogenerate.api import AutogenContext
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel
from sqlmodel.sql.sqltypes import AutoString

from alembic import context
from src.auth.models import *  # noqa: F403 # to import all tables automatically
from src.config import settings
from src.ferron.models import *  # noqa: F403 # to import all tables automatically

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# specifying this here instead of alembic.ini because if in future I change my db url in env vars, I do not have to
# change it in alembic.ini too
database_url = settings.database_url
database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://")
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def render_item(type_: str, obj: Any, autogen_context: AutogenContext) -> str | bool:  # noqa: ANN401
    # https://alembic.sqlalchemy.org/en/latest/autogenerate.html#affecting-the-rendering-of-types-themselves
    # this will render sqlmodel.sql.sqltypes.AutoString() as sa.String()
    # this is required because in comparison of refresh_token (which is stored as a string) cookie,
    # sqlmodel.sql.sqltypes.AutoString() fails for some reason
    if type_ == "type" and isinstance(obj, AutoString):
        return "sa.String()"

    # default rendering for other items
    return False


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_item=render_item,
            render_as_batch=True,  # https://stackoverflow.com/a/32510603
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
