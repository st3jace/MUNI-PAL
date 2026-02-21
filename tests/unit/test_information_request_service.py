"""Unit tests for InformationRequestService request-code generation."""

from uuid import UUID

import pytest

import munipal.services.information_request_service as request_service_module
from munipal.core.schemas.information_request import (
    EvidenceState,
    InformationRequestCreate,
    RequestPriority,
)
from munipal.services.information_request_service import InformationRequestService


def _project_token(project_id: str) -> str:
    return project_id.replace("-", "").upper()


def _build_create_payload(project_id: UUID, title: str) -> InformationRequestCreate:
    return InformationRequestCreate(
        project_id=project_id,
        request_code="ignored-by-service",
        title=title,
        missing_fact_paths=["risk.factors.material-risks"],
        current_evidence_state=EvidenceState.NONE,
        gap_id="gap-risk-factors",
        why_it_matters="Risk-factor quality is required for advisor-grade deliverables.",
        who_needs_it=["Municipal Advisor"],
        when_needed="Before external package generation",
        consequences="Insufficient evidence weakens disclosure quality.",
        related_requirements=["risk_factors"],
        regulatory_reference="SEC Rule 10b-5",
        affected_checklist_items=["P3.1"],
        affected_dimensions=["legal_disclosure"],
        guidance_overview="Provide current material risk factors with evidence.",
        specific_questions=["What are the top material risk factors for this deal?"],
        data_points_needed=["material risk list", "supporting source references"],
        suggested_approach="Draft from existing legal and technical documentation.",
        common_pitfalls=["Using outdated risk language"],
        time_estimate="2 hours",
        examples=[],
        acceptable_sources=["Counsel memo", "Draft OS risk section"],
        minimum_confidence=0.80,
        expected_format="memo",
        priority=RequestPriority.HIGH,
        suggested_owner="Sponsor",
    )


class TestInformationRequestServiceRequestCodes:
    @pytest.fixture
    async def service(self, db_session):
        return InformationRequestService(db_session)

    @pytest.fixture
    def minimal_gap_templates(self, monkeypatch):
        monkeypatch.setattr(
            request_service_module,
            "INFORMATION_REQUEST_TEMPLATES",
            [
                {
                    "title_template": "Provide material risk factors",
                    "trigger_fact_paths": ["risk.factors.material-risks"],
                    "trigger_phase": "P1",
                    "why_it_matters": "Required for high-quality advisory packaging.",
                    "who_needs_it": ["Municipal Advisor"],
                    "when_needed": "Before package release",
                    "consequences": "External package may be incomplete.",
                    "guidance_overview": "Collect and validate risk-factor evidence.",
                    "specific_questions": ["What are top material risks?"],
                    "data_points_needed": ["material risk list"],
                    "default_priority": "high",
                    "default_owner": "Sponsor",
                }
            ],
        )
        monkeypatch.setattr(
            request_service_module,
            "SCHEMA_PATHS",
            [{"path": "risk.factors.material-risks", "criticality": "critical"}],
        )
        monkeypatch.setattr(request_service_module, "CHECKLIST_ITEMS", [])
        monkeypatch.setattr(request_service_module, "READINESS_CONFIG", {"dimensions": {}})
        monkeypatch.setattr(request_service_module, "OWNER_MAP", {"risk": "Sponsor"})

    async def test_create_request_codes_are_unique_across_projects(
        self,
        service,
        factory,
        db_session,
    ):
        playbook = await factory.create_playbook()
        project_a = await factory.create_project(playbook["id"], name="Project A")
        project_b = await factory.create_project(playbook["id"], name="Project B")
        await db_session.commit()

        request_a = await service.create_request(
            _build_create_payload(UUID(project_a["id"]), "Request A")
        )
        request_b = await service.create_request(
            _build_create_payload(UUID(project_b["id"]), "Request B")
        )

        assert request_a.request_code != request_b.request_code
        assert request_a.request_code.startswith(f"IR-{_project_token(project_a['id'])}-")
        assert request_b.request_code.startswith(f"IR-{_project_token(project_b['id'])}-")

    async def test_generate_requests_from_gaps_codes_do_not_collide_across_projects(
        self,
        service,
        factory,
        db_session,
        minimal_gap_templates,
    ):
        playbook = await factory.create_playbook()
        project_a = await factory.create_project(playbook["id"], name="Project A")
        project_b = await factory.create_project(playbook["id"], name="Project B")
        await db_session.commit()

        requests_a = await service.generate_requests_from_gaps(UUID(project_a["id"]))
        await db_session.commit()
        requests_b = await service.generate_requests_from_gaps(UUID(project_b["id"]))

        codes_a = {r.request_code for r in requests_a}
        codes_b = {r.request_code for r in requests_b}

        assert codes_a == {f"IR-{_project_token(project_a['id'])}-P1-001"}
        assert codes_b == {f"IR-{_project_token(project_b['id'])}-P1-001"}
        assert codes_a.isdisjoint(codes_b)
