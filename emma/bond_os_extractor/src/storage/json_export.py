from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from ..config import get_settings
from ..schema.deal_record import DealRecord

logger = logging.getLogger("bond_os_extractor.storage.json")


def _make_serializable(obj: Any) -> Any:
    """Convert Pydantic models and Decimals for JSON serialization."""
    from decimal import Decimal
    from datetime import date, datetime

    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json", exclude_none=True)
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(i) for i in obj]
    return obj


def export_deal_to_json(record: DealRecord, output_dir: Path | None = None) -> Path:
    """Export a single DealRecord to JSON file."""
    if output_dir is None:
        output_dir = get_settings().extracted_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build filename
    issuer_short = (record.identity.issuer_name or "unknown")[:40]
    issuer_short = "".join(c if c.isalnum() or c in " -_" else "_" for c in issuer_short).strip()
    issuer_short = issuer_short.replace(" ", "_")
    hash_prefix = record.source_hash[:12] if record.source_hash else "nohash"
    filename = f"{hash_prefix}_{issuer_short}.json"

    data = _make_serializable(record)
    output_path = output_dir / filename

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Exported JSON: %s", output_path.name)
    return output_path


def export_all_to_json(
    records: list[DealRecord],
    output_dir: Path | None = None,
) -> int:
    """Export multiple DealRecords to individual JSON files."""
    count = 0
    for record in records:
        try:
            export_deal_to_json(record, output_dir)
            count += 1
        except Exception as exc:
            logger.warning("Failed to export %s: %s", record.source_file, exc)
    return count
