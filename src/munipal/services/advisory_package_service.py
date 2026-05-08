"""
Advisory Package Services for v2 Bifurcated Deliverables.

Per spec: Split the current monolithic handoff pack into:
- InternalReadinessReport (for sponsor team use)
- ExternalAdvisoryPackage (for municipal advisor consumption)

Core principles (NON-NEGOTIABLE):
- External Package never reveals internal gaps, conflicts, or operational status
- Internal Report contains full operational detail
- Same underlying facts, different presentations
"""

import logging
import re
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.config import get_settings
from munipal.core.models.advisory_package import (
    ExternalAdvisoryPackage,
    InternalReadinessReport,
)
from munipal.core.models.fact import ExtractedFact
from munipal.core.models.information_request import InformationRequest
from munipal.core.models.project import Project
from munipal.core.schemas.advisory_package import (
    DistributionValidation,
    ExternalAdvisoryPackageRead,
    InternalReadinessReportRead,
)
from munipal.core.schemas.base import ChecklistPhase, ReviewStatus
from munipal.core.schemas.information_request import RequestStatus
from munipal.services.fact_service import FactConflictDetector, FactService
from munipal.services.playbook_data import READINESS_CONFIG

logger = logging.getLogger(__name__)


# =============================================================================
# Internal Readiness Report Service
# =============================================================================


class InternalReportService:
    """
    Service for generating Internal Readiness Reports.

    Per spec: Operational control document providing complete visibility
    into readiness state, gaps, information requests, evidence, and checklist.
    NOT for external consumption.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def create_report(
        self, project_id: UUID, playbook_version: str | None = None
    ) -> InternalReadinessReport:
        """Create a new internal readiness report."""
        # Get next version
        result = await self.session.execute(
            select(func.max(InternalReadinessReport.version)).where(
                InternalReadinessReport.project_id == str(project_id)
            )
        )
        max_version = result.scalar() or 0

        report = InternalReadinessReport(
            id=str(uuid4()),
            project_id=str(project_id),
            version=max_version + 1,
            playbook_version=playbook_version,
            bfms_version="2.0.0",
            is_complete=False,
        )
        self.session.add(report)
        await self.session.flush()
        return report

    async def get_report(self, report_id: UUID) -> InternalReadinessReport | None:
        """Get an internal report by ID."""
        result = await self.session.execute(
            select(InternalReadinessReport).where(
                InternalReadinessReport.id == str(report_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_report(self, project_id: UUID) -> InternalReadinessReport | None:
        """Get the latest internal report for a project."""
        result = await self.session.execute(
            select(InternalReadinessReport)
            .where(InternalReadinessReport.project_id == str(project_id))
            .order_by(InternalReadinessReport.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_reports(
        self, project_id: UUID, limit: int = 10, offset: int = 0
    ) -> tuple[list[InternalReadinessReport], int]:
        """List internal reports for a project."""
        # Get total count
        count_result = await self.session.execute(
            select(func.count(InternalReadinessReport.id)).where(
                InternalReadinessReport.project_id == str(project_id)
            )
        )
        total = count_result.scalar() or 0

        # Get reports
        result = await self.session.execute(
            select(InternalReadinessReport)
            .where(InternalReadinessReport.project_id == str(project_id))
            .order_by(InternalReadinessReport.version.desc())
            .limit(limit)
            .offset(offset)
        )
        reports = list(result.scalars().all())

        return reports, total

    async def generate_report(
        self, project_id: UUID, force_regenerate: bool = False
    ) -> InternalReadinessReport:
        """Generate a complete internal readiness report."""
        logger.info(f"Generating internal readiness report for project {project_id}")

        # Create new report
        report = await self.create_report(project_id)
        report.generation_started_at = datetime.now(UTC)

        # Import services for readiness and checklist computation
        from munipal.services.checklist_service import ChecklistService
        from munipal.services.information_request_service import InformationRequestService
        from munipal.services.readiness_service import ReadinessService

        readiness_service = ReadinessService(self.session)
        checklist_service = ChecklistService(self.session)
        info_request_service = InformationRequestService(self.session)

        # Generate information requests from gaps BEFORE fetching requests
        # This ensures all templates (including risk_factors_013) are evaluated
        try:
            await info_request_service.generate_requests_from_gaps(project_id)
            logger.info(f"Generated information requests from gaps for project {project_id}")
        except Exception as e:
            logger.warning(f"Failed to generate info requests from gaps: {e}")

        # Get data (now includes any newly generated requests)
        facts = await self._get_facts(project_id)
        requests = await self._get_requests(project_id)

        # Compute readiness
        assessment = await readiness_service.compute_assessment(str(project_id))

        # Build sections
        report.executive_summary = self._build_executive_summary(assessment, requests)
        report.readiness_dashboard = self._build_readiness_dashboard(assessment)
        report.gap_analysis = await self._build_gap_analysis(project_id, readiness_service)
        report.information_requests_section = self._build_requests_section(requests)
        report.checklist_status = await self._build_checklist_status(project_id, checklist_service)
        report.evidence_index = await self._build_evidence_index(project_id, facts)
        report.assumption_register = self._build_assumption_register(facts)

        # Set metrics
        report.overall_score = assessment.overall_score
        report.dimension_scores = [
            {
                "dimension": dim.value if hasattr(dim, 'value') else dim,
                "name": score.dimension_name,
                "score": score.score,
                "weight": score.weight,
            }
            for dim, score in assessment.dimensions.items()
        ]
        report.critical_gap_count = assessment.critical_gaps_count
        report.high_gap_count = assessment.material_gaps_count
        report.open_request_count = sum(
            1 for r in requests if r.status == RequestStatus.OPEN.value
        )
        report.overdue_request_count = sum(
            1
            for r in requests
            if r.target_date
            and r.target_date < datetime.now(UTC).date()
            and r.status in [RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value]
        )
        report.facts_count = len([
            f
            for f in facts
            if f.review_status == ReviewStatus.APPROVED.value
            and f.lifecycle_state == "active"
        ])

        report.is_complete = True
        report.generation_completed_at = datetime.now(UTC)

        await self.session.flush()
        logger.info(f"Generated internal report {report.id}")

        return report

    def _build_executive_summary(self, assessment, requests) -> dict:
        """Build the executive summary section."""
        score = assessment.overall_score

        # Determine status
        if score >= 7.6:
            interpretation = "Ready for advisor-led market review"
            emoji = "green_circle"
        elif score >= 5.6:
            interpretation = "Ready for selective advisor engagement"
            emoji = "yellow_circle"
        elif score >= 3.1:
            interpretation = "Structurally viable; sponsor work should continue"
            emoji = "orange_circle"
        else:
            interpretation = "Too early; focus on foundational work"
            emoji = "red_circle"

        # Get critical blockers
        critical_blockers = []
        for _dim, dim_score in assessment.dimensions.items():
            if dim_score.score < 2.0:
                critical_blockers.append({
                    "title": dim_score.dimension_name,
                    "summary": f"Score: {dim_score.score:.1f}/5.0",
                    "consequences": dim_score.explanation,
                    "owner": "Sponsor",
                })

        return {
            "overall_score": score,
            "score_interpretation": interpretation,
            "status_emoji": emoji,
            "recent_achievements": [],  # Would need historical tracking
            "critical_blockers": critical_blockers,
        }

    def _build_readiness_dashboard(self, assessment) -> dict:
        """Build the readiness dashboard section."""
        dimensions = []
        for dim, score in assessment.dimensions.items():
            # Handle both enum and string keys (Pydantic may convert enum keys to strings)
            dim_value = dim.value if hasattr(dim, 'value') else dim
            dimensions.append({
                "dimension": dim_value,
                "dimension_name": score.dimension_name,
                "score": score.score,
                "max_score": score.max_score,
                "weight": score.weight,
                "weighted_contribution": score.weighted_contribution,
                "critical_paths_covered": score.critical_paths_covered,
                "critical_paths_total": score.critical_paths_total,
                "material_paths_covered": score.material_paths_covered,
                "material_paths_total": score.material_paths_total,
                "explanation": score.explanation,
                "improvement_suggestions": score.improvement_suggestions,
            })

        return {
            "overall_score": assessment.overall_score,
            "dimensions": dimensions,
            "score_interpretation_guide": READINESS_CONFIG["score_thresholds"],
        }

    async def _build_gap_analysis(self, project_id: UUID, readiness_service) -> dict:
        """Build the gap analysis section."""
        gap_report = await readiness_service.compute_gaps(str(project_id))

        # Helper to convert gap to dict
        def gap_to_dict(g):
            return {
                "schema_path": g.schema_path,
                "dimension": g.dimension.value if hasattr(g.dimension, 'value') else g.dimension,
                "criticality": g.criticality,
                "description": g.description,
                "impact": g.impact,
                "suggested_evidence": g.suggested_evidence,
            }

        # Extract risk-specific gaps from all categories
        all_gaps = gap_report.critical_gaps + gap_report.material_gaps + gap_report.secondary_gaps
        risk_factor_gaps = [
            gap_to_dict(g) for g in all_gaps
            if g.schema_path.startswith("risk.")
        ]

        return {
            "summary": {
                "critical_count": len(gap_report.critical_gaps),
                "high_count": len(gap_report.material_gaps),
                "medium_count": len(gap_report.secondary_gaps),
                "low_count": 0,
                "risk_factor_gap_count": len(risk_factor_gaps),
            },
            "critical_gaps": [gap_to_dict(g) for g in gap_report.critical_gaps],
            "high_gaps": [gap_to_dict(g) for g in gap_report.material_gaps],
            "medium_gaps": [gap_to_dict(g) for g in gap_report.secondary_gaps],
            "low_gaps": [],
            "risk_factor_gaps": risk_factor_gaps,
            "priority_actions": gap_report.priority_actions,
        }

    def _build_requests_section(self, requests: list[InformationRequest]) -> dict:
        """Build the information requests section."""
        # Count by status
        status_counts = {s.value: 0 for s in RequestStatus}
        for r in requests:
            status_counts[r.status] = status_counts.get(r.status, 0) + 1

        # Group by owner
        by_owner = {}
        for r in requests:
            owner = r.suggested_owner or "Unassigned"
            if owner not in by_owner:
                by_owner[owner] = {"open_count": 0, "requests": []}
            if r.status == RequestStatus.OPEN.value:
                by_owner[owner]["open_count"] += 1
            by_owner[owner]["requests"].append({
                "request_code": r.request_code,
                "title": r.title,
                "priority": r.priority,
                "status": r.status,
                "target_date": str(r.target_date) if r.target_date else None,
            })

        # Find overdue
        today = datetime.now(UTC).date()
        overdue = [
            {
                "request_code": r.request_code,
                "title": r.title,
                "target_date": str(r.target_date),
                "owner": r.suggested_owner,
            }
            for r in requests
            if r.target_date
            and r.target_date < today
            and r.status in [RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value]
        ]

        return {
            "summary": status_counts,
            "by_owner": [
                {"owner": k, **v} for k, v in by_owner.items()
            ],
            "overdue_requests": overdue,
            "full_requests": [
                {
                    "request_code": r.request_code,
                    "title": r.title,
                    "priority": r.priority,
                    "status": r.status,
                    "owner": r.suggested_owner,
                    "why_it_matters": r.why_it_matters,
                    "guidance_overview": r.guidance_overview,
                    "specific_questions": r.specific_questions,
                }
                for r in requests
            ],
        }

    async def _build_checklist_status(self, project_id: UUID, checklist_service) -> dict:
        """Build the checklist status section."""
        phases = {}
        phase_summary = []

        for phase in ChecklistPhase:
            summary = await checklist_service.get_phase_summary(str(project_id), phase)
            items = await checklist_service.list_items_with_status(str(project_id), phase)

            phases[phase.value] = {
                "completion_percent": summary.completion_percentage,
                "ready_count": summary.ready_count,
                "in_progress_count": summary.in_progress_count,
                "blocked_count": summary.blocked_count,
                "not_started_count": summary.not_started_count,
                "can_proceed": summary.can_proceed_to_next,
                "items": [
                    {
                        "item_code": item.item_code,
                        "title": item.title,
                        "status": item.status.value if hasattr(item.status, 'value') else item.status,
                        "coverage_pct": item.coverage_percentage,
                    }
                    for item in items
                ],
            }

            phase_summary.append({
                "phase": phase.value,
                "name": phase.name,
                "ready": summary.ready_count,
                "in_progress": summary.in_progress_count,
                "blocked": summary.blocked_count,
                "not_started": summary.not_started_count,
                "can_proceed": summary.can_proceed_to_next,
            })

        return {
            "phase_summary": phase_summary,
            "phases": phases,
        }

    async def _build_evidence_index(self, project_id: UUID, facts: list[ExtractedFact]) -> dict:
        """Build the evidence index section."""
        # Count by status
        status_counts = {
            "approved": 0,
            "pending": 0,
            "rejected": 0,
        }
        lifecycle_counts = {
            "active": 0,
            "pending_review": 0,
            "rejected": 0,
            "archived": 0,
        }
        duplicate_counts = {
            "unique": 0,
            "duplicate_exact": 0,
            "duplicate_semantic": 0,
            "candidate_conflict": 0,
        }
        for f in facts:
            if f.review_status == ReviewStatus.APPROVED.value:
                status_counts["approved"] += 1
            elif f.review_status == ReviewStatus.PENDING.value:
                status_counts["pending"] += 1
            elif f.review_status == ReviewStatus.REJECTED.value:
                status_counts["rejected"] += 1
            lifecycle_counts[f.lifecycle_state or "active"] = lifecycle_counts.get(
                f.lifecycle_state or "active",
                0,
            ) + 1
            duplicate_counts[f.duplicate_classification or "unique"] = duplicate_counts.get(
                f.duplicate_classification or "unique",
                0,
            ) + 1

        # Group canonical view by domain (one preferred row per path).
        active_approved = [
            f
            for f in facts
            if f.review_status == ReviewStatus.APPROVED.value
            and f.lifecycle_state == "active"
        ]
        canonical_facts = FactService.select_preferred_facts_by_path(active_approved)

        canonical_by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for f in canonical_facts.values():
            domain = f.schema_path.split(".")[0]
            canonical_by_domain[domain].append({
                "fact_id": f.id,
                "schema_path": f.schema_path,
                "value": str(f.value)[:100],
                "confidence": f.confidence_score,
                "status": f.review_status,
                "criticality": f.criticality,
                "duplicate_classification": f.duplicate_classification,
                "is_canonical": bool(f.is_canonical),
                "lifecycle_state": f.lifecycle_state,
            })

        # Group full ledger by domain (all facts, including archived).
        ledger_by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for f in sorted(
            facts,
            key=lambda item: (
                item.schema_path,
                item.created_at.isoformat() if item.created_at else "",
                item.id,
            ),
        ):
            domain = f.schema_path.split(".")[0]
            ledger_by_domain[domain].append({
                "fact_id": f.id,
                "schema_path": f.schema_path,
                "value": str(f.value)[:100],
                "confidence": f.confidence_score,
                "status": f.review_status,
                "criticality": f.criticality,
                "source_type": f.source_type,
                "duplicate_classification": f.duplicate_classification,
                "is_canonical": bool(f.is_canonical),
                "lifecycle_state": f.lifecycle_state,
                "created_at": f.created_at.isoformat() if f.created_at else None,
                "updated_at": f.updated_at.isoformat() if f.updated_at else None,
            })

        # Keep by_domain for backwards compatibility (canonical view).
        by_domain = {}
        for domain, entries in canonical_by_domain.items():
            by_domain[domain] = entries

        conflict_detector = FactConflictDetector(self.session)
        conflicts = await conflict_detector.find_conflicts(project_id)
        conflict_summary = {
            "total_unresolved_conflicts": len(conflicts),
            "critical": len([c for c in conflicts if str(c.get("criticality", "")).lower() == "critical"]),
            "material": len([c for c in conflicts if str(c.get("criticality", "")).lower() == "material"]),
            "secondary": len([c for c in conflicts if str(c.get("criticality", "")).lower() == "secondary"]),
        }

        return {
            "summary": {
                "total": len(facts),
                **status_counts,
                "canonical_total": len(canonical_facts),
                "ledger_total": len(facts),
                "lifecycle": lifecycle_counts,
                "duplicate_classification": duplicate_counts,
            },
            "by_domain": by_domain,
            "canonical_by_domain": dict(canonical_by_domain),
            "ledger_by_domain": dict(ledger_by_domain),
            "conflicts": conflicts,
            "conflict_summary": conflict_summary,
        }

    def _build_assumption_register(self, facts: list[ExtractedFact]) -> dict:
        """Build the assumption register section."""
        # Filter to assumption-type facts (could be enhanced)
        assumptions = []
        for f in facts:
            if (
                f.review_status == ReviewStatus.APPROVED.value
                and f.lifecycle_state != "archived"
            ):
                assumptions.append({
                    "schema_path": f.schema_path,
                    "value": str(f.value),
                    "confidence": f.confidence_score,
                    "source_type": f.source_type,
                })

        return {
            "summary": {
                "total": len(assumptions),
            },
            "assumptions": assumptions[:50],  # Limit for readability
            "high_impact_assumptions": [],  # Would need impact analysis
        }

    async def _get_facts(self, project_id: UUID) -> list[ExtractedFact]:
        """Get full fact ledger for a project, including archived rows."""
        result = await self.session.execute(
            select(ExtractedFact).where(
                ExtractedFact.project_id == str(project_id),
            )
        )
        return list(result.scalars().all())

    async def _get_requests(self, project_id: UUID) -> list[InformationRequest]:
        """Get all information requests for a project."""
        result = await self.session.execute(
            select(InformationRequest).where(
                InformationRequest.project_id == str(project_id)
            )
        )
        return list(result.scalars().all())

    def report_to_read_schema(
        self, report: InternalReadinessReport
    ) -> InternalReadinessReportRead:
        """Convert model to read schema."""
        return InternalReadinessReportRead(
            id=UUID(report.id),
            project_id=UUID(report.project_id),
            version=report.version,
            playbook_version=report.playbook_version,
            bfms_version=report.bfms_version,
            is_complete=report.is_complete,
            generation_started_at=report.generation_started_at,
            generation_completed_at=report.generation_completed_at,
            executive_summary=report.executive_summary,
            readiness_dashboard=report.readiness_dashboard,
            gap_analysis=report.gap_analysis,
            information_requests_section=report.information_requests_section,
            checklist_status=report.checklist_status,
            evidence_index=report.evidence_index,
            assumption_register=report.assumption_register,
            overall_score=report.overall_score,
            dimension_scores=report.dimension_scores,
            critical_gap_count=report.critical_gap_count,
            high_gap_count=report.high_gap_count,
            open_request_count=report.open_request_count,
            overdue_request_count=report.overdue_request_count,
            facts_count=report.facts_count,
            pdf_storage_path=report.pdf_storage_path,
            md_storage_path=report.md_storage_path,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )


# =============================================================================
# External Advisory Package Service
# =============================================================================


class ExternalPackageService:
    """
    Service for generating External Advisory Packages.

    Per spec: Professional deliverable for municipal advisors.
    Does NOT reveal internal gaps, conflicts, or operational status.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    async def create_package(
        self,
        project_id: UUID,
        title: str,
        generated_for: str,
        playbook_version: str | None = None,
    ) -> ExternalAdvisoryPackage:
        """Create a new external advisory package."""
        # Get next version
        result = await self.session.execute(
            select(func.max(ExternalAdvisoryPackage.version)).where(
                ExternalAdvisoryPackage.project_id == str(project_id)
            )
        )
        max_version = result.scalar() or 0

        package = ExternalAdvisoryPackage(
            id=str(uuid4()),
            project_id=str(project_id),
            version=max_version + 1,
            title=title,
            generated_for=generated_for,
            playbook_version=playbook_version,
            bfms_version="2.0.0",
            is_complete=False,
        )
        self.session.add(package)
        await self.session.flush()
        return package

    async def get_package(self, package_id: UUID) -> ExternalAdvisoryPackage | None:
        """Get a package by ID."""
        result = await self.session.execute(
            select(ExternalAdvisoryPackage).where(
                ExternalAdvisoryPackage.id == str(package_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_package(self, project_id: UUID) -> ExternalAdvisoryPackage | None:
        """Get the latest package for a project."""
        result = await self.session.execute(
            select(ExternalAdvisoryPackage)
            .where(ExternalAdvisoryPackage.project_id == str(project_id))
            .order_by(ExternalAdvisoryPackage.version.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_packages(
        self, project_id: UUID, limit: int = 10, offset: int = 0
    ) -> tuple[list[ExternalAdvisoryPackage], int]:
        """List external packages for a project."""
        # Get total count
        count_result = await self.session.execute(
            select(func.count(ExternalAdvisoryPackage.id)).where(
                ExternalAdvisoryPackage.project_id == str(project_id)
            )
        )
        total = count_result.scalar() or 0

        # Get packages
        result = await self.session.execute(
            select(ExternalAdvisoryPackage)
            .where(ExternalAdvisoryPackage.project_id == str(project_id))
            .order_by(ExternalAdvisoryPackage.version.desc())
            .limit(limit)
            .offset(offset)
        )
        packages = list(result.scalars().all())

        return packages, total

    async def generate_package(
        self,
        project_id: UUID,
        title: str,
        generated_for: str,
        include_disclosure: bool = True,
        force_regenerate: bool = False,
    ) -> ExternalAdvisoryPackage:
        """Generate a complete external advisory package."""
        logger.info(f"Generating external advisory package for project {project_id}")

        # Create package
        package = await self.create_package(project_id, title, generated_for)
        package.generation_started_at = datetime.now(UTC)

        # Get approved facts
        facts = await self._get_approved_facts(project_id)
        facts_by_path = FactService.select_preferred_facts_by_path(facts)
        risk_context = await self._build_risk_integration_context(project_id, facts=facts_by_path)

        # Build sections
        package.cover_page = self._build_cover_page(project_id, title, generated_for, facts_by_path)
        package.executive_summary = self._build_executive_summary(facts_by_path, risk_context)
        package.deal_overview = self._build_deal_overview(facts_by_path)
        package.financial_tables = self._build_financial_tables(facts_by_path)
        package.slb_brief = self._build_slb_brief(facts_by_path)
        package.key_assumptions = self._build_key_assumptions(facts_by_path, risk_context)
        package.disclaimer = self._build_disclaimer()

        # Generate disclosure document if requested
        if include_disclosure:
            from munipal.services.disclosure_service import DisclosureSynthesisService
            disclosure_service = DisclosureSynthesisService(self.session)
            disclosure_doc = await disclosure_service.generate_document(project_id)
            # Ensure async-safe relationship access before iterating tbd_items.
            await self.session.refresh(disclosure_doc, attribute_names=["tbd_items"])
            package.disclosure_document_id = disclosure_doc.id
            package.disclosure_completeness_score = disclosure_doc.completeness_score

            # Count TBDs
            critical_tbd = sum(1 for m in disclosure_doc.tbd_items if m.severity == "critical")
            high_tbd = sum(1 for m in disclosure_doc.tbd_items if m.severity == "high")
            package.critical_tbd_count = critical_tbd
            package.high_tbd_count = high_tbd

        # Validate for distribution, including unresolved conflict checks.
        conflict_detector = FactConflictDetector(self.session)
        unresolved_conflicts = await conflict_detector.find_conflicts(project_id)
        critical_conflict_count = len(
            [c for c in unresolved_conflicts if str(c.get("criticality", "")).lower() == "critical"]
        )
        material_conflict_count = len(
            [c for c in unresolved_conflicts if str(c.get("criticality", "")).lower() == "material"]
        )
        validation = self._validate_for_distribution(
            package,
            critical_conflict_count=critical_conflict_count,
            material_conflict_count=material_conflict_count,
            unresolved_conflict_count=len(unresolved_conflicts),
        )
        package.ready_for_distribution = validation.ready_for_distribution
        package.distribution_issues = validation.issues

        # Get readiness score
        from munipal.services.readiness_service import ReadinessService
        readiness_service = ReadinessService(self.session)
        assessment = await readiness_service.compute_assessment(str(project_id))
        package.readiness_score_at_generation = assessment.overall_score

        package.is_complete = True
        package.generation_completed_at = datetime.now(UTC)

        await self.session.flush()
        logger.info(f"Generated external package {package.id}")

        return package

    def _build_cover_page(
        self, project_id: UUID, title: str, generated_for: str, facts: dict
    ) -> dict:
        """Build the cover page section."""
        project_name = str(self._get_fact_value(facts, "project.canonicaldescription", "Project") or "Project")[:100]
        location = str(self._get_fact_value(facts, "project.location.jurisdiction", "") or "")

        # Determine structure description
        cab_enabled = self._get_fact_value(facts, "cab.enabled", False)
        slb_enabled = self._get_fact_value(facts, "slb.enabled", False)

        if cab_enabled and slb_enabled:
            structure = "Capital Appreciation Bond Structure with Sustainability-Linked Bond Features"
        elif cab_enabled:
            structure = "Capital Appreciation Bond Structure"
        elif slb_enabled:
            structure = "Revenue Bonds with Sustainability-Linked Features"
        else:
            structure = "Revenue Bonds"

        return {
            "project_name": project_name,
            "location": location,
            "bond_type": "Revenue Bonds",
            "structure_description": structure,
            "prepared_for": generated_for,
            "prepared_by": "Project Sponsor",
            "prepared_date": datetime.now(UTC).isoformat(),
            "disclaimer_text": "PRELIMINARY - FOR DISCUSSION PURPOSES ONLY",
        }

    def _build_executive_summary(
        self,
        facts: dict,
        risk_context: dict[str, Any] | None = None,
    ) -> dict:
        """Build the executive summary for external package."""
        # Build key metrics
        metrics = {}
        if "capital.project-cost" in facts:
            metrics["Total Project Cost"] = f"${self._get_numeric_fact_value(facts, 'capital.project-cost', 0):,.0f}"
        if "cab.originalprincipial" in facts:
            metrics["Target Financing Amount"] = f"${self._get_numeric_fact_value(facts, 'cab.originalprincipial', 0):,.0f}"
        if "capital.equity-contribution" in facts:
            metrics["Equity Contribution"] = f"${self._get_numeric_fact_value(facts, 'capital.equity-contribution', 0):,.0f}"
        if "finmodel.outputs.dscrbase" in facts:
            metrics["Base Case DSCR"] = f"{self._get_numeric_fact_value(facts, 'finmodel.outputs.dscrbase', 0):.2f}x"

        next_steps = (
            "This package is provided to support preliminary discussions with the registered municipal advisory team; it is not a recommendation, approval, sizing, pricing, or issuance instruction."
        )
        if risk_context:
            integration_mode = str(risk_context.get("integration_mode", "full")).lower()
            posture_score = float(risk_context.get("overall_posture_score", 0.0))
            directional_guidance_only = bool(risk_context.get("directional_guidance_only", False))
            fallback_reasons = list(risk_context.get("fallback_reasons", []))

            metrics["Risk Integration Mode"] = integration_mode.title()
            metrics["Risk Posture Score"] = f"{posture_score:.3f}"
            metrics["Risk Guidance"] = (
                "Directional" if directional_guidance_only else "Review Ready"
            )

            if integration_mode == "fallback":
                primary_reason = (
                    f" {fallback_reasons[0]}" if fallback_reasons else ""
                )
                next_steps = (
                    "BFMS risk integration is currently in fallback mode; treat risk outputs as directional."
                    f"{primary_reason} "
                    "This package is provided to support preliminary discussions with the registered municipal advisory team; it is not a recommendation, approval, sizing, pricing, or issuance instruction."
                )
            else:
                next_steps = (
                    "BFMS risk integration is currently in full mode for evidence-backed advisor review support. "
                    "This package is provided to support preliminary discussions with the registered municipal advisory team; it is not a recommendation, approval, sizing, pricing, or issuance instruction."
                )

        # Structural highlights
        highlights = []
        if "cab.accretion.period.years" in facts:
            highlights.append(f"CAB Accretion Period: {self._get_fact_value(facts, 'cab.accretion.period.years', 0)} years")
        if "cab.accretionrate" in facts:
            highlights.append(f"Accretion Rate: {self._get_fact_value(facts, 'cab.accretionrate', 0)}%")
        if "slb.kpis.shortlist" in facts:
            highlights.append(f"SLB KPIs: {self._get_fact_value(facts, 'slb.kpis.shortlist', 'TBD')}")

        # Transaction overview
        issuer = str(self._get_fact_value(facts, "parties.issuer.name", "[Issuer TBD]") or "[Issuer TBD]")
        project_desc = str(self._get_fact_value(facts, "project.canonicaldescription", "[Project description TBD]") or "[Project description TBD]")

        return {
            "transaction_overview": f"{issuer} is evaluating potential revenue bond financing for {project_desc[:200]}...",
            "key_metrics": metrics,
            "structural_highlights": highlights,
            "information_pending": [],  # Don't expose gaps
            "next_steps": next_steps,
        }

    def _build_deal_overview(self, facts: dict) -> dict:
        """Build the deal overview memo."""
        return {
            "project_summary": self._get_fact_value(
                facts, "project.canonicaldescription", "[Project description pending]"
            ),
            "financing_context": "Potential revenue bond financing structure for registered advisor and deal-team review",
            "transaction_parties": {
                "Issuer": self._get_fact_value(facts, "parties.issuer.name", "[TBD]"),
                "Borrower": self._get_fact_value(facts, "parties.borrower.name", "[TBD]"),
                "Operator": self._get_fact_value(facts, "parties.operator.name", "[TBD]"),
            },
            "use_of_proceeds": {
                "Total Project Cost": self._get_fact_value(facts, "capital.project-cost", "[TBD]"),
                "Target Financing Amount": self._get_fact_value(facts, "cab.originalprincipial", "[TBD]"),
                "Equity Contribution": self._get_fact_value(facts, "capital.equity-contribution", "[TBD]"),
            },
            "revenue_model_summary": f"Revenue from {self._get_fact_value(facts, 'revenue.commodities.list', '[commodities TBD]')}",
            "structural_notes": "Details in disclosure document sections.",
        }

    def _build_financial_tables(self, facts: dict) -> dict:
        """Build financial tables section."""
        return {
            "capital_structure": {
                "total_project_cost": self._get_fact_value(facts, "capital.project-cost", None),
                "bond_proceeds": self._get_fact_value(facts, "cab.originalprincipial", None),
                "equity": self._get_fact_value(facts, "capital.equity-contribution", None),
                "equity_percent": self._get_fact_value(facts, "capital.equity-percent", None),
            },
            "revenue_projections": [],  # Would need time series data
            "cab_accretion_schedule": [],  # Would need schedule
            "debt_service_schedule": [],  # Would need schedule
            "dscr_analysis": {
                "base_case": self._get_fact_value(facts, "finmodel.outputs.dscrbase", None),
                "stress_case": self._get_fact_value(facts, "finmodel.outputs.dscrstress", None),
                "minimum_covenant": self._get_fact_value(facts, "finmodel.inputs.dscr.minimum", None),
            },
            "sensitivity_tables": [],
            "disclaimer": "All financial projections are preliminary and subject to independent verification.",
        }

    def _build_slb_brief(self, facts: dict) -> dict:
        """Build SLB KPI brief section."""
        slb_enabled = self._get_fact_value(facts, "slb.enabled", False)
        if not slb_enabled:
            return {}

        return {
            "framework_alignment": "ICMA Sustainability-Linked Bond Principles (2023)",
            "kpi_summary_table": [],
            "kpi_details": [
                {
                    "name": self._get_fact_value(facts, "slb.kpi.1.name", "[KPI 1]"),
                    "baseline_value": self._get_fact_value(facts, "slb.kpi.1.baseline.value", "[TBD]"),
                    "methodology": self._get_fact_value(facts, "slb.kpi.1.baseline.methodology", "[TBD]"),
                    "verification": self._get_fact_value(facts, "slb.kpi.1.verification.method", "[TBD]"),
                }
            ],
            "economic_linkage": {
                "SPT Met": "No coupon adjustment",
                "SPT Missed": f"+{self._get_fact_value(facts, 'slb.penalty.stepup.magnitude', '[TBD]')} bps step-up",
            },
            "observation_schedule": ["Year 3", "Year 6", "Year 9"],
            "verification_protocol": "Annual third-party verification anticipated.",
        }

    def _build_key_assumptions(
        self,
        facts: dict,
        risk_context: dict[str, Any] | None = None,
    ) -> list[dict]:
        """Build key assumptions section (filtered subset)."""
        assumptions = []

        # Financial assumptions
        if "cab.accretionrate" in facts:
            assumptions.append({
                "category": "Financial",
                "assumption": "CAB Accretion Rate",
                "value": f"{self._get_fact_value(facts, 'cab.accretionrate', 0)}%",
                "basis": "Market comparable analysis",
            })

        if "opex.margin" in facts:
            assumptions.append({
                "category": "Operational",
                "assumption": "Operating Margin",
                "value": f"{self._get_fact_value(facts, 'opex.margin', 0)}%",
                "basis": "Operator projections",
            })

        if "feedstock.volume.annual" in facts:
            assumptions.append({
                "category": "Operational",
                "assumption": "Annual Throughput",
                "value": f"{self._get_numeric_fact_value(facts, 'feedstock.volume.annual', 0):,.0f} tons",
                "basis": "Nameplate capacity",
            })

        if risk_context:
            integration_mode = str(risk_context.get("integration_mode", "full")).lower()
            directional_guidance_only = bool(risk_context.get("directional_guidance_only", False))
            fallback_reasons = list(risk_context.get("fallback_reasons", []))
            top_next_steps = list(risk_context.get("top_next_steps", []))

            assumptions.append({
                "category": "Risk Analytics",
                "assumption": "BFMS Integration Mode",
                "value": (
                    "Fallback (Directional Guidance)"
                    if directional_guidance_only
                    else "Full (Execution Grade)"
                ),
                "basis": "risk-bfms-integration-v1 contract output",
            })

            if integration_mode == "fallback" and fallback_reasons:
                assumptions.append({
                    "category": "Risk Analytics",
                    "assumption": "Fallback Rationale",
                    "value": str(fallback_reasons[0]),
                    "basis": "risk-bfms-integration-v1 fallback metadata",
                })

            if top_next_steps:
                assumptions.append({
                    "category": "Risk Analytics",
                    "assumption": "Priority Risk Action",
                    "value": str(top_next_steps[0]),
                    "basis": "risk-bfms-integration-v1 advisory_next_steps",
                })

        return assumptions

    async def _build_risk_integration_context(
        self,
        project_id: UUID,
        facts: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Build risk integration context for advisory package content enrichment."""
        settings = get_settings()
        if not settings.risk_reporting_v2_foundation:
            return None

        try:
            from munipal.core.schemas.risk_reporting import RiskBenchmarkCohort
            from munipal.services.risk_reporting_service import RiskReportingService

            project = await self._get_project(project_id)
            cohort_values = self._infer_risk_benchmark_cohort_values(
                project=project,
                facts=facts or {},
            )
            cohort = RiskBenchmarkCohort(**cohort_values)

            service = RiskReportingService(self.session)
            payload = await service.build_bfms_integration_payload(
                project_id=project_id,
                cohort=cohort,
            )
            integration_mode = (
                payload.integration_mode.value
                if hasattr(payload.integration_mode, "value")
                else str(payload.integration_mode)
            )
            return {
                "integration_mode": integration_mode,
                "overall_posture_score": payload.overall_posture_score,
                "directional_guidance_only": payload.directional_guidance_only,
                "reliability_low_dimensions": payload.reliability_low_dimensions,
                "fallback_reasons": payload.fallback_reasons,
                "top_next_steps": [action.title for action in payload.advisory_next_steps[:3]],
                "cohort": cohort_values,
            }
        except Exception:
            logger.warning(
                "BFMS risk integration context unavailable for external package generation",
                exc_info=True,
            )
            return None

    def _infer_risk_benchmark_cohort_values(
        self,
        *,
        project: Project | None,
        facts: dict[str, Any],
    ) -> dict[str, Any]:
        sector = self._infer_cohort_sector(project=project, facts=facts)
        deal_type = self._infer_cohort_deal_type(project=project, facts=facts)
        issuer_size_band = self._infer_cohort_issuer_size_band(project=project, facts=facts)
        return {
            "sector": sector,
            "issuer_size_band": issuer_size_band,
            "deal_type": deal_type,
            "recency_window": "5y",
            "sample_size": self._infer_cohort_sample_size(sector=sector, deal_type=deal_type),
        }

    def _infer_cohort_sector(
        self,
        *,
        project: Project | None,
        facts: dict[str, Any],
    ) -> str:
        hint_blob = self._cohort_hint_blob(project=project, facts=facts)
        healthcare_tokens = (
            "healthcare",
            "hospital",
            "clinic",
            "medical",
            "fqhc",
            "medicaid",
            "patient care",
            "community health",
        )
        waste_tokens = (
            "waste",
            "feedstock",
            "biomass",
            "msw",
            "solid waste",
            "landfill",
            "biochar",
            "renewable diesel",
        )
        if any(token in hint_blob for token in healthcare_tokens):
            return "healthcare"
        if any(token in hint_blob for token in waste_tokens):
            return "waste_to_energy"
        if "feedstock.type" in facts or "feedstock.volume.annual" in facts:
            return "waste_to_energy"
        return "waste_to_energy"

    def _infer_cohort_deal_type(
        self,
        *,
        project: Project | None,
        facts: dict[str, Any],
    ) -> str:
        issuer_text = self._cohort_hint_text(self._get_fact_value(facts, "parties.issuer.name", ""))
        if not issuer_text and project is not None:
            issuer_text = self._cohort_hint_text(project.issuer_name)
        borrower_text = self._cohort_hint_text(self._get_fact_value(facts, "parties.borrower.name", ""))
        hint_blob = self._cohort_hint_blob(project=project, facts=facts)

        if "private activity" in hint_blob or "industrial development bond" in hint_blob:
            return "private_activity"
        if "501(c)(3)" in hint_blob or "501c3" in hint_blob:
            return "private_activity"

        issuer_indicates_conduit = (
            "industrial development authority" in issuer_text
            or "health facilities authority" in issuer_text
            or "housing authority" in issuer_text
            or bool(re.search(r"\bida\b", issuer_text))
        )
        if "conduit" in hint_blob or (bool(borrower_text) and issuer_indicates_conduit):
            return "conduit"
        return "revenue"

    def _infer_cohort_issuer_size_band(
        self,
        *,
        project: Project | None,
        facts: dict[str, Any],
    ) -> str:
        amount = self._cohort_hint_number(self._get_fact_value(facts, "cab.originalprincipial", None))
        if amount is None and project is not None:
            amount = self._cohort_hint_number(project.target_bond_amount)
        if amount is None:
            amount = self._cohort_hint_number(self._get_fact_value(facts, "capital.project-cost", None))

        if amount is None:
            return "mid"
        if amount >= 250_000_000:
            return "large"
        if amount >= 50_000_000:
            return "mid"
        return "small"

    @staticmethod
    def _infer_cohort_sample_size(*, sector: str, deal_type: str) -> int:
        sample_map = {
            ("waste_to_energy", "revenue"): 50,
            ("waste_to_energy", "conduit"): 35,
            ("waste_to_energy", "private_activity"): 30,
            ("healthcare", "revenue"): 30,
            ("healthcare", "conduit"): 24,
            ("healthcare", "private_activity"): 24,
        }
        return sample_map.get((sector, deal_type), 35)

    def _cohort_hint_blob(
        self,
        *,
        project: Project | None,
        facts: dict[str, Any],
    ) -> str:
        hints: list[str] = []
        for path in (
            "project.canonicaldescription",
            "parties.issuer.name",
            "parties.borrower.name",
            "revenue.commodities.list",
            "feedstock.type",
            "project.location.jurisdiction",
        ):
            hint = self._cohort_hint_text(self._get_fact_value(facts, path, ""))
            if hint:
                hints.append(hint)

        if project is not None:
            for value in (
                project.name,
                project.description,
                project.issuer_name,
                project.project_location,
            ):
                hint = self._cohort_hint_text(value)
                if hint:
                    hints.append(hint)
        return " ".join(hints)

    @staticmethod
    def _cohort_hint_text(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, dict):
            if "value" in value:
                return ExternalPackageService._cohort_hint_text(value.get("value"))
            return " ".join(
                ExternalPackageService._cohort_hint_text(item) for item in value.values()
            ).strip().lower()
        if isinstance(value, (list, tuple, set)):
            return " ".join(
                ExternalPackageService._cohort_hint_text(item) for item in value
            ).strip().lower()
        return str(value).strip().lower()

    @staticmethod
    def _cohort_hint_number(value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, dict):
            return ExternalPackageService._cohort_hint_number(value.get("value"))
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _build_disclaimer(self) -> str:
        """Build mandatory disclaimer text."""
        return """## Important Notices and Disclaimer

THIS DOCUMENT IS PRELIMINARY AND FOR DISCUSSION PURPOSES ONLY

### Not an Offering

This Advisory Information Package does not constitute:
- An offer to sell or solicitation of an offer to buy any securities
- A commitment to proceed with the proposed financing
- Investment advice or a recommendation to purchase securities
- A substitute for independent professional advice

### No Reliance

Recipients should not rely on this document for:
- Investment decisions
- Legal, tax, or accounting advice
- Verification of facts or projections
- Assessment of creditworthiness

### Professional Review Required

Before any financing transaction:
- Bond counsel must provide required legal opinions
- Financial advisor must validate financial projections
- Independent Engineer must certify project feasibility
- Rating agencies (if applicable) must complete credit analysis
- Underwriter must complete due diligence

Prepared by Bond Facility Management System v2.0"""

    def _validate_for_distribution(
        self,
        package: ExternalAdvisoryPackage,
        *,
        critical_conflict_count: int = 0,
        material_conflict_count: int = 0,
        unresolved_conflict_count: int = 0,
    ) -> DistributionValidation:
        """Validate package for external distribution."""
        issues = []
        warnings = []
        recommendations = []

        # Check completeness
        if package.disclosure_completeness_score and package.disclosure_completeness_score < 0.5:
            issues.append("Disclosure completeness below 50%")

        # Check TBD counts
        if package.critical_tbd_count > 3:
            issues.append(f"Too many critical TBDs ({package.critical_tbd_count})")

        # Check disclaimer
        if not package.disclaimer:
            issues.append("Missing mandatory disclaimer")

        # Check for key sections
        if not package.deal_overview:
            issues.append("Missing deal overview")

        # Conflict gate: unresolved critical conflicts block external distribution.
        if critical_conflict_count > 0:
            issues.append(
                f"Unresolved critical fact conflicts: {critical_conflict_count}"
            )
            recommendations.append(
                "Resolve critical-path fact conflicts in Facts Review before external distribution."
            )

        if material_conflict_count > 0:
            warnings.append(
                f"Unresolved material fact conflicts: {material_conflict_count}"
            )

        non_critical_conflicts = max(
            0,
            unresolved_conflict_count - critical_conflict_count,
        )
        if non_critical_conflicts > 0:
            recommendations.append(
                "Review remaining non-critical conflicts and archive superseded facts to improve package quality."
            )

        return DistributionValidation(
            ready_for_distribution=len(issues) == 0,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
        )

    def _get_fact_value(self, facts: dict, path: str, default: Any = None) -> Any:
        """Get fact value by path with default."""
        if path in facts:
            fact = facts[path]
            value = fact.value
            if isinstance(value, dict):
                return value.get("value", default)
            return value
        return default

    def _get_numeric_fact_value(self, facts: dict, path: str, default: float = 0.0) -> float:
        """Get fact value as a number, with safe conversion."""
        value = self._get_fact_value(facts, path, default)
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    async def _get_approved_facts(self, project_id: UUID) -> list[ExtractedFact]:
        """Get approved facts for a project."""
        fact_service = FactService(self.session)
        return await fact_service.get_active_approved_facts(project_id)

    async def _get_project(self, project_id: UUID) -> Project | None:
        """Get project metadata for cohort inference."""
        result = await self.session.execute(
            select(Project).where(Project.id == str(project_id))
        )
        return result.scalar_one_or_none()

    def package_to_read_schema(
        self, package: ExternalAdvisoryPackage
    ) -> ExternalAdvisoryPackageRead:
        """Convert model to read schema."""
        return ExternalAdvisoryPackageRead(
            id=UUID(package.id),
            project_id=UUID(package.project_id),
            version=package.version,
            title=package.title,
            generated_for=package.generated_for,
            playbook_version=package.playbook_version,
            bfms_version=package.bfms_version,
            is_complete=package.is_complete,
            generation_started_at=package.generation_started_at,
            generation_completed_at=package.generation_completed_at,
            cover_page=package.cover_page,
            executive_summary=package.executive_summary,
            deal_overview=package.deal_overview,
            financial_tables=package.financial_tables,
            slb_brief=package.slb_brief,
            key_assumptions=package.key_assumptions,
            disclaimer=package.disclaimer,
            disclosure_document_id=UUID(package.disclosure_document_id) if package.disclosure_document_id else None,
            disclosure_completeness_score=package.disclosure_completeness_score,
            critical_tbd_count=package.critical_tbd_count,
            high_tbd_count=package.high_tbd_count,
            readiness_score_at_generation=package.readiness_score_at_generation,
            ready_for_distribution=package.ready_for_distribution,
            distribution_issues=package.distribution_issues,
            pdf_storage_path=package.pdf_storage_path,
            docx_storage_path=package.docx_storage_path,
            md_storage_path=package.md_storage_path,
            created_at=package.created_at,
            updated_at=package.updated_at,
        )
