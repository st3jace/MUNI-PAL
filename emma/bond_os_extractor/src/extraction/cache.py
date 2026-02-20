from __future__ import annotations

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger("bond_os_extractor.extraction.cache")


def compute_cache_key(doc_hash: str, section_id: str, extractor_name: str) -> str:
    raw = f"{doc_hash}:{section_id}:{extractor_name}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def save_to_cache(cache_dir: Path, key: str, response: dict[str, Any]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "key": key,
        "timestamp": time.time(),
        "response": response,
    }
    path = cache_dir / f"{key}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, default=str)


def load_from_cache(
    cache_dir: Path,
    key: str,
    ttl_days: int = 30,
) -> dict[str, Any] | None:
    path = cache_dir / f"{key}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            entry = json.load(f)
        # Check TTL
        age_days = (time.time() - entry.get("timestamp", 0)) / 86400
        if age_days > ttl_days:
            logger.debug("Cache entry %s expired (%.1f days old)", key, age_days)
            path.unlink(missing_ok=True)
            return None
        return entry.get("response")
    except Exception as exc:
        logger.debug("Cache read failed for %s: %s", key, exc)
        return None


def clear_cache(cache_dir: Path, older_than_days: int = 0) -> int:
    """Remove cache entries older than N days. Use 0 to clear all."""
    removed = 0
    if not cache_dir.exists():
        return 0
    for path in cache_dir.glob("*.json"):
        try:
            if older_than_days > 0:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                age_days = (time.time() - entry.get("timestamp", 0)) / 86400
                if age_days <= older_than_days:
                    continue
            path.unlink()
            removed += 1
        except Exception:
            continue
    return removed
