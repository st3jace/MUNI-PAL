"""
Pydantic schemas - the contract-first data definitions.

Per spec: All data contracts are defined here as the source of truth.
"""

from munipal.core.schemas.artifact import (
    ArtifactCreate,
    ArtifactRead,
    ArtifactSummary,
    ChunkCreate,
    ChunkRead,
    ChunkSummary,
)
from munipal.core.schemas.base import (
    ArtifactType,
    BaseSchema,
    ChecklistPhase,
    ChecklistStatus,
    ChunkReference,
    ChunkType,
    CriticalityTier,
    JobStatus,
    ReadinessDimension,
    ReviewStatus,
)
from munipal.core.schemas.checklist import (
    ChecklistItemDefinition,
    ChecklistItemRead,
    ChecklistItemStatus,
    ChecklistPhaseSummary,
)
from munipal.core.schemas.deliverable import (
    DeliverablePackCreate,
    DeliverablePackRead,
    DeliverablePackSummary,
    DeliverableSection,
)
from munipal.core.schemas.extraction import (
    ExtractionJobCreate,
    ExtractionJobRead,
    ExtractionJobSummary,
    ExtractionProgress,
)
from munipal.core.schemas.fact import (
    EvidenceLinkBase,
    EvidenceLinkRead,
    ExtractedFactCreate,
    ExtractedFactRead,
    ExtractedFactSummary,
    FactReviewRequest,
    FactRevisionRead,
)
from munipal.core.schemas.playbook import (
    ExtractorDefinition,
    PlaybookCreate,
    PlaybookDetail,
    PlaybookRead,
    SchemaPathDefinition,
)
from munipal.core.schemas.project import (
    ProjectCreate,
    ProjectRead,
    ProjectSummary,
    ProjectUpdate,
)
from munipal.core.schemas.readiness import (
    DIMENSION_NAMES,
    DIMENSION_WEIGHTS,
    DimensionScore,
    ReadinessAssessment,
    ReadinessGap,
    ReadinessGapReport,
)

__all__ = [
    # Base
    "BaseSchema",
    "ArtifactType",
    "ChunkType",
    "JobStatus",
    "ReviewStatus",
    "ChecklistStatus",
    "ChecklistPhase",
    "CriticalityTier",
    "ReadinessDimension",
    "ChunkReference",
    # Project
    "ProjectCreate",
    "ProjectRead",
    "ProjectSummary",
    "ProjectUpdate",
    # Artifact
    "ArtifactCreate",
    "ArtifactRead",
    "ArtifactSummary",
    "ChunkCreate",
    "ChunkRead",
    "ChunkSummary",
    # Fact
    "ExtractedFactCreate",
    "ExtractedFactRead",
    "ExtractedFactSummary",
    "FactReviewRequest",
    "FactRevisionRead",
    "EvidenceLinkBase",
    "EvidenceLinkRead",
    # Extraction
    "ExtractionJobCreate",
    "ExtractionJobRead",
    "ExtractionJobSummary",
    "ExtractionProgress",
    # Checklist
    "ChecklistItemDefinition",
    "ChecklistItemRead",
    "ChecklistItemStatus",
    "ChecklistPhaseSummary",
    # Readiness
    "DIMENSION_WEIGHTS",
    "DIMENSION_NAMES",
    "DimensionScore",
    "ReadinessAssessment",
    "ReadinessGap",
    "ReadinessGapReport",
    # Playbook
    "SchemaPathDefinition",
    "ExtractorDefinition",
    "PlaybookCreate",
    "PlaybookRead",
    "PlaybookDetail",
    # Deliverable
    "DeliverableSection",
    "DeliverablePackCreate",
    "DeliverablePackRead",
    "DeliverablePackSummary",
]
