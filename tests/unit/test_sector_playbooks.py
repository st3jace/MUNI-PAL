"""Tests for reusable BFMS sector playbook schema."""

import pytest

from munipal.services.sector_playbooks import (
    HEALTHCARE_SECTOR_PLAYBOOK,
    HOUSING_SECTOR_PLAYBOOK,
    UCS_WTE_SECTOR_PLAYBOOK,
    SectorPlaybook,
    SectorPlaybookValidationError,
    get_sector_playbook,
    list_sector_playbooks,
    migrate_pilot_to_production,
    validate_sector_playbook,
)


def test_ucs_wte_playbook_conforms_to_reusable_schema_without_wte_only_primitives() -> None:
    playbook = validate_sector_playbook(UCS_WTE_SECTOR_PLAYBOOK)

    assert playbook.metadata.sector == "waste"
    assert playbook.metadata.archetype_id == "ucs_wte_cab_slb"
    assert playbook.metadata.version == "v1"
    assert playbook.metadata.lifecycle_stage == "production"
    assert playbook.required_artifacts
    assert playbook.fact_definitions
    assert playbook.readiness_rules
    assert playbook.deliverable_templates
    assert playbook.liability_disclaimers

    fact_paths = {fact.path for fact in playbook.fact_definitions}
    assert "feedstock.supply.mechanism" in fact_paths
    assert "revenue.offtake.status" in fact_paths
    assert "cab.accretionrate" in fact_paths
    assert "slb.kpi.1.name" in fact_paths

    assert {template.output_key for template in playbook.deliverable_templates} >= {
        "internal_readiness_report",
        "external_advisory_package",
        "disclosure_summary",
        "slb_kpi_pack",
    }


def test_validation_rejects_incomplete_playbook_sections() -> None:
    incomplete = SectorPlaybook.model_validate(
        UCS_WTE_SECTOR_PLAYBOOK.model_dump() | {"required_artifacts": []}
    )

    with pytest.raises(SectorPlaybookValidationError, match="required_artifacts"):
        validate_sector_playbook(incomplete)


def test_validation_rejects_ambiguous_duplicate_fact_paths() -> None:
    payload = UCS_WTE_SECTOR_PLAYBOOK.model_dump()
    payload["fact_definitions"] = payload["fact_definitions"] + [payload["fact_definitions"][0]]
    duplicate = SectorPlaybook.model_validate(payload)

    with pytest.raises(SectorPlaybookValidationError, match="duplicate fact path"):
        validate_sector_playbook(duplicate)


def test_readiness_rules_must_reference_declared_facts_and_artifacts() -> None:
    payload = UCS_WTE_SECTOR_PLAYBOOK.model_dump()
    payload["readiness_rules"][0]["fact_paths"] = ["unknown.fact.path"]
    invalid = SectorPlaybook.model_validate(payload)

    with pytest.raises(SectorPlaybookValidationError, match="unknown fact path"):
        validate_sector_playbook(invalid)


def test_pilot_to_production_migration_requires_new_version_and_notes() -> None:
    pilot_payload = UCS_WTE_SECTOR_PLAYBOOK.model_dump()
    pilot_payload["metadata"]["version"] = "v1-pilot"
    pilot_payload["metadata"]["lifecycle_stage"] = "pilot"
    pilot = SectorPlaybook.model_validate(pilot_payload)

    promoted = migrate_pilot_to_production(
        pilot,
        new_version="v2",
        migration_notes="Validated against production UCS/WTE pilot corpus and advisor handoff outputs.",
    )

    assert promoted.metadata.version == "v2"
    assert promoted.metadata.lifecycle_stage == "production"
    assert promoted.metadata.supersedes_version == "v1-pilot"
    assert "pilot corpus" in promoted.metadata.migration_notes
    validate_sector_playbook(promoted)

    with pytest.raises(SectorPlaybookValidationError, match="migration_notes"):
        migrate_pilot_to_production(pilot, new_version="v2", migration_notes="")


def test_healthcare_primary_playbook_conforms_without_cab_slb_or_feedstock_leakage() -> None:
    playbook = validate_sector_playbook(HEALTHCARE_SECTOR_PLAYBOOK)

    assert playbook.metadata.sector == "healthcare"
    assert playbook.metadata.archetype_id == "healthcare_501c3_hospital_revenue_bond"
    assert playbook.metadata.lifecycle_stage == "production"

    fact_paths = {fact.path for fact in playbook.fact_definitions}
    assert {
        "healthcare.net_patient_revenue",
        "healthcare.payor_mix",
        "healthcare.cms_certification",
        "healthcare.accreditation",
        "liquidity.days_cash_on_hand",
        "healthcare.ehr_platform",
        "healthcare.physician_alignment",
        "healthcare.utilization.trend",
    } <= fact_paths
    assert not any(path.startswith("feedstock.") for path in fact_paths)
    assert not any(path.startswith("cab.") for path in fact_paths)
    assert not any(path.startswith("slb.") for path in fact_paths)

    artifact_keys = {artifact.artifact_key for artifact in playbook.required_artifacts}
    assert {"licensure_accreditation", "financial_operating_metrics", "clinical_service_area"} <= artifact_keys


def test_housing_secondary_playbook_conforms_as_pilot_for_migration() -> None:
    playbook = validate_sector_playbook(HOUSING_SECTOR_PLAYBOOK)

    assert playbook.metadata.sector == "housing"
    assert playbook.metadata.archetype_id == "housing_affordable_multifamily_revenue_bond"
    assert playbook.metadata.lifecycle_stage == "pilot"

    fact_paths = {fact.path for fact in playbook.fact_definitions}
    assert {
        "housing.lihtc_status",
        "housing.hap_section8_revenue",
        "housing.rental_income",
        "housing.occupancy_rate",
        "housing.site_control",
        "construction.permits.status",
        "market.demographics.summary",
        "housing.lease_up_risk",
        "housing.compliance_risk",
    } <= fact_paths
    assert not any(path.startswith("feedstock.") for path in fact_paths)
    assert not any(path.startswith("cab.") for path in fact_paths)
    assert not any(path.startswith("slb.") for path in fact_paths)

    artifact_keys = {artifact.artifact_key for artifact in playbook.required_artifacts}
    assert {"subsidy_stack", "rent_roll_operating", "site_control_permits", "market_compliance"} <= artifact_keys


def test_focused_sector_playbook_registry_tracks_current_strategy_order() -> None:
    playbooks = list_sector_playbooks()

    assert [playbook.metadata.archetype_id for playbook in playbooks] == [
        "healthcare_501c3_hospital_revenue_bond",
        "housing_affordable_multifamily_revenue_bond",
        "ucs_wte_cab_slb",
    ]
    assert get_sector_playbook("healthcare").metadata.playbook_id == HEALTHCARE_SECTOR_PLAYBOOK.metadata.playbook_id
    assert get_sector_playbook("housing").metadata.playbook_id == HOUSING_SECTOR_PLAYBOOK.metadata.playbook_id
    assert get_sector_playbook("waste").metadata.playbook_id == UCS_WTE_SECTOR_PLAYBOOK.metadata.playbook_id
