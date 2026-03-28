"""
Integration tests for Checklist API endpoints.

Per spec: ChecklistItem status is COMPUTED from linked facts.
Tests phase summaries, item status, and gap analysis.
"""

from uuid import uuid4

import pytest


class TestChecklistAPI:
    """Test suite for Checklist API."""

    @pytest.fixture
    async def project_with_checklist_data(self, factory, db_session):
        """Create project with facts that affect checklist status."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        # Create approved facts for checklist items
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.name",
            value="Test Project",
            review_status="approved",
            criticality="critical",
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.location",
            value="Test City",
            review_status="pending",
            criticality="material",
        )

        await db_session.commit()

        return {
            "project": project,
            "playbook": playbook,
        }

    async def test_list_checklist_items(self, test_client, project_with_checklist_data, auth_headers):
        """Test listing checklist items for a project."""
        project_id = project_with_checklist_data["project"]["id"]

        response = await test_client.get(
            f"/api/v1/checklist/?project_id={project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "checklist_items" in data
        assert "total" in data

    async def test_list_checklist_items_filter_by_phase(self, test_client, project_with_checklist_data, auth_headers):
        """Test filtering checklist items by phase."""
        project_id = project_with_checklist_data["project"]["id"]

        response = await test_client.get(
            f"/api/v1/checklist/?project_id={project_id}&phase=P1",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["phase"] == "P1"

    async def test_list_checklist_items_filter_by_status(self, test_client, project_with_checklist_data, auth_headers):
        """Test filtering checklist items by computed status."""
        project_id = project_with_checklist_data["project"]["id"]

        response = await test_client.get(
            f"/api/v1/checklist/?project_id={project_id}&status_filter=not_started",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filters"]["status"] == "not_started"

    async def test_get_checklist_definitions(self, test_client, project_with_checklist_data, auth_headers):
        """Test listing checklist item definitions from playbook."""
        response = await test_client.get("/api/v1/checklist/definitions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "item_code" in data[0]
            assert "phase" in data[0]
            assert "title" in data[0]

    async def test_get_checklist_summary(self, test_client, project_with_checklist_data, auth_headers):
        """Test getting checklist summary by phase."""
        project_id = project_with_checklist_data["project"]["id"]

        response = await test_client.get(
            f"/api/v1/checklist/summary?project_id={project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # Should have summaries for P1-P6 phases
        expected_phases = ["P1", "P2", "P3", "P4", "P5", "P6"]
        for phase in expected_phases:
            if phase in data:
                assert "total_items" in data[phase]
                assert "ready_count" in data[phase]

    async def test_get_project_gaps(self, test_client, project_with_checklist_data, auth_headers):
        """Test getting comprehensive project gap analysis."""
        project_id = project_with_checklist_data["project"]["id"]

        response = await test_client.get(
            f"/api/v1/checklist/gaps?project_id={project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "by_phase" in data
        assert "critical_missing" in data
        assert "total_missing_paths" in data

    async def test_get_single_checklist_item(self, test_client, factory, db_session, auth_headers):
        """Test getting a specific checklist item with computed status."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        await db_session.commit()

        # Use a canonical playbook item code
        response = await test_client.get(
            f"/api/v1/checklist/P1.1?project_id={project['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["item_code"] == "P1.1"
        assert "status" in data

    async def test_get_nonexistent_checklist_item(self, test_client, factory, db_session, auth_headers):
        """Test getting nonexistent checklist item returns 404."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        await db_session.commit()

        response = await test_client.get(
            f"/api/v1/checklist/NONEXISTENT-001?project_id={project['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_checklist_item_gaps(self, test_client, factory, db_session, auth_headers):
        """Test getting gaps for a specific checklist item."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        await db_session.commit()

        response = await test_client.get(
            f"/api/v1/checklist/P1.1/gaps?project_id={project['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "missing_paths" in data or "gaps" in data or "required_paths" in data

    async def test_get_checklist_item_facts(self, test_client, project_with_checklist_data, auth_headers):
        """Test getting facts relevant to a checklist item."""
        project_id = project_with_checklist_data["project"]["id"]

        response = await test_client.get(
            f"/api/v1/checklist/P1.1/facts?project_id={project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_phase_summary(self, test_client, project_with_checklist_data, auth_headers):
        """Test getting detailed summary for a specific phase."""
        project_id = project_with_checklist_data["project"]["id"]

        response = await test_client.get(
            f"/api/v1/checklist/phase/P1?project_id={project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "phase" in data or "total_items" in data

    async def test_list_phase_items(self, test_client, project_with_checklist_data, auth_headers):
        """Test listing all items in a phase with computed status."""
        project_id = project_with_checklist_data["project"]["id"]

        response = await test_client.get(
            f"/api/v1/checklist/phase/P1/items?project_id={project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
