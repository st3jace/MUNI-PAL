from __future__ import annotations

from typing import Any

from .common import click_tab, parse_first_table
from ..utils import logger


async def extract_interest_rates(page: Any) -> list[dict[str, Any]]:
    try:
        clicked = await click_tab(page, "Interest Rate")
        if not clicked:
            return []
        rows = await parse_first_table(page)
        normalized: list[dict[str, Any]] = []
        for row in rows:
            normalized.append(
                {
                    "reset_date_time": row.get("reset_date_time") or row.get("col_1", ""),
                    "interest_rate": row.get("rate") or row.get("interest_rate") or row.get("col_2", ""),
                    "rate_type": row.get("type") or row.get("col_3", ""),
                    "rate_effective_date": row.get("effective_date") or row.get("col_4", ""),
                    "aggregate_par_bank_bonds": row.get("aggregate_par_bank_bonds") or row.get("col_5", ""),
                    "aggregate_par_investors": row.get("aggregate_par_investors_remarketing") or row.get("col_6", ""),
                }
            )
        return normalized
    except Exception as exc:
        logger.warning("Interest Rate tab click failed: %s", exc)
    return []
