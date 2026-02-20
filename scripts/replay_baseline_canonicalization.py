"""
Replay canonicalization for baseline projects and write deterministic snapshots.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from munipal.db.session import AsyncSessionLocal
from munipal.services.fact_service import FactService

DEFAULT_BASELINE_PROJECT_IDS = [
    "de618f31-bb6f-4905-be68-8445c357ed32",
    "41f263ab-d83a-42c6-9f30-be128ddd3320",
    "9253227f-6453-43ce-a199-c59caf66a281",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Replay canonicalization across baseline projects and verify "
            "snapshot stability across repeated runs."
        )
    )
    parser.add_argument(
        "--project-id",
        action="append",
        dest="project_ids",
        help="Repeatable project id override. If omitted, baseline defaults are used.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=3,
        help="Number of replay iterations to compare (minimum 2).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON path (default: reports/baseline_canonical_replay_YYYYMMDD.json).",
    )
    parser.add_argument(
        "--fail-on-empty",
        action="store_true",
        help="Exit non-zero if any project has no facts to replay.",
    )
    return parser.parse_args()


def _default_output_path(root: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    return root / "reports" / f"baseline_canonical_replay_{stamp}.json"


async def _replay_project(project_id: str, iterations: int) -> dict[str, Any]:
    async with AsyncSessionLocal() as session:
        service = FactService(session)
        schema_paths = await service.get_project_schema_paths(project_id, include_archived=True)
        if not schema_paths:
            return {
                "project_id": project_id,
                "status": "no_facts",
                "schema_path_count": 0,
                "fact_count": 0,
                "stable": False,
                "unstable_iterations": [],
            }

        snapshots: list[dict[str, dict[str, Any]]] = []
        for iteration in range(iterations):
            await service.refresh_canonicalization_for_project(
                project_id=project_id,
                actor_id="system",
                reason=f"baseline_replay:{iteration + 1}",
                source_action="baseline_canonical_replay",
            )
            await session.commit()
            snapshots.append(
                await service.canonical_snapshot_for_project(
                    project_id=project_id,
                    include_archived=True,
                )
            )

        baseline_snapshot = snapshots[0]
        unstable_iterations = [
            iteration_index + 2
            for iteration_index, snapshot in enumerate(snapshots[1:])
            if snapshot != baseline_snapshot
        ]
        fact_count = sum(item["fact_count"] for item in baseline_snapshot.values())
        canonical_path_count = sum(
            1 for item in baseline_snapshot.values() if item["canonical_fact_ids"]
        )

        return {
            "project_id": project_id,
            "status": "ok",
            "schema_path_count": len(baseline_snapshot),
            "fact_count": fact_count,
            "canonical_path_count": canonical_path_count,
            "stable": len(unstable_iterations) == 0,
            "unstable_iterations": unstable_iterations,
            "snapshot": baseline_snapshot,
        }


async def run(args: argparse.Namespace) -> int:
    if args.iterations < 2:
        raise ValueError("--iterations must be >= 2")

    root = Path(__file__).resolve().parents[1]
    output_path = args.output or _default_output_path(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    project_ids = args.project_ids or DEFAULT_BASELINE_PROJECT_IDS
    project_reports = []
    for project_id in project_ids:
        try:
            project_reports.append(await _replay_project(project_id, args.iterations))
        except SQLAlchemyError as exc:
            project_reports.append(
                {
                    "project_id": project_id,
                    "status": "schema_error",
                    "schema_path_count": 0,
                    "fact_count": 0,
                    "stable": False,
                    "unstable_iterations": [],
                    "error_type": exc.__class__.__name__,
                    "error_message": str(exc).splitlines()[0][:500],
                }
            )

    replayable_reports = [report for report in project_reports if report["status"] == "ok"]
    empty_project_ids = [
        report["project_id"] for report in project_reports if report["status"] == "no_facts"
    ]
    schema_error_project_ids = [
        report["project_id"] for report in project_reports if report["status"] == "schema_error"
    ]
    overall_stable = bool(replayable_reports) and all(
        report["stable"] for report in replayable_reports
    )

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "iterations": args.iterations,
        "project_ids": project_ids,
        "overall_stable": overall_stable,
        "empty_project_ids": empty_project_ids,
        "schema_error_project_ids": schema_error_project_ids,
        "projects": project_reports,
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print(f"Wrote canonical replay report to {output_path}")
    for report in project_reports:
        status = report["status"]
        if status == "no_facts":
            print(f"- {report['project_id']}: no facts")
            continue
        if status == "schema_error":
            print(f"- {report['project_id']}: schema error ({report['error_type']})")
            continue
        stability = "stable" if report["stable"] else "unstable"
        print(
            f"- {report['project_id']}: {stability}, "
            f"{report['schema_path_count']} paths, {report['fact_count']} facts"
        )

    if not overall_stable:
        return 1
    if args.fail_on_empty and empty_project_ids:
        return 1
    return 0


def main() -> None:
    args = parse_args()
    exit_code = asyncio.run(run(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
