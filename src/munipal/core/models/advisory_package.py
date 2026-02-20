"""
Bifurcated deliverable models for v2.

Per spec: Split the current monolithic handoff pack into:
- InternalReadinessReport (for sponsor team use)
- ExternalAdvisoryPackage (for municipal advisor consumption)
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin, UUIDType


class InternalReadinessReport(Base, TimestampMixin):
    """
    Operational control document for the project sponsor team.

    Per spec: Provides complete visibility into readiness state, gaps,
    information requests, evidence audit trail, and checklist progress.

    NOT for external consumption.
    """

    __tablename__ = "internal_readiness_reports"

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Version tracking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Generation status
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    generation_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generation_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ===== CONTENT SECTIONS (stored as JSON) =====

    # 1. Executive Summary
    executive_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 2. Readiness Dashboard
    readiness_dashboard: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 3. Gap Analysis
    gap_analysis: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 4. Information Requests
    information_requests_section: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 5. Checklist Status
    checklist_status: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 6. Evidence Index
    evidence_index: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 7. Assumption Register (full detail)
    assumption_register: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # ===== SNAPSHOT METRICS =====
    overall_score: Mapped[float | None] = mapped_column(Float)  # 0-10
    dimension_scores: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    critical_gap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_gap_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    open_request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overdue_request_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    facts_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ===== METADATA =====
    playbook_version: Mapped[str | None] = mapped_column(String(50))
    bfms_version: Mapped[str | None] = mapped_column(String(50))

    # Storage
    pdf_storage_path: Mapped[str | None] = mapped_column(String(500))
    md_storage_path: Mapped[str | None] = mapped_column(String(500))

    # Celery task tracking
    celery_task_id: Mapped[str | None] = mapped_column(String(255))

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )

    # Relationships
    project = relationship("Project", back_populates="internal_reports")


class ExternalAdvisoryPackage(Base, TimestampMixin):
    """
    Professional deliverable for municipal advisors, bond counsel, underwriters,
    and rating agencies.

    Per spec: Demonstrates sponsor preparation without revealing internal
    operational details, gap tracking, or work-in-progress status.
    """

    __tablename__ = "external_advisory_packages"

    id: Mapped[str] = mapped_column(
        UUIDType,
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    # Version tracking
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    generated_for: Mapped[str] = mapped_column(String(255), nullable=False)

    # Generation status
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    generation_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    generation_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ===== CONTENT SECTIONS (stored as JSON) =====

    # 1. Cover Page
    cover_page: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 2. Executive Summary
    executive_summary: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 3. Deal Overview Memo
    deal_overview: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 4. Disclosure Document (from WP7)
    # Reference to DisclosureDocument is via disclosure_document_id

    # 5. Financial Tables
    financial_tables: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 6. SLB KPI Brief
    slb_brief: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 7. Key Assumptions (filtered subset)
    key_assumptions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # 8. Mandatory Disclaimer
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # ===== QUALITY METRICS =====
    disclosure_completeness_score: Mapped[float | None] = mapped_column(Float)
    critical_tbd_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    high_tbd_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    readiness_score_at_generation: Mapped[float | None] = mapped_column(Float)

    # Quality gate status
    ready_for_distribution: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    distribution_issues: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    # ===== METADATA =====
    playbook_version: Mapped[str | None] = mapped_column(String(50))
    bfms_version: Mapped[str | None] = mapped_column(String(50))

    # Storage
    pdf_storage_path: Mapped[str | None] = mapped_column(String(500))
    docx_storage_path: Mapped[str | None] = mapped_column(String(500))
    md_storage_path: Mapped[str | None] = mapped_column(String(500))

    # Celery task tracking
    celery_task_id: Mapped[str | None] = mapped_column(String(255))

    # Foreign keys
    project_id: Mapped[str] = mapped_column(
        UUIDType,
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    disclosure_document_id: Mapped[str | None] = mapped_column(
        UUIDType,
        ForeignKey("disclosure_documents.id"),
        nullable=True,
    )

    # Relationships
    project = relationship("Project", back_populates="external_packages")
    disclosure_document = relationship("DisclosureDocument")
