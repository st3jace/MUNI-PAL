from __future__ import annotations

import re
from typing import Any

from .common import click_tab, parse_table_by_header_tokens
from ..utils import logger, normalize_text


async def extract_ratings(page: Any) -> list[dict[str, Any]]:
    try:
        clicked = await click_tab(page, "Ratings")
        if not clicked:
            return []
        rows = await parse_table_by_header_tokens(page, ["rating", "agency", "outlook", "date"])
        if not rows:
            body = await page.inner_text("body")
            agencies = ["Fitch", "KBRA", "Moody's", "S&P"]
            extracted: list[dict[str, Any]] = []
            for agency in agencies:
                pattern = rf"{re.escape(agency)}\s+(.*?)(?=\n(?:Fitch|KBRA|Moody's|S&P)\b|$)"
                match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
                note = normalize_text(match.group(1)) if match else ""
                # Cap note length to avoid capturing page footer / copyright text.
                if len(note) > 300:
                    first_period = note.find(".")
                    note = note[:first_period + 1] if 0 < first_period < 300 else note[:300]
                if note:
                    extracted.append(
                        {
                            "agency": agency,
                            "rating": "",
                            "outlook": "",
                            "as_of": "",
                            "note": note,
                        }
                    )
            return extracted
        normalized: list[dict[str, Any]] = []
        for row in rows:
            rec = {
                "agency": row.get("rating_agency") or row.get("agency") or row.get("col_1", ""),
                "rating": row.get("rating") or row.get("col_2", ""),
                "outlook": row.get("outlook") or row.get("col_3", ""),
                "as_of": row.get("as_of_date") or row.get("date") or row.get("col_4", ""),
                "fitch": row.get("fitch", ""),
                "kbra": row.get("kbra", ""),
                "moodys": row.get("moodys", ""),
                "sp": row.get("s_p") or row.get("sp", ""),
            }
            if any(rec.values()):
                normalized.append(rec)
        return normalized
    except Exception as exc:
        logger.warning("Ratings tab click failed: %s", exc)
    return []
