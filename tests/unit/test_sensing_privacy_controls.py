"""ELA-55 privacy controls for public sensing lead capture."""

import pytest
from fastapi import HTTPException

from munipal.api.routes import sensing
from munipal.core.models import SensingLead
from munipal.services.sensing_pilot_funnel import SENSING_PILOT_FUNNEL_CONTRACT


class FakeAsyncSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.executed = []

    def add(self, obj):
        self.added.append(obj)

    async def execute(self, stmt):
        self.executed.append(stmt)
        class Result:
            def scalar_one_or_none(self): return None
        return Result()

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        return None


def lead_request(**overrides):
    payload = {
        "email": "finance@example.org",
        "name": "Finance Director",
        "organization": "Oakport Hospital",
        "sector": "healthcare",
        "session_id": "session-privacy-1",
        "privacy_consent": True,
        "market_intel_json": '{"summary":"screening artifact"}',
        "readiness_json": '{"score":72}',
    }
    payload.update(overrides)
    return sensing.LeadCaptureRequest(**payload)


def test_lead_capture_request_requires_affirmative_privacy_consent():
    assert lead_request().privacy_consent is True
    assert lead_request().consent_version == "sensing-lead-v1"

    declined = lead_request(privacy_consent=False)
    db = FakeAsyncSession()

    with pytest.raises(HTTPException) as exc_info:
        import anyio
        anyio.run(sensing.capture_lead, declined, db)

    assert exc_info.value.status_code == 422
    detail = str(exc_info.value.detail).lower()
    assert "consent" in detail
    assert "contact details" in detail
    assert db.added == []
    assert db.committed is False


def test_lead_capture_records_minimized_consent_event():
    db = FakeAsyncSession()
    import anyio

    response = anyio.run(sensing.capture_lead, lead_request(), db)

    assert response["status"] == "captured"
    events = [obj for obj in db.added if getattr(obj, "event_type", None) == "lead_privacy_consent"]
    assert len(events) == 1
    data = events[0].event_data.lower()
    assert "sensing-lead-v1" in data
    assert "contact" in data
    assert "report_snapshots" in data
    assert "retention_days" in data
    assert "export" in data
    assert "delete" in data


def test_sensing_lead_model_covers_unsubscribe_fields_from_email_sequence_migration():
    assert hasattr(SensingLead, "unsubscribe_token")
    assert hasattr(SensingLead, "unsubscribed")
    assert hasattr(SensingLead, "email_sequence_step")
    assert hasattr(SensingLead, "last_email_sent_at")


def test_privacy_contract_defines_retention_export_delete_and_admin_scope():
    privacy = SENSING_PILOT_FUNNEL_CONTRACT.privacy_compliance
    controls = " ".join(privacy.required_controls).lower()
    assert "consent version" in controls
    assert "retention" in controls
    assert "export" in controls
    assert "delete" in controls
    assert "unsubscribe" in controls

    scope = SENSING_PILOT_FUNNEL_CONTRACT.deployment_scope
    assert "/api/v1/sensing/privacy" in scope.allowed_public_routes
    assert "/api/v1/sensing/leads/{lead_id}/privacy-export" in scope.protected_sensing_admin_routes
    assert "/api/v1/sensing/leads/{lead_id}" in scope.protected_sensing_admin_routes


def test_privacy_export_and_delete_routes_are_authenticated_admin_routes():
    routes = {getattr(route, "path", ""): route for route in sensing.router.routes}
    export_route = routes["/leads/{lead_id}/privacy-export"]
    delete_route = routes["/leads/{lead_id}"]

    assert "GET" in export_route.methods
    assert "DELETE" in delete_route.methods
    assert any(getattr(dep.call, "__name__", "") == "require_auth" for dep in export_route.dependant.dependencies)
    assert any(getattr(dep.call, "__name__", "") == "require_auth" for dep in delete_route.dependant.dependencies)
