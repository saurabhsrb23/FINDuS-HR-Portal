"""Async SQLAlchemy engine and session factory."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.is_development,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,       # drop stale connections before use
    pool_recycle=3600,        # recycle connections every hour
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # keeps objects accessible after commit
    autoflush=False,
)


async def get_async_session() -> AsyncSession:
    """Return a new async session (non-context-manager form for direct use)."""
    return AsyncSessionLocal()
