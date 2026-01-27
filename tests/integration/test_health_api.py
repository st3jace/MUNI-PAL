"""
Integration tests for health check endpoints.
"""

import pytest


class TestHealthEndpoints:
    """Test suite for health check API."""

    async def test_health_check(self, test_client):
        """Test health check endpoint returns OK."""
        response = await test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    async def test_root_endpoint(self, test_client):
        """Test root endpoint returns API info."""
        response = await test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Muni-Pal BFMS"
        assert "version" in data
