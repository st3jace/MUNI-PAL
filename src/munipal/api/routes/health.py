"""
Health check endpoints.

Provides liveness and readiness probes for container orchestration.
"""

import asyncio
from typing import Any

import redis.asyncio as redis
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from munipal import __version__
from munipal.config import get_settings
from munipal.db.session import get_async_session

router = APIRouter()
settings = get_settings()

async def _check_redis(settings_obj: Any) -> bool:
    """Return Redis readiness using a bounded ping instead of a static stub."""
    client = None
    try:
        client = redis.from_url(settings_obj.redis_connection_url)
        pong = await asyncio.wait_for(client.ping(), timeout=1.0)
        return bool(pong)
    except Exception:
        return False
    finally:
        if client is not None:
            close = getattr(client, "aclose", None) or getattr(client, "close", None)
            if close is not None:
                result = close()
                if hasattr(result, "__await__"):
                    await result


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.

    Returns service status without checking dependencies.
    Use this for liveness probes.
    """
    # Check EMMA corpus availability for sensing tools
    from munipal.services.sensing import _EMMA_EXTRACTOR, _SEED_DIR, _corpus_available
    corpus_status = {
        "emma_path": str(_EMMA_EXTRACTOR),
        "emma_exists": _EMMA_EXTRACTOR.exists(),
        "seed_path": str(_SEED_DIR),
        "seed_exists": _SEED_DIR.exists(),
        "waste_corpus": _corpus_available("waste"),
        "healthcare_corpus": _corpus_available("healthcare"),
    }

    return {
        "status": "healthy",
        "version": __version__,
        "environment": settings.app_env,
        "corpus": corpus_status,
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(
    db: AsyncSession = Depends(get_async_session),  # noqa: B008
) -> dict[str, Any]:
    """
    Readiness check endpoint.

    Verifies database connectivity. Use this for readiness probes.
    """
    checks = {
        "database": False,
        "redis": False,
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    checks["redis"] = await _check_redis(settings)

    all_healthy = all(checks.values())

    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
        "version": __version__,
    }
