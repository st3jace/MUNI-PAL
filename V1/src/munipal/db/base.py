"""
SQLAlchemy declarative base and common model utilities.

Supports both PostgreSQL and SQLite databases.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from munipal.config import get_settings

settings = get_settings()


# Use String(36) for SQLite compatibility, PostgreSQL UUID otherwise
if settings.use_sqlite:
    UUIDType = String(36)
else:
    from sqlalchemy.dialects.postgresql import UUID
    UUIDType = UUID(as_uuid=False)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    # Enable type annotations for all models
    type_annotation_map = {
        datetime: DateTime(timezone=True),
    }


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDPrimaryKeyMixin:
    """Mixin for UUID primary keys."""

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )
