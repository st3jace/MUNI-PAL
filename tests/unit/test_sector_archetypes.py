"""Tests for BFMS sector archetype registry."""

from munipal.services.sector_archetypes import (
    ARCHETYPE_CAPABILITY_REVENUE_MIX,
    ARCHETYPE_CAPABILITY_SLB_KPIS,
    get_archetype,
    list_archetypes,
    resolve_archetype,
)


def test_healthcare_is_canonical_primary_archetype_without_wte_leakage() -> None:
    archetype = get_archetype("healthcare_501c3_hospital_revenue_bond.v1")

    assert archetype.id == "healthcare_501c3_hospital_revenue_bond"
    assert archetype.version == "v1"
    assert archetype.sector == "healthcare"
    assert archetype.subsector == "healthcare_hospital"
    assert archetype.priority == 10
    assert "healthcare.payor_mix" in archetype.required_evidence_paths
    assert "healthcare.net_patient_revenue" in archetype.required_evidence_paths
    assert "healthcare.cms_certification" in archetype.required_evidence_paths
    assert "healthcare.accreditation" in archetype.required_evidence_paths
    assert "healthcare.licensure" in archetype.required_evidence_paths

    all_paths = set(archetype.required_evidence_paths) | set(archetype.readiness_paths)
    assert not any(path.startswith("feedstock.") for path in all_paths)
    assert not any(path.startswith("slb.") for path in all_paths)
    assert not any(path.startswith("cab.") for path in all_paths)
    assert ARCHETYPE_CAPABILITY_SLB_KPIS not in archetype.capabilities
    assert ARCHETYPE_CAPABILITY_REVENUE_MIX not in archetype.capabilities


def test_wte_archetype_preserves_feedstock_offtake_cab_and_slb_specialization() -> None:
    archetype = get_archetype("ucs_wte_cab_slb.v1")

    assert archetype.sector == "waste"
    assert archetype.subsector == "waste_to_energy"
    assert "feedstock.supply.mechanism" in archetype.required_evidence_paths
    assert "revenue.offtake.status" in archetype.required_evidence_paths
    assert "cab.enabled" in archetype.required_evidence_paths
    assert "slb.enabled" in archetype.required_evidence_paths
    assert ARCHETYPE_CAPABILITY_REVENUE_MIX in archetype.capabilities
    assert ARCHETYPE_CAPABILITY_SLB_KPIS in archetype.capabilities


def test_housing_secondary_archetype_is_first_class_not_generic_fallback() -> None:
    archetype = get_archetype("housing_affordable_multifamily_revenue_bond.v1")

    assert archetype.sector == "housing"
    assert archetype.subsector == "housing_affordable_multifamily"
    assert "housing.lihtec_status" not in archetype.required_evidence_paths
    assert "housing.lihtc_status" in archetype.required_evidence_paths
    assert "housing.hap_section8_revenue" in archetype.required_evidence_paths
    assert "housing.occupancy_rate" in archetype.required_evidence_paths
    assert "housing.site_control" in archetype.required_evidence_paths


def test_resolve_archetype_defaults_to_healthcare_for_current_product_strategy() -> None:
    assert resolve_archetype(None, None).qualified_id == "healthcare_501c3_hospital_revenue_bond.v1"
    assert resolve_archetype("healthcare", None).qualified_id == "healthcare_501c3_hospital_revenue_bond.v1"
    assert resolve_archetype("housing", None).qualified_id == "housing_affordable_multifamily_revenue_bond.v1"
    assert resolve_archetype("waste", None).qualified_id == "ucs_wte_cab_slb.v1"


def test_registry_order_tracks_sector_strategy() -> None:
    archetypes = list_archetypes()

    assert [a.qualified_id for a in archetypes[:3]] == [
        "healthcare_501c3_hospital_revenue_bond.v1",
        "housing_affordable_multifamily_revenue_bond.v1",
        "ucs_wte_cab_slb.v1",
    ]
