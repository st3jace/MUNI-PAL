"""
Generate frozen OpenAPI contract snapshot for API drift detection.
"""

from __future__ import annotations

import json
from pathlib import Path

from munipal.main import app


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    output_path = root / "contracts" / "openapi.v1.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    schema = app.openapi()
    output_path.write_text(
        json.dumps(schema, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"Wrote OpenAPI snapshot to {output_path}")


if __name__ == "__main__":
    main()
