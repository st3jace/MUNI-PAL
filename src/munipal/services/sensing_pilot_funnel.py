"""Sensing-to-pilot funnel contract for BFMS pilot onboarding.

This module records the deployment boundary and handoff expectations that
connect the public sensing/lead-capture surface to qualified BFMS pilots.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SensingDeploymentScope:
    """Public sensing app route scope and BFMS routes excluded from it."""

    allowed_public_routes: tuple[str, ...]
    protected_sensing_admin_routes: tuple[str, ...]
    blocked_bfms_route_prefixes: tuple[str, ...]
    allowed_non_sensing_routes: tuple[str, ...] = ("/", "/health", "/health/ready")


@dataclass(frozen=True)
class LeadHandoffStage:
    """One stage in the lead-to-pilot handoff."""

    stage_key: str
    owner: str
    source_artifacts: tuple[str, ...]
    exit_criteria: tuple[str, ...]


@dataclass(frozen=True)
class LeadToPilotHandoff:
    """Expected progression from public lead to BFMS pilot project."""

    stages: tuple[LeadHandoffStage, ...]
    required_conversion_stage: str
    post_conversion_stage: str
    project_creation_endpoint: str
    pilot_qualification_requirements: tuple[str, ...]
    project_creation_requirements: tuple[str, ...]


@dataclass(frozen=True)
class PrivacyComplianceExpectations:
    """Privacy/compliance posture for sensing lead capture."""

    public_surface_posture: str
    required_controls: tuple[str, ...]
    prohibited_uses: tuple[str, ...]


@dataclass(frozen=True)
class SensingPilotFunnelContract:
    """Complete ELA-38 sensing/lead-capture to pilot funnel contract."""

    deployment_scope: SensingDeploymentScope
    lead_handoff: LeadToPilotHandoff
    privacy_compliance: PrivacyComplianceExpectations
    follow_up_gap_keys: tuple[str, ...]


SENSING_PILOT_FUNNEL_CONTRACT = SensingPilotFunnelContract(
    deployment_scope=SensingDeploymentScope(
        allowed_public_routes=(
            "/api/v1/sensing/sectors",
            "/api/v1/sensing/market-intelligence",
            "/api/v1/sensing/benchmark",
            "/api/v1/sensing/credit-spreads",
            "/api/v1/sensing/questionnaire",
            "/api/v1/sensing/readiness",
            "/api/v1/sensing/coi-benchmarks",
            "/api/v1/sensing/coi-deal-benchmarks",
            "/api/v1/sensing/lead",
            "/api/v1/sensing/event",
            "/api/v1/sensing/unsubscribe",
        ),
        protected_sensing_admin_routes=(
            "/api/v1/sensing/leads",
            "/api/v1/sensing/leads/{lead_id}",
            "/api/v1/sensing/leads/{lead_id}/funnel",
            "/api/v1/sensing/leads/{lead_id}/convert-to-project",
        ),
        blocked_bfms_route_prefixes=(
            "/api/v1/auth",
            "/api/v1/playbooks",
            "/api/v1/projects",
            "/api/v1/artifacts",
            "/api/v1/extraction",
            "/api/v1/facts",
            "/api/v1/checklist",
            "/api/v1/readiness",
            "/api/v1/deliverables",
            "/api/v1/disclosure",
            "/api/v1/information-requests",
            "/api/v1/advisory-packages",
            "/api/v1/risk",
            "/api/v1/deal-documents",
            "/api/v1/templates",
            "/api/v1/stripe",
        ),
    ),
    lead_handoff=LeadToPilotHandoff(
        stages=(
            LeadHandoffStage(
                stage_key="lead_capture",
                owner="public_sensing_surface",
                source_artifacts=("lead form", "session events", "market/readiness/benchmark snapshots"),
                exit_criteria=("lead captured", "session events linked", "report_requested stage recorded"),
            ),
            LeadHandoffStage(
                stage_key="pilot_qualification",
                owner="muni_pal_operator",
                source_artifacts=("lead detail", "readiness snapshot", "baseline follow-up", "sector fit review"),
                exit_criteria=("qualified stage assigned", "registered MA coverage confirmed or stop noted", "sector playbook selected"),
            ),
            LeadHandoffStage(
                stage_key="bfms_project_creation",
                owner="authenticated_bfms_user",
                source_artifacts=("qualified lead", "owner_id", "tenant_id", "sector playbook"),
                exit_criteria=("BFMS project created", "lead moved to engaged", "conversion event recorded"),
            ),
            LeadHandoffStage(
                stage_key="pilot_onboarding",
                owner="pilot_onboarding_workflow",
                source_artifacts=("BFMS project", "sector playbook", "lead source channel"),
                exit_criteria=("pre-pilot gates checked", "workspace created", "document requests scoped"),
            ),
        ),
        required_conversion_stage="qualified",
        post_conversion_stage="engaged",
        project_creation_endpoint="/api/v1/sensing/leads/{lead_id}/convert-to-project",
        pilot_qualification_requirements=(
            "Operator/entity fit reviewed against the sector pilot strategy.",
            "Registered MA coverage is confirmed before live pilot engagement or the lead is held.",
            "Healthcare, Housing, or UCS/WTE sector playbook is selected before BFMS setup.",
            "Readiness snapshot and lead source are preserved as pilot context.",
        ),
        project_creation_requirements=(
            "Conversion requires authenticated BFMS/admin access, not public sensing access.",
            "Project creation carries forward issuer name, estimated bond amount, state, and sector playbook.",
            "Conversion records a durable event linking the lead to the created project.",
        ),
    ),
    privacy_compliance=PrivacyComplianceExpectations(
        public_surface_posture="lead-generation-only",
        required_controls=(
            "Consent language must state why contact details and report snapshots are collected.",
            "PII is minimized to contact, organization, sector, estimated deal context, and selected report snapshots.",
            "Protected sensing admin endpoints require auth and must not be exposed as public lead tools.",
            "Unsubscribe support is required for email drip follow-up.",
            "Retention/export/delete policy must be defined before production lead-scale rollout.",
            "No legal advice, municipal advisory advice, deal approval, pricing recommendation, or issuance instruction may be implied by sensing outputs.",
        ),
        prohibited_uses=(
            "Do not auto-create BFMS projects from public lead capture without qualification.",
            "Do not treat readiness scores as approval or municipal advisory advice.",
            "Do not expose BFMS project, artifact, extraction, fact review, DMS/VDR, or Stripe routes from the public sensing app.",
        ),
    ),
    follow_up_gap_keys=(
        "enforce-qualified-stage-before-project-conversion",
        "codify-lead-consent-retention-delete-export-policy",
        "gate-sensing-admin-routes-outside-public-deployment-if-needed",
    ),
)


def standalone_sensing_app_route_violations(app: Any) -> list[str]:
    """Return routes that violate the standalone public sensing app boundary."""
    scope = SENSING_PILOT_FUNNEL_CONTRACT.deployment_scope
    allowed_exact = set(scope.allowed_non_sensing_routes)
    allowed_exact.update(scope.allowed_public_routes)
    allowed_exact.update(scope.protected_sensing_admin_routes)

    violations: list[str] = []
    for route in getattr(app, "routes", []):
        path = getattr(route, "path", "")
        if not path or path in {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}:
            continue
        if any(path.startswith(prefix) for prefix in scope.blocked_bfms_route_prefixes):
            violations.append(path)
            continue
        if path.startswith("/api/v1/sensing") and path not in allowed_exact:
            violations.append(path)
            continue
        if not path.startswith("/api/v1/sensing") and path not in allowed_exact:
            violations.append(path)
    return sorted(set(violations))
