"""
Alembic env.py – uses synchronous psycopg2 for migrations.
The running app uses asyncpg; alembic uses psycopg2 (sync) — this is the standard pattern.
"""
from logging.config import fileConfig

# Import all models so Alembic can auto-detect them
import app.models  # noqa: F401
from alembic import context
from app.core.config import settings
from app.core.database import Base
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_sync_url() -> str:
    """Convert asyncpg URL to psycopg2 URL for synchronous Alembic use."""
    url = settings.DATABASE_URL
    # Strip query params (e.g. ?ssl=false) — handled via connect_args below
    url = url.split("?")[0]
    return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


def run_migrations_offline() -> None:
    context.configure(
        url=get_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section) or {}
    cfg["sqlalchemy.url"] = get_sync_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={"sslmode": "disable"},  # local PostgreSQL, no SSL
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
