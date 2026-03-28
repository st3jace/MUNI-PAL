"""
Integration tests for Facts API endpoints.

Per spec: ExtractedFact is THE CORE PRIMITIVE - tests review workflow and queries.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from munipal.core.schemas.base import ReviewStatus
from munipal.core.schemas.fact import FactLifecycleState
from munipal.services.fact_service import FactService


class TestFactsAPI:
    """Test suite for Facts API."""

    @pytest.fixture(autouse=True)
    def _use_jwt_auth_headers(self, test_client, auth_headers):
        """Run this suite against JWT-enforced auth without per-request boilerplate."""
        test_client.headers.update(auth_headers)
        yield
        test_client.headers.pop("Authorization", None)

    @pytest.fixture
    async def project_with_facts(self, factory, db_session):
        """Create project with facts for testing."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        facts = []
        for path, value, status, conf in [
            ("project.name", "Test Project", "pending", 0.95),
            ("capital.project-cost", 50000000.0, "approved", 0.90),
            ("project.location", "Test City", "pending", 0.85),
            ("revenue.annual", 5000000.0, "rejected", 0.80),
        ]:
            fact = await factory.create_fact(
                project["id"],
                job["id"],
                schema_path=path,
                value=value,
                review_status=status,
                confidence_score=conf,
            )
            facts.append(fact)

        await db_session.commit()

        return {
            "project": project,
            "facts": facts,
        }

    async def _seed_replay_project(
        self,
        db_session,
        factory,
        dataset_rows: dict[str, dict],
        insertion_order: list[str],
    ) -> str:
        """Seed one replay project with deterministic timestamps/lifecycle."""
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

        service = FactService(db_session)
        for row_key, row in dataset_rows.items():
            fact = await service.get_fact(UUID(row_to_fact_id[row_key]))
            assert fact is not None
            fact.created_at = row["created_at"]
            fact.review_status = row["review_status"]
            if row["lifecycle_state"] == FactLifecycleState.ARCHIVED.value:
                fact.lifecycle_state = FactLifecycleState.ARCHIVED.value
                fact.archive_reason_code = "duplicate_exact"
                fact.archive_note = "Seeded archived row for integration replay test."
                fact.archived_at = row["created_at"]
            elif row["lifecycle_state"] == FactLifecycleState.REJECTED.value:
                fact.lifecycle_state = FactLifecycleState.REJECTED.value
            else:
                fact.lifecycle_state = row["lifecycle_state"]
        await db_session.commit()

        await service.refresh_canonicalization_for_project(
            project["id"],
            actor_id="system",
            reason="api_replay_seed",
            source_action="integration_test_dataset_replay",
        )
        await db_session.commit()

        return project["id"]

    async def _facts_snapshot_via_api(self, test_client, project_id: str) -> dict[str, dict]:
        """Collect normalized facts snapshot using API responses."""
        response = await test_client.get(
            f"/api/v1/facts/?project_id={project_id}&include_archived=true&limit=500"
        )
        assert response.status_code == 200
        payload = response.json()
        snapshot: dict[str, dict] = {}
        for item in payload["facts"]:
            path_snapshot = snapshot.setdefault(
                item["schema_path"],
                {"fact_count": 0, "canonical_values": [], "facts": []},
            )
            path_snapshot["fact_count"] += 1
            if item["is_canonical"]:
                path_snapshot["canonical_values"].append(str(item["value"]))
            path_snapshot["facts"].append(
                {
                    "value": str(item["value"]),
                    "review_status": item["review_status"],
                    "lifecycle_state": item["lifecycle_state"],
                    "duplicate_classification": item["duplicate_classification"],
                    "is_canonical": item["is_canonical"],
                }
            )
        for path_snapshot in snapshot.values():
            path_snapshot["canonical_values"].sort()
            path_snapshot["facts"].sort(
                key=lambda item: (
                    item["value"],
                    item["review_status"],
                    item["lifecycle_state"],
                    item["duplicate_classification"],
                    item["is_canonical"],
                )
            )
        return snapshot

    async def _queue_snapshot_via_api(self, test_client, project_id: str) -> list[dict]:
        """Collect normalized conflict queue signature."""
        response = await test_client.get(
            f"/api/v1/facts/conflicts/queue?project_id={project_id}&max_age_days=0"
        )
        assert response.status_code == 200
        queue = []
        for item in response.json()["queue"]:
            queue.append(
                {
                    "queue_type": item["queue_type"],
                    "schema_path": item["schema_path"],
                    "criticality": item.get("criticality"),
                    "phase": item.get("phase"),
                    "fact_count": item.get("fact_count"),
                    "oldest_pending_days": item.get("oldest_pending_days"),
                }
            )
        queue.sort(
            key=lambda item: (
                item["queue_type"],
                item["schema_path"],
                item["oldest_pending_days"] or 0,
            )
        )
        return queue

    # -------------------------------------------------------------------------
    # List and Query Tests
    # -------------------------------------------------------------------------

    async def test_list_facts(self, test_client, project_with_facts):
        """Test listing facts for a project."""
        project_id = project_with_facts["project"]["id"]

        response = await test_client.get(
            f"/api/v1/facts/?project_id={project_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["facts"]) == 4

    async def test_list_facts_filter_by_status(self, test_client, project_with_facts):
        """Test filtering facts by review status."""
        project_id = project_with_facts["project"]["id"]

        response = await test_client.get(
            f"/api/v1/facts/?project_id={project_id}&status=pending"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(f["review_status"] == "pending" for f in data["facts"])

    async def test_list_facts_filter_by_path_prefix(self, test_client, project_with_facts):
        """Test filtering facts by schema path prefix."""
        project_id = project_with_facts["project"]["id"]

        response = await test_client.get(
            f"/api/v1/facts/?project_id={project_id}&schema_path_prefix=project."
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(f["schema_path"].startswith("project.") for f in data["facts"])

    async def test_list_facts_filter_by_min_confidence(self, test_client, project_with_facts):
        """Test filtering facts by minimum confidence."""
        project_id = project_with_facts["project"]["id"]

        response = await test_client.get(
            f"/api/v1/facts/?project_id={project_id}&min_confidence=0.90"
        )

        assert response.status_code == 200
        data = response.json()
        assert all(f["confidence_score"] >= 0.90 for f in data["facts"])

    async def test_list_facts_pagination(self, test_client, project_with_facts):
        """Test facts pagination."""
        project_id = project_with_facts["project"]["id"]

        response = await test_client.get(
            f"/api/v1/facts/?project_id={project_id}&limit=2&offset=0"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["facts"]) == 2

    async def test_get_fact(self, test_client, project_with_facts):
        """Test retrieving a fact by ID."""
        fact = project_with_facts["facts"][0]

        response = await test_client.get(f"/api/v1/facts/{fact['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == fact["id"]
        assert data["schema_path"] == fact["schema_path"]

    async def test_get_nonexistent_fact(self, test_client):
        """Test retrieving nonexistent fact returns 404."""
        response = await test_client.get(f"/api/v1/facts/{uuid4()}")

        assert response.status_code == 404

    async def test_get_review_status_counts(self, test_client, project_with_facts):
        """Test getting review status counts."""
        project_id = project_with_facts["project"]["id"]

        response = await test_client.get(
            f"/api/v1/facts/status-counts?project_id={project_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["pending"] == 2
        assert data["approved"] == 1
        assert data["rejected"] == 1

    # -------------------------------------------------------------------------
    # Review Workflow Tests
    # -------------------------------------------------------------------------

    async def test_approve_fact(self, test_client, project_with_facts):
        """Test approving a fact."""
        fact = project_with_facts["facts"][0]  # pending fact

        response = await test_client.post(
            f"/api/v1/facts/{fact['id']}/review",
            json={
                "action": "approved",
                "note": "Verified against source document",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["review_status"] == "approved"
        assert data["review_note"] == "Verified against source document"

    async def test_approve_fact_with_correction(self, test_client, project_with_facts):
        """Test approving a fact with corrected value."""
        fact = project_with_facts["facts"][0]  # pending fact

        response = await test_client.post(
            f"/api/v1/facts/{fact['id']}/review",
            json={
                "action": "approved",
                "corrected_value": "Corrected Value",
                "note": "Fixed typo in extracted value",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["review_status"] == "approved"
        assert data["value"] == "Corrected Value"
        assert data["original_value"] == fact["value"]

    async def test_reject_fact(self, test_client, project_with_facts):
        """Test rejecting a fact."""
        fact = project_with_facts["facts"][0]  # pending fact

        response = await test_client.post(
            f"/api/v1/facts/{fact['id']}/review",
            json={
                "action": "rejected",
                "note": "Incorrect extraction",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["review_status"] == "rejected"

    async def test_request_revision(self, test_client, project_with_facts):
        """Test flagging fact for revision."""
        fact = project_with_facts["facts"][0]  # pending fact

        response = await test_client.post(
            f"/api/v1/facts/{fact['id']}/review",
            json={
                "action": "needs_revision",
                "note": "Please verify the amount",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["review_status"] == "needs_revision"

    async def test_archive_and_unarchive_fact(self, test_client, project_with_facts):
        """Test archive/unarchive lifecycle endpoints."""
        fact = project_with_facts["facts"][0]
        project_id = project_with_facts["project"]["id"]

        archive_response = await test_client.post(
            f"/api/v1/facts/{fact['id']}/archive",
            json={
                "reason_code": "duplicate_exact",
                "note": "Archived as redundant source copy",
            },
        )
        assert archive_response.status_code == 200
        archived = archive_response.json()
        assert archived["lifecycle_state"] == "archived"
        assert archived["archive_reason_code"] == "duplicate_exact"

        list_default = await test_client.get(f"/api/v1/facts/?project_id={project_id}")
        assert list_default.status_code == 200
        assert list_default.json()["total"] == 3

        list_with_archived = await test_client.get(
            f"/api/v1/facts/?project_id={project_id}&include_archived=true"
        )
        assert list_with_archived.status_code == 200
        assert list_with_archived.json()["total"] == 4

        unarchive_response = await test_client.post(
            f"/api/v1/facts/{fact['id']}/unarchive",
            json={"note": "Restoring for comparison"},
        )
        assert unarchive_response.status_code == 200
        restored = unarchive_response.json()
        assert restored["lifecycle_state"] in {"active", "pending_review"}
        assert restored["archive_reason_code"] is None

    async def test_review_nonexistent_fact(self, test_client):
        """Test reviewing nonexistent fact returns 404."""
        response = await test_client.post(
            f"/api/v1/facts/{uuid4()}/review",
            json={
                "action": "approved",
            },
        )

        assert response.status_code == 404

    # -------------------------------------------------------------------------
    # Revision History Tests
    # -------------------------------------------------------------------------

    async def test_get_revisions(self, test_client, project_with_facts):
        """Test getting revision history for a fact."""
        fact = project_with_facts["facts"][0]

        # First, create a review to generate a revision
        await test_client.post(
            f"/api/v1/facts/{fact['id']}/review",
            json={"action": "approved"},
        )

        response = await test_client.get(f"/api/v1/facts/{fact['id']}/revisions")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["revision_number"] == 1

    # -------------------------------------------------------------------------
    # Conflict Detection Tests
    # -------------------------------------------------------------------------

    async def test_find_conflicts(self, test_client, factory, db_session):
        """Test finding conflicting facts."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        # Create conflicting facts
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.cost",
            value=50000000.0,
            confidence_score=0.95,
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.cost",
            value=55000000.0,
            confidence_score=0.85,
        )
        await db_session.commit()

        response = await test_client.get(
            f"/api/v1/facts/conflicts/?project_id={project['id']}"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["conflicts"]) == 1
        assert data["conflicts"][0]["schema_path"] == "capital.cost"

    async def test_auto_resolve_conflicts(self, test_client, factory, db_session):
        """Test auto-resolving conflicts."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        # Create conflicting facts
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.cost",
            value=50000000.0,
            confidence_score=0.95,
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.cost",
            value=55000000.0,
            confidence_score=0.85,
        )
        await db_session.commit()

        response = await test_client.post(
            f"/api/v1/facts/conflicts/resolve?project_id={project['id']}&strategy=highest_confidence"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["resolutions"]) == 1

        # Verify no more conflicts
        conflicts_response = await test_client.get(
            f"/api/v1/facts/conflicts/?project_id={project['id']}"
        )
        conflicts_data = conflicts_response.json()
        assert len(conflicts_data["conflicts"]) == 0

    async def test_conflict_queue_endpoint(self, test_client, factory, db_session):
        """Test conflict queue endpoint includes unresolved conflicts/pending items."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.cost",
            value=50000000.0,
            confidence_score=0.95,
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.cost",
            value=55000000.0,
            confidence_score=0.85,
        )
        await db_session.commit()

        response = await test_client.get(
            f"/api/v1/facts/conflicts/queue?project_id={project['id']}&max_age_days=0"
        )
        assert response.status_code == 200
        payload = response.json()
        assert "queue" in payload
        assert any(
            item["queue_type"] in {"conflict", "stale_pending"}
            for item in payload["queue"]
        )

    async def test_replay_dataset_api_outputs_are_order_invariant(
        self,
        test_client,
        factory,
        db_session,
    ):
        """Replay corpus should produce the same API-level canonical/queue outputs."""
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
        first_project_id = await self._seed_replay_project(
            db_session=db_session,
            factory=factory,
            dataset_rows=dataset_rows,
            insertion_order=row_keys,
        )
        second_project_id = await self._seed_replay_project(
            db_session=db_session,
            factory=factory,
            dataset_rows=dataset_rows,
            insertion_order=list(reversed(row_keys)),
        )

        first_facts_snapshot = await self._facts_snapshot_via_api(test_client, first_project_id)
        second_facts_snapshot = await self._facts_snapshot_via_api(test_client, second_project_id)
        assert first_facts_snapshot == second_facts_snapshot

        first_queue_snapshot = await self._queue_snapshot_via_api(test_client, first_project_id)
        second_queue_snapshot = await self._queue_snapshot_via_api(test_client, second_project_id)
        assert first_queue_snapshot == second_queue_snapshot
