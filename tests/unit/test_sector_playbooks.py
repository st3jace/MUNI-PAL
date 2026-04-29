"""Tests for reusable BFMS sector playbook schema."""

import pytest

from munipal.services.sector_playbooks import (
    UCS_WTE_SECTOR_PLAYBOOK,
    SectorPlaybook,
    SectorPlaybookValidationError,
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
