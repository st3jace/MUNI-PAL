"""Warm Handoff Pack acceptance criteria and provenance contracts.

ELA-35 defines the advisor-review quality gate for BFMS handoff packs. The
contract is intentionally sector-neutral: sector playbooks can determine which
facts/artifacts are expected, while this module enforces that every outbound
claim is either traced to accepted evidence or explicitly marked missing or
unknown.
"""
from __future__ import annotations

import re
from enum import StrEnum
from typing import Literal

from pydantic import Field

from munipal.core.schemas.base import BaseSchema


class WarmHandoffValidationError(ValueError):
    """Raised when a Warm Handoff Pack contract is incomplete or unsafe."""


class ClaimSupportStatus(StrEnum):
    """Evidence support posture for a handoff-pack claim."""

    SUPPORTED = "supported"
    MISSING = "missing"
    UNKNOWN = "unknown"


HandoffAudience = Literal["registered_municipal_advisor", "bond_counsel", "underwriter", "issuer_team"]


class HandoffAcceptanceCriterion(BaseSchema):
    """Single acceptance criterion for an advisor-review Warm Handoff Pack."""

    key: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    required: bool = True
    description: str = Field(..., min_length=1)
    verification_steps: tuple[str, ...] = Field(..., min_length=1)


class HandoffSectionRequirement(BaseSchema):
    """Required section in the Warm Handoff Pack."""

    key: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=1)
    required_claim_statuses: tuple[ClaimSupportStatus, ...]


class HandoffFactRef(BaseSchema):
    """Evidence reference used by a handoff-pack claim and appendix entry."""

    fact_id: str = Field(..., min_length=1)
    schema_path: str = Field(..., min_length=1)
    value: object
    review_status: str = Field(..., min_length=1)
    artifact_id: str = Field(..., min_length=1)
    artifact_filename: str = Field(..., min_length=1)
    chunk_id: str = Field(..., min_length=1)
    page_number: int | None = None
    excerpt: str = Field(..., min_length=1)
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)


class HandoffClaim(BaseSchema):
    """Claim rendered in a Warm Handoff Pack."""

    claim_id: str = Field(..., min_length=1)
    text: str = Field(..., min_length=1)
    section_key: str = Field(..., min_length=1)
    support_status: ClaimSupportStatus
    fact_refs: list[HandoffFactRef] = Field(default_factory=list)
    missing_reason: str = ""


class ProvenanceAppendix(BaseSchema):
    """Appendix listing source provenance for all evidence-backed claims."""

    required: bool = True
    required_fields: tuple[str, ...] = (
        "fact_id",
        "schema_path",
        "review_status",
        "artifact_id",
        "artifact_filename",
        "chunk_id",
        "page_number",
        "excerpt",
        "confidence_score",
    )
    entries: list[HandoffFactRef] = Field(default_factory=list)


class WarmHandoffPackContract(BaseSchema):
    """Advisor-ready Warm Handoff Pack contract and validation payload."""

    contract_id: str = "warm_handoff_pack.v1"
    sector: str = Field(default="sector_neutral", min_length=1)
    target_audience: HandoffAudience = "registered_municipal_advisor"
    sections: tuple[HandoffSectionRequirement, ...] = Field(..., min_length=1)
    acceptance_criteria: tuple[HandoffAcceptanceCriterion, ...] = Field(..., min_length=1)
    claims: list[HandoffClaim] = Field(default_factory=list)
    provenance_appendix: ProvenanceAppendix = Field(default_factory=ProvenanceAppendix)
    liability_boundary: str = Field(..., min_length=1)


_ACCEPTANCE_CRITERIA = (
    HandoffAcceptanceCriterion(
        key="advisor_summary",
        display_name="Advisor-ready summary",
        description="Summarize the transaction, readiness posture, and open diligence questions in neutral descriptive language.",
        verification_steps=(
            "Confirm summary claims either cite accepted facts or are marked missing/unknown.",
            "Confirm language is descriptive and ready for registered municipal advisor review.",
        ),
    ),
    HandoffAcceptanceCriterion(
        key="evidence_backed_claims",
        display_name="Evidence-backed claims",
        description="Every substantive claim must trace to accepted facts with artifact, chunk, page, excerpt, and confidence provenance.",
        verification_steps=(
            "For each supported claim, confirm at least one accepted fact reference is present.",
            "Confirm each referenced fact appears in the provenance appendix.",
        ),
    ),
    HandoffAcceptanceCriterion(
        key="missing_data",
        display_name="Missing data register",
        description="Material unknowns must be explicit rather than implied as known facts.",
        verification_steps=(
            "Confirm missing/unknown claims include a missing reason.",
            "Confirm no missing value is silently rendered as a completed fact.",
        ),
    ),
    HandoffAcceptanceCriterion(
        key="risks",
        display_name="Risks and diligence flags",
        description="Risks must be framed as diligence observations for advisor review, not recommendations.",
        verification_steps=(
            "Confirm risk statements avoid approval, pricing, or issuance recommendation language.",
            "Confirm each factual risk premise traces to accepted facts or is marked unknown.",
        ),
    ),
    HandoffAcceptanceCriterion(
        key="assumptions",
        display_name="Assumption register",
        description="Assumptions must identify basis, source, and whether supporting evidence is accepted or pending.",
        verification_steps=(
            "Confirm assumptions cite accepted facts when available.",
            "Confirm unsupported assumptions are marked missing/unknown with a reason.",
        ),
    ),
    HandoffAcceptanceCriterion(
        key="advisor_next_questions",
        display_name="Advisor next questions",
        description="The pack must list questions for the registered advisor/deal team to resolve next.",
        verification_steps=(
            "Confirm questions are framed for advisor review, not as Muni-Pal instructions.",
            "Confirm question premises cite accepted facts or are marked missing/unknown.",
        ),
    ),
    HandoffAcceptanceCriterion(
        key="provenance_appendix",
        display_name="Provenance appendix",
        description="The pack includes an appendix mapping claims to accepted facts, artifact IDs, chunk IDs, pages, excerpts, and confidence.",
        verification_steps=(
            "Confirm supported claims have accepted fact references.",
            "Confirm appendix entries contain required provenance fields.",
        ),
    ),
    HandoffAcceptanceCriterion(
        key="liability_boundary",
        display_name="Liability and advisory boundary",
        description="The pack states Muni-Pal does not approve, size, price, recommend issuance, or replace registered professionals.",
        verification_steps=(
            "Confirm non-approval, non-sizing, non-pricing, and non-advice language is present.",
            "Confirm final decisions remain with borrower and registered advisors.",
        ),
    ),
)

_SECTION_REQUIREMENTS = (
    HandoffSectionRequirement(
        key="summary",
        display_name="Summary",
        purpose="Neutral deal/readiness summary for fast advisor orientation.",
        required_claim_statuses=(ClaimSupportStatus.SUPPORTED, ClaimSupportStatus.MISSING, ClaimSupportStatus.UNKNOWN),
    ),
    HandoffSectionRequirement(
        key="evidence_backed_claims",
        display_name="Evidence-Backed Claims",
        purpose="Claims with accepted-fact source references.",
        required_claim_statuses=(ClaimSupportStatus.SUPPORTED,),
    ),
    HandoffSectionRequirement(
        key="missing_data",
        display_name="Missing Data",
        purpose="Explicit unresolved facts and required follow-up evidence.",
        required_claim_statuses=(ClaimSupportStatus.MISSING, ClaimSupportStatus.UNKNOWN),
    ),
    HandoffSectionRequirement(
        key="risks",
        display_name="Risks",
        purpose="Diligence observations and risk flags for advisor review.",
        required_claim_statuses=(ClaimSupportStatus.SUPPORTED, ClaimSupportStatus.UNKNOWN),
    ),
    HandoffSectionRequirement(
        key="assumptions",
        display_name="Assumptions",
        purpose="Assumptions with source basis and confidence posture.",
        required_claim_statuses=(ClaimSupportStatus.SUPPORTED, ClaimSupportStatus.UNKNOWN),
    ),
    HandoffSectionRequirement(
        key="advisor_next_questions",
        display_name="Advisor Next Questions",
        purpose="Questions for registered advisor, counsel, underwriter, or issuer team to resolve.",
        required_claim_statuses=(ClaimSupportStatus.SUPPORTED, ClaimSupportStatus.UNKNOWN),
    ),
    HandoffSectionRequirement(
        key="provenance_appendix",
        display_name="Provenance Appendix",
        purpose="Claim-to-fact traceability appendix.",
        required_claim_statuses=(ClaimSupportStatus.SUPPORTED,),
    ),
    HandoffSectionRequirement(
        key="liability_boundary",
        display_name="Liability Boundary",
        purpose="Non-approval, non-pricing, non-advice boundary language.",
        required_claim_statuses=(ClaimSupportStatus.UNKNOWN,),
    ),
)

_LIABILITY_BOUNDARY = (
    "Muni-Pal provides an evidence organization and readiness support artifact for review by the "
    "borrower, issuer team, registered municipal advisor, bond counsel, underwriter, and other deal "
    "professionals. Muni-Pal does not approve the financing, does not size the bonds, does not price "
    "the bonds, does not recommend issuance, does not recommend timing, structure, sale method, "
    "participants, credit enhancement, ratings strategy, or disclosure content, and does not replace "
    "the borrower’s registered municipal advisor, bond counsel, underwriter, or other professionals. "
    "All final decisions remain with the borrower/issuer and their registered advisors."
)

_PROHIBITED_PATTERNS = (
    re.compile(r"\bmuni[- ]?pal\s+(recommends?|advises?|approves?|certifies?)\b", re.IGNORECASE),
    re.compile(r"\b(approved|cleared|certified)\s+for\s+(pricing|issuance|sale)\b", re.IGNORECASE),
    re.compile(r"\b(recommend|recommends|recommended|advises|advice)\s+issuing\s+now\b", re.IGNORECASE),
)


def build_warm_handoff_acceptance_criteria() -> tuple[HandoffAcceptanceCriterion, ...]:
    """Return the canonical ELA-35 acceptance criteria."""

    return _ACCEPTANCE_CRITERIA


def build_warm_handoff_pack_contract(sector: str = "sector_neutral") -> WarmHandoffPackContract:
    """Build the canonical Warm Handoff Pack contract for a sector."""

    return WarmHandoffPackContract(
        sector=sector,
        sections=_SECTION_REQUIREMENTS,
        acceptance_criteria=_ACCEPTANCE_CRITERIA,
        liability_boundary=_LIABILITY_BOUNDARY,
    )


def validate_warm_handoff_pack_contract(
    contract: WarmHandoffPackContract,
) -> WarmHandoffPackContract:
    """Validate claim traceability, provenance appendix, and liability boundaries."""

    section_keys = {section.key for section in contract.sections}
    criterion_keys = {criterion.key for criterion in contract.acceptance_criteria}
    required = {criterion.key for criterion in _ACCEPTANCE_CRITERIA}
    missing_criteria = required - criterion_keys
    if missing_criteria:
        raise WarmHandoffValidationError(f"Missing acceptance criteria: {sorted(missing_criteria)}")

    appendix_fact_ids = {entry.fact_id for entry in contract.provenance_appendix.entries}

    for claim in contract.claims:
        if claim.section_key not in section_keys:
            raise WarmHandoffValidationError(f"Unknown handoff section: {claim.section_key}")

        if any(pattern.search(claim.text) for pattern in _PROHIBITED_PATTERNS):
            raise WarmHandoffValidationError("Claim contains prohibited advisory language")

        if claim.support_status == ClaimSupportStatus.SUPPORTED:
            if not claim.fact_refs:
                raise WarmHandoffValidationError("Supported claim lacks accepted fact references")
            for fact_ref in claim.fact_refs:
                if fact_ref.review_status.lower() != "approved":
                    raise WarmHandoffValidationError("Supported claim references a fact that is not approved")
                if fact_ref.fact_id not in appendix_fact_ids:
                    raise WarmHandoffValidationError("Supported claim is missing from provenance appendix")
        elif not claim.missing_reason.strip():
            raise WarmHandoffValidationError("Missing or unknown claim requires a missing reason")

    boundary = contract.liability_boundary.lower()
    for phrase in (
        "does not approve",
        "does not size",
        "does not price",
        "does not recommend issuance",
        "registered municipal advisor",
    ):
        if phrase not in boundary:
            raise WarmHandoffValidationError(f"Liability boundary missing phrase: {phrase}")

    return contract
