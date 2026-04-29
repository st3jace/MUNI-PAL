"""Versioned sector archetype registry for BFMS.

Sector archetypes keep domain-specific evidence, readiness, deliverable, and UI
capability decisions outside the platform primitives.  A Project remains the
workspace; the archetype describes how that workspace should be interpreted for
a sector/deal pattern.
"""
from __future__ import annotations

from dataclasses import dataclass

ARCHETYPE_CAPABILITY_HEALTHCARE_READINESS = "healthcare_readiness"
ARCHETYPE_CAPABILITY_HOUSING_AFFORDABILITY = "housing_affordability"
ARCHETYPE_CAPABILITY_REVENUE_MIX = "revenue_mix"
ARCHETYPE_CAPABILITY_COMMODITY_REVENUE = "commodity_revenue"
ARCHETYPE_CAPABILITY_CAB_STRUCTURE = "cab_structure"
ARCHETYPE_CAPABILITY_SLB_KPIS = "slb_kpis"


@dataclass(frozen=True, slots=True)
class SectorArchetype:
    """Stable, versioned sector archetype metadata."""

    id: str
    version: str
    sector: str
    subsector: str | None
    display_name: str
    description: str
    priority: int
    bond_structures: tuple[str, ...]
    required_evidence_paths: tuple[str, ...]
    readiness_paths: tuple[str, ...]
    deliverables: tuple[str, ...]
    handoff_outputs: tuple[str, ...]
    information_request_themes: tuple[str, ...]
    capabilities: tuple[str, ...]

    @property
    def qualified_id(self) -> str:
        """Return stable id plus version."""
        return f"{self.id}.{self.version}"


HEALTHCARE_HOSPITAL = SectorArchetype(
    id="healthcare_501c3_hospital_revenue_bond",
    version="v1",
    sector="healthcare",
    subsector="healthcare_hospital",
    display_name="Healthcare 501(c)(3) Hospital Revenue Bond",
    description=(
        "Canonical/current-primary BFMS archetype for nonprofit hospital and "
        "health-system financings."
    ),
    priority=10,
    bond_structures=("501(c)(3) revenue bond", "hospital revenue bond"),
    required_evidence_paths=(
        "parties.issuer.name",
        "parties.issuer.jurisdiction",
        "governance.inducement",
        "healthcare.facility_type",
        "healthcare.licensure",
        "healthcare.cms_certification",
        "healthcare.accreditation",
        "healthcare.net_patient_revenue",
        "healthcare.payor_mix",
        "healthcare.service_area",
        "finmodel.outputs.dscrbase",
        "finmodel.inputs.dscr.minimum",
        "liquidity.days_cash_on_hand",
        "opex.margin",
        "capital.project-cost",
        "security.revenue.pledge",
    ),
    readiness_paths=(
        "healthcare.facility_type",
        "healthcare.licensure",
        "healthcare.cms_certification",
        "healthcare.accreditation",
        "healthcare.net_patient_revenue",
        "healthcare.payor_mix",
        "healthcare.service_area",
        "finmodel.outputs.dscrbase",
        "finmodel.inputs.dscr.minimum",
        "liquidity.days_cash_on_hand",
        "opex.margin",
    ),
    deliverables=("internal_readiness_report", "external_advisory_package", "disclosure_summary"),
    handoff_outputs=("readiness_report", "gap_analysis", "advisor_handoff_pack"),
    information_request_themes=(
        "payor_mix_and_revenue_concentration",
        "cms_licensure_and_accreditation",
        "liquidity_margin_and_leverage",
        "facility_scope_and_service_area",
        "reimbursement_and_regulatory_risk",
    ),
    capabilities=(ARCHETYPE_CAPABILITY_HEALTHCARE_READINESS,),
)

HOUSING_AFFORDABLE_MULTIFAMILY = SectorArchetype(
    id="housing_affordable_multifamily_revenue_bond",
    version="v1",
    sector="housing",
    subsector="housing_affordable_multifamily",
    display_name="Affordable Multifamily Housing Revenue Bond",
    description=(
        "Secondary strategic BFMS archetype for affordable multifamily housing "
        "transactions, including LIHTC/HAP-supported projects."
    ),
    priority=20,
    bond_structures=("multifamily housing revenue bond", "affordable housing revenue bond"),
    required_evidence_paths=(
        "parties.issuer.name",
        "parties.borrower.name",
        "housing.project_type",
        "housing.lihtc_status",
        "housing.hap_section8_revenue",
        "housing.rental_income",
        "housing.occupancy_rate",
        "housing.site_control",
        "housing.affordability_restrictions",
        "capital.project-cost",
        "capital.equity_contribution",
        "construction.permits.status",
        "market.demographics.summary",
        "security.revenue.pledge",
    ),
    readiness_paths=(
        "housing.lihtc_status",
        "housing.hap_section8_revenue",
        "housing.rental_income",
        "housing.occupancy_rate",
        "housing.site_control",
        "capital.project-cost",
        "capital.equity_contribution",
        "construction.permits.status",
    ),
    deliverables=("internal_readiness_report", "external_advisory_package", "disclosure_summary"),
    handoff_outputs=("readiness_report", "gap_analysis", "advisor_handoff_pack"),
    information_request_themes=(
        "lihtc_and_subsidy_status",
        "occupancy_and_rent_roll",
        "site_control_and_permitting",
        "construction_budget_and_sources_uses",
        "affordability_and_compliance_restrictions",
    ),
    capabilities=(ARCHETYPE_CAPABILITY_HOUSING_AFFORDABILITY,),
)

UCS_WTE_CAB_SLB = SectorArchetype(
    id="ucs_wte_cab_slb",
    version="v1",
    sector="waste",
    subsector="waste_to_energy",
    display_name="UCS Waste-to-Energy CAB + SLB Revenue Bond",
    description=(
        "Mature validated BFMS archetype for UCS/waste-to-energy financings "
        "with feedstock, commodity offtake, CAB, and SLB-specific evidence."
    ),
    priority=30,
    bond_structures=("exempt facility revenue bond", "capital appreciation bond", "sustainability-linked bond"),
    required_evidence_paths=(
        "parties.issuer.name",
        "parties.issuer.jurisdiction",
        "governance.inducement",
        "technology.type",
        "technology.throughput.nameplate",
        "feedstock.type",
        "feedstock.volume.annual",
        "feedstock.supply.mechanism",
        "feedstock.supply.confidence",
        "revenue.offtake.status",
        "revenue.commodities.list",
        "revenue.gross.annual",
        "cab.enabled",
        "cab.originalprincipial",
        "cab.accretionrate",
        "slb.enabled",
        "slb.kpi.1.name",
        "slb.verifier.name",
        "security.revenue.pledge",
    ),
    readiness_paths=(
        "technology.type",
        "technology.throughput.nameplate",
        "feedstock.supply.mechanism",
        "revenue.offtake.status",
        "revenue.gross.annual",
        "cab.enabled",
        "cab.originalprincipial",
        "cab.accretionrate",
        "slb.enabled",
        "slb.kpi.1.name",
        "slb.verifier.name",
    ),
    deliverables=("internal_readiness_report", "external_advisory_package", "disclosure_summary", "slb_kpi_pack"),
    handoff_outputs=("readiness_report", "gap_analysis", "advisor_handoff_pack", "slb_verification_pack"),
    information_request_themes=(
        "feedstock_supply_and_confidence",
        "commodity_offtake_and_revenue_validation",
        "cab_terms_and_accretion",
        "slb_kpis_and_verification",
        "technology_and_construction_risk",
    ),
    capabilities=(
        ARCHETYPE_CAPABILITY_REVENUE_MIX,
        ARCHETYPE_CAPABILITY_COMMODITY_REVENUE,
        ARCHETYPE_CAPABILITY_CAB_STRUCTURE,
        ARCHETYPE_CAPABILITY_SLB_KPIS,
    ),
)

_ARCHETYPES = {
    a.qualified_id: a
    for a in (HEALTHCARE_HOSPITAL, HOUSING_AFFORDABLE_MULTIFAMILY, UCS_WTE_CAB_SLB)
}
_ALIASES = {
    "healthcare": HEALTHCARE_HOSPITAL.qualified_id,
    "healthcare_hospital": HEALTHCARE_HOSPITAL.qualified_id,
    "hospital": HEALTHCARE_HOSPITAL.qualified_id,
    "housing": HOUSING_AFFORDABLE_MULTIFAMILY.qualified_id,
    "housing_affordable_multifamily": HOUSING_AFFORDABLE_MULTIFAMILY.qualified_id,
    "affordable_housing": HOUSING_AFFORDABLE_MULTIFAMILY.qualified_id,
    "waste": UCS_WTE_CAB_SLB.qualified_id,
    "waste_to_energy": UCS_WTE_CAB_SLB.qualified_id,
    "wte": UCS_WTE_CAB_SLB.qualified_id,
    "ucs": UCS_WTE_CAB_SLB.qualified_id,
    "ucs_wte_cab_slb": UCS_WTE_CAB_SLB.qualified_id,
}


def list_archetypes() -> list[SectorArchetype]:
    """List known archetypes in product-strategy order."""
    return sorted(_ARCHETYPES.values(), key=lambda a: a.priority)


def get_archetype(qualified_id: str) -> SectorArchetype:
    """Return an archetype by stable qualified id or alias."""
    key = _ALIASES.get(qualified_id, qualified_id)
    try:
        return _ARCHETYPES[key]
    except KeyError as exc:
        raise KeyError(f"Unknown sector archetype: {qualified_id}") from exc


def resolve_archetype(sector: str | None, subsector: str | None = None) -> SectorArchetype:
    """Resolve project sector/subsector to the best matching archetype.

    Healthcare is the current primary/canonical default.  WTE remains explicit
    and mature, and Housing is a first-class secondary option.
    """
    for candidate in (subsector, sector):
        if candidate:
            normalized = candidate.strip().lower().replace("-", "_").replace("/", "_").replace(" ", "_")
            if normalized in _ALIASES:
                return get_archetype(_ALIASES[normalized])
    return HEALTHCARE_HOSPITAL
