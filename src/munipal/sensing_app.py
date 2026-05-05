"""
Muni-Pal Sensing Microservice — Standalone FastAPI Application

Public-facing sensing layer for the Bond Readiness Accelerator.
Exposes ONLY public /api/v1/sensing/* endpoints with rate limiting and CORS.

Deploy this instead of main.py for the public muni-pal.io service.
All BFMS, project, admin, extraction, and sensing-admin routes are excluded entirely.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from munipal import __version__
from munipal.api.routes import health, sensing
from munipal.config import get_settings
from munipal.middleware.telemetry import TelemetryMiddleware

settings = get_settings()

# ---------------------------------------------------------------------------
# Rate Limiter
# ---------------------------------------------------------------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    storage_uri=settings.redis_connection_url,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup (lead capture requires Postgres)."""
    if settings.use_sqlite:
        from munipal.db.session import init_db
        await init_db()
    yield


app = FastAPI(
    title="Muni-Pal Bond Intelligence — Public Sensing API",
    description=(
        "Free top-of-funnel bond readiness assessment tools. "
        "Powered by the EMMA corpus and the Bond Readiness Accelerator."
    ),
    version=__version__,
    lifespan=lifespan,
    # Disable interactive docs in production (set DEBUG=true to enable)
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# ---------------------------------------------------------------------------
# Rate limiting state + handler
# ---------------------------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — allow configured public frontend origin(s)
# ---------------------------------------------------------------------------
_cors_origins: list[str] = []
if settings.sensing_cors_origins:
    _cors_origins = [o.strip() for o in settings.sensing_cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins if _cors_origins else (["*"] if settings.debug else []),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Session-Id"],
)

# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------
app.add_middleware(
    TelemetryMiddleware,
    jsonl_path=settings.telemetry_jsonl_path,
    enabled=settings.telemetry_enabled,
)

# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if settings.debug:
        import traceback
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "traceback": traceback.format_exc(),
            },
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred."},
    )


# ---------------------------------------------------------------------------
# Routes — sensing only
# ---------------------------------------------------------------------------
app.include_router(health.router, tags=["Health"])
app.include_router(sensing.public_router, prefix="/api/v1/sensing", tags=["Sensing"])


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root() -> dict[str, Any]:
    return {
        "service": "Muni-Pal Bond Intelligence",
        "description": "Public sensing API — bond readiness & market benchmarks",
        "tools": "/api/v1/sensing/sectors",
        "docs": "/docs" if settings.debug else None,
    }
