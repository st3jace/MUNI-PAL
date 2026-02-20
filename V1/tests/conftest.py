"""
Test fixtures and configuration for Muni-Pal.

Provides:
- In-memory SQLite database for tests
- Async session fixtures
- Test client for API integration tests
- Factory fixtures for test data
"""

import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import StaticPool, create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from munipal.core.models import Base
from munipal.db.session import get_async_session
from munipal.main import app


# -----------------------------------------------------------------------------
# Database Fixtures
# -----------------------------------------------------------------------------

# Use SQLite in-memory for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def async_engine():
    """Create async engine with in-memory SQLite."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide async database session for tests."""
    async_session = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def test_client(async_engine, db_session) -> AsyncGenerator[AsyncClient, None]:
    """Provide test client with dependency overrides."""

    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_async_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# Factory Fixtures
# -----------------------------------------------------------------------------


class TestDataFactory:
    """Factory for creating test data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_playbook(
        self,
        name: str = "Test Playbook",
        version: str = "1.0.0",
        is_default: bool = True,
        is_active: bool = True,
    ) -> dict[str, Any]:
        """Create a test playbook."""
        from munipal.core.models.playbook import Playbook

        playbook_id = str(uuid4())
        playbook = Playbook(
            id=playbook_id,
            name=name,
            version=version,
            description="Test playbook for unit tests",
            bond_archetype="Test Bond",
            is_default=is_default,
            is_active=is_active,
            schema_paths={
                "project.name": {"criticality": "critical", "description": "Project name"},
                "project.location": {"criticality": "material", "description": "Location"},
            },
            extractors={"test_extractor": {"model": "test"}},
            checklist_items=[
                {
                    "code": "TEST-001",
                    "phase": "P1",
                    "name": "Test Item",
                    "required_paths": ["project.name"],
                }
            ],
            readiness_config={
                "dimensions": {
                    "issuer_authority": {"weight": 0.20},
                    "project_tech": {"weight": 0.20},
                }
            },
        )

        self.session.add(playbook)
        await self.session.flush()

        return {
            "id": playbook_id,
            "name": name,
            "version": version,
        }

    async def create_project(
        self,
        playbook_id: str,
        name: str = "Test Project",
        owner_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a test project."""
        from munipal.core.models.project import Project

        project_id = str(uuid4())
        owner = owner_id or str(uuid4())

        project = Project(
            id=project_id,
            name=name,
            description="Test project for unit tests",
            issuer_name="Test Issuer",
            project_location="Test City, ST",
            target_bond_amount=10000000.0,
            playbook_id=playbook_id,
            owner_id=owner,
        )

        self.session.add(project)
        await self.session.flush()

        return {
            "id": project_id,
            "name": name,
            "playbook_id": playbook_id,
            "owner_id": owner,
        }

    async def create_artifact(
        self,
        project_id: str,
        filename: str = "test_document.pdf",
        artifact_type: str = "pdf",
    ) -> dict[str, Any]:
        """Create a test artifact."""
        from munipal.core.models.artifact import Artifact

        artifact_id = str(uuid4())

        artifact = Artifact(
            id=artifact_id,
            project_id=project_id,
            filename=filename,
            original_filename=filename,
            artifact_type=artifact_type,
            file_size=1024,
            storage_path=f"/test/storage/{artifact_id}/{filename}",
            mime_type="application/pdf",
            checksum="abc123",
        )

        self.session.add(artifact)
        await self.session.flush()

        return {
            "id": artifact_id,
            "filename": filename,
            "project_id": project_id,
        }

    async def create_chunk(
        self,
        artifact_id: str,
        content: str = "Test chunk content",
        chunk_type: str = "page",
        page_number: int = 1,
    ) -> dict[str, Any]:
        """Create a test chunk."""
        from munipal.core.models.artifact import Chunk

        chunk_id = str(uuid4())

        chunk = Chunk(
            id=chunk_id,
            artifact_id=artifact_id,
            chunk_type=chunk_type,
            sequence_number=page_number,
            page_number=page_number,
            content=content,
            token_count=len(content.split()),
        )

        self.session.add(chunk)
        await self.session.flush()

        return {
            "id": chunk_id,
            "artifact_id": artifact_id,
            "content": content,
        }

    async def create_extraction_job(
        self,
        project_id: str,
        artifact_id: str,
        status: str = "completed",
    ) -> dict[str, Any]:
        """Create a test extraction job."""
        from munipal.core.models.extraction import ExtractionJob

        job_id = str(uuid4())

        job = ExtractionJob(
            id=job_id,
            project_id=project_id,
            artifact_id=artifact_id,
            status=status,
            extractor_type="test_extractor",
            config={"test": True},
        )

        self.session.add(job)
        await self.session.flush()

        return {
            "id": job_id,
            "project_id": project_id,
            "artifact_id": artifact_id,
            "status": status,
        }

    async def create_fact(
        self,
        project_id: str,
        extraction_job_id: str,
        schema_path: str = "project.name",
        value: Any = "Test Value",
        confidence_score: float = 0.95,
        review_status: str = "pending",
        criticality: str = "critical",
    ) -> dict[str, Any]:
        """Create a test extracted fact."""
        from munipal.core.models.fact import ExtractedFact

        fact_id = str(uuid4())

        fact = ExtractedFact(
            id=fact_id,
            schema_path=schema_path,
            criticality=criticality,
            value=value,
            value_type="string",
            confidence_score=confidence_score,
            confidence_rationale="Test confidence",
            project_id=project_id,
            extraction_job_id=extraction_job_id,
            review_status=review_status,
        )

        self.session.add(fact)
        await self.session.flush()

        return {
            "id": fact_id,
            "schema_path": schema_path,
            "value": value,
            "confidence_score": confidence_score,
            "review_status": review_status,
            "project_id": project_id,
        }


@pytest.fixture
def factory(db_session: AsyncSession) -> TestDataFactory:
    """Provide test data factory."""
    return TestDataFactory(db_session)


# -----------------------------------------------------------------------------
# Utility Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_project_data() -> dict[str, Any]:
    """Sample project creation data."""
    return {
        "name": "Sample Municipal Project",
        "description": "A test municipal bond project",
        "issuer_name": "City of Testville",
        "project_location": "Testville, TX",
        "target_bond_amount": 50000000.0,
    }


@pytest.fixture
def sample_fact_data() -> dict[str, Any]:
    """Sample fact data."""
    return {
        "schema_path": "capital.project-cost",
        "value": 75000000.0,
        "value_type": "number",
        "unit": "USD",
        "confidence_score": 0.92,
        "confidence_rationale": "Extracted from financial summary",
        "criticality": "critical",
    }


@pytest.fixture
def reviewer_id() -> str:
    """Provide a reviewer UUID for tests."""
    return str(uuid4())
