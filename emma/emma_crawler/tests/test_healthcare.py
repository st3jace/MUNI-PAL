"""Tests for EMMA crawler healthcare sector changes.

Covers:
- Date chunking helpers (generate_year_chunks, _parse_date, _format_date)
- Dedup helper (_get_existing_url_hashes)
- FIELD_MAP completeness (purpose_sector, issuer_name, state)
- Config loading with CLI overrides
- YAML config file validation
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


# ---------------------------------------------------------------------------
# Date chunking helpers
# ---------------------------------------------------------------------------

from src.main import _format_date, _parse_date, generate_year_chunks, _get_existing_url_hashes


class TestParseDate:
    def test_standard_date(self):
        result = _parse_date("1/1/2020")
        assert result == datetime(2020, 1, 1)

    def test_padded_date(self):
        result = _parse_date("01/15/2023")
        assert result == datetime(2023, 1, 15)

    def test_today(self):
        result = _parse_date("TODAY")
        assert result.date() == datetime.now().date()

    def test_today_lowercase(self):
        result = _parse_date("today")
        assert result.date() == datetime.now().date()

    def test_whitespace(self):
        result = _parse_date("  1/1/2020  ")
        assert result == datetime(2020, 1, 1)


class TestFormatDate:
    def test_format_no_padding(self):
        result = _format_date(datetime(2020, 1, 1))
        assert result == "1/1/2020"

    def test_format_double_digit_month_day(self):
        result = _format_date(datetime(2023, 12, 31))
        assert result == "12/31/2023"

    def test_roundtrip(self):
        original = "6/15/2022"
        dt = _parse_date(original)
        assert _format_date(dt) == original


class TestGenerateYearChunks:
    def test_single_year(self):
        chunks = generate_year_chunks("1/1/2020", "12/31/2020")
        assert len(chunks) == 1
        assert chunks[0] == ("1/1/2020", "12/31/2020")

    def test_two_full_years(self):
        chunks = generate_year_chunks("1/1/2020", "12/31/2021")
        assert len(chunks) == 2
        assert chunks[0] == ("1/1/2020", "12/31/2020")
        assert chunks[1] == ("1/1/2021", "12/31/2021")

    def test_multi_year_range(self):
        chunks = generate_year_chunks("1/1/2020", "6/15/2023")
        assert len(chunks) == 4
        assert chunks[0][0] == "1/1/2020"
        assert chunks[0][1] == "12/31/2020"
        assert chunks[1][0] == "1/1/2021"
        assert chunks[1][1] == "12/31/2021"
        assert chunks[2][0] == "1/1/2022"
        assert chunks[2][1] == "12/31/2022"
        assert chunks[3][0] == "1/1/2023"
        assert chunks[3][1] == "6/15/2023"

    def test_mid_year_start(self):
        chunks = generate_year_chunks("6/1/2020", "3/15/2021")
        assert len(chunks) == 2
        assert chunks[0] == ("6/1/2020", "12/31/2020")
        assert chunks[1] == ("1/1/2021", "3/15/2021")

    def test_same_date_returns_single_chunk(self):
        chunks = generate_year_chunks("1/1/2020", "1/1/2020")
        assert len(chunks) == 1

    def test_reversed_dates_returns_single_chunk(self):
        chunks = generate_year_chunks("12/31/2021", "1/1/2020")
        assert len(chunks) == 1

    def test_today_end_date(self):
        chunks = generate_year_chunks("1/1/2025", "TODAY")
        # Should produce at least one chunk
        assert len(chunks) >= 1
        assert chunks[0][0] == "1/1/2025"

    def test_full_healthcare_range(self):
        """The actual range used in healthcare configs."""
        chunks = generate_year_chunks("1/1/2020", "2/19/2026")
        assert len(chunks) == 7  # 2020, 2021, 2022, 2023, 2024, 2025, 2026
        # First chunk starts on config date
        assert chunks[0][0] == "1/1/2020"
        # Last chunk ends on config date
        assert chunks[-1][1] == "2/19/2026"


# ---------------------------------------------------------------------------
# Dedup helper
# ---------------------------------------------------------------------------

class TestGetExistingUrlHashes:
    def test_empty_directory(self, tmp_path):
        result = _get_existing_url_hashes(tmp_path)
        assert result == set()

    def test_finds_json_files(self, tmp_path):
        (tmp_path / "ABC123.json").write_text("{}")
        (tmp_path / "DEF456.json").write_text("{}")
        result = _get_existing_url_hashes(tmp_path)
        assert result == {"ABC123", "DEF456"}

    def test_excludes_processing_queue(self, tmp_path):
        (tmp_path / "processing_queue.json").write_text("{}")
        (tmp_path / "ABC123.json").write_text("{}")
        result = _get_existing_url_hashes(tmp_path)
        assert result == {"ABC123"}
        assert "processing_queue" not in result

    def test_non_json_files_ignored(self, tmp_path):
        (tmp_path / "ABC123.json").write_text("{}")
        (tmp_path / "notes.txt").write_text("notes")
        (tmp_path / "data.csv").write_text("a,b")
        result = _get_existing_url_hashes(tmp_path)
        assert result == {"ABC123"}


# ---------------------------------------------------------------------------
# FIELD_MAP completeness
# ---------------------------------------------------------------------------

from src.search import FIELD_MAP


class TestFieldMap:
    """Verify all healthcare-critical fields are wired into FIELD_MAP."""

    def test_purpose_sector_present(self):
        assert "purpose_sector" in FIELD_MAP
        selectors = FIELD_MAP["purpose_sector"]
        assert any("Purpose" in s for s in selectors)

    def test_issuer_name_present(self):
        assert "issuer_name" in FIELD_MAP
        selectors = FIELD_MAP["issuer_name"]
        assert any("IssuerName" in s for s in selectors)

    def test_state_present(self):
        assert "state" in FIELD_MAP
        selectors = FIELD_MAP["state"]
        assert any("State" in s for s in selectors)

    def test_issue_description_present(self):
        assert "issue_description" in FIELD_MAP

    def test_source_of_repayment_present(self):
        assert "source_of_repayment" in FIELD_MAP

    def test_closing_dates_present(self):
        assert "closing_date_from" in FIELD_MAP
        assert "closing_date_to" in FIELD_MAP

    def test_all_selectors_are_lists(self):
        for key, selectors in FIELD_MAP.items():
            assert isinstance(selectors, list), f"{key} selectors should be a list"
            assert len(selectors) >= 1, f"{key} should have at least 1 selector"


# ---------------------------------------------------------------------------
# Config file validation
# ---------------------------------------------------------------------------

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

REQUIRED_SEARCH_KEYS = [
    "search_filters", "result_filters", "view_mode",
]

REQUIRED_SECURITY_INFO_KEYS = [
    "state", "issuer_name", "issue_description",
    "closing_date_from", "closing_date_to",
    "purpose_sector", "source_of_repayment",
    "rate_type", "insured", "tax_status", "callable",
]


class TestHealthcareConfigs:
    """Validate all healthcare YAML config files parse correctly and have required fields."""

    @staticmethod
    def _load_yaml(filename: str) -> dict:
        path = CONFIG_DIR / filename
        assert path.exists(), f"Config file not found: {path}"
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @pytest.mark.parametrize("filename", [
        "search_params_healthcare.yaml",
        "search_params_healthcare_hospital.yaml",
        "search_params_healthcare_ccrc.yaml",
        "search_params_healthcare_senior.yaml",
        "search_params_healthcare_behavioral.yaml",
        "search_params_healthcare_medical.yaml",
        "search_params_healthcare_clinic.yaml",
    ])
    def test_yaml_parses(self, filename):
        cfg = self._load_yaml(filename)
        assert isinstance(cfg, dict)

    @pytest.mark.parametrize("filename", [
        "search_params_healthcare.yaml",
        "search_params_healthcare_hospital.yaml",
        "search_params_healthcare_ccrc.yaml",
        "search_params_healthcare_senior.yaml",
        "search_params_healthcare_behavioral.yaml",
        "search_params_healthcare_medical.yaml",
        "search_params_healthcare_clinic.yaml",
    ])
    def test_has_required_top_level_keys(self, filename):
        cfg = self._load_yaml(filename)
        for key in REQUIRED_SEARCH_KEYS:
            assert key in cfg, f"{filename} missing top-level key: {key}"

    @pytest.mark.parametrize("filename", [
        "search_params_healthcare.yaml",
        "search_params_healthcare_hospital.yaml",
        "search_params_healthcare_ccrc.yaml",
        "search_params_healthcare_senior.yaml",
        "search_params_healthcare_behavioral.yaml",
        "search_params_healthcare_medical.yaml",
        "search_params_healthcare_clinic.yaml",
    ])
    def test_has_security_information_keys(self, filename):
        cfg = self._load_yaml(filename)
        sec_info = cfg["search_filters"]["security_information"]
        for key in REQUIRED_SECURITY_INFO_KEYS:
            assert key in sec_info, f"{filename} missing security_information key: {key}"

    def test_broad_pass_uses_health_sector(self):
        cfg = self._load_yaml("search_params_healthcare.yaml")
        assert cfg["search_filters"]["security_information"]["purpose_sector"] == "Health"
        # Broad pass should have blank issue_description
        assert cfg["search_filters"]["security_information"]["issue_description"] == ""

    @pytest.mark.parametrize("filename,expected_keyword", [
        ("search_params_healthcare_hospital.yaml", "Hospital"),
        ("search_params_healthcare_ccrc.yaml", "Continuing Care"),
        ("search_params_healthcare_senior.yaml", "Senior Living"),
        ("search_params_healthcare_behavioral.yaml", "Behavioral"),
        ("search_params_healthcare_medical.yaml", "Medical"),
        ("search_params_healthcare_clinic.yaml", "Clinic"),
    ])
    def test_keyword_pass_has_correct_keyword(self, filename, expected_keyword):
        cfg = self._load_yaml(filename)
        sec_info = cfg["search_filters"]["security_information"]
        assert sec_info["issue_description"] == expected_keyword
        # Keyword passes use purpose_sector "All" to catch mislabeled bonds
        assert sec_info["purpose_sector"] == "All"

    @pytest.mark.parametrize("filename", [
        "search_params_healthcare.yaml",
        "search_params_healthcare_hospital.yaml",
        "search_params_healthcare_ccrc.yaml",
        "search_params_healthcare_senior.yaml",
        "search_params_healthcare_behavioral.yaml",
        "search_params_healthcare_medical.yaml",
        "search_params_healthcare_clinic.yaml",
    ])
    def test_min_principal_amount_is_set(self, filename):
        cfg = self._load_yaml(filename)
        min_principal = cfg["result_filters"]["min_principal_amount"]
        assert isinstance(min_principal, int)
        assert min_principal >= 1_000_000

    def test_original_waste_config_unchanged(self):
        """Ensure the original waste config was not modified."""
        cfg = self._load_yaml("search_params.yaml")
        assert cfg["search_filters"]["security_information"]["issue_description"] == "Waste"
        assert cfg["search_filters"]["security_information"]["source_of_repayment"] == "Revenue"


# ---------------------------------------------------------------------------
# Config loading with CLI overrides
# ---------------------------------------------------------------------------

class TestLoadConfig:
    def test_date_overrides_applied(self, tmp_path):
        """Verify --date-from and --date-to override YAML values."""
        yaml_content = {
            "search_filters": {
                "security_information": {
                    "closing_date_from": "1/1/2020",
                    "closing_date_to": "12/31/2025",
                }
            }
        }
        yaml_path = tmp_path / "search_params.yaml"
        yaml_path.write_text(yaml.dump(yaml_content))
        crawler_path = tmp_path / "crawler_settings.yaml"
        crawler_path.write_text(yaml.dump({
            "logging": {"level": "INFO", "format": "%(message)s"},
            "browser": {"headless": True},
            "timing": {},
            "pagination": {},
        }))

        from src.main import load_config
        args = MagicMock()
        args.search_params = "search_params.yaml"
        args.date_from = "6/1/2022"
        args.date_to = "12/31/2022"
        args.log_level = None
        args.emma_username = None
        args.emma_password = None

        config = load_config(tmp_path, args)
        sec_info = config["search"]["search_filters"]["security_information"]
        assert sec_info["closing_date_from"] == "6/1/2022"
        assert sec_info["closing_date_to"] == "12/31/2022"

    def test_no_date_overrides_preserves_yaml(self, tmp_path):
        """Verify YAML values are preserved when no CLI overrides given."""
        yaml_content = {
            "search_filters": {
                "security_information": {
                    "closing_date_from": "1/1/2020",
                    "closing_date_to": "TODAY",
                }
            }
        }
        yaml_path = tmp_path / "search_params.yaml"
        yaml_path.write_text(yaml.dump(yaml_content))
        crawler_path = tmp_path / "crawler_settings.yaml"
        crawler_path.write_text(yaml.dump({
            "logging": {"level": "INFO", "format": "%(message)s"},
            "browser": {"headless": True},
            "timing": {},
            "pagination": {},
        }))

        from src.main import load_config
        args = MagicMock()
        args.search_params = "search_params.yaml"
        args.date_from = None
        args.date_to = None
        args.log_level = None
        args.emma_username = None
        args.emma_password = None

        config = load_config(tmp_path, args)
        sec_info = config["search"]["search_filters"]["security_information"]
        assert sec_info["closing_date_from"] == "1/1/2020"
        assert sec_info["closing_date_to"] == "TODAY"
