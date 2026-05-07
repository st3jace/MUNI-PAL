"""
Readiness scoring service.

Per spec: ReadinessDimension scoring is DETERMINISTIC (rules-based).
Scores are computed from approved facts against playbook dimensions.

Scoring ranges (0-10 overall):
- 0.0-3.0: Not Yet Viable
- 3.0-5.5: Structurally Viable
- 5.5-7.5: Ready for Selective Engagement
- 7.5-10.0: Ready for Broad Market
"""

import logging
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.models.fact import ExtractedFact
from munipal.core.models.project import Project
from munipal.core.schemas.base import ReadinessDimension, ReviewStatus, CriticalityTier
from munipal.core.schemas.readiness import (
    DimensionScore,
    ReadinessAssessment,
    ReadinessGap,
    ReadinessGapReport,
    DIMENSION_WEIGHTS,
    DIMENSION_NAMES,
)
from munipal.services.fact_service import FactService
from munipal.services.playbook_data import READINESS_CONFIG, SCHEMA_PATHS, SCHEMA_PATH_METADATA

logger = logging.getLogger(__name__)


# Recommendation thresholds
SCORE_THRESHOLDS = {
    "not_yet_viable": (0.0, 3.0),
    "structurally_viable": (3.0, 5.5),
    "ready_for_selective_engagement": (5.5, 7.5),
    "ready_for_broad_market": (7.5, 10.0),
}

RECOMMENDATION_LABELS = {
    "not_yet_viable": "Not Yet Viable",
    "structurally_viable": "Structurally Viable",
    "ready_for_selective_engagement": "Ready for Selective Engagement",
    "ready_for_broad_market": "Ready for Broad Market",
}

RECOMMENDATION_RATIONALES = {
    "not_yet_viable": (
        "The project lacks fundamental evidence required for bond structuring. "
        "Key areas like issuer authority, technology definition, or financial structure "
        "need substantial documentation before engaging advisors."
    ),
    "structurally_viable": (
        "The project has a viable foundation but needs additional evidence in key areas. "
        "Consider gathering more documentation on revenue model, debt structure, and key risk mitigants "
        "before broader market engagement."
    ),
    "ready_for_selective_engagement": (
        "The project has sufficient documentation for selective advisor discussions. "
        "Targeted gaps remain but the overall structure is clear enough for "
        "preliminary term sheet discussions with select underwriters."
    ),
    "ready_for_broad_market": (
        "The project is substantially documented and ready for broad market engagement. "
        "The evidence base supports formal RFP process and competitive underwriter selection. "
        "Minor gaps can be addressed during document drafting phase."
    ),
}


SECTOR_READINESS_PROFILES = {
    "healthcare_hospital": {
        "dimension_names": {
            ReadinessDimension.ISSUER_AUTHORITY: "Issuer Authority & Tax-Exempt Eligibility",
            ReadinessDimension.PROJECT_TECH: "Hospital / Healthcare Project Scope",
            ReadinessDimension.REVENUE_FEEDSTOCK: "Audited Financials & Demand",
            ReadinessDimension.CAB_FINANCIAL: "Revenue Pledge & Coverage",
            ReadinessDimension.RISK_SECURITY_SLB: "Healthcare Risk & Disclosure",
            ReadinessDimension.SLB_VERIFICATION: "Disclosure & Advisor Readiness",
        },
        "dimensions": {
            ReadinessDimension.ISSUER_AUTHORITY: {
                "contributing_paths": ["governance.inducement", "bond_counsel.tax_certificate"],
                "critical_paths": ["governance.inducement", "bond_counsel.tax_certificate"],
            },
            ReadinessDimension.PROJECT_TECH: {
                "contributing_paths": ["project.name", "project.location", "capital.project-cost"],
                "critical_paths": ["project.name", "capital.project-cost"],
            },
            ReadinessDimension.REVENUE_FEEDSTOCK: {
                "contributing_paths": ["financials.audited-statements", "market.demand"],
                "critical_paths": ["financials.audited-statements", "market.demand"],
            },
            ReadinessDimension.CAB_FINANCIAL: {
                "contributing_paths": ["security.revenue.pledge", "debt_service.reserve_policy"],
                "critical_paths": ["security.revenue.pledge", "debt_service.reserve_policy"],
            },
            ReadinessDimension.RISK_SECURITY_SLB: {
                "contributing_paths": ["disclosure.risk-factors"],
                "critical_paths": ["disclosure.risk-factors"],
            },
            ReadinessDimension.SLB_VERIFICATION: {
                "contributing_paths": ["rating.preliminary_indication"],
                "critical_paths": ["rating.preliminary_indication"],
            },
        },
        "path_labels": {
            "bond_counsel.tax_certificate": "Bond counsel tax certificate",
            "rating.preliminary_indication": "Preliminary rating indication",
            "debt_service.reserve_policy": "Debt service reserve policy",
            "financials.audited-statements": "Audited financial statements",
            "market.demand": "Service-area demand evidence",
            "security.revenue.pledge": "Healthcare revenue pledge",
            "disclosure.risk-factors": "Healthcare disclosure risk factors",
            "capital.project-cost": "Healthcare capital project cost",
        },
    },
    "housing_affordable_multifamily": {
        "dimension_names": {
            ReadinessDimension.ISSUER_AUTHORITY: "Issuer & Inducement Readiness",
            ReadinessDimension.PROJECT_TECH: "Affordable Housing Project Scope",
            ReadinessDimension.REVENUE_FEEDSTOCK: "Affordability & Subsidy Stack",
            ReadinessDimension.CAB_FINANCIAL: "Housing Finance Readiness",
            ReadinessDimension.RISK_SECURITY_SLB: "Site Control & Diligence",
            ReadinessDimension.SLB_VERIFICATION: "Housing Disclosure & Advisor Readiness",
        },
        "dimensions": {
            ReadinessDimension.ISSUER_AUTHORITY: {
                "contributing_paths": ["governance.inducement", "bond_counsel.inducement_resolution"],
                "critical_paths": ["governance.inducement", "bond_counsel.inducement_resolution"],
            },
            ReadinessDimension.PROJECT_TECH: {
                "contributing_paths": ["project.name", "project.location", "capital.project-cost", "housing.units.total"],
                "critical_paths": ["project.name", "capital.project-cost", "housing.units.total"],
            },
            ReadinessDimension.REVENUE_FEEDSTOCK: {
                "contributing_paths": ["housing.affordability.restrictions", "housing.tax_credit_allocation"],
                "critical_paths": ["housing.affordability.restrictions", "housing.tax_credit_allocation"],
            },
            ReadinessDimension.CAB_FINANCIAL: {
                "contributing_paths": ["housing.appraisal"],
                "critical_paths": ["housing.appraisal"],
            },
            ReadinessDimension.RISK_SECURITY_SLB: {
                "contributing_paths": ["project.location.sitecontrol", "environmental.phase_one"],
                "critical_paths": ["project.location.sitecontrol", "environmental.phase_one"],
            },
            ReadinessDimension.SLB_VERIFICATION: {
                "contributing_paths": ["bond_counsel.inducement_resolution"],
                "critical_paths": ["bond_counsel.inducement_resolution"],
            },
        },
        "path_labels": {
            "bond_counsel.inducement_resolution": "Bond counsel inducement resolution",
            "housing.appraisal": "Housing appraisal",
            "housing.tax_credit_allocation": "Tax credit allocation",
            "environmental.phase_one": "Phase One environmental report",
            "housing.units.total": "Total affordable housing units",
            "housing.affordability.restrictions": "Affordability restrictions",
            "project.location.sitecontrol": "Site control evidence",
            "capital.project-cost": "Housing development budget",
        },
    },
}


class ReadinessService:
    """
    Service for computing readiness scores.

    Scores are deterministic based on:
    1. Coverage of schema paths per dimension
    2. Confidence scores of approved facts
    3. Critical vs material path weighting
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self._schema_path_config = {p["path"]: p for p in SCHEMA_PATHS}
        self._readiness_config = READINESS_CONFIG["dimensions"]
        self._sector_profile = None


    async def _get_sector_profile(self, project_id: UUID) -> dict | None:
        """Return sector-specific readiness profile for the project, if configured."""
        result = await self.session.execute(select(Project).where(Project.id == str(project_id)))
        project = result.scalar_one_or_none()
        if project is None:
            return None
        return (
            SECTOR_READINESS_PROFILES.get(project.subsector or "")
            or SECTOR_READINESS_PROFILES.get(project.sector or "")
        )

    def _dimension_config(self, dimension: ReadinessDimension) -> dict | None:
        if getattr(self, "_sector_profile", None):
            return self._sector_profile["dimensions"].get(dimension)
        return self._readiness_config.get(dimension.value)

    def _dimension_name(self, dimension: ReadinessDimension) -> str:
        if getattr(self, "_sector_profile", None):
            return self._sector_profile["dimension_names"].get(dimension, DIMENSION_NAMES[dimension])
        return DIMENSION_NAMES[dimension]

    def _path_label(self, path: str) -> str:
        if getattr(self, "_sector_profile", None):
            label = self._sector_profile.get("path_labels", {}).get(path)
            if label:
                return label
        return self._schema_path_config.get(path, {}).get("display_name", path)

    def _path_config(self, path: str) -> dict:
        config = dict(self._schema_path_config.get(path, {}))
        config["display_name"] = self._path_label(path)
        return config

    # -------------------------------------------------------------------------
    # Score Computation
    # -------------------------------------------------------------------------

    async def compute_assessment(self, project_id: UUID) -> ReadinessAssessment:
        """
        Compute full readiness assessment for a project.

        Args:
            project_id: Project UUID

        Returns:
            ReadinessAssessment with all dimension scores
        """
        self._sector_profile = await self._get_sector_profile(project_id)

        # Get all approved facts for project
        approved_facts = await self._get_approved_facts(project_id)
        facts_by_path = FactService.select_preferred_facts_by_path(approved_facts)

        # Get counts for summary
        pending_count = await self._count_pending_facts(project_id)

        # Compute each dimension
        dimension_scores = {}
        total_weighted_score = 0.0
        critical_gaps = 0
        material_gaps = 0

        for dim in ReadinessDimension:
            dim_score = self._compute_dimension_score(dim, facts_by_path)
            dimension_scores[dim] = dim_score
            total_weighted_score += dim_score.weighted_contribution

            # Track gaps
            critical_gaps += dim_score.critical_paths_total - dim_score.critical_paths_covered
            material_gaps += dim_score.material_paths_total - dim_score.material_paths_covered

        # Scale to 0-10
        overall_score = total_weighted_score * 2  # Each dimension max is 5, weighted sum max is 5

        # Determine recommendation
        recommendation, rationale = self._get_recommendation(overall_score)

        return ReadinessAssessment(
            project_id=str(project_id),
            dimensions=dimension_scores,
            overall_score=overall_score,
            recommendation=recommendation,
            recommendation_rationale=rationale,
            total_facts_approved=len(facts_by_path),
            total_facts_pending=pending_count,
            critical_gaps_count=critical_gaps,
            material_gaps_count=material_gaps,
        )

    def _compute_dimension_score(
        self,
        dimension: ReadinessDimension,
        facts_by_path: dict[str, ExtractedFact],
    ) -> DimensionScore:
        """
        Compute score for a single dimension.

        Scoring algorithm:
        1. Get contributing paths for dimension
        2. Check which paths have approved facts
        3. Weight critical paths more heavily
        4. Apply confidence score modifiers
        5. Scale to 0-5
        """
        dim_key = dimension.value
        if self._dimension_config(dimension) is None:
            # Handle missing config
            return DimensionScore(
                dimension=dimension,
                dimension_name=self._dimension_name(dimension),
                score=0.0,
                weight=DIMENSION_WEIGHTS[dimension],
                weighted_contribution=0.0,
                explanation="Dimension configuration not found",
            )

        config = self._dimension_config(dimension)
        contributing_paths = config.get("contributing_paths", [])
        critical_paths = set(config.get("critical_paths", []))

        if not contributing_paths:
            return DimensionScore(
                dimension=dimension,
                dimension_name=self._dimension_name(dimension),
                score=5.0,  # Full score if no paths required
                weight=DIMENSION_WEIGHTS[dimension],
                weighted_contribution=5.0 * DIMENSION_WEIGHTS[dimension],
                explanation="No contributing paths defined",
            )

        # Analyze coverage
        critical_covered = 0
        critical_total = len(critical_paths)
        material_covered = 0
        material_total = 0
        total_score_points = 0.0
        max_score_points = 0.0

        for path in contributing_paths:
            is_critical = path in critical_paths
            path_weight = 2.0 if is_critical else 1.0

            max_score_points += path_weight

            if not is_critical:
                material_total += 1

            if path in facts_by_path:
                fact = facts_by_path[path]

                # Apply confidence modifier (0.5-1.0 based on confidence)
                confidence_modifier = 0.5 + (fact.confidence_score * 0.5)
                total_score_points += path_weight * confidence_modifier

                if is_critical:
                    critical_covered += 1
                else:
                    material_covered += 1

        # Calculate raw score (0-5)
        if max_score_points > 0:
            raw_score = (total_score_points / max_score_points) * 5.0
        else:
            raw_score = 5.0

        # Apply critical penalty: if critical paths missing, cap score
        if critical_total > 0 and critical_covered < critical_total:
            critical_penalty = (critical_total - critical_covered) / critical_total
            raw_score = min(raw_score, 3.0 * (1 - critical_penalty))

        score = round(raw_score, 2)
        weight = DIMENSION_WEIGHTS[dimension]
        weighted = score * weight

        # Generate explanation
        explanation = self._generate_dimension_explanation(
            dimension=dimension,
            score=score,
            critical_covered=critical_covered,
            critical_total=critical_total,
            material_covered=material_covered,
            material_total=material_total,
        )

        # Generate improvement suggestions
        suggestions = self._generate_improvement_suggestions(
            dimension=dimension,
            contributing_paths=contributing_paths,
            critical_paths=critical_paths,
            facts_by_path=facts_by_path,
        )

        return DimensionScore(
            dimension=dimension,
            dimension_name=self._dimension_name(dimension),
            score=score,
            weight=weight,
            weighted_contribution=weighted,
            critical_paths_covered=critical_covered,
            critical_paths_total=critical_total,
            material_paths_covered=material_covered,
            material_paths_total=material_total,
            explanation=explanation,
            improvement_suggestions=suggestions,
        )

    def _generate_dimension_explanation(
        self,
        dimension: ReadinessDimension,
        score: float,
        critical_covered: int,
        critical_total: int,
        material_covered: int,
        material_total: int,
    ) -> str:
        """Generate why-it-matters narrative for dimension."""
        dim_name = self._dimension_name(dimension)

        if score >= 4.5:
            return (
                f"{dim_name} is substantially documented. "
                f"All critical requirements met with strong evidence base."
            )
        elif score >= 3.5:
            return (
                f"{dim_name} has good coverage ({critical_covered}/{critical_total} critical). "
                f"Some supporting evidence would strengthen the position."
            )
        elif score >= 2.0:
            return (
                f"{dim_name} has partial coverage. "
                f"{critical_total - critical_covered} critical items and "
                f"{material_total - material_covered} material items need documentation."
            )
        else:
            return (
                f"{dim_name} needs substantial documentation. "
                f"Only {critical_covered}/{critical_total} critical items covered. "
                f"This dimension is blocking deal progression."
            )

    def _generate_improvement_suggestions(
        self,
        dimension: ReadinessDimension,
        contributing_paths: list[str],
        critical_paths: set[str],
        facts_by_path: dict[str, ExtractedFact],
    ) -> list[str]:
        """Generate specific improvement suggestions."""
        suggestions = []

        # Find missing critical paths
        missing_critical = sorted(p for p in critical_paths if p not in facts_by_path)
        if missing_critical:
            path_names = [
                self._path_label(p)
                for p in missing_critical[:3]  # Limit to top 3
            ]
            suggestions.append(
                f"Upload documents containing: {', '.join(path_names)}"
            )

        # Find low confidence facts
        low_conf = [
            p for p in contributing_paths
            if p in facts_by_path and facts_by_path[p].confidence_score < 0.7
        ]
        if low_conf:
            suggestions.append(
                f"Review and verify {len(low_conf)} facts with low confidence scores"
            )

        # Find missing material paths
        material_paths = set(contributing_paths) - critical_paths
        missing_material = sorted(p for p in material_paths if p not in facts_by_path)
        if missing_material and len(suggestions) < 3:
            suggestions.append(
                f"Gather evidence for {len(missing_material)} additional supporting items"
            )

        return suggestions

    def _get_recommendation(self, overall_score: float) -> tuple[str, str]:
        """Get recommendation label and rationale based on score."""
        for level, (min_score, max_score) in SCORE_THRESHOLDS.items():
            if min_score <= overall_score < max_score:
                return RECOMMENDATION_LABELS[level], RECOMMENDATION_RATIONALES[level]

        # Handle edge case of exactly 10.0
        if overall_score >= 10.0:
            return (
                RECOMMENDATION_LABELS["ready_for_broad_market"],
                RECOMMENDATION_RATIONALES["ready_for_broad_market"],
            )

        return RECOMMENDATION_LABELS["not_yet_viable"], RECOMMENDATION_RATIONALES["not_yet_viable"]

    # -------------------------------------------------------------------------
    # Gap Analysis
    # -------------------------------------------------------------------------

    async def compute_gaps(self, project_id: UUID) -> ReadinessGapReport:
        """
        Compute prioritized gap report.

        Returns gaps organized by criticality with improvement suggestions.
        """
        self._sector_profile = await self._get_sector_profile(project_id)
        approved_facts = await self._get_approved_facts(project_id)
        facts_by_path = FactService.select_preferred_facts_by_path(approved_facts)

        assessment = await self.compute_assessment(project_id)

        critical_gaps = []
        material_gaps = []
        secondary_gaps = []

        # Analyze each dimension for gaps
        for dim in ReadinessDimension:
            config = self._dimension_config(dim)
            if config is None:
                continue

            contributing_paths = config.get("contributing_paths", [])
            critical_paths = set(config.get("critical_paths", []))

            for path in contributing_paths:
                if path in facts_by_path:
                    continue  # Not a gap

                # Determine criticality
                path_config = self._path_config(path)
                path_criticality = path_config.get("criticality", "secondary")

                # Override with dimension critical designation
                if path in critical_paths:
                    path_criticality = "critical"

                # Get short_description from metadata
                short_desc = self._path_label(path)

                gap = ReadinessGap(
                    schema_path=path,
                    dimension=dim,
                    criticality=path_criticality,
                    description=self._path_label(path),
                    short_description=short_desc,
                    impact=self._get_gap_impact(path_criticality, dim),
                    suggested_evidence=self._suggest_evidence(path, path_config),
                )

                if path_criticality == "critical":
                    critical_gaps.append(gap)
                elif path_criticality == "material":
                    material_gaps.append(gap)
                else:
                    secondary_gaps.append(gap)

        # Generate priority actions
        priority_actions = self._generate_priority_actions(
            critical_gaps, material_gaps, assessment.overall_score
        )

        return ReadinessGapReport(
            project_id=str(project_id),
            overall_score=assessment.overall_score,
            critical_gaps=critical_gaps,
            material_gaps=material_gaps,
            secondary_gaps=secondary_gaps,
            priority_actions=priority_actions,
        )

    def _get_gap_impact(self, criticality: str, dimension: ReadinessDimension) -> str:
        """Generate impact statement for a gap."""
        dim_name = self._dimension_name(dimension)

        if criticality == "critical":
            return f"Blocks {dim_name} from achieving full readiness. Required for deal progression."
        elif criticality == "material":
            return f"Significantly affects {dim_name} scoring. Important for advisor confidence."
        else:
            return f"Contributes to {dim_name} completeness. Nice to have for comprehensive package."

    def _suggest_evidence(self, path: str, path_config: dict) -> str:
        """Suggest what evidence would fill a gap."""
        value_type = path_config.get("value_type", "string")
        display_name = self._path_label(path)

        suggestions = {
            "currency": f"Financial document showing {display_name} (dollar amount)",
            "number": f"Technical or financial document specifying {display_name}",
            "percentage": f"Document showing {display_name} as percentage",
            "date": f"Legal or financial document with {display_name} date",
            "enum": f"Document confirming {display_name} status/type",
            "boolean": f"Document confirming whether {display_name} applies",
            "array": f"Document listing {display_name} items",
            "object": f"Detailed documentation of {display_name} structure",
        }

        return suggestions.get(value_type, f"Document containing {display_name}")

    def _generate_priority_actions(
        self,
        critical_gaps: list[ReadinessGap],
        material_gaps: list[ReadinessGap],
        overall_score: float,
    ) -> list[str]:
        """Generate top priority actions."""
        actions = []

        # Critical gaps first
        if critical_gaps:
            critical_by_dim = {}
            for gap in critical_gaps:
                dim_name = self._dimension_name(gap.dimension)
                if dim_name not in critical_by_dim:
                    critical_by_dim[dim_name] = []
                critical_by_dim[dim_name].append(gap.description)

            for dim_name, gaps in list(critical_by_dim.items())[:2]:
                actions.append(
                    f"Upload documents for {dim_name}: {', '.join(gaps[:3])}"
                )

        # Material gaps if room
        if len(actions) < 3 and material_gaps:
            material_count = len(material_gaps)
            actions.append(
                f"Gather evidence for {material_count} material items to improve scoring"
            )

        # Score-based recommendations
        if overall_score < 3.0:
            actions.append(
                "Focus on critical path documentation before engaging advisors"
            )
        elif overall_score < 5.5:
            actions.append(
                "Consider preliminary advisor discussions while gathering remaining evidence"
            )
        elif overall_score < 7.5:
            actions.append(
                "Ready for selective underwriter outreach; finalize remaining items in parallel"
            )

        return actions[:5]  # Limit to 5

    # -------------------------------------------------------------------------
    # Database Helpers
    # -------------------------------------------------------------------------

    async def _get_approved_facts(self, project_id: UUID) -> list[ExtractedFact]:
        """Get all approved facts for a project."""
        fact_service = FactService(self.session)
        return await fact_service.get_active_approved_facts(project_id)

    async def _count_pending_facts(self, project_id: UUID) -> int:
        """Count pending facts for a project."""
        result = await self.session.execute(
            select(func.count(ExtractedFact.id)).where(
                and_(
                    ExtractedFact.project_id == str(project_id),
                    ExtractedFact.review_status == ReviewStatus.PENDING.value,
                    ExtractedFact.lifecycle_state != "archived",
                )
            )
        )
        return result.scalar() or 0

    # -------------------------------------------------------------------------
    # Single Dimension Detail
    # -------------------------------------------------------------------------

    async def get_dimension_detail(
        self,
        project_id: UUID,
        dimension: ReadinessDimension,
    ) -> dict:
        """
        Get detailed breakdown for a single dimension.

        Returns contributing facts and specific gap information.
        """
        approved_facts = await self._get_approved_facts(project_id)
        facts_by_path = FactService.select_preferred_facts_by_path(approved_facts)

        dim_score = self._compute_dimension_score(dimension, facts_by_path)

        # Get contributing facts
        dim_key = dimension.value
        config = self._readiness_config.get(dim_key, {})
        contributing_paths = config.get("contributing_paths", [])
        critical_paths = set(config.get("critical_paths", []))

        contributing_facts = []
        missing_paths = []

        for path in contributing_paths:
            path_config = self._schema_path_config.get(path, {})
            is_critical = path in critical_paths

            if path in facts_by_path:
                fact = facts_by_path[path]
                contributing_facts.append({
                    "schema_path": path,
                    "display_name": path_config.get("display_name", path),
                    "value": fact.value,
                    "confidence": fact.confidence_score,
                    "is_critical": is_critical,
                    "fact_id": fact.id,
                })
            else:
                missing_paths.append({
                    "schema_path": path,
                    "display_name": path_config.get("display_name", path),
                    "is_critical": is_critical,
                    "suggested_evidence": self._suggest_evidence(path, path_config),
                })

        return {
            "dimension": dimension.value,
            "dimension_name": DIMENSION_NAMES[dimension],
            "score": dim_score.score,
            "max_score": 5.0,
            "weight": dim_score.weight,
            "weighted_contribution": dim_score.weighted_contribution,
            "critical_coverage": f"{dim_score.critical_paths_covered}/{dim_score.critical_paths_total}",
            "material_coverage": f"{dim_score.material_paths_covered}/{dim_score.material_paths_total}",
            "explanation": dim_score.explanation,
            "improvement_suggestions": dim_score.improvement_suggestions,
            "contributing_facts": contributing_facts,
            "missing_paths": missing_paths,
        }
