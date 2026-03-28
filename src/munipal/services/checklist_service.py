"""
Checklist management service.

Per spec: ChecklistItem status is COMPUTED from linked facts.
Status follows deterministic rules, not learned behavior.

Phases P1-P6 represent bond diligence progression.
"""

import logging
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.models.fact import ExtractedFact, EvidenceLink
from munipal.core.schemas.base import (
    ChecklistPhase,
    ChecklistStatus,
    CriticalityTier,
    ReviewStatus,
)
from munipal.core.schemas.checklist import (
    ChecklistItemDefinition,
    ChecklistItemStatus,
    ChecklistPhaseSummary,
)
from munipal.services.fact_service import FactService
from munipal.services.playbook_data import CHECKLIST_ITEMS, SCHEMA_PATHS

logger = logging.getLogger(__name__)


# Phase display names
PHASE_NAMES = {
    ChecklistPhase.P1: "Issuer Authority & Deal Formation",
    ChecklistPhase.P2: "Project & Technology Definition",
    ChecklistPhase.P3: "Financial Structure & Revenue Model",
    ChecklistPhase.P4: "Risk, Security & Disclosure",
    ChecklistPhase.P5: "SLB Architecture & Final Modeling",
    ChecklistPhase.P6: "Advisor Engagement & Execution",
}


class ChecklistService:
    """
    Service for checklist management.

    Computes checklist item status from linked facts and provides
    gap analysis for identifying missing evidence.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self._schema_path_config = {p["path"]: p for p in SCHEMA_PATHS}

    # -------------------------------------------------------------------------
    # Checklist Item Definitions
    # -------------------------------------------------------------------------

    def get_item_definitions(
        self,
        phase: ChecklistPhase | None = None,
    ) -> list[ChecklistItemDefinition]:
        """
        Get checklist item definitions from playbook.

        Args:
            phase: Optional phase filter

        Returns:
            List of ChecklistItemDefinition
        """
        items = []
        for item_data in CHECKLIST_ITEMS:
            if phase and item_data["phase"] != phase.value:
                continue

            items.append(
                ChecklistItemDefinition(
                    item_code=item_data["item_code"],
                    phase=ChecklistPhase(item_data["phase"]),
                    title=item_data["title"],
                    description=item_data["description"],
                    required_schema_paths=item_data["required_schema_paths"],
                    optional_schema_paths=item_data.get("optional_schema_paths", []),
                    criticality=CriticalityTier(item_data["criticality"]),
                    blocks_phase_completion=item_data["blocks_phase_completion"],
                )
            )

        return items

    def get_item_definition(self, item_code: str) -> ChecklistItemDefinition | None:
        """
        Get a single checklist item definition by code.

        Args:
            item_code: Item code (e.g., 'P1.1')

        Returns:
            ChecklistItemDefinition or None
        """
        for item_data in CHECKLIST_ITEMS:
            if item_data["item_code"] == item_code:
                return ChecklistItemDefinition(
                    item_code=item_data["item_code"],
                    phase=ChecklistPhase(item_data["phase"]),
                    title=item_data["title"],
                    description=item_data["description"],
                    required_schema_paths=item_data["required_schema_paths"],
                    optional_schema_paths=item_data.get("optional_schema_paths", []),
                    criticality=CriticalityTier(item_data["criticality"]),
                    blocks_phase_completion=item_data["blocks_phase_completion"],
                )
        return None

    # -------------------------------------------------------------------------
    # Status Computation
    # -------------------------------------------------------------------------

    async def compute_item_status(
        self,
        project_id: UUID,
        item_code: str,
    ) -> ChecklistItemStatus | None:
        """
        Compute status for a checklist item based on linked facts.

        Per spec: Status is deterministic based on rules:
        - NOT_STARTED: No approved facts for required paths
        - IN_PROGRESS: Some required paths covered
        - BLOCKED: Critical path missing or low confidence
        - READY: All required paths have approved facts

        Args:
            project_id: Project UUID
            item_code: Checklist item code

        Returns:
            ChecklistItemStatus or None if item not found
        """
        definition = self.get_item_definition(item_code)
        if not definition:
            return None

        # Get approved facts for project
        facts_by_path = await self._get_approved_facts_by_path(
            project_id, definition.required_schema_paths + definition.optional_schema_paths
        )

        # Analyze coverage
        required_paths = set(definition.required_schema_paths)
        covered_paths = set()
        missing_paths = []
        low_confidence_paths = []
        linked_fact_ids = []

        for path in required_paths:
            if path in facts_by_path:
                fact = facts_by_path[path]
                linked_fact_ids.append(UUID(fact.id))

                # Check confidence threshold
                min_confidence = self._get_min_confidence(path)
                if fact.confidence_score < min_confidence:
                    low_confidence_paths.append(path)
                else:
                    covered_paths.add(path)
            else:
                missing_paths.append(path)

        # Calculate coverage
        required_count = len(required_paths)
        covered_count = len(covered_paths)
        coverage_pct = (covered_count / required_count * 100) if required_count > 0 else 100.0

        # Determine status
        status, status_reason = self._determine_status(
            definition=definition,
            covered_paths=covered_paths,
            missing_paths=missing_paths,
            low_confidence_paths=low_confidence_paths,
        )

        return ChecklistItemStatus(
            item_code=item_code,
            phase=definition.phase,
            title=definition.title,
            status=status,
            status_reason=status_reason,
            required_paths_count=required_count,
            covered_paths_count=covered_count,
            coverage_percentage=coverage_pct,
            linked_fact_ids=linked_fact_ids,
            missing_paths=missing_paths,
            low_confidence_paths=low_confidence_paths,
        )

    def _determine_status(
        self,
        definition: ChecklistItemDefinition,
        covered_paths: set[str],
        missing_paths: list[str],
        low_confidence_paths: list[str],
    ) -> tuple[ChecklistStatus, str]:
        """
        Determine checklist status based on coverage analysis.

        Returns:
            Tuple of (status, human-readable reason)
        """
        required_paths = set(definition.required_schema_paths)

        # Check for critical blocking issues
        critical_missing = [
            p for p in missing_paths
            if self._is_critical_path(p)
        ]
        critical_low_conf = [
            p for p in low_confidence_paths
            if self._is_critical_path(p)
        ]

        if critical_missing or critical_low_conf:
            issues = []
            if critical_missing:
                issues.append(f"Missing critical: {', '.join(critical_missing)}")
            if critical_low_conf:
                issues.append(f"Low confidence on critical: {', '.join(critical_low_conf)}")
            return ChecklistStatus.BLOCKED, "; ".join(issues)

        # No required paths = ready by default
        if not required_paths:
            return ChecklistStatus.READY, "No required paths defined"

        # Check coverage
        if not covered_paths:
            return ChecklistStatus.NOT_STARTED, "No approved facts for required paths"

        if covered_paths == required_paths:
            if low_confidence_paths:
                return (
                    ChecklistStatus.IN_PROGRESS,
                    f"All paths covered but {len(low_confidence_paths)} have low confidence"
                )
            return ChecklistStatus.READY, "All required paths have approved facts"

        coverage_pct = len(covered_paths) / len(required_paths) * 100
        return (
            ChecklistStatus.IN_PROGRESS,
            f"{len(covered_paths)}/{len(required_paths)} required paths covered ({coverage_pct:.0f}%)"
        )

    async def _get_approved_facts_by_path(
        self,
        project_id: UUID,
        schema_paths: list[str],
    ) -> dict[str, ExtractedFact]:
        """
        Get approved facts indexed by schema path.

        Returns preferred canonical-first fact for each path.
        """
        if not schema_paths:
            return {}
        fact_service = FactService(self.session)
        return await fact_service.get_active_approved_facts_by_path(
            project_id=project_id,
            schema_paths=schema_paths,
        )

    def _get_min_confidence(self, schema_path: str) -> float:
        """Get minimum confidence threshold for a schema path."""
        if schema_path in self._schema_path_config:
            return self._schema_path_config[schema_path].get("min_confidence", 0.70)
        return 0.70

    def _is_critical_path(self, schema_path: str) -> bool:
        """Check if schema path is critical tier."""
        if schema_path in self._schema_path_config:
            return self._schema_path_config[schema_path].get("criticality") == "critical"
        return False

    # -------------------------------------------------------------------------
    # Listing and Summary
    # -------------------------------------------------------------------------

    async def list_items_with_status(
        self,
        project_id: UUID,
        phase: ChecklistPhase | None = None,
        status_filter: ChecklistStatus | None = None,
    ) -> list[ChecklistItemStatus]:
        """
        List all checklist items with computed status.

        Args:
            project_id: Project UUID
            phase: Optional phase filter
            status_filter: Optional status filter

        Returns:
            List of ChecklistItemStatus
        """
        definitions = self.get_item_definitions(phase)
        statuses = []

        for definition in definitions:
            item_status = await self.compute_item_status(project_id, definition.item_code)
            if item_status:
                if status_filter and item_status.status != status_filter:
                    continue
                statuses.append(item_status)

        return statuses

    async def get_phase_summary(
        self,
        project_id: UUID,
        phase: ChecklistPhase,
    ) -> ChecklistPhaseSummary:
        """
        Get summary of checklist completion for a phase.

        Args:
            project_id: Project UUID
            phase: Phase to summarize

        Returns:
            ChecklistPhaseSummary
        """
        items = await self.list_items_with_status(project_id, phase)

        total = len(items)
        ready = sum(1 for i in items if i.status == ChecklistStatus.READY)
        in_progress = sum(1 for i in items if i.status == ChecklistStatus.IN_PROGRESS)
        blocked = sum(1 for i in items if i.status == ChecklistStatus.BLOCKED)
        not_started = sum(1 for i in items if i.status == ChecklistStatus.NOT_STARTED)

        completion_pct = (ready / total * 100) if total > 0 else 0.0

        # Check if blocking items are all ready
        definitions = self.get_item_definitions(phase)
        blocking_codes = [d.item_code for d in definitions if d.blocks_phase_completion]
        blocking_statuses = [i for i in items if i.item_code in blocking_codes]
        can_proceed = all(i.status == ChecklistStatus.READY for i in blocking_statuses)

        return ChecklistPhaseSummary(
            phase=phase,
            phase_name=PHASE_NAMES[phase],
            total_items=total,
            ready_count=ready,
            in_progress_count=in_progress,
            blocked_count=blocked,
            not_started_count=not_started,
            completion_percentage=completion_pct,
            can_proceed_to_next=can_proceed,
        )

    async def get_all_phases_summary(
        self,
        project_id: UUID,
    ) -> dict[str, ChecklistPhaseSummary]:
        """
        Get summary for all phases.

        Args:
            project_id: Project UUID

        Returns:
            Dict mapping phase to summary
        """
        summaries = {}
        for phase in ChecklistPhase:
            summaries[phase.value] = await self.get_phase_summary(project_id, phase)
        return summaries

    # -------------------------------------------------------------------------
    # Gap Analysis
    # -------------------------------------------------------------------------

    async def get_item_gaps(
        self,
        project_id: UUID,
        item_code: str,
    ) -> dict:
        """
        Get detailed gap analysis for a checklist item.

        Returns missing paths and paths with low confidence facts.
        """
        status = await self.compute_item_status(project_id, item_code)
        if not status:
            return {"error": f"Item {item_code} not found"}

        definition = self.get_item_definition(item_code)

        return {
            "item_code": item_code,
            "title": definition.title,
            "status": status.status if isinstance(status.status, str) else status.status.value,
            "coverage_percentage": status.coverage_percentage,
            "missing_paths": [
                {
                    "path": p,
                    "display_name": self._schema_path_config.get(p, {}).get("display_name", p),
                    "criticality": self._schema_path_config.get(p, {}).get("criticality", "secondary"),
                }
                for p in status.missing_paths
            ],
            "low_confidence_paths": [
                {
                    "path": p,
                    "display_name": self._schema_path_config.get(p, {}).get("display_name", p),
                    "required_confidence": self._get_min_confidence(p),
                }
                for p in status.low_confidence_paths
            ],
            "recommendations": self._generate_recommendations(status),
        }

    def _generate_recommendations(self, status: ChecklistItemStatus) -> list[str]:
        """Generate recommendations for closing gaps."""
        recommendations = []

        if status.missing_paths:
            critical_missing = [p for p in status.missing_paths if self._is_critical_path(p)]
            if critical_missing:
                recommendations.append(
                    f"Upload documents containing information for critical paths: {', '.join(critical_missing)}"
                )

            non_critical = [p for p in status.missing_paths if not self._is_critical_path(p)]
            if non_critical:
                recommendations.append(
                    f"Gather evidence for remaining paths: {', '.join(non_critical)}"
                )

        if status.low_confidence_paths:
            recommendations.append(
                f"Review and verify facts with low confidence: {', '.join(status.low_confidence_paths)}"
            )

        if status.status == ChecklistStatus.READY:
            recommendations.append("Item is complete - no action needed")

        return recommendations

    async def get_project_gaps(
        self,
        project_id: UUID,
    ) -> dict:
        """
        Get comprehensive gap analysis for entire project.

        Returns gaps organized by phase and criticality.
        """
        all_gaps = {
            "by_phase": {},
            "critical_missing": [],
            "total_missing_paths": 0,
            "total_low_confidence": 0,
        }

        for phase in ChecklistPhase:
            phase_items = await self.list_items_with_status(project_id, phase)
            phase_gaps = []

            for item in phase_items:
                if item.missing_paths or item.low_confidence_paths:
                    phase_gaps.append({
                        "item_code": item.item_code,
                        "title": item.title,
                        "status": item.status if isinstance(item.status, str) else item.status.value,
                        "missing_count": len(item.missing_paths),
                        "low_confidence_count": len(item.low_confidence_paths),
                    })
                    all_gaps["total_missing_paths"] += len(item.missing_paths)
                    all_gaps["total_low_confidence"] += len(item.low_confidence_paths)

                    # Track critical missing
                    for path in item.missing_paths:
                        if self._is_critical_path(path):
                            all_gaps["critical_missing"].append({
                                "path": path,
                                "item_code": item.item_code,
                                "phase": phase.value,
                            })

            all_gaps["by_phase"][phase.value] = phase_gaps

        return all_gaps

    # -------------------------------------------------------------------------
    # Evidence Linking
    # -------------------------------------------------------------------------

    async def link_fact_to_item(
        self,
        fact_id: UUID,
        item_code: str,
    ) -> bool:
        """
        Create evidence link from fact to checklist item.

        Args:
            fact_id: Fact UUID
            item_code: Checklist item code

        Returns:
            True if link created successfully
        """
        link = EvidenceLink(
            fact_id=str(fact_id),
            link_type="checklist_item",
            target_id=item_code,
            contribution_weight=1.0,
        )
        self.session.add(link)
        await self.session.commit()

        logger.info(f"Linked fact {fact_id} to checklist item {item_code}")
        return True

    async def get_facts_for_item(
        self,
        project_id: UUID,
        item_code: str,
        approved_only: bool = True,
    ) -> list[ExtractedFact]:
        """
        Get all facts relevant to a checklist item.

        Returns facts whose schema paths match the item's required/optional paths.
        """
        definition = self.get_item_definition(item_code)
        if not definition:
            return []

        all_paths = definition.required_schema_paths + definition.optional_schema_paths
        if not all_paths:
            return []

        query = select(ExtractedFact).where(
            and_(
                ExtractedFact.project_id == str(project_id),
                ExtractedFact.schema_path.in_(all_paths),
                ExtractedFact.lifecycle_state != "archived",
            )
        )

        if approved_only:
            query = query.where(
                ExtractedFact.review_status == ReviewStatus.APPROVED.value
            )

        result = await self.session.execute(
            query.order_by(ExtractedFact.schema_path, ExtractedFact.confidence_score.desc())
        )

        return list(result.scalars().all())
