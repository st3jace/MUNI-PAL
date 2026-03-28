"""
Model-to-document consistency checking for legal terms.

Supports baseline parity checks between extracted legal document terms
and model parameters for covenant and waterfall domains.
"""

from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from munipal.core.models.deal_document import DealDocument
from munipal.core.schemas.deal_document import (
    ConsistencyCheckRequest,
    ConsistencyCheckResult,
    ConsistencyDomain,
    ConsistencyIssue,
    ConsistencySeverity,
)
from munipal.services.document_audit_service import DocumentAuditService

DOMAIN_FIELDS: dict[ConsistencyDomain, list[str]] = {
    ConsistencyDomain.COVENANT: [
        "dscr_min",
        "additional_bonds_test_dscr",
        "debt_service_reserve_months",
        "rate_covenant_pct",
        "max_ltv_pct",
        "cure_period_days",
    ],
    ConsistencyDomain.WATERFALL: [
        "preferred_return_pct",
        "gp_carry_pct",
        "catch_up_pct",
        "hurdle_multiple_x",
        "clawback_pct",
    ],
}


COVENANT_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "dscr_min": [re.compile(r"(?:minimum\s+)?dscr[^0-9]{0,20}(\d+(?:\.\d+)?)\s*x", re.IGNORECASE)],
    "additional_bonds_test_dscr": [
        re.compile(r"additional bonds(?: test)?[^0-9]{0,40}(\d+(?:\.\d+)?)\s*x", re.IGNORECASE)
    ],
    "debt_service_reserve_months": [
        re.compile(r"debt service reserve(?: fund)?[^0-9]{0,50}(\d+(?:\.\d+)?)\s*(?:months?|mos?)", re.IGNORECASE)
    ],
    "rate_covenant_pct": [
        re.compile(r"rate covenant[^0-9]{0,35}(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
    ],
    "max_ltv_pct": [
        re.compile(r"(?:maximum|max)\s+l(?:oan)?tv[^0-9]{0,20}(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
    ],
    "cure_period_days": [
        re.compile(r"cure period[^0-9]{0,20}(\d+)\s*days?", re.IGNORECASE)
    ],
}


WATERFALL_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "preferred_return_pct": [
        re.compile(r"(?:preferred return|pref return)[^0-9]{0,30}(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
    ],
    "gp_carry_pct": [
        re.compile(r"(?:carried interest|carry)[^0-9]{0,30}(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
    ],
    "catch_up_pct": [re.compile(r"catch[- ]up[^0-9]{0,30}(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)],
    "hurdle_multiple_x": [re.compile(r"hurdle[^0-9]{0,30}(\d+(?:\.\d+)?)\s*x", re.IGNORECASE)],
    "clawback_pct": [re.compile(r"clawback[^0-9]{0,30}(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)],
}


class DocumentConsistencyService:
    """Service for legal-model term consistency checks."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._audit = DocumentAuditService(db)

    async def check_document(
        self,
        *,
        document_id: UUID,
        request: ConsistencyCheckRequest,
        actor_id: str | None = None,
    ) -> ConsistencyCheckResult:
        """Check a deal document against model terms for the selected domain."""
        document = await self.db.get(DealDocument, str(document_id))
        if not document:
            raise ValueError(f"Document {document_id} not found")

        legal_terms = dict(request.legal_terms or {})
        if not legal_terms:
            text = document.content_plaintext or self._extract_plaintext(document.content_json)
            legal_terms = self._extract_terms(text or "", request.domain)

        issues, checked_fields, matched_fields = self._compare_terms(
            domain=request.domain,
            legal_terms=legal_terms,
            model_terms=request.model_terms,
            tolerance_ratio=request.tolerance_ratio,
            strict=request.strict,
        )

        consistency_score = 0.0
        if checked_fields > 0:
            consistency_score = round(matched_fields / checked_fields, 4)

        is_consistent = not any(issue.severity == ConsistencySeverity.ERROR for issue in issues)
        result = ConsistencyCheckResult(
            document_id=document_id,
            domain=request.domain,
            extracted_legal_terms=legal_terms,
            model_terms=request.model_terms,
            issues=issues,
            checked_fields=checked_fields,
            matched_fields=matched_fields,
            consistency_score=consistency_score,
            is_consistent=is_consistent,
        )

        if actor_id:
            await self._audit.log(
                document_id=document_id,
                actor_id=actor_id,
                action="consistency_checked",
                details={
                    "domain": request.domain.value,
                    "is_consistent": result.is_consistent,
                    "checked_fields": checked_fields,
                    "matched_fields": matched_fields,
                    "issue_count": len(issues),
                },
            )

        return result

    @classmethod
    def _extract_terms(
        cls,
        text: str,
        domain: ConsistencyDomain,
    ) -> dict[str, float]:
        patterns = COVENANT_PATTERNS if domain == ConsistencyDomain.COVENANT else WATERFALL_PATTERNS
        extracted: dict[str, float] = {}
        for field, field_patterns in patterns.items():
            for pattern in field_patterns:
                match = pattern.search(text)
                if not match:
                    continue
                try:
                    extracted[field] = float(match.group(1))
                    break
                except (TypeError, ValueError):
                    continue
        return extracted

    @classmethod
    def _compare_terms(
        cls,
        *,
        domain: ConsistencyDomain,
        legal_terms: dict,
        model_terms: dict,
        tolerance_ratio: float,
        strict: bool,
    ) -> tuple[list[ConsistencyIssue], int, int]:
        expected_fields = set(DOMAIN_FIELDS[domain])
        keys = sorted(expected_fields | set(legal_terms.keys()) | set(model_terms.keys()))

        issues: list[ConsistencyIssue] = []
        checked_fields = 0
        matched_fields = 0

        for key in keys:
            legal_raw = legal_terms.get(key)
            model_raw = model_terms.get(key)

            if legal_raw is None and model_raw is None:
                continue

            checked_fields += 1
            if legal_raw is None or model_raw is None:
                severity = ConsistencySeverity.ERROR if strict else ConsistencySeverity.WARNING
                issues.append(
                    ConsistencyIssue(
                        field=key,
                        legal_value=legal_raw,
                        model_value=model_raw,
                        severity=severity,
                        message="Missing legal or model value for field",
                    )
                )
                continue

            legal_num = cls._to_number(key, legal_raw)
            model_num = cls._to_number(key, model_raw)

            if legal_num is None or model_num is None:
                if str(legal_raw).strip().lower() == str(model_raw).strip().lower():
                    matched_fields += 1
                    continue
                issues.append(
                    ConsistencyIssue(
                        field=key,
                        legal_value=legal_raw,
                        model_value=model_raw,
                        severity=ConsistencySeverity.ERROR,
                        message="Text value mismatch",
                    )
                )
                continue

            delta = abs(legal_num - model_num)
            tolerance = max(0.0001, abs(legal_num) * tolerance_ratio)
            if delta <= tolerance:
                matched_fields += 1
                continue

            issues.append(
                ConsistencyIssue(
                    field=key,
                    legal_value=legal_num,
                    model_value=model_num,
                    severity=ConsistencySeverity.ERROR,
                    message=f"Numeric mismatch exceeds tolerance ({tolerance:.6f})",
                    delta=round(delta, 6),
                )
            )

        return issues, checked_fields, matched_fields

    @staticmethod
    def _to_number(field: str, value: object) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            numeric = float(value)
        elif isinstance(value, str):
            cleaned = (
                value.strip()
                .lower()
                .replace(",", "")
                .replace("%", "")
                .replace("x", "")
                .replace("$", "")
            )
            try:
                numeric = float(cleaned)
            except ValueError:
                return None
        else:
            return None

        if field.endswith("_pct") and abs(numeric) <= 1.0:
            numeric = numeric * 100.0
        return numeric

    @staticmethod
    def _extract_plaintext(content_json: dict | None) -> str | None:
        if not content_json:
            return None

        texts: list[str] = []

        def walk(node: dict) -> None:
            if node.get("type") == "text":
                text = node.get("text", "")
                if text:
                    texts.append(text)
            for child in node.get("content", []):
                if isinstance(child, dict):
                    walk(child)

        walk(content_json)
        return " ".join(texts) if texts else None
