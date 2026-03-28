"""
Integration tests for Healthcare Sensing Layer.

Validates sector-aware questionnaire, readiness scoring, market intelligence,
and benchmarking against the live healthcare corpus.db.

Per plan (LAU-26): integration testing with healthcare corpus data.
"""
from __future__ import annotations

import pytest


# Healthcare-specific readiness dimensions (from risk_benchmark.py)
HEALTHCARE_DIMENSIONS = [
    "risk.technology",
    "risk.construction",
    "risk.market",
    "risk.regulatory",
    "risk.reimbursement",
]

HEALTHCARE_DIMENSION_LABELS = {
    "risk.technology": "Technology & Clinical Systems Risk",
    "risk.construction": "Facility & Capital Risk",
    "risk.market": "Market & Volume Risk",
    "risk.regulatory": "Regulatory & Compliance Risk",
    "risk.reimbursement": "Reimbursement & Payer Risk",
}


class TestSensingHealthcareSectors:
    """Healthcare sector appears in available sectors."""

    async def test_sectors_includes_healthcare(self, test_client):
        """GET /sectors should list healthcare as an available sector."""
        response = await test_client.get("/api/v1/sensing/sectors")
        assert response.status_code == 200
        sectors = response.json()
        sector_ids = [s["id"] for s in sectors]
        assert "healthcare" in sector_ids

    async def test_sectors_includes_waste(self, test_client):
        """Waste sector should still be present (regression check)."""
        response = await test_client.get("/api/v1/sensing/sectors")
        assert response.status_code == 200
        sector_ids = [s["id"] for s in response.json()]
        assert "waste" in sector_ids


class TestSensingHealthcareQuestionnaire:
    """Healthcare questionnaire returns sector-specific dimensions."""

    async def test_questionnaire_returns_items(self, test_client):
        """GET /questionnaire?sector=healthcare returns non-empty list."""
        response = await test_client.get(
            "/api/v1/sensing/questionnaire", params={"sector": "healthcare"}
        )
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        assert len(items) > 0

    async def test_questionnaire_has_five_dimensions(self, test_client):
        """Healthcare questionnaire covers exactly 5 risk dimensions."""
        response = await test_client.get(
            "/api/v1/sensing/questionnaire", params={"sector": "healthcare"}
        )
        items = response.json()
        dimensions = {item["dimension"] for item in items}
        assert len(dimensions) == 5

    async def test_questionnaire_dimensions_are_healthcare_specific(self, test_client):
        """Healthcare dimensions should include reimbursement, not feedstock."""
        response = await test_client.get(
            "/api/v1/sensing/questionnaire", params={"sector": "healthcare"}
        )
        items = response.json()
        dimensions = {item["dimension"] for item in items}

        # Healthcare has reimbursement instead of feedstock
        assert "risk.reimbursement" in dimensions
        assert "risk.feedstock" not in dimensions

    async def test_questionnaire_dimension_labels(self, test_client):
        """Each item should have a dimension_label field matching healthcare config."""
        response = await test_client.get(
            "/api/v1/sensing/questionnaire", params={"sector": "healthcare"}
        )
        items = response.json()
        for item in items:
            assert "dimension_label" in item
            dim = item["dimension"]
            if dim in HEALTHCARE_DIMENSION_LABELS:
                assert item["dimension_label"] == HEALTHCARE_DIMENSION_LABELS[dim]

    async def test_questionnaire_item_structure(self, test_client):
        """Each questionnaire item has required fields."""
        response = await test_client.get(
            "/api/v1/sensing/questionnaire", params={"sector": "healthcare"}
        )
        items = response.json()
        required_keys = {"item_id", "dimension", "dimension_label", "category", "question", "points"}
        for item in items:
            assert required_keys.issubset(item.keys()), (
                f"Item {item.get('item_id')} missing keys: {required_keys - item.keys()}"
            )

    async def test_questionnaire_categories(self, test_client):
        """Each dimension should have description, mitigants, and evidence items."""
        response = await test_client.get(
            "/api/v1/sensing/questionnaire", params={"sector": "healthcare"}
        )
        items = response.json()
        for dim in HEALTHCARE_DIMENSIONS:
            dim_items = [i for i in items if i["dimension"] == dim]
            categories = {i["category"] for i in dim_items}
            assert "description" in categories, f"{dim} missing description"
            assert "mitigants" in categories, f"{dim} missing mitigants"
            assert "evidence" in categories, f"{dim} missing evidence"

    async def test_questionnaire_max_points_100(self, test_client):
        """Total max points across all items should be 100."""
        response = await test_client.get(
            "/api/v1/sensing/questionnaire", params={"sector": "healthcare"}
        )
        items = response.json()
        total = sum(item["points"] for item in items)
        assert total == 100.0

    async def test_questionnaire_differs_from_waste(self, test_client):
        """Healthcare questionnaire should differ from waste questionnaire."""
        hc_resp = await test_client.get(
            "/api/v1/sensing/questionnaire", params={"sector": "healthcare"}
        )
        waste_resp = await test_client.get(
            "/api/v1/sensing/questionnaire", params={"sector": "waste"}
        )
        hc_dims = {i["dimension"] for i in hc_resp.json()}
        waste_dims = {i["dimension"] for i in waste_resp.json()}
        assert hc_dims != waste_dims


class TestSensingHealthcareReadiness:
    """Healthcare readiness scoring against the corpus."""

    async def test_readiness_empty_responses(self, test_client):
        """Scoring with no responses should return early-stage/low score."""
        response = await test_client.post(
            "/api/v1/sensing/readiness",
            json={
                "sector": "healthcare",
                "project_name": "Test Hospital Project",
                "responses": {},
                "evidence_ids": [],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sector"] == "healthcare"
        assert data["readiness_score"] == 0.0
        assert data["tier"] == "Early Stage"

    async def test_readiness_full_responses(self, test_client):
        """Scoring with all items answered True should yield high score."""
        # First get the questionnaire to know all item IDs
        q_resp = await test_client.get(
            "/api/v1/sensing/questionnaire", params={"sector": "healthcare"}
        )
        items = q_resp.json()

        responses = {}
        evidence_ids = []
        for item in items:
            if item["category"] == "evidence":
                evidence_ids.append(item["item_id"])
            else:
                responses[item["item_id"]] = True

        response = await test_client.post(
            "/api/v1/sensing/readiness",
            json={
                "sector": "healthcare",
                "project_name": "Well-Prepared Hospital",
                "responses": responses,
                "evidence_ids": evidence_ids,
                "dscr": 1.5,
                "revenue": 100_000_000,
                "coverage_ratio": 1.4,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["sector"] == "healthcare"
        # With all items answered + strong financials, should be Bond Ready or Nearly Ready
        assert data["readiness_score"] >= 65.0
        assert data["tier"] in ("Bond Ready", "Nearly Ready")

    async def test_readiness_response_structure(self, test_client):
        """Response should contain all expected fields."""
        response = await test_client.post(
            "/api/v1/sensing/readiness",
            json={
                "sector": "healthcare",
                "project_name": "Structure Test",
                "responses": {"risk.technology.description": True},
                "evidence_ids": [],
            },
        )
        assert response.status_code == 200
        data = response.json()
        required_keys = {
            "project_name", "sector", "readiness_score", "raw_score",
            "tier", "tier_guidance", "dimensions", "financial_assessment",
            "priority_actions", "gap_analysis", "corpus_summary",
        }
        assert required_keys.issubset(data.keys())

    async def test_readiness_five_dimensions_scored(self, test_client):
        """Response dimensions should have exactly 5 entries for healthcare."""
        response = await test_client.post(
            "/api/v1/sensing/readiness",
            json={
                "sector": "healthcare",
                "project_name": "Dimension Count Test",
                "responses": {},
                "evidence_ids": [],
            },
        )
        data = response.json()
        assert len(data["dimensions"]) == 5

    async def test_readiness_reimbursement_dimension_present(self, test_client):
        """Healthcare readiness should include reimbursement dimension."""
        response = await test_client.post(
            "/api/v1/sensing/readiness",
            json={
                "sector": "healthcare",
                "project_name": "Reimbursement Check",
                "responses": {},
                "evidence_ids": [],
            },
        )
        data = response.json()
        dim_names = [d["dimension"] for d in data["dimensions"]]
        assert "risk.reimbursement" in dim_names
        assert "risk.feedstock" not in dim_names

    async def test_readiness_partial_responses(self, test_client):
        """Partial completion should yield mid-range score."""
        response = await test_client.post(
            "/api/v1/sensing/readiness",
            json={
                "sector": "healthcare",
                "project_name": "Partial Hospital",
                "responses": {
                    "risk.technology.description": True,
                    "risk.technology.mitigants": True,
                    "risk.construction.description": True,
                    "risk.market.description": True,
                },
                "evidence_ids": [],
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Partial: should be above zero but not Bond Ready
        assert 0 < data["readiness_score"] < 85


class TestSensingHealthcareMarketIntelligence:
    """Market intelligence generation from healthcare corpus."""

    async def test_market_intelligence_returns_200(self, test_client):
        """GET /market-intelligence?sector=healthcare should succeed."""
        response = await test_client.get(
            "/api/v1/sensing/market-intelligence",
            params={"sector": "healthcare"},
        )
        assert response.status_code == 200

    async def test_market_intelligence_has_content(self, test_client):
        """Response should contain market intelligence data."""
        response = await test_client.get(
            "/api/v1/sensing/market-intelligence",
            params={"sector": "healthcare"},
        )
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0


class TestSensingHealthcareBenchmark:
    """Benchmarking against healthcare corpus."""

    async def test_benchmark_returns_200(self, test_client):
        """POST /benchmark with healthcare sector should succeed."""
        response = await test_client.post(
            "/api/v1/sensing/benchmark",
            json={
                "sector": "healthcare",
                "deal_size": 50_000_000,
                "state": "AZ",
                "rating": "A",
                "maturity": 30.0,
            },
        )
        assert response.status_code == 200

    async def test_benchmark_has_content(self, test_client):
        """Benchmark response should contain meaningful data."""
        response = await test_client.post(
            "/api/v1/sensing/benchmark",
            json={
                "sector": "healthcare",
                "deal_size": 25_000_000,
                "state": "CA",
                "rating": "BBB",
                "maturity": 20.0,
            },
        )
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0


class TestSensingHealthcareInvalidSector:
    """Invalid sector handling."""

    async def test_invalid_sector_market_intel_returns_404(self, test_client):
        """Market intelligence for unknown sector should return 404."""
        response = await test_client.get(
            "/api/v1/sensing/market-intelligence", params={"sector": "nonexistent"}
        )
        assert response.status_code == 404

    async def test_invalid_sector_readiness_returns_404(self, test_client):
        """Readiness scoring for unknown sector should return 404."""
        response = await test_client.post(
            "/api/v1/sensing/readiness",
            json={
                "sector": "nonexistent",
                "project_name": "Invalid",
                "responses": {},
                "evidence_ids": [],
            },
        )
        assert response.status_code == 404
