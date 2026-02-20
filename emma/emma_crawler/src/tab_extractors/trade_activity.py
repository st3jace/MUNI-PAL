from __future__ import annotations

import asyncio
from typing import Any

from .common import click_tab, parse_table_by_header_tokens
from ..utils import logger

_TRADE_TOKENS = [
    "trade date/time",
    "settlement date",
    "price",
    "yield",
    "trade amount",
    "trade type",
]


async def extract_trade_activity(page: Any) -> list[dict[str, Any]]:
    try:
        clicked = await click_tab(page, "Trade Activity")
        if not clicked:
            return []
        # Switch to the detail view for row-level trade data.
        details_btn = page.locator("text=Trade Details").first
        if await details_btn.count() > 0:
            try:
                await details_btn.click()
                await page.wait_for_load_state("networkidle")
            except Exception:
                pass
        # Select 100 results per page when available.
        try:
            selects = page.locator("select:visible")
            for i in range(await selects.count()):
                sel = selects.nth(i)
                options_text = await sel.inner_text()
                if "100" in options_text:
                    await sel.select_option(value="100")
                    await page.wait_for_load_state("networkidle")
                    break
        except Exception:
            pass
        # Wait for actual data rows (AJAX-loaded table content).
        try:
            await page.locator("table tbody tr td").first.wait_for(
                state="visible", timeout=15000
            )
        except Exception:
            pass

        all_rows: list[dict[str, str]] = []
        max_pages = 25
        for _ in range(max_pages):
            rows = await parse_table_by_header_tokens(page, _TRADE_TOKENS)
            all_rows.extend(rows)
            # Paginate: try clicking the "Next" link.
            next_link = page.locator("a:has-text('Next')").first
            if await next_link.count() == 0:
                break
            try:
                if not await next_link.is_visible():
                    break
                # Detect disabled state (EMMA wraps disabled links in
                # <li class="...disabled..."> or similar).
                parent_class = await next_link.evaluate(
                    "el => el.closest('li')?.className || el.className || ''"
                )
                if "disabled" in parent_class.lower():
                    break
                await next_link.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(1)
            except Exception:
                break

        normalized: list[dict[str, Any]] = []
        for row in all_rows:
            rec = {
                "trade_date": row.get("trade_date_time") or row.get("trade_date") or row.get("col_1", ""),
                "settlement_date": row.get("settlement_date") or row.get("col_2", ""),
                "price": row.get("price") or row.get("price_pct") or row.get("col_3", ""),
                "yield": row.get("yield") or row.get("yield_pct") or row.get("col_4", ""),
                "calculation_date_price": row.get("calculation_date_price") or row.get("col_5", ""),
                "trade_amount": row.get("trade_amount") or row.get("par_amount") or row.get("col_6", ""),
                "trade_type": row.get("trade_type") or row.get("col_7", ""),
                "special_condition": row.get("special_condition") or row.get("col_8", ""),
            }
            if any(rec.values()):
                normalized.append(rec)
        return normalized
    except Exception as exc:
        logger.warning("Trade Activity extraction failed: %s", exc)
    return []
