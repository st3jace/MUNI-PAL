"""
Bootstrap a baseline project from an existing populated corpus without LLM calls.

Use this when a baseline project exists on disk (artifact files) but has no rows
or fact corpus in the active database environment.
"""

from __future__ import annotations

import argparse
import mimetypes
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select

from munipal.core.models import Artifact, ExtractionJob, Project
from munipal.core.models.fact import ExtractedFact
from munipal.db.session import AsyncSessionLocal
from munipal.services.artifact_service import ArtifactService
from munipal.services.fact_service import FactService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Populate a baseline project from a legacy populated project, "
            "including local artifact registration, chunk processing, and fact clone."
        )
    )
    parser.add_argument(
        "--source-project-id",
        required=True,
        help="Project id with existing fact corpus.",
    )
    parser.add_argument(
        "--target-project-id",
        required=True,
        help="Project id to create/populate.",
    )
    parser.add_argument(
        "--target-project-name",
        default="UCS WTE Facility",
        help="Target project display name if project row is created.",
    )
    parser.add_argument(
        "--artifact-dir",
        required=True,
        help="Path to local artifact directory for target project.",
    )
    return parser.parse_args()


def _artifact_type_for_suffix(path: Path) -> tuple[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf", "application/pdf"
    if suffix == ".docx":
        return "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    if suffix == ".xlsx":
        return "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if suffix == ".xls":
        return "xls", "application/vnd.ms-excel"
    if suffix == ".csv":
        return "csv", "text/csv"
    if suffix == ".txt":
        return "txt", "text/plain"
    guessed = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return suffix.lstrip(".") or "bin", guessed


async def _ensure_target_project(
    source_project_id: str,
    target_project_id: str,
    target_project_name: str,
) -> tuple[str, str]:
    async with AsyncSessionLocal() as session:
        source_project = await session.get(Project, source_project_id)
        if not source_project:
            raise ValueError(f"Source project {source_project_id} not found")

        target_project = await session.get(Project, target_project_id)
        if not target_project:
            target_project = Project(
                id=target_project_id,
                name=target_project_name,
                description=source_project.description,
                issuer_name=source_project.issuer_name,
                project_location=source_project.project_location,
                target_bond_amount=source_project.target_bond_amount,
                owner_id=source_project.owner_id,
                playbook_id=source_project.playbook_id,
            )
            session.add(target_project)
            await session.commit()

        return target_project.owner_id, target_project.playbook_id


async def _ensure_target_artifacts(target_project_id: str, artifact_dir: Path) -> list[str]:
    if not artifact_dir.exists():
        raise ValueError(f"Artifact directory not found: {artifact_dir}")

    files = sorted(
        [path for path in artifact_dir.iterdir() if path.is_file()],
        key=lambda path: path.name,
    )
    if not files:
        raise ValueError(f"No files found in artifact directory: {artifact_dir}")

    async with AsyncSessionLocal() as session:
        existing_result = await session.execute(
            select(Artifact).where(Artifact.project_id == target_project_id)
        )
        existing = {artifact.id: artifact for artifact in existing_result.scalars().all()}
        artifact_ids: list[str] = []

        for file_path in files:
            artifact_id = file_path.stem
            artifact_type, mime_type = _artifact_type_for_suffix(file_path)
            relative_storage_path = str(Path(target_project_id) / file_path.name)
            file_size = file_path.stat().st_size

            if artifact_id not in existing:
                artifact = Artifact(
                    id=artifact_id,
                    project_id=target_project_id,
                    filename=file_path.name,
                    display_name=file_path.name,
                    artifact_type=artifact_type,
                    mime_type=mime_type,
                    file_size_bytes=file_size,
                    storage_path=relative_storage_path,
                    is_processed=False,
                    is_extracted=False,
                )
                session.add(artifact)
            artifact_ids.append(artifact_id)

        await session.commit()
        return artifact_ids


async def _process_target_artifacts(artifact_ids: list[str]) -> None:
    async with AsyncSessionLocal() as session:
        artifact_service = ArtifactService(session)
        for artifact_id in artifact_ids:
            artifact = await session.get(Artifact, artifact_id)
            if not artifact or artifact.is_processed:
                continue
            success, message = await artifact_service.process_artifact(UUID(artifact_id))
            if not success:
                raise RuntimeError(f"Failed to process artifact {artifact_id}: {message}")
        await session.commit()


def _clone_fact_payload(fact: ExtractedFact) -> dict[str, Any]:
    return {
        "schema_path": fact.schema_path,
        "criticality": fact.criticality,
        "source_type": fact.source_type,
        "value": fact.value,
        "value_type": fact.value_type,
        "unit": fact.unit,
        "confidence_score": float(fact.confidence_score or 0.0),
        "confidence_rationale": fact.confidence_rationale,
        "review_status": fact.review_status,
        "reviewed_by": fact.reviewed_by,
        "reviewed_at": fact.reviewed_at,
        "review_note": fact.review_note,
        "original_value": fact.original_value,
        "lifecycle_state": fact.lifecycle_state,
        "archive_reason_code": fact.archive_reason_code,
        "archive_note": fact.archive_note,
        "archived_by": fact.archived_by,
        "archived_at": fact.archived_at,
    }


async def _clone_fact_corpus(
    source_project_id: str,
    target_project_id: str,
    artifact_ids: list[str],
) -> int:
    async with AsyncSessionLocal() as session:
        existing_count_result = await session.execute(
            select(ExtractedFact).where(ExtractedFact.project_id == target_project_id)
        )
        existing_target_facts = list(existing_count_result.scalars().all())
        if existing_target_facts:
            return len(existing_target_facts)

        source_facts_result = await session.execute(
            select(ExtractedFact)
            .where(ExtractedFact.project_id == source_project_id)
            .order_by(ExtractedFact.created_at.asc(), ExtractedFact.id.asc())
        )
        source_facts = list(source_facts_result.scalars().all())
        if not source_facts:
            raise ValueError(f"Source project {source_project_id} has no facts to clone")

        clone_job_id = str(uuid4())
        clone_job = ExtractionJob(
            id=clone_job_id,
            project_id=target_project_id,
            job_type="baseline_clone_backfill",
            artifact_ids=artifact_ids,
            target_schema_paths=[],
            status="completed",
            total_chunks=0,
            processed_chunks=0,
            facts_extracted=len(source_facts),
        )
        session.add(clone_job)
        await session.flush()

        cloned_count = 0
        for source_fact in source_facts:
            payload = _clone_fact_payload(source_fact)
            target_fact = ExtractedFact(
                id=str(uuid4()),
                project_id=target_project_id,
                extraction_job_id=clone_job_id if payload["source_type"] != "manual" else None,
                schema_path=payload["schema_path"],
                criticality=payload["criticality"],
                source_type=payload["source_type"],
                value=payload["value"],
                value_type=payload["value_type"],
                unit=payload["unit"],
                confidence_score=payload["confidence_score"],
                confidence_rationale=payload["confidence_rationale"],
                review_status=payload["review_status"],
                reviewed_by=payload["reviewed_by"],
                reviewed_at=payload["reviewed_at"],
                review_note=payload["review_note"],
                original_value=payload["original_value"],
                lifecycle_state=payload["lifecycle_state"],
                archive_reason_code=payload["archive_reason_code"],
                archive_note=payload["archive_note"],
                archived_by=payload["archived_by"],
                archived_at=payload["archived_at"],
            )
            session.add(target_fact)
            cloned_count += 1

        await session.flush()

        for artifact_id in artifact_ids:
            artifact = await session.get(Artifact, artifact_id)
            if artifact:
                artifact.is_extracted = True
                artifact.last_extraction_job_id = clone_job_id

        fact_service = FactService(session)
        await fact_service.refresh_canonicalization_for_project(
            target_project_id,
            actor_id="system",
            reason=f"baseline_clone:{source_project_id}",
            source_action="bootstrap_baseline_project_from_legacy",
        )
        await session.commit()
        return cloned_count


async def run(args: argparse.Namespace) -> int:
    source_project_id = str(UUID(args.source_project_id))
    target_project_id = str(UUID(args.target_project_id))
    artifact_dir = Path(args.artifact_dir).resolve()

    owner_id, playbook_id = await _ensure_target_project(
        source_project_id=source_project_id,
        target_project_id=target_project_id,
        target_project_name=args.target_project_name,
    )
    artifact_ids = await _ensure_target_artifacts(target_project_id, artifact_dir)
    await _process_target_artifacts(artifact_ids)
    cloned_count = await _clone_fact_corpus(
        source_project_id=source_project_id,
        target_project_id=target_project_id,
        artifact_ids=artifact_ids,
    )

    print(
        f"Bootstrapped target project {target_project_id} from source {source_project_id} "
        f"(owner={owner_id}, playbook={playbook_id})"
    )
    print(f"- artifacts registered: {len(artifact_ids)}")
    print(f"- facts available: {cloned_count}")
    return 0


def main() -> None:
    args = parse_args()
    import asyncio

    exit_code = asyncio.run(run(args))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
