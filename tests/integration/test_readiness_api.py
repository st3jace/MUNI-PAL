"""
Integration tests for Readiness API endpoints.

Per spec: Readiness scoring is DETERMINISTIC on a 0-10 scale.
Tests scoring computation, gap analysis, and dimension details.
"""

from uuid import uuid4

import pytest


class TestReadinessAPI:
    """Test suite for Readiness API."""

    @pytest.fixture
    async def project_with_approved_facts(self, factory, db_session):
        """Create project with approved facts for readiness scoring."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        # Create approved facts covering various schema paths
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.name",
            value="Test Project",
            review_status="approved",
            criticality="critical",
            confidence_score=0.95,
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.location",
            value="Test City",
            review_status="approved",
            criticality="material",
            confidence_score=0.90,
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=50000000.0,
            review_status="approved",
            criticality="critical",
            confidence_score=0.92,
        )

        await db_session.commit()

        return {
            "project": project,
            "playbook": playbook,
        }

    async def test_get_readiness_assessment(self, test_client, project_with_approved_facts, auth_headers):
        """Test getting full readiness assessment."""
        project_id = project_with_approved_facts["project"]["id"]

        response = await test_client.get(f"/api/v1/readiness/{project_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert "recommendation" in data
        assert "dimensions" in data
        assert 0 <= data["overall_score"] <= 10

    async def test_readiness_assessment_includes_dimensions(self, test_client, project_with_approved_facts, auth_headers):
        """Test that assessment includes all 6 dimensions."""
        project_id = project_with_approved_facts["project"]["id"]

        response = await test_client.get(f"/api/v1/readiness/{project_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should have 6 dimensions per spec
        dimensions = data["dimensions"]
        expected_dimensions = [
            "issuer_authority",
            "project_tech",
            "revenue_feedstock",
            "cab_financial",
            "risk_security_slb",
            "slb_verification",
        ]

        for dim in expected_dimensions:
            assert dim in dimensions
            assert "score" in dimensions[dim]
            assert "weight" in dimensions[dim]
            assert 0 <= dimensions[dim]["score"] <= 5

    async def test_get_readiness_gaps(self, test_client, project_with_approved_facts, auth_headers):
        """Test getting readiness gap report."""
        project_id = project_with_approved_facts["project"]["id"]

        response = await test_client.get(f"/api/v1/readiness/{project_id}/gaps", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "critical_gaps" in data
        assert "material_gaps" in data
        assert "priority_actions" in data

    async def test_get_readiness_explanation_handles_string_dimension_keys(self, test_client, project_with_approved_facts, auth_headers):
        """Readiness explanation should not crash when assessment dimension keys are strings."""
        project_id = project_with_approved_facts["project"]["id"]

        response = await test_client.get(
            f"/api/v1/readiness/explanation?project_id={project_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "dimension_explanations" in data
        assert "recommendation_rationale" in data
        assert data["dimension_explanations"]
        assert all(isinstance(key, str) for key in data["dimension_explanations"].keys())


    async def test_get_dimension_detail(self, test_client, project_with_approved_facts, auth_headers):
        """Test getting detail for a specific dimension."""
        project_id = project_with_approved_facts["project"]["id"]

        response = await test_client.get(
            f"/api/v1/readiness/{project_id}/dimensions/project_tech",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dimension"] == "project_tech"
        assert "score" in data
        assert "weight" in data
        assert "explanation" in data

    async def test_get_invalid_dimension(self, test_client, project_with_approved_facts, auth_headers):
        """Test getting invalid dimension returns 404."""
        project_id = project_with_approved_facts["project"]["id"]

        response = await test_client.get(
            f"/api/v1/readiness/{project_id}/dimensions/invalid_dimension",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_readiness_nonexistent_project(self, test_client, auth_headers):
        """Test readiness for nonexistent project returns 404."""
        response = await test_client.get(f"/api/v1/readiness/{uuid4()}", headers=auth_headers)

        assert response.status_code == 404

    async def test_readiness_recommendation_thresholds(self, test_client, project_with_approved_facts, auth_headers):
        """Test that recommendation matches score thresholds."""
        project_id = project_with_approved_facts["project"]["id"]

        response = await test_client.get(f"/api/v1/readiness/{project_id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        score = data["overall_score"]
        recommendation = data["recommendation"]

        # Per spec thresholds:
        # 0.0-3.0: Not Yet Viable
        # 3.0-5.5: Structurally Viable
        # 5.5-7.5: Ready for Selective Engagement
        # 7.5-10.0: Ready for Broad Market

        if score < 3.0:
            assert recommendation == "Not Yet Viable"
        elif score < 5.5:
            assert recommendation == "Structurally Viable"
        elif score < 7.5:
            assert recommendation == "Ready for Selective Engagement"
        else:
            assert recommendation == "Ready for Broad Market"
