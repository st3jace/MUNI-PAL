"""Tests for BFMS pilot/operator onboarding workflow."""

from munipal.services.pilot_onboarding import (
    PilotOnboardingStage,
    PilotOnboardingValidationError,
    build_pilot_onboarding_workflow,
    validate_pilot_onboarding_workflow,
)


def test_pilot_onboarding_workflow_covers_linear_acceptance_sequence() -> None:
    workflow = validate_pilot_onboarding_workflow(build_pilot_onboarding_workflow("healthcare"))

    assert [stage.stage for stage in workflow.stages] == [
        PilotOnboardingStage.INTAKE,
        PilotOnboardingStage.DOCUMENT_REQUEST,
        PilotOnboardingStage.UPLOAD,
        PilotOnboardingStage.EXTRACTION,
        PilotOnboardingStage.REVIEW,
        PilotOnboardingStage.READINESS,
        PilotOnboardingStage.HANDOFF,
    ]
    assert workflow.playbook.metadata.sector == "healthcare"
    assert workflow.document_request_list
    assert workflow.evidence_workspace_folders == (
        "00_WELCOME",
        "01_PROJECT-OVERVIEW",
        "02_FINANCING-STRUCTURE",
        "03_DUE-DILIGENCE",
        "04_CLOSING-DOCUMENTS",
        "05_POST-ISSUANCE-COMPLIANCE",
        "06_REPORTING",
        "07_RESOURCE-LIBRARY",
    )


def test_workflow_roles_are_explicit_and_include_advisors_reviewers_operator_and_munipal() -> None:
    workflow = build_pilot_onboarding_workflow("housing")
    roles = {role.role for role in workflow.roles}

    assert roles == {"operator", "muni_pal", "advisor", "reviewer"}
    for stage in workflow.stages:
        assert stage.owner_role in roles
        assert stage.participant_roles


def test_workflow_encodes_operator_burden_and_cost_of_issuance_reduction_mechanisms() -> None:
    workflow = build_pilot_onboarding_workflow("waste")
    mechanism_keys = {mechanism.key for mechanism in workflow.burden_reduction_mechanisms}

    assert {
        "playbook_scoped_document_requests",
        "artifact_vault_reuse_and_hashing",
        "ai_extraction_with_human_review",
        "advisor_ready_handoff_pack",
        "measurement_and_cost_learning",
    } <= mechanism_keys
    assert all(mechanism.cost_of_issuance_rationale for mechanism in workflow.burden_reduction_mechanisms)


def test_workflow_links_to_sensing_and_lead_funnel_without_skipping_registered_ma_gate() -> None:
    workflow = build_pilot_onboarding_workflow(
        "healthcare",
        sensing_lead_id="lead-123",
        source_channel="readiness_scan",
    )

    assert workflow.sensing_link is not None
    assert workflow.sensing_link.lead_id == "lead-123"
    assert workflow.sensing_link.source_channel == "readiness_scan"
    assert workflow.sensing_link.allowed_sources == ("market_intelligence", "readiness_scan", "credit_spread_monitor", "direct")
    assert any(gate.gate_id == "registered_ma_confirmed" and gate.required for gate in workflow.pre_pilot_gates)


def test_validation_rejects_workflow_missing_required_stage_or_role() -> None:
    workflow = build_pilot_onboarding_workflow("healthcare")
    workflow.stages.pop()

    try:
        validate_pilot_onboarding_workflow(workflow)
    except PilotOnboardingValidationError as exc:
        assert "handoff" in str(exc)
    else:
        raise AssertionError("expected validation failure for missing handoff stage")

    workflow = build_pilot_onboarding_workflow("healthcare")
    workflow.roles = [role for role in workflow.roles if role.role != "advisor"]

    try:
        validate_pilot_onboarding_workflow(workflow)
    except PilotOnboardingValidationError as exc:
        assert "advisor" in str(exc)
    else:
        raise AssertionError("expected validation failure for missing advisor role")
