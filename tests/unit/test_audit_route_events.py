from types import SimpleNamespace
from uuid import uuid4

import pytest

from munipal.api.routes import (
    advisory_packages,
    artifacts,
    deliverables,
    disclosure,
    facts,
    projects,
    risk_reporting,
)


@pytest.mark.asyncio
async def test_approve_fact_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    project_id = uuid4()
    fact_id = uuid4()
    reviewer_id = uuid4()

    async def fake_require_fact_write(self, user_id, requested_fact_id):
        assert user_id == "actor-1"
        assert requested_fact_id == fact_id

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    class FakeFactService:
        async def approve_fact(self, **kwargs):
            assert kwargs["fact_id"] == fact_id
            return SimpleNamespace(project_id=project_id)

        def fact_to_read_schema(self, _fact):
            return {"id": str(fact_id)}

    monkeypatch.setattr(facts.AuthorizationService, "require_fact_write", fake_require_fact_write)
    monkeypatch.setattr(facts.AuditService, "emit_event", fake_emit_event)

    await facts.approve_fact(
        db=object(),
        user_id="actor-1",
        fact_id=fact_id,
        reviewer_id=reviewer_id,
        corrected_value=None,
        note=None,
        service=FakeFactService(),
        _="analyst",
    )

    assert len(events) == 1
    assert events[0]["action"] == "approve_fact"
    assert events[0]["target_id"] == str(fact_id)
    assert events[0]["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_reject_fact_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    project_id = uuid4()
    fact_id = uuid4()
    reviewer_id = uuid4()

    async def fake_require_fact_write(self, _user_id, _fact_id):
        return None

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    class FakeFactService:
        async def reject_fact(self, **kwargs):
            assert kwargs["fact_id"] == fact_id
            return SimpleNamespace(project_id=project_id)

        def fact_to_read_schema(self, _fact):
            return {"id": str(fact_id)}

    monkeypatch.setattr(facts.AuthorizationService, "require_fact_write", fake_require_fact_write)
    monkeypatch.setattr(facts.AuditService, "emit_event", fake_emit_event)

    await facts.reject_fact(
        db=object(),
        user_id="actor-2",
        fact_id=fact_id,
        reviewer_id=reviewer_id,
        reason="invalid",
        service=FakeFactService(),
        _="analyst",
    )

    assert len(events) == 1
    assert events[0]["action"] == "reject_fact"
    assert events[0]["target_id"] == str(fact_id)
    assert events[0]["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_archive_fact_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    project_id = uuid4()
    fact_id = uuid4()
    reviewer_id = uuid4()

    async def fake_require_fact_write(self, _user_id, _fact_id):
        return None

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    class FakeFactService:
        async def archive_fact(self, **kwargs):
            assert kwargs["fact_id"] == fact_id
            return SimpleNamespace(project_id=project_id)

        def fact_to_read_schema(self, _fact):
            return {"id": str(fact_id), "lifecycle_state": "archived"}

    monkeypatch.setattr(facts.AuthorizationService, "require_fact_write", fake_require_fact_write)
    monkeypatch.setattr(facts.AuditService, "emit_event", fake_emit_event)

    await facts.archive_fact(
        db=object(),
        user_id="actor-archive",
        fact_id=fact_id,
        request=facts.FactArchiveRequest(reason_code="duplicate_exact", note="archived"),
        reviewer_id=reviewer_id,
        service=FakeFactService(),
        _="analyst",
    )

    assert len(events) == 1
    assert events[0]["action"] == "archive_fact"
    assert events[0]["target_id"] == str(fact_id)
    assert events[0]["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_unarchive_fact_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    project_id = uuid4()
    fact_id = uuid4()
    reviewer_id = uuid4()

    async def fake_require_fact_write(self, _user_id, _fact_id):
        return None

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    class FakeFactService:
        async def unarchive_fact(self, **kwargs):
            assert kwargs["fact_id"] == fact_id
            return SimpleNamespace(project_id=project_id)

        def fact_to_read_schema(self, _fact):
            return {"id": str(fact_id), "lifecycle_state": "active"}

    monkeypatch.setattr(facts.AuthorizationService, "require_fact_write", fake_require_fact_write)
    monkeypatch.setattr(facts.AuditService, "emit_event", fake_emit_event)

    await facts.unarchive_fact(
        db=object(),
        user_id="actor-unarchive",
        fact_id=fact_id,
        request=facts.FactUnarchiveRequest(note="restore"),
        reviewer_id=reviewer_id,
        service=FakeFactService(),
        _="analyst",
    )

    assert len(events) == 1
    assert events[0]["action"] == "unarchive_fact"
    assert events[0]["target_id"] == str(fact_id)
    assert events[0]["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_delete_project_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    project_id = uuid4()

    async def fake_require_project_write(self, _user_id, _project_id):
        return None

    async def fake_delete(self, requested_project_id):
        assert requested_project_id == project_id
        return True

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    monkeypatch.setattr(projects.AuthorizationService, "require_project_write", fake_require_project_write)
    monkeypatch.setattr(projects.ProjectService, "delete", fake_delete)
    monkeypatch.setattr(projects.AuditService, "emit_event", fake_emit_event)

    await projects.delete_project(
        project_id=project_id,
        db=object(),
        user_id="admin-1",
        _="admin",
    )

    assert len(events) == 1
    assert events[0]["action"] == "delete_project"
    assert events[0]["target_id"] == str(project_id)
    assert events[0]["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_delete_artifact_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    artifact_id = uuid4()

    async def fake_require_artifact_write(self, _user_id, _artifact_id):
        return None

    async def fake_delete(self, requested_artifact_id):
        assert requested_artifact_id == artifact_id
        return True

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    monkeypatch.setattr(artifacts.AuthorizationService, "require_artifact_write", fake_require_artifact_write)
    monkeypatch.setattr(artifacts.ArtifactService, "delete", fake_delete)
    monkeypatch.setattr(artifacts.AuditService, "emit_event", fake_emit_event)

    await artifacts.delete_artifact(
        artifact_id=artifact_id,
        db=object(),
        user_id="admin-1",
        _="admin",
    )

    assert len(events) == 1
    assert events[0]["action"] == "delete_artifact"
    assert events[0]["target_id"] == str(artifact_id)


@pytest.mark.asyncio
async def test_export_deliverable_markdown_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    pack_id = uuid4()
    project_id = uuid4()

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    class FakeDeliverableService:
        async def get_pack(self, requested_pack_id):
            assert requested_pack_id == pack_id
            return SimpleNamespace(
                id=str(pack_id),
                title="Pack",
                is_complete=True,
                project_id=project_id,
                sections=[],
            )

    monkeypatch.setattr(deliverables.AuditService, "emit_event", fake_emit_event)

    await deliverables.export_markdown(
        pack_id=pack_id,
        user_id="actor-3",
        service=FakeDeliverableService(),
    )

    assert len(events) == 1
    assert events[0]["action"] == "export_deliverable_pack_markdown"
    assert events[0]["target_id"] == str(pack_id)
    assert events[0]["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_export_deliverable_pdf_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    pack_id = uuid4()
    project_id = uuid4()

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    class FakeTask:
        id = "task-1"

    class FakeExportPackPdf:
        @staticmethod
        def delay(_pack_id):
            return FakeTask()

    class FakeDeliverableService:
        async def get_pack(self, requested_pack_id):
            assert requested_pack_id == pack_id
            return SimpleNamespace(
                id=str(pack_id),
                title="Pack",
                is_complete=True,
                project_id=project_id,
                sections=[],
            )

    monkeypatch.setattr(deliverables.AuditService, "emit_event", fake_emit_event)
    monkeypatch.setattr(deliverables, "export_pack_pdf", FakeExportPackPdf)

    await deliverables.export_pdf(
        pack_id=pack_id,
        user_id="actor-3",
        service=FakeDeliverableService(),
    )

    assert len(events) == 1
    assert events[0]["action"] == "export_deliverable_pack_pdf"
    assert events[0]["target_id"] == str(pack_id)
    assert events[0]["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_export_internal_report_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    report_id = uuid4()
    project_id = uuid4()

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    class FakeInternalReportService:
        async def get_report(self, requested_report_id):
            assert requested_report_id == report_id
            return SimpleNamespace(
                id=str(report_id),
                version=1,
                project_id=project_id,
                generation_completed_at=None,
                overall_score=None,
                critical_gap_count=0,
                open_request_count=0,
                facts_count=0,
                executive_summary=None,
                gap_analysis=None,
                information_requests_section=None,
                checklist_status=None,
                evidence_index=None,
                bfms_version="2.0",
            )

    monkeypatch.setattr(advisory_packages.AuditService, "emit_event", fake_emit_event)
    monkeypatch.setattr(
        advisory_packages,
        "_generate_internal_report_markdown",
        lambda _report: "# Internal",
    )

    await advisory_packages.export_internal_report(
        report_id=report_id,
        user_id="actor-4",
        format="md",
        service=FakeInternalReportService(),
    )

    assert len(events) == 1
    assert events[0]["action"] == "export_internal_report_markdown"
    assert events[0]["target_id"] == str(report_id)
    assert events[0]["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_export_external_package_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    package_id = uuid4()
    project_id = uuid4()

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    class FakeExternalPackageService:
        async def get_package(self, requested_package_id):
            assert requested_package_id == package_id
            return SimpleNamespace(
                id=str(package_id),
                version=1,
                project_id=project_id,
            )

    monkeypatch.setattr(advisory_packages.AuditService, "emit_event", fake_emit_event)
    monkeypatch.setattr(
        advisory_packages,
        "_generate_external_package_markdown",
        lambda _package: "# External",
    )

    await advisory_packages.export_external_package(
        package_id=package_id,
        user_id="actor-6",
        format="md",
        service=FakeExternalPackageService(),
    )

    assert len(events) == 1
    assert events[0]["action"] == "export_external_package_markdown"
    assert events[0]["target_id"] == str(package_id)
    assert events[0]["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_export_disclosure_document_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    document_id = uuid4()
    project_id = uuid4()

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    class FakeDisclosureService:
        async def get_document(self, requested_document_id):
            assert requested_document_id == document_id
            return SimpleNamespace(
                id=str(document_id),
                version=1,
                project_id=project_id,
                sections=[SimpleNamespace(section_order=1, content_md="Section 1")],
            )

    monkeypatch.setattr(disclosure.AuditService, "emit_event", fake_emit_event)

    await disclosure.export_disclosure_document(
        document_id=document_id,
        user_id="actor-5",
        format="md",
        service=FakeDisclosureService(),
    )

    assert len(events) == 1
    assert events[0]["action"] == "export_disclosure_markdown"
    assert events[0]["target_id"] == str(document_id)
    assert events[0]["project_id"] == str(project_id)


@pytest.mark.asyncio
async def test_risk_diagnostics_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    project_id = uuid4()

    class FakeRiskService:
        async def build_diagnostics(self, _project_id, _cohort):
            return SimpleNamespace(dimensions=[1, 2], actions=[1])

    async def fake_require_project_read(self, _user_id, _project_id):
        return None

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    monkeypatch.setattr(risk_reporting, "get_settings", lambda: SimpleNamespace(risk_reporting_v2_foundation=True))
    monkeypatch.setattr(risk_reporting.AuthorizationService, "require_project_read", fake_require_project_read)
    monkeypatch.setattr(risk_reporting, "RiskReportingService", lambda _db: FakeRiskService())
    monkeypatch.setattr(risk_reporting.AuditService, "emit_event", fake_emit_event)

    await risk_reporting.get_risk_diagnostics(
        db=object(),
        user_id="actor-risk-1",
        project_id=project_id,
        sector="waste_to_energy",
        issuer_size_band="mid",
        deal_type="revenue",
        recency_window="5y",
        sample_size=42,
        _="analyst",
    )

    assert len(events) == 1
    assert events[0]["action"] == "generate_risk_diagnostics"
    assert events[0]["target_id"] == str(project_id)


@pytest.mark.asyncio
async def test_risk_override_decision_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    project_id = uuid4()

    async def fake_require_project_write(self, _user_id, _project_id):
        return None

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    monkeypatch.setattr(risk_reporting, "get_settings", lambda: SimpleNamespace(risk_reporting_v2_foundation=True))
    monkeypatch.setattr(risk_reporting.AuthorizationService, "require_project_write", fake_require_project_write)
    monkeypatch.setattr(risk_reporting.AuditService, "emit_event", fake_emit_event)

    decision = risk_reporting.RiskOverrideDecisionRequest(
        project_id=project_id,
        target_ref="risk.market",
        reason="Reviewed against updated market memorandum.",
        previous_value="above",
        override_value="at",
        notes="Temporary adjustment",
    )
    await risk_reporting.record_risk_override_decision(
        db=object(),
        user_id="actor-risk-2",
        decision=decision,
        _="analyst",
    )

    assert len(events) == 1
    assert events[0]["action"] == "risk_override_decision"
    assert events[0]["project_id"] == str(project_id)
    assert events[0]["metadata"]["reason"] == decision.reason


@pytest.mark.asyncio
async def test_risk_action_acceptance_emits_audit_event(monkeypatch: pytest.MonkeyPatch):
    events = []
    project_id = uuid4()

    async def fake_require_project_write(self, _user_id, _project_id):
        return None

    def fake_emit_event(**kwargs):
        events.append(kwargs)
        return kwargs

    monkeypatch.setattr(risk_reporting, "get_settings", lambda: SimpleNamespace(risk_reporting_v2_foundation=True))
    monkeypatch.setattr(risk_reporting.AuthorizationService, "require_project_write", fake_require_project_write)
    monkeypatch.setattr(risk_reporting.AuditService, "emit_event", fake_emit_event)

    acceptance = risk_reporting.RiskActionAcceptanceRequest(
        project_id=project_id,
        reason="Execution owner confirmed in weekly risk review.",
        notes="Proceed immediately",
    )
    await risk_reporting.accept_risk_action(
        action_id="action.dscr.coverage",
        db=object(),
        user_id="actor-risk-3",
        acceptance=acceptance,
        _="analyst",
    )

    assert len(events) == 1
    assert events[0]["action"] == "risk_action_accepted"
    assert events[0]["target_id"] == "action.dscr.coverage"
    assert events[0]["project_id"] == str(project_id)
