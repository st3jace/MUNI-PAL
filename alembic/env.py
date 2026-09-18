"""
Alembic migration environment configuration.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import models and base
from munipal.config import get_settings

# Import all models to register them with Base.metadata
from munipal.core import models  # noqa: F401
from munipal.db.base import Base

# Alembic Config object
config = context.config

# Setup logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata for autogenerate support
target_metadata = Base.metadata

# Get database URL from settings
settings = get_settings()


def get_url() -> str:
    """Get database URL for migrations (sync driver)."""
    return settings.database_url_sync


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    dialect = context.get_context().dialect
    if dialect.name == "postgresql":
        # Online SQLAlchemy discovers this from SHOW standard_conforming_strings.
        # Offline exports target modern PostgreSQL's default ON, including Supabase.
        # Otherwise the uninitialized dialect doubles JSON backslashes and emits
        # invalid JSON. Changing the server setting inside a multi-statement SQL
        # batch is too late: PostgreSQL parses its literals before executing it.
        dialect._backslash_escapes = False

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
