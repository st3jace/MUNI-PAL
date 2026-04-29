"""
Base schema definitions and common types.

Per spec: Contract-first design using Pydantic schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class TimestampSchema(BaseSchema):
    """Schema mixin for timestamps."""

    created_at: datetime
    updated_at: datetime


class UUIDSchema(BaseSchema):
    """Schema with UUID identifier."""

    id: UUID


# -----------------------------------------------------------------------------
# Common Enums
# -----------------------------------------------------------------------------


class ReviewStatus(str, Enum):
    """Review status for ExtractedFacts."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class SourceType(str, Enum):
    """Source type for ExtractedFacts."""

    EXTRACTED = "extracted"  # AI-extracted from documents
    MANUAL = "manual"  # User-entered manually


class ChecklistStatus(str, Enum):
    """Computed status for ChecklistItems."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    READY = "ready"


class ArtifactType(str, Enum):
    """Supported artifact file types."""

    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    XLS = "xls"
    CSV = "csv"
    TXT = "txt"
    PNG = "png"
    JPEG = "jpeg"


class ChunkType(str, Enum):
    """Types of chunks extracted from artifacts."""

    PAGE = "page"  # PDF page
    SHEET = "sheet"  # Excel sheet
    SECTION = "section"  # Document section
    DOCUMENT = "document"  # Full document (docx, txt)
    IMAGE = "image"  # Image file


class JobStatus(str, Enum):
    """Status of async extraction jobs."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CriticalityTier(str, Enum):
    """
    Criticality tiers for schema paths.

    Per playbook:
    - CRITICAL: Requires 0.90+ confidence, blocks progression if missing
    - MATERIAL: Significant impact on readiness scoring
    - SECONDARY: Nice to have, lower confidence thresholds acceptable
    """

    CRITICAL = "critical"
    MATERIAL = "material"
    SECONDARY = "secondary"


class ChecklistPhase(str, Enum):
    """
    Checklist phases per playbook.

    P1-P6 represent the progression of bond diligence.
    """

    P1 = "P1"  # Issuer Authority & Deal Formation
    P2 = "P2"  # Project & Technology Definition
    P3 = "P3"  # Financial Structure & Revenue Model
    P4 = "P4"  # Risk, Security & Disclosure
    P5 = "P5"  # SLB Architecture & Final Modeling
    P6 = "P6"  # Advisor Engagement & Execution


class ReadinessDimension(str, Enum):
    """
    Readiness scoring dimensions per playbook.

    Each dimension has a weight contributing to overall score.
    """

    ISSUER_AUTHORITY = "issuer_authority"  # 20%
    PROJECT_TECH = "project_tech"  # 20%
    REVENUE_FEEDSTOCK = "revenue_feedstock"  # 15%
    CAB_FINANCIAL = "cab_financial"  # 20%
    RISK_SECURITY_SLB = "risk_security_slb"  # 15%
    SLB_VERIFICATION = "slb_verification"  # 10%


# -----------------------------------------------------------------------------
# Provenance Types
# -----------------------------------------------------------------------------


class ChunkReference(BaseSchema):
    """
    Reference to a specific chunk for provenance tracking.

    Per spec: Every fact must trace back to source evidence.
    """

    chunk_id: UUID
    artifact_id: UUID
    page_number: int | None = None
    sheet_name: str | None = None
    excerpt: str | None = Field(None, max_length=500, description="Relevant text excerpt")


class SourceReference(ChunkReference):
    """Advisor-facing immutable source reference for an accepted fact.

    Extends the compact chunk reference with stable file and chunk provenance so
    API/export consumers can trace an approved claim back to Artifact -> Chunk ->
    Page/Sheet -> source file without lazy-loading database models.
    """

    artifact_filename: str
    artifact_display_name: str | None = None
    storage_path: str
    chunk_type: str
    sequence_number: int
    section_title: str | None = None
    content_hash: str
