"""
Project model.

Per spec: Project is the workspace for one bond-eligible project.
All artifacts, facts, and deliverables belong to a project.
"""

from uuid import uuid4

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin, UUIDType


class Project(Base, TimestampMixin):
    """Workspace for one bond-eligible project."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Project metadata
    issuer_name: Mapped[str | None] = mapped_column(String(255))
    project_location: Mapped[str | None] = mapped_column(String(500))
    target_bond_amount: Mapped[float | None] = mapped_column(Float)
    tenant_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default="default", index=True
    )

    # Relationships
    owner_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("users.id"),
        nullable=False,
    )
    playbook_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("playbooks.id"),
        nullable=False,
    )

    # Relationships
    owner = relationship("User", back_populates="projects")
    playbook = relationship("Playbook", back_populates="projects")
    artifacts = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")
    extraction_jobs = relationship(
        "ExtractionJob", back_populates="project", cascade="all, delete-orphan"
    )
    extracted_facts = relationship(
        "ExtractedFact", back_populates="project", cascade="all, delete-orphan"
    )
    deliverable_packs = relationship(
        "DeliverablePack", back_populates="project", cascade="all, delete-orphan"
    )

    # v2 deliverables
    disclosure_documents = relationship(
        "DisclosureDocument", back_populates="project", cascade="all, delete-orphan"
    )
    information_requests = relationship(
        "InformationRequest", back_populates="project", cascade="all, delete-orphan"
    )
    internal_reports = relationship(
        "InternalReadinessReport", back_populates="project", cascade="all, delete-orphan"
    )
    external_packages = relationship(
        "ExternalAdvisoryPackage", back_populates="project", cascade="all, delete-orphan"
    )

    # Document Management System
    deal_documents = relationship(
        "DealDocument", back_populates="project", cascade="all, delete-orphan"
    )
    virtual_data_room = relationship(
        "VirtualDataRoom", back_populates="project", uselist=False, cascade="all, delete-orphan"
    )
