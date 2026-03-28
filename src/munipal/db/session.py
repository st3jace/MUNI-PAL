"""
Database session management.

Provides async session factory for FastAPI dependency injection
and sync session for Celery workers (as per spec requirement).

Supports both PostgreSQL (production) and SQLite (development).
"""

from collections.abc import AsyncGenerator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from munipal.config import get_settings

settings = get_settings()

# -----------------------------------------------------------------------------
# Async Engine & Session (for FastAPI)
# -----------------------------------------------------------------------------

if settings.use_sqlite:
    # SQLite configuration for development
    async_engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL configuration for production
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

if settings.use_sqlite:
    # SQLite configuration for development
    sync_engine = create_engine(
        settings.database_url_sync,
        echo=settings.debug,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL configuration for production
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

# Alias for convenience — matches the common SQLAlchemy convention expected by
# tests, examples, and documentation.
SessionLocal = SyncSessionLocal


def get_sync_session() -> Session:
    """Get sync session for Celery workers."""
    return SyncSessionLocal()


@contextmanager
def get_sync_session_context():
    """Context manager for sync sessions."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# -----------------------------------------------------------------------------
# Database Initialization (for SQLite dev mode)
# -----------------------------------------------------------------------------

async def init_db():
    """Initialize database tables (for SQLite development mode)."""
    from munipal.core.models import Base

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
