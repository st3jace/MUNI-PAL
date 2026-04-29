from __future__ import annotations

import json
import socket
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid5, NAMESPACE_URL

from munipal.core.schemas.base import ReadinessDimension
from munipal.services.fact_service import FactService
from munipal.services.playbook_data import READINESS_CONFIG, SCHEMA_PATHS
from munipal.services.readiness_service import ReadinessService

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "readiness_golden"


def _fact(raw: dict) -> SimpleNamespace:
    return SimpleNamespace(
        id=raw["id"],
        schema_path=raw["schema_path"],
        value=raw["value"],
        confidence_score=raw["confidence_score"],
        review_status=raw.get("review_status", "approved"),
        is_canonical=raw.get("is_canonical", False),
        canonical_score=raw.get("canonical_score", 0.0),
        created_at=datetime.fromisoformat(raw["created_at"]).replace(tzinfo=timezone.utc),
    )


def _service() -> ReadinessService:
    service = ReadinessService.__new__(ReadinessService)
    service._schema_path_config = {p["path"]: p for p in SCHEMA_PATHS}
    service._readiness_config = READINESS_CONFIG["dimensions"]
    return service


def _golden_output(fixture: dict) -> dict:
    service = _service()
    facts = [_fact(raw) for raw in fixture["facts"] if raw.get("review_status") == "approved"]
    facts_by_path = FactService.select_preferred_facts_by_path(facts)

    dimension_scores = {}
    total_weighted_score = 0.0
    critical_gaps = 0
    material_gaps = 0
    for dimension in ReadinessDimension:
        score = service._compute_dimension_score(dimension, facts_by_path)
        dimension_scores[dimension.value] = {
            "score": score.score,
            "weighted_contribution": round(score.weighted_contribution, 4),
            "critical_paths_covered": score.critical_paths_covered,
            "critical_paths_total": score.critical_paths_total,
            "material_paths_covered": score.material_paths_covered,
            "material_paths_total": score.material_paths_total,
            "improvement_suggestions": score.improvement_suggestions,
        }
        total_weighted_score += score.weighted_contribution
        critical_gaps += score.critical_paths_total - score.critical_paths_covered
        material_gaps += score.material_paths_total - score.material_paths_covered

    overall_score = round(total_weighted_score * 2, 2)
    recommendation, rationale = service._get_recommendation(overall_score)
    return {
        "sector": fixture["sector"],
        "project_archetype": fixture["project_archetype"],
        "overall_score": overall_score,
        "recommendation": recommendation,
        "recommendation_rationale": rationale,
        "critical_gaps_count": critical_gaps,
        "material_gaps_count": material_gaps,
        "selected_fact_ids_by_path": {
            path: fact.id for path, fact in facts_by_path.items()
        },
        "dimensions": dimension_scores,
    }


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))


def test_healthcare_golden_fixture_is_primary_and_matches_snapshot(monkeypatch) -> None:
    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network disabled")))
    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("network disabled")))
    fixture = _load_fixture("healthcare_primary")

    first = _golden_output(fixture)
    second = _golden_output(fixture)

    assert fixture["sector_priority"] == 1
    assert fixture["sector"] == "healthcare"
    assert first == second
    assert first == fixture["expected_output"]


def test_sector_golden_fixtures_cover_ucs_wte_then_housing_and_are_stable() -> None:
    fixtures = [_load_fixture("ucs_wte"), _load_fixture("housing")]

    assert [fixture["sector_priority"] for fixture in fixtures] == [2, 3]
    assert [fixture["sector"] for fixture in fixtures] == ["ucs_wte", "housing"]

    for fixture in fixtures:
        assert _golden_output(fixture) == _golden_output(fixture)
        assert _golden_output(fixture) == fixture["expected_output"]


def test_golden_fixtures_cover_missing_data_and_conflicting_evidence() -> None:
    healthcare = _load_fixture("healthcare_primary")
    output = _golden_output(healthcare)

    assert output["critical_gaps_count"] > 0
    assert output["material_gaps_count"] > 0
    assert output["selected_fact_ids_by_path"]["security.revenue.pledge"] == "healthcare-security-stronger"
    assert any(
        suggestion.startswith("Upload documents containing:")
        for dimension in output["dimensions"].values()
        for suggestion in dimension["improvement_suggestions"]
    )
