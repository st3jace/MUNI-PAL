"""
Extraction response parser.

Converts Claude's JSON responses into ExtractedFact structures
with validation and normalization.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ParsedFact:
    """A fact parsed from Claude's extraction response."""

    schema_path: str
    value: Any
    value_type: str
    unit: str | None
    confidence: float
    confidence_rationale: str | None
    source_quote: str | None

    def to_dict(self) -> dict:
        """Convert to dictionary for database insertion."""
        return {
            "schema_path": self.schema_path,
            "value": self.value,
            "value_type": self.value_type,
            "unit": self.unit,
            "confidence_score": self.confidence,
            "confidence_rationale": self.confidence_rationale,
            "source_quote": self.source_quote,
        }


class ExtractionResponseParser:
    """
    Parses and validates extraction responses from Claude.

    Handles:
    - JSON structure validation
    - Value type normalization
    - Confidence score validation
    - Error recovery for malformed responses
    """

    # Valid value types per schema
    VALID_VALUE_TYPES = {
        "string",
        "number",
        "date",
        "boolean",
        "currency",
        "percentage",
        "array",
        "object",
        "enum",
    }

    def __init__(self, schema_paths: list[dict] | None = None):
        """
        Initialize parser.

        Args:
            schema_paths: Optional list of schema path definitions for validation
        """
        self.schema_paths = {p["path"]: p for p in (schema_paths or [])}

    def parse(self, response: dict[str, Any]) -> tuple[list[ParsedFact], list[str], str | None]:
        """
        Parse extraction response into facts.

        Args:
            response: JSON response from Claude

        Returns:
            Tuple of (parsed_facts, unfound_paths, extraction_notes)
        """
        parsed_facts: list[ParsedFact] = []
        unfound_paths: list[str] = response.get("unfound_paths", [])
        extraction_notes: str | None = response.get("extraction_notes")

        # Check for parse errors
        if "parse_error" in response:
            logger.warning(f"Response had parse error: {response.get('parse_error')}")
            return [], [], f"Parse error: {response.get('parse_error')}"

        # Extract facts array
        facts_data = response.get("facts", [])
        if not isinstance(facts_data, list):
            logger.warning("Response 'facts' is not a list")
            return [], [], "Invalid response: facts is not a list"

        for fact_data in facts_data:
            try:
                parsed = self._parse_single_fact(fact_data)
                if parsed:
                    parsed_facts.append(parsed)
            except Exception as e:
                logger.warning(f"Failed to parse fact: {e}")
                continue

        logger.info(f"Parsed {len(parsed_facts)} facts, {len(unfound_paths)} unfound paths")
        return parsed_facts, unfound_paths, extraction_notes

    def _parse_single_fact(self, fact_data: dict) -> ParsedFact | None:
        """Parse a single fact from response data."""
        # Required fields
        schema_path = fact_data.get("schema_path")
        if not schema_path:
            logger.warning("Fact missing schema_path")
            return None

        value = fact_data.get("value")
        if value is None:
            logger.debug(f"Fact {schema_path} has null value, skipping")
            return None

        # Normalize value type
        value_type = fact_data.get("value_type", "string")
        if value_type not in self.VALID_VALUE_TYPES:
            value_type = "string"

        # Normalize and validate value based on type
        normalized_value = self._normalize_value(value, value_type)

        # Validate confidence
        confidence = fact_data.get("confidence", 0.5)
        try:
            confidence = float(confidence)
            confidence = max(0.0, min(1.0, confidence))
        except (ValueError, TypeError):
            confidence = 0.5

        return ParsedFact(
            schema_path=schema_path,
            value=normalized_value,
            value_type=value_type,
            unit=fact_data.get("unit"),
            confidence=confidence,
            confidence_rationale=fact_data.get("confidence_rationale"),
            source_quote=fact_data.get("source_quote"),
        )

    def _normalize_value(self, value: Any, value_type: str) -> Any:
        """Normalize value based on its declared type."""
        if value is None:
            return None

        try:
            if value_type == "number":
                return self._parse_number(value)
            elif value_type == "currency":
                return self._parse_currency(value)
            elif value_type == "percentage":
                return self._parse_percentage(value)
            elif value_type == "boolean":
                return self._parse_boolean(value)
            elif value_type == "date":
                return self._parse_date(value)
            elif value_type in ("array", "object"):
                return value  # Keep as-is
            else:
                return str(value)
        except Exception as e:
            logger.debug(f"Value normalization failed for {value_type}: {e}")
            return str(value)

    def _parse_number(self, value: Any) -> float | int:
        """Parse numeric value."""
        if isinstance(value, (int, float)):
            return value

        # Handle string numbers with commas
        str_val = str(value).replace(",", "").strip()

        # Remove common suffixes
        for suffix in ["M", "K", "B", "m", "k", "b"]:
            if str_val.endswith(suffix):
                multiplier = {"M": 1_000_000, "K": 1_000, "B": 1_000_000_000}
                mult = multiplier.get(suffix.upper(), 1)
                str_val = str_val[:-1]
                return float(str_val) * mult

        return float(str_val)

    def _parse_currency(self, value: Any) -> float:
        """Parse currency value (returns as float)."""
        if isinstance(value, (int, float)):
            return float(value)

        str_val = str(value)
        # Remove currency symbols and commas
        for char in ["$", "€", "£", ",", " "]:
            str_val = str_val.replace(char, "")

        return self._parse_number(str_val)

    def _parse_percentage(self, value: Any) -> float:
        """Parse percentage value (returns as decimal 0-1 or 0-100 based on input)."""
        if isinstance(value, (int, float)):
            # If > 1, assume it's already a percentage (e.g., 6.5 = 6.5%)
            return float(value)

        str_val = str(value).replace("%", "").strip()
        return float(str_val)

    def _parse_boolean(self, value: Any) -> bool:
        """Parse boolean value."""
        if isinstance(value, bool):
            return value

        str_val = str(value).lower().strip()
        return str_val in ("true", "yes", "1", "enabled", "on")

    def _parse_date(self, value: Any) -> str:
        """Parse and normalize date value."""
        if isinstance(value, datetime):
            return value.isoformat()

        # Return as-is for now, could add more parsing
        return str(value)

    def validate_against_schema(
        self,
        facts: list[ParsedFact],
        schema_paths: list[dict],
    ) -> tuple[list[ParsedFact], list[dict]]:
        """
        Validate facts against schema definitions.

        Returns:
            Tuple of (valid_facts, validation_warnings)
        """
        valid_facts = []
        warnings = []

        schema_lookup = {p["path"]: p for p in schema_paths}

        for fact in facts:
            schema_def = schema_lookup.get(fact.schema_path)

            if not schema_def:
                warnings.append({
                    "fact": fact.schema_path,
                    "warning": "Schema path not in allowlist",
                })
                continue

            # Check confidence threshold
            min_confidence = schema_def.get("min_confidence", 0.65)
            if fact.confidence < min_confidence:
                warnings.append({
                    "fact": fact.schema_path,
                    "warning": f"Confidence {fact.confidence:.2f} below threshold {min_confidence}",
                })
                # Still include, but flag for review

            # Check value type
            expected_type = schema_def.get("value_type", "string")
            if fact.value_type != expected_type:
                # Try to coerce
                fact.value_type = expected_type

            # Check allowed values for enums
            allowed = schema_def.get("allowed_values")
            if allowed and str(fact.value).lower() not in [v.lower() for v in allowed]:
                warnings.append({
                    "fact": fact.schema_path,
                    "warning": f"Value '{fact.value}' not in allowed values: {allowed}",
                })

            valid_facts.append(fact)

        return valid_facts, warnings
