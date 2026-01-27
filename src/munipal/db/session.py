"""
Database session management.

Provides async session factory for FastAPI dependency injection
and sync session for Celery workers (as per spec requirement).
"""

from collections.abc import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from munipal.config import get_settings

settings = get_settings()

# -----------------------------------------------------------------------------
# Async Engine & Session (for FastAPI)
# -----------------------------------------------------------------------------
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# -----------------------------------------------------------------------------
# Sync Engine & Session (for Celery workers)
# Per spec: "Celery workers run sync SQLAlchemy inside tasks"
# -----------------------------------------------------------------------------
sync_engine = create_engine(
    settings.database_url_sync,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_sync_session() -> Session:
    """Get sync session for Celery workers."""
    return SyncSessionLocal()
