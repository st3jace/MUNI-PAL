from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from munipal.services.playbook_data import SCHEMA_PATHS


@dataclass(frozen=True)
class RulesBasedFact:
    schema_path: str
    value: Any
    value_type: str
    unit: str | None
    confidence: float
    confidence_rationale: str
    source_quote: str
    chunk_id: str

    def to_extraction_fact(self) -> dict[str, Any]:
        return {
            "schema_path": self.schema_path,
            "value": self.value,
            "value_type": self.value_type,
            "unit": self.unit,
            "confidence": self.confidence,
            "confidence_rationale": self.confidence_rationale,
            "source_quote": self.source_quote,
            "chunk_id": self.chunk_id,
        }


_EXTRA_SCHEMA_PATHS = {
    "project.name": {"path": "project.name", "value_type": "string", "unit": None},
    "project.location": {"path": "project.location", "value_type": "string", "unit": None},
    "healthcare.facility_type": {"path": "healthcare.facility_type", "value_type": "string", "unit": None},
    "healthcare.licensure": {"path": "healthcare.licensure", "value_type": "string", "unit": None},
    "healthcare.cms_certification": {"path": "healthcare.cms_certification", "value_type": "string", "unit": None},
    "healthcare.accreditation": {"path": "healthcare.accreditation", "value_type": "string", "unit": None},
    "healthcare.ehr_platform": {"path": "healthcare.ehr_platform", "value_type": "string", "unit": None},
    "healthcare.net_patient_revenue": {"path": "healthcare.net_patient_revenue", "value_type": "currency", "unit": "USD"},
    "healthcare.payor_mix": {"path": "healthcare.payor_mix", "value_type": "percentage", "unit": None},
    "liquidity.days_cash_on_hand": {"path": "liquidity.days_cash_on_hand", "value_type": "number", "unit": "days"},
    "liquidity.cash_to_debt": {"path": "liquidity.cash_to_debt", "value_type": "percentage", "unit": None},
    "healthcare.service_area": {"path": "healthcare.service_area", "value_type": "string", "unit": None},
    "healthcare.physician_alignment": {"path": "healthcare.physician_alignment", "value_type": "string", "unit": None},
    "healthcare.utilization.trend": {"path": "healthcare.utilization.trend", "value_type": "string", "unit": None},
    "environmental.phase_one": {"path": "environmental.phase_one", "value_type": "string", "unit": None},
}
_SCHEMA_BY_PATH = {**_EXTRA_SCHEMA_PATHS, **{path["path"]: path for path in SCHEMA_PATHS}}

_PATH_LABELS: dict[str, tuple[str, ...]] = {
    "parties.borrower.name": ("borrower", "borrower name", "obligated borrower"),
    "parties.issuer.name": ("issuer", "issuing authority", "bond issuer"),
    "parties.operator.name": ("operator", "facility operator"),
    "parties.sponsor.name": ("sponsor", "equity sponsor"),
    "project.location.jurisdiction": ("project location", "location", "jurisdiction", "county"),
    "project.location.coordinates": ("coordinates", "gps coordinates"),
    "project.operatingstatus": ("operating status", "development status", "project status"),
    "technology.throughput.nameplate": ("nameplate capacity", "design capacity", "throughput"),
    "technology.throughput.annual": ("annual throughput", "annual feedstock throughput"),
    "feedstock.volume.annual": ("annual feedstock volume", "feedstock volume"),
    "feedstock.type": ("feedstock type", "feedstock"),
    "feedstock.supply.mechanism": ("supply mechanism", "feedstock agreement"),
    "capital.project-cost": ("total project cost", "project cost", "capital cost", "authorized amount"),
    "capital.equipment-cost": ("equipment cost",),
    "capital.equity-contribution": ("equity contribution",),
    "capital.equity-percent": ("equity percentage", "equity percent"),
    "revenue.gross.annual": ("gross annual revenue", "total revenue"),
    "revenue.offtake.status": ("offtake status", "offtake"),
    "opex.total.annual": ("total annual opex", "annual opex", "operating expenses"),
    "opex.margin": ("operating margin", "margin"),
    "ebitda": ("ebitda",),
    "finmodel.inputs.dscr.minimum": ("minimum dscr covenant", "minimum dscr", "dscr covenant"),
    "finmodel.outputs.dscrbase": ("base dscr", "debt service coverage ratio", "dscr latest"),
    "finmodel.outputs.dscrstress": ("stress dscr",),
    "permitting.air-quality.status": ("air quality permit", "air permit"),
    "permitting.solidwaste.status": ("solid waste permit",),
    "permitting.buildingzoning.status": ("building zoning", "zoning", "building permit"),
    "regulatory.tax-status": ("tax status", "tax exempt status"),
    "project.name": ("organization", "organization name", "facility name", "entity name", "provider name", "named insured"),
    "project.location": ("location", "city", "state", "service area"),
    "healthcare.facility_type": ("facility type", "entity type"),
    "healthcare.licensure": ("license number", "hospital operating license"),
    "healthcare.cms_certification": ("certification status", "medicare provider number", "cms 855", "medicare participation"),
    "healthcare.accreditation": ("accreditation decision", "accreditation status", "joint commission"),
    "healthcare.ehr_platform": ("ehr", "clinical information systems"),
    "healthcare.net_patient_revenue": ("net patient revenue",),
    "healthcare.payor_mix": ("payer mix", "payor mix"),
    "liquidity.days_cash_on_hand": ("days cash on hand",),
    "liquidity.cash_to_debt": ("cash to debt",),
    "healthcare.service_area": ("service area", "community"),
    "healthcare.physician_alignment": ("physician", "physician alignment", "physician recruitment"),
    "healthcare.utilization.trend": ("utilization", "bed capacity", "licensed beds"),
    "environmental.phase_one": ("phase i environmental", "recognized environmental conditions", "assessment findings"),
}


_ENUM_NORMALIZATIONS = {
    "planned": "planned", "planning": "planned", "under construction": "under-construction",
    "under-construction": "under-construction", "operational": "operational", "operating": "operational",
    "executed": "executed", "advanced mou": "advanced-mou", "advanced-mou": "advanced-mou",
    "letter of intent": "letter-of-intent", "letter-of-intent": "letter-of-intent", "loi": "letter-of-intent",
    "negotiating": "negotiating", "not started": "not-started", "not-started": "not-started",
    "in progress": "in-progress", "in-progress": "in-progress", "pending approval": "pending-approval",
    "pending-approval": "pending-approval", "approved": "approved", "tax exempt idb": "tax-exempt-idb",
    "tax-exempt-idb": "tax-exempt-idb", "tax exempt solid waste": "tax-exempt-solidwaste",
    "tax-exempt-solidwaste": "tax-exempt-solidwaste", "taxable": "taxable", "contract": "contract",
    "mou": "mou", "assessment": "assessment", "preliminary": "preliminary", "advanced": "advanced",
    "secured": "secured", "forestry": "forestry", "msw": "msw", "municipal solid waste": "msw",
    "agricultural": "agricultural", "mixed": "mixed",
}

_VALUE_PATTERNS = {
    "currency": re.compile(r"[$]\s?\d[\d,]*(?:\.\d+)?\s*(?:million|mm|billion|bn|thousand|k)?", re.I),
    "number": re.compile(r"\b\d[\d,]*(?:\.\d+)?\s*(?:x|tons?/day|tpd|tons?/year|years?)?\b", re.I),
    "percentage": re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|percent|bps)\b", re.I),
    "date": re.compile(r"\b(?:\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2}|[A-Z][a-z]+ \d{1,2}, \d{4})\b"),
}


class RulesBasedExtractor:
    """Extract explicit labelled values from chunks without external AI calls."""

    def extract(self, chunks: list[dict[str, Any]], target_schema_paths: list[str] | None = None) -> list[RulesBasedFact]:
        paths = target_schema_paths or list(_SCHEMA_BY_PATH)
        results: list[RulesBasedFact] = []
        for path in paths:
            schema = _SCHEMA_BY_PATH.get(path, {"path": path, "value_type": "string"})
            for chunk in chunks:
                fact = self._extract_path_from_chunk(schema, chunk)
                if fact:
                    results.append(fact)
                    break
        return results

    def _extract_path_from_chunk(self, schema: dict[str, Any], chunk: dict[str, Any]) -> RulesBasedFact | None:
        path = schema["path"]
        text = chunk.get("text_content") or ""
        if not text.strip():
            return None
        labels = self._labels_for_path(path, schema)
        value_type = schema.get("value_type", "string")
        unit = schema.get("unit")
        for line in self._candidate_lines(text):
            normalized_line = self._normalize_label(line)
            if not any(label in normalized_line for label in labels):
                continue
            raw_value = (
                self._value_from_pipe_row(line, labels)
                or self._value_after_label(line, labels)
                or self._value_by_type(line, value_type)
            )
            if raw_value is None:
                continue
            value = self._coerce_value(raw_value, value_type, schema)
            if value is None or value == "":
                continue
            return RulesBasedFact(
                schema_path=path,
                value=value,
                value_type=value_type,
                unit=unit,
                confidence=0.72,
                confidence_rationale="Deterministic rules-based extraction from an explicit label or nearby keyword; requires human evidence review before approval.",
                source_quote=line.strip()[:500],
                chunk_id=str(chunk.get("id")),
            )
        return None

    def _labels_for_path(self, path: str, schema: dict[str, Any]) -> tuple[str, ...]:
        labels = list(_PATH_LABELS.get(path, ()))
        labels.append(self._normalize_label(path.replace(".", " ").replace("-", " ")))
        labels.append(self._normalize_label(path.split(".")[-1].replace("-", " ")))
        if schema.get("display_name"):
            labels.append(self._normalize_label(schema["display_name"]))
        return tuple(dict.fromkeys(label for label in labels if label))

    def _candidate_lines(self, text: str) -> list[str]:
        base_lines = [
            raw.strip(" \t•-*–—")
            for raw in re.split(r"[\n\r]+", text)
            if raw.strip(" \t•-*–—")
        ]
        lines: list[str] = []
        for index, line in enumerate(base_lines):
            lines.append(line)
            if line.endswith(":") and index + 1 < len(base_lines):
                lines.append(f"{line} {base_lines[index + 1]}")
        if len(lines) == 1:
            lines = [part.strip() for part in re.split(r";|(?<=[.!?])\s+", lines[0]) if part.strip()]
        return lines


    def _value_from_pipe_row(self, line: str, labels: tuple[str, ...]) -> str | None:
        if "|" not in line:
            return None
        cells = [cell.strip() for cell in line.split("|") if cell.strip()]
        if not cells:
            return None
        first_cell = re.sub(r"^row\s+\d+\s*:\s*", "", cells[0], flags=re.I).strip()
        normalized_first = self._normalize_label(first_cell)
        if not any(label in normalized_first for label in labels):
            return None
        for cell in reversed(cells[1:]):
            if cell:
                return cell.rstrip(".")
        return None

    def _value_after_label(self, line: str, labels: tuple[str, ...]) -> str | None:
        for separator in (":", " - ", " – ", " — "):
            if separator in line:
                left, right = line.split(separator, 1)
                normalized_left = self._normalize_label(left)
                if any(label in normalized_left for label in labels) and right.strip():
                    return right.strip().rstrip(".")
        return None

    def _value_by_type(self, line: str, value_type: str) -> str | None:
        pattern = _VALUE_PATTERNS.get(value_type)
        if pattern and (match := pattern.search(line)):
            return match.group(0)
        if value_type == "enum":
            normalized = self._normalize_label(line)
            for candidate in _ENUM_NORMALIZATIONS:
                if candidate in normalized:
                    return candidate
        if value_type == "boolean":
            normalized = self._normalize_label(line)
            if any(token in normalized for token in ("enabled", "yes", "true")):
                return "true"
            if any(token in normalized for token in ("disabled", "no", "false")):
                return "false"
        return None

    def _coerce_value(self, raw_value: str, value_type: str, schema: dict[str, Any]) -> Any:
        cleaned = raw_value.strip().strip(chr(34)).strip(chr(39))
        if value_type == "currency":
            return self._parse_scaled_number(cleaned, currency=True)
        if value_type == "number":
            return self._parse_scaled_number(cleaned, currency=False)
        if value_type == "percentage":
            return self._parse_scaled_number(cleaned, currency=False)
        if value_type == "boolean":
            normalized = self._normalize_label(cleaned)
            if any(token in normalized for token in ("enabled", "yes", "true")):
                return True
            if any(token in normalized for token in ("disabled", "no", "false")):
                return False
            return None
        if value_type == "enum":
            normalized = self._normalize_label(cleaned)
            allowed = schema.get("allowed_values") or []
            for value in allowed:
                if self._normalize_label(value) in normalized or normalized in self._normalize_label(value):
                    return value
            for key, value in _ENUM_NORMALIZATIONS.items():
                if key in normalized and (not allowed or value in allowed):
                    return value
            return None
        if value_type == "array":
            return [part.strip() for part in re.split(r",|;", cleaned) if part.strip()]
        return cleaned

    def _parse_scaled_number(self, raw_value: str, currency: bool) -> int | float | None:
        match = re.search(r"\d[\d,]*(?:\.\d+)?", raw_value)
        if not match:
            return None
        value = float(match.group(0).replace(",", ""))
        normalized = self._normalize_label(raw_value)
        if "billion" in normalized or "bn" in normalized:
            value *= 1_000_000_000
        elif "million" in normalized or "mm" in normalized:
            value *= 1_000_000
        elif "thousand" in normalized or re.search(r"\bk\b", normalized):
            value *= 1_000
        if currency or value.is_integer():
            return int(value)
        return value

    def _normalize_label(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
