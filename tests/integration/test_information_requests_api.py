"""
Integration tests for Information Requests API endpoints.
"""

from uuid import uuid4

import pytest

class TestInformationRequestsAPI:
    """Test suite for Information Requests API."""

    @pytest.fixture
    async def setup_project(self, factory, db_session):
        """Create a project fixture for information-request tests."""
        playbook = await factory.create_playbook(is_default=True)
        project = await factory.create_project(playbook["id"])
        await db_session.commit()
        return project

    async def test_generate_information_requests(self, test_client, setup_project, auth_headers):
        """Generate requests from gap analysis for an existing project."""
        response = await test_client.post(
            "/api/v1/information-requests/generate",
            params={"project_id": setup_project["id"]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        payload = response.json()
        assert "generated_count" in payload
        assert "requests" in payload
        assert payload["generated_count"] == len(payload["requests"])

    async def test_generate_information_requests_missing_project_returns_404(self, test_client, auth_headers):
        """Generate endpoint should reject unknown project IDs."""
        missing_project_id = str(uuid4())
        response = await test_client.post(
            "/api/v1/information-requests/generate",
            params={"project_id": missing_project_id},
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == f"Project {missing_project_id} not found"

    async def test_list_information_requests_missing_project_returns_404(self, test_client, auth_headers):
        """List endpoint should reject unknown project IDs."""
        missing_project_id = str(uuid4())
        response = await test_client.get(
            "/api/v1/information-requests/",
            params={"project_id": missing_project_id},
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == f"Project {missing_project_id} not found"

    async def test_report_missing_project_returns_404(self, test_client, auth_headers):
        """Report endpoint should reject unknown project IDs."""
        missing_project_id = str(uuid4())
        response = await test_client.get(
            f"/api/v1/information-requests/report/{missing_project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == f"Project {missing_project_id} not found"

    async def test_overdue_missing_project_returns_404(self, test_client, auth_headers):
        """Overdue endpoint should reject unknown project IDs."""
        missing_project_id = str(uuid4())
        response = await test_client.get(
            f"/api/v1/information-requests/overdue/{missing_project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == f"Project {missing_project_id} not found"
