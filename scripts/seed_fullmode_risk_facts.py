"""
Seed risk facts for full-mode BFMS staging validation.

Creates 10 approved risk dimension facts for the live baseline project
(de618f31-bb6f-4905-be68-8445c357ed32), pushing all 5 dimensions from LOW
to HIGH reliability and triggering FULL integration mode.

Usage (from project root, with server NOT required):
    python scripts/seed_fullmode_risk_facts.py

After running, call the BFMS endpoint:
    GET http://localhost:8080/api/v1/risk/bfms-integration
        ?project_id=de618f31-bb6f-4905-be68-8445c357ed32
        &sector=waste_to_energy
        &issuer_size_band=mid
        &deal_type=revenue
        &recency_window=5y
        &sample_size=50

Expected: integration_mode='full', directional_guidance_only=false
"""

from __future__ import annotations

import hashlib
import os
import sys

# Allow running from project root without installing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
os.environ.setdefault("USE_SQLITE", "false")

from uuid import uuid4

from sqlalchemy import select

from munipal.core.models.extraction import ExtractionJob
from munipal.core.models.fact import ExtractedFact
from munipal.db.session import get_sync_session_context

PROJECT_ID = "de618f31-bb6f-4905-be68-8445c357ed32"

RISK_FACTS: list[tuple[str, str]] = [
    (
        "risk.technology.description",
        "Proven thermal treatment technology with 15+ years operational track record "
        "at comparable facilities; proprietary combustion control system.",
    ),
    (
        "risk.technology.mitigants",
        "Independent Engineer review of technology selection; OEM performance "
        "guarantees and long-term O&M support agreement in place.",
    ),
    (
        "risk.construction.description",
        "Fixed-price, date-certain EPC contract with liquidated damages provisions "
        "covering schedule and performance shortfalls.",
    ),
    (
        "risk.construction.mitigants",
        "Completion bond and performance surety from rated surety provider; "
        "construction reserve fund sized at 6-month debt service.",
    ),
    (
        "risk.market.description",
        "Long-term tipping fee agreements with municipal waste haulers representing "
        "primary revenue stream; secondary energy offtake from utility.",
    ),
    (
        "risk.market.mitigants",
        "Revenue floor established via offtake contracts covering 80% of nameplate "
        "capacity; host community agreement provides minimum throughput guarantee.",
    ),
    (
        "risk.regulatory.description",
        "Air permit and operating license secured from state environmental agency "
        "prior to financial close; Title V compliance plan in effect.",
    ),
    (
        "risk.regulatory.mitigants",
        "Third-party environmental compliance monitoring program; bond counsel has "
        "reviewed all material permits for adequacy and transferability.",
    ),
    (
        "risk.feedstock.description",
        "Municipal solid waste supply secured via 20-year host community agreement "
        "with minimum guaranteed tonnage and escalation provisions.",
    ),
    (
        "risk.feedstock.mitigants",
        "Secondary feedstock supply agreements with neighboring municipalities "
        "and commercial haulers provide supply redundancy above minimum threshold.",
    ),
]


def _source_hash(project_id: str, schema_path: str) -> str:
    return hashlib.sha256(
        f"{project_id}:{schema_path}:bfms_fullmode_seed_v1".encode()
    ).hexdigest()


def main() -> None:
    print(f"Seeding full-mode risk facts for project {PROJECT_ID}\n")

    with get_sync_session_context() as session:
        # ------------------------------------------------------------------
        # 1. Find (or create) an extraction job to attach facts to
        # ------------------------------------------------------------------
        result = session.execute(
            select(ExtractionJob)
            .where(ExtractionJob.project_id == PROJECT_ID)
            .limit(1)
        )
        job = result.scalar_one_or_none()

        if job is None:
            print("  No extraction job found — creating seed job.")
            job = ExtractionJob(
                id=str(uuid4()),
                project_id=PROJECT_ID,
                artifact_ids=[],
                chunk_ids=None,
                status="completed",
                job_type="manual_seed",
                target_schema_paths=[p for p, _ in RISK_FACTS],
                total_chunks=1,
                processed_chunks=1,
                facts_extracted=0,
            )
            session.add(job)
            session.flush()

        print(f"  Using extraction job: {job.id}")

        # ------------------------------------------------------------------
        # 2. Check which risk paths already exist (skip duplicates)
        # ------------------------------------------------------------------
        existing_result = session.execute(
            select(ExtractedFact.schema_path).where(
                ExtractedFact.project_id == PROJECT_ID,
                ExtractedFact.schema_path.like("risk.%"),
                ExtractedFact.review_status == "approved",
            )
        )
        existing_paths = {row[0] for row in existing_result}

        # ------------------------------------------------------------------
        # 3. Insert new facts
        # ------------------------------------------------------------------
        created = 0
        for schema_path, value in RISK_FACTS:
            if schema_path in existing_paths:
                print(f"  SKIP (exists): {schema_path}")
                continue

            fact = ExtractedFact(
                id=str(uuid4()),
                schema_path=schema_path,
                criticality="material",
                value=value,
                value_type="string",
                confidence_score=0.95,
                confidence_rationale=(
                    "Seeded from project documentation for BFMS full-mode staging validation"
                ),
                source_type="manual",
                project_id=PROJECT_ID,
                extraction_job_id=job.id,
                review_status="approved",
                lifecycle_state="active",
                source_hash=_source_hash(PROJECT_ID, schema_path),
            )
            session.add(fact)
            created += 1
            print(f"  CREATED: {schema_path}")

        print(f"\n  Committed {created} new risk facts.")

    # ------------------------------------------------------------------
    # 4. Print verification instructions
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("NEXT STEP — call the BFMS endpoint in your browser:")
    print("=" * 60)
    print(
        "http://localhost:8080/api/v1/risk/bfms-integration"
        "?project_id=de618f31-bb6f-4905-be68-8445c357ed32"
        "&sector=waste_to_energy"
        "&issuer_size_band=mid"
        "&deal_type=revenue"
        "&recency_window=5y"
        "&sample_size=50"
    )
    print()
    print('Expected: "integration_mode": "full"')
    print('          "directional_guidance_only": false')
    print('          "fallback_reasons": []')


if __name__ == "__main__":
    main()
