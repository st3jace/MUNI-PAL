"""Pilot onboarding workflow contracts for BFMS.

The workflow is derived from the pilot navigation system and BFMS operations
playbooks in the OneDrive MUNI-PAL folders. It turns the live-pilot guidance
into reusable platform data: sector playbook assignment, document request,
upload, extraction, review, readiness, and handoff.
"""
from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field

from munipal.core.schemas.base import BaseSchema
from munipal.services.sector_playbooks import SectorPlaybook, get_sector_playbook

PilotRoleName = Literal["operator", "muni_pal", "advisor", "reviewer"]
GateSeverity = Literal["required", "recommended"]


class PilotOnboardingValidationError(ValueError):
    """Raised when a pilot onboarding workflow is incomplete or unsafe."""


class PilotOnboardingStage(StrEnum):
    """Canonical BFMS onboarding stages for an operator pilot."""

    INTAKE = "intake"
    DOCUMENT_REQUEST = "document_request"
    UPLOAD = "upload"
    EXTRACTION = "extraction"
    REVIEW = "review"
    READINESS = "readiness"
    HANDOFF = "handoff"


class PilotRole(BaseSchema):
    """Role participating in the pilot workflow."""

    role: PilotRoleName
    display_name: str = Field(..., min_length=1)
    responsibilities: tuple[str, ...] = Field(..., min_length=1)


class PrePilotGate(BaseSchema):
    """Gate that must be satisfied before a live pilot launches."""

    gate_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    severity: GateSeverity
    required: bool = True
    rationale: str = Field(..., min_length=1)


class SensingLeadLink(BaseSchema):
    """Linkage back to the sensing/lead funnel that created the opportunity."""

    lead_id: str = Field(..., min_length=1)
    source_channel: str = Field(..., min_length=1)
    allowed_sources: tuple[str, ...] = (
        "market_intelligence",
        "readiness_scan",
        "credit_spread_monitor",
        "direct",
    )


class PilotOnboardingStep(BaseSchema):
    """Single stage in the onboarding workflow."""

    stage: PilotOnboardingStage
    display_name: str = Field(..., min_length=1)
    owner_role: PilotRoleName
    participant_roles: tuple[PilotRoleName, ...] = Field(..., min_length=1)
    input_refs: tuple[str, ...] = Field(default_factory=tuple)
    output_refs: tuple[str, ...] = Field(..., min_length=1)
    acceptance_criteria: tuple[str, ...] = Field(..., min_length=1)
    operator_burden_reduction: str = Field(..., min_length=1)


class BurdenReductionMechanism(BaseSchema):
    """How the pilot reduces borrower/operator burden and issuance cost."""

    key: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    cost_of_issuance_rationale: str = Field(..., min_length=1)


class PilotOnboardingWorkflow(BaseSchema):
    """Complete pilot onboarding workflow bound to a sector playbook."""

    workflow_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    playbook: SectorPlaybook
    roles: list[PilotRole] = Field(..., min_length=1)
    pre_pilot_gates: list[PrePilotGate] = Field(..., min_length=1)
    sensing_link: SensingLeadLink | None = None
    evidence_workspace_folders: tuple[str, ...] = Field(..., min_length=1)
    document_request_list: tuple[str, ...] = Field(..., min_length=1)
    stages: list[PilotOnboardingStep] = Field(..., min_length=1)
    burden_reduction_mechanisms: list[BurdenReductionMechanism] = Field(..., min_length=1)
    measurement_hooks: tuple[str, ...] = Field(..., min_length=1)


_REQUIRED_STAGE_SEQUENCE = [
    PilotOnboardingStage.INTAKE,
    PilotOnboardingStage.DOCUMENT_REQUEST,
    PilotOnboardingStage.UPLOAD,
    PilotOnboardingStage.EXTRACTION,
    PilotOnboardingStage.REVIEW,
    PilotOnboardingStage.READINESS,
    PilotOnboardingStage.HANDOFF,
]
_REQUIRED_ROLES: set[PilotRoleName] = {"operator", "muni_pal", "advisor", "reviewer"}
_REQUIRED_GATES = {
    "registered_ma_confirmed",
    "pilot_smoke_test_green",
    "engagement_scope_signed",
}
_REQUIRED_MECHANISMS = {
    "playbook_scoped_document_requests",
    "artifact_vault_reuse_and_hashing",
    "ai_extraction_with_human_review",
    "advisor_ready_handoff_pack",
    "measurement_and_cost_learning",
}
_OPERATOR_WORKSPACE_FOLDERS = (
    "00_WELCOME",
    "01_PROJECT-OVERVIEW",
    "02_FINANCING-STRUCTURE",
    "03_DUE-DILIGENCE",
    "04_CLOSING-DOCUMENTS",
    "05_POST-ISSUANCE-COMPLIANCE",
    "06_REPORTING",
    "07_RESOURCE-LIBRARY",
)


_ROLES = [
    PilotRole(
        role="operator",
        display_name="Operator / Borrower",
        responsibilities=(
            "Confirms entity, project, financing need, and authorized pilot contacts.",
            "Uploads requested documents and answers structured clarification requests.",
            "Completes weekly hours diary during live pilots.",
        ),
    ),
    PilotRole(
        role="muni_pal",
        display_name="Muni-Pal Delivery Team",
        responsibilities=(
            "Creates project workspace and assigns the sector playbook.",
            "Runs ingestion, extraction, readiness, and handoff pack assembly workflows.",
            "Maintains task log, milestone timestamps, and pilot measurement hooks.",
        ),
    ),
    PilotRole(
        role="advisor",
        display_name="Registered Municipal Advisor / Deal Advisor",
        responsibilities=(
            "Provides municipal advisory authority where required.",
            "Reviews BFMS outputs before client-facing reliance.",
            "Receives advisor-ready handoff materials with evidence provenance.",
        ),
    ),
    PilotRole(
        role="reviewer",
        display_name="Bond Strategist / Human Fact Reviewer",
        responsibilities=(
            "Reviews AI-proposed facts before acceptance.",
            "Checks sector terminology, liability boundaries, and deliverable quality.",
            "Approves pilot smoke-test outputs before live pilot launch.",
        ),
    ),
]


_PRE_PILOT_GATES = [
    PrePilotGate(
        gate_id="registered_ma_confirmed",
        display_name="Registered MA confirmed for the deal",
        severity="required",
        rationale="Pilot navigation guidance requires stopping operator engagement until the deal has registered MA coverage.",
    ),
    PrePilotGate(
        gate_id="pilot_smoke_test_green",
        display_name="Synthetic Oakport end-to-end test passed",
        severity="required",
        rationale="Before a live pilot, the WP1-WP6 healthcare/waste smoke test must pass without sector leakage or handoff defects.",
    ),
    PrePilotGate(
        gate_id="engagement_scope_signed",
        display_name="Pilot engagement scope signed",
        severity="required",
        rationale="Clarifies Muni-Pal's support boundary, advisor role, deliverables, and measurement obligations.",
    ),
]


def _document_request_list(playbook: SectorPlaybook) -> tuple[str, ...]:
    return tuple(
        f"{artifact.display_name} ({artifact.requirement_level})"
        for artifact in playbook.required_artifacts
        if artifact.requirement_level in {"required", "recommended"}
    )


def _stages(playbook: SectorPlaybook) -> list[PilotOnboardingStep]:
    sector_label = playbook.metadata.display_name
    artifact_refs = tuple(artifact.artifact_key for artifact in playbook.required_artifacts)
    fact_refs = tuple(fact.path for fact in playbook.fact_definitions)
    readiness_refs = tuple(rule.rule_id for rule in playbook.readiness_rules)
    deliverable_refs = tuple(template.output_key for template in playbook.deliverable_templates)

    return [
        PilotOnboardingStep(
            stage=PilotOnboardingStage.INTAKE,
            display_name="Classify client, tier, sector playbook, and MA status",
            owner_role="muni_pal",
            participant_roles=("operator", "advisor"),
            input_refs=("sensing_lead", "baseline_interview", "pricing_signal"),
            output_refs=(playbook.metadata.playbook_id, "engagement_tier", "ma_status"),
            acceptance_criteria=(
                f"{sector_label} playbook is assigned before document requests are sent.",
                "Registered MA status is confirmed or workflow stops.",
            ),
            operator_burden_reduction="Reuses sensing and baseline interview data so the operator does not repeat qualification information.",
        ),
        PilotOnboardingStep(
            stage=PilotOnboardingStage.DOCUMENT_REQUEST,
            display_name="Generate playbook-scoped document request list",
            owner_role="muni_pal",
            participant_roles=("operator", "reviewer"),
            input_refs=artifact_refs,
            output_refs=("document_request_checklist", "onboarding_package"),
            acceptance_criteria=(
                "Checklist contains only required or recommended artifacts for the assigned sector playbook.",
                "Bond Strategist reviews package for sector terminology before delivery.",
            ),
            operator_burden_reduction="Narrows requests to sector-specific evidence instead of sending a generic bond diligence dump.",
        ),
        PilotOnboardingStep(
            stage=PilotOnboardingStage.UPLOAD,
            display_name="Create evidence workspace and upload artifacts",
            owner_role="operator",
            participant_roles=("muni_pal",),
            input_refs=artifact_refs,
            output_refs=("artifact_ids", "sha256_hashes", "workspace_folders"),
            acceptance_criteria=(
                "Uploaded artifacts are hashed, deduplicated, and mapped to playbook artifact keys.",
                "Workspace follows the operator launch-package folder structure.",
            ),
            operator_burden_reduction="Reusable artifact vault avoids repeated file requests across readiness, modeling, and handoff work.",
        ),
        PilotOnboardingStep(
            stage=PilotOnboardingStage.EXTRACTION,
            display_name="Extract schema-bound facts with provenance",
            owner_role="muni_pal",
            participant_roles=("reviewer",),
            input_refs=fact_refs,
            output_refs=("proposed_facts", "fact_provenance", "confidence_tiers"),
            acceptance_criteria=(
                "Every proposed fact references a declared playbook fact path.",
                "Every fact carries artifact/chunk/page provenance before review.",
            ),
            operator_burden_reduction="Automates first-pass evidence normalization while keeping AI outputs reviewable and rejectable.",
        ),
        PilotOnboardingStep(
            stage=PilotOnboardingStage.REVIEW,
            display_name="Human fact review and conflict resolution",
            owner_role="reviewer",
            participant_roles=("operator", "advisor", "muni_pal"),
            input_refs=("proposed_facts", "source_artifacts"),
            output_refs=("accepted_facts", "rejected_facts", "clarification_requests"),
            acceptance_criteria=(
                "Material facts are accepted, rejected, or sent back for clarification by a human reviewer.",
                "Advisor-facing outputs do not rely on unreviewed AI assertions.",
            ),
            operator_burden_reduction="Bundles clarifications around specific evidence gaps instead of ad hoc email churn.",
        ),
        PilotOnboardingStep(
            stage=PilotOnboardingStage.READINESS,
            display_name="Run deterministic readiness and gap analysis",
            owner_role="muni_pal",
            participant_roles=("reviewer", "advisor"),
            input_refs=readiness_refs,
            output_refs=("readiness_score", "gap_analysis", "dimension_scores"),
            acceptance_criteria=(
                "Readiness rules reference only declared sector facts and artifacts.",
                "Output frames gaps and evidence status, not deal approval or issuance advice.",
            ),
            operator_burden_reduction="Turns accepted evidence into a prioritized gap list the operator can action before expensive professional review cycles.",
        ),
        PilotOnboardingStep(
            stage=PilotOnboardingStage.HANDOFF,
            display_name="Assemble advisor-ready handoff pack",
            owner_role="muni_pal",
            participant_roles=("reviewer", "advisor", "operator"),
            input_refs=deliverable_refs,
            output_refs=("handoff_pack", "evidence_index", "measurement_log"),
            acceptance_criteria=(
                "Handoff pack includes required disclaimers and evidence references.",
                "Task log, hours diary, milestone, and COI measurement hooks are active for the pilot.",
            ),
            operator_burden_reduction="Packages reviewed facts, readiness gaps, assumptions, and evidence index into reusable advisor-ready materials.",
        ),
    ]


def _burden_reduction_mechanisms() -> list[BurdenReductionMechanism]:
    return [
        BurdenReductionMechanism(
            key="playbook_scoped_document_requests",
            description="Document checklists are generated from the sector playbook's declared artifacts.",
            cost_of_issuance_rationale="Reduces counsel/advisor time spent sorting irrelevant or missing diligence requests.",
        ),
        BurdenReductionMechanism(
            key="artifact_vault_reuse_and_hashing",
            description="Uploaded documents are hashed, deduplicated, and reused across readiness, modeling, and handoff outputs.",
            cost_of_issuance_rationale="Avoids repeated document collection cycles and creates an audit trail for professional review.",
        ),
        BurdenReductionMechanism(
            key="ai_extraction_with_human_review",
            description="AI proposes schema-bound facts while a reviewer accepts or rejects material outputs.",
            cost_of_issuance_rationale="Compresses manual diligence synthesis without replacing advisor or human judgment.",
        ),
        BurdenReductionMechanism(
            key="advisor_ready_handoff_pack",
            description="Reviewed facts, readiness gaps, assumptions, and disclosure outline are assembled into a reusable pack.",
            cost_of_issuance_rationale="Shortens pre-issuance coordination and gives advisors a structured starting point.",
        ),
        BurdenReductionMechanism(
            key="measurement_and_cost_learning",
            description="Task logs, client hours diaries, milestones, and closing COI line items are captured during the pilot.",
            cost_of_issuance_rationale="Creates evidence for which steps actually lower borrower effort and issuance cost in later pilots.",
        ),
    ]


def build_pilot_onboarding_workflow(
    sector_key: str,
    *,
    sensing_lead_id: str | None = None,
    source_channel: str = "direct",
) -> PilotOnboardingWorkflow:
    """Build the canonical operator pilot onboarding workflow for a sector."""

    playbook = get_sector_playbook(sector_key)
    sensing_link = (
        SensingLeadLink(lead_id=sensing_lead_id, source_channel=source_channel)
        if sensing_lead_id
        else None
    )
    workflow = PilotOnboardingWorkflow(
        workflow_id=f"bfms-pilot-onboarding-{playbook.metadata.sector}",
        display_name=f"BFMS Pilot Onboarding — {playbook.metadata.display_name}",
        playbook=playbook,
        roles=list(_ROLES),
        pre_pilot_gates=list(_PRE_PILOT_GATES),
        sensing_link=sensing_link,
        evidence_workspace_folders=_OPERATOR_WORKSPACE_FOLDERS,
        document_request_list=_document_request_list(playbook),
        stages=_stages(playbook),
        burden_reduction_mechanisms=_burden_reduction_mechanisms(),
        measurement_hooks=(
            "pilot_task_log",
            "weekly_client_hours_diary",
            "deal_milestone_timestamps",
            "frozen_coi_prediction",
            "closing_coi_line_items",
            "post_pilot_demand_signal",
        ),
    )
    return validate_pilot_onboarding_workflow(workflow)


def validate_pilot_onboarding_workflow(workflow: PilotOnboardingWorkflow) -> PilotOnboardingWorkflow:
    """Validate workflow completeness, role references, gates, and mechanisms."""

    stage_sequence = [step.stage for step in workflow.stages]
    if stage_sequence != _REQUIRED_STAGE_SEQUENCE:
        missing = [stage.value for stage in _REQUIRED_STAGE_SEQUENCE if stage not in stage_sequence]
        raise PilotOnboardingValidationError(
            f"pilot onboarding stage sequence must be {[stage.value for stage in _REQUIRED_STAGE_SEQUENCE]}; missing {missing}"
        )

    roles = {role.role for role in workflow.roles}
    missing_roles = sorted(_REQUIRED_ROLES - roles)
    if missing_roles:
        raise PilotOnboardingValidationError(f"pilot onboarding roles missing: {', '.join(missing_roles)}")

    gate_ids = {gate.gate_id for gate in workflow.pre_pilot_gates if gate.required}
    missing_gates = sorted(_REQUIRED_GATES - gate_ids)
    if missing_gates:
        raise PilotOnboardingValidationError(f"required pre-pilot gates missing: {', '.join(missing_gates)}")

    mechanism_keys = {mechanism.key for mechanism in workflow.burden_reduction_mechanisms}
    missing_mechanisms = sorted(_REQUIRED_MECHANISMS - mechanism_keys)
    if missing_mechanisms:
        raise PilotOnboardingValidationError(
            f"burden reduction mechanisms missing: {', '.join(missing_mechanisms)}"
        )

    for step in workflow.stages:
        if step.owner_role not in roles:
            raise PilotOnboardingValidationError(
                f"stage {step.stage.value} references unknown owner role: {step.owner_role}"
            )
        unknown_participants = sorted(set(step.participant_roles) - roles)
        if unknown_participants:
            raise PilotOnboardingValidationError(
                f"stage {step.stage.value} references unknown participant roles: {', '.join(unknown_participants)}"
            )

    if workflow.sensing_link and workflow.sensing_link.source_channel not in workflow.sensing_link.allowed_sources:
        raise PilotOnboardingValidationError(
            f"unknown sensing source channel: {workflow.sensing_link.source_channel}"
        )

    return workflow
