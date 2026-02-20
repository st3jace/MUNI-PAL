"""
Bifurcated deliverable schemas for v2.

Per spec: Split the current monolithic handoff pack into:
- InternalReadinessReport (for sponsor team use)
- ExternalAdvisoryPackage (for municipal advisor consumption)
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import (
    BaseSchema,
    ChecklistPhase,
    ReadinessDimension,
    TimestampSchema,
    UUIDSchema,
)
from munipal.core.schemas.disclosure import TBDSeverity


# -----------------------------------------------------------------------------
# Internal Readiness Report Schemas
# -----------------------------------------------------------------------------


class ReportDimensionScore(BaseSchema):
    """Dimension score for reports."""

    dimension: ReadinessDimension
    dimension_name: str
    score: float = Field(..., ge=0.0, le=5.0)
    weight: float
    status_emoji: str  # e.g., "green_circle", "yellow_circle", "red_circle"
    what_measured: str
    current_state_explanation: str
    why_it_matters: str
    supporting_facts: list[dict] = Field(default_factory=list)  # {schema_path, value, confidence}
    related_gaps: list[dict] = Field(default_factory=list)  # {title, severity}
    recommended_action: str | None = None


class ExecutiveSummary(BaseSchema):
    """Executive summary section for internal report."""

    overall_score: float = Field(..., ge=0.0, le=10.0)
    score_interpretation: str
    status_emoji: str
    recent_achievements: list[dict] = Field(default_factory=list)  # {description, date}
    critical_blockers: list[dict] = Field(default_factory=list)  # {title, summary, consequences, owner}


class ReadinessDashboard(BaseSchema):
    """Readiness dashboard section for internal report."""

    overall_score: float
    dimensions: list[ReportDimensionScore] = Field(default_factory=list)
    score_interpretation_guide: dict = Field(default_factory=dict)


class GapAnalysisSection(BaseSchema):
    """Gap analysis section for internal report."""

    summary: dict = Field(default_factory=dict)  # {critical_count, high_count, medium_count, low_count}
    critical_gaps: list[dict] = Field(default_factory=list)
    high_gaps: list[dict] = Field(default_factory=list)
    medium_gaps: list[dict] = Field(default_factory=list)
    low_gaps: list[dict] = Field(default_factory=list)


class InformationRequestsSection(BaseSchema):
    """Information requests section for internal report."""

    summary: dict = Field(default_factory=dict)  # status counts
    by_owner: list[dict] = Field(default_factory=list)
    overdue_requests: list[dict] = Field(default_factory=list)
    full_requests: list[dict] = Field(default_factory=list)


class ChecklistStatusSection(BaseSchema):
    """Checklist status section for internal report."""

    phase_summary: list[dict] = Field(default_factory=list)
    phases: dict[str, dict] = Field(default_factory=dict)  # phase -> {completion_percent, items, etc.}


class EvidenceIndexSection(BaseSchema):
    """Evidence index section for internal report."""

    summary: dict = Field(default_factory=dict)  # counts by status
    by_domain: dict[str, list[dict]] = Field(default_factory=dict)  # domain -> facts
    conflicts: list[dict] = Field(default_factory=list)


class AssumptionRegisterSection(BaseSchema):
    """Assumption register section for internal report."""

    summary: dict = Field(default_factory=dict)  # counts and avg confidence by category
    assumptions: list[dict] = Field(default_factory=list)
    high_impact_assumptions: list[dict] = Field(default_factory=list)


class InternalReadinessReportBase(BaseSchema):
    """Base schema for internal readiness reports."""

    version: int = 1
    playbook_version: str | None = None
    bfms_version: str | None = None


class InternalReadinessReportCreate(InternalReadinessReportBase):
    """Schema for creating an internal readiness report."""

    project_id: UUID


class InternalReadinessReportRead(InternalReadinessReportBase, UUIDSchema, TimestampSchema):
    """Schema for reading an internal readiness report."""

    project_id: UUID

    # Generation status
    is_complete: bool = False
    generation_started_at: datetime | None = None
    generation_completed_at: datetime | None = None

    # Sections
    executive_summary: ExecutiveSummary | dict = Field(default_factory=dict)
    readiness_dashboard: ReadinessDashboard | dict = Field(default_factory=dict)
    gap_analysis: GapAnalysisSection | dict = Field(default_factory=dict)
    information_requests_section: InformationRequestsSection | dict = Field(default_factory=dict)
    checklist_status: ChecklistStatusSection | dict = Field(default_factory=dict)
    evidence_index: EvidenceIndexSection | dict = Field(default_factory=dict)
    assumption_register: AssumptionRegisterSection | dict = Field(default_factory=dict)

    # Snapshot metrics
    overall_score: float | None = None
    dimension_scores: list[dict] = Field(default_factory=list)
    critical_gap_count: int = 0
    high_gap_count: int = 0
    open_request_count: int = 0
    overdue_request_count: int = 0
    facts_count: int = 0

    # Storage
    pdf_storage_path: str | None = None
    md_storage_path: str | None = None


class InternalReadinessReportSummary(UUIDSchema):
    """Summary of an internal report for listings."""

    project_id: UUID
    version: int
    overall_score: float | None
    critical_gap_count: int
    open_request_count: int
    is_complete: bool
    created_at: datetime


# -----------------------------------------------------------------------------
# External Advisory Package Schemas
# -----------------------------------------------------------------------------


class CoverPage(BaseSchema):
    """Cover page for external advisory package."""

    project_name: str
    location: str | None = None
    bond_type: str = "Revenue Bonds"
    structure_description: str  # e.g., "Capital Appreciation Bond Structure with SLB Features"
    prepared_for: str = "Municipal Advisor Review"
    prepared_by: str
    prepared_date: datetime
    disclaimer_text: str


class ExternalExecutiveSummary(BaseSchema):
    """Executive summary for external package."""

    transaction_overview: str
    key_metrics: dict = Field(default_factory=dict)  # {metric_name: value}
    structural_highlights: list[str] = Field(default_factory=list)
    information_pending: list[str] = Field(default_factory=list)
    next_steps: str


class DealOverviewMemo(BaseSchema):
    """Deal overview memo for external package."""

    project_summary: str
    issuance_intent: str
    transaction_parties: dict = Field(default_factory=dict)  # role -> details
    use_of_proceeds: dict = Field(default_factory=dict)  # sources and uses
    revenue_model_summary: str
    structural_notes: str


class FinancialTables(BaseSchema):
    """Financial tables for external package."""

    capital_structure: dict = Field(default_factory=dict)
    revenue_projections: list[dict] = Field(default_factory=list)  # year-by-year
    cab_accretion_schedule: list[dict] = Field(default_factory=list)
    debt_service_schedule: list[dict] = Field(default_factory=list)
    dscr_analysis: dict = Field(default_factory=dict)  # scenario -> metrics
    sensitivity_tables: list[dict] = Field(default_factory=list)
    disclaimer: str = ""


class SLBKPIBrief(BaseSchema):
    """SLB KPI brief for external package."""

    framework_alignment: str
    kpi_summary_table: list[dict] = Field(default_factory=list)  # kpi details
    kpi_details: list[dict] = Field(default_factory=list)  # full kpi info
    economic_linkage: dict = Field(default_factory=dict)  # event -> consequence
    observation_schedule: list[str] = Field(default_factory=list)
    verification_protocol: str | None = None


class KeyAssumption(BaseSchema):
    """A key assumption for external package."""

    category: str  # Financial, Operational, Market
    assumption: str
    value: str
    basis: str


class ExternalAdvisoryPackageBase(BaseSchema):
    """Base schema for external advisory packages."""

    version: int = 1
    title: str
    generated_for: str
    playbook_version: str | None = None
    bfms_version: str | None = None


class ExternalAdvisoryPackageCreate(ExternalAdvisoryPackageBase):
    """Schema for creating an external advisory package."""

    project_id: UUID


class ExternalAdvisoryPackageRead(ExternalAdvisoryPackageBase, UUIDSchema, TimestampSchema):
    """Schema for reading an external advisory package."""

    project_id: UUID

    # Generation status
    is_complete: bool = False
    generation_started_at: datetime | None = None
    generation_completed_at: datetime | None = None

    # Sections
    cover_page: CoverPage | dict = Field(default_factory=dict)
    executive_summary: ExternalExecutiveSummary | dict = Field(default_factory=dict)
    deal_overview: DealOverviewMemo | dict = Field(default_factory=dict)
    financial_tables: FinancialTables | dict = Field(default_factory=dict)
    slb_brief: SLBKPIBrief | dict = Field(default_factory=dict)
    key_assumptions: list[KeyAssumption | dict] = Field(default_factory=list)
    disclaimer: str = ""

    # Disclosure document reference
    disclosure_document_id: UUID | None = None

    # Quality metrics
    disclosure_completeness_score: float | None = None
    critical_tbd_count: int = 0
    high_tbd_count: int = 0
    readiness_score_at_generation: float | None = None

    # Quality gate status
    ready_for_distribution: bool = False
    distribution_issues: list[str] = Field(default_factory=list)

    # Storage
    pdf_storage_path: str | None = None
    docx_storage_path: str | None = None
    md_storage_path: str | None = None


class ExternalAdvisoryPackageSummary(UUIDSchema):
    """Summary of an external package for listings."""

    project_id: UUID
    version: int
    title: str
    generated_for: str
    ready_for_distribution: bool
    disclosure_completeness_score: float | None
    critical_tbd_count: int
    is_complete: bool
    created_at: datetime


# -----------------------------------------------------------------------------
# Generation Schemas
# -----------------------------------------------------------------------------


class GenerateInternalReportRequest(BaseSchema):
    """Request to generate an internal readiness report."""

    project_id: UUID
    force_regenerate: bool = False


class GenerateInternalReportResponse(BaseSchema):
    """Response from internal report generation."""

    report_id: UUID
    status: str
    message: str | None = None
    celery_task_id: str | None = None


class GenerateExternalPackageRequest(BaseSchema):
    """Request to generate an external advisory package."""

    project_id: UUID
    title: str
    generated_for: str
    include_disclosure: bool = True
    force_regenerate: bool = False


class GenerateExternalPackageResponse(BaseSchema):
    """Response from external package generation."""

    package_id: UUID
    status: str
    message: str | None = None
    celery_task_id: str | None = None


class DistributionValidation(BaseSchema):
    """Validation result for package distribution readiness."""

    ready_for_distribution: bool
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Export Schemas
# -----------------------------------------------------------------------------


class ExportFormat(BaseSchema):
    """Available export formats."""

    format: str = Field(..., description="md, pdf, docx, html")


class ExportResponse(BaseSchema):
    """Response from export request."""

    format: str
    filename: str
    storage_path: str | None = None
    download_url: str | None = None
