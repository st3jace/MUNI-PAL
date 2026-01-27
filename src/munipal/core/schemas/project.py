"""
Project schemas.

Per spec: Project is the workspace for one bond-eligible project.
All artifacts, facts, and deliverables belong to a project.
"""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import BaseSchema, TimestampSchema, UUIDSchema


class ProjectBase(BaseSchema):
    """Base project fields."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)

    # Project metadata
    issuer_name: str | None = Field(None, max_length=255)
    project_location: str | None = Field(None, max_length=500)
    target_bond_amount: float | None = Field(None, ge=0, description="Target bond amount in USD")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""

    playbook_id: UUID | None = Field(
        None,
        description="Optional playbook to use. Defaults to latest UCS CAB+SLB playbook.",
    )


class ProjectUpdate(BaseSchema):
    """Schema for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    issuer_name: str | None = Field(None, max_length=255)
    project_location: str | None = Field(None, max_length=500)
    target_bond_amount: float | None = Field(None, ge=0)


class ProjectRead(ProjectBase, UUIDSchema, TimestampSchema):
    """Schema for reading a project."""

    playbook_id: UUID
    owner_id: UUID

    # Computed summary fields
    artifact_count: int = 0
    fact_count: int = 0
    approved_fact_count: int = 0
    overall_readiness_score: float | None = None


class ProjectSummary(UUIDSchema):
    """Minimal project summary for listings."""

    name: str
    issuer_name: str | None
    artifact_count: int = 0
    overall_readiness_score: float | None = None
    updated_at: datetime
