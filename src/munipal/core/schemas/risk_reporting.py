"""
Risk reporting schemas (Phase 5).

Defines internal-only diagnostics contracts for:
- canonical risk dimensions
- benchmark cohort metadata
- confidence and reliability outputs
- benchmark posture scoring outputs
- quantitative guardrail checks with tolerance bands
- synthesized prioritized actions linked to risk findings
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from munipal.core.schemas.base import BaseSchema


class RiskReliabilityBand(str, Enum):
    """Reliability band for confidence interpretation."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskProjectStatus(str, Enum):
    """Project evidence status for a risk dimension."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    MISSING = "missing"


class RiskGapSeverity(str, Enum):
    """Severity of evidence gaps for a risk dimension."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskBenchmarkPosition(str, Enum):
    """Relative risk posture versus benchmark corpus."""

    ABOVE = "above"
    AT = "at"
    BELOW = "below"


class RiskGuardrailStatus(str, Enum):
    """Evaluation status for a quantitative guardrail check."""

    PASS = "pass"
    WATCH = "watch"
    BREACH = "breach"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class RiskActionPriority(str, Enum):
    """Priority tier for synthesized risk actions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskIntegrationMode(str, Enum):
    """Integration mode for BFMS consumption."""

    FULL = "full"
    FALLBACK = "fallback"


class RiskBenchmarkCohort(BaseSchema):
    """Cohort metadata required for benchmark-aware risk outputs."""

    sector: str = Field(..., min_length=1)
    issuer_size_band: str = Field(..., min_length=1)
    deal_type: str = Field(..., min_length=1)
    recency_window: str = Field(..., min_length=1)
    sample_size: int = Field(..., ge=1)


class RiskBenchmarkStats(BaseSchema):
    """Benchmark summary statistics for one risk dimension."""

    n_issuances: int = Field(..., ge=0)
    n_disclosures: int = Field(..., ge=0)
    mitigation_rate: float = Field(..., ge=0.0, le=1.0)
    severity_distribution: dict[str, float] = Field(default_factory=dict)


class RiskConfidence(BaseSchema):
    """Confidence and reliability metadata for one risk dimension."""

    score: float = Field(..., ge=0.0, le=1.0)
    reliability_band: RiskReliabilityBand
    uncertainty_note: str | None = None


class RiskDimensionDiagnostics(BaseSchema):
    """Canonical risk diagnostics payload per dimension."""

    dimension_id: str
    project_status: RiskProjectStatus
    gap_severity: RiskGapSeverity
    benchmark_position: RiskBenchmarkPosition
    posture_score: float = Field(..., ge=0.0, le=1.0)
    posture_explainer: str = Field(..., min_length=1)
    benchmark_stats: RiskBenchmarkStats
    confidence: RiskConfidence
    evidence_count: int = Field(0, ge=0)
    conflict_count: int = Field(0, ge=0)
    advanced_metrics: dict[str, float] = Field(default_factory=dict)
    advanced_analytics_applied: bool = False
    advanced_analytics_note: str | None = None


class RiskOverallPosture(BaseSchema):
    """Overall project posture versus benchmark corpus."""

    benchmark_position: RiskBenchmarkPosition
    posture_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str = Field(..., min_length=1)


class RiskGuardrailThreshold(BaseSchema):
    """Target and tolerance bounds for a quantitative metric."""

    target_min: float | None = None
    target_max: float | None = None
    tolerance_min: float | None = None
    tolerance_max: float | None = None


class RiskGuardrailCheck(BaseSchema):
    """One quantitative guardrail metric evaluation."""

    guardrail_id: str = Field(..., min_length=1)
    metric_name: str = Field(..., min_length=1)
    status: RiskGuardrailStatus
    violation: bool = False
    observed_value: float | None = None
    unit: str | None = None
    benchmark_percentile_band: str | None = None
    threshold: RiskGuardrailThreshold
    evidence_paths: list[str] = Field(default_factory=list)
    rationale: str = Field(..., min_length=1)


class RiskActionItem(BaseSchema):
    """Action synthesized from risk gaps and/or guardrail outcomes."""

    action_id: str = Field(..., min_length=1)
    priority: RiskActionPriority
    owner: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)
    evidence_required: list[str] = Field(default_factory=list)
    target_date_hint: str = Field(..., min_length=1)
    expected_impact: str = Field(..., min_length=1)
    source_refs: list[str] = Field(default_factory=list)


class RiskInternalExecutiveSummary(BaseSchema):
    """High-level executive summary for internal risk report consumption."""

    overall_benchmark_position: RiskBenchmarkPosition
    overall_posture_score: float = Field(..., ge=0.0, le=1.0)
    reliability_low_dimensions: int = Field(0, ge=0)
    guardrail_breaches: int = Field(0, ge=0)
    guardrail_watches: int = Field(0, ge=0)
    high_priority_actions: int = Field(0, ge=0)
    top_findings: list[str] = Field(default_factory=list)


class RiskReadinessInput(BaseSchema):
    """Ready-to-consume risk block for readiness services."""

    critical_risk_flags: list[str] = Field(default_factory=list)
    directional_guidance_only: bool = False
    recommended_actions: list[RiskActionItem] = Field(default_factory=list)


class RiskAdvisoryStatement(BaseSchema):
    """Advisory-oriented statement derived from internal diagnostics."""

    dimension_id: str = Field(..., min_length=1)
    statement: str = Field(..., min_length=1)
    gap_severity: RiskGapSeverity
    benchmark_position: RiskBenchmarkPosition
    reliability_band: RiskReliabilityBand


class RiskAdvisoryInput(BaseSchema):
    """Ready-to-consume risk block for advisory package generation."""

    material_risk_statements: list[RiskAdvisoryStatement] = Field(default_factory=list)
    mitigant_highlights: list[str] = Field(default_factory=list)
    action_briefs: list[str] = Field(default_factory=list)


class RiskExternalComplianceCheck(BaseSchema):
    """Disclosure-safety checks for external risk brief generation."""

    rule_id: str = Field(..., min_length=1)
    passed: bool = True
    detail: str = Field(..., min_length=1)


class RiskExternalActionBrief(BaseSchema):
    """External-safe action summary without internal diagnostics metadata."""

    action_id: str = Field(..., min_length=1)
    priority: RiskActionPriority
    owner: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    target_date_hint: str = Field(..., min_length=1)
    expected_impact: str = Field(..., min_length=1)


class RiskExternalBriefResponse(BaseSchema):
    """Versioned external advisory risk brief contract (JSON + Markdown)."""

    contract_version: str = "risk-external-v1"
    generated_at: datetime
    project_id: UUID
    cohort: RiskBenchmarkCohort
    overall_benchmark_position: RiskBenchmarkPosition
    overall_posture_score: float = Field(..., ge=0.0, le=1.0)
    material_risk_statements: list[RiskAdvisoryStatement] = Field(default_factory=list)
    mitigant_summary: list[str] = Field(default_factory=list)
    key_assumptions: list[str] = Field(default_factory=list)
    advisory_next_steps: list[RiskExternalActionBrief] = Field(default_factory=list)
    compliance_checks: list[RiskExternalComplianceCheck] = Field(default_factory=list)
    markdown_brief: str = Field(..., min_length=1)


class RiskBfmsIntegrationResponse(BaseSchema):
    """
    Versioned BFMS integration contract with graceful fallback metadata.

    This contract is intentionally compact so BFMS can consume a stable payload
    without coupling to internal diagnostics internals.
    """

    contract_version: str = "risk-bfms-integration-v1"
    generated_at: datetime
    project_id: UUID
    cohort: RiskBenchmarkCohort
    integration_mode: RiskIntegrationMode
    fallback_reasons: list[str] = Field(default_factory=list)
    overall_benchmark_position: RiskBenchmarkPosition
    overall_posture_score: float = Field(..., ge=0.0, le=1.0)
    reliability_low_dimensions: int = Field(0, ge=0)
    directional_guidance_only: bool = False
    critical_risk_flags: list[str] = Field(default_factory=list)
    material_risk_statements: list[RiskAdvisoryStatement] = Field(default_factory=list)
    advisory_next_steps: list[RiskExternalActionBrief] = Field(default_factory=list)
    key_assumptions: list[str] = Field(default_factory=list)
    compliance_checks: list[RiskExternalComplianceCheck] = Field(default_factory=list)
    internal_report_contract_version: str = "risk-internal-v1"
    external_brief_contract_version: str = "risk-external-v1"


class RiskActionRequestSyncItem(BaseSchema):
    """Outcome for one risk action sync attempt to information requests."""

    action_id: str = Field(..., min_length=1)
    operation: str = Field(..., min_length=1)
    request_id: UUID | None = None
    request_code: str | None = None
    request_status: str | None = None


class RiskActionSyncResponse(BaseSchema):
    """Sync summary for risk actions mapped into information requests."""

    project_id: UUID
    synced_at: datetime
    total_actions: int = Field(0, ge=0)
    created_count: int = Field(0, ge=0)
    updated_count: int = Field(0, ge=0)
    skipped_count: int = Field(0, ge=0)
    synced_requests: list[RiskActionRequestSyncItem] = Field(default_factory=list)


class RiskOverrideDecisionRequest(BaseSchema):
    """Override decision input for governed risk score/guardrail adjustments."""

    project_id: UUID
    target_ref: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=5)
    previous_value: str | None = None
    override_value: str = Field(..., min_length=1)
    notes: str | None = None


class RiskOverrideDecisionResponse(BaseSchema):
    """Recorded override decision payload."""

    decision_id: UUID
    project_id: UUID
    actor_id: str = Field(..., min_length=1)
    target_ref: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=5)
    recorded_at: datetime


class RiskActionAcceptanceRequest(BaseSchema):
    """Accept a synthesized risk action for execution."""

    project_id: UUID
    reason: str = Field(..., min_length=5)
    notes: str | None = None


class RiskActionAcceptanceResponse(BaseSchema):
    """Recorded action-acceptance payload."""

    action_id: str = Field(..., min_length=1)
    project_id: UUID
    actor_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=5)
    accepted_at: datetime


class RiskDiagnosticsResponse(BaseSchema):
    """Internal diagnostics response for risk reporting foundation."""

    project_id: UUID
    cohort: RiskBenchmarkCohort
    dimensions: list[RiskDimensionDiagnostics]
    overall_posture: RiskOverallPosture
    guardrails: list[RiskGuardrailCheck]
    actions: list[RiskActionItem]


class RiskInternalReportResponse(BaseSchema):
    """Versioned internal risk report contract (JSON + Markdown)."""

    contract_version: str = "risk-internal-v1"
    generated_at: datetime
    project_id: UUID
    cohort: RiskBenchmarkCohort
    executive_summary: RiskInternalExecutiveSummary
    diagnostics: RiskDiagnosticsResponse
    readiness_input: RiskReadinessInput
    advisory_input: RiskAdvisoryInput
    markdown_report: str = Field(..., min_length=1)
