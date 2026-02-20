"""
OpenAPI contract snapshot test.

Prevents undocumented API drift by requiring intentional snapshot refresh.
"""

from __future__ import annotations

import json
from pathlib import Path

from munipal.main import app


_PYDANTIC_INTERNAL_SCHEMAS = {"ValidationError", "HTTPValidationError"}


def _normalize(schema: dict) -> dict:
    """Canonicalize dict ordering and strip Pydantic-internal component schemas.

    ValidationError / HTTPValidationError schema shapes vary across Pydantic
    minor versions (e.g. ctx/input fields added in some releases). They are
    framework internals, not application API contracts, so excluding them keeps
    the snapshot stable across Python / Pydantic version combinations.
    """
    cleaned = json.loads(json.dumps(schema, sort_keys=True))
    components = cleaned.get("components", {})
    schemas = components.get("schemas", {})
    for name in _PYDANTIC_INTERNAL_SCHEMAS:
        schemas.pop(name, None)
    return cleaned


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
