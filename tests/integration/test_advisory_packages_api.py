"""Integration tests for advisory package generation endpoints."""

import pytest


class TestAdvisoryPackagesAPI:
    """Test suite for advisory package API endpoints."""

    @pytest.fixture
    async def project(self, factory, db_session):
        """Create a project fixture for advisory package tests."""
        playbook = await factory.create_playbook(is_default=True)
        project = await factory.create_project(playbook["id"])
        await db_session.commit()
        return project

    async def test_generate_internal_and_external_packages(self, test_client, project, auth_headers):
        """Internal and external generate endpoints return successful responses."""
        internal_response = await test_client.post(
            "/api/v1/advisory-packages/internal/generate",
            json={
                "project_id": project["id"],
                "force_regenerate": False,
            },
            headers=auth_headers,
        )

        assert internal_response.status_code == 200
        internal_payload = internal_response.json()
        assert internal_payload["status"] == "completed"
        assert "report_id" in internal_payload

        external_response = await test_client.post(
            "/api/v1/advisory-packages/external/generate",
            json={
                "project_id": project["id"],
                "title": "Integration Test Package",
                "generated_for": "Municipal Advisor",
                "include_disclosure": True,
                "force_regenerate": False,
            },
            headers=auth_headers,
        )

        assert external_response.status_code == 200
        external_payload = external_response.json()
        assert external_payload["status"] == "completed"
        assert "package_id" in external_payload

        package_response = await test_client.get(
            f"/api/v1/advisory-packages/external/{external_payload['package_id']}",
            headers=auth_headers,
        )

        assert package_response.status_code == 200
        package_payload = package_response.json()
        assert package_payload["id"] == external_payload["package_id"]
        assert "executive_summary" in package_payload
