"""
Health check endpoints.

Provides liveness and readiness probes for container orchestration.
"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from munipal import __version__
from munipal.config import get_settings
from munipal.db.session import get_async_session

router = APIRouter()
settings = get_settings()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.

    Returns service status without checking dependencies.
    Use this for liveness probes.
    """
    return {
        "status": "healthy",
        "version": __version__,
        "environment": settings.app_env,
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(
    db: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """
    Readiness check endpoint.

    Verifies database connectivity. Use this for readiness probes.
    """
    checks = {
        "database": False,
        "redis": False,  # TODO: Add Redis check
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    # TODO: Check Redis connectivity
    # For now, mark as true if we reach this point
    checks["redis"] = True

    all_healthy = all(checks.values())

    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
        "version": __version__,
    }
