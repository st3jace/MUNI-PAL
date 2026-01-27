"""
Integration tests for Projects API endpoints.
"""

from uuid import uuid4

import pytest


class TestProjectsAPI:
    """Test suite for Projects API."""

    @pytest.fixture
    async def setup_playbook(self, factory, db_session):
        """Create a default playbook for project tests."""
        playbook = await factory.create_playbook(is_default=True)
        await db_session.commit()
        return playbook

    async def test_create_project(self, test_client, setup_playbook):
        """Test creating a new project."""
        response = await test_client.post(
            "/api/v1/projects/",
            json={
                "name": "New Municipal Project",
                "description": "A test project",
                "issuer_name": "City of Test",
                "project_location": "Test City, TX",
                "target_bond_amount": 25000000.0,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Municipal Project"
        assert data["issuer_name"] == "City of Test"
        assert "id" in data
        assert data["playbook_id"] == setup_playbook["id"]

    async def test_create_project_with_playbook(self, test_client, setup_playbook):
        """Test creating a project with explicit playbook."""
        response = await test_client.post(
            "/api/v1/projects/",
            json={
                "name": "Project with Playbook",
                "issuer_name": "Issuer",
                "playbook_id": setup_playbook["id"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["playbook_id"] == setup_playbook["id"]

    async def test_create_project_minimal(self, test_client, setup_playbook):
        """Test creating a project with minimal required fields."""
        response = await test_client.post(
            "/api/v1/projects/",
            json={
                "name": "Minimal Project",
                "issuer_name": "Issuer",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Project"

    async def test_create_project_invalid_playbook(self, test_client, setup_playbook):
        """Test creating a project with invalid playbook returns error."""
        response = await test_client.post(
            "/api/v1/projects/",
            json={
                "name": "Project",
                "issuer_name": "Issuer",
                "playbook_id": str(uuid4()),  # Non-existent
            },
        )

        assert response.status_code == 404

    async def test_get_project(self, test_client, factory, db_session):
        """Test retrieving a project by ID."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        await db_session.commit()

        response = await test_client.get(f"/api/v1/projects/{project['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project["id"]
        assert data["name"] == project["name"]

    async def test_get_nonexistent_project(self, test_client):
        """Test retrieving nonexistent project returns 404."""
        response = await test_client.get(f"/api/v1/projects/{uuid4()}")

        assert response.status_code == 404

    async def test_list_projects(self, test_client, factory, db_session):
        """Test listing projects."""
        playbook = await factory.create_playbook()
        for i in range(3):
            await factory.create_project(playbook["id"], name=f"Project {i}")
        await db_session.commit()

        response = await test_client.get("/api/v1/projects/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["projects"]) == 3

    async def test_list_projects_pagination(self, test_client, factory, db_session):
        """Test listing projects with pagination."""
        playbook = await factory.create_playbook()
        for i in range(5):
            await factory.create_project(playbook["id"], name=f"Project {i}")
        await db_session.commit()

        response = await test_client.get("/api/v1/projects/?limit=2&skip=0")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["projects"]) == 2

    async def test_update_project(self, test_client, factory, db_session):
        """Test updating a project."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        await db_session.commit()

        response = await test_client.patch(
            f"/api/v1/projects/{project['id']}",
            json={
                "name": "Updated Name",
                "description": "Updated description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    async def test_update_nonexistent_project(self, test_client):
        """Test updating nonexistent project returns 404."""
        response = await test_client.patch(
            f"/api/v1/projects/{uuid4()}",
            json={"name": "New Name"},
        )

        assert response.status_code == 404

    async def test_delete_project(self, test_client, factory, db_session):
        """Test deleting a project."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        await db_session.commit()

        response = await test_client.delete(f"/api/v1/projects/{project['id']}")

        assert response.status_code == 204

        # Verify deletion
        get_response = await test_client.get(f"/api/v1/projects/{project['id']}")
        assert get_response.status_code == 404

    async def test_delete_nonexistent_project(self, test_client):
        """Test deleting nonexistent project returns 404."""
        response = await test_client.delete(f"/api/v1/projects/{uuid4()}")

        assert response.status_code == 404
