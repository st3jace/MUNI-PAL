from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from munipal.api.dependencies import DEV_FALLBACK_USER_ID
from munipal.core.models import Artifact, ExtractedFact, ExtractionJob, Playbook, Project, User
from munipal.db.session import AsyncSessionLocal, init_db

DEMO_TENANT_ID = "launch-demo"
DEMO_OWNER_ID = DEV_FALLBACK_USER_ID
PLAYBOOK_ID = str(uuid5(NAMESPACE_URL, "muni-pal:launch-demo:playbook:v1"))


@dataclass(frozen=True)
class DemoFact:
    schema_path: str
    value: Any
    criticality: str = "critical"
    review_status: str = "approved"
    confidence_score: float = 0.92


@dataclass(frozen=True)
class DemoScenario:
    slug: str
    name: str
    issuer_name: str
    sector: str
    subsector: str
    project_location: str
    target_bond_amount: float
    description: str
    artifacts: tuple[str, ...]
    facts: tuple[DemoFact, ...]
    missing_evidence_paths: tuple[str, ...]
    walkthrough_path: str


DEMO_SCENARIOS: tuple[DemoScenario, ...] = (
    DemoScenario(
        slug="healthcare-primary",
        name="Launch Demo — Healthcare Hospital Revenue Bond",
        issuer_name="Demo Regional Health Authority",
        sector="healthcare",
        subsector="healthcare_hospital",
        project_location="Fictional County, ST",
        target_bond_amount=42_000_000,
        description=(
            "Synthetic healthcare primary scenario for BFMS launch review. "
            "Represents a nonprofit hospital capital project with enough approved "
            "evidence to demonstrate readiness scoring while preserving visible gaps."
        ),
        artifacts=(
            "healthcare-board-resolution-draft.pdf",
            "healthcare-capital-plan-summary.pdf",
            "healthcare-audited-financials-excerpt.pdf",
        ),
        facts=(
            DemoFact("project.name", "Demo Regional Health Authority Revenue Bond"),
            DemoFact("project.location", "Fictional County, ST", "material"),
            DemoFact("governance.inducement", "draft board authorization package under review"),
            DemoFact("capital.project-cost", "2,000,000 estimated project fund", "critical"),
            DemoFact("security.revenue.pledge", "gross revenue pledge under counsel review", "critical", "approved", 0.88),
            DemoFact("financials.audited-statements", "FY2024 audited financial statements received", "material"),
            DemoFact("market.demand", "service area utilization memo provided", "material"),
            DemoFact("disclosure.risk-factors", "draft risk factor outline pending counsel review", "material", "pending", 0.71),
        ),
        missing_evidence_paths=(
            "bond_counsel.tax_certificate",
            "rating.preliminary_indication",
            "debt_service.reserve_policy",
        ),
        walkthrough_path="docs/launch-readiness/walkthroughs/healthcare_primary_demo.md",
    ),
    DemoScenario(
        slug="housing-pilot-stage",
        name="Launch Demo — Affordable Housing Pilot Stage",
        issuer_name="Demo Housing Finance Authority",
        sector="housing",
        subsector="housing_affordable_multifamily",
        project_location="Sample City, ST",
        target_bond_amount=28_500_000,
        description=(
            "Synthetic housing pilot-stage scenario for BFMS launch review. "
            "Represents an affordable multifamily financing that is useful for pilot "
            "navigation but intentionally less mature than the healthcare primary scenario."
        ),
        artifacts=(
            "housing-preliminary-sources-uses.pdf",
            "housing-site-control-summary.pdf",
        ),
        facts=(
            DemoFact("project.name", "Demo Affordable Housing Revenue Bond"),
            DemoFact("project.location", "Sample City, ST", "material"),
            DemoFact("capital.project-cost", "8,500,000 preliminary development budget"),
            DemoFact("governance.inducement", "draft issuer inducement calendar identified", "critical", "approved", 0.84),
            DemoFact("housing.units.total", "96 affordable units", "material"),
            DemoFact("housing.affordability.restrictions", "60% AMI set-aside proposed", "critical", "approved", 0.86),
            DemoFact("project.location.sitecontrol", "site control term sheet received", "critical", "pending", 0.72),
        ),
        missing_evidence_paths=(
            "housing.appraisal",
            "housing.tax_credit_allocation",
            "environmental.phase_one",
            "bond_counsel.inducement_resolution",
        ),
        walkthrough_path="docs/launch-readiness/walkthroughs/housing_pilot_stage_demo.md",
    ),
)


def stable_id(kind: str, slug: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"muni-pal:launch-demo:{kind}:{slug}:v1"))


async def ensure_demo_owner(session: AsyncSession) -> None:
    owner = await session.get(User, DEMO_OWNER_ID)
    if owner:
        return
    session.add(
        User(
            id=DEMO_OWNER_ID,
            email="launch-demo@muni-pal.example",
            hashed_password="not-used-demo-seed",
            full_name="Muni-Pal Launch Demo Operator",
            organization="Launch Demo Workspace",
            is_active=True,
            is_superuser=True,
        )
    )
    await session.flush()


async def ensure_demo_playbook(session: AsyncSession) -> Playbook:
    playbook = await session.get(Playbook, PLAYBOOK_ID)
    if playbook:
        return playbook
    playbook = Playbook(
        id=PLAYBOOK_ID,
        name="Launch Demo Playbook",
        version="1.0.0",
        description="Synthetic launch-demo playbook for Healthcare and Housing walkthroughs.",
        bond_archetype="Launch demo revenue bond",
        is_active=True,
        is_default=False,
        schema_paths=[],
        extractors=[],
        checklist_items=[],
        readiness_config={"dimensions": {}},
    )
    session.add(playbook)
    await session.flush()
    return playbook


async def seed_demo_scenarios(session: AsyncSession) -> list[dict[str, Any]]:
    await ensure_demo_owner(session)
    playbook = await ensure_demo_playbook(session)
    results: list[dict[str, Any]] = []

    for scenario in DEMO_SCENARIOS:
        project_id = stable_id("project", scenario.slug)
        project = await session.get(Project, project_id)
        created = project is None
        if project is None:
            project = Project(id=project_id, owner_id=DEMO_OWNER_ID, playbook_id=playbook.id)
            session.add(project)

        project.name = scenario.name
        project.issuer_name = scenario.issuer_name
        project.sector = scenario.sector
        project.subsector = scenario.subsector
        project.project_location = scenario.project_location
        project.target_bond_amount = scenario.target_bond_amount
        project.description = scenario.description
        project.tenant_id = DEMO_TENANT_ID
        project.archetype_id = scenario.subsector
        project.archetype_version = "launch-demo-v1"
        await session.flush()

        artifact_ids: list[str] = []
        for filename in scenario.artifacts:
            artifact_id = stable_id("artifact", f"{scenario.slug}:{filename}")
            artifact = await session.get(Artifact, artifact_id)
            if artifact is None:
                artifact = Artifact(id=artifact_id, project_id=project.id)
                session.add(artifact)
            artifact.filename = filename
            artifact.display_name = filename.replace("-", " ").replace(".pdf", "").title()
            artifact.artifact_type = "pdf"
            artifact.mime_type = "application/pdf"
            artifact.file_size_bytes = 32_768
            artifact.storage_path = f"demo://{scenario.slug}/{filename}"
            artifact.is_processed = True
            artifact.is_extracted = True
            artifact_ids.append(artifact_id)
        await session.flush()

        job_id = stable_id("extraction-job", scenario.slug)
        job = await session.get(ExtractionJob, job_id)
        if job is None:
            job = ExtractionJob(id=job_id, project_id=project.id)
            session.add(job)
        job.job_type = "launch_demo_seed"
        job.target_schema_paths = [fact.schema_path for fact in scenario.facts]
        job.artifact_ids = artifact_ids
        job.chunk_ids = []
        job.status = "completed"
        job.total_chunks = len(artifact_ids)
        job.processed_chunks = len(artifact_ids)
        job.facts_extracted = len(scenario.facts)
        await session.flush()

        for fact in scenario.facts:
            fact_id = stable_id("fact", f"{scenario.slug}:{fact.schema_path}")
            existing = await session.get(ExtractedFact, fact_id)
            if existing is None:
                existing = ExtractedFact(id=fact_id, project_id=project.id, extraction_job_id=job.id)
                session.add(existing)
            existing.schema_path = fact.schema_path
            existing.criticality = fact.criticality
            existing.value = {"text": fact.value}
            existing.value_type = "string"
            existing.confidence_score = fact.confidence_score
            existing.confidence_rationale = "Synthetic launch-demo seed evidence."
            existing.review_status = fact.review_status
            existing.source_type = "extracted"
            existing.is_canonical = fact.review_status == "approved"
            existing.canonical_score = fact.confidence_score if fact.review_status == "approved" else 0.0
            existing.source_trust_score = 0.8
        await session.flush()

        results.append(
            {
                "slug": scenario.slug,
                "project_id": project.id,
                "project_name": project.name,
                "created": created,
                "artifacts": len(scenario.artifacts),
                "facts": len(scenario.facts),
                "approved_facts": sum(1 for fact in scenario.facts if fact.review_status == "approved"),
                "missing_evidence_paths": list(scenario.missing_evidence_paths),
                "walkthrough_path": scenario.walkthrough_path,
            }
        )

    return results


async def main() -> None:
    parser = argparse.ArgumentParser(description="Seed synthetic BFMS launch-demo scenarios.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned scenarios without writing.")
    args = parser.parse_args()

    if args.dry_run:
        for scenario in DEMO_SCENARIOS:
            print(f"{scenario.slug}: {scenario.name} ({len(scenario.artifacts)} artifacts, {len(scenario.facts)} facts)")
        return

    await init_db()
    async with AsyncSessionLocal() as session:
        results = await seed_demo_scenarios(session)
        await session.commit()
    for result in results:
        print(
            f"seeded {result['slug']}: project_id={result['project_id']} "
            f"artifacts={result['artifacts']} facts={result['facts']} "
            f"approved_facts={result['approved_facts']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
