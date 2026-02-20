"""
Unit tests for FactService.

Tests fact CRUD, review workflow, revision history, and conflict detection.
Per spec: ExtractedFact is THE CORE PRIMITIVE.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from munipal.core.schemas.base import ReviewStatus, CriticalityTier
from munipal.core.schemas.fact import (
    FactDuplicateClassification,
    FactLifecycleState,
    FactReviewRequest,
)
from munipal.services.fact_service import FactService, FactConflictDetector


class TestFactService:
    """Test suite for FactService."""

    @pytest.fixture
    async def service(self, db_session):
        """Provide FactService instance."""
        return FactService(db_session)

    @pytest.fixture
    async def project_with_facts(self, factory, db_session):
        """Create project with facts for testing."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        facts = []
        for i, (path, value, status) in enumerate([
            ("project.name", "Test Project", "pending"),
            ("capital.project-cost", 50000000.0, "approved"),
            ("project.location", "Test City", "pending"),
            ("revenue.annual", 5000000.0, "rejected"),
        ]):
            fact = await factory.create_fact(
                project["id"],
                job["id"],
                schema_path=path,
                value=value,
                review_status=status,
                confidence_score=0.90 - (i * 0.05),
            )
            facts.append(fact)

        await db_session.commit()

        return {
            "project": project,
            "artifact": artifact,
            "job": job,
            "facts": facts,
        }

    async def _seed_replay_corpus_and_snapshot(
        self,
        service: FactService,
        factory,
        db_session,
        dataset_rows: dict[str, dict],
        insertion_order: list[str],
    ) -> dict[str, dict]:
        """Seed one corpus replay run and return a row-key-normalized snapshot."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        row_to_fact_id: dict[str, str] = {}
        for row_key in insertion_order:
            row = dataset_rows[row_key]
            fact = await factory.create_fact(
                project["id"],
                job["id"],
                schema_path=row["schema_path"],
                value=row["value"],
                confidence_score=row["confidence_score"],
                review_status=row["review_status"],
            )
            row_to_fact_id[row_key] = fact["id"]
        await db_session.commit()

        # Normalize time/lifecycle metadata so replay order does not affect outputs.
        for row_key, row in dataset_rows.items():
            fact = await service.get_fact(UUID(row_to_fact_id[row_key]))
            assert fact is not None
            fact.created_at = row["created_at"]
            fact.review_status = row["review_status"]
            if row["lifecycle_state"] == FactLifecycleState.ARCHIVED.value:
                fact.lifecycle_state = FactLifecycleState.ARCHIVED.value
                fact.archive_reason_code = "duplicate_exact"
                fact.archive_note = "Seeded archived row for replay test."
                fact.archived_at = row["created_at"]
            elif row["lifecycle_state"] == FactLifecycleState.REJECTED.value:
                fact.lifecycle_state = FactLifecycleState.REJECTED.value
            else:
                fact.lifecycle_state = row["lifecycle_state"]
        await db_session.commit()

        await service.refresh_canonicalization_for_project(
            UUID(project["id"]),
            actor_id="system",
            reason="dataset_replay_seed",
            source_action="unit_test_dataset_replay",
        )
        await db_session.commit()

        raw_snapshot = await service.canonical_snapshot_for_project(
            UUID(project["id"]),
            include_archived=True,
        )

        id_to_row = {fact_id: row_key for row_key, fact_id in row_to_fact_id.items()}
        normalized_snapshot: dict[str, dict] = {}
        for schema_path, path_snapshot in raw_snapshot.items():
            canonical_pairs = [
                (id_to_row[fact_id], value_hash)
                for fact_id, value_hash in zip(
                    path_snapshot["canonical_fact_ids"],
                    path_snapshot["canonical_value_hashes"],
                    strict=False,
                )
            ]
            canonical_pairs.sort(key=lambda pair: pair[0])
            normalized_snapshot[schema_path] = {
                "fact_count": path_snapshot["fact_count"],
                "canonical_rows": [row_key for row_key, _ in canonical_pairs],
                "canonical_value_hashes": [value_hash for _, value_hash in canonical_pairs],
                "facts": sorted(
                    [
                        {
                            "row_key": id_to_row[item["fact_id"]],
                            "value_hash": item["value_hash"],
                            "review_status": item["review_status"],
                            "lifecycle_state": item["lifecycle_state"],
                            "duplicate_classification": item["duplicate_classification"],
                            "is_canonical": item["is_canonical"],
                        }
                        for item in path_snapshot["facts"]
                    ],
                    key=lambda item: item["row_key"],
                ),
            }

        return normalized_snapshot

    # -------------------------------------------------------------------------
    # Query Tests
    # -------------------------------------------------------------------------

    async def test_get_fact(self, service, project_with_facts):
        """Test retrieving a fact by ID."""
        fact_data = project_with_facts["facts"][0]

        result = await service.get_fact(UUID(fact_data["id"]))

        assert result is not None
        assert result.id == fact_data["id"]
        assert result.schema_path == fact_data["schema_path"]
        assert result.value == fact_data["value"]

    async def test_get_nonexistent_fact(self, service):
        """Test retrieving nonexistent fact returns None."""
        result = await service.get_fact(uuid4())
        assert result is None

    async def test_list_facts(self, service, project_with_facts):
        """Test listing facts for a project."""
        project_id = project_with_facts["project"]["id"]

        facts, total = await service.list_facts(UUID(project_id))

        assert total == 4
        assert len(facts) == 4

    async def test_list_facts_filter_by_status(self, service, project_with_facts):
        """Test filtering facts by review status."""
        project_id = project_with_facts["project"]["id"]

        facts, total = await service.list_facts(
            UUID(project_id),
            status_filter=ReviewStatus.PENDING,
        )

        assert total == 2
        assert all(f.review_status == "pending" for f in facts)

    async def test_list_facts_filter_by_schema_path_prefix(self, service, project_with_facts):
        """Test filtering facts by schema path prefix."""
        project_id = project_with_facts["project"]["id"]

        facts, total = await service.list_facts(
            UUID(project_id),
            schema_path_prefix="project.",
        )

        assert total == 2
        assert all(f.schema_path.startswith("project.") for f in facts)

    async def test_list_facts_filter_by_min_confidence(self, service, project_with_facts):
        """Test filtering facts by minimum confidence."""
        project_id = project_with_facts["project"]["id"]

        facts, total = await service.list_facts(
            UUID(project_id),
            min_confidence=0.85,
        )

        assert all(f.confidence_score >= 0.85 for f in facts)

    async def test_list_facts_pagination(self, service, project_with_facts):
        """Test facts pagination."""
        project_id = project_with_facts["project"]["id"]

        facts, total = await service.list_facts(
            UUID(project_id),
            limit=2,
            offset=0,
        )

        assert total == 4
        assert len(facts) == 2

    async def test_get_facts_by_schema_path(self, service, project_with_facts):
        """Test getting facts by exact schema path."""
        project_id = project_with_facts["project"]["id"]

        facts = await service.get_facts_by_schema_path(
            UUID(project_id),
            "project.name",
        )

        assert len(facts) == 1
        assert facts[0].schema_path == "project.name"

    async def test_get_facts_by_schema_path_approved_only(self, service, project_with_facts):
        """Test getting only approved facts for a schema path."""
        project_id = project_with_facts["project"]["id"]

        # Get all facts for capital.project-cost (which is approved)
        all_facts = await service.get_facts_by_schema_path(
            UUID(project_id),
            "capital.project-cost",
        )
        approved_facts = await service.get_facts_by_schema_path(
            UUID(project_id),
            "capital.project-cost",
            approved_only=True,
        )

        assert len(all_facts) == 1
        assert len(approved_facts) == 1

    async def test_get_pending_review_count(self, service, project_with_facts):
        """Test getting counts by review status."""
        project_id = project_with_facts["project"]["id"]

        counts = await service.get_pending_review_count(UUID(project_id))

        assert counts["pending"] == 2
        assert counts["approved"] == 1
        assert counts["rejected"] == 1
        assert counts["needs_revision"] == 0

    # -------------------------------------------------------------------------
    # Review Workflow Tests
    # -------------------------------------------------------------------------

    async def test_approve_fact(self, service, project_with_facts, reviewer_id, db_session):
        """Test approving a fact."""
        pending_fact = project_with_facts["facts"][0]

        result = await service.approve_fact(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            note="Looks good",
        )

        assert result.review_status == ReviewStatus.APPROVED.value
        assert result.reviewed_by == reviewer_id
        assert result.review_note == "Looks good"
        assert result.reviewed_at is not None

    async def test_approve_fact_with_correction(self, service, project_with_facts, reviewer_id):
        """Test approving a fact with corrected value."""
        pending_fact = project_with_facts["facts"][0]
        original_value = pending_fact["value"]

        result = await service.approve_fact(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            corrected_value="Corrected Project Name",
            note="Fixed typo",
        )

        assert result.review_status == ReviewStatus.APPROVED.value
        assert result.value == "Corrected Project Name"
        assert result.original_value == original_value

    async def test_reject_fact(self, service, project_with_facts, reviewer_id):
        """Test rejecting a fact."""
        pending_fact = project_with_facts["facts"][0]

        result = await service.reject_fact(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            reason="Incorrect extraction",
        )

        assert result.review_status == ReviewStatus.REJECTED.value
        assert result.review_note == "Incorrect extraction"

    async def test_request_revision(self, service, project_with_facts, reviewer_id):
        """Test flagging a fact for revision."""
        pending_fact = project_with_facts["facts"][0]

        result = await service.request_revision(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            revision_note="Please verify against source document",
        )

        assert result.review_status == ReviewStatus.NEEDS_REVISION.value
        assert result.review_note == "Please verify against source document"

    async def test_review_nonexistent_fact_raises(self, service, reviewer_id):
        """Test reviewing nonexistent fact raises error."""
        review = FactReviewRequest(
            action=ReviewStatus.APPROVED,
            note="Test",
        )

        with pytest.raises(ValueError, match="not found"):
            await service.review_fact(uuid4(), UUID(reviewer_id), review)

    async def test_archive_and_unarchive_fact_updates_lifecycle(
        self,
        service,
        factory,
        db_session,
        reviewer_id,
    ):
        """Archive should demote canonical and unarchive should restore active state."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        fact_primary = await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=50000000.0,
            confidence_score=0.95,
            review_status="approved",
        )
        fact_secondary = await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=52000000.0,
            confidence_score=0.80,
            review_status="approved",
        )
        await db_session.commit()

        await service.refresh_canonicalization_for_path(
            UUID(project["id"]),
            "capital.project-cost",
        )
        primary = await service.get_fact(UUID(fact_primary["id"]))
        secondary = await service.get_fact(UUID(fact_secondary["id"]))
        assert primary is not None and secondary is not None
        assert primary.is_canonical or secondary.is_canonical

        archived = await service.archive_fact(
            UUID(fact_primary["id"]),
            UUID(reviewer_id),
            reason_code="superseded_higher_trust_source",
            note="Superseded during review.",
        )
        assert archived.lifecycle_state == FactLifecycleState.ARCHIVED.value
        assert archived.is_canonical is False
        assert archived.archive_reason_code == "superseded_higher_trust_source"

        refreshed_secondary = await service.get_fact(UUID(fact_secondary["id"]))
        assert refreshed_secondary is not None
        assert refreshed_secondary.is_canonical is True

        restored = await service.unarchive_fact(
            UUID(fact_primary["id"]),
            UUID(reviewer_id),
            note="Restoring for comparison.",
        )
        assert restored.lifecycle_state == FactLifecycleState.ACTIVE.value
        assert restored.archive_reason_code is None

    async def test_archive_emits_canonical_promote_demote_audit_events(
        self,
        service,
        factory,
        db_session,
        reviewer_id,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Canonical transitions should emit promote/demote audit events with rationale."""
        events: list[dict] = []

        def fake_emit_event(**kwargs):
            events.append(kwargs)
            return kwargs

        monkeypatch.setattr("munipal.services.fact_service.AuditService.emit_event", fake_emit_event)

        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        fact_one = await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=50000000.0,
            confidence_score=0.95,
            review_status="approved",
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=52000000.0,
            confidence_score=0.80,
            review_status="approved",
        )
        await db_session.commit()

        # Seed canonical status so subsequent archive produces demote/promote pair.
        await service.refresh_canonicalization_for_path(
            UUID(project["id"]),
            "capital.project-cost",
            actor_id=UUID(reviewer_id),
            reason="seed",
            source_action="unit_test_seed",
        )
        await db_session.flush()
        events.clear()

        seeded = await service.get_facts_by_schema_path(
            UUID(project["id"]),
            "capital.project-cost",
            include_archived=True,
        )
        canonical_ids = [fact.id for fact in seeded if fact.is_canonical]
        assert len(canonical_ids) == 1

        await service.archive_fact(
            UUID(canonical_ids[0]),
            UUID(reviewer_id),
            reason_code="duplicate_exact",
            note="Archive canonical for transition test.",
        )

        actions = [event["action"] for event in events]
        assert "demote" in actions
        assert "promote_canonical" in actions

        demote_event = next(event for event in events if event["action"] == "demote")
        promote_event = next(event for event in events if event["action"] == "promote_canonical")
        assert demote_event["actor_id"] == reviewer_id
        assert demote_event["metadata"]["reason"] == "archive:duplicate_exact"
        assert demote_event["metadata"]["source_action"] == "archive_fact"
        assert promote_event["actor_id"] == reviewer_id
        assert promote_event["metadata"]["reason"] == "archive:duplicate_exact"

    async def test_canonical_selection_is_stable_across_refreshes(
        self,
        service,
        factory,
        db_session,
    ):
        """Repeated canonical refresh runs should pick the same fact under identical inputs."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        fact_one = await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=50000000.0,
            confidence_score=0.90,
            review_status="approved",
        )
        fact_two = await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=52000000.0,
            confidence_score=0.90,
            review_status="approved",
        )
        await db_session.commit()

        # Force same timestamp to exercise deterministic tie-break behavior.
        same_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
        first_model = await service.get_fact(UUID(fact_one["id"]))
        second_model = await service.get_fact(UUID(fact_two["id"]))
        assert first_model is not None and second_model is not None
        first_model.created_at = same_time
        second_model.created_at = same_time
        await db_session.commit()

        canonical_ids: list[str] = []
        for _ in range(5):
            await service.refresh_canonicalization_for_path(
                UUID(project["id"]),
                "capital.project-cost",
            )
            refreshed = await service.get_facts_by_schema_path(
                UUID(project["id"]),
                "capital.project-cost",
                include_archived=True,
            )
            canonical = [fact.id for fact in refreshed if fact.is_canonical]
            assert len(canonical) == 1
            canonical_ids.append(canonical[0])

        assert len(set(canonical_ids)) == 1

    async def test_refresh_canonicalization_for_project_is_replay_stable(
        self,
        service,
        project_with_facts,
        db_session,
    ):
        """Project-level replay refresh should keep canonical snapshots stable."""
        project_id = UUID(project_with_facts["project"]["id"])

        refreshed_paths = await service.refresh_canonicalization_for_project(
            project_id,
            actor_id="system",
            reason="project_replay_seed",
            source_action="unit_test_project_replay",
        )
        assert refreshed_paths == sorted(refreshed_paths)
        await db_session.commit()

        baseline_snapshot = await service.canonical_snapshot_for_project(
            project_id,
            include_archived=True,
        )
        for _ in range(3):
            replay_paths = await service.refresh_canonicalization_for_project(
                project_id,
                actor_id="system",
                reason="project_replay_check",
                source_action="unit_test_project_replay",
            )
            assert replay_paths == refreshed_paths
            await db_session.commit()
            replay_snapshot = await service.canonical_snapshot_for_project(
                project_id,
                include_archived=True,
            )
            assert replay_snapshot == baseline_snapshot

    async def test_canonical_replay_dataset_is_order_invariant(
        self,
        service,
        factory,
        db_session,
    ):
        """Canonical outputs should be reproducible across replay ingestion orders."""
        base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        dataset_rows = {
            "cost_primary": {
                "schema_path": "capital.project-cost",
                "value": 50000000.0,
                "confidence_score": 0.95,
                "review_status": ReviewStatus.APPROVED.value,
                "lifecycle_state": FactLifecycleState.ACTIVE.value,
                "created_at": base_time,
            },
            "cost_duplicate": {
                "schema_path": "capital.project-cost",
                "value": 50000000.0,
                "confidence_score": 0.90,
                "review_status": ReviewStatus.APPROVED.value,
                "lifecycle_state": FactLifecycleState.ACTIVE.value,
                "created_at": base_time + timedelta(minutes=1),
            },
            "cost_conflict": {
                "schema_path": "capital.project-cost",
                "value": 54000000.0,
                "confidence_score": 0.91,
                "review_status": ReviewStatus.APPROVED.value,
                "lifecycle_state": FactLifecycleState.ACTIVE.value,
                "created_at": base_time + timedelta(minutes=2),
            },
            "location_primary": {
                "schema_path": "project.location",
                "value": "Long Beach, CA",
                "confidence_score": 0.93,
                "review_status": ReviewStatus.APPROVED.value,
                "lifecycle_state": FactLifecycleState.ACTIVE.value,
                "created_at": base_time + timedelta(minutes=3),
            },
            "location_pending": {
                "schema_path": "project.location",
                "value": "Long Beach",
                "confidence_score": 0.88,
                "review_status": ReviewStatus.PENDING.value,
                "lifecycle_state": FactLifecycleState.PENDING_REVIEW.value,
                "created_at": base_time + timedelta(minutes=4),
            },
            "tenor_archived": {
                "schema_path": "debt.tenor.years",
                "value": 20,
                "confidence_score": 0.96,
                "review_status": ReviewStatus.APPROVED.value,
                "lifecycle_state": FactLifecycleState.ARCHIVED.value,
                "created_at": base_time + timedelta(minutes=5),
            },
            "tenor_active": {
                "schema_path": "debt.tenor.years",
                "value": 22,
                "confidence_score": 0.84,
                "review_status": ReviewStatus.APPROVED.value,
                "lifecycle_state": FactLifecycleState.ACTIVE.value,
                "created_at": base_time + timedelta(minutes=6),
            },
            "pledge_rejected": {
                "schema_path": "security.revenue.pledge",
                "value": "net",
                "confidence_score": 0.92,
                "review_status": ReviewStatus.REJECTED.value,
                "lifecycle_state": FactLifecycleState.REJECTED.value,
                "created_at": base_time + timedelta(minutes=7),
            },
            "pledge_approved": {
                "schema_path": "security.revenue.pledge",
                "value": "gross",
                "confidence_score": 0.85,
                "review_status": ReviewStatus.APPROVED.value,
                "lifecycle_state": FactLifecycleState.ACTIVE.value,
                "created_at": base_time + timedelta(minutes=8),
            },
        }

        row_keys = list(dataset_rows.keys())
        replay_orders = [
            row_keys,
            list(reversed(row_keys)),
            sorted(row_keys, key=lambda key: dataset_rows[key]["schema_path"]),
            row_keys[::2] + row_keys[1::2],
        ]

        snapshots: list[dict[str, dict]] = []
        for order in replay_orders:
            snapshots.append(
                await self._seed_replay_corpus_and_snapshot(
                    service=service,
                    factory=factory,
                    db_session=db_session,
                    dataset_rows=dataset_rows,
                    insertion_order=order,
                )
            )

        baseline = snapshots[0]
        for replay_snapshot in snapshots[1:]:
            assert replay_snapshot == baseline

    async def test_conflict_queue_includes_conflicts_and_stale_pending(
        self,
        service,
        factory,
        db_session,
    ):
        """Conflict queue should return unresolved conflicts and stale pending facts."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=50000000.0,
            confidence_score=0.90,
            review_status="pending",
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=55000000.0,
            confidence_score=0.85,
            review_status="pending",
        )
        stale_fact = await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.location",
            value="Old pending",
            confidence_score=0.70,
            review_status="pending",
        )
        await db_session.commit()

        stale = await service.get_fact(UUID(stale_fact["id"]))
        assert stale is not None
        stale.created_at = stale.created_at.replace(year=stale.created_at.year - 1)
        await db_session.commit()

        queue = await service.get_conflict_queue(UUID(project["id"]), max_age_days=30)
        queue_types = {item["queue_type"] for item in queue}
        assert "conflict" in queue_types
        assert "stale_pending" in queue_types

    # -------------------------------------------------------------------------
    # Revision History Tests
    # -------------------------------------------------------------------------

    async def test_revision_created_on_review(self, service, project_with_facts, reviewer_id):
        """Test that reviewing a fact creates a revision record."""
        pending_fact = project_with_facts["facts"][0]

        await service.approve_fact(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
        )

        revisions = await service.list_revisions(UUID(pending_fact["id"]))

        assert len(revisions) == 1
        assert revisions[0].previous_status == "pending"
        assert revisions[0].new_status == ReviewStatus.APPROVED.value
        assert revisions[0].revision_number == 1

    async def test_multiple_revisions_tracked(self, service, project_with_facts, reviewer_id):
        """Test that multiple reviews create sequential revisions."""
        pending_fact = project_with_facts["facts"][0]

        # First review: request revision
        await service.request_revision(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            revision_note="Need more info",
        )

        # Second review: approve
        await service.approve_fact(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            note="Now looks good",
        )

        revisions = await service.list_revisions(UUID(pending_fact["id"]))

        assert len(revisions) == 2
        assert revisions[0].revision_number == 1
        assert revisions[0].new_status == ReviewStatus.NEEDS_REVISION.value
        assert revisions[1].revision_number == 2
        assert revisions[1].new_status == ReviewStatus.APPROVED.value

    # -------------------------------------------------------------------------
    # Serialization Tests
    # -------------------------------------------------------------------------

    async def test_fact_to_read_schema(self, service, project_with_facts):
        """Test converting fact to read schema."""
        fact_data = project_with_facts["facts"][0]
        fact = await service.get_fact(UUID(fact_data["id"]))
        await service.refresh_canonicalization_for_path(
            UUID(project_with_facts["project"]["id"]),
            fact_data["schema_path"],
        )
        fact = await service.get_fact(UUID(fact_data["id"]))

        schema = service.fact_to_read_schema(fact)

        assert schema.id == UUID(fact_data["id"])
        assert schema.schema_path == fact_data["schema_path"]
        assert schema.value == fact_data["value"]
        assert schema.duplicate_classification in {
            FactDuplicateClassification.UNIQUE,
            FactDuplicateClassification.CANDIDATE_CONFLICT,
        }
        assert schema.lifecycle_state in {
            FactLifecycleState.ACTIVE,
            FactLifecycleState.PENDING_REVIEW,
        }

    async def test_fact_to_summary_schema(self, service, project_with_facts):
        """Test converting fact to summary schema."""
        fact_data = project_with_facts["facts"][0]
        fact = await service.get_fact(UUID(fact_data["id"]))
        await service.refresh_canonicalization_for_path(
            UUID(project_with_facts["project"]["id"]),
            fact_data["schema_path"],
        )
        fact = await service.get_fact(UUID(fact_data["id"]))

        schema = service.fact_to_summary_schema(fact)

        assert schema.id == UUID(fact_data["id"])
        assert schema.schema_path == fact_data["schema_path"]
        assert schema.value == fact_data["value"]
        assert schema.review_status == ReviewStatus.PENDING
        assert isinstance(schema.is_canonical, bool)


class TestFactConflictDetector:
    """Test suite for FactConflictDetector."""

    @pytest.fixture
    async def detector(self, db_session):
        """Provide FactConflictDetector instance."""
        return FactConflictDetector(db_session)

    @pytest.fixture
    async def project_with_conflicts(self, factory, db_session):
        """Create project with conflicting facts."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        # Create conflicting facts for same schema path
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=50000000.0,
            confidence_score=0.95,
            review_status="pending",
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=55000000.0,
            confidence_score=0.85,
            review_status="pending",
        )

        # Non-conflicting fact
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.name",
            value="Test",
            confidence_score=0.90,
            review_status="pending",
        )

        await db_session.commit()

        return project

    async def test_find_conflicts(self, detector, project_with_conflicts):
        """Test finding conflicting facts."""
        conflicts = await detector.find_conflicts(
            UUID(project_with_conflicts["id"])
        )

        assert len(conflicts) == 1
        assert conflicts[0]["schema_path"] == "capital.project-cost"
        assert conflicts[0]["fact_count"] == 2
        assert conflicts[0]["unique_value_count"] == 2

    async def test_find_conflicts_specific_path(self, detector, project_with_conflicts):
        """Test finding conflicts for specific schema path."""
        conflicts = await detector.find_conflicts(
            UUID(project_with_conflicts["id"]),
            schema_path="capital.project-cost",
        )

        assert len(conflicts) == 1

        # Non-existent path
        no_conflicts = await detector.find_conflicts(
            UUID(project_with_conflicts["id"]),
            schema_path="nonexistent.path",
        )

        assert len(no_conflicts) == 0

    async def test_auto_resolve_highest_confidence(self, detector, project_with_conflicts, db_session):
        """Test auto-resolving conflicts with highest confidence strategy."""
        resolutions = await detector.auto_resolve_conflicts(
            UUID(project_with_conflicts["id"]),
            strategy="highest_confidence",
        )

        assert len(resolutions) == 1
        assert resolutions[0]["schema_path"] == "capital.project-cost"
        assert len(resolutions[0]["rejected_ids"]) == 1

        # Verify no more conflicts
        remaining_conflicts = await detector.find_conflicts(
            UUID(project_with_conflicts["id"])
        )
        assert len(remaining_conflicts) == 0

    async def test_auto_resolve_unknown_strategy_raises(self, detector, project_with_conflicts):
        """Test that unknown resolution strategy raises error."""
        with pytest.raises(ValueError, match="Unknown resolution strategy"):
            await detector.auto_resolve_conflicts(
                UUID(project_with_conflicts["id"]),
                strategy="unknown_strategy",
            )

    async def test_no_conflicts_when_values_match(self, factory, detector, db_session):
        """Test that duplicate facts with same value don't count as conflicts."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        # Same value, different confidence
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.name",
            value="Same Value",
            confidence_score=0.95,
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.name",
            value="Same Value",
            confidence_score=0.85,
        )
        await db_session.commit()

        conflicts = await detector.find_conflicts(UUID(project["id"]))

        assert len(conflicts) == 0
