"""
Legal corpus lookup and recommendation helpers.

Provides a lightweight bridge between the generated EMMA legal-template
catalog and runtime clause recommendation flows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from munipal.config import get_settings

FEATURE_TO_DOC_CLASSES: dict[str, set[str]] = {
    "additional_bonds_test": {"trust_indenture", "master_trust_indenture"},
    "debt_service_reserve_fund": {"trust_indenture", "master_trust_indenture"},
    "rate_covenant": {"trust_indenture", "loan_agreement"},
    "flow_of_funds": {"trust_indenture", "master_trust_indenture"},
    "event_of_default": {"trust_indenture", "loan_agreement", "credit_agreement"},
    "cross_default": {"loan_agreement", "credit_agreement"},
    "tip_fee": {"tip_fee_agreement", "service_agreement"},
    "power_purchase": {"power_purchase_agreement"},
    "interconnection": {"interconnection_agreement"},
    "environmental_permit": {"environmental_permit"},
    "lpa_waterfall": {"limited_partnership_agreement"},
    "side_letter": {"side_letter"},
    "subscription": {"subscription_agreement"},
    "operating_agreement": {"operating_agreement"},
    "purchase_sale": {"purchase_and_sale_agreement"},
    "continuing_disclosure": {"continuing_disclosure_agreement", "event_notice"},
    "official_statement": {"official_statement"},
}


DOC_TYPE_CODE_TO_DOC_CLASSES: dict[str, set[str]] = {
    "trust_indenture": {"trust_indenture", "master_trust_indenture"},
    "loan_agreement": {"loan_agreement", "credit_agreement"},
    "bond_purchase_agreement": {"bond_purchase_agreement"},
    "continuing_disclosure_agreement": {"continuing_disclosure_agreement", "event_notice"},
    "letter_of_credit": {"letter_of_credit_reimbursement_agreement"},
    "remarketing_agreement": {"remarketing_agreement"},
    "isda_master_agreement": {"isda_master_agreement"},
    "official_statement": {"official_statement"},
    "preliminary_official_statement": {"official_statement"},
    "tax_certificate": {"tax_certificate"},
    "nda": {"nda"},
    "loi_term_sheet": {"letter_of_intent"},
}


class LegalCorpusService:
    """Read and query generated legal-template catalog data."""

    def __init__(self, catalog_path: str | None = None):
        settings = get_settings()
        self.catalog_path = Path(catalog_path or settings.legal_template_catalog_path)
        self._catalog = self._load_catalog()
        self._class_index = self._build_class_index(self._catalog)

    @staticmethod
    def _build_class_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
        classes = catalog.get("document_classes", [])
        if not isinstance(classes, list):
            return {}

        index: dict[str, dict[str, Any]] = {}
        for item in classes:
            if not isinstance(item, dict):
                continue
            class_name = item.get("class_name")
            if isinstance(class_name, str) and class_name.strip():
                index[class_name.strip().lower()] = item
        return index

    def _load_catalog(self) -> dict[str, Any]:
        if not self.catalog_path.exists():
            return {}

        try:
            raw = self.catalog_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except Exception:  # noqa: BLE001
            return {}
        return {}

    def has_catalog(self) -> bool:
        return bool(self._class_index)

    def recommend_document_classes(
        self,
        *,
        document_type_code: str | None,
        deal_features: list[str],
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Score document classes by document type + deal feature signals."""
        scores: dict[str, float] = {}
        reasons: dict[str, list[str]] = {}

        for feature in self._normalize_features(deal_features):
            for class_name in FEATURE_TO_DOC_CLASSES.get(feature, set()):
                self._bump_score(
                    scores,
                    reasons,
                    class_name,
                    delta=2.0,
                    reason=f"feature:{feature}",
                )

        if document_type_code:
            code = document_type_code.strip().lower()
            for class_name in DOC_TYPE_CODE_TO_DOC_CLASSES.get(code, set()):
                self._bump_score(
                    scores,
                    reasons,
                    class_name,
                    delta=3.0,
                    reason=f"document_type:{code}",
                )

        results: list[dict[str, Any]] = []
        for class_name, score in sorted(scores.items(), key=lambda item: item[1], reverse=True):
            catalog_item = self._class_index.get(class_name)
            sample_files = []
            total_documents = 0
            top_features = []

            if catalog_item:
                sample_files = catalog_item.get("sample_files", []) or []
                total_documents = int(catalog_item.get("count", 0) or 0)
                top_features = catalog_item.get("top_features", []) or []

            results.append(
                {
                    "class_name": class_name,
                    "score": round(score, 3),
                    "reasons": reasons.get(class_name, []),
                    "count": total_documents,
                    "sample_files": sample_files[:5],
                    "top_features": top_features[:5],
                }
            )

        return results[:limit]

    @staticmethod
    def _normalize_features(features: list[str]) -> list[str]:
        seen: set[str] = set()
        normalized: list[str] = []
        for feature in features:
            if not isinstance(feature, str):
                continue
            value = feature.strip().lower()
            if not value or value in seen:
                continue
            seen.add(value)
            normalized.append(value)
        return normalized

    @staticmethod
    def _bump_score(
        scores: dict[str, float],
        reasons: dict[str, list[str]],
        class_name: str,
        *,
        delta: float,
        reason: str,
    ) -> None:
        key = class_name.strip().lower()
        scores[key] = scores.get(key, 0.0) + delta
        reasons.setdefault(key, []).append(reason)
