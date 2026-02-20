from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .utils import logger


def ensure_output_dirs(base_dir: Path) -> dict[str, Path]:
    data_dir = base_dir / "data"
    pdf_dir = base_dir / "pdfs"
    logs_dir = base_dir / "logs"
    for p in (data_dir, pdf_dir, logs_dir):
        p.mkdir(parents=True, exist_ok=True)
    return {"data": data_dir, "pdfs": pdf_dir, "logs": logs_dir}


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(checkpoint_path: Path, checkpoint: dict[str, Any]) -> None:
    checkpoint["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_json(checkpoint_path, checkpoint)


def load_checkpoint(checkpoint_path: Path) -> dict[str, Any]:
    return load_json(checkpoint_path, default={}) or {}


def save_processing_queue(output_data_dir: Path, securities: list[dict[str, Any]]) -> Path:
    queue_path = output_data_dir / "processing_queue.json"
    seen = set()
    deduped = []
    for sec in securities:
        detail_url = sec.get("detail_url")
        if detail_url and detail_url not in seen:
            deduped.append(sec)
            seen.add(detail_url)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_qualifying": len(deduped),
        "securities": deduped,
    }
    save_json(queue_path, payload)
    logger.info("Saved queue: %s (%s securities)", queue_path, len(deduped))
    return queue_path


def load_processing_queue(output_data_dir: Path) -> dict[str, Any] | None:
    return load_json(output_data_dir / "processing_queue.json", default=None)


def append_summary_row(csv_path: Path, row: dict[str, Any]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not csv_path.exists()
    fieldnames = [
        "cusip",
        "security_name",
        "state",
        "principal_amount",
        "coupon_pct",
        "maturity_date",
        "dated_date",
        "closing_date",
        "interest_rate_current",
        "rate_type",
        "source_of_repayment",
        "rating_fitch",
        "rating_kbra",
        "rating_moodys",
        "rating_sp",
        "liquidity_facility",
        "provider_identity",
        "remarketing_agent",
        "num_trades",
        "num_rate_resets",
        "num_disclosures",
        "emma_url",
        "crawl_timestamp",
    ]
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(row)
