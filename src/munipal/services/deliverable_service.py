"""
Deliverable pack generation service.

Per spec (WP6): Warm Handoff Pack Assembly
- Package everything into professional, neutral advisor-ready deliverable
- Generate all 9 sections per playbook
- Include mandatory disclaimer

Per playbook: "An advisor can review the handoff pack in <15 minutes"
"""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from munipal.core.models.artifact import Artifact, Chunk
from munipal.core.models.deliverable import DeliverablePack
from munipal.core.models.fact import ExtractedFact
from munipal.core.models.project import Project
from munipal.core.schemas.base import CriticalityTier, ChecklistPhase
from munipal.core.schemas.deliverable import DeliverableSection
from munipal.services.checklist_service import ChecklistService
from munipal.services.fact_service import FactService
from munipal.services.readiness_service import ReadinessService
from munipal.services.playbook_data import SCHEMA_PATHS

logger = logging.getLogger(__name__)


# Section definitions per playbook
SECTION_DEFINITIONS = {
    1: {"name": "Cover", "generator": "_generate_cover"},
    2: {"name": "Deal Overview Memo", "generator": "_generate_deal_overview"},
    3: {"name": "Readiness & Gap Report", "generator": "_generate_readiness_report"},
    4: {"name": "Checklist Status", "generator": "_generate_checklist_status"},
    5: {"name": "Evidence Index", "generator": "_generate_evidence_index"},
    6: {"name": "Assumption Register", "generator": "_generate_assumption_register"},
    7: {"name": "Financial Model Outputs", "generator": "_generate_financial_outputs"},
    8: {"name": "SLB KPI Brief", "generator": "_generate_slb_brief"},
    9: {"name": "Disclosure Outline", "generator": "_generate_disclosure_outline"},
}


class DeliverableService:
    """
    Service for generating advisor-ready deliverable packs.

    Aggregates approved facts, checklist status, and readiness scores
    into a structured document bundle.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self._schema_path_config = {p["path"]: p for p in SCHEMA_PATHS}

    # -------------------------------------------------------------------------
    # Pack Management
    # -------------------------------------------------------------------------

    async def create_pack(
        self,
        project_id: UUID,
        title: str,
        generated_for: str,
        include_sections: list[int] | None = None,
        include_appendices: bool = True,
    ) -> DeliverablePack:
        """
        Create a new deliverable pack record.

        Args:
            project_id: Project UUID
            title: Pack title
            generated_for: Intended recipient
            include_sections: Section numbers to include (default all)
            include_appendices: Whether to include appendices

        Returns:
            Created DeliverablePack
        """
        if include_sections is None:
            include_sections = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        pack = DeliverablePack(
            project_id=str(project_id),
            title=title,
            generated_for=generated_for,
            include_sections=include_sections,
            include_appendices=include_appendices,
        )

        self.session.add(pack)
        await self.session.commit()
        await self.session.refresh(pack)

        logger.info(f"Created deliverable pack {pack.id} for project {project_id}")
        return pack

    async def get_pack(self, pack_id: UUID) -> DeliverablePack | None:
        """Get a deliverable pack by ID."""
        result = await self.session.execute(
            select(DeliverablePack)
            .options(selectinload(DeliverablePack.project))
            .where(DeliverablePack.id == str(pack_id))
        )
        return result.scalar_one_or_none()

    async def list_packs(
        self,
        project_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[DeliverablePack]:
        """List deliverable packs for a project."""
        result = await self.session.execute(
            select(DeliverablePack)
            .where(DeliverablePack.project_id == str(project_id))
            .order_by(DeliverablePack.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Pack Generation
    # -------------------------------------------------------------------------

    async def generate_pack(self, pack_id: UUID) -> DeliverablePack:
        """
        Generate all sections for a deliverable pack.

        Args:
            pack_id: Pack UUID

        Returns:
            Updated DeliverablePack with generated sections
        """
        pack = await self.get_pack(pack_id)
        if not pack:
            raise ValueError(f"Pack {pack_id} not found")

        # Mark generation started
        pack.generation_started_at = datetime.now(timezone.utc)
        await self.session.commit()

        project_id = UUID(pack.project_id)

        # Load all required data
        project = await self._get_project(project_id)
        raw_facts = await self._get_approved_facts(project_id)
        facts_by_path = self._index_facts_by_path(raw_facts)
        facts = list(facts_by_path.values())

        # Get checklist and readiness data
        checklist_service = ChecklistService(self.session)
        readiness_service = ReadinessService(self.session)

        readiness = await readiness_service.compute_assessment(project_id)
        checklist_summary = await checklist_service.get_all_phases_summary(project_id)
        gaps = await readiness_service.compute_gaps(project_id)

        # Context for section generators
        context = {
            "project": project,
            "facts": facts,
            "facts_by_path": facts_by_path,
            "readiness": readiness,
            "checklist_summary": checklist_summary,
            "gaps": gaps,
            "generated_for": pack.generated_for,
            "pack_title": pack.title,
        }

        # Generate requested sections
        sections = []
        warnings = []

        for section_num in pack.include_sections:
            if section_num not in SECTION_DEFINITIONS:
                continue

            section_def = SECTION_DEFINITIONS[section_num]
            generator_name = section_def["generator"]
            generator = getattr(self, generator_name, None)

            if generator:
                try:
                    section = await generator(context)
                    section.section_number = section_num
                    section.section_name = section_def["name"]
                    sections.append(section.model_dump())
                    warnings.extend(section.warnings)
                except Exception as e:
                    logger.error(f"Failed to generate section {section_num}: {e}")
                    sections.append({
                        "section_number": section_num,
                        "section_name": section_def["name"],
                        "content": f"*Error generating section: {str(e)}*",
                        "is_complete": False,
                        "warnings": [f"Generation failed: {str(e)}"],
                    })
                    warnings.append(f"Section {section_num} generation failed")

        # Update pack title with current date on (re)generation
        now = datetime.now(timezone.utc)
        pack.title = f"Advisor Handoff Pack - {now.month}/{now.day}/{now.year}"

        # Update pack with generated content
        pack.sections = sections
        pack.warnings = warnings
        pack.facts_included_count = len(facts)
        pack.readiness_score_at_generation = readiness.overall_score
        pack.is_complete = True
        pack.generation_completed_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(pack)

        logger.info(f"Generated pack {pack_id} with {len(sections)} sections")
        return pack

    # -------------------------------------------------------------------------
    # Section Generators
    # -------------------------------------------------------------------------

    async def _generate_cover(self, ctx: dict) -> DeliverableSection:
        """Generate Section 1: Cover page."""
        project = ctx["project"]
        readiness = ctx["readiness"]

        content = f"""# {ctx['pack_title']}

**Project:** {project.name}

**Prepared For:** {ctx['generated_for']}

**Date:** {datetime.now(timezone.utc).strftime('%B %d, %Y')}

---

## Readiness Summary

**Overall Score:** {readiness.overall_score:.1f} / 10.0

**Recommendation:** {readiness.recommendation}

---

*This document has been prepared by Muni-Pal Bond Facility Management System.*

*All facts and figures are derived from uploaded project documents and are subject to verification by qualified professionals.*
"""

        return DeliverableSection(
            section_number=1,
            section_name="Cover",
            content=content,
            is_complete=True,
            warnings=[],
        )

    async def _generate_deal_overview(self, ctx: dict) -> DeliverableSection:
        """Generate Section 2: Deal Overview Memo."""
        project = ctx["project"]
        facts_by_path = ctx["facts_by_path"]
        warnings = []

        # Extract key facts for deal overview
        def get_fact_value(path: str, default: str = "Not specified") -> str:
            if path in facts_by_path:
                return str(facts_by_path[path].value)
            warnings.append(f"Missing: {path}")
            return default

        issuer = get_fact_value("parties.issuer.name", project.issuer_name or "TBD")
        borrower = get_fact_value("parties.borrower.name")
        technology = get_fact_value("technology.type")
        throughput = get_fact_value("technology.throughput.nameplate")
        project_cost = get_fact_value("capital.project-cost")
        cab_principal = get_fact_value("cab.originalprincipial")
        accretion_rate = get_fact_value("cab.accretionrate")
        dscr = get_fact_value("finmodel.outputs.dscrbase")

        content = f"""# Deal Overview Memo

## Project Summary

**Project Name:** {project.name}

**Description:** {project.description or get_fact_value("project.canonicaldescription")}

**Location:** {project.project_location or get_fact_value("project.location.jurisdiction")}

---

## Transaction Parties

| Role | Entity |
|------|--------|
| Issuer | {issuer} |
| Borrower/Operator | {borrower} |
| Technology Provider | {get_fact_value("parties.operator.name")} |
| Sponsor | {get_fact_value("parties.sponsor.name")} |

---

## Technology & Operations

- **Technology Type:** {technology}
- **Nameplate Throughput:** {throughput}
- **Annual Throughput:** {get_fact_value("technology.throughput.annual")}
- **Operating Status:** {get_fact_value("project.operatingstatus")}

---

## Capital Structure

- **Total Project Cost:** {project_cost}
- **Equity Contribution:** {get_fact_value("capital.equity-contribution")} ({get_fact_value("capital.equity-percent")})
- **CAB Original Principal:** {cab_principal}
- **Accretion Rate:** {accretion_rate}

---

## Financial Metrics

- **Gross Annual Revenue:** {get_fact_value("revenue.gross.annual")}
- **EBITDA:** {get_fact_value("ebitda")}
- **Base DSCR:** {dscr}
- **Minimum DSCR Covenant:** {get_fact_value("finmodel.inputs.dscr.minimum")}

---

## Regulatory & Tax Status

- **Tax Status:** {get_fact_value("regulatory.tax-status")}
- **Inducement Status:** {get_fact_value("governance.inducement")}
"""

        return DeliverableSection(
            section_number=2,
            section_name="Deal Overview Memo",
            content=content,
            is_complete=len(warnings) < 10,
            warnings=warnings[:5],  # Limit warnings
        )

    async def _generate_readiness_report(self, ctx: dict) -> DeliverableSection:
        """Generate Section 3: Readiness & Gap Report."""
        readiness = ctx["readiness"]
        gaps = ctx["gaps"]

        # Build dimension table
        dim_rows = []
        for dim, score in readiness.dimensions.items():
            status = "✅" if score.score >= 4.0 else "⚠️" if score.score >= 2.5 else "❌"
            dim_rows.append(
                f"| {score.dimension_name} | {score.score:.1f} | {score.weight*100:.0f}% | {status} |"
            )

        content = f"""# Readiness & Gap Report

## Overall Assessment

**Score:** {readiness.overall_score:.1f} / 10.0

**Recommendation:** {readiness.recommendation}

{readiness.recommendation_rationale}

---

## Dimension Scores

| Dimension | Score (0-5) | Weight | Status |
|-----------|-------------|--------|--------|
{chr(10).join(dim_rows)}

---

## Critical Gaps ({len(gaps.critical_gaps)})

"""
        if gaps.critical_gaps:
            for gap in gaps.critical_gaps[:10]:
                # gap.dimension is a plain str when use_enum_values=True
                dim_value = getattr(gap.dimension, 'value', gap.dimension)
                content += f"- **{gap.description}** ({dim_value}): {gap.impact}\n"
        else:
            content += "*No critical gaps identified.*\n"

        content += f"""
---

## Material Gaps ({len(gaps.material_gaps)})

"""
        if gaps.material_gaps:
            for gap in gaps.material_gaps[:10]:
                dim_value = getattr(gap.dimension, 'value', gap.dimension)
                content += f"- {gap.description} ({dim_value})\n"
        else:
            content += "*No material gaps identified.*\n"

        content += f"""
---

## Priority Actions

"""
        for i, action in enumerate(gaps.priority_actions, 1):
            content += f"{i}. {action}\n"

        warnings = []
        if readiness.critical_gaps_count > 0:
            warnings.append(f"{readiness.critical_gaps_count} critical gaps need attention")

        return DeliverableSection(
            section_number=3,
            section_name="Readiness & Gap Report",
            content=content,
            is_complete=True,
            warnings=warnings,
        )

    async def _generate_checklist_status(self, ctx: dict) -> DeliverableSection:
        """Generate Section 4: Checklist Status."""
        checklist_summary = ctx["checklist_summary"]

        content = """# Checklist Status

## Phase Summary

| Phase | Name | Ready | In Progress | Blocked | Not Started | Can Proceed |
|-------|------|-------|-------------|---------|-------------|-------------|
"""
        for phase_key, summary in checklist_summary.items():
            can_proceed = "✅" if summary.can_proceed_to_next else "❌"
            content += (
                f"| {phase_key} | {summary.phase_name} | "
                f"{summary.ready_count} | {summary.in_progress_count} | "
                f"{summary.blocked_count} | {summary.not_started_count} | {can_proceed} |\n"
            )

        content += """
---

## Phase Details

"""
        phase_order = ["P1", "P2", "P3", "P4", "P5", "P6"]
        for phase_key in phase_order:
            if phase_key in checklist_summary:
                summary = checklist_summary[phase_key]
                pct = summary.completion_percentage
                content += f"""### {phase_key}: {summary.phase_name}

**Completion:** {pct:.0f}% ({summary.ready_count}/{summary.total_items} items ready)

"""

        warnings = []
        blocked_count = sum(s.blocked_count for s in checklist_summary.values())
        if blocked_count > 0:
            warnings.append(f"{blocked_count} checklist items are blocked")

        return DeliverableSection(
            section_number=4,
            section_name="Checklist Status",
            content=content,
            is_complete=True,
            warnings=warnings,
        )

    async def _generate_evidence_index(self, ctx: dict) -> DeliverableSection:
        """Generate Section 5: Evidence Index."""
        facts = ctx["facts"]

        # Group facts by schema path prefix
        grouped: dict[str, list] = {}
        for fact in facts:
            prefix = fact.schema_path.split(".")[0]
            if prefix not in grouped:
                grouped[prefix] = []
            grouped[prefix].append(fact)

        content = """# Evidence Index

This section provides a complete index of all approved facts with their sources.

"""
        for prefix, prefix_facts in sorted(grouped.items()):
            display_prefix = prefix.replace("_", " ").title()
            content += f"""## {display_prefix}

| Schema Path | Value | Confidence | Criticality |
|-------------|-------|------------|-------------|
"""
            for fact in sorted(prefix_facts, key=lambda f: f.schema_path):
                value_str = str(fact.value)[:50]
                if len(str(fact.value)) > 50:
                    value_str += "..."
                content += (
                    f"| {fact.schema_path} | {value_str} | "
                    f"{fact.confidence_score:.0%} | {fact.criticality} |\n"
                )
            content += "\n"

        content += f"""
---

**Total Facts:** {len(facts)}
"""

        return DeliverableSection(
            section_number=5,
            section_name="Evidence Index",
            content=content,
            is_complete=True,
            warnings=[],
        )

    async def _generate_assumption_register(self, ctx: dict) -> DeliverableSection:
        """Generate Section 6: Assumption Register."""
        facts = ctx["facts"]
        gaps = ctx["gaps"]

        content = """# Assumption Register

This section documents assumptions made where evidence is incomplete or requires verification.

## Gaps Requiring Assumption

"""
        if gaps.critical_gaps or gaps.material_gaps:
            for gap in gaps.critical_gaps + gaps.material_gaps:
                # gap.dimension is a plain str when use_enum_values=True
                dim_value = getattr(gap.dimension, 'value', gap.dimension)
                content += f"""### {gap.description}

- **Dimension:** {dim_value}
- **Criticality:** {gap.criticality}
- **Suggested Evidence:** {gap.suggested_evidence}
- **Assumption:** *Value must be provided or verified by project sponsor*

"""
        else:
            content += "*No significant gaps requiring assumptions.*\n"

        content += """
---

## Low Confidence Facts

The following facts have confidence scores below 80% and may require verification:

| Schema Path | Value | Confidence | Action Required |
|-------------|-------|------------|-----------------|
"""
        low_conf = [f for f in facts if f.confidence_score < 0.80]
        for fact in low_conf[:20]:
            content += (
                f"| {fact.schema_path} | {str(fact.value)[:30]} | "
                f"{fact.confidence_score:.0%} | Verify with source document |\n"
            )

        if len(low_conf) > 20:
            content += f"\n*... and {len(low_conf) - 20} more low-confidence facts*\n"

        warnings = []
        if len(low_conf) > 10:
            warnings.append(f"{len(low_conf)} facts have low confidence scores")

        return DeliverableSection(
            section_number=6,
            section_name="Assumption Register",
            content=content,
            is_complete=True,
            warnings=warnings,
        )

    async def _generate_financial_outputs(self, ctx: dict) -> DeliverableSection:
        """Generate Section 7: Financial Model Outputs."""
        facts_by_path = ctx["facts_by_path"]
        warnings = []

        def get_val(path: str) -> str:
            if path in facts_by_path:
                return str(facts_by_path[path].value)
            warnings.append(f"Missing: {path}")
            return "—"

        content = f"""# Financial Model Outputs

## Capital Structure

| Item | Value |
|------|-------|
| Total Project Cost | {get_val("capital.project-cost")} |
| Equipment Cost | {get_val("capital.equipment-cost")} |
| Equity Contribution | {get_val("capital.equity-contribution")} |
| Equity Percentage | {get_val("capital.equity-percent")} |

---

## CAB Structure

| Item | Value |
|------|-------|
| CAB Enabled | {get_val("cab.enabled")} |
| Original Principal | {get_val("cab.originalprincipial")} |
| Accretion Rate | {get_val("cab.accretionrate")} |
| Accretion Period | {get_val("cab.accretion.period.years")} years |
| Final Maturity | {get_val("cab.finalmaturitydate")} |
| Turbo Redemption | {get_val("cab.turbo.enabled")} |
| Conversion Rate | {get_val("cab.conversion.rate")} |

---

## Revenue & Operations

| Item | Value |
|------|-------|
| Gross Annual Revenue | {get_val("revenue.gross.annual")} |
| Total Annual OpEx | {get_val("opex.total.annual")} |
| Operating Margin | {get_val("opex.margin")} |
| EBITDA | {get_val("ebitda")} |

---

## Debt Service Coverage

| Item | Value |
|------|-------|
| Minimum DSCR Covenant | {get_val("finmodel.inputs.dscr.minimum")} |
| Base Case DSCR | {get_val("finmodel.outputs.dscrbase")} |
| Stress Case DSCR | {get_val("finmodel.outputs.dscrstress")} |

---

*Note: Financial figures are extracted from project documents and require verification by financial advisors.*
"""

        return DeliverableSection(
            section_number=7,
            section_name="Financial Model Outputs",
            content=content,
            is_complete=len(warnings) < 10,
            warnings=warnings[:5],
        )

    async def _generate_slb_brief(self, ctx: dict) -> DeliverableSection:
        """Generate Section 8: SLB KPI Brief."""
        facts_by_path = ctx["facts_by_path"]
        warnings = []

        def get_val(path: str) -> str:
            if path in facts_by_path:
                return str(facts_by_path[path].value)
            warnings.append(f"Missing: {path}")
            return "—"

        slb_enabled = get_val("slb.enabled")

        content = f"""# SLB KPI Brief

## Sustainability-Linked Bond Structure

**SLB Enabled:** {slb_enabled}

"""
        if slb_enabled.lower() in ("true", "yes", "1"):
            content += f"""
## Selected KPIs

{get_val("slb.kpis.shortlist")}

---

## KPI 1 Details

| Item | Value |
|------|-------|
| KPI Name | {get_val("slb.kpi.1.name")} |
| Baseline Value | {get_val("slb.kpi.1.baseline.value")} |
| Baseline Methodology | {get_val("slb.kpi.1.baseline.methodology")} |
| Verification Method | {get_val("slb.kpi.1.verification.method")} |

---

## Penalty Structure

| Item | Value |
|------|-------|
| Step-Up Magnitude | {get_val("slb.penalty.stepup.magnitude")} bps |

---

*Note: SLB KPIs and verification methodology require review by sustainability advisors.*
"""
        else:
            content += "*SLB structure is not enabled for this transaction.*\n"

        return DeliverableSection(
            section_number=8,
            section_name="SLB KPI Brief",
            content=content,
            is_complete=True,
            warnings=warnings[:3],
        )

    async def _generate_disclosure_outline(self, ctx: dict) -> DeliverableSection:
        """Generate Section 9: Disclosure Outline."""
        facts_by_path = ctx["facts_by_path"]
        readiness = ctx["readiness"]

        content = f"""# Disclosure Outline

This section provides a preliminary outline for Official Statement preparation.

## Suggested OS Sections

### 1. Introduction and Summary
- Issuer description
- Project overview
- Security summary
- Use of proceeds

### 2. The Issuer
- Legal authority: {facts_by_path.get("governance.inducement", type("", (), {"value": "TBD"})()).value}
- Tax status: {facts_by_path.get("regulatory.tax-status", type("", (), {"value": "TBD"})()).value}

### 3. The Project
- Technology description
- Operating plan
- Construction timeline
- Permitting status

### 4. Security and Sources of Payment
- Revenue pledge: {facts_by_path.get("security.revenue.pledge", type("", (), {"value": "TBD"})()).value}
- Collateral package
- Reserve requirements

### 5. Financial Information
- Pro forma projections
- DSCR analysis
- Sensitivity analysis

### 6. Risk Factors
- Technology risk
- Construction risk
- Market/offtake risk
- Regulatory risk
- Environmental risk

### 7. Sustainability-Linked Features
- KPI descriptions
- SPT targets
- Verification procedures
- Step-up/step-down mechanics

---

## Readiness for Disclosure

**Current Readiness Score:** {readiness.overall_score:.1f}/10

**Missing Critical Information:**
"""
        gaps = ctx["gaps"]
        for gap in gaps.critical_gaps[:5]:
            content += f"- {gap.description}\n"

        content += """
---

*This outline is preliminary and subject to review by bond counsel and underwriter's counsel.*
"""

        return DeliverableSection(
            section_number=9,
            section_name="Disclosure Outline",
            content=content,
            is_complete=True,
            warnings=[],
        )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def _get_project(self, project_id: UUID) -> Project:
        """Get project by ID."""
        result = await self.session.execute(
            select(Project).where(Project.id == str(project_id))
        )
        project = result.scalar_one_or_none()
        if not project:
            raise ValueError(f"Project {project_id} not found")
        return project

    async def _get_approved_facts(self, project_id: UUID) -> list[ExtractedFact]:
        """Get all approved facts for a project."""
        fact_service = FactService(self.session)
        return await fact_service.get_active_approved_facts(project_id)

    def _index_facts_by_path(
        self,
        facts: list[ExtractedFact],
    ) -> dict[str, ExtractedFact]:
        """Index facts by schema path using canonical-first deterministic selection."""
        return FactService.select_preferred_facts_by_path(facts)
