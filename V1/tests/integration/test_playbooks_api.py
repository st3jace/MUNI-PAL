"""
Integration tests for Playbooks API endpoints.

Tests playbook listing, retrieval, and schema path queries.
"""

from uuid import uuid4

import pytest


class TestPlaybooksAPI:
    """Test suite for Playbooks API."""

    @pytest.fixture
    async def playbooks(self, factory, db_session):
        """Create multiple playbooks for testing."""
        playbooks = []
        playbooks.append(await factory.create_playbook(
            name="Default Playbook",
            version="1.0.0",
            is_default=True,
            is_active=True,
        ))
        playbooks.append(await factory.create_playbook(
            name="Secondary Playbook",
            version="2.0.0",
            is_default=False,
            is_active=True,
        ))
        playbooks.append(await factory.create_playbook(
            name="Inactive Playbook",
            version="0.9.0",
            is_default=False,
            is_active=False,
        ))
        await db_session.commit()
        return playbooks

    async def test_list_playbooks(self, test_client, playbooks):
        """Test listing all active playbooks."""
        response = await test_client.get("/api/v1/playbooks/")

        assert response.status_code == 200
        data = response.json()
        # Should only return active playbooks
        assert len(data["playbooks"]) == 2
        assert all(p["is_active"] for p in data["playbooks"])

    async def test_list_playbooks_include_inactive(self, test_client, playbooks):
        """Test listing all playbooks including inactive."""
        response = await test_client.get("/api/v1/playbooks/?include_inactive=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data["playbooks"]) == 3

    async def test_get_playbook(self, test_client, playbooks):
        """Test retrieving a playbook by ID."""
        playbook = playbooks[0]

        response = await test_client.get(f"/api/v1/playbooks/{playbook['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == playbook["id"]
        assert data["name"] == playbook["name"]
        assert "schema_paths" in data
        assert "checklist_items" in data

    async def test_get_nonexistent_playbook(self, test_client):
        """Test retrieving nonexistent playbook returns 404."""
        response = await test_client.get(f"/api/v1/playbooks/{uuid4()}")

        assert response.status_code == 404

    async def test_get_default_playbook(self, test_client, playbooks):
        """Test retrieving the default playbook."""
        response = await test_client.get("/api/v1/playbooks/default")

        assert response.status_code == 200
        data = response.json()
        assert data["is_default"] is True
        assert data["name"] == "Default Playbook"

    async def test_get_schema_paths(self, test_client, playbooks):
        """Test retrieving schema paths from a playbook."""
        playbook = playbooks[0]

        response = await test_client.get(f"/api/v1/playbooks/{playbook['id']}/schema-paths")

        assert response.status_code == 200
        data = response.json()
        assert "schema_paths" in data
        assert len(data["schema_paths"]) > 0

    async def test_get_schema_paths_by_criticality(self, test_client, playbooks):
        """Test filtering schema paths by criticality."""
        playbook = playbooks[0]

        response = await test_client.get(
            f"/api/v1/playbooks/{playbook['id']}/schema-paths?criticality=critical"
        )

        assert response.status_code == 200
        data = response.json()
        # All returned paths should be critical
        assert all(
            p.get("criticality") == "critical"
            for p in data["schema_paths"].values()
        )

    async def test_get_checklist_definitions(self, test_client, playbooks):
        """Test retrieving checklist item definitions."""
        playbook = playbooks[0]

        response = await test_client.get(f"/api/v1/playbooks/{playbook['id']}/checklist-items")

        assert response.status_code == 200
        data = response.json()
        assert "checklist_items" in data
        assert len(data["checklist_items"]) > 0
