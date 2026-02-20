"""
SQLAlchemy ORM models.

All models are imported here for Alembic autogenerate support.
"""

from munipal.db.base import Base
from munipal.core.models.artifact import Artifact, Chunk
from munipal.core.models.deliverable import DeliverablePack
from munipal.core.models.extraction import ExtractionJob
from munipal.core.models.fact import (
    EvidenceLink,
    ExtractedFact,
    FactChunkAssociation,
    FactRevision,
)
from munipal.core.models.playbook import Playbook
from munipal.core.models.project import Project
from munipal.core.models.user import User

# WP7 - Disclosure Synthesis Engine
from munipal.core.models.disclosure import (
    DisclosureDocument,
    DisclosureSection,
    TBDMarker,
)

# WP8 - Information Request System
from munipal.core.models.information_request import (
    InformationRequest,
    InformationRequestNote,
)

# Bifurcated Deliverables (v2)
from munipal.core.models.advisory_package import (
    InternalReadinessReport,
    ExternalAdvisoryPackage,
)

__all__ = [
    "Base",
    "User",
    "Project",
    "Playbook",
    "Artifact",
    "Chunk",
    "ExtractionJob",
    "ExtractedFact",
    "FactChunkAssociation",
    "FactRevision",
    "EvidenceLink",
    "DeliverablePack",
    # WP7
    "DisclosureDocument",
    "DisclosureSection",
    "TBDMarker",
    # WP8
    "InformationRequest",
    "InformationRequestNote",
    # v2 Deliverables
    "InternalReadinessReport",
    "ExternalAdvisoryPackage",
]
