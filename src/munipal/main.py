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
from munipal.api.routes import (
    advisory_packages,
    artifacts,
    checklist,
    deal_documents,
    deliverables,
    # v2 - WP7, WP8, Bifurcated Deliverables
    disclosure,
    extraction,
    facts,
    health,
    information_requests,
    playbooks,
    projects,
    readiness,
    risk_reporting,
    sensing,
    templates,
)
from munipal.config import get_settings
from munipal.middleware.telemetry import TelemetryMiddleware

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    if settings.use_sqlite:
        # Initialize SQLite database tables for development
        from munipal.db.session import init_db
        await init_db()
        print(f"SQLite database initialized at {settings.sqlite_path}")
    yield
    # Shutdown
    # Cleanup resources if needed


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
    TelemetryMiddleware,
    jsonl_path=settings.telemetry_jsonl_path,
    enabled=settings.telemetry_enabled,
)
_cors_origins: list[str] = []
if settings.cors_origins:
    _cors_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins if _cors_origins else (["*"] if settings.debug else []),
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
    # Include actual error message in debug mode
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

    # Log the error in production
    # TODO: Add proper logging

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
app.include_router(playbooks.router, prefix="/api/v1/playbooks", tags=["Playbooks"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(artifacts.router, prefix="/api/v1/artifacts", tags=["Artifacts"])
app.include_router(extraction.router, prefix="/api/v1/extraction", tags=["Extraction"])
app.include_router(facts.router, prefix="/api/v1/facts", tags=["Facts"])
app.include_router(checklist.router, prefix="/api/v1/checklist", tags=["Checklist"])
app.include_router(readiness.router, prefix="/api/v1/readiness", tags=["Readiness"])
app.include_router(deliverables.router, prefix="/api/v1/deliverables", tags=["Deliverables"])

# v2 - WP7: Disclosure Synthesis Engine
app.include_router(disclosure.router, prefix="/api/v1/disclosure", tags=["Disclosure"])

# v2 - WP8: Information Request System
app.include_router(information_requests.router, prefix="/api/v1/information-requests", tags=["Information Requests"])

# v2 - Bifurcated Deliverables (Internal/External)
app.include_router(advisory_packages.router, prefix="/api/v1/advisory-packages", tags=["Advisory Packages"])
app.include_router(risk_reporting.router, prefix="/api/v1/risk", tags=["Risk"])

# Document Management System
app.include_router(deal_documents.router, prefix="/api/v1/deal-documents", tags=["Deal Documents"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["Templates"])

# Sensing Component (top-of-funnel lead generation tools)
app.include_router(sensing.router, prefix="/api/v1/sensing", tags=["Sensing"])


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
