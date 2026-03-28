"""
Integration tests for Information Requests acknowledge behavior.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt

from munipal.config import get_settings


def _make_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "role": "analyst",
        "exp": datetime.now(UTC) + timedelta(minutes=10),
    }
    return jwt.encode(payload, "test-secret", algorithm="HS256")


@pytest.fixture(autouse=True)
def enable_auth_enforcement(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_ENFORCEMENT_V2", "true")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_acknowledge_request_without_user_override_returns_200(test_client, factory, db_session):
    user_id = str(uuid4())
    playbook = await factory.create_playbook(is_default=True)
    project = await factory.create_project(playbook_id=playbook["id"], owner_id=user_id)
    await db_session.commit()

    token = _make_token(user_id)
    headers = {"Authorization": f"Bearer {token}"}

    generate_response = await test_client.post(
        "/api/v1/information-requests/generate",
        params={"project_id": project["id"]},
        headers=headers,
    )
    assert generate_response.status_code == 200
    generated = generate_response.json()
    assert generated["generated_count"] > 0
    request_id = generated["requests"][0]["id"]

    acknowledge_response = await test_client.post(
        f"/api/v1/information-requests/{request_id}/acknowledge",
        headers=headers,
    )
    assert acknowledge_response.status_code == 200
    payload = acknowledge_response.json()
    assert payload["status"] == "in_progress"
