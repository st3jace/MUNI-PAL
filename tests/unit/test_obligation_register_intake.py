"""Obligation Register intake: the two hard gates hold on the server, and a good intake is stored."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from munipal.api.routes import obligation_register
from munipal.sensing_app import app as sensing_app

URL = "/api/v1/sensing/obligation-register/intake"

GOOD = {
    "bonds_already_closed": True,
    "legal_name": "Saguaro Commons Apartments, LP",
    "entity_type": "private_obligated_person",
    "state": "AZ",
    "contact_name": "Test Controller",
    "contact_title": "Controller",
    "contact_email": "controller@example.com",
    "bond_counsel_contact": "Creosote & Mesa LLP",
    "instrument_list": "Multifamily Housing Revenue Bonds, Series 2025",
    "instrument_count": 1,
    "cda_present": "yes",
    "concurrent_preissuance": False,
    "privacy_consent": True,
    "session_id": "sess-test-1",
}


@pytest.fixture(autouse=True)
def _no_email(monkeypatch):
    async def _noop(*_a, **_k):
        return None

    monkeypatch.setattr(obligation_register, "_notify_team", _noop)


async def test_pre_issuance_is_refused(test_client):
    resp = await test_client.post(URL, json={**GOOD, "bonds_already_closed": False})
    assert resp.status_code == 422
    assert "post-close" in resp.json()["detail"]


async def test_municipal_entity_is_refused(test_client):
    resp = await test_client.post(URL, json={**GOOD, "entity_type": "municipal_entity"})
    assert resp.status_code == 422
    assert "no path" in resp.json()["detail"]


async def test_consent_is_required(test_client):
    resp = await test_client.post(URL, json={**GOOD, "privacy_consent": False})
    assert resp.status_code == 422


async def test_good_intake_is_stored_as_lead(test_client, db_session):
    from munipal.core.models.lead import SensingLead

    resp = await test_client.post(URL, json=GOOD)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "received"
    assert body["flags"] == {
        "entity_unclear": False,
        "concurrent_preissuance": False,
        "no_professional_named": False,
        "workshop_attendee": False,
    }
    # No price, no compliance word, anywhere in what the prospect sees.
    assert "$" not in json.dumps(body)
    assert "compliant" not in json.dumps(body).lower()

    lead = (await db_session.execute(select(SensingLead).where(SensingLead.id == body["lead_id"]))).scalar_one()
    assert lead.sector == "obligation-register"
    assert lead.funnel_stage == "intake_submitted"
    assert lead.organization == GOOD["legal_name"]
    stored = json.loads(lead.market_intel_json)
    assert stored["instrument_list"] == GOOD["instrument_list"]
    assert stored["consent_version"] == "obligation-intake-v1"


async def test_unclear_entity_and_concurrent_work_are_flagged_not_refused(test_client):
    resp = await test_client.post(
        URL, json={**GOOD, "entity_type": "unclear", "concurrent_preissuance": True, "bond_counsel_contact": None}
    )
    assert resp.status_code == 200
    assert resp.json()["flags"] == {
        "entity_unclear": True,
        "concurrent_preissuance": True,
        "no_professional_named": True,
        "workshop_attendee": False,
    }


def test_public_sensing_app_mounts_the_intake_route():
    """The standalone public API (api.muni-pal.io) must expose the intake, or the page posts into a 404."""
    paths = {getattr(r, "path", "") for r in sensing_app.routes}
    assert URL in paths
    client = TestClient(sensing_app)
    assert client.get("/api/v1/sensing/obligation-register/privacy").status_code == 200
