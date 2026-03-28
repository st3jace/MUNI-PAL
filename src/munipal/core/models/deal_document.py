"""
Deal document models for the Document Management System.

Supports document lifecycle management across deal verticals:
municipal finance, private equity, real estate, and project finance.
Includes template engine, e-signature tracking, version history,
virtual data rooms, and compliance audit trails.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from munipal.db.base import Base, TimestampMixin, UUIDType


# ---------------------------------------------------------------------------
# Document Type Registry
# ---------------------------------------------------------------------------


class DealDocumentType(Base, TimestampMixin):
    """
    Extensible registry of document types across deal verticals.

    Seed data populates 25+ muni finance types on first migration.
    PE/RE types added later via subsequent migrations.
    """

    __tablename__ = "deal_document_types"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # Values: templated, negotiated, professional_report, regulatory
    deal_vertical: Mapped[str] = mapped_column(
        String(50), nullable=False, default="muni"
    )
    # Values: muni, pe, re, project_finance
    description: Mapped[str | None] = mapped_column(Text)
    default_workflow: Mapped[str] = mapped_column(
        String(50), nullable=False, default="standard"
    )
    retention_policy: Mapped[str] = mapped_column(
        String(50), nullable=False, default="standard_6yr"
    )
    # Values: standard_6yr, indefinite, bond_life_plus_3yr
    requires_signature: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


# ---------------------------------------------------------------------------
# Document Templates & Clause Library
# ---------------------------------------------------------------------------


class DocumentTemplate(Base, TimestampMixin):
    """
    Jinja2 templates stored in DB for multi-tenant isolation.

    Templates produce TipTap-compatible JSON when rendered with variables.
    """

    __tablename__ = "document_templates"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("deal_document_types.id"), nullable=False, index=True
    )
    jurisdiction: Mapped[str | None] = mapped_column(String(100))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    template_body: Mapped[str] = mapped_column(Text, nullable=False)
    variable_schema: Mapped[dict | None] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default="default", index=True
    )

    # Relationships
    document_type = relationship("DealDocumentType")
    clauses = relationship(
        "TemplateClause", back_populates="template", cascade="all, delete-orphan"
    )


class TemplateClause(Base, TimestampMixin):
    """
    Reusable clause library for contract assembly.

    Clauses can be standalone or linked to a specific template.
    Content is stored as TipTap JSON node trees for direct insertion.
    """

    __tablename__ = "template_clauses"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    template_id: Mapped[str | None] = mapped_column(
        UUIDType, ForeignKey("document_templates.id")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    # Values: rate_covenant, additional_bonds_test, default_events,
    #         flow_of_funds, credit_enhancement, tax_compliance, etc.
    content_json: Mapped[dict | None] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    jurisdiction: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    tenant_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default="default", index=True
    )

    # Relationships
    template = relationship("DocumentTemplate", back_populates="clauses")


# ---------------------------------------------------------------------------
# Core Deal Document
# ---------------------------------------------------------------------------


class DealDocument(Base, TimestampMixin):
    """
    Core document instance within a deal (Project).

    Tracks full lifecycle: draft → under_review → approved → execution →
    signed → filed → archived. Stores editor content as TipTap JSON.
    """

    __tablename__ = "deal_documents"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )

    # Identification
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(50))

    # Type reference
    document_type_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("deal_document_types.id"), nullable=False, index=True
    )

    # Workflow state machine
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    # Values: draft, under_review, approved, execution, signed, filed, archived

    # Content (TipTap / ProseMirror JSON)
    content_json: Mapped[dict | None] = mapped_column(JSON)
    content_html: Mapped[str | None] = mapped_column(Text)
    content_plaintext: Mapped[str | None] = mapped_column(Text)

    # Template provenance
    template_id: Mapped[str | None] = mapped_column(
        UUIDType, ForeignKey("document_templates.id")
    )
    template_version: Mapped[int | None] = mapped_column(Integer)

    # Signature tracking
    signature_request_id: Mapped[str | None] = mapped_column(String(255))
    signature_status: Mapped[str | None] = mapped_column(String(30))
    # Values: pending, signed, declined, expired

    # Filing tracking
    filed_to: Mapped[str | None] = mapped_column(String(100))
    # Values: emma, edgar, irs
    filed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    filing_reference: Mapped[str | None] = mapped_column(String(255))

    # Retention & compliance
    retention_policy: Mapped[str] = mapped_column(
        String(50), nullable=False, default="standard_6yr"
    )
    legal_hold: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retention_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )

    # Linked artifact (for uploaded reports, signed PDFs)
    artifact_id: Mapped[str | None] = mapped_column(
        UUIDType, ForeignKey("artifacts.id")
    )

    # Ownership
    project_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("projects.id"), nullable=False, index=True
    )
    created_by_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    assigned_to_id: Mapped[str | None] = mapped_column(
        UUIDType, ForeignKey("users.id")
    )

    # Relationships
    project = relationship("Project", back_populates="deal_documents")
    document_type = relationship("DealDocumentType")
    template = relationship("DocumentTemplate")
    artifact = relationship("Artifact")
    created_by = relationship("User", foreign_keys=[created_by_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    versions = relationship(
        "DealDocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DealDocumentVersion.version_number.desc()",
    )
    review_assignments = relationship(
        "DocumentReview",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    signers = relationship(
        "DocumentSigner",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    audit_entries = relationship(
        "DocumentAuditLog",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    vdr_permissions = relationship(
        "VdrDocumentPermission",
        back_populates="document",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# Version History
# ---------------------------------------------------------------------------


class DealDocumentVersion(Base, TimestampMixin):
    """
    Immutable version snapshot of a deal document.

    Created on auto-save, manual save, pre-review, and pre-signature events.
    Content is stored as TipTap JSON with a SHA-256 integrity hash.
    """

    __tablename__ = "deal_document_versions"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("deal_documents.id"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content_json: Mapped[dict | None] = mapped_column(JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    change_summary: Mapped[str | None] = mapped_column(Text)
    snapshot_reason: Mapped[str] = mapped_column(
        String(50), nullable=False, default="auto_save"
    )
    # Values: auto_save, manual_save, pre_review, pre_signature, status_change
    created_by_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    storage_path: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    document = relationship("DealDocument", back_populates="versions")
    created_by = relationship("User")

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_doc_version"),
    )


# ---------------------------------------------------------------------------
# Review Workflow
# ---------------------------------------------------------------------------


class DocumentReview(Base, TimestampMixin):
    """
    Parallel review assignment for a document.

    Multiple reviewers can be assigned simultaneously. All must complete
    before the document can transition from under_review to approved.
    """

    __tablename__ = "document_reviews"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("deal_documents.id"), nullable=False, index=True
    )
    reviewer_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    # Values: pending, in_progress, approved, rejected, changes_requested
    comments: Mapped[str | None] = mapped_column(Text)
    review_version: Mapped[int | None] = mapped_column(Integer)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    document = relationship("DealDocument", back_populates="review_assignments")
    reviewer = relationship("User")


# ---------------------------------------------------------------------------
# E-Signature Tracking
# ---------------------------------------------------------------------------


class DocumentSigner(Base, TimestampMixin):
    """
    E-signature signer tracking for Dropbox Sign integration.

    Supports sequential (signing_order > 0) and parallel (signing_order = 0)
    signing workflows. Status updated via webhook callbacks.
    """

    __tablename__ = "document_signers"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("deal_documents.id"), nullable=False, index=True
    )
    signer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    signer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    signer_role: Mapped[str] = mapped_column(String(100), nullable=False)
    # Values: issuer, underwriter, bond_counsel, trustee, municipal_advisor, etc.
    signing_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    # Values: pending, sent, viewed, signed, declined, expired
    dropbox_sign_signer_id: Mapped[str | None] = mapped_column(String(255))
    signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String(45))
    device_info: Mapped[str | None] = mapped_column(String(500))

    # Relationships
    document = relationship("DealDocument", back_populates="signers")


# ---------------------------------------------------------------------------
# Audit Trail (Immutable, Append-Only)
# ---------------------------------------------------------------------------


class DocumentAuditLog(Base):
    """
    Immutable audit log for all document operations.

    No TimestampMixin — uses single timestamp field. No updated_at because
    audit entries are never modified after creation.
    """

    __tablename__ = "document_audit_log"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("deal_documents.id"), nullable=False, index=True
    )
    actor_id: Mapped[str] = mapped_column(UUIDType, nullable=False)
    actor_email: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    # Values: created, edited, version_saved, status_changed, review_assigned,
    #         review_completed, signature_requested, signature_completed,
    #         downloaded, viewed, exported, filed, legal_hold_set,
    #         legal_hold_released, shared, permission_changed, deleted
    details: Mapped[dict | None] = mapped_column(JSON, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Relationships
    document = relationship("DealDocument", back_populates="audit_entries")


# ---------------------------------------------------------------------------
# Virtual Data Room
# ---------------------------------------------------------------------------


class VirtualDataRoom(Base, TimestampMixin):
    """
    Virtual Data Room for controlled external document sharing.

    One VDR per Project. Supports NDA gates, watermarking, granular
    per-document permissions, and page-level view analytics.
    """

    __tablename__ = "virtual_data_rooms"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    project_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("projects.id"), nullable=False, unique=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_nda: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    nda_template_id: Mapped[str | None] = mapped_column(
        UUIDType, ForeignKey("document_templates.id")
    )
    watermark_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    default_access_expiry_days: Mapped[int] = mapped_column(
        Integer, default=30, nullable=False
    )
    settings: Mapped[dict | None] = mapped_column(JSON, default=dict)
    # Settings: { allow_download: true, allow_print: false, require_2fa: false }

    # Relationships
    project = relationship("Project", back_populates="virtual_data_room")
    nda_template = relationship("DocumentTemplate")
    participants = relationship(
        "VdrParticipant",
        back_populates="data_room",
        cascade="all, delete-orphan",
    )
    document_permissions = relationship(
        "VdrDocumentPermission",
        back_populates="data_room",
        cascade="all, delete-orphan",
    )


class VdrParticipant(Base, TimestampMixin):
    """
    External party with access to a Virtual Data Room.

    Access is token-based (no JWT required). Participants must accept
    an NDA before viewing documents when require_nda is enabled.
    """

    __tablename__ = "vdr_participants"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    data_room_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("virtual_data_rooms.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="viewer")
    # Values: viewer, downloader, uploader, admin
    access_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    nda_accepted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nda_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    data_room = relationship("VirtualDataRoom", back_populates="participants")

    __table_args__ = (
        UniqueConstraint(
            "data_room_id", "email", name="uq_vdr_participant_email"
        ),
    )


class VdrDocumentPermission(Base, TimestampMixin):
    """
    Per-document permission grant within a Virtual Data Room.

    When participant_id is NULL, the permission applies to all participants.
    Specific participant permissions override room-level defaults.
    """

    __tablename__ = "vdr_document_permissions"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    data_room_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("virtual_data_rooms.id"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("deal_documents.id"), nullable=False, index=True
    )
    participant_id: Mapped[str | None] = mapped_column(
        UUIDType, ForeignKey("vdr_participants.id")
    )
    can_view: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_download: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_print: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    data_room = relationship("VirtualDataRoom", back_populates="document_permissions")
    document = relationship("DealDocument", back_populates="vdr_permissions")
    participant = relationship("VdrParticipant")


class VdrActivityLog(Base):
    """
    Page-level view analytics for Virtual Data Room documents.

    No TimestampMixin — uses single timestamp. Append-only like audit log.
    """

    __tablename__ = "vdr_activity_log"

    id: Mapped[str] = mapped_column(
        UUIDType, primary_key=True, default=lambda: str(uuid4())
    )
    data_room_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("virtual_data_rooms.id"), nullable=False, index=True
    )
    participant_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("vdr_participants.id"), nullable=False, index=True
    )
    document_id: Mapped[str] = mapped_column(
        UUIDType, ForeignKey("deal_documents.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    # Values: viewed, downloaded, printed
    page_number: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
