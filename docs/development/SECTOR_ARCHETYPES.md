# BFMS Sector Archetypes

ELA-32 establishes sector archetypes as the boundary between BFMS platform primitives and sector-specific bond-finance logic.

## Sector strategy

MUNI-PAL began with a deep UCS waste-to-energy CAB + SLB use case. That WTE archetype remains supported and valuable, but it is not the whole product. The current product strategy is:

1. Healthcare is the current primary/canonical archetype.
2. Housing is the secondary strategic archetype and must be represented as first-class, not generic fallback.
3. UCS/WTE remains a mature specialized archetype with feedstock, offtake, CAB, and SLB logic isolated from other sectors.

## Platform primitives vs archetypes

Platform primitives stay reusable across sectors:

- Project
- Artifact / document
- Extracted fact
- Fact review status
- Checklist item
- Readiness assessment
- Disclosure document
- Information request
- Deliverable / handoff pack

Sector archetypes describe how those primitives should be interpreted for a deal pattern:

- stable archetype id and version
- sector and subsector
- applicable bond structures
- required evidence paths
- readiness paths/rules
- deliverables and handoff outputs
- information request themes
- UI capabilities

## Initial archetypes

### healthcare_501c3_hospital_revenue_bond.v1

Canonical/current-primary archetype for nonprofit hospital and health-system financings.

Representative evidence includes:

- healthcare.net_patient_revenue
- healthcare.payor_mix
- healthcare.cms_certification
- healthcare.accreditation
- healthcare.licensure
- healthcare.service_area
- finmodel.outputs.dscrbase
- finmodel.inputs.dscr.minimum
- liquidity.days_cash_on_hand
- opex.margin

Healthcare must not inherit WTE-only CAB, SLB, feedstock, or commodity-offtake requirements unless a specific project later opts into those structures.

### housing_affordable_multifamily_revenue_bond.v1

Secondary strategic archetype for affordable multifamily housing revenue bonds.

Representative evidence includes:

- housing.lihtc_status
- housing.hap_section8_revenue
- housing.rental_income
- housing.occupancy_rate
- housing.site_control
- housing.affordability_restrictions
- capital.project-cost
- capital.equity_contribution
- construction.permits.status

Housing is first-class in the archetype registry even if full downstream scoring/templates are staged across later ELAs.

### ucs_wte_cab_slb.v1

Mature validated archetype for UCS/waste-to-energy financings with CAB + SLB structure.

Representative evidence includes:

- feedstock.supply.mechanism
- feedstock.volume.annual
- revenue.offtake.status
- revenue.commodities.list
- cab.enabled
- cab.originalprincipial
- cab.accretionrate
- slb.enabled
- slb.kpi.1.name
- slb.verifier.name

WTE-specific logic should remain available but isolated through archetype metadata/capabilities so it does not leak into Healthcare or Housing readiness/disclosure copy.

## Implementation notes

The registry lives in src/munipal/services/sector_archetypes.py.

Projects now carry optional sector metadata:

- sector
- subsector
- archetype_id
- archetype_version

When a project is created without explicit archetype metadata, the resolver uses the current product strategy and defaults to Healthcare. Explicit Housing and WTE selections resolve to their respective archetypes.
