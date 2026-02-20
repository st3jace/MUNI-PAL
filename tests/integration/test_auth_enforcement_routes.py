"""
Integration checks for SEC-002 route-level auth enforcement.
"""

from uuid import uuid4

import pytest

from munipal.config import get_settings


@pytest.fixture(autouse=True)
def enable_auth_enforcement(monkeypatch: pytest.MonkeyPatch):
    """Enable enforced auth for this module."""
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/facts/",
        "/api/v1/readiness/",
        "/api/v1/checklist/",
        "/api/v1/deliverables/",
        "/api/v1/disclosure/",
        "/api/v1/information-requests/",
        "/api/v1/advisory-packages/internal/",
    ],
)
async def test_sec002_route_groups_require_auth_without_bearer_token(test_client, path: str):
    response = await test_client.get(path, params={"project_id": str(uuid4())})
    assert response.status_code == 401
    payload = response.json()
    assert payload["detail"] == "Missing bearer token"
