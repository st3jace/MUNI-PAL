"""ELA-54 qualified lead gate tests for sensing-to-BFMS conversion."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from munipal.api.routes import sensing
from munipal.core.models import SensingLead


class FakeAsyncSession:
    def __init__(self, lead):
        self.lead = lead
        self.added = []
        self.committed = False

    async def get(self, model, lead_id):
        if self.lead and self.lead.id == lead_id:
            return self.lead
        return None

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.committed = True


class RecordingProjectService:
    created_payloads = []

    def __init__(self, db):
        self.db = db

    async def create(self, project_data, owner_id, tenant_id):
        self.created_payloads.append(
            {
                "project_data": project_data,
                "owner_id": owner_id,
                "tenant_id": tenant_id,
            }
        )
        return SimpleNamespace(id=uuid4())


@pytest.fixture(autouse=True)
def reset_recording_project_service(monkeypatch):
    RecordingProjectService.created_payloads = []
    monkeypatch.setattr(
        "munipal.services.project_service.ProjectService",
        RecordingProjectService,
    )


def make_lead(stage: str) -> SensingLead:
    return SensingLead(
        id="lead-123",
        email="cfo@example.org",
        name="Healthcare CFO",
        organization="Oakport Community Hospital",
        sector="healthcare",
        state="CA",
        expected_rating="A",
        deal_size_estimate=25_000_000.0,
        funnel_stage=stage,
    )


def convert_request() -> sensing.LeadConvertRequest:
    return sensing.LeadConvertRequest(
        project_name="Oakport Pilot",
        owner_id="owner-123",
        tenant_id="tenant-123",
        playbook_id="11111111-1111-4111-8111-111111111111",
    )


@pytest.mark.asyncio
async def test_convert_to_project_blocks_unqualified_sensing_leads():
    lead = make_lead("contacted")
    db = FakeAsyncSession(lead)

    with pytest.raises(HTTPException) as exc_info:
        await sensing.convert_lead_to_project(lead.id, convert_request(), db)

    assert exc_info.value.status_code == 409
    detail = str(exc_info.value.detail).lower()
    assert "qualified" in detail
    assert "pilot qualification" in detail
    assert "not deal approval" in detail
    assert "not municipal advisory advice" in detail
    assert lead.funnel_stage == "contacted"
    assert db.committed is False
    assert RecordingProjectService.created_payloads == []


@pytest.mark.asyncio
async def test_convert_to_project_allows_qualified_lead_and_records_prior_stage():
    lead = make_lead("qualified")
    db = FakeAsyncSession(lead)

    response = await sensing.convert_lead_to_project(lead.id, convert_request(), db)

    assert response["lead_id"] == lead.id
    assert response["funnel_stage"] == "engaged"
    assert response["status"] == "converted"
    assert lead.funnel_stage == "engaged"
    assert db.committed is True
    assert len(RecordingProjectService.created_payloads) == 1
    conversion_events = [e for e in db.added if getattr(e, "event_type", None) == "converted_to_project"]
    assert len(conversion_events) == 1
    assert '"from_stage": "qualified"' in conversion_events[0].event_data
