import asyncio
import os
import uuid

import pytest
from fastapi.testclient import TestClient

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = (
    os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://bharatai:bharatai_pass@localhost:5432/bharatai_db",
    )
    .replace("?ssl=false", "?sslmode=disable")
    .split("?")[0]
    + "?sslmode=disable"
)
os.environ["REDIS_URL"] = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

from app.core.database import (AsyncSessionLocal, Base, close_all_databases,
                               engine)
from app.core.redis import close_redis
from app.core.security import create_access_token, hash_password
from app.main import create_application
from app.models.user import Profile, User


async def _reset_db() -> None:
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def _session_loop():
    """
    Reuse a single event loop for all async fixture helpers.
    This avoids asyncpg finalizers running after per-call loops are already closed.
    """
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        # Guard each cleanup step — the TestClient lifespan may have already
        # closed connections, which is fine.
        try:
            loop.run_until_complete(close_redis())
        except Exception:
            pass
        try:
            loop.run_until_complete(close_all_databases())
        except Exception:
            pass
        # Yield control briefly so asyncpg background disconnect coroutines
        # (AbstractConnection.disconnect) can complete before we cancel them.
        loop.run_until_complete(asyncio.sleep(0.25))
        pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
        for task in pending:
            task.cancel()
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


@pytest.fixture(scope="session")
def run_async(_session_loop):
    def _run(coro):
        return _session_loop.run_until_complete(coro)

    return _run


@pytest.fixture(autouse=True)
def reset_database(run_async):
    run_async(_reset_db())
    yield


@pytest.fixture(scope="session")
def client():
    app = create_application()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def create_user_token(run_async):
    def _create(
        role: str = "student", email: str | None = None, name: str | None = None
    ) -> str:
        user_id = uuid.uuid4()
        user_email = email or f"{role}-{uuid.uuid4().hex[:8]}@example.com"
        user_name = name or f"{role.title()} User"

        async def _insert() -> None:
            async with AsyncSessionLocal() as db:
                user = User(
                    id=user_id,
                    name=user_name,
                    email=user_email,
                    hashed_password=hash_password("StrongPass9"),
                    role=role,
                    is_active=True,
                    is_verified=True,
                )
                db.add(user)
                db.add(Profile(user_id=user_id))
                await db.commit()

        run_async(_insert())
        return create_access_token(str(user_id), role)

    return _create
