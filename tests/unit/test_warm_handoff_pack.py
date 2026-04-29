"""Tests for BFMS Warm Handoff Pack acceptance and provenance contracts."""

import pytest

from munipal.services.warm_handoff import (
    ClaimSupportStatus,
    HandoffClaim,
    HandoffFactRef,
    WarmHandoffValidationError,
    build_warm_handoff_acceptance_criteria,
    build_warm_handoff_pack_contract,
    validate_warm_handoff_pack_contract,
)


def _fact(path: str = "project.canonicaldescription") -> HandoffFactRef:
    return HandoffFactRef(
        fact_id="fact-1",
        schema_path=path,
        value="Hospital revenue bond for campus modernization",
        review_status="approved",
        artifact_id="artifact-1",
        artifact_filename="offering-memo.pdf",
        chunk_id="chunk-1",
        page_number=7,
        excerpt="campus modernization",
        confidence_score=0.94,
    )


def test_acceptance_criteria_cover_linear_required_sections_and_quality_gates() -> None:
    criteria = build_warm_handoff_acceptance_criteria()
    keys = {criterion.key for criterion in criteria}

    assert {
        "advisor_summary",
        "evidence_backed_claims",
        "missing_data",
        "risks",
        "assumptions",
        "advisor_next_questions",
        "provenance_appendix",
        "liability_boundary",
    } <= keys
    assert all(criterion.verification_steps for criterion in criteria)
    assert any("accepted facts" in step.lower() for criterion in criteria for step in criterion.verification_steps)


def test_pack_contract_contains_provenance_appendix_and_non_advice_boundary_language() -> None:
    contract = build_warm_handoff_pack_contract(sector="healthcare")

    section_keys = {section.key for section in contract.sections}
    assert {
        "summary",
        "evidence_backed_claims",
        "missing_data",
        "risks",
        "assumptions",
        "advisor_next_questions",
        "provenance_appendix",
        "liability_boundary",
    } <= section_keys
    assert contract.provenance_appendix.required is True
    assert "artifact_id" in contract.provenance_appendix.required_fields
    assert "chunk_id" in contract.provenance_appendix.required_fields
    assert "page_number" in contract.provenance_appendix.required_fields
    boundary = contract.liability_boundary.lower()
    assert "does not approve" in boundary
    assert "does not size" in boundary
    assert "does not price" in boundary
    assert "does not recommend issuance" in boundary
    assert "registered municipal advisor" in boundary


def test_validation_rejects_supported_claim_without_accepted_fact_trace() -> None:
    contract = build_warm_handoff_pack_contract()
    contract.claims = [
        HandoffClaim(
            claim_id="claim-1",
            text="The borrower has uploaded audited financial statements.",
            section_key="summary",
            support_status=ClaimSupportStatus.SUPPORTED,
            fact_refs=[_fact()],
        )
    ]
    contract.provenance_appendix.entries = []

    with pytest.raises(WarmHandoffValidationError, match="provenance appendix"):
        validate_warm_handoff_pack_contract(contract)


def test_validation_requires_missing_or_unknown_claims_to_be_marked_not_implied() -> None:
    contract = build_warm_handoff_pack_contract()
    contract.claims = [
        HandoffClaim(
            claim_id="claim-2",
            text="Bond amount is currently unknown.",
            section_key="missing_data",
            support_status=ClaimSupportStatus.UNKNOWN,
            missing_reason="Borrower has not provided target par amount.",
        )
    ]

    validated = validate_warm_handoff_pack_contract(contract)
    assert validated.claims[0].support_status == ClaimSupportStatus.UNKNOWN

    contract.claims[0].missing_reason = ""
    with pytest.raises(WarmHandoffValidationError, match="missing reason"):
        validate_warm_handoff_pack_contract(contract)


def test_validation_blocks_approval_pricing_or_issuance_recommendation_language() -> None:
    contract = build_warm_handoff_pack_contract()
    contract.claims = [
        HandoffClaim(
            claim_id="claim-3",
            text="Muni-Pal recommends issuing now because the deal is approved for pricing.",
            section_key="summary",
            support_status=ClaimSupportStatus.SUPPORTED,
            fact_refs=[_fact()],
        )
    ]
    contract.provenance_appendix.entries = [_fact()]

    with pytest.raises(WarmHandoffValidationError, match="prohibited advisory language"):
        validate_warm_handoff_pack_contract(contract)
