"""
Schemas for the Document Management System.

Covers deal documents, templates, clauses, reviews, signers,
virtual data rooms, and audit logging.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import BaseSchema, TimestampSchema, UUIDSchema

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class DocumentStatus(str, Enum):
    """Document lifecycle states."""

    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    EXECUTION = "execution"
    SIGNED = "signed"
    FILED = "filed"
    ARCHIVED = "archived"


class DocumentCategory(str, Enum):
    """Document type categories."""

    TEMPLATED = "templated"
    NEGOTIATED = "negotiated"
    PROFESSIONAL_REPORT = "professional_report"
    REGULATORY = "regulatory"


class DealVertical(str, Enum):
    """Deal verticals for document type registry."""

    MUNI = "muni"
    PE = "pe"
    RE = "re"
    PROJECT_FINANCE = "project_finance"


class RetentionPolicy(str, Enum):
    """Compliance retention policies."""

    STANDARD_6YR = "standard_6yr"
    INDEFINITE = "indefinite"
    BOND_LIFE_PLUS_3YR = "bond_life_plus_3yr"


class SignatureStatus(str, Enum):
    """E-signature request statuses."""

    PENDING = "pending"
    SIGNED = "signed"
    DECLINED = "declined"
    EXPIRED = "expired"


class ReviewStatus(str, Enum):
    """Document review statuses."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class SignerStatus(str, Enum):
    """Individual signer statuses."""

    PENDING = "pending"
    SENT = "sent"
    VIEWED = "viewed"
    SIGNED = "signed"
    DECLINED = "declined"
    EXPIRED = "expired"


class VdrRole(str, Enum):
    """VDR participant roles."""

    VIEWER = "viewer"
    DOWNLOADER = "downloader"
    UPLOADER = "uploader"
    ADMIN = "admin"


class SnapshotReason(str, Enum):
    """Reasons for creating a version snapshot."""

    AUTO_SAVE = "auto_save"
    MANUAL_SAVE = "manual_save"
    PRE_REVIEW = "pre_review"
    PRE_SIGNATURE = "pre_signature"
    STATUS_CHANGE = "status_change"


# ---------------------------------------------------------------------------
# Document Type Schemas
# ---------------------------------------------------------------------------


class DealDocumentTypeRead(UUIDSchema, TimestampSchema):
    """Read schema for document type registry entries."""

    code: str
    display_name: str
    category: DocumentCategory
    deal_vertical: DealVertical
    description: str | None = None
    default_workflow: str
    retention_policy: RetentionPolicy
    requires_signature: bool
    is_active: bool
    sort_order: int


# ---------------------------------------------------------------------------
# Template Schemas
# ---------------------------------------------------------------------------


class TemplateCreate(BaseSchema):
    """Schema for creating a document template."""

    name: str = Field(..., min_length=1, max_length=255)
    document_type_id: UUID
    jurisdiction: str | None = Field(None, max_length=100)
    template_body: str = Field(..., min_length=1)
    variable_schema: dict | None = None


class TemplateUpdate(BaseSchema):
    """Schema for updating a template."""

    name: str | None = Field(None, min_length=1, max_length=255)
    jurisdiction: str | None = Field(None, max_length=100)
    template_body: str | None = None
    variable_schema: dict | None = None
    is_active: bool | None = None


class TemplateRead(UUIDSchema, TimestampSchema):
    """Full template read schema."""

    name: str
    document_type_id: UUID
    document_type: DealDocumentTypeRead | None = None
    jurisdiction: str | None
    version: int
    template_body: str
    variable_schema: dict | None
    is_active: bool
    is_system: bool
    tenant_id: str


class TemplateSummary(UUIDSchema):
    """Minimal template info for listings."""

    name: str
    document_type_id: UUID
    document_type_code: str | None = None
    jurisdiction: str | None
    version: int
    is_active: bool
    is_system: bool
    updated_at: datetime


class TemplateRenderRequest(BaseSchema):
    """Request to render a template with variables."""

    variables: dict = Field(default_factory=dict)


class TemplateRenderResult(BaseSchema):
    """Template rendering result with structured output and diagnostics."""

    template_id: UUID
    content_json: dict | None = None
    rendered_text: str
    missing_variables: list[str] = Field(default_factory=list)
    used_variables: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Clause Schemas
# ---------------------------------------------------------------------------


class ClauseCreate(BaseSchema):
    """Schema for creating a template clause."""

    template_id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    content_json: dict
    description: str | None = Field(None, max_length=2000)
    jurisdiction: str | None = Field(None, max_length=100)


class ClauseUpdate(BaseSchema):
    """Schema for updating a template clause."""

    name: str | None = Field(None, min_length=1, max_length=255)
    category: str | None = Field(None, min_length=1, max_length=100)
    content_json: dict | None = None
    description: str | None = Field(None, max_length=2000)
    jurisdiction: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class ClauseRead(UUIDSchema, TimestampSchema):
    """Full clause read schema."""

    template_id: UUID | None
    name: str
    category: str
    content_json: dict
    description: str | None
    jurisdiction: str | None
    is_active: bool
    tenant_id: str


class ClauseRecommendationRequest(BaseSchema):
    """Input for deal-structure-driven clause recommendations."""

    document_type_code: str | None = Field(None, max_length=100)
    deal_vertical: DealVertical = DealVertical.MUNI
    jurisdiction: str | None = Field(None, max_length=100)
    deal_features: list[str] = Field(default_factory=list)
    text_query: str | None = Field(None, max_length=500)
    limit: int = Field(20, ge=1, le=100)


class ClauseRecommendation(BaseSchema):
    """Recommended clause candidate with scoring details."""

    clause_id: UUID | None = None
    clause_name: str
    category: str
    score: float
    reason: str
    source: str
    sample_documents: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Deal Document Schemas
# ---------------------------------------------------------------------------


class UserSummary(UUIDSchema):
    """Minimal user reference for document ownership."""

    email: str | None = None
    full_name: str | None = None


class DealDocumentCreate(BaseSchema):
    """Schema for creating a new deal document."""

    project_id: UUID
    document_type_id: UUID
    title: str = Field(..., min_length=1, max_length=500)
    template_id: UUID | None = None
    template_variables: dict | None = None
    content_json: dict | None = None
    assigned_to_id: UUID | None = None


class DealDocumentUpdate(BaseSchema):
    """Schema for updating document metadata."""

    title: str | None = Field(None, min_length=1, max_length=500)
    assigned_to_id: UUID | None = None


class ContentUpdateRequest(BaseSchema):
    """Schema for updating document content (editor auto-save)."""

    content_json: dict
    auto_snapshot: bool = True


class StatusTransitionRequest(BaseSchema):
    """Schema for transitioning document workflow status."""

    new_status: DocumentStatus
    comment: str | None = None


class DealDocumentRead(UUIDSchema, TimestampSchema):
    """Full deal document read schema."""

    project_id: UUID
    title: str
    document_number: str | None
    document_type: DealDocumentTypeRead
    status: DocumentStatus
    content_json: dict | None
    content_html: str | None = None
    template_id: UUID | None
    template_version: int | None
    signature_request_id: str | None = None
    signature_status: str | None
    filed_to: str | None
    filed_at: datetime | None
    filing_reference: str | None
    retention_policy: RetentionPolicy
    legal_hold: bool
    retention_expires_at: datetime | None
    artifact_id: UUID | None
    created_by: UserSummary | None = None
    assigned_to: UserSummary | None = None
    version_count: int = 0
    current_version: int = 0


class DealDocumentSummary(UUIDSchema):
    """Minimal document info for listings."""

    title: str
    document_number: str | None
    document_type_code: str | None = None
    document_type_name: str | None = None
    status: DocumentStatus
    signature_status: str | None
    legal_hold: bool
    assigned_to_name: str | None = None
    updated_at: datetime


# ---------------------------------------------------------------------------
# Version Schemas
# ---------------------------------------------------------------------------


class DealDocumentVersionRead(UUIDSchema, TimestampSchema):
    """Version snapshot read schema."""

    document_id: UUID
    version_number: int
    content_hash: str
    change_summary: str | None
    snapshot_reason: SnapshotReason
    created_by_id: UUID
    storage_path: str | None


class VersionDiff(BaseSchema):
    """Result of comparing two document versions."""

    document_id: UUID
    version_a: int
    version_b: int
    content_a: dict | None
    content_b: dict | None


# ---------------------------------------------------------------------------
# Review Schemas
# ---------------------------------------------------------------------------


class ReviewAssignRequest(BaseSchema):
    """Schema for assigning a reviewer."""

    reviewer_id: UUID


class DocumentReviewRead(UUIDSchema, TimestampSchema):
    """Document review read schema."""

    document_id: UUID
    reviewer_id: UUID
    reviewer_email: str | None = None
    status: ReviewStatus
    comments: str | None
    review_version: int | None
    completed_at: datetime | None


class ReviewDecisionRequest(BaseSchema):
    """Schema for submitting a review decision."""

    status: ReviewStatus
    comments: str | None = None


# ---------------------------------------------------------------------------
# Signer Schemas
# ---------------------------------------------------------------------------


class SignerCreate(BaseSchema):
    """Schema for adding a signer to a document."""

    signer_name: str = Field(..., min_length=1, max_length=255)
    signer_email: str = Field(..., min_length=1, max_length=255)
    signer_role: str = Field(..., min_length=1, max_length=100)
    signing_order: int = Field(0, ge=0)


class SignatureRequestCreate(BaseSchema):
    """Schema for creating a signature request."""

    signers: list[SignerCreate] = Field(..., min_length=1)
    message: str | None = Field(None, max_length=2000)
    subject: str | None = Field(None, max_length=255)


class DocumentSignerRead(UUIDSchema, TimestampSchema):
    """Signer read schema."""

    document_id: UUID
    signer_name: str
    signer_email: str
    signer_role: str
    signing_order: int
    status: SignerStatus
    signed_at: datetime | None
    ip_address: str | None


class SignatureStatusRead(BaseSchema):
    """Signature request status overview."""

    document_id: UUID
    signature_request_id: str | None
    overall_status: str | None
    signers: list[DocumentSignerRead]


# ---------------------------------------------------------------------------
# Audit Log Schemas
# ---------------------------------------------------------------------------


class AuditEntryRead(UUIDSchema):
    """Audit log entry read schema."""

    document_id: UUID
    actor_id: UUID
    actor_email: str | None
    action: str
    details: dict | None
    ip_address: str | None
    timestamp: datetime


# ---------------------------------------------------------------------------
# Virtual Data Room Schemas
# ---------------------------------------------------------------------------


class VdrCreate(BaseSchema):
    """Schema for creating a Virtual Data Room."""

    project_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    require_nda: bool = True
    nda_template_id: UUID | None = None
    watermark_enabled: bool = True
    default_access_expiry_days: int = Field(30, ge=1, le=365)
    settings: dict | None = None


class VdrUpdate(BaseSchema):
    """Schema for updating VDR settings."""

    name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None
    require_nda: bool | None = None
    nda_template_id: UUID | None = None
    watermark_enabled: bool | None = None
    default_access_expiry_days: int | None = Field(None, ge=1, le=365)
    settings: dict | None = None


class VdrRead(UUIDSchema, TimestampSchema):
    """Full VDR read schema."""

    project_id: UUID
    name: str
    is_active: bool
    require_nda: bool
    nda_template_id: UUID | None
    watermark_enabled: bool
    default_access_expiry_days: int
    settings: dict | None
    participant_count: int = 0
    document_count: int = 0


class ParticipantInvite(BaseSchema):
    """Schema for inviting a participant to a VDR."""

    email: str = Field(..., min_length=1, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    organization: str | None = Field(None, max_length=255)
    role: VdrRole = VdrRole.VIEWER
    access_expiry_days: int | None = Field(None, ge=1, le=365)


class ParticipantRead(UUIDSchema, TimestampSchema):
    """VDR participant read schema."""

    data_room_id: UUID
    email: str
    full_name: str
    organization: str | None
    role: VdrRole
    nda_accepted: bool
    nda_accepted_at: datetime | None
    access_expires_at: datetime | None
    is_active: bool
    last_accessed_at: datetime | None


class PermissionUpdate(BaseSchema):
    """Schema for updating document permissions."""

    can_view: bool = True
    can_download: bool = False
    can_print: bool = False


class VdrDocPermRead(UUIDSchema):
    """VDR document permission read schema."""

    data_room_id: UUID
    document_id: UUID
    participant_id: UUID | None
    can_view: bool
    can_download: bool
    can_print: bool


class VdrActivityCreate(BaseSchema):
    """Schema for logging VDR activity."""

    document_id: UUID
    action: str = Field(..., max_length=30)
    page_number: int | None = None
    duration_seconds: int | None = None


class DocumentAnalytics(BaseSchema):
    """Analytics for a single document in the VDR."""

    document_id: UUID
    total_views: int = 0
    unique_viewers: int = 0
    total_downloads: int = 0
    avg_view_duration_seconds: float | None = None
    page_view_distribution: dict | None = None


class RoomAnalytics(BaseSchema):
    """Analytics for the entire VDR."""

    data_room_id: UUID
    total_views: int = 0
    unique_participants: int = 0
    total_downloads: int = 0
    most_viewed_documents: list[dict] | None = None
    activity_by_date: list[dict] | None = None


class ParticipantActivity(BaseSchema):
    """Activity summary for a single participant."""

    participant_id: UUID
    documents_viewed: int = 0
    documents_downloaded: int = 0
    total_view_seconds: int = 0
    last_activity: datetime | None = None
    document_details: list[dict] | None = None


# ---------------------------------------------------------------------------
# Closing Checklist
# ---------------------------------------------------------------------------


class ChecklistItemRead(BaseSchema):
    """Auto-generated closing checklist item."""

    document_type_code: str
    document_type_name: str
    category: DocumentCategory
    requires_signature: bool
    document_id: UUID | None = None
    document_status: DocumentStatus | None = None
    is_complete: bool = False


# ---------------------------------------------------------------------------
# Model-to-Document Consistency
# ---------------------------------------------------------------------------


class ConsistencyDomain(str, Enum):
    """Supported legal consistency domains."""

    COVENANT = "covenant"
    WATERFALL = "waterfall"


class ConsistencySeverity(str, Enum):
    """Consistency issue severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ConsistencyCheckRequest(BaseSchema):
    """Request payload for model-to-document consistency checks."""

    domain: ConsistencyDomain
    model_terms: dict = Field(default_factory=dict)
    legal_terms: dict | None = None
    tolerance_ratio: float = Field(0.001, ge=0.0, le=1.0)
    strict: bool = False


class ConsistencyIssue(BaseSchema):
    """A single mismatch or warning from a consistency check."""

    field: str
    legal_value: str | float | int | bool | None = None
    model_value: str | float | int | bool | None = None
    severity: ConsistencySeverity
    message: str
    delta: float | None = None


class ConsistencyCheckResult(BaseSchema):
    """Result of comparing legal terms against model terms."""

    document_id: UUID
    domain: ConsistencyDomain
    extracted_legal_terms: dict = Field(default_factory=dict)
    model_terms: dict = Field(default_factory=dict)
    issues: list[ConsistencyIssue] = Field(default_factory=list)
    checked_fields: int = 0
    matched_fields: int = 0
    consistency_score: float = 0.0
    is_consistent: bool = False
