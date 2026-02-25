from scripts.assess_phase6_analytics_reproducibility import (
    _canonicalize_score_payload,
    evaluate_sector_reproducibility,
)


def test_canonicalize_score_payload_removes_scored_at() -> None:
    payload = {
        "scored_at": "2026-02-25T00:00:00Z",
        "summary": {"total_obligors": 10, "investable_count": 2},
        "scores": [{"obligor_name": "A", "f_score": 55.0}],
    }
    canonical = _canonicalize_score_payload(payload)
    assert "scored_at" not in canonical
    assert canonical["summary"]["total_obligors"] == 10


def test_evaluate_sector_reproducibility_ignores_scored_at_drift() -> None:
    first = {
        "scored_at": "2026-02-25T00:00:00Z",
        "summary": {"total_obligors": 5, "investable_count": 1},
        "scores": [{"obligor_name": "A", "f_score": 60.0}],
    }
    second = {
        "scored_at": "2026-02-25T00:00:01Z",
        "summary": {"total_obligors": 5, "investable_count": 1},
        "scores": [{"obligor_name": "A", "f_score": 60.0}],
    }
    status, issues = evaluate_sector_reproducibility(
        sector="waste",
        first_payload=first,
        second_payload=second,
    )
    assert status == "pass"
    assert issues == []


def test_evaluate_sector_reproducibility_flags_canonical_drift() -> None:
    first = {
        "summary": {"total_obligors": 5, "investable_count": 1},
        "scores": [{"obligor_name": "A", "f_score": 60.0}],
    }
    second = {
        "summary": {"total_obligors": 5, "investable_count": 2},
        "scores": [{"obligor_name": "A", "f_score": 61.0}],
    }
    status, issues = evaluate_sector_reproducibility(
        sector="waste",
        first_payload=first,
        second_payload=second,
    )
    assert status == "fail"
    assert any("drifted" in item for item in issues)

