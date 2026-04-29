"""ELA-38 sensing-to-pilot funnel contract tests."""

from pathlib import Path

from munipal.sensing_app import app as sensing_app
from munipal.services.sensing_pilot_funnel import (
    SENSING_PILOT_FUNNEL_CONTRACT,
    standalone_sensing_app_route_violations,
)


def test_sensing_deployment_scope_blocks_bfms_admin_routes():
    scope = SENSING_PILOT_FUNNEL_CONTRACT.deployment_scope

    assert "/api/v1/sensing/lead" in scope.allowed_public_routes
    assert "/api/v1/sensing/readiness" in scope.allowed_public_routes
    assert "/api/v1/sensing/leads" in scope.protected_sensing_admin_routes

    blocked = set(scope.blocked_bfms_route_prefixes)
    assert "/api/v1/auth" in blocked
    assert "/api/v1/projects" in blocked
    assert "/api/v1/artifacts" in blocked
    assert "/api/v1/extraction" in blocked
    assert "/api/v1/facts" in blocked
    assert "/api/v1/deal-documents" in blocked

    assert standalone_sensing_app_route_violations(sensing_app) == []


def test_lead_to_pilot_handoff_requires_qualification_before_project_creation():
    handoff = SENSING_PILOT_FUNNEL_CONTRACT.lead_handoff
    stage_keys = [stage.stage_key for stage in handoff.stages]

    assert stage_keys == [
        "lead_capture",
        "pilot_qualification",
        "bfms_project_creation",
        "pilot_onboarding",
    ]
    assert "qualified" in handoff.required_conversion_stage
    assert "engaged" in handoff.post_conversion_stage
    assert handoff.project_creation_endpoint == "/api/v1/sensing/leads/{lead_id}/convert-to-project"
    assert "sector playbook" in " ".join(handoff.project_creation_requirements).lower()
    assert "registered ma" in " ".join(handoff.pilot_qualification_requirements).lower()


def test_privacy_and_compliance_expectations_cover_public_lead_capture():
    privacy = SENSING_PILOT_FUNNEL_CONTRACT.privacy_compliance
    controls = " ".join(privacy.required_controls).lower()

    assert "consent" in controls
    assert "pii" in controls
    assert "unsubscribe" in controls
    assert "retention" in controls
    assert "auth" in controls
    assert "no legal advice" in controls
    assert privacy.public_surface_posture == "lead-generation-only"


def test_sensing_pilot_funnel_document_covers_linear_acceptance_criteria():
    doc = Path("docs/architecture/SENSING_PILOT_FUNNEL.md")
    assert doc.exists()
    text = doc.read_text(encoding="utf-8").lower()

    for required in [
        "deployment scope",
        "blocked bfms/admin routes",
        "lead -> pilot qualification -> bfms project creation",
        "privacy and compliance expectations",
        "follow-up implementation issues",
    ]:
        assert required in text
