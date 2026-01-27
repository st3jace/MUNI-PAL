"""
Integration tests for Facts API endpoints.

Per spec: ExtractedFact is THE CORE PRIMITIVE - tests review workflow and queries.
"""

from uuid import uuid4

import pytest


class TestFactsAPI:
    """Test suite for Facts API."""

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
