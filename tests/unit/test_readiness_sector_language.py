"""Sector-language regression tests for readiness recommendations."""

from munipal.services.readiness_service import RECOMMENDATION_RATIONALES


def test_generic_structurally_viable_rationale_does_not_leak_wte_terms() -> None:
    rationale = RECOMMENDATION_RATIONALES["structurally_viable"]

    assert "CAB" not in rationale
    assert "SLB" not in rationale
    assert "feedstock" not in rationale.lower()
