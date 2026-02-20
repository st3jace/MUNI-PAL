"""
OpenAPI contract snapshot test.

Prevents undocumented API drift by requiring intentional snapshot refresh.
"""

from __future__ import annotations

import json
from pathlib import Path

from munipal.main import app


def _normalize(schema: dict) -> dict:
    """Canonicalize dict ordering for stable equality checks."""
    return json.loads(json.dumps(schema, sort_keys=True))


def test_openapi_contract_snapshot_is_current():
    snapshot_path = Path(__file__).resolve().parents[2] / "contracts" / "openapi.v1.json"
    assert snapshot_path.exists(), (
        "Missing OpenAPI snapshot. Run `python scripts/generate_openapi_snapshot.py` "
        "to create contracts/openapi.v1.json."
    )

    current_schema = _normalize(app.openapi())
    expected_schema = _normalize(json.loads(snapshot_path.read_text(encoding="utf-8")))

    assert current_schema == expected_schema, (
        "OpenAPI contract drift detected. If intentional, regenerate snapshot with "
        "`python scripts/generate_openapi_snapshot.py` and review changes."
    )
