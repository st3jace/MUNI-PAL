"""Reusable, versioned sector playbook schema for BFMS.

Sector playbooks are the product-level configuration contract for adding a new
sector without baking UCS/WTE assumptions into platform services.  The schema is
intentionally sector-neutral: WTE is represented as data, not as special code.
"""
from __future__ import annotations

from typing import Literal

from pydantic import Field

from munipal.core.schemas.base import BaseSchema
from munipal.services.sector_archetypes import (
    HEALTHCARE_HOSPITAL,
    HOUSING_AFFORDABLE_MULTIFAMILY,
    UCS_WTE_CAB_SLB,
)

LifecycleStage = Literal["pilot", "production", "deprecated"]
FactValueType = Literal["string", "number", "boolean", "currency", "percentage", "date", "list", "object"]
ArtifactRequirementLevel = Literal["required", "recommended", "optional"]


class SectorPlaybookValidationError(ValueError):
    """Raised when a sector playbook is incomplete or ambiguous."""


class SectorPlaybookMetadata(BaseSchema):
    """Stable identity and migration metadata for a sector playbook."""

    playbook_id: str = Field(..., min_length=1)
    archetype_id: str = Field(..., min_length=1)
    sector: str = Field(..., min_length=1)
    subsector: str | None = None
    display_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    lifecycle_stage: LifecycleStage
    supersedes_version: str | None = None
    migration_notes: str | None = None


class RequiredArtifact(BaseSchema):
    """Artifact or evidence package expected for a sector playbook."""

    artifact_key: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    requirement_level: ArtifactRequirementLevel
    accepted_file_types: tuple[str, ...] = Field(default_factory=tuple)
    description: str = Field(..., min_length=1)


class FactDefinition(BaseSchema):
    """A sector fact that may be extracted, manually entered, and reviewed."""

    path: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    value_type: FactValueType
    required: bool = True
    artifact_keys: tuple[str, ...] = Field(default_factory=tuple)
    description: str = Field(..., min_length=1)
    liability_note: str | None = None


class ReadinessRule(BaseSchema):
    """Deterministic readiness rule referencing declared facts/artifacts."""

    rule_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    dimension: str = Field(..., min_length=1)
    fact_paths: tuple[str, ...] = Field(..., min_length=1)
    artifact_keys: tuple[str, ...] = Field(default_factory=tuple)
    weight: float = Field(..., gt=0.0, le=1.0)
    pass_condition: str = Field(..., min_length=1)


class DeliverableTemplate(BaseSchema):
    """Output template enabled by a sector playbook."""

    output_key: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    template_ref: str = Field(..., min_length=1)
    required_fact_paths: tuple[str, ...] = Field(default_factory=tuple)
    disclaimer_keys: tuple[str, ...] = Field(default_factory=tuple)


class LiabilityDisclaimer(BaseSchema):
    """Reusable disclaimer text associated with facts or deliverables."""

    disclaimer_key: str = Field(..., min_length=1)
    applies_to: tuple[str, ...] = Field(..., min_length=1)
    text: str = Field(..., min_length=1)


class SectorPlaybook(BaseSchema):
    """Complete sector onboarding playbook schema."""

    metadata: SectorPlaybookMetadata
    required_artifacts: list[RequiredArtifact]
    fact_definitions: list[FactDefinition]
    readiness_rules: list[ReadinessRule]
    deliverable_templates: list[DeliverableTemplate]
    liability_disclaimers: list[LiabilityDisclaimer]


def _ensure_unique(values: list[str], label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise SectorPlaybookValidationError(f"duplicate {label}: {value}")
        seen.add(value)


def validate_sector_playbook(playbook: SectorPlaybook) -> SectorPlaybook:
    """Validate completeness and cross-references for a sector playbook."""

    required_sections = {
        "required_artifacts": playbook.required_artifacts,
        "fact_definitions": playbook.fact_definitions,
        "readiness_rules": playbook.readiness_rules,
        "deliverable_templates": playbook.deliverable_templates,
        "liability_disclaimers": playbook.liability_disclaimers,
    }
    for section, values in required_sections.items():
        if not values:
            raise SectorPlaybookValidationError(f"{section} must not be empty")

    artifact_keys = [artifact.artifact_key for artifact in playbook.required_artifacts]
    fact_paths = [fact.path for fact in playbook.fact_definitions]
    rule_ids = [rule.rule_id for rule in playbook.readiness_rules]
    output_keys = [template.output_key for template in playbook.deliverable_templates]
    disclaimer_keys = [disclaimer.disclaimer_key for disclaimer in playbook.liability_disclaimers]

    _ensure_unique(artifact_keys, "artifact key")
    _ensure_unique(fact_paths, "fact path")
    _ensure_unique(rule_ids, "readiness rule")
    _ensure_unique(output_keys, "deliverable template")
    _ensure_unique(disclaimer_keys, "liability disclaimer")

    artifact_key_set = set(artifact_keys)
    fact_path_set = set(fact_paths)
    disclaimer_key_set = set(disclaimer_keys)

    for fact in playbook.fact_definitions:
        for artifact_key in fact.artifact_keys:
            if artifact_key not in artifact_key_set:
                raise SectorPlaybookValidationError(
                    f"fact {fact.path} references unknown artifact key: {artifact_key}"
                )

    for rule in playbook.readiness_rules:
        for fact_path in rule.fact_paths:
            if fact_path not in fact_path_set:
                raise SectorPlaybookValidationError(
                    f"readiness rule {rule.rule_id} references unknown fact path: {fact_path}"
                )
        for artifact_key in rule.artifact_keys:
            if artifact_key not in artifact_key_set:
                raise SectorPlaybookValidationError(
                    f"readiness rule {rule.rule_id} references unknown artifact key: {artifact_key}"
                )

    for template in playbook.deliverable_templates:
        for fact_path in template.required_fact_paths:
            if fact_path not in fact_path_set:
                raise SectorPlaybookValidationError(
                    f"deliverable {template.output_key} references unknown fact path: {fact_path}"
                )
        for disclaimer_key in template.disclaimer_keys:
            if disclaimer_key not in disclaimer_key_set:
                raise SectorPlaybookValidationError(
                    f"deliverable {template.output_key} references unknown disclaimer: {disclaimer_key}"
                )

    if playbook.metadata.lifecycle_stage == "production" and not playbook.metadata.description:
        raise SectorPlaybookValidationError("production playbooks require metadata description")

    return playbook


def migrate_pilot_to_production(
    playbook: SectorPlaybook,
    *,
    new_version: str,
    migration_notes: str,
) -> SectorPlaybook:
    """Promote a validated pilot playbook to a new production version."""

    if playbook.metadata.lifecycle_stage != "pilot":
        raise SectorPlaybookValidationError("only pilot playbooks can be migrated to production")
    if not new_version or new_version == playbook.metadata.version:
        raise SectorPlaybookValidationError("new_version must be a non-empty version distinct from the pilot")
    if not migration_notes.strip():
        raise SectorPlaybookValidationError("migration_notes are required for pilot-to-production migration")

    payload = playbook.model_dump()
    payload["metadata"] = payload["metadata"] | {
        "version": new_version,
        "lifecycle_stage": "production",
        "supersedes_version": playbook.metadata.version,
        "migration_notes": migration_notes.strip(),
    }
    return validate_sector_playbook(SectorPlaybook.model_validate(payload))



def _display_from_path(path: str) -> str:
    return path.replace(".", " ").replace("-", " ").title()


_HEALTHCARE_ARTIFACTS = [
    RequiredArtifact(
        artifact_key="issuer_authority",
        display_name="Issuer authority and 501(c)(3) borrower package",
        requirement_level="required",
        accepted_file_types=("pdf", "docx"),
        description="Issuer jurisdiction, inducement, nonprofit borrower status, and revenue pledge evidence.",
    ),
    RequiredArtifact(
        artifact_key="licensure_accreditation",
        display_name="Healthcare licensure, CMS certification, and accreditation",
        requirement_level="required",
        accepted_file_types=("pdf", "docx"),
        description="Hospital licensure, CMS certification, Joint Commission or equivalent accreditation, and EHR/clinical compliance support.",
    ),
    RequiredArtifact(
        artifact_key="financial_operating_metrics",
        display_name="Financial and operating metrics package",
        requirement_level="required",
        accepted_file_types=("pdf", "xlsx", "csv"),
        description="Net patient revenue, payor mix, DSCR, days cash, cash-to-debt, margins, and utilization trends.",
    ),
    RequiredArtifact(
        artifact_key="clinical_service_area",
        display_name="Clinical service area and physician alignment evidence",
        requirement_level="recommended",
        accepted_file_types=("pdf", "docx", "xlsx"),
        description="Service area, utilization, physician alignment, and strategic clinical positioning evidence.",
    ),
]

_HEALTHCARE_FACT_ARTIFACTS = {
    "parties.issuer.name": ("issuer_authority",),
    "parties.issuer.jurisdiction": ("issuer_authority",),
    "governance.inducement": ("issuer_authority",),
    "security.revenue.pledge": ("issuer_authority",),
    "healthcare.facility_type": ("licensure_accreditation",),
    "healthcare.licensure": ("licensure_accreditation",),
    "healthcare.cms_certification": ("licensure_accreditation",),
    "healthcare.accreditation": ("licensure_accreditation",),
    "healthcare.ehr_platform": ("licensure_accreditation",),
    "healthcare.net_patient_revenue": ("financial_operating_metrics",),
    "healthcare.payor_mix": ("financial_operating_metrics",),
    "finmodel.outputs.dscrbase": ("financial_operating_metrics",),
    "finmodel.inputs.dscr.minimum": ("financial_operating_metrics",),
    "liquidity.days_cash_on_hand": ("financial_operating_metrics",),
    "liquidity.cash_to_debt": ("financial_operating_metrics",),
    "opex.margin": ("financial_operating_metrics",),
    "capital.project-cost": ("financial_operating_metrics",),
    "healthcare.service_area": ("clinical_service_area",),
    "healthcare.physician_alignment": ("clinical_service_area",),
    "healthcare.utilization.trend": ("clinical_service_area",),
}

_HEALTHCARE_FACT_PATHS = tuple(dict.fromkeys((*HEALTHCARE_HOSPITAL.required_evidence_paths, "healthcare.ehr_platform", "healthcare.physician_alignment", "healthcare.utilization.trend", "liquidity.cash_to_debt")))


HEALTHCARE_SECTOR_PLAYBOOK = validate_sector_playbook(
    SectorPlaybook(
        metadata=SectorPlaybookMetadata(
            playbook_id="healthcare_501c3_hospital_sector_playbook",
            archetype_id=HEALTHCARE_HOSPITAL.id,
            sector=HEALTHCARE_HOSPITAL.sector,
            subsector=HEALTHCARE_HOSPITAL.subsector,
            display_name=HEALTHCARE_HOSPITAL.display_name,
            description="Production playbook for nonprofit hospital and health-system 501(c)(3) revenue bond readiness.",
            version=HEALTHCARE_HOSPITAL.version,
            lifecycle_stage="production",
        ),
        required_artifacts=_HEALTHCARE_ARTIFACTS,
        fact_definitions=[
            FactDefinition(
                path=path,
                display_name=_display_from_path(path),
                value_type="currency" if path in {"healthcare.net_patient_revenue", "capital.project-cost"} else "percentage" if path in {"healthcare.payor_mix", "opex.margin", "liquidity.cash_to_debt"} else "number" if path in {"finmodel.outputs.dscrbase", "finmodel.inputs.dscr.minimum", "liquidity.days_cash_on_hand"} else "string",
                required=True,
                artifact_keys=_HEALTHCARE_FACT_ARTIFACTS.get(path, ()),
                description=f"Healthcare sector fact required for hospital revenue bond readiness: {path}.",
                liability_note="Subject to healthcare municipal advisor, bond counsel, and management verification before disclosure use.",
            )
            for path in _HEALTHCARE_FACT_PATHS
        ],
        readiness_rules=[
            ReadinessRule(
                rule_id="healthcare_regulatory_readiness",
                display_name="Licensure, CMS, accreditation, and EHR readiness",
                dimension="regulatory_clinical",
                fact_paths=("healthcare.licensure", "healthcare.cms_certification", "healthcare.accreditation", "healthcare.ehr_platform"),
                artifact_keys=("licensure_accreditation",),
                weight=0.25,
                pass_condition="Licensure, CMS participation, accreditation, and EHR evidence are source-backed.",
            ),
            ReadinessRule(
                rule_id="healthcare_revenue_liquidity_readiness",
                display_name="Revenue, payor mix, DSCR, liquidity, and leverage readiness",
                dimension="financial_operating",
                fact_paths=("healthcare.net_patient_revenue", "healthcare.payor_mix", "finmodel.outputs.dscrbase", "liquidity.days_cash_on_hand", "liquidity.cash_to_debt"),
                artifact_keys=("financial_operating_metrics",),
                weight=0.40,
                pass_condition="Core financial and operating metrics are complete enough for advisor review.",
            ),
            ReadinessRule(
                rule_id="healthcare_service_area_readiness",
                display_name="Service area, utilization, and physician alignment readiness",
                dimension="market_clinical_strategy",
                fact_paths=("healthcare.service_area", "healthcare.utilization.trend", "healthcare.physician_alignment"),
                artifact_keys=("clinical_service_area",),
                weight=0.20,
                pass_condition="Clinical market and utilization evidence supports the financing narrative.",
            ),
            ReadinessRule(
                rule_id="healthcare_issuer_security_readiness",
                display_name="Issuer authority and revenue pledge readiness",
                dimension="issuer_security",
                fact_paths=("parties.issuer.name", "parties.issuer.jurisdiction", "governance.inducement", "security.revenue.pledge"),
                artifact_keys=("issuer_authority",),
                weight=0.15,
                pass_condition="Issuer authority and revenue pledge evidence is present.",
            ),
        ],
        deliverable_templates=[
            DeliverableTemplate(
                output_key=output_key,
                display_name=_display_from_path(output_key),
                template_ref=f"sector_playbooks/healthcare/{output_key}.md",
                required_fact_paths=HEALTHCARE_HOSPITAL.readiness_paths,
                disclaimer_keys=("advisor_review_required", "healthcare_regulatory_review_required"),
            )
            for output_key in HEALTHCARE_HOSPITAL.deliverables
        ],
        liability_disclaimers=[
            LiabilityDisclaimer(
                disclaimer_key="advisor_review_required",
                applies_to=("facts", "deliverables"),
                text="Healthcare sector facts are decision-support inputs and require qualified municipal advisor and bond counsel review before disclosure use.",
            ),
            LiabilityDisclaimer(
                disclaimer_key="healthcare_regulatory_review_required",
                applies_to=("licensure_accreditation", "disclosure_summary"),
                text="Licensure, CMS certification, accreditation, reimbursement, and clinical compliance statements require borrower management and regulatory counsel confirmation.",
            ),
        ],
    )
)

_HOUSING_ARTIFACTS = [
    RequiredArtifact(
        artifact_key="issuer_borrower_authority",
        display_name="Issuer, borrower, and revenue pledge package",
        requirement_level="required",
        accepted_file_types=("pdf", "docx"),
        description="Issuer, borrower, bond authorization, and pledged revenue evidence for multifamily housing bonds.",
    ),
    RequiredArtifact(
        artifact_key="subsidy_stack",
        display_name="LIHTC, HAP, subsidy, and affordability restriction stack",
        requirement_level="required",
        accepted_file_types=("pdf", "docx", "xlsx"),
        description="LIHTC status, HAP/Section 8 revenue, subordinate subsidies, and affordability covenant evidence.",
    ),
    RequiredArtifact(
        artifact_key="rent_roll_operating",
        display_name="Rent roll, occupancy, and operating revenue package",
        requirement_level="required",
        accepted_file_types=("xlsx", "csv", "pdf"),
        description="Rental income, ancillary revenue, occupancy, expenses, and stabilized operating metrics.",
    ),
    RequiredArtifact(
        artifact_key="site_control_permits",
        display_name="Site control, permits, and construction readiness package",
        requirement_level="required",
        accepted_file_types=("pdf", "docx", "xlsx"),
        description="Site control, permits, construction budget, sources/uses, and completion readiness evidence.",
    ),
    RequiredArtifact(
        artifact_key="market_compliance",
        display_name="Market, demographics, lease-up, and compliance risk package",
        requirement_level="recommended",
        accepted_file_types=("pdf", "docx", "xlsx", "csv"),
        description="Demographic market data, lease-up assumptions, tenant eligibility, and ongoing compliance risk support.",
    ),
]

_HOUSING_FACT_ARTIFACTS = {
    "parties.issuer.name": ("issuer_borrower_authority",),
    "parties.borrower.name": ("issuer_borrower_authority",),
    "security.revenue.pledge": ("issuer_borrower_authority",),
    "housing.project_type": ("subsidy_stack",),
    "housing.lihtc_status": ("subsidy_stack",),
    "housing.hap_section8_revenue": ("subsidy_stack",),
    "housing.affordability_restrictions": ("subsidy_stack",),
    "housing.rental_income": ("rent_roll_operating",),
    "housing.ancillary_revenue": ("rent_roll_operating",),
    "housing.occupancy_rate": ("rent_roll_operating",),
    "housing.site_control": ("site_control_permits",),
    "capital.project-cost": ("site_control_permits",),
    "capital.equity_contribution": ("site_control_permits",),
    "construction.permits.status": ("site_control_permits",),
    "market.demographics.summary": ("market_compliance",),
    "housing.lease_up_risk": ("market_compliance",),
    "housing.compliance_risk": ("market_compliance",),
}

_HOUSING_FACT_PATHS = tuple(dict.fromkeys((*HOUSING_AFFORDABLE_MULTIFAMILY.required_evidence_paths, "housing.ancillary_revenue", "housing.lease_up_risk", "housing.compliance_risk")))


HOUSING_SECTOR_PLAYBOOK = validate_sector_playbook(
    SectorPlaybook(
        metadata=SectorPlaybookMetadata(
            playbook_id="housing_affordable_multifamily_sector_playbook",
            archetype_id=HOUSING_AFFORDABLE_MULTIFAMILY.id,
            sector=HOUSING_AFFORDABLE_MULTIFAMILY.sector,
            subsector=HOUSING_AFFORDABLE_MULTIFAMILY.subsector,
            display_name=HOUSING_AFFORDABLE_MULTIFAMILY.display_name,
            description="Pilot playbook for affordable multifamily housing revenue bond readiness and sector expansion.",
            version=f"{HOUSING_AFFORDABLE_MULTIFAMILY.version}-pilot",
            lifecycle_stage="pilot",
        ),
        required_artifacts=_HOUSING_ARTIFACTS,
        fact_definitions=[
            FactDefinition(
                path=path,
                display_name=_display_from_path(path),
                value_type="currency" if path in {"housing.hap_section8_revenue", "housing.rental_income", "housing.ancillary_revenue", "capital.project-cost", "capital.equity_contribution"} else "percentage" if path == "housing.occupancy_rate" else "string",
                required=True,
                artifact_keys=_HOUSING_FACT_ARTIFACTS.get(path, ()),
                description=f"Housing sector fact required for affordable multifamily revenue bond readiness: {path}.",
                liability_note="Subject to housing finance advisor, bond counsel, and tax-credit compliance review before disclosure use.",
            )
            for path in _HOUSING_FACT_PATHS
        ],
        readiness_rules=[
            ReadinessRule(
                rule_id="housing_subsidy_stack_readiness",
                display_name="LIHTC, HAP, subsidy, and affordability readiness",
                dimension="subsidy_affordability",
                fact_paths=("housing.lihtc_status", "housing.hap_section8_revenue", "housing.affordability_restrictions"),
                artifact_keys=("subsidy_stack",),
                weight=0.30,
                pass_condition="Subsidy sources and affordability restrictions are source-backed.",
            ),
            ReadinessRule(
                rule_id="housing_operating_revenue_readiness",
                display_name="Rental revenue, ancillary revenue, and occupancy readiness",
                dimension="operating_revenue",
                fact_paths=("housing.rental_income", "housing.ancillary_revenue", "housing.occupancy_rate"),
                artifact_keys=("rent_roll_operating",),
                weight=0.25,
                pass_condition="Rent roll and operating revenue evidence supports underwriting assumptions.",
            ),
            ReadinessRule(
                rule_id="housing_site_construction_readiness",
                display_name="Site control, permits, and construction readiness",
                dimension="site_construction",
                fact_paths=("housing.site_control", "capital.project-cost", "capital.equity_contribution", "construction.permits.status"),
                artifact_keys=("site_control_permits",),
                weight=0.25,
                pass_condition="Site control, permits, and construction financing evidence is present.",
            ),
            ReadinessRule(
                rule_id="housing_market_compliance_readiness",
                display_name="Market, lease-up, and compliance readiness",
                dimension="market_compliance",
                fact_paths=("market.demographics.summary", "housing.lease_up_risk", "housing.compliance_risk"),
                artifact_keys=("market_compliance",),
                weight=0.20,
                pass_condition="Market data, lease-up risk, and compliance risk evidence is advisor-reviewable.",
            ),
        ],
        deliverable_templates=[
            DeliverableTemplate(
                output_key=output_key,
                display_name=_display_from_path(output_key),
                template_ref=f"sector_playbooks/housing/{output_key}.md",
                required_fact_paths=HOUSING_AFFORDABLE_MULTIFAMILY.readiness_paths,
                disclaimer_keys=("advisor_review_required", "housing_tax_credit_compliance_review_required"),
            )
            for output_key in HOUSING_AFFORDABLE_MULTIFAMILY.deliverables
        ],
        liability_disclaimers=[
            LiabilityDisclaimer(
                disclaimer_key="advisor_review_required",
                applies_to=("facts", "deliverables"),
                text="Housing sector facts are decision-support inputs and require qualified municipal advisor and bond counsel review before disclosure use.",
            ),
            LiabilityDisclaimer(
                disclaimer_key="housing_tax_credit_compliance_review_required",
                applies_to=("subsidy_stack", "disclosure_summary"),
                text="LIHTC, HAP, affordability, tenant eligibility, and compliance statements require housing finance, tax, and regulatory counsel confirmation.",
            ),
        ],
    )
)

_UCS_ARTIFACTS = [
    RequiredArtifact(
        artifact_key="issuer_authority",
        display_name="Issuer authority and inducement package",
        requirement_level="required",
        accepted_file_types=("pdf", "docx"),
        description="IDA issuer authority, jurisdiction, public purpose, and inducement evidence.",
    ),
    RequiredArtifact(
        artifact_key="technical_feedstock",
        display_name="Technology and feedstock diligence",
        requirement_level="required",
        accepted_file_types=("pdf", "docx", "xlsx"),
        description="UCS technology, throughput, feedstock volume, and supply confidence materials.",
    ),
    RequiredArtifact(
        artifact_key="revenue_offtake",
        display_name="Commodity revenue and offtake evidence",
        requirement_level="required",
        accepted_file_types=("pdf", "docx", "xlsx", "csv"),
        description="Commodity list, gross revenue, pricing, and offtake status support.",
    ),
    RequiredArtifact(
        artifact_key="cab_slb_terms",
        display_name="CAB and SLB structuring evidence",
        requirement_level="required",
        accepted_file_types=("pdf", "docx", "xlsx"),
        description="Capital appreciation bond terms, SLB KPI definitions, and verifier evidence.",
    ),
]

_UCS_FACT_ARTIFACTS = {
    "parties.issuer.name": ("issuer_authority",),
    "parties.issuer.jurisdiction": ("issuer_authority",),
    "governance.inducement": ("issuer_authority",),
    "technology.type": ("technical_feedstock",),
    "technology.throughput.nameplate": ("technical_feedstock",),
    "feedstock.type": ("technical_feedstock",),
    "feedstock.volume.annual": ("technical_feedstock",),
    "feedstock.supply.mechanism": ("technical_feedstock",),
    "feedstock.supply.confidence": ("technical_feedstock",),
    "revenue.offtake.status": ("revenue_offtake",),
    "revenue.commodities.list": ("revenue_offtake",),
    "revenue.gross.annual": ("revenue_offtake",),
    "cab.enabled": ("cab_slb_terms",),
    "cab.originalprincipial": ("cab_slb_terms",),
    "cab.accretionrate": ("cab_slb_terms",),
    "slb.enabled": ("cab_slb_terms",),
    "slb.kpi.1.name": ("cab_slb_terms",),
    "slb.verifier.name": ("cab_slb_terms",),
    "security.revenue.pledge": ("issuer_authority", "cab_slb_terms"),
}


def _display_from_path(path: str) -> str:
    return path.replace(".", " ").replace("-", " ").title()


UCS_WTE_SECTOR_PLAYBOOK = validate_sector_playbook(
    SectorPlaybook(
        metadata=SectorPlaybookMetadata(
            playbook_id="ucs_wte_cab_slb_sector_playbook",
            archetype_id=UCS_WTE_CAB_SLB.id,
            sector=UCS_WTE_CAB_SLB.sector,
            subsector=UCS_WTE_CAB_SLB.subsector,
            display_name=UCS_WTE_CAB_SLB.display_name,
            description="Reusable production playbook for UCS/WTE CAB+SLB revenue bond onboarding.",
            version=UCS_WTE_CAB_SLB.version,
            lifecycle_stage="production",
        ),
        required_artifacts=_UCS_ARTIFACTS,
        fact_definitions=[
            FactDefinition(
                path=path,
                display_name=_display_from_path(path),
                value_type="list" if path.endswith(".list") else "boolean" if path.endswith(".enabled") else "string",
                required=True,
                artifact_keys=_UCS_FACT_ARTIFACTS.get(path, ()),
                description=f"Sector fact required for UCS/WTE readiness: {path}.",
                liability_note="Subject to advisor verification against source documents before disclosure use.",
            )
            for path in UCS_WTE_CAB_SLB.required_evidence_paths
        ],
        readiness_rules=[
            ReadinessRule(
                rule_id="technology_feedstock_readiness",
                display_name="Technology and feedstock readiness",
                dimension="project_technology_feedstock",
                fact_paths=(
                    "technology.type",
                    "technology.throughput.nameplate",
                    "feedstock.supply.mechanism",
                    "feedstock.supply.confidence",
                ),
                artifact_keys=("technical_feedstock",),
                weight=0.30,
                pass_condition="Required technology and feedstock facts are present and source-backed.",
            ),
            ReadinessRule(
                rule_id="commodity_revenue_readiness",
                display_name="Commodity revenue and offtake readiness",
                dimension="revenue_offtake",
                fact_paths=("revenue.offtake.status", "revenue.commodities.list", "revenue.gross.annual"),
                artifact_keys=("revenue_offtake",),
                weight=0.25,
                pass_condition="Commodity list, gross annual revenue, and offtake status are supportable.",
            ),
            ReadinessRule(
                rule_id="cab_slb_structuring_readiness",
                display_name="CAB and SLB structuring readiness",
                dimension="cab_slb",
                fact_paths=(
                    "cab.enabled",
                    "cab.originalprincipial",
                    "cab.accretionrate",
                    "slb.enabled",
                    "slb.kpi.1.name",
                    "slb.verifier.name",
                ),
                artifact_keys=("cab_slb_terms",),
                weight=0.25,
                pass_condition="CAB terms, SLB KPI, and verifier facts are available for advisor review.",
            ),
            ReadinessRule(
                rule_id="issuer_security_readiness",
                display_name="Issuer authority and pledged security readiness",
                dimension="issuer_security",
                fact_paths=(
                    "parties.issuer.name",
                    "parties.issuer.jurisdiction",
                    "governance.inducement",
                    "security.revenue.pledge",
                ),
                artifact_keys=("issuer_authority",),
                weight=0.20,
                pass_condition="Issuer, inducement, and revenue pledge evidence is present.",
            ),
        ],
        deliverable_templates=[
            DeliverableTemplate(
                output_key=output_key,
                display_name=_display_from_path(output_key),
                template_ref=f"sector_playbooks/ucs_wte/{output_key}.md",
                required_fact_paths=UCS_WTE_CAB_SLB.readiness_paths,
                disclaimer_keys=("advisor_review_required", "no_municipal_obligation"),
            )
            for output_key in UCS_WTE_CAB_SLB.deliverables
        ],
        liability_disclaimers=[
            LiabilityDisclaimer(
                disclaimer_key="advisor_review_required",
                applies_to=("facts", "deliverables"),
                text="Extracted sector facts are decision-support inputs and require qualified advisor review before use in offering or disclosure materials.",
            ),
            LiabilityDisclaimer(
                disclaimer_key="no_municipal_obligation",
                applies_to=("disclosure_summary", "external_advisory_package"),
                text="Revenue bond analysis does not imply a general obligation of the municipal issuer unless explicitly documented by counsel.",
            ),
        ],
    )
)

_SECTOR_PLAYBOOKS = {
    playbook.metadata.playbook_id: playbook
    for playbook in (HEALTHCARE_SECTOR_PLAYBOOK, HOUSING_SECTOR_PLAYBOOK, UCS_WTE_SECTOR_PLAYBOOK)
}
_SECTOR_PLAYBOOK_ALIASES = {
    "healthcare": HEALTHCARE_SECTOR_PLAYBOOK.metadata.playbook_id,
    "healthcare_hospital": HEALTHCARE_SECTOR_PLAYBOOK.metadata.playbook_id,
    "healthcare_501c3_hospital_revenue_bond": HEALTHCARE_SECTOR_PLAYBOOK.metadata.playbook_id,
    "housing": HOUSING_SECTOR_PLAYBOOK.metadata.playbook_id,
    "housing_affordable_multifamily": HOUSING_SECTOR_PLAYBOOK.metadata.playbook_id,
    "housing_affordable_multifamily_revenue_bond": HOUSING_SECTOR_PLAYBOOK.metadata.playbook_id,
    "waste": UCS_WTE_SECTOR_PLAYBOOK.metadata.playbook_id,
    "wte": UCS_WTE_SECTOR_PLAYBOOK.metadata.playbook_id,
    "ucs": UCS_WTE_SECTOR_PLAYBOOK.metadata.playbook_id,
    "ucs_wte_cab_slb": UCS_WTE_SECTOR_PLAYBOOK.metadata.playbook_id,
}


def list_sector_playbooks() -> list[SectorPlaybook]:
    """List focused-sector playbooks in current product strategy order."""

    return [HEALTHCARE_SECTOR_PLAYBOOK, HOUSING_SECTOR_PLAYBOOK, UCS_WTE_SECTOR_PLAYBOOK]


def get_sector_playbook(key: str) -> SectorPlaybook:
    """Return a sector playbook by playbook id, archetype id, or sector alias."""

    normalized = key.strip().lower().replace("-", "_").replace("/", "_").replace(" ", "_")
    playbook_id = _SECTOR_PLAYBOOK_ALIASES.get(normalized, key)
    try:
        return _SECTOR_PLAYBOOKS[playbook_id]
    except KeyError as exc:
        raise KeyError(f"Unknown sector playbook: {key}") from exc
