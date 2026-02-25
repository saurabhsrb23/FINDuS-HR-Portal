"""Shared pytest fixtures for unit and integration tests."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.user import User, UserRole

# ─── Test database URL ────────────────────────────────────────────────────────
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://donehr:donehr@localhost:5432/donehr_test",
)


# ─── Async engine + session (real DB, used in integration tests) ──────────────
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a session wrapped in a savepoint; rolls back after each test."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ─── HTTP client (full app, integration) ─────────────────────────────────────
@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    from app.core.dependencies import get_db
    from main import app

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ─── Mock Redis (unit tests) ──────────────────────────────────────────────────
@pytest.fixture
def mock_redis():
    with patch("app.core.redis_client._redis") as mock:
        mock.set = AsyncMock(return_value=True)
        mock.exists = AsyncMock(return_value=0)
        mock.aclose = AsyncMock()
        yield mock


# ─── Pre-built User factory ───────────────────────────────────────────────────
def make_user(
    *,
    role: UserRole = UserRole.CANDIDATE,
    is_verified: bool = True,
    is_active: bool = True,
    email: str = "test@example.com",
) -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        password_hash="$2b$12$fakehash",
        full_name="Test User",
        role=role,
        is_active=is_active,
        is_verified=is_verified,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
        deleted_at=None,
    )
