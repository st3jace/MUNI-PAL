"""
Muni-Pal FastAPI Application

Evidence-first, advisor-grade platform for municipal bond structuring.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from munipal import __version__
from munipal.api.routes import health, projects, artifacts, facts, checklist, readiness
from munipal.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    # TODO: Initialize database connections, run migrations check, etc.
    yield
    # Shutdown
    # TODO: Close connections, cleanup resources


app = FastAPI(
    title="Muni-Pal BFMS",
    description=(
        "Bond Facility Management System - An evidence-first, advisor-grade platform "
        "for municipal bond structuring. Converts messy project documentation into "
        "structured, bond-issuance-ready outputs with full provenance tracking."
    ),
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else [],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------------------------------------------------------
# Exception Handlers
# -----------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    # Log the error in production
    if not settings.debug:
        # TODO: Add proper logging
        pass

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal error occurred.",
            "type": "internal_error",
        },
    )


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------
app.include_router(health.router, tags=["Health"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(artifacts.router, prefix="/api/v1/artifacts", tags=["Artifacts"])
app.include_router(facts.router, prefix="/api/v1/facts", tags=["Facts"])
app.include_router(checklist.router, prefix="/api/v1/checklist", tags=["Checklist"])
app.include_router(readiness.router, prefix="/api/v1/readiness", tags=["Readiness"])


# -----------------------------------------------------------------------------
# Root Endpoint
# -----------------------------------------------------------------------------
@app.get("/", include_in_schema=False)
async def root() -> dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "name": "Muni-Pal BFMS",
        "version": __version__,
        "description": "Bond Facility Management System",
        "docs": "/docs" if settings.debug else None,
    }
