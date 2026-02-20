"""
Backfill dedup/canonical metadata for extracted facts after schema migration.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import distinct, func, select

from munipal.core.models.fact import ExtractedFact
from munipal.db.session import AsyncSessionLocal
from munipal.services.fact_service import FactService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recompute dedup/canonical metadata for extracted facts per project "
            "using current canonicalization rules."
        )
    )
    parser.add_argument(
        "--project-id",
        action="append",
        dest="project_ids",
        help="Repeatable project id filter. Defaults to all projects that currently have facts.",
    )
    return parser.parse_args()


async def _project_ids_with_facts() -> list[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(distinct(ExtractedFact.project_id)).where(ExtractedFact.project_id.is_not(None))
        )
        return sorted(row[0] for row in result if row[0])


async def _backfill_project(project_id: str) -> tuple[int, int]:
    async with AsyncSessionLocal() as session:
        service = FactService(session)
        schema_paths = await service.refresh_canonicalization_for_project(
            project_id=project_id,
            actor_id="system",
            reason="migration_backfill",
            source_action="backfill_fact_canonicalization",
        )
        await session.commit()

        canonical_count_result = await session.execute(
            select(func.count(ExtractedFact.id)).where(
                ExtractedFact.project_id == project_id,
                ExtractedFact.is_canonical.is_(True),
            )
        )
        canonical_count = int(canonical_count_result.scalar() or 0)
        return len(schema_paths), canonical_count


async def run(args: argparse.Namespace) -> int:
    project_ids = sorted(set(args.project_ids or await _project_ids_with_facts()))
    if not project_ids:
        print("No projects with extracted facts found. Nothing to backfill.")
        return 0

    print(f"Backfilling canonicalization for {len(project_ids)} project(s)")
    for project_id in project_ids:
        schema_path_count, canonical_count = await _backfill_project(project_id)
        print(
            f"- {project_id}: refreshed {schema_path_count} schema path(s), "
            f"{canonical_count} canonical fact(s)"
        )

    stamp = datetime.now(timezone.utc).isoformat()
    print(f"Backfill completed at {stamp}")
    return 0


def main() -> None:
    args = parse_args()
    _ = Path(__file__).resolve()
    exit_code = asyncio.run(run(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
