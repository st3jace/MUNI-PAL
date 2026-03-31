"""
Unit tests for SensingLead and SensingEvent models.

Validates table creation, column constraints, and basic CRUD operations
for the sensing lead capture and funnel analytics tables.
"""

from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from munipal.core.models import Base, SensingEvent, SensingLead


@pytest.fixture(scope="module")
def sync_session():
    """In-memory SQLite session for model tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    engine.dispose()


class TestSensingLeadModel:
    def test_table_exists(self, sync_session: Session):
        inspector = inspect(sync_session.bind)
        tables = inspector.get_table_names()
        assert "sensing_leads" in tables

    def test_create_lead(self, sync_session: Session):
        lead = SensingLead(
            id=str(uuid4()),
            email="test@example.com",
            name="Test User",
            organization="Test Corp",
            sector="healthcare",
            funnel_stage="report_requested",
        )
        sync_session.add(lead)
        sync_session.commit()

        result = sync_session.query(SensingLead).filter_by(email="test@example.com").first()
        assert result is not None
        assert result.name == "Test User"
        assert result.organization == "Test Corp"
        assert result.sector == "healthcare"
        assert result.funnel_stage == "report_requested"

    def test_optional_fields(self, sync_session: Session):
        lead = SensingLead(
            id=str(uuid4()),
            email="optional@example.com",
            name="Optional Fields",
            organization="Test Corp",
            sector="water_sewer",
            funnel_stage="report_requested",
            title="CFO",
            phone="555-1234",
            deal_size_estimate=50_000_000.0,
            state="CA",
            expected_rating="AA",
            referral_source="conference",
        )
        sync_session.add(lead)
        sync_session.commit()

        result = sync_session.query(SensingLead).filter_by(email="optional@example.com").first()
        assert result.title == "CFO"
        assert result.deal_size_estimate == 50_000_000.0
        assert result.state == "CA"

    def test_json_blob_fields(self, sync_session: Session):
        lead = SensingLead(
            id=str(uuid4()),
            email="json@example.com",
            name="JSON Test",
            organization="Test Corp",
            sector="healthcare",
            funnel_stage="report_downloaded",
            market_intel_json='{"key": "value"}',
            benchmark_json='{"score": 85}',
            readiness_json='{"ready": true}',
        )
        sync_session.add(lead)
        sync_session.commit()

        result = sync_session.query(SensingLead).filter_by(email="json@example.com").first()
        assert '"key"' in result.market_intel_json
        assert '"score"' in result.benchmark_json


class TestSensingEventModel:
    def test_table_exists(self, sync_session: Session):
        inspector = inspect(sync_session.bind)
        tables = inspector.get_table_names()
        assert "sensing_events" in tables

    def test_create_event(self, sync_session: Session):
        event = SensingEvent(
            id=str(uuid4()),
            session_id="sess-abc-123",
            event_type="page_view",
        )
        sync_session.add(event)
        sync_session.commit()

        result = sync_session.query(SensingEvent).filter_by(session_id="sess-abc-123").first()
        assert result is not None
        assert result.event_type == "page_view"
        assert result.lead_id is None

    def test_event_with_lead_link(self, sync_session: Session):
        lead_id = str(uuid4())
        event = SensingEvent(
            id=str(uuid4()),
            lead_id=lead_id,
            session_id="sess-def-456",
            event_type="report_requested",
            sector="healthcare",
            event_data='{"report_type": "combined"}',
        )
        sync_session.add(event)
        sync_session.commit()

        result = sync_session.query(SensingEvent).filter_by(session_id="sess-def-456").first()
        assert result.lead_id == lead_id
        assert result.sector == "healthcare"
        assert result.event_data is not None
