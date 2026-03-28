"""
Risk reporting foundation endpoints.
"""

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from munipal.api.dependencies import AuthenticatedUserId, DbSession, require_auth, require_roles
from munipal.config import get_settings
from munipal.core.schemas.risk_reporting import (
    RiskActionAcceptanceRequest,
    RiskActionAcceptanceResponse,
    RiskActionSyncResponse,
    RiskBenchmarkCohort,
    RiskBfmsIntegrationResponse,
    RiskDiagnosticsResponse,
    RiskExternalBriefResponse,
    RiskInternalReportResponse,
    RiskOverrideDecisionRequest,
    RiskOverrideDecisionResponse,
)
from munipal.core.schemas.revenue_visualization import (
    RevenueDiversificationVisualizationResponse,
)
from munipal.services.audit_service import AuditService
from munipal.services.authorization_service import AuthorizationService
from munipal.services.revenue_visualization_service import RevenueVisualizationService
from munipal.services.risk_reporting_service import (
    RISK_SCORING_GOVERNANCE_POLICY_VERSION,
    RISK_SCORING_PROFILE_CHECKSUM,
    RISK_SCORING_PROFILE_VERSION,
    RiskReportingService,
)

router = APIRouter(dependencies=[Depends(require_auth)])


def _ensure_risk_reporting_enabled() -> None:
    settings = get_settings()
    if not settings.risk_reporting_v2_foundation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )


def _build_cohort(
    *,
    sector: str,
    issuer_size_band: str,
    deal_type: str,
    recency_window: str,
    sample_size: int,
) -> RiskBenchmarkCohort:
    return RiskBenchmarkCohort(
        sector=sector,
        issuer_size_band=issuer_size_band,
        deal_type=deal_type,
        recency_window=recency_window,
        sample_size=sample_size,
    )


def _scoring_profile_metadata() -> dict[str, str]:
    return {
        "scoring_profile_version": RISK_SCORING_PROFILE_VERSION,
        "scoring_profile_checksum": RISK_SCORING_PROFILE_CHECKSUM,
        "governance_policy_version": RISK_SCORING_GOVERNANCE_POLICY_VERSION,
    }


def _override_governance_scope(target_ref: str) -> str:
    normalized = target_ref.strip().lower()
    if normalized.startswith("scoring_profile.") or normalized.startswith("profile."):
        return "scoring_profile"
    if normalized.startswith("guardrail."):
        return "guardrail"
    if normalized.startswith("risk."):
        return "dimension"
    return "other"


@router.get(
    "/revenue-diversification",
    response_model=RevenueDiversificationVisualizationResponse,
)
async def get_revenue_diversification_visualization(
    db: DbSession,
    user_id: AuthenticatedUserId,
    project_id: UUID,
    mode: Literal["auto", "native", "packet"] = Query("auto"),
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> RevenueDiversificationVisualizationResponse:
    """
    Typed visualization payload for the revenue diversification comparison chart.
    """
    authz = AuthorizationService(db)
    await authz.require_project_read(user_id, project_id)

    service = RevenueVisualizationService(db)
    visualization = await service.build_visualization(project_id, mode=mode)

    AuditService.emit_event(
        actor_id=user_id,
        action="generate_revenue_diversification_visualization",
        target_type="project",
        target_id=str(project_id),
        project_id=str(project_id),
        metadata={
            "mode": mode,
            "contract_version": visualization.contract_version,
            "scenario_count": len(visualization.revenue_scenarios),
            "stream_definition_count": len(visualization.stream_definitions),
            "has_data_quality_notes": bool(visualization.data_quality_notes),
        },
    )
    return visualization


@router.get("/diagnostics", response_model=RiskDiagnosticsResponse)
async def get_risk_diagnostics(
    db: DbSession,
    user_id: AuthenticatedUserId,
    project_id: UUID,
    sector: str = Query(..., min_length=1),
    issuer_size_band: str = Query(..., min_length=1),
    deal_type: str = Query(..., min_length=1),
    recency_window: str = Query(..., min_length=1),
    sample_size: int = Query(..., ge=1),
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> RiskDiagnosticsResponse:
    """
    Internal-only diagnostics endpoint for risk foundation outputs.
    """
    _ensure_risk_reporting_enabled()

    authz = AuthorizationService(db)
    await authz.require_project_read(user_id, project_id)

    cohort = _build_cohort(
        sector=sector,
        issuer_size_band=issuer_size_band,
        deal_type=deal_type,
        recency_window=recency_window,
        sample_size=sample_size,
    )
    service = RiskReportingService(db)
    diagnostics = await service.build_diagnostics(project_id, cohort)

    AuditService.emit_event(
        actor_id=user_id,
        action="generate_risk_diagnostics",
        target_type="project",
        target_id=str(project_id),
        project_id=str(project_id),
        metadata={
            "cohort": cohort.model_dump(),
            "dimension_count": len(diagnostics.dimensions),
            "action_count": len(diagnostics.actions),
        }
        | _scoring_profile_metadata(),
    )
    return diagnostics


@router.get("/internal-report", response_model=RiskInternalReportResponse)
async def get_risk_internal_report(
    db: DbSession,
    user_id: AuthenticatedUserId,
    project_id: UUID,
    sector: str = Query(..., min_length=1),
    issuer_size_band: str = Query(..., min_length=1),
    deal_type: str = Query(..., min_length=1),
    recency_window: str = Query(..., min_length=1),
    sample_size: int = Query(..., ge=1),
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> RiskInternalReportResponse:
    """
    Internal risk report contract for readiness and advisory service consumption.
    """
    _ensure_risk_reporting_enabled()

    authz = AuthorizationService(db)
    await authz.require_project_read(user_id, project_id)

    cohort = _build_cohort(
        sector=sector,
        issuer_size_band=issuer_size_band,
        deal_type=deal_type,
        recency_window=recency_window,
        sample_size=sample_size,
    )
    service = RiskReportingService(db)
    report = await service.build_internal_report(project_id, cohort)

    AuditService.emit_event(
        actor_id=user_id,
        action="generate_risk_internal_report",
        target_type="project",
        target_id=str(project_id),
        project_id=str(project_id),
        metadata={
            "cohort": cohort.model_dump(),
            "contract_version": report.contract_version,
        }
        | _scoring_profile_metadata(),
    )
    return report


@router.get("/external-brief", response_model=RiskExternalBriefResponse)
async def get_risk_external_brief(
    db: DbSession,
    user_id: AuthenticatedUserId,
    project_id: UUID,
    sector: str = Query(..., min_length=1),
    issuer_size_band: str = Query(..., min_length=1),
    deal_type: str = Query(..., min_length=1),
    recency_window: str = Query(..., min_length=1),
    sample_size: int = Query(..., ge=1),
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> RiskExternalBriefResponse:
    """
    External-safe advisory risk brief contract.
    """
    _ensure_risk_reporting_enabled()

    authz = AuthorizationService(db)
    await authz.require_project_read(user_id, project_id)

    cohort = _build_cohort(
        sector=sector,
        issuer_size_band=issuer_size_band,
        deal_type=deal_type,
        recency_window=recency_window,
        sample_size=sample_size,
    )
    service = RiskReportingService(db)
    brief = await service.build_external_brief(project_id, cohort)

    AuditService.emit_event(
        actor_id=user_id,
        action="generate_risk_external_brief",
        target_type="project",
        target_id=str(project_id),
        project_id=str(project_id),
        metadata={
            "cohort": cohort.model_dump(),
            "contract_version": brief.contract_version,
            "material_statement_count": len(brief.material_risk_statements),
        }
        | _scoring_profile_metadata(),
    )
    return brief


@router.get("/bfms-integration", response_model=RiskBfmsIntegrationResponse)
async def get_risk_bfms_integration_payload(
    db: DbSession,
    user_id: AuthenticatedUserId,
    project_id: UUID,
    sector: str = Query(..., min_length=1),
    issuer_size_band: str = Query(..., min_length=1),
    deal_type: str = Query(..., min_length=1),
    recency_window: str = Query(..., min_length=1),
    sample_size: int = Query(..., ge=1),
    _: str = Depends(require_roles("admin", "analyst", "viewer")),
) -> RiskBfmsIntegrationResponse:
    """
    Versioned BFMS integration payload with graceful fallback semantics.
    """
    _ensure_risk_reporting_enabled()

    authz = AuthorizationService(db)
    await authz.require_project_read(user_id, project_id)

    cohort = _build_cohort(
        sector=sector,
        issuer_size_band=issuer_size_band,
        deal_type=deal_type,
        recency_window=recency_window,
        sample_size=sample_size,
    )
    service = RiskReportingService(db)
    payload = await service.build_bfms_integration_payload(project_id, cohort)

    AuditService.emit_event(
        actor_id=user_id,
        action="generate_risk_bfms_integration",
        target_type="project",
        target_id=str(project_id),
        project_id=str(project_id),
        metadata={
            "cohort": cohort.model_dump(),
            "contract_version": payload.contract_version,
            "integration_mode": str(payload.integration_mode),
            "fallback_reason_count": len(payload.fallback_reasons),
            "directional_guidance_only": payload.directional_guidance_only,
        }
        | _scoring_profile_metadata(),
    )
    return payload


@router.post("/sync-information-requests", response_model=RiskActionSyncResponse)
async def sync_risk_information_requests(
    db: DbSession,
    user_id: AuthenticatedUserId,
    project_id: UUID,
    sector: str = Query(..., min_length=1),
    issuer_size_band: str = Query(..., min_length=1),
    deal_type: str = Query(..., min_length=1),
    recency_window: str = Query(..., min_length=1),
    sample_size: int = Query(..., ge=1),
    _: str = Depends(require_roles("admin", "analyst")),
) -> RiskActionSyncResponse:
    """
    Auto-create/refresh risk-related information requests from synthesized actions.
    """
    _ensure_risk_reporting_enabled()

    authz = AuthorizationService(db)
    await authz.require_project_write(user_id, project_id)

    cohort = _build_cohort(
        sector=sector,
        issuer_size_band=issuer_size_band,
        deal_type=deal_type,
        recency_window=recency_window,
        sample_size=sample_size,
    )
    service = RiskReportingService(db)
    diagnostics = await service.build_diagnostics(project_id, cohort)
    sync_response = await service.sync_actions_to_information_requests(
        project_id=project_id,
        actions=diagnostics.actions,
    )

    AuditService.emit_event(
        actor_id=user_id,
        action="sync_risk_information_requests",
        target_type="project",
        target_id=str(project_id),
        project_id=str(project_id),
        metadata={
            "created_count": sync_response.created_count,
            "updated_count": sync_response.updated_count,
            "skipped_count": sync_response.skipped_count,
        }
        | _scoring_profile_metadata(),
    )
    return sync_response


@router.post("/overrides", response_model=RiskOverrideDecisionResponse)
async def record_risk_override_decision(
    db: DbSession,
    user_id: AuthenticatedUserId,
    decision: RiskOverrideDecisionRequest,
    _: str = Depends(require_roles("admin", "analyst")),
) -> RiskOverrideDecisionResponse:
    """
    Record governed override decisions for risk scores/guardrail outcomes.
    """
    _ensure_risk_reporting_enabled()

    authz = AuthorizationService(db)
    await authz.require_project_write(user_id, decision.project_id)

    decision_id = uuid4()
    recorded_at = datetime.now(UTC)
    governance_scope = _override_governance_scope(decision.target_ref)
    AuditService.emit_event(
        actor_id=user_id,
        action="risk_override_decision",
        target_type="risk_override",
        target_id=str(decision_id),
        project_id=str(decision.project_id),
        metadata={
            "target_ref": decision.target_ref,
            "reason": decision.reason,
            "previous_value": decision.previous_value,
            "override_value": decision.override_value,
            "governance_scope": governance_scope,
            "notes": decision.notes,
            "recorded_at": recorded_at.isoformat(),
        }
        | _scoring_profile_metadata(),
    )

    return RiskOverrideDecisionResponse(
        decision_id=decision_id,
        project_id=decision.project_id,
        actor_id=user_id,
        target_ref=decision.target_ref,
        reason=decision.reason,
        recorded_at=recorded_at,
    )


@router.post("/actions/{action_id}/accept", response_model=RiskActionAcceptanceResponse)
async def accept_risk_action(
    action_id: str,
    db: DbSession,
    user_id: AuthenticatedUserId,
    acceptance: RiskActionAcceptanceRequest,
    _: str = Depends(require_roles("admin", "analyst")),
) -> RiskActionAcceptanceResponse:
    """
    Record acceptance of a synthesized risk action for execution.
    """
    _ensure_risk_reporting_enabled()

    authz = AuthorizationService(db)
    await authz.require_project_write(user_id, acceptance.project_id)

    accepted_at = datetime.now(UTC)
    AuditService.emit_event(
        actor_id=user_id,
        action="risk_action_accepted",
        target_type="risk_action",
        target_id=action_id,
        project_id=str(acceptance.project_id),
        metadata={
            "reason": acceptance.reason,
            "notes": acceptance.notes,
            "accepted_at": accepted_at.isoformat(),
        }
        | _scoring_profile_metadata(),
    )

    return RiskActionAcceptanceResponse(
        action_id=action_id,
        project_id=acceptance.project_id,
        actor_id=user_id,
        reason=acceptance.reason,
        accepted_at=accepted_at,
    )
