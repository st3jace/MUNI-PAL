from uuid import UUID, uuid4

import pytest
from munipal.core.models.fact import FactChunkAssociation
from munipal.core.schemas.base import ReviewStatus
from munipal.services.deliverable_service import DeliverableService
from munipal.services.fact_service import FactService


async def _project_artifact_chunk_job(factory):
    playbook = await factory.create_playbook()
    project = await factory.create_project(playbook["id"])
    artifact = await factory.create_artifact(project["id"], filename="source_agreement.pdf")
    chunk = await factory.create_chunk(
        artifact["id"],
        content="The issuer authority was approved by council resolution.",
        page_number=7,
    )
    job = await factory.create_extraction_job(project["id"], artifact["id"])
    return project, artifact, chunk, job


async def test_accepted_fact_exposes_stable_advisor_source_refs(factory, db_session, reviewer_id):
    project, artifact, chunk, job = await _project_artifact_chunk_job(factory)
    fact = await factory.create_fact(
        project["id"],
        job["id"],
        schema_path="governance.inducement",
        value="Council resolution adopted",
        review_status="pending",
        with_source_refs=False,
    )
    db_session.add(
        FactChunkAssociation(
            fact_id=fact["id"],
            chunk_id=chunk["id"],
            excerpt="approved by council resolution",
        )
    )
    await db_session.commit()

    service = FactService(db_session)
    accepted = await service.approve_fact(
        UUID(fact["id"]),
        UUID(reviewer_id),
        note="Advisor verified against uploaded source.",
    )
    accepted = await service.get_fact(UUID(accepted.id))
    read_model = service.fact_to_read_schema(accepted)

    assert read_model.review_status == ReviewStatus.APPROVED
    assert read_model.reviewed_at is not None
    assert len(read_model.source_chunks) == 1
    assert len(read_model.source_refs) == 1
    source_ref = read_model.source_refs[0]
    assert source_ref.artifact_id == UUID(artifact["id"])
    assert source_ref.chunk_id == UUID(chunk["id"])
    assert source_ref.artifact_filename == "source_agreement.pdf"
    assert source_ref.storage_path.endswith("source_agreement.pdf")
    assert source_ref.page_number == 7
    assert source_ref.content_hash.startswith("test-hash-")
    assert source_ref.excerpt == "approved by council resolution"
    assert read_model.provenance_fingerprint


async def test_extracted_fact_cannot_be_approved_without_source_refs(factory, db_session, reviewer_id):
    project, _artifact, _chunk, job = await _project_artifact_chunk_job(factory)
    fact = await factory.create_fact(
        project["id"],
        job["id"],
        schema_path="governance.inducement",
        value="Council resolution adopted",
        review_status="pending",
        with_source_refs=False,
    )
    await db_session.commit()

    service = FactService(db_session)
    with pytest.raises(ValueError, match="source evidence"):
        await service.approve_fact(UUID(fact["id"]), UUID(reviewer_id))


async def test_reviewed_fact_source_association_cannot_be_deleted_silently(factory, db_session, reviewer_id):
    project, _artifact, chunk, job = await _project_artifact_chunk_job(factory)
    fact = await factory.create_fact(
        project["id"],
        job["id"],
        schema_path="governance.inducement",
        value="Council resolution adopted",
        review_status="pending",
        with_source_refs=False,
    )
    db_session.add(FactChunkAssociation(fact_id=fact["id"], chunk_id=chunk["id"]))
    await db_session.commit()

    service = FactService(db_session)
    await service.approve_fact(UUID(fact["id"]), UUID(reviewer_id))

    model = await service.get_fact(UUID(fact["id"]))
    await db_session.delete(model.source_chunks[0])
    with pytest.raises(ValueError, match="Cannot mutate provenance"):
        await db_session.commit()


async def test_reviewed_fact_chunk_content_cannot_be_overwritten_silently(factory, db_session, reviewer_id):
    project, _artifact, chunk, job = await _project_artifact_chunk_job(factory)
    fact = await factory.create_fact(
        project["id"],
        job["id"],
        schema_path="governance.inducement",
        value="Council resolution adopted",
        review_status="pending",
        with_source_refs=False,
    )
    db_session.add(FactChunkAssociation(fact_id=fact["id"], chunk_id=chunk["id"])
    )
    await db_session.commit()

    service = FactService(db_session)
    await service.approve_fact(UUID(fact["id"]), UUID(reviewer_id))

    model = await service.get_fact(UUID(fact["id"]))
    cited_chunk = model.source_chunks[0].chunk
    cited_chunk.text_content = "Overwritten evidence text"
    with pytest.raises(ValueError, match="Cannot mutate provenance"):
        await db_session.commit()


async def test_evidence_index_export_includes_advisor_review_provenance(factory, db_session, reviewer_id):
    project, artifact, chunk, job = await _project_artifact_chunk_job(factory)
    fact = await factory.create_fact(
        project["id"],
        job["id"],
        schema_path="governance.inducement",
        value="Council resolution adopted",
        review_status="pending",
        with_source_refs=False,
    )
    db_session.add(
        FactChunkAssociation(
            fact_id=fact["id"],
            chunk_id=chunk["id"],
            excerpt="approved by council resolution",
        )
    )
    await db_session.commit()

    fact_service = FactService(db_session)
    await fact_service.approve_fact(UUID(fact["id"]), UUID(reviewer_id))
    approved_facts = await fact_service.get_active_approved_facts(UUID(project["id"]))

    section = await DeliverableService(db_session)._generate_evidence_index(
        {"facts": approved_facts}
    )

    assert "Advisor Review Provenance" in section.content
    assert "source_agreement.pdf" in section.content
    assert str(artifact["id"]) in section.content
    assert str(chunk["id"]) in section.content
    assert "Page 7" in section.content
    assert "approved by council resolution" in section.content
