"""Advisor/compliance language guardrails for readiness copy."""

from munipal.services import readiness_service


def test_readiness_high_score_copy_requires_professional_review_boundary() -> None:
    label = readiness_service.RECOMMENDATION_LABELS["ready_for_broad_market"]
    rationale = readiness_service.RECOMMENDATION_RATIONALES["ready_for_broad_market"]
    rendered = f"{label} {rationale}".lower()

    assert "ready for broad market engagement" not in rendered
    assert "formal rfp process" not in rendered
    assert "competitive underwriter selection" not in rendered
    assert "advisor" in rendered
    assert "review" in rendered
    assert "does not" in rendered or "subject to" in rendered
