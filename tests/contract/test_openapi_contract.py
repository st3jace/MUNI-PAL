"""
OpenAPI contract snapshot test.

Prevents undocumented API drift by requiring intentional snapshot refresh.
"""

from __future__ import annotations

import json
from pathlib import Path

from munipal.main import app


_PYDANTIC_INTERNAL_SCHEMAS = {"ValidationError", "HTTPValidationError"}


def _canonicalize_binary_format(obj: object) -> object:
    """Normalize binary file upload schema across Pydantic versions.

    Pydantic < 2.13 uses ``{"format": "binary", "type": "string"}`` while
    >= 2.13 uses ``{"contentMediaType": "application/octet-stream", "type":
    "string"}``.  Canonicalize to the ``format`` variant so the snapshot is
    stable regardless of Pydantic version.
    """
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "contentMediaType" and v == "application/octet-stream":
                out["format"] = "binary"
            else:
                out[k] = _canonicalize_binary_format(v)
        return out
    if isinstance(obj, list):
        return [_canonicalize_binary_format(item) for item in obj]
    return obj


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
    cleaned = _canonicalize_binary_format(cleaned)
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
