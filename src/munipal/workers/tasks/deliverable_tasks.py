"""
Deliverable generation tasks.

Per spec (WP6): Warm Handoff Pack Assembly
- Package everything into professional, neutral advisor-ready deliverable
- Generate all 9 sections per playbook
- Include mandatory disclaimer
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select

from munipal.core.models.deliverable import DeliverablePack
from munipal.core.models.fact import ExtractedFact
from munipal.core.models.project import Project
from munipal.core.schemas.base import ReviewStatus
from munipal.db.session import get_sync_session
from munipal.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="munipal.workers.tasks.deliverable_tasks.generate_pack")
def generate_pack(self, pack_id: str) -> dict:
    """
    Generate a complete deliverable pack.

    Per playbook Section 8, the pack has 9 sections:
    1. Cover
    2. Deal Overview Memo
    3. Readiness & Gap Report
    4. Checklist Status
    5. Evidence Index
    6. Assumption Register
    7. Financial Model Outputs
    8. SLB KPI Brief
    9. Disclosure Outline

    Per spec: "An advisor can review the handoff pack in <15 minutes"
    """
    logger.info(f"Starting pack generation for {pack_id}")

    with get_sync_session() as session:
        pack = session.execute(
            select(DeliverablePack).where(DeliverablePack.id == pack_id)
        ).scalar_one_or_none()

        if not pack:
            logger.error(f"Pack {pack_id} not found")
            return {"pack_id": pack_id, "status": "error", "error": "Pack not found"}

        pack.celery_task_id = self.request.id
        pack.generation_started_at = datetime.now(timezone.utc)
        session.commit()

        try:
            project = session.execute(
                select(Project).where(Project.id == pack.project_id)
            ).scalar_one_or_none()

            if not project:
                raise ValueError(f"Project {pack.project_id} not found")

            facts = list(
                session.execute(
                    select(ExtractedFact).where(
                        ExtractedFact.project_id == pack.project_id,
                        ExtractedFact.review_status == ReviewStatus.APPROVED.value,
                    )
                ).scalars().all()
            )

            facts_by_path = {f.schema_path: f for f in facts}

            sections = []
            warnings = []

            # Section 1: Cover
            sections.append(_generate_cover(project, pack, len(facts)))

            # Section 2: Deal Overview
            section, section_warnings = _generate_deal_overview(project, facts_by_path)
            sections.append(section)
            warnings.extend(section_warnings)

            # Section 3: Readiness
            sections.append(_generate_readiness(project, facts))

            # Section 4: Checklist
            sections.append(_generate_checklist(project))

            # Section 5: Evidence Index
            sections.append(_generate_evidence_index(facts))

            # Section 6: Assumption Register
            section = _generate_assumption_register(facts)
            sections.append(section)
            if section.get("warnings"):
                warnings.extend(section["warnings"])

            # Section 7: Financial Outputs
            section, section_warnings = _generate_financial(facts_by_path)
            sections.append(section)
            warnings.extend(section_warnings)

            # Section 8: SLB Brief
            sections.append(_generate_slb(facts_by_path))

            # Section 9: Disclosure Outline
            sections.append(_generate_disclosure(facts_by_path))

            pack.sections = sections
            pack.warnings = list(set(warnings))[:20]
            pack.facts_included_count = len(facts)
            pack.is_complete = True
            pack.generation_completed_at = datetime.now(timezone.utc)

            session.commit()

            logger.info(f"Pack {pack_id} generated with {len(sections)} sections")

            return {
                "pack_id": pack_id,
                "status": "completed",
                "sections_generated": len(sections),
                "facts_included": len(facts),
                "warnings_count": len(warnings),
            }

        except Exception as e:
            logger.error(f"Pack generation failed for {pack_id}: {e}")
            pack.warnings = [f"Generation failed: {str(e)}"]
            session.commit()

            return {"pack_id": pack_id, "status": "failed", "error": str(e)}


@celery_app.task(bind=True, name="munipal.workers.tasks.deliverable_tasks.generate_section")
def generate_section(self, pack_id: str, section_number: int) -> dict:
    """Generate a single section of the deliverable pack."""
    logger.info(f"Regenerating section {section_number} for pack {pack_id}")
    return generate_pack(pack_id)


@celery_app.task(bind=True, name="munipal.workers.tasks.deliverable_tasks.export_pack_pdf")
def export_pack_pdf(self, pack_id: str) -> dict:
    """Export a deliverable pack to PDF format."""
    logger.info(f"Exporting pack {pack_id} to PDF")

    with get_sync_session() as session:
        pack = session.execute(
            select(DeliverablePack).where(DeliverablePack.id == pack_id)
        ).scalar_one_or_none()

        if not pack:
            return {"pack_id": pack_id, "status": "error", "error": "Pack not found"}

        if not pack.is_complete:
            return {"pack_id": pack_id, "status": "error", "error": "Pack not generated"}

        return {
            "pack_id": pack_id,
            "status": "pending",
            "message": "PDF export requires weasyprint or similar library",
            "pdf_path": None,
        }


# -----------------------------------------------------------------------------
# Section Generators
# -----------------------------------------------------------------------------


def _generate_cover(project, pack, fact_count: int) -> dict:
    """Generate cover section."""
    content = f"""# {pack.title}

**Project:** {project.name}

**Prepared For:** {pack.generated_for}

**Date:** {datetime.now(timezone.utc).strftime('%B %d, %Y')}

---

**Facts Included:** {fact_count}

---

*This document has been prepared by Muni-Pal Bond Facility Management System.*

*All facts and figures are derived from uploaded project documents and are subject to verification by qualified professionals.*
"""
    return {
        "section_number": 1,
        "section_name": "Cover",
        "content": content,
        "is_complete": True,
        "warnings": [],
    }


def _generate_deal_overview(project, facts_by_path: dict) -> tuple[dict, list]:
    """Generate deal overview section."""
    warnings = []

    def get_val(path: str, default: str = "Not specified") -> str:
        if path in facts_by_path:
            return str(facts_by_path[path].value)
        warnings.append(f"Missing: {path}")
        return default

    content = f"""# Deal Overview Memo

## Project Summary

**Project Name:** {project.name}

**Description:** {project.description or get_val("project.canonicaldescription")}

**Location:** {project.project_location or get_val("project.location.jurisdiction")}

---

## Transaction Parties

| Role | Entity |
|------|--------|
| Issuer | {get_val("parties.issuer.name")} |
| Borrower | {get_val("parties.borrower.name")} |
| Operator | {get_val("parties.operator.name")} |
| Sponsor | {get_val("parties.sponsor.name")} |

---

## Technology & Operations

- **Technology Type:** {get_val("technology.type")}
- **Nameplate Throughput:** {get_val("technology.throughput.nameplate")}
- **Annual Throughput:** {get_val("technology.throughput.annual")}
- **Operating Status:** {get_val("project.operatingstatus")}

---

## Capital Structure

- **Total Project Cost:** {get_val("capital.project-cost")}
- **Equity Contribution:** {get_val("capital.equity-contribution")} ({get_val("capital.equity-percent")})
- **CAB Principal:** {get_val("cab.originalprincipial")}
- **Accretion Rate:** {get_val("cab.accretionrate")}

---

## Financial Metrics

- **Gross Annual Revenue:** {get_val("revenue.gross.annual")}
- **EBITDA:** {get_val("ebitda")}
- **Base DSCR:** {get_val("finmodel.outputs.dscrbase")}
- **Min DSCR Covenant:** {get_val("finmodel.inputs.dscr.minimum")}

---

## Tax & Regulatory

- **Tax Status:** {get_val("regulatory.tax-status")}
- **Inducement:** {get_val("governance.inducement")}
"""
    return {
        "section_number": 2,
        "section_name": "Deal Overview Memo",
        "content": content,
        "is_complete": len(warnings) < 15,
        "warnings": warnings[:5],
    }, warnings


def _generate_readiness(project, facts: list) -> dict:
    """Generate readiness section."""
    critical = [f for f in facts if f.criticality == "critical"]
    material = [f for f in facts if f.criticality == "material"]

    content = f"""# Readiness & Gap Report

## Evidence Summary

| Category | Count |
|----------|-------|
| Critical Facts | {len(critical)} |
| Material Facts | {len(material)} |
| Total Approved | {len(facts)} |

---

*For detailed readiness scoring, use the /api/v1/readiness endpoint.*
"""
    return {
        "section_number": 3,
        "section_name": "Readiness & Gap Report",
        "content": content,
        "is_complete": True,
        "warnings": [],
    }


def _generate_checklist(project) -> dict:
    """Generate checklist section."""
    content = """# Checklist Status

## Phase Overview

| Phase | Name |
|-------|------|
| P1 | Issuer Authority & Deal Formation |
| P2 | Project & Technology Definition |
| P3 | Financial Structure & Revenue Model |
| P4 | Risk, Security & Disclosure |
| P5 | SLB Architecture & Final Modeling |
| P6 | Advisor Engagement & Execution |

---

*For detailed checklist status, use the /api/v1/checklist endpoint.*
"""
    return {
        "section_number": 4,
        "section_name": "Checklist Status",
        "content": content,
        "is_complete": True,
        "warnings": [],
    }


def _generate_evidence_index(facts: list) -> dict:
    """Generate evidence index."""
    grouped: dict[str, list] = {}
    for fact in facts:
        prefix = fact.schema_path.split(".")[0]
        if prefix not in grouped:
            grouped[prefix] = []
        grouped[prefix].append(fact)

    content = "# Evidence Index\n\n"

    for prefix, prefix_facts in sorted(grouped.items()):
        content += f"## {prefix.replace('_', ' ').title()}\n\n"
        content += "| Path | Value | Confidence | Criticality |\n"
        content += "|------|-------|------------|-------------|\n"
        for f in sorted(prefix_facts, key=lambda x: x.schema_path):
            val = str(f.value)[:40]
            if len(str(f.value)) > 40:
                val += "..."
            content += f"| {f.schema_path} | {val} | {f.confidence_score:.0%} | {f.criticality} |\n"
        content += "\n"

    content += f"\n---\n\n**Total Facts:** {len(facts)}\n"

    return {
        "section_number": 5,
        "section_name": "Evidence Index",
        "content": content,
        "is_complete": True,
        "warnings": [],
    }


def _generate_assumption_register(facts: list) -> dict:
    """Generate assumption register."""
    low_conf = [f for f in facts if f.confidence_score < 0.80]

    content = """# Assumption Register

## Low Confidence Facts Requiring Verification

"""
    if low_conf:
        content += "| Path | Value | Confidence |\n"
        content += "|------|-------|------------|\n"
        for f in low_conf[:25]:
            val = str(f.value)[:30]
            content += f"| {f.schema_path} | {val} | {f.confidence_score:.0%} |\n"

        if len(low_conf) > 25:
            content += f"\n*... and {len(low_conf) - 25} more facts requiring verification*\n"
    else:
        content += "*All facts have confidence scores >= 80%*\n"

    warnings = []
    if len(low_conf) > 10:
        warnings.append(f"{len(low_conf)} facts have low confidence")

    return {
        "section_number": 6,
        "section_name": "Assumption Register",
        "content": content,
        "is_complete": True,
        "warnings": warnings,
    }


def _generate_financial(facts_by_path: dict) -> tuple[dict, list]:
    """Generate financial outputs section."""
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
| Accretion Period | {get_val("cab.accretion.period.years")} |
| Final Maturity | {get_val("cab.finalmaturitydate")} |
| Turbo Enabled | {get_val("cab.turbo.enabled")} |

---

## Revenue & Coverage

| Item | Value |
|------|-------|
| Gross Revenue | {get_val("revenue.gross.annual")} |
| Total OpEx | {get_val("opex.total.annual")} |
| EBITDA | {get_val("ebitda")} |
| Min DSCR | {get_val("finmodel.inputs.dscr.minimum")} |
| Base DSCR | {get_val("finmodel.outputs.dscrbase")} |
| Stress DSCR | {get_val("finmodel.outputs.dscrstress")} |

---

*Financial figures require verification by financial advisors.*
"""
    return {
        "section_number": 7,
        "section_name": "Financial Model Outputs",
        "content": content,
        "is_complete": len(warnings) < 10,
        "warnings": warnings[:5],
    }, warnings


def _generate_slb(facts_by_path: dict) -> dict:
    """Generate SLB brief section."""
    def get_val(path: str) -> str:
        return str(facts_by_path[path].value) if path in facts_by_path else "—"

    slb_enabled = get_val("slb.enabled")

    content = f"""# SLB KPI Brief

## Structure

**SLB Enabled:** {slb_enabled}

"""
    if slb_enabled.lower() in ("true", "yes", "1"):
        content += f"""## Selected KPIs

{get_val("slb.kpis.shortlist")}

## KPI Details

| Item | Value |
|------|-------|
| KPI Name | {get_val("slb.kpi.1.name")} |
| Baseline | {get_val("slb.kpi.1.baseline.value")} |
| Methodology | {get_val("slb.kpi.1.baseline.methodology")} |
| Verification | {get_val("slb.kpi.1.verification.method")} |

## Penalty Structure

| Item | Value |
|------|-------|
| Step-Up | {get_val("slb.penalty.stepup.magnitude")} bps |

---

*SLB structure requires review by sustainability advisors.*
"""
    else:
        content += "*SLB structure not enabled for this transaction.*\n"

    return {
        "section_number": 8,
        "section_name": "SLB KPI Brief",
        "content": content,
        "is_complete": True,
        "warnings": [],
    }


def _generate_disclosure(facts_by_path: dict) -> dict:
    """Generate disclosure outline section."""
    content = """# Disclosure Outline

## Suggested Official Statement Sections

1. **Introduction and Summary**
   - Issuer description
   - Project overview
   - Security summary

2. **The Issuer**
   - Legal authority
   - Tax status

3. **The Project**
   - Technology
   - Operations
   - Permitting

4. **Security and Sources of Payment**
   - Revenue pledge
   - Collateral
   - Reserves

5. **Financial Information**
   - Projections
   - DSCR analysis

6. **Risk Factors**
   - Technology
   - Construction
   - Market
   - Regulatory

7. **Sustainability Features**
   - KPIs
   - Targets
   - Verification

---

*This outline is preliminary and requires review by bond counsel.*
"""
    return {
        "section_number": 9,
        "section_name": "Disclosure Outline",
        "content": content,
        "is_complete": True,
        "warnings": [],
    }
