"""
Risk reporting service (Phase 5).

Implements:
- canonical risk dimension assembler
- cohort-aware benchmark metadata contract
- confidence and reliability scoring
- deterministic posture scoring versus benchmark corpus
"""

import hashlib
import re
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.models.fact import ExtractedFact
from munipal.core.models.information_request import InformationRequest
from munipal.core.schemas.base import ReviewStatus
from munipal.core.schemas.information_request import EvidenceState, RequestPriority, RequestStatus
from munipal.core.schemas.risk_reporting import (
    RiskActionItem,
    RiskActionPriority,
    RiskActionRequestSyncItem,
    RiskActionSyncResponse,
    RiskAdvisoryInput,
    RiskAdvisoryStatement,
    RiskBenchmarkCohort,
    RiskBenchmarkPosition,
    RiskBenchmarkStats,
    RiskBfmsIntegrationResponse,
    RiskConfidence,
    RiskDiagnosticsResponse,
    RiskDimensionDiagnostics,
    RiskExternalActionBrief,
    RiskExternalBriefResponse,
    RiskExternalComplianceCheck,
    RiskGapSeverity,
    RiskGuardrailCheck,
    RiskGuardrailStatus,
    RiskGuardrailThreshold,
    RiskIntegrationMode,
    RiskInternalExecutiveSummary,
    RiskInternalReportResponse,
    RiskOverallPosture,
    RiskProjectStatus,
    RiskReadinessInput,
    RiskReliabilityBand,
)
from munipal.config import Settings, get_settings

RISK_DIMENSIONS: Mapping[str, tuple[str, str]] = {
    "risk.technology": ("risk.technology.description", "risk.technology.mitigants"),
    "risk.construction": ("risk.construction.description", "risk.construction.mitigants"),
    "risk.market": ("risk.market.description", "risk.market.mitigants"),
    "risk.regulatory": ("risk.regulatory.description", "risk.regulatory.mitigants"),
    "risk.feedstock": ("risk.feedstock.description", "risk.feedstock.mitigants"),
}


BENCHMARK_BASELINES: Mapping[str, Mapping[str, object]] = {
    "risk.technology": {
        "mitigation_rate": 0.72,
        "severity_distribution": {"high": 0.24, "medium": 0.50, "low": 0.26},
    },
    "risk.construction": {
        "mitigation_rate": 0.69,
        "severity_distribution": {"high": 0.28, "medium": 0.46, "low": 0.26},
    },
    "risk.market": {
        "mitigation_rate": 0.65,
        "severity_distribution": {"high": 0.31, "medium": 0.44, "low": 0.25},
    },
    "risk.regulatory": {
        "mitigation_rate": 0.67,
        "severity_distribution": {"high": 0.27, "medium": 0.47, "low": 0.26},
    },
    "risk.feedstock": {
        "mitigation_rate": 0.64,
        "severity_distribution": {"high": 0.30, "medium": 0.45, "low": 0.25},
    },
}

GUARDRAIL_FACT_PATHS: tuple[str, ...] = (
    "finmodel.inputs.dscr.minimum",
    "finmodel.outputs.dscrbase",
    "finmodel.outputs.dscrstress",
    "capital.equipment-cost",
    "capital.project-cost",
)

ACTION_TARGET_HINT_BY_PRIORITY: Mapping[RiskActionPriority, str] = {
    RiskActionPriority.HIGH: "7 days",
    RiskActionPriority.MEDIUM: "14 days",
    RiskActionPriority.LOW: "30 days",
}

ADVANCED_ANALYTICS_METRICS: tuple[str, ...] = (
    "spectral_omega",
    "wavelet_omega",
    "dynamic_omega",
)

ADVANCED_ANALYTICS_PATHS: Mapping[str, Mapping[str, str]] = {
    dimension_id: {
        metric: f"analytics.extended_risk.{dimension_id.split('.')[1]}.{metric}"
        for metric in ADVANCED_ANALYTICS_METRICS
    }
    for dimension_id in RISK_DIMENSIONS
}


class RiskReportingService:
    """Service for internal risk diagnostics payload generation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_diagnostics(
        self,
        project_id: UUID,
        cohort: RiskBenchmarkCohort,
    ) -> RiskDiagnosticsResponse:
        """
        Build deterministic risk diagnostics for a project.
        """
        settings = get_settings()
        all_paths = [
            *[path for pair in RISK_DIMENSIONS.values() for path in pair],
            *GUARDRAIL_FACT_PATHS,
        ]
        if settings.risk_reporting_v2_advanced_analytics:
            all_paths.extend(
                path
                for metric_paths in ADVANCED_ANALYTICS_PATHS.values()
                for path in metric_paths.values()
            )
        all_paths = list(dict.fromkeys(all_paths))

        approved_facts = await self._list_facts(
            project_id=project_id,
            schema_paths=all_paths,
            include_rejected=False,
            approved_only=True,
        )
        non_rejected_facts = await self._list_facts(
            project_id=project_id,
            schema_paths=all_paths,
            include_rejected=False,
            approved_only=False,
        )

        approved_by_path = self._group_by_path(approved_facts)
        non_rejected_by_path = self._group_by_path(non_rejected_facts)

        dimensions: list[RiskDimensionDiagnostics] = []
        for dimension_id, (exposure_path, mitigant_path) in RISK_DIMENSIONS.items():
            exposure_facts = approved_by_path.get(exposure_path, [])
            mitigant_facts = approved_by_path.get(mitigant_path, [])

            evidence_count = len(exposure_facts) + len(mitigant_facts)
            conflict_count = (
                self._count_conflicts(non_rejected_by_path.get(exposure_path, []))
                + self._count_conflicts(non_rejected_by_path.get(mitigant_path, []))
            )

            project_status = self._project_status(
                has_exposure=bool(exposure_facts),
                has_mitigant=bool(mitigant_facts),
            )
            gap_severity = self._gap_severity(project_status)

            benchmark_stats = self._build_benchmark_stats(
                dimension_id=dimension_id,
                cohort=cohort,
                gap_severity=gap_severity,
            )
            confidence = self._compute_confidence(
                sample_size=cohort.sample_size,
                evidence_count=evidence_count,
                conflict_count=conflict_count,
            )
            benchmark_position, posture_score, posture_explainer = self._score_dimension_posture(
                gap_severity=gap_severity,
                benchmark_stats=benchmark_stats,
                confidence=confidence,
                evidence_count=evidence_count,
                conflict_count=conflict_count,
            )
            (
                benchmark_position,
                posture_score,
                posture_explainer,
                advanced_metrics,
                advanced_analytics_applied,
                advanced_analytics_note,
            ) = self._apply_advanced_analytics(
                settings=settings,
                dimension_id=dimension_id,
                approved_by_path=approved_by_path,
                confidence=confidence,
                benchmark_stats=benchmark_stats,
                benchmark_position=benchmark_position,
                posture_score=posture_score,
                posture_explainer=posture_explainer,
            )

            dimensions.append(
                RiskDimensionDiagnostics(
                    dimension_id=dimension_id,
                    project_status=project_status,
                    gap_severity=gap_severity,
                    benchmark_position=benchmark_position,
                    posture_score=posture_score,
                    posture_explainer=posture_explainer,
                    benchmark_stats=benchmark_stats,
                    confidence=confidence,
                    evidence_count=evidence_count,
                    conflict_count=conflict_count,
                    advanced_metrics=advanced_metrics,
                    advanced_analytics_applied=advanced_analytics_applied,
                    advanced_analytics_note=advanced_analytics_note,
                )
            )

        dimensions.sort(key=lambda item: item.dimension_id)
        overall_posture = self._score_overall_posture(dimensions)
        guardrails = self._build_guardrails(approved_by_path)
        actions = self._synthesize_actions(dimensions, guardrails)
        return RiskDiagnosticsResponse(
            project_id=project_id,
            cohort=cohort,
            dimensions=dimensions,
            overall_posture=overall_posture,
            guardrails=guardrails,
            actions=actions,
        )

    async def build_internal_report(
        self,
        project_id: UUID,
        cohort: RiskBenchmarkCohort,
    ) -> RiskInternalReportResponse:
        """
        Build versioned internal risk report contract (JSON + Markdown).
        """
        diagnostics = await self.build_diagnostics(project_id=project_id, cohort=cohort)
        executive_summary = self._build_internal_executive_summary(diagnostics)
        readiness_input = self._build_readiness_input(diagnostics)
        advisory_input = self._build_advisory_input(diagnostics)
        markdown_report = self._render_internal_markdown(
            diagnostics=diagnostics,
            executive_summary=executive_summary,
            readiness_input=readiness_input,
            advisory_input=advisory_input,
        )

        return RiskInternalReportResponse(
            generated_at=datetime.now(UTC),
            project_id=project_id,
            cohort=cohort,
            executive_summary=executive_summary,
            diagnostics=diagnostics,
            readiness_input=readiness_input,
            advisory_input=advisory_input,
            markdown_report=markdown_report,
        )

    async def build_external_brief(
        self,
        project_id: UUID,
        cohort: RiskBenchmarkCohort,
    ) -> RiskExternalBriefResponse:
        """
        Build disclosure-safe external risk brief contract.

        Internal diagnostics fields (conflicts, uncertainty notes, queue metadata)
        are intentionally excluded from this contract.
        """
        diagnostics = await self.build_diagnostics(project_id=project_id, cohort=cohort)
        advisory_input = self._build_advisory_input(diagnostics)
        overall_position = self._normalize_benchmark_position(
            diagnostics.overall_posture.benchmark_position
        )
        external_actions = [
            RiskExternalActionBrief(
                action_id=action.action_id,
                priority=action.priority,
                owner=action.owner,
                title=action.title,
                target_date_hint=action.target_date_hint,
                expected_impact=action.expected_impact,
            )
            for action in diagnostics.actions[:5]
        ]
        key_assumptions = self._build_external_assumptions(diagnostics)
        compliance_checks = self._build_external_compliance_checks()
        markdown_brief = self._render_external_markdown(
            diagnostics=diagnostics,
            advisory_input=advisory_input,
            key_assumptions=key_assumptions,
            next_steps=external_actions,
            compliance_checks=compliance_checks,
        )

        return RiskExternalBriefResponse(
            generated_at=datetime.now(UTC),
            project_id=project_id,
            cohort=cohort,
            overall_benchmark_position=overall_position,
            overall_posture_score=diagnostics.overall_posture.posture_score,
            material_risk_statements=advisory_input.material_risk_statements,
            mitigant_summary=advisory_input.mitigant_highlights,
            key_assumptions=key_assumptions,
            advisory_next_steps=external_actions,
            compliance_checks=compliance_checks,
            markdown_brief=markdown_brief,
        )

    async def build_bfms_integration_payload(
        self,
        project_id: UUID,
        cohort: RiskBenchmarkCohort,
    ) -> RiskBfmsIntegrationResponse:
        """
        Build a stable BFMS integration payload with graceful fallback semantics.

        Fallback mode is engaged when risk outputs are directional-only due to
        low reliability bands in one or more dimensions.
        """
        diagnostics = await self.build_diagnostics(project_id=project_id, cohort=cohort)
        executive_summary = self._build_internal_executive_summary(diagnostics)
        readiness_input = self._build_readiness_input(diagnostics)
        advisory_input = self._build_advisory_input(diagnostics)
        key_assumptions = self._build_external_assumptions(diagnostics)
        compliance_checks = self._build_external_compliance_checks()
        advisory_next_steps = [
            RiskExternalActionBrief(
                action_id=action.action_id,
                priority=action.priority,
                owner=action.owner,
                title=action.title,
                target_date_hint=action.target_date_hint,
                expected_impact=action.expected_impact,
            )
            for action in diagnostics.actions[:5]
        ]

        fallback_reasons: list[str] = []
        if readiness_input.directional_guidance_only:
            fallback_reasons.append(
                "One or more risk dimensions are low reliability; use directional guidance."
            )

        integration_mode = (
            RiskIntegrationMode.FALLBACK if fallback_reasons else RiskIntegrationMode.FULL
        )

        return RiskBfmsIntegrationResponse(
            generated_at=datetime.now(UTC),
            project_id=project_id,
            cohort=cohort,
            integration_mode=integration_mode,
            fallback_reasons=fallback_reasons,
            overall_benchmark_position=self._normalize_benchmark_position(
                diagnostics.overall_posture.benchmark_position
            ),
            overall_posture_score=diagnostics.overall_posture.posture_score,
            reliability_low_dimensions=executive_summary.reliability_low_dimensions,
            directional_guidance_only=readiness_input.directional_guidance_only,
            critical_risk_flags=readiness_input.critical_risk_flags,
            material_risk_statements=advisory_input.material_risk_statements,
            advisory_next_steps=advisory_next_steps,
            key_assumptions=key_assumptions,
            compliance_checks=compliance_checks,
        )

    async def sync_actions_to_information_requests(
        self,
        project_id: UUID,
        actions: list[RiskActionItem],
    ) -> RiskActionSyncResponse:
        """
        Auto-create or refresh risk-related information requests from actions.
        """
        if not actions:
            return RiskActionSyncResponse(
                project_id=project_id,
                synced_at=datetime.now(UTC),
                total_actions=0,
                created_count=0,
                updated_count=0,
                skipped_count=0,
                synced_requests=[],
            )

        gap_ids = [self._risk_gap_id(action.action_id) for action in actions]
        result = await self.db.execute(
            select(InformationRequest).where(
                and_(
                    InformationRequest.project_id == str(project_id),
                    InformationRequest.gap_id.in_(gap_ids),
                )
            )
        )
        existing_by_gap = {
            request.gap_id: request
            for request in result.scalars().all()
            if request.gap_id
        }

        created_count = 0
        updated_count = 0
        skipped_count = 0
        synced_items: list[RiskActionRequestSyncItem] = []

        for action in actions:
            gap_id = self._risk_gap_id(action.action_id)
            payload = self._build_information_request_payload(action)
            existing = existing_by_gap.get(gap_id)

            if existing is not None and existing.status == RequestStatus.RESOLVED.value:
                skipped_count += 1
                synced_items.append(
                    RiskActionRequestSyncItem(
                        action_id=action.action_id,
                        operation="skipped_resolved",
                        request_id=UUID(existing.id),
                        request_code=existing.request_code,
                        request_status=existing.status,
                    )
                )
                continue

            if existing is None:
                request = InformationRequest(
                    id=str(uuid4()),
                    project_id=str(project_id),
                    request_code=self._risk_request_code(project_id, action.action_id),
                    title=payload["title"],
                    missing_fact_paths=payload["missing_fact_paths"],
                    current_evidence_state=payload["current_evidence_state"],
                    gap_id=gap_id,
                    why_it_matters=payload["why_it_matters"],
                    who_needs_it=payload["who_needs_it"],
                    when_needed=payload["when_needed"],
                    consequences=payload["consequences"],
                    related_requirements=payload["related_requirements"],
                    regulatory_reference=payload["regulatory_reference"],
                    affected_checklist_items=payload["affected_checklist_items"],
                    affected_dimensions=payload["affected_dimensions"],
                    guidance_overview=payload["guidance_overview"],
                    specific_questions=payload["specific_questions"],
                    data_points_needed=payload["data_points_needed"],
                    suggested_approach=payload["suggested_approach"],
                    common_pitfalls=payload["common_pitfalls"],
                    time_estimate=payload["time_estimate"],
                    examples=payload["examples"],
                    acceptable_sources=payload["acceptable_sources"],
                    minimum_confidence=payload["minimum_confidence"],
                    expected_format=payload["expected_format"],
                    priority=payload["priority"],
                    suggested_owner=payload["suggested_owner"],
                    target_date=payload["target_date"],
                    status=RequestStatus.OPEN.value,
                )
                self.db.add(request)
                existing_by_gap[gap_id] = request
                created_count += 1
                synced_items.append(
                    RiskActionRequestSyncItem(
                        action_id=action.action_id,
                        operation="created",
                        request_id=UUID(request.id),
                        request_code=request.request_code,
                        request_status=request.status,
                    )
                )
                continue

            self._apply_information_request_payload(existing, payload)
            updated_count += 1
            synced_items.append(
                RiskActionRequestSyncItem(
                    action_id=action.action_id,
                    operation="updated",
                    request_id=UUID(existing.id),
                    request_code=existing.request_code,
                    request_status=existing.status,
                )
            )

        await self.db.flush()
        return RiskActionSyncResponse(
            project_id=project_id,
            synced_at=datetime.now(UTC),
            total_actions=len(actions),
            created_count=created_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            synced_requests=synced_items,
        )

    async def _list_facts(
        self,
        project_id: UUID,
        schema_paths: list[str],
        include_rejected: bool,
        approved_only: bool,
    ) -> list[ExtractedFact]:
        query = select(ExtractedFact).where(
            and_(
                ExtractedFact.project_id == str(project_id),
                ExtractedFact.schema_path.in_(schema_paths),
                ExtractedFact.lifecycle_state != "archived",
            )
        )

        if approved_only:
            query = query.where(ExtractedFact.review_status == ReviewStatus.APPROVED.value)
        elif not include_rejected:
            query = query.where(ExtractedFact.review_status != ReviewStatus.REJECTED.value)

        result = await self.db.execute(
            query.order_by(ExtractedFact.schema_path.asc(), ExtractedFact.confidence_score.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    def _group_by_path(facts: list[ExtractedFact]) -> dict[str, list[ExtractedFact]]:
        grouped: dict[str, list[ExtractedFact]] = {}
        for fact in facts:
            grouped.setdefault(fact.schema_path, []).append(fact)
        return grouped

    @staticmethod
    def _count_conflicts(facts: list[ExtractedFact]) -> int:
        if len(facts) < 2:
            return 0
        unique_values = {str(f.value) for f in facts}
        return 1 if len(unique_values) > 1 else 0

    @staticmethod
    def _project_status(has_exposure: bool, has_mitigant: bool) -> RiskProjectStatus:
        if has_exposure and has_mitigant:
            return RiskProjectStatus.COMPLETE
        if has_exposure or has_mitigant:
            return RiskProjectStatus.PARTIAL
        return RiskProjectStatus.MISSING

    @staticmethod
    def _gap_severity(project_status: RiskProjectStatus) -> RiskGapSeverity:
        if project_status == RiskProjectStatus.COMPLETE:
            return RiskGapSeverity.LOW
        if project_status == RiskProjectStatus.PARTIAL:
            return RiskGapSeverity.MEDIUM
        return RiskGapSeverity.HIGH

    def _build_benchmark_stats(
        self,
        dimension_id: str,
        cohort: RiskBenchmarkCohort,
        gap_severity: RiskGapSeverity,
    ) -> RiskBenchmarkStats:
        baseline = BENCHMARK_BASELINES[dimension_id]
        base_mitigation_rate = float(baseline["mitigation_rate"])

        if gap_severity == RiskGapSeverity.HIGH:
            mitigation_rate = base_mitigation_rate - 0.12
        elif gap_severity == RiskGapSeverity.MEDIUM:
            mitigation_rate = base_mitigation_rate - 0.05
        else:
            mitigation_rate = base_mitigation_rate

        mitigation_rate = max(0.0, min(1.0, round(mitigation_rate, 3)))
        n_issuances = cohort.sample_size
        n_disclosures = max(int(cohort.sample_size * 2), cohort.sample_size)

        return RiskBenchmarkStats(
            n_issuances=n_issuances,
            n_disclosures=n_disclosures,
            mitigation_rate=mitigation_rate,
            severity_distribution=dict(baseline["severity_distribution"]),
        )

    def _compute_confidence(
        self,
        sample_size: int,
        evidence_count: int,
        conflict_count: int,
    ) -> RiskConfidence:
        sample_score = self._sample_score(sample_size)
        source_quality = self._source_quality_score(evidence_count)
        source_quality_missing = source_quality is None
        if source_quality is None:
            source_quality = 0.0

        conflict_rate = 0.0 if evidence_count == 0 else min(1.0, conflict_count / evidence_count)
        base_score = round(
            (sample_score * 0.45) + (source_quality * 0.40) + ((1.0 - conflict_rate) * 0.15),
            3,
        )

        band = self._band_from_score(base_score)
        if sample_size < 20:
            band = RiskReliabilityBand.LOW
        if conflict_rate >= 0.35:
            band = self._downgrade_band(band)

        notes: list[str] = []
        if sample_size < 20:
            notes.append("Cohort sample size below reliability threshold.")
        if source_quality_missing:
            notes.append("Source quality inputs missing.")
        if conflict_rate >= 0.35:
            notes.append("High conflict rate reduced reliability.")

        uncertainty_note = " ".join(notes) if notes else None
        return RiskConfidence(
            score=base_score,
            reliability_band=band,
            uncertainty_note=uncertainty_note,
        )

    @staticmethod
    def _sample_score(sample_size: int) -> float:
        if sample_size >= 100:
            return 1.0
        if sample_size >= 50:
            return 0.8
        if sample_size >= 20:
            return 0.6
        return 0.3

    @staticmethod
    def _source_quality_score(evidence_count: int) -> float | None:
        if evidence_count <= 0:
            return None
        return min(1.0, evidence_count / 2.0)

    @staticmethod
    def _band_from_score(score: float) -> RiskReliabilityBand:
        if score >= 0.80:
            return RiskReliabilityBand.HIGH
        if score >= 0.55:
            return RiskReliabilityBand.MEDIUM
        return RiskReliabilityBand.LOW

    @staticmethod
    def _downgrade_band(band: RiskReliabilityBand) -> RiskReliabilityBand:
        if band == RiskReliabilityBand.HIGH:
            return RiskReliabilityBand.MEDIUM
        if band == RiskReliabilityBand.MEDIUM:
            return RiskReliabilityBand.LOW
        return RiskReliabilityBand.LOW

    def _score_dimension_posture(
        self,
        gap_severity: RiskGapSeverity,
        benchmark_stats: RiskBenchmarkStats,
        confidence: RiskConfidence,
        evidence_count: int,
        conflict_count: int,
    ) -> tuple[RiskBenchmarkPosition, float, str]:
        """
        Compute deterministic dimension-level posture versus corpus benchmark.

        `posture_score` is normalized to 0-1 where higher means riskier.
        """
        conflict_rate = 0.0 if evidence_count == 0 else min(1.0, conflict_count / evidence_count)
        base_risk = self._severity_risk_score(gap_severity)
        posture_score = max(0.0, min(1.0, round(base_risk + (0.10 * conflict_rate), 3)))
        cohort_risk = max(0.0, min(1.0, round(1.0 - benchmark_stats.mitigation_rate, 3)))

        delta = round(posture_score - cohort_risk, 3)
        neutral_band = self._neutral_delta_band(confidence.reliability_band)
        benchmark_position = self._position_from_delta(delta, neutral_band)
        posture_explainer = self._build_dimension_posture_explainer(
            gap_severity=gap_severity,
            posture_score=posture_score,
            cohort_risk=cohort_risk,
            confidence=confidence,
            conflict_rate=conflict_rate,
            delta=delta,
        )
        return benchmark_position, posture_score, posture_explainer

    def _apply_advanced_analytics(
        self,
        *,
        settings: Settings,
        dimension_id: str,
        approved_by_path: Mapping[str, list[ExtractedFact]],
        confidence: RiskConfidence,
        benchmark_stats: RiskBenchmarkStats,
        benchmark_position: RiskBenchmarkPosition,
        posture_score: float,
        posture_explainer: str,
    ) -> tuple[RiskBenchmarkPosition, float, str, dict[str, float], bool, str | None]:
        if not settings.risk_reporting_v2_advanced_analytics:
            return (
                benchmark_position,
                posture_score,
                posture_explainer,
                {},
                False,
                "Advanced analytics bridge disabled.",
            )

        reliability_band = self._normalize_reliability_band(confidence.reliability_band)
        required_band = RiskReliabilityBand(
            settings.risk_reporting_v2_advanced_min_reliability.lower()
        )
        if self._reliability_rank(reliability_band) < self._reliability_rank(required_band):
            return (
                benchmark_position,
                posture_score,
                posture_explainer,
                {},
                False,
                (
                    "Advanced analytics withheld: reliability "
                    f"{reliability_band.value} below required {required_band.value}."
                ),
            )

        metric_paths = ADVANCED_ANALYTICS_PATHS.get(dimension_id, {})
        advanced_metrics: dict[str, float] = {}
        for metric_name, metric_path in metric_paths.items():
            metric_value = self._numeric_fact_value(approved_by_path, metric_path)
            if metric_value is not None:
                advanced_metrics[metric_name] = round(metric_value, 4)

        if len(advanced_metrics) < 2:
            return (
                benchmark_position,
                posture_score,
                posture_explainer,
                advanced_metrics,
                False,
                "Advanced analytics withheld: insufficient approved advanced metrics.",
            )

        normalized_components = [
            max(-1.0, min(1.0, metric_value - 1.0))
            for metric_value in advanced_metrics.values()
        ]
        adjustment = round(sum(normalized_components) / len(normalized_components) * 0.08, 3)
        adjusted_posture_score = max(0.0, min(1.0, round(posture_score - adjustment, 3)))

        cohort_risk = max(0.0, min(1.0, round(1.0 - benchmark_stats.mitigation_rate, 3)))
        neutral_band = self._neutral_delta_band(reliability_band)
        adjusted_position = self._position_from_delta(
            delta=round(adjusted_posture_score - cohort_risk, 3),
            neutral_band=neutral_band,
        )
        adjusted_explainer = (
            f"{posture_explainer} Advanced analytics adjustment {adjustment:+.3f} "
            f"from {len(advanced_metrics)} metric(s)."
        )
        return (
            adjusted_position,
            adjusted_posture_score,
            adjusted_explainer,
            advanced_metrics,
            True,
            (
                f"Applied advanced analytics bridge with minimum reliability "
                f"{required_band.value}."
            ),
        )

    @staticmethod
    def _severity_risk_score(gap_severity: RiskGapSeverity) -> float:
        if gap_severity == RiskGapSeverity.HIGH:
            return 0.78
        if gap_severity == RiskGapSeverity.MEDIUM:
            return 0.52
        return 0.25

    @staticmethod
    def _neutral_delta_band(reliability_band: RiskReliabilityBand) -> float:
        if reliability_band == RiskReliabilityBand.HIGH:
            return 0.14
        if reliability_band == RiskReliabilityBand.MEDIUM:
            return 0.18
        return 0.24

    @staticmethod
    def _position_from_delta(
        delta: float,
        neutral_band: float,
    ) -> RiskBenchmarkPosition:
        if delta > neutral_band:
            return RiskBenchmarkPosition.ABOVE
        if delta < -neutral_band:
            return RiskBenchmarkPosition.BELOW
        return RiskBenchmarkPosition.AT

    def _score_overall_posture(
        self,
        dimensions: list[RiskDimensionDiagnostics],
    ) -> RiskOverallPosture:
        if not dimensions:
            return RiskOverallPosture(
                benchmark_position=RiskBenchmarkPosition.AT,
                posture_score=0.5,
                explanation="No risk dimensions available; overall posture defaults to corpus baseline.",
            )

        posture_score = round(
            sum(item.posture_score for item in dimensions) / len(dimensions),
            3,
        )
        overall_position = self._position_from_delta(delta=posture_score - 0.5, neutral_band=0.08)

        above_count = sum(
            1 for item in dimensions if item.benchmark_position == RiskBenchmarkPosition.ABOVE
        )
        at_count = sum(
            1 for item in dimensions if item.benchmark_position == RiskBenchmarkPosition.AT
        )
        below_count = sum(
            1 for item in dimensions if item.benchmark_position == RiskBenchmarkPosition.BELOW
        )
        explanation = (
            f"{above_count} dimensions above corpus, {at_count} at corpus, {below_count} below corpus; "
            f"average posture score {posture_score:.3f}."
        )

        return RiskOverallPosture(
            benchmark_position=overall_position,
            posture_score=posture_score,
            explanation=explanation,
        )

    @staticmethod
    def _build_dimension_posture_explainer(
        gap_severity: RiskGapSeverity,
        posture_score: float,
        cohort_risk: float,
        confidence: RiskConfidence,
        conflict_rate: float,
        delta: float,
    ) -> str:
        gap_severity_value = (
            gap_severity.value if isinstance(gap_severity, RiskGapSeverity) else str(gap_severity)
        )
        reliability_value = (
            confidence.reliability_band.value
            if isinstance(confidence.reliability_band, RiskReliabilityBand)
            else str(confidence.reliability_band)
        )
        parts = [
            (
                f"Gap severity '{gap_severity_value}' produced posture score {posture_score:.3f} "
                f"against cohort baseline risk {cohort_risk:.3f}"
            ),
            (
                f"(delta {delta:+.3f}, reliability {reliability_value})."
            ),
        ]
        if conflict_rate > 0:
            parts.append(f"Conflict rate contribution: {conflict_rate:.3f}.")
        return " ".join(parts)

    def _build_guardrails(
        self,
        approved_by_path: Mapping[str, list[ExtractedFact]],
    ) -> list[RiskGuardrailCheck]:
        checks = [
            self._guardrail_dscr_headroom(approved_by_path),
            self._guardrail_dscr_stress_floor(approved_by_path),
            self._guardrail_equipment_concentration(approved_by_path),
        ]
        checks.sort(key=lambda item: item.guardrail_id)
        return checks

    def _guardrail_dscr_headroom(
        self,
        approved_by_path: Mapping[str, list[ExtractedFact]],
    ) -> RiskGuardrailCheck:
        evidence_paths = [
            "finmodel.outputs.dscrbase",
            "finmodel.inputs.dscr.minimum",
        ]
        base_dscr = self._numeric_fact_value(approved_by_path, "finmodel.outputs.dscrbase")
        minimum_dscr = self._numeric_fact_value(approved_by_path, "finmodel.inputs.dscr.minimum")
        threshold = RiskGuardrailThreshold(
            target_min=0.15,
            tolerance_min=0.05,
        )

        if base_dscr is None or minimum_dscr is None:
            return RiskGuardrailCheck(
                guardrail_id="guardrail.dscr.headroom",
                metric_name="DSCR covenant headroom",
                status=RiskGuardrailStatus.INSUFFICIENT_EVIDENCE,
                violation=False,
                observed_value=None,
                unit="x",
                benchmark_percentile_band=None,
                threshold=threshold,
                evidence_paths=evidence_paths,
                rationale="Missing approved DSCR base or covenant fact; guardrail could not be evaluated.",
            )

        headroom = round(base_dscr - minimum_dscr, 3)
        status = self._status_for_minimum(
            observed_value=headroom,
            target_min=0.15,
            tolerance_min=0.05,
        )
        percentile = self._dscr_percentile_band(base_dscr)
        rationale = (
            f"Base DSCR {base_dscr:.2f}x vs covenant {minimum_dscr:.2f}x gives {headroom:.2f}x headroom."
        )
        if status == RiskGuardrailStatus.WATCH:
            rationale += " Headroom is within tolerance but below target."
        elif status == RiskGuardrailStatus.BREACH:
            rationale += " Headroom is below tolerance minimum."

        return RiskGuardrailCheck(
            guardrail_id="guardrail.dscr.headroom",
            metric_name="DSCR covenant headroom",
            status=status,
            violation=status == RiskGuardrailStatus.BREACH,
            observed_value=headroom,
            unit="x",
            benchmark_percentile_band=percentile,
            threshold=threshold,
            evidence_paths=evidence_paths,
            rationale=rationale,
        )

    def _guardrail_dscr_stress_floor(
        self,
        approved_by_path: Mapping[str, list[ExtractedFact]],
    ) -> RiskGuardrailCheck:
        evidence_paths = [
            "finmodel.outputs.dscrstress",
            "finmodel.inputs.dscr.minimum",
        ]
        stress_dscr = self._numeric_fact_value(approved_by_path, "finmodel.outputs.dscrstress")
        minimum_dscr = self._numeric_fact_value(approved_by_path, "finmodel.inputs.dscr.minimum")
        target_min = max(1.20, round((minimum_dscr or 1.30) - 0.10, 2))
        tolerance_min = round(target_min - 0.10, 2)
        threshold = RiskGuardrailThreshold(
            target_min=target_min,
            tolerance_min=tolerance_min,
        )

        if stress_dscr is None:
            return RiskGuardrailCheck(
                guardrail_id="guardrail.dscr.stress_floor",
                metric_name="Stress DSCR floor",
                status=RiskGuardrailStatus.INSUFFICIENT_EVIDENCE,
                violation=False,
                observed_value=None,
                unit="x",
                benchmark_percentile_band=None,
                threshold=threshold,
                evidence_paths=evidence_paths,
                rationale="Missing approved stress DSCR fact; stress-floor guardrail could not be evaluated.",
            )

        status = self._status_for_minimum(
            observed_value=stress_dscr,
            target_min=target_min,
            tolerance_min=tolerance_min,
        )
        percentile = self._dscr_percentile_band(stress_dscr)
        rationale = (
            f"Stress DSCR {stress_dscr:.2f}x evaluated against target floor {target_min:.2f}x "
            f"(tolerance {tolerance_min:.2f}x)."
        )
        if minimum_dscr is None:
            rationale += " Covenant DSCR not available; default floor calibration applied."
        if status == RiskGuardrailStatus.WATCH:
            rationale += " Stress coverage is within tolerance but below target."
        elif status == RiskGuardrailStatus.BREACH:
            rationale += " Stress coverage is below tolerance minimum."

        return RiskGuardrailCheck(
            guardrail_id="guardrail.dscr.stress_floor",
            metric_name="Stress DSCR floor",
            status=status,
            violation=status == RiskGuardrailStatus.BREACH,
            observed_value=round(stress_dscr, 3),
            unit="x",
            benchmark_percentile_band=percentile,
            threshold=threshold,
            evidence_paths=evidence_paths,
            rationale=rationale,
        )

    def _guardrail_equipment_concentration(
        self,
        approved_by_path: Mapping[str, list[ExtractedFact]],
    ) -> RiskGuardrailCheck:
        evidence_paths = [
            "capital.equipment-cost",
            "capital.project-cost",
        ]
        equipment_cost = self._numeric_fact_value(approved_by_path, "capital.equipment-cost")
        project_cost = self._numeric_fact_value(approved_by_path, "capital.project-cost")
        threshold = RiskGuardrailThreshold(
            target_max=0.65,
            tolerance_max=0.70,
        )

        if equipment_cost is None or project_cost is None or project_cost <= 0:
            return RiskGuardrailCheck(
                guardrail_id="guardrail.capital.equipment_concentration",
                metric_name="Equipment cost concentration",
                status=RiskGuardrailStatus.INSUFFICIENT_EVIDENCE,
                violation=False,
                observed_value=None,
                unit="ratio",
                benchmark_percentile_band=None,
                threshold=threshold,
                evidence_paths=evidence_paths,
                rationale="Missing approved capital cost facts; equipment concentration could not be evaluated.",
            )

        concentration = round(equipment_cost / project_cost, 3)
        status = self._status_for_maximum(
            observed_value=concentration,
            target_max=0.65,
            tolerance_max=0.70,
        )
        rationale = (
            f"Equipment concentration is {concentration:.1%} of total project cost "
            f"(target <= 65.0%, tolerance <= 70.0%)."
        )
        if status == RiskGuardrailStatus.WATCH:
            rationale += " Concentration is elevated but within tolerance."
        elif status == RiskGuardrailStatus.BREACH:
            rationale += " Concentration exceeds tolerance maximum."

        return RiskGuardrailCheck(
            guardrail_id="guardrail.capital.equipment_concentration",
            metric_name="Equipment cost concentration",
            status=status,
            violation=status == RiskGuardrailStatus.BREACH,
            observed_value=concentration,
            unit="ratio",
            benchmark_percentile_band=None,
            threshold=threshold,
            evidence_paths=evidence_paths,
            rationale=rationale,
        )

    @staticmethod
    def _status_for_minimum(
        observed_value: float,
        target_min: float,
        tolerance_min: float,
    ) -> RiskGuardrailStatus:
        if observed_value < tolerance_min:
            return RiskGuardrailStatus.BREACH
        if observed_value < target_min:
            return RiskGuardrailStatus.WATCH
        return RiskGuardrailStatus.PASS

    @staticmethod
    def _status_for_maximum(
        observed_value: float,
        target_max: float,
        tolerance_max: float,
    ) -> RiskGuardrailStatus:
        if observed_value > tolerance_max:
            return RiskGuardrailStatus.BREACH
        if observed_value > target_max:
            return RiskGuardrailStatus.WATCH
        return RiskGuardrailStatus.PASS

    @staticmethod
    def _dscr_percentile_band(dscr_value: float) -> str:
        if dscr_value < 1.35:
            return "p0-p25"
        if dscr_value < 1.55:
            return "p25-p50"
        if dscr_value < 1.80:
            return "p50-p75"
        return "p75-p100"

    def _numeric_fact_value(
        self,
        approved_by_path: Mapping[str, list[ExtractedFact]],
        schema_path: str,
    ) -> float | None:
        facts = approved_by_path.get(schema_path, [])
        for fact in facts:
            numeric_value = self._coerce_numeric_value(fact.value)
            if numeric_value is not None:
                return numeric_value
        return None

    def _coerce_numeric_value(self, value: object) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.strip().lower().replace(",", "")
            if cleaned.endswith("x"):
                cleaned = cleaned[:-1]
            if cleaned.endswith("%"):
                cleaned = cleaned[:-1]
            try:
                return float(cleaned)
            except ValueError:
                return None
        if isinstance(value, Mapping):
            for key in ("value", "amount", "numeric_value", "number", "raw"):
                if key in value:
                    nested_value = self._coerce_numeric_value(value[key])
                    if nested_value is not None:
                        return nested_value
            for nested in value.values():
                nested_value = self._coerce_numeric_value(nested)
                if nested_value is not None:
                    return nested_value
            return None
        if isinstance(value, list):
            for item in value:
                nested_value = self._coerce_numeric_value(item)
                if nested_value is not None:
                    return nested_value
            return None
        return None

    def _synthesize_actions(
        self,
        dimensions: list[RiskDimensionDiagnostics],
        guardrails: list[RiskGuardrailCheck],
    ) -> list[RiskActionItem]:
        """Build prioritized, deduplicated action list from risk findings."""
        action_map: dict[str, RiskActionItem] = {}

        for guardrail in guardrails:
            synthesized = self._action_from_guardrail(guardrail)
            if synthesized is None:
                continue
            self._merge_action(action_map, synthesized)

        for dimension in dimensions:
            synthesized = self._action_from_dimension(dimension)
            if synthesized is None:
                continue
            self._merge_action(action_map, synthesized)

        actions = list(action_map.values())
        actions.sort(key=lambda item: (self._priority_rank(item.priority), item.action_id))
        return actions[:8]

    def _action_from_guardrail(
        self,
        guardrail: RiskGuardrailCheck,
    ) -> RiskActionItem | None:
        guardrail_status = self._normalize_guardrail_status(guardrail.status)
        if guardrail_status == RiskGuardrailStatus.PASS:
            return None

        if guardrail.guardrail_id.startswith("guardrail.dscr."):
            action_id = "action.dscr.coverage"
            title = "Strengthen DSCR coverage and covenant cushion"
            owner = "Financial Advisor / Sponsor"
            expected_impact = (
                "Improves debt-service resilience and reduces probability of covenant stress."
            )
        elif guardrail.guardrail_id == "guardrail.capital.equipment_concentration":
            action_id = "action.capital.equipment_concentration"
            title = "Reduce equipment concentration or add concentration mitigants"
            owner = "Sponsor / Independent Engineer"
            expected_impact = (
                "Lowers single-technology concentration exposure in project capital structure."
            )
        else:
            action_id = f"action.{guardrail.guardrail_id.replace('.', '_')}"
            title = f"Resolve {guardrail.metric_name} finding"
            owner = "Project Team"
            expected_impact = "Reduces identified quantitative risk condition."

        priority = self._priority_from_guardrail(guardrail_status)
        target_date_hint = ACTION_TARGET_HINT_BY_PRIORITY[priority]
        rationale = (
            f"{guardrail.metric_name} is currently '{guardrail_status.value}'. {guardrail.rationale}"
        )

        return RiskActionItem(
            action_id=action_id,
            priority=priority,
            owner=owner,
            title=title,
            rationale=rationale,
            evidence_required=list(guardrail.evidence_paths),
            target_date_hint=target_date_hint,
            expected_impact=expected_impact,
            source_refs=[guardrail.guardrail_id],
        )

    def _action_from_dimension(
        self,
        dimension: RiskDimensionDiagnostics,
    ) -> RiskActionItem | None:
        dimension_gap_severity = self._normalize_gap_severity(dimension.gap_severity)
        if dimension_gap_severity == RiskGapSeverity.LOW:
            return None

        priority = (
            RiskActionPriority.HIGH
            if dimension_gap_severity == RiskGapSeverity.HIGH
            else RiskActionPriority.MEDIUM
        )
        action_id = f"action.{dimension.dimension_id.replace('.', '_')}.coverage"
        title = f"Close evidence coverage for {dimension.dimension_id}"
        owner = self._owner_for_dimension(dimension.dimension_id)
        evidence_required = list(RISK_DIMENSIONS.get(dimension.dimension_id, ()))
        target_date_hint = ACTION_TARGET_HINT_BY_PRIORITY[priority]
        project_status_value = (
            dimension.project_status.value
            if isinstance(dimension.project_status, RiskProjectStatus)
            else str(dimension.project_status)
        )
        rationale = (
            f"Dimension status is '{project_status_value}' with gap severity "
            f"'{dimension_gap_severity.value}'."
        )
        expected_impact = (
            "Improves benchmark posture stability and reduces uncertainty in risk diagnostics."
        )

        return RiskActionItem(
            action_id=action_id,
            priority=priority,
            owner=owner,
            title=title,
            rationale=rationale,
            evidence_required=evidence_required,
            target_date_hint=target_date_hint,
            expected_impact=expected_impact,
            source_refs=[dimension.dimension_id],
        )

    def _merge_action(
        self,
        action_map: dict[str, RiskActionItem],
        action: RiskActionItem,
    ) -> None:
        existing = action_map.get(action.action_id)
        if existing is None:
            action_map[action.action_id] = action
            return

        merged_priority = (
            existing.priority
            if self._priority_rank(existing.priority) <= self._priority_rank(action.priority)
            else action.priority
        )
        action_map[action.action_id] = RiskActionItem(
            action_id=existing.action_id,
            priority=merged_priority,
            owner=existing.owner,
            title=existing.title,
            rationale=existing.rationale,
            evidence_required=sorted(set(existing.evidence_required + action.evidence_required)),
            target_date_hint=ACTION_TARGET_HINT_BY_PRIORITY[merged_priority],
            expected_impact=existing.expected_impact,
            source_refs=sorted(set(existing.source_refs + action.source_refs)),
        )

    @staticmethod
    def _priority_rank(priority: RiskActionPriority | str) -> int:
        normalized = priority.value if isinstance(priority, RiskActionPriority) else str(priority)
        if normalized == RiskActionPriority.HIGH.value:
            return 0
        if normalized == RiskActionPriority.MEDIUM.value:
            return 1
        return 2

    @classmethod
    def _priority_from_guardrail(cls, status: RiskGuardrailStatus | str) -> RiskActionPriority:
        normalized_status = cls._normalize_guardrail_status(status)
        if normalized_status == RiskGuardrailStatus.BREACH:
            return RiskActionPriority.HIGH
        if normalized_status == RiskGuardrailStatus.WATCH:
            return RiskActionPriority.MEDIUM
        return RiskActionPriority.LOW

    @staticmethod
    def _normalize_guardrail_status(status: RiskGuardrailStatus | str) -> RiskGuardrailStatus:
        if isinstance(status, RiskGuardrailStatus):
            return status
        return RiskGuardrailStatus(str(status))

    @staticmethod
    def _normalize_gap_severity(gap_severity: RiskGapSeverity | str) -> RiskGapSeverity:
        if isinstance(gap_severity, RiskGapSeverity):
            return gap_severity
        return RiskGapSeverity(str(gap_severity))

    @staticmethod
    def _owner_for_dimension(dimension_id: str) -> str:
        if dimension_id == "risk.technology":
            return "Independent Engineer / Sponsor"
        if dimension_id == "risk.construction":
            return "EPC / Sponsor"
        if dimension_id == "risk.market":
            return "Commercial Lead / Financial Advisor"
        if dimension_id == "risk.regulatory":
            return "Bond Counsel / Permitting Lead"
        if dimension_id == "risk.feedstock":
            return "Operations / Sponsor"
        return "Project Team"

    def _build_internal_executive_summary(
        self,
        diagnostics: RiskDiagnosticsResponse,
    ) -> RiskInternalExecutiveSummary:
        low_reliability_dimensions = sum(
            1
            for dimension in diagnostics.dimensions
            if self._normalize_reliability_band(dimension.confidence.reliability_band)
            == RiskReliabilityBand.LOW
        )
        guardrail_breaches = sum(
            1
            for guardrail in diagnostics.guardrails
            if self._normalize_guardrail_status(guardrail.status) == RiskGuardrailStatus.BREACH
        )
        guardrail_watches = sum(
            1
            for guardrail in diagnostics.guardrails
            if self._normalize_guardrail_status(guardrail.status) == RiskGuardrailStatus.WATCH
        )
        high_priority_actions = sum(
            1 for action in diagnostics.actions if self._priority_rank(action.priority) == 0
        )

        top_findings: list[str] = []
        for guardrail in diagnostics.guardrails:
            if self._normalize_guardrail_status(guardrail.status) == RiskGuardrailStatus.BREACH:
                top_findings.append(
                    f"{guardrail.metric_name}: breach ({self._format_observed_value(guardrail)})."
                )
            if len(top_findings) >= 3:
                break

        if len(top_findings) < 3:
            for dimension in diagnostics.dimensions:
                if self._normalize_gap_severity(dimension.gap_severity) == RiskGapSeverity.HIGH:
                    top_findings.append(
                        f"{dimension.dimension_id}: high evidence gap with "
                        f"{self._normalize_benchmark_position(dimension.benchmark_position).value} "
                        "benchmark posture."
                    )
                if len(top_findings) >= 3:
                    break

        if not top_findings:
            top_findings = ["No material risk findings above baseline thresholds."]

        return RiskInternalExecutiveSummary(
            overall_benchmark_position=self._normalize_benchmark_position(
                diagnostics.overall_posture.benchmark_position
            ),
            overall_posture_score=diagnostics.overall_posture.posture_score,
            reliability_low_dimensions=low_reliability_dimensions,
            guardrail_breaches=guardrail_breaches,
            guardrail_watches=guardrail_watches,
            high_priority_actions=high_priority_actions,
            top_findings=top_findings,
        )

    def _build_readiness_input(
        self,
        diagnostics: RiskDiagnosticsResponse,
    ) -> RiskReadinessInput:
        critical_risk_flags: list[str] = []
        for guardrail in diagnostics.guardrails:
            if self._normalize_guardrail_status(guardrail.status) == RiskGuardrailStatus.BREACH:
                critical_risk_flags.append(
                    f"{guardrail.metric_name}: {guardrail.rationale}"
                )

        for dimension in diagnostics.dimensions:
            if self._normalize_gap_severity(dimension.gap_severity) == RiskGapSeverity.HIGH:
                critical_risk_flags.append(
                    f"{dimension.dimension_id}: missing evidence set; posture "
                    f"{self._normalize_benchmark_position(dimension.benchmark_position).value} corpus."
                )

        if not critical_risk_flags:
            critical_risk_flags = ["No critical risk flags from current evidence baseline."]

        directional_guidance_only = any(
            self._normalize_reliability_band(dimension.confidence.reliability_band)
            == RiskReliabilityBand.LOW
            for dimension in diagnostics.dimensions
        )
        recommended_actions = [
            action
            for action in diagnostics.actions
            if self._priority_rank(action.priority) <= 1
        ][:5]
        if not recommended_actions:
            recommended_actions = diagnostics.actions[:3]

        return RiskReadinessInput(
            critical_risk_flags=critical_risk_flags[:8],
            directional_guidance_only=directional_guidance_only,
            recommended_actions=recommended_actions,
        )

    def _build_advisory_input(
        self,
        diagnostics: RiskDiagnosticsResponse,
    ) -> RiskAdvisoryInput:
        material_statements: list[RiskAdvisoryStatement] = []
        for dimension in diagnostics.dimensions:
            gap_severity = self._normalize_gap_severity(dimension.gap_severity)
            benchmark_position = self._normalize_benchmark_position(dimension.benchmark_position)
            if gap_severity == RiskGapSeverity.LOW and benchmark_position != RiskBenchmarkPosition.ABOVE:
                continue

            reliability_band = self._normalize_reliability_band(
                dimension.confidence.reliability_band
            )
            statement = (
                f"{dimension.dimension_id} is {benchmark_position.value} corpus with "
                f"{gap_severity.value} gap severity and {reliability_band.value} reliability."
            )
            material_statements.append(
                RiskAdvisoryStatement(
                    dimension_id=dimension.dimension_id,
                    statement=statement,
                    gap_severity=gap_severity,
                    benchmark_position=benchmark_position,
                    reliability_band=reliability_band,
                )
            )

        mitigant_highlights = [
            f"{dimension.dimension_id}: mitigants documented with "
            f"{self._normalize_reliability_band(dimension.confidence.reliability_band).value} "
            "reliability."
            for dimension in diagnostics.dimensions
            if (
                (
                    self._normalize_project_status(dimension.project_status)
                    == RiskProjectStatus.COMPLETE
                )
                and (
                    self._normalize_reliability_band(dimension.confidence.reliability_band)
                    != RiskReliabilityBand.LOW
                )
            )
        ]
        if not mitigant_highlights:
            mitigant_highlights = ["No high-confidence mitigant highlights available yet."]

        action_briefs = [
            f"{action.title} ({self._priority_value(action.priority)} priority, target {action.target_date_hint})"
            for action in diagnostics.actions[:5]
        ]

        return RiskAdvisoryInput(
            material_risk_statements=material_statements[:8],
            mitigant_highlights=mitigant_highlights[:5],
            action_briefs=action_briefs,
        )

    def _build_external_assumptions(
        self,
        diagnostics: RiskDiagnosticsResponse,
    ) -> list[str]:
        assumptions: list[str] = []
        for dimension in diagnostics.dimensions:
            if (
                self._normalize_reliability_band(dimension.confidence.reliability_band)
                == RiskReliabilityBand.LOW
            ):
                assumptions.append(
                    f"{dimension.dimension_id}: current posture is directional pending additional evidence."
                )

        for guardrail in diagnostics.guardrails:
            if self._normalize_guardrail_status(guardrail.status) == (
                RiskGuardrailStatus.INSUFFICIENT_EVIDENCE
            ):
                assumptions.append(
                    f"{guardrail.metric_name}: quantitative assessment pending validated supporting data."
                )

        if not assumptions:
            assumptions = ["No material assumptions beyond current validated evidence set."]

        return assumptions[:6]

    @staticmethod
    def _build_external_compliance_checks() -> list[RiskExternalComplianceCheck]:
        return [
            RiskExternalComplianceCheck(
                rule_id="no_internal_conflict_diagnostics",
                passed=True,
                detail="Conflict counts and unresolved conflict references are excluded.",
            ),
            RiskExternalComplianceCheck(
                rule_id="no_operational_queue_metadata",
                passed=True,
                detail="Internal queue and workflow metadata are not included.",
            ),
            RiskExternalComplianceCheck(
                rule_id="no_internal_uncertainty_notes",
                passed=True,
                detail="Internal uncertainty notes are converted to external assumptions.",
            ),
        ]

    def _render_external_markdown(
        self,
        diagnostics: RiskDiagnosticsResponse,
        advisory_input: RiskAdvisoryInput,
        key_assumptions: list[str],
        next_steps: list[RiskExternalActionBrief],
        compliance_checks: list[RiskExternalComplianceCheck],
    ) -> str:
        lines: list[str] = [
            "# External Advisory Risk Brief",
            "",
            "- Contract Version: risk-external-v1",
            f"- Project ID: {diagnostics.project_id}",
            f"- Overall posture score: {diagnostics.overall_posture.posture_score:.3f}",
            (
                "- Overall benchmark posture: "
                f"{self._normalize_benchmark_position(diagnostics.overall_posture.benchmark_position).value}"
            ),
            "",
            "## Material Risk Statements",
        ]
        if not advisory_input.material_risk_statements:
            lines.append("- No material risk statements above external disclosure threshold.")
        else:
            for statement in advisory_input.material_risk_statements:
                lines.append(f"- {statement.statement}")

        lines.extend(["", "## Mitigant Summary"])
        for highlight in advisory_input.mitigant_highlights:
            lines.append(f"- {highlight}")

        lines.extend(["", "## Key Assumptions"])
        for assumption in key_assumptions:
            lines.append(f"- {assumption}")

        lines.extend(["", "## Advisory Next Steps"])
        if not next_steps:
            lines.append("- No immediate advisory actions.")
        else:
            for index, action in enumerate(next_steps, start=1):
                lines.append(
                    f"{index}. [{self._priority_value(action.priority)}] {action.title} "
                    f"(owner: {action.owner}; target: {action.target_date_hint})."
                )

        lines.extend(["", "## Compliance Review"])
        for check in compliance_checks:
            lines.append(
                f"- {check.rule_id}: {'pass' if check.passed else 'fail'} - {check.detail}"
            )

        return "\n".join(lines)

    def _render_internal_markdown(
        self,
        diagnostics: RiskDiagnosticsResponse,
        executive_summary: RiskInternalExecutiveSummary,
        readiness_input: RiskReadinessInput,
        advisory_input: RiskAdvisoryInput,
    ) -> str:
        lines: list[str] = [
            "# Internal Risk Report",
            "",
            "- Contract Version: risk-internal-v1",
            f"- Project ID: {diagnostics.project_id}",
            f"- Cohort: {diagnostics.cohort.sector} / {diagnostics.cohort.deal_type} / "
            f"{diagnostics.cohort.issuer_size_band} / {diagnostics.cohort.recency_window}",
            f"- Cohort Sample Size: {diagnostics.cohort.sample_size}",
            "",
            "## Executive Summary",
            "",
            (
                f"- Overall posture: {self._normalize_benchmark_position(executive_summary.overall_benchmark_position).value} corpus "
                f"({executive_summary.overall_posture_score:.3f})"
            ),
            f"- Guardrail breaches: {executive_summary.guardrail_breaches}",
            f"- Guardrail watches: {executive_summary.guardrail_watches}",
            f"- Low-reliability dimensions: {executive_summary.reliability_low_dimensions}",
            f"- High-priority actions: {executive_summary.high_priority_actions}",
            "",
            "### Top Findings",
        ]
        for finding in executive_summary.top_findings:
            lines.append(f"- {finding}")

        lines.extend(
            [
                "",
                "## Dimension Diagnostics",
                "",
                "| Dimension | Status | Gap | Benchmark | Reliability | Evidence | Conflicts |",
                "|---|---|---|---|---|---:|---:|",
            ]
        )
        for dimension in diagnostics.dimensions:
            reliability_band = self._normalize_reliability_band(
                dimension.confidence.reliability_band
            ).value
            benchmark_position = self._normalize_benchmark_position(
                dimension.benchmark_position
            ).value
            project_status = (
                dimension.project_status.value
                if isinstance(dimension.project_status, RiskProjectStatus)
                else str(dimension.project_status)
            )
            gap_severity = self._normalize_gap_severity(dimension.gap_severity).value
            lines.append(
                "| "
                f"{dimension.dimension_id} | {project_status} | {gap_severity} | "
                f"{benchmark_position} | {reliability_band} | {dimension.evidence_count} | "
                f"{dimension.conflict_count} |"
            )

        lines.extend(
            [
                "",
                "## Guardrail Checks",
                "",
                "| Guardrail | Status | Observed | Thresholds | Evidence Paths |",
                "|---|---|---|---|---|",
            ]
        )
        for guardrail in diagnostics.guardrails:
            status = self._normalize_guardrail_status(guardrail.status).value
            lines.append(
                "| "
                f"{guardrail.metric_name} | {status} | "
                f"{self._format_observed_value(guardrail)} | "
                f"{self._format_threshold(guardrail.threshold)} | "
                f"{', '.join(guardrail.evidence_paths) if guardrail.evidence_paths else 'n/a'} |"
            )

        lines.extend(["", "## Prioritized Actions", ""])
        if not diagnostics.actions:
            lines.append("- No actions generated.")
        else:
            for index, action in enumerate(diagnostics.actions, start=1):
                lines.append(
                    f"{index}. [{self._priority_value(action.priority)}] {action.title} - owner: {action.owner}; "
                    f"target: {action.target_date_hint}."
                )

        lines.extend(["", "## Readiness Handoff", ""])
        lines.append(
            "- Directional guidance only: "
            f"{'yes' if readiness_input.directional_guidance_only else 'no'}"
        )
        lines.append("- Critical flags:")
        for flag in readiness_input.critical_risk_flags:
            lines.append(f"- {flag}")

        lines.extend(["", "## Advisory Handoff", ""])
        lines.append("- Material risk statements:")
        for statement in advisory_input.material_risk_statements:
            lines.append(f"- {statement.statement}")
        lines.append("- Mitigant highlights:")
        for highlight in advisory_input.mitigant_highlights:
            lines.append(f"- {highlight}")
        lines.append("- Action briefs:")
        for brief in advisory_input.action_briefs:
            lines.append(f"- {brief}")

        return "\n".join(lines)

    @staticmethod
    def _normalize_reliability_band(
        reliability_band: RiskReliabilityBand | str,
    ) -> RiskReliabilityBand:
        if isinstance(reliability_band, RiskReliabilityBand):
            return reliability_band
        return RiskReliabilityBand(str(reliability_band))

    @staticmethod
    def _reliability_rank(reliability_band: RiskReliabilityBand) -> int:
        if reliability_band == RiskReliabilityBand.HIGH:
            return 2
        if reliability_band == RiskReliabilityBand.MEDIUM:
            return 1
        return 0

    @staticmethod
    def _normalize_benchmark_position(
        benchmark_position: RiskBenchmarkPosition | str,
    ) -> RiskBenchmarkPosition:
        if isinstance(benchmark_position, RiskBenchmarkPosition):
            return benchmark_position
        return RiskBenchmarkPosition(str(benchmark_position))

    @staticmethod
    def _format_observed_value(guardrail: RiskGuardrailCheck) -> str:
        if guardrail.observed_value is None:
            return "n/a"
        if guardrail.unit == "x":
            return f"{guardrail.observed_value:.3f}x"
        if guardrail.unit == "ratio":
            return f"{guardrail.observed_value:.1%}"
        return f"{guardrail.observed_value:.3f}"

    @staticmethod
    def _format_threshold(threshold: RiskGuardrailThreshold) -> str:
        parts: list[str] = []
        if threshold.target_min is not None:
            parts.append(f"target >= {threshold.target_min}")
        if threshold.tolerance_min is not None:
            parts.append(f"tol >= {threshold.tolerance_min}")
        if threshold.target_max is not None:
            parts.append(f"target <= {threshold.target_max}")
        if threshold.tolerance_max is not None:
            parts.append(f"tol <= {threshold.tolerance_max}")
        return "; ".join(parts) if parts else "n/a"

    @staticmethod
    def _normalize_project_status(
        project_status: RiskProjectStatus | str,
    ) -> RiskProjectStatus:
        if isinstance(project_status, RiskProjectStatus):
            return project_status
        return RiskProjectStatus(str(project_status))

    @staticmethod
    def _priority_value(priority: RiskActionPriority | str) -> str:
        if isinstance(priority, RiskActionPriority):
            return priority.value
        return str(priority)

    @staticmethod
    def _risk_gap_id(action_id: str) -> str:
        return f"risk_action:{action_id}"

    def _build_information_request_payload(
        self,
        action: RiskActionItem,
    ) -> dict[str, object]:
        request_priority = self._request_priority_from_action(action)
        minimum_confidence = self._minimum_confidence_for_priority(request_priority)
        missing_fact_paths = list(action.evidence_required or action.source_refs)
        if not missing_fact_paths:
            missing_fact_paths = [f"risk.action.{action.action_id}"]

        return {
            "title": action.title,
            "missing_fact_paths": missing_fact_paths,
            "current_evidence_state": self._evidence_state_for_priority(request_priority).value,
            "why_it_matters": (
                f"{action.expected_impact} This request operationalizes risk action "
                f"'{action.action_id}'."
            ),
            "who_needs_it": self._split_owner_roles(action.owner),
            "when_needed": f"Target completion in {action.target_date_hint}",
            "consequences": self._consequences_for_priority(request_priority),
            "related_requirements": list(action.source_refs),
            "regulatory_reference": None,
            "affected_checklist_items": [],
            "affected_dimensions": self._extract_affected_dimensions(action),
            "guidance_overview": (
                f"{action.rationale} Acceptance criteria: provide source-backed evidence for each "
                f"required path and review at confidence >= {minimum_confidence:.2f}."
            ),
            "specific_questions": [
                f"Provide validated evidence for '{path}' and explain how it addresses this action."
                for path in missing_fact_paths[:6]
            ],
            "data_points_needed": missing_fact_paths[:10],
            "suggested_approach": (
                "Submit source documents and extracted facts with provenance references for review."
            ),
            "common_pitfalls": [
                "Submitting evidence without provenance or date context.",
                "Providing summaries without underlying support documents.",
            ],
            "time_estimate": action.target_date_hint,
            "examples": [],
            "acceptable_sources": [
                "Financial model extracts",
                "Engineering reports",
                "Executed agreements or signed term sheets",
                "Regulatory filings and permits",
            ],
            "minimum_confidence": minimum_confidence,
            "expected_format": (
                "Approved facts per required path with linked source artifacts and reviewer notes."
            ),
            "priority": request_priority.value,
            "suggested_owner": action.owner,
            "target_date": self._target_date_from_hint(action.target_date_hint),
        }

    @staticmethod
    def _apply_information_request_payload(
        request: InformationRequest,
        payload: Mapping[str, object],
    ) -> None:
        request.title = str(payload["title"])
        request.missing_fact_paths = list(payload["missing_fact_paths"])
        request.current_evidence_state = str(payload["current_evidence_state"])
        request.why_it_matters = str(payload["why_it_matters"])
        request.who_needs_it = list(payload["who_needs_it"])
        request.when_needed = str(payload["when_needed"]) if payload["when_needed"] else None
        request.consequences = str(payload["consequences"])
        request.related_requirements = list(payload["related_requirements"])
        request.regulatory_reference = (
            str(payload["regulatory_reference"]) if payload["regulatory_reference"] else None
        )
        request.affected_checklist_items = list(payload["affected_checklist_items"])
        request.affected_dimensions = list(payload["affected_dimensions"])
        request.guidance_overview = str(payload["guidance_overview"])
        request.specific_questions = list(payload["specific_questions"])
        request.data_points_needed = list(payload["data_points_needed"])
        request.suggested_approach = (
            str(payload["suggested_approach"]) if payload["suggested_approach"] else None
        )
        request.common_pitfalls = list(payload["common_pitfalls"])
        request.time_estimate = str(payload["time_estimate"]) if payload["time_estimate"] else None
        request.examples = list(payload["examples"])
        request.acceptable_sources = list(payload["acceptable_sources"])
        request.minimum_confidence = float(payload["minimum_confidence"])
        request.expected_format = (
            str(payload["expected_format"]) if payload["expected_format"] else None
        )
        request.priority = str(payload["priority"])
        request.suggested_owner = str(payload["suggested_owner"]) if payload["suggested_owner"] else None
        request.target_date = payload["target_date"]

    def _request_priority_from_action(self, action: RiskActionItem) -> RequestPriority:
        priority_value = self._priority_value(action.priority)
        if priority_value == RiskActionPriority.HIGH.value:
            if any(ref.startswith("guardrail.") for ref in action.source_refs):
                return RequestPriority.CRITICAL
            return RequestPriority.HIGH
        if priority_value == RiskActionPriority.MEDIUM.value:
            return RequestPriority.MEDIUM
        return RequestPriority.LOW

    @staticmethod
    def _evidence_state_for_priority(priority: RequestPriority) -> EvidenceState:
        if priority in {RequestPriority.CRITICAL, RequestPriority.HIGH}:
            return EvidenceState.NONE
        if priority == RequestPriority.MEDIUM:
            return EvidenceState.PARTIAL
        return EvidenceState.WEAK

    @staticmethod
    def _minimum_confidence_for_priority(priority: RequestPriority) -> float:
        if priority == RequestPriority.CRITICAL:
            return 0.92
        if priority == RequestPriority.HIGH:
            return 0.90
        if priority == RequestPriority.MEDIUM:
            return 0.85
        return 0.80

    @staticmethod
    def _split_owner_roles(owner: str) -> list[str]:
        normalized = owner.replace(",", "/")
        roles = [part.strip() for part in normalized.split("/") if part.strip()]
        return roles or ["Project Team"]

    @staticmethod
    def _extract_affected_dimensions(action: RiskActionItem) -> list[str]:
        dimensions: set[str] = set()
        for ref in [*action.source_refs, *action.evidence_required]:
            if not ref.startswith("risk."):
                continue
            parts = ref.split(".")
            if len(parts) >= 2:
                dimensions.add(".".join(parts[:2]))
        return sorted(dimensions)

    @staticmethod
    def _consequences_for_priority(priority: RequestPriority) -> str:
        if priority == RequestPriority.CRITICAL:
            return "Unresolved critical risk action can block readiness and advisory progression."
        if priority == RequestPriority.HIGH:
            return "Delayed response may materially degrade risk posture confidence."
        if priority == RequestPriority.MEDIUM:
            return "Missing evidence limits directional confidence for advisory decisions."
        return "Timely completion improves evidence quality and advisory clarity."

    @staticmethod
    def _target_date_from_hint(target_date_hint: str) -> date:
        match = re.search(r"(\d+)", target_date_hint or "")
        days = int(match.group(1)) if match else 14
        days = max(1, min(days, 180))
        return date.today() + timedelta(days=days)

    @staticmethod
    def _risk_request_code(project_id: UUID, action_id: str) -> str:
        base_action = re.sub(r"[^a-z0-9]+", "-", action_id.lower()).strip("-")
        base_action = base_action[:16] if base_action else "action"
        project_part = str(project_id).split("-")[0]
        digest = hashlib.sha1(f"{project_id}:{action_id}".encode("utf-8")).hexdigest()[:6]
        return f"IR-RISK-{project_part}-{base_action}-{digest}"[:50]
