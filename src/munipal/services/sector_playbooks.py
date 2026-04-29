"""Reusable, versioned sector playbook schema for BFMS.

Sector playbooks are the product-level configuration contract for adding a new
sector without baking UCS/WTE assumptions into platform services.  The schema is
intentionally sector-neutral: WTE is represented as data, not as special code.
"""
from __future__ import annotations

from typing import Literal

from pydantic import Field

from munipal.core.schemas.base import BaseSchema
from munipal.services.sector_archetypes import UCS_WTE_CAB_SLB

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
