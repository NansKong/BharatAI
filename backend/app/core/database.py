"""
Async SQLAlchemy database manager with loop-safe engine/session handling.
"""

from __future__ import annotations

import asyncio
import threading
from typing import AsyncGenerator

from app.core.config import settings
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

_engine_kwargs: dict = {"echo": settings.DEBUG}

if settings.APP_ENV == "test":
    # Prevent pooled asyncpg connections from crossing event-loop boundaries in tests.
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs.update(
        {
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }
    )

_registry_lock = threading.Lock()
_engines_by_loop: dict[int, AsyncEngine] = {}
_sessions_by_loop: dict[int, async_sessionmaker[AsyncSession]] = {}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


def _current_loop_key() -> int:
    loop = asyncio.get_running_loop()
    return id(loop)


def _build_engine() -> AsyncEngine:
    return create_async_engine(settings.DATABASE_URL, **_engine_kwargs)


def _ensure_loop_resources() -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    loop_key = _current_loop_key()

    with _registry_lock:
        engine = _engines_by_loop.get(loop_key)
        session_factory = _sessions_by_loop.get(loop_key)
        if engine is None or session_factory is None:
            engine = _build_engine()
            session_factory = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            _engines_by_loop[loop_key] = engine
            _sessions_by_loop[loop_key] = session_factory

    return engine, session_factory


def get_engine() -> AsyncEngine:
    engine, _ = _ensure_loop_resources()
    return engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    _, session_factory = _ensure_loop_resources()
    return session_factory


async def init_database() -> None:
    """Initialize DB resources for the current running event loop."""
    _ensure_loop_resources()


async def close_database() -> None:
    """Dispose DB engine bound to the current running event loop."""
    loop_key = _current_loop_key()
    with _registry_lock:
        engine = _engines_by_loop.pop(loop_key, None)
        _sessions_by_loop.pop(loop_key, None)
    if engine is not None:
        await engine.dispose()


async def close_all_databases() -> None:
    """Dispose all known DB engines (used by tests/process teardown)."""
    with _registry_lock:
        engines = list(_engines_by_loop.values())
        _engines_by_loop.clear()
        _sessions_by_loop.clear()

    for engine in engines:
        await engine.dispose()


class _EngineProxy:
    """
    Backward-compatible proxy for legacy imports (`from app.core.database import engine`).
    """

    def __getattr__(self, name: str):
        return getattr(get_engine(), name)

    async def dispose(self) -> None:
        await close_database()

    def connect(self):
        return get_engine().connect()

    def begin(self):
        return get_engine().begin()


class _SessionFactoryProxy:
    """
    Backward-compatible proxy for legacy imports (`from app.core.database import AsyncSessionLocal`).
    """

    def __call__(self, *args, **kwargs):
        return get_session_factory()(*args, **kwargs)


engine = _EngineProxy()
AsyncSessionLocal = _SessionFactoryProxy()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an async DB session.
    Session is automatically committed or rolled back on exit.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables (used for testing; migrations handle production)."""
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Drop all tables (used in testing only)."""
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
