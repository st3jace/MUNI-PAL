from __future__ import annotations

import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from .base_extractor import BaseExtractor, ExtractionTier

logger = logging.getLogger("bond_os_extractor.extraction.tables")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_cell(val: str | None) -> str:
    if val is None:
        return ""
    return val.strip().replace("\n", " ")


def _parse_decimal(text: str) -> Decimal | None:
    cleaned = text.replace("$", "").replace(",", "").replace(" ", "").strip()
    # Handle parenthetical negatives: (1,234) -> -1234
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = "-" + cleaned[1:-1]
    if not cleaned or cleaned == "-":
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _parse_year(text: str) -> int | None:
    m = re.search(r"\b(19|20)\d{2}\b", text)
    return int(m.group()) if m else None


def _parse_date_cell(text: str) -> date | None:
    from dateutil import parser as dateparser
    try:
        return dateparser.parse(text, fuzzy=True).date()
    except Exception:
        return None


def _is_total_row(row: list[str]) -> bool:
    first = _clean_cell(row[0]).lower() if row else ""
    return any(kw in first for kw in ["total", "totals", "grand total", "aggregate"])


def _is_subtotal_row(row: list[str]) -> bool:
    first = _clean_cell(row[0]).lower() if row else ""
    return "subtotal" in first


# ---------------------------------------------------------------------------
# Maturity Schedule Table Extractor
# ---------------------------------------------------------------------------

class MaturityTableExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_1
    name = "maturity_table_extractor"

    HEADER_KEYWORDS = [
        "maturity", "date", "amount", "rate", "yield", "price", "cusip",
    ]

    def _find_maturity_table(self, tables: list[list[list[str]]]) -> list[list[str]] | None:
        """Find the table most likely to be a maturity schedule."""
        best_table = None
        best_score = 0

        for tbl in tables:
            if len(tbl) < 2:
                continue
            header = " ".join(_clean_cell(c) for c in tbl[0]).lower()
            score = sum(1 for kw in self.HEADER_KEYWORDS if kw in header)
            if score > best_score:
                best_score = score
                best_table = tbl

        return best_table if best_score >= 2 else None

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        if not tables:
            return {}

        tbl = self._find_maturity_table(tables)
        if tbl is None:
            return {}

        # Parse header to identify columns
        header = [_clean_cell(c).lower() for c in tbl[0]]
        col_map: dict[str, int] = {}
        for i, h in enumerate(header):
            if "maturity" in h or (h == "date" and i == 0):
                col_map["maturity_date"] = i
            elif "amount" in h or "principal" in h or "par" in h:
                col_map["par_amount"] = i
            elif "rate" in h or "coupon" in h:
                col_map["coupon_rate"] = i
            elif "yield" in h:
                col_map["yield"] = i
            elif "price" in h:
                col_map["price"] = i
            elif "cusip" in h:
                col_map["cusip"] = i

        rows: list[dict[str, Any]] = []
        total_par = Decimal(0)

        for row in tbl[1:]:
            if _is_total_row(row) or _is_subtotal_row(row):
                continue

            entry: dict[str, Any] = {}

            if "maturity_date" in col_map and col_map["maturity_date"] < len(row):
                entry["maturity_date"] = _parse_date_cell(_clean_cell(row[col_map["maturity_date"]]))

            if "par_amount" in col_map and col_map["par_amount"] < len(row):
                amt = _parse_decimal(_clean_cell(row[col_map["par_amount"]]))
                entry["par_amount"] = amt
                if amt:
                    total_par += amt

            if "coupon_rate" in col_map and col_map["coupon_rate"] < len(row):
                entry["coupon_rate"] = _parse_decimal(_clean_cell(row[col_map["coupon_rate"]]))

            if "yield" in col_map and col_map["yield"] < len(row):
                entry["yield_to_maturity"] = _parse_decimal(_clean_cell(row[col_map["yield"]]))

            if "price" in col_map and col_map["price"] < len(row):
                entry["price"] = _parse_decimal(_clean_cell(row[col_map["price"]]))

            if "cusip" in col_map and col_map["cusip"] < len(row):
                entry["cusip"] = _clean_cell(row[col_map["cusip"]])

            if entry.get("maturity_date") or entry.get("par_amount"):
                rows.append(entry)

        if not rows:
            return {}

        return {
            "maturity_schedule": {
                "rows": rows,
                "total_par": total_par if total_par > 0 else None,
            },
            "_confidence": {"maturity_schedule": 0.80},
        }


# ---------------------------------------------------------------------------
# Debt Service Schedule Table Extractor
# ---------------------------------------------------------------------------

class DebtServiceTableExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_1
    name = "debt_service_table_extractor"

    HEADER_KEYWORDS = ["year", "principal", "interest", "total", "debt service"]

    def _find_ds_table(self, tables: list[list[list[str]]]) -> list[list[str]] | None:
        best_table = None
        best_score = 0
        for tbl in tables:
            if len(tbl) < 3:
                continue
            header = " ".join(_clean_cell(c) for c in tbl[0]).lower()
            score = sum(1 for kw in self.HEADER_KEYWORDS if kw in header)
            if score > best_score:
                best_score = score
                best_table = tbl
        return best_table if best_score >= 2 else None

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        if not tables:
            return {}

        tbl = self._find_ds_table(tables)
        if tbl is None:
            return {}

        header = [_clean_cell(c).lower() for c in tbl[0]]
        col_map: dict[str, int] = {}
        for i, h in enumerate(header):
            if "year" in h or "period" in h or "fiscal" in h:
                col_map["year"] = i
            elif "principal" in h:
                col_map["principal"] = i
            elif "interest" in h:
                col_map["interest"] = i
            elif "total" in h or "debt service" in h:
                col_map["total"] = i
            elif "balance" in h or "outstanding" in h:
                col_map["balance"] = i

        rows: list[dict[str, Any]] = []
        max_total = Decimal(0)
        sum_principal = Decimal(0)
        sum_interest = Decimal(0)
        sum_total = Decimal(0)

        for row in tbl[1:]:
            if _is_total_row(row):
                continue

            entry: dict[str, Any] = {}

            if "year" in col_map and col_map["year"] < len(row):
                yr = _parse_year(_clean_cell(row[col_map["year"]]))
                if yr:
                    entry["fiscal_year"] = yr

            if "principal" in col_map and col_map["principal"] < len(row):
                val = _parse_decimal(_clean_cell(row[col_map["principal"]]))
                entry["principal"] = val
                if val:
                    sum_principal += val

            if "interest" in col_map and col_map["interest"] < len(row):
                val = _parse_decimal(_clean_cell(row[col_map["interest"]]))
                entry["interest"] = val
                if val:
                    sum_interest += val

            if "total" in col_map and col_map["total"] < len(row):
                val = _parse_decimal(_clean_cell(row[col_map["total"]]))
                entry["total"] = val
                if val:
                    sum_total += val
                    if val > max_total:
                        max_total = val

            if "balance" in col_map and col_map["balance"] < len(row):
                entry["outstanding_balance"] = _parse_decimal(
                    _clean_cell(row[col_map["balance"]])
                )

            if entry.get("fiscal_year"):
                rows.append(entry)

        if not rows:
            return {}

        return {
            "debt_service": {
                "rows": rows,
                "total_principal": sum_principal if sum_principal > 0 else None,
                "total_interest": sum_interest if sum_interest > 0 else None,
                "total_debt_service": sum_total if sum_total > 0 else None,
                "maximum_annual_debt_service": max_total if max_total > 0 else None,
            },
            "_confidence": {"debt_service": 0.80},
        }


# ---------------------------------------------------------------------------
# Sources and Uses Table Extractor
# ---------------------------------------------------------------------------

class SourcesUsesTableExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_1
    name = "sources_uses_table_extractor"

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        if not tables:
            return {}

        # Try to find a sources/uses table
        for tbl in tables:
            if len(tbl) < 2:
                continue
            all_text = " ".join(
                _clean_cell(c) for row in tbl for c in row
            ).lower()
            if ("source" in all_text or "bond proceed" in all_text) and (
                "use" in all_text or "project" in all_text
            ):
                return self._parse_su_table(tbl)

        # Fallback: try regex on section text
        return self._parse_su_from_text(section_text)

    def _parse_su_table(self, tbl: list[list[str]]) -> dict[str, Any]:
        sources: dict[str, Decimal] = {}
        uses: dict[str, Decimal] = {}
        current_section = None

        for row in tbl:
            if not row:
                continue
            label = _clean_cell(row[0]).lower()
            value = _parse_decimal(_clean_cell(row[-1])) if len(row) > 1 else None

            if "source" in label:
                current_section = "sources"
                continue
            elif "use" in label or "application" in label:
                current_section = "uses"
                continue

            if value and current_section == "sources":
                sources[_clean_cell(row[0])] = value
            elif value and current_section == "uses":
                uses[_clean_cell(row[0])] = value

        if not sources and not uses:
            return {}

        result: dict[str, Any] = {}
        su: dict[str, Any] = {}

        # Identify key line items
        for label, val in sources.items():
            ll = label.lower()
            if "bond proceed" in ll or "par amount" in ll:
                su["bond_proceeds"] = val
            elif "premium" in ll:
                su["original_issue_premium"] = val

        for label, val in uses.items():
            ll = label.lower()
            if "project" in ll or "construction" in ll or "acquisition" in ll:
                su["project_fund_deposit"] = val
            elif "reserve" in ll and "debt" in ll:
                su["debt_service_reserve_deposit"] = val
            elif "capitalized interest" in ll:
                su["capitalized_interest"] = val
            elif "cost" in ll and "issuance" in ll:
                su["costs_of_issuance"] = val
            elif "underwriter" in ll or "discount" in ll:
                su["underwriter_discount"] = val

        su["total_sources"] = sum(sources.values()) if sources else None
        su["total_uses"] = sum(uses.values()) if uses else None

        result["sources_uses"] = su
        result["_confidence"] = {"sources_uses": 0.75}
        return result

    def _parse_su_from_text(self, text: str) -> dict[str, Any]:
        """Fallback: parse sources/uses from narrative text."""
        result: dict[str, Any] = {}
        su: dict[str, Any] = {}

        # Try to find total sources/uses
        m = re.search(r"[Tt]otal\s+[Ss]ources[:\s]*\$([\d,]+)", text)
        if m:
            su["total_sources"] = _parse_decimal(m.group(1))

        m = re.search(r"[Tt]otal\s+[Uu]ses[:\s]*\$([\d,]+)", text)
        if m:
            su["total_uses"] = _parse_decimal(m.group(1))

        if su:
            result["sources_uses"] = su
            result["_confidence"] = {"sources_uses": 0.60}
        return result


ALL_TABLE_EXTRACTORS: list[type[BaseExtractor]] = [
    MaturityTableExtractor,
    DebtServiceTableExtractor,
    SourcesUsesTableExtractor,
]
