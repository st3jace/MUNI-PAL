"""Regression tests for proposed fact -> accepted fact review lifecycle."""

from uuid import UUID

import pytest

from munipal.core.schemas.base import ReviewStatus, SourceType
from munipal.core.schemas.fact import FactLifecycleState, ManualFactCreate
from munipal.services.fact_service import FactService


async def _project_artifact_job(factory):
    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"])
    artifact = await factory.create_artifact(project["id"])
    job = await factory.create_extraction_job(project["id"], artifact["id"])
    return project, artifact, job


async def test_pending_extracted_fact_is_proposed_until_human_acceptance(
    factory,
    db_session,
    reviewer_id,
):
    project, _artifact, job = await _project_artifact_job(factory)
    fact = await factory.create_fact(
        project["id"],
        job["id"],
        schema_path="governance.inducement",
        value="Resolution pending advisor review",
        review_status="pending",
    )

    service = FactService(db_session)
    proposed = service.fact_to_read_schema(await service.get_fact(UUID(fact["id"])))

    assert proposed.review_status == ReviewStatus.PENDING
    assert proposed.lifecycle_state == FactLifecycleState.PENDING_REVIEW
    assert proposed.review_lifecycle_stage == "proposed"
    assert proposed.can_drive_outputs is False
    assert proposed.reviewed_by is None
    assert proposed.reviewed_at is None

    accepted_fact = await service.approve_fact(
        UUID(fact["id"]),
        UUID(reviewer_id),
        note="Advisor accepted after source review.",
    )
    accepted = service.fact_to_read_schema(accepted_fact)
    revisions = await service.list_revisions(UUID(fact["id"]))

    assert accepted.review_status == ReviewStatus.APPROVED
    assert accepted.review_lifecycle_stage == "accepted"
    assert accepted.can_drive_outputs is True
    assert accepted.reviewed_by == UUID(reviewer_id)
    assert accepted.reviewed_at is not None
    assert revisions[-1].previous_status == ReviewStatus.PENDING.value
    assert revisions[-1].new_status == ReviewStatus.APPROVED.value
    assert revisions[-1].changed_by_id == reviewer_id


async def test_rejected_fact_cannot_drive_readiness_or_export_outputs(
    factory,
    db_session,
    reviewer_id,
):
    project, _artifact, job = await _project_artifact_job(factory)
    fact = await factory.create_fact(
        project["id"],
        job["id"],
        schema_path="governance.inducement",
        value="Unsupported claim",
        review_status="pending",
    )

    service = FactService(db_session)
    rejected_fact = await service.reject_fact(
        UUID(fact["id"]),
        UUID(reviewer_id),
        reason="Source document does not support this claim.",
    )
    rejected = service.fact_to_read_schema(rejected_fact)
    approved_for_outputs = await service.get_active_approved_facts(UUID(project["id"]))

    assert rejected.review_status == ReviewStatus.REJECTED
    assert rejected.lifecycle_state == FactLifecycleState.REJECTED
    assert rejected.review_lifecycle_stage == "rejected"
    assert rejected.can_drive_outputs is False
    assert all(item.id != UUID(fact["id"]) for item in approved_for_outputs)


async def test_manual_facts_require_review_and_cannot_auto_bypass_acceptance(
    factory,
    db_session,
    reviewer_id,
):
    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"])
    service = FactService(db_session)
    request = ManualFactCreate(
        project_id=UUID(project["id"]),
        schema_path="governance.inducement",
        value="Manual advisor-entered resolution",
        note="Entered from advisor diligence call.",
    )

    with pytest.raises(ValueError, match="Manual facts must enter human review"):
        await service.create_manual_fact(
            request=request,
            created_by=UUID(reviewer_id),
            auto_approve=True,
        )

    manual_fact = await service.create_manual_fact(
        request=request,
        created_by=UUID(reviewer_id),
    )
    manual = service.fact_to_read_schema(manual_fact)
    creation_revisions = await service.list_revisions(manual.id)

    assert manual.source_type == SourceType.MANUAL
    assert manual.review_status == ReviewStatus.PENDING
    assert manual.lifecycle_state == FactLifecycleState.PENDING_REVIEW
    assert manual.review_lifecycle_stage == "proposed"
    assert manual.can_drive_outputs is False
    assert creation_revisions[-1].new_status == ReviewStatus.PENDING.value
    assert creation_revisions[-1].changed_by_id == reviewer_id

    accepted_manual_fact = await service.approve_fact(
        manual.id,
        UUID(reviewer_id),
        note="Advisor accepted manually entered diligence fact.",
    )
    accepted_manual = service.fact_to_read_schema(accepted_manual_fact)

    assert accepted_manual.review_lifecycle_stage == "accepted"
    assert accepted_manual.can_drive_outputs is True
    assert accepted_manual.reviewed_by == UUID(reviewer_id)
    assert accepted_manual.reviewed_at is not None
