from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin

from .storage import save_checkpoint
from .utils import SessionExpiredError, delay_ms, first_visible_locator, logger, normalize_header, normalize_text, parse_currency


async def set_results_per_page(page: Any, per_page: int) -> None:
    selectors = [
        "select[id*='ddlResultsPerPage']",
        "select[name*='ResultsPerPage']",
        "select:near(:text('Display'))",
    ]
    locator = None
    for selector in selectors:
        candidate = page.locator(selector).first
        if await candidate.count() > 0:
            locator = candidate
            break
    if locator is None:
        logger.warning("Results-per-page selector not found; continuing with default page size")
        return
    try:
        await locator.select_option(value=str(per_page))
    except Exception:
        await locator.select_option(label=str(per_page))
    await page.wait_for_load_state("networkidle")
    logger.info("Set results per page to %s", per_page)


async def ensure_principal_sort_desc(page: Any, wait_ms: int = 2000) -> None:
    header = await first_visible_locator(
        page,
        [
            "th:has-text('Principal Amount At Issuance')",
            "a:has-text('Principal Amount At Issuance')",
            "text=Principal Amount At Issuance",
        ],
    )
    if header is None:
        logger.warning("Principal column header not found; continuing without forced sort")
        return

    # Click twice max: first click typically sorts ascending, second descending.
    for attempt in range(2):
        await header.click()
        await page.wait_for_load_state("networkidle")
        await delay_ms(wait_ms)

        rows = await extract_results_rows(page)
        principals = []
        for row in rows[:5]:
            value = parse_currency(row.get("principal_amount"))
            if value is not None:
                principals.append(value)
        if len(principals) >= 2 and principals[0] >= principals[1]:
            logger.info("Principal column sorted descending")
            return
    logger.info("Principal sort click attempted; proceeding with parsed filtering")


async def _find_next_button(page: Any) -> Any | None:
    return await first_visible_locator(
        page,
        [
            "a:has-text('Next')",
            "button:has-text('Next')",
            "input[type='button'][value='Next']",
            "input[type='submit'][value='Next']",
            "[aria-label='Next']",
        ],
    )


async def _is_disabled(locator: Any) -> bool:
    try:
        disabled_attr = await locator.get_attribute("disabled")
        aria_disabled = await locator.get_attribute("aria-disabled")
        class_attr = (await locator.get_attribute("class")) or ""
        return bool(disabled_attr) or aria_disabled == "true" or "disabled" in class_attr.lower()
    except Exception:
        return False


def _parse_principal_from_text(text: str) -> str:
    patterns = [
        r"Principal Amount At Issuance[^0-9]*([0-9][0-9,]*)",
        r"Principal Amount[^0-9]*([0-9][0-9,]*)",
        r"\$([0-9][0-9,]{6,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _detect_principal_from_cells(cell_values: list[str]) -> str:
    candidates: list[int] = []
    for value in cell_values:
        parsed = parse_currency(value)
        if parsed is None:
            continue
        # Principal values are typically six+ digits with commas in this table.
        if parsed >= 100000:
            candidates.append(parsed)
    if not candidates:
        return ""
    return f"{max(candidates):,}"


async def _extract_rows_from_links(page: Any) -> list[dict[str, str]]:
    links = page.locator("a[href*='/Security/Details/']")
    count = await links.count()
    if count == 0:
        return []
    rows: list[dict[str, str]] = []
    for i in range(count):
        link = links.nth(i)
        href = await link.get_attribute("href")
        if not href:
            continue
        desc = normalize_text(await link.inner_text())
        context_text = ""
        try:
            # Use DOM closest() to avoid fragile union XPath behavior.
            raw_context = await link.evaluate(
                """(el) => {
                    const c = el.closest('tr, li, div');
                    return c ? c.innerText : '';
                }"""
            )
            context_text = normalize_text(raw_context)
        except Exception:
            context_text = desc
        principal = _parse_principal_from_text(context_text)
        maturity_match = re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", context_text)
        maturity = maturity_match.group(0) if maturity_match else ""
        coupon_match = re.search(r"\b\d+(\.\d+)?%\b", context_text)
        coupon = coupon_match.group(0) if coupon_match else ""
        rows.append(
            {
                "state": "",
                "description_text": desc,
                "description_link": href,
                "coupon_pct": coupon,
                "maturity_date": maturity,
                "principal_amount": principal,
                "dated_date": "",
            }
        )
    return rows


async def _find_results_table(page: Any) -> Any | None:
    tables = page.locator("table")
    table_count = await tables.count()
    for i in range(table_count):
        table = tables.nth(i)
        row_count = await table.locator("tbody tr").count()
        if row_count == 0:
            continue
        link_count = await table.locator("a[href*='/Security/Details/']").count()
        if link_count > 0:
            return table
    return None


async def _principal_col_index(table: Any) -> int | None:
    headers = table.locator("th")
    count = await headers.count()
    for i in range(count):
        txt = normalize_text(await headers.nth(i).inner_text()).lower()
        if "principal amount" in txt and "issuance" in txt:
            return i
    return None


async def extract_results_rows(page: Any) -> list[dict[str, str]]:
    table = await _find_results_table(page)
    if table is None:
        return await _extract_rows_from_links(page)

    header_cells = table.locator("thead th")
    header_count = await header_cells.count()
    headers: list[str] = []
    for idx in range(header_count):
        headers.append(normalize_header(await header_cells.nth(idx).inner_text()) or f"col_{idx + 1}")

    row_locator = table.locator("tbody tr")
    row_count = await row_locator.count()
    principal_idx = await _principal_col_index(table)
    rows: list[dict[str, str]] = []
    for idx in range(row_count):
        row = row_locator.nth(idx)
        cells = row.locator("td")
        cell_count = await cells.count()
        if cell_count < 5:
            continue
        raw: dict[str, str] = {}
        for col_idx in range(cell_count):
            key = headers[col_idx] if col_idx < len(headers) else f"col_{col_idx + 1}"
            raw[key] = normalize_text(await cells.nth(col_idx).inner_text())
        all_values = [raw[k] for k in raw.keys()]
        description_link = row.locator("a").first
        href = await description_link.get_attribute("href")
        description_text = raw.get("description") or raw.get("security_description") or raw.get("col_2", "")
        state = raw.get("state") or raw.get("col_1", "")
        coupon_pct = raw.get("coupon") or raw.get("coupon_pct") or raw.get("col_3", "")
        maturity_date = raw.get("maturity_date") or raw.get("col_4", "")
        principal_from_index = ""
        if principal_idx is not None and principal_idx < cell_count:
            principal_from_index = normalize_text(await cells.nth(principal_idx).inner_text())
        principal_amount_guess = (
            principal_from_index
            or
            raw.get("principal_amount_at_issuance_amount")
            or raw.get("principal_amount_at_issuance")
            or raw.get("principal_amount")
            or raw.get("principal_amount_at_issuance_amount_amount")
            or raw.get("principal_amount_at_issuance_dollar")
            or raw.get("col_5", "")
        )
        if parse_currency(principal_amount_guess) is None:
            principal_amount = _detect_principal_from_cells(all_values)
        else:
            principal_amount = principal_amount_guess
        dated_date = raw.get("dated_date") or raw.get("col_6", "")
        rows.append(
            {
                "state": state,
                "description_text": description_text,
                "description_link": href or "",
                "coupon_pct": coupon_pct,
                "maturity_date": maturity_date,
                "principal_amount": principal_amount,
                "dated_date": dated_date,
            }
        )
    if rows:
        return rows
    return await _extract_rows_from_links(page)


async def go_to_page(page: Any, target_page: int) -> None:
    if target_page <= 1:
        return
    for p in range(2, target_page + 1):
        next_button = await _find_next_button(page)
        if next_button is None:
            raise SessionExpiredError(f"Unable to navigate to page {target_page}; missing Next on step {p}")
        if await _is_disabled(next_button):
            raise SessionExpiredError(f"Unable to navigate to page {target_page}; Next is disabled at step {p}")
        await next_button.click()
        await page.wait_for_load_state("networkidle")


async def collect_all_qualifying_securities(
    page: Any,
    config: dict[str, Any],
    checkpoint: dict[str, Any],
    checkpoint_path: Any,
) -> list[dict[str, Any]]:
    timing = config["crawler"]["timing"]
    min_principal = int(config["search"]["result_filters"]["min_principal_amount"])
    start_page = int(checkpoint.get("phase2_last_page_scanned", 0)) + 1
    current_page = start_page
    qualifying: list[dict[str, Any]] = checkpoint.get("phase2_queue", [])

    if start_page > 1:
        logger.info("Resuming Phase 2 at page %s", start_page)
        await go_to_page(page, start_page)

    total_scanned = 0
    while True:
        rows = []
        empty_attempts = int(timing.get("empty_results_retry_attempts", 5))
        retry_delay = int(timing.get("empty_results_retry_delay", 3000))
        for attempt in range(empty_attempts):
            rows = await extract_results_rows(page)
            if rows:
                break
            no_results = page.locator("text=/No\\s+results|0\\s+securities|No\\s+records/i").first
            if await no_results.count() > 0 and await no_results.is_visible():
                logger.info("Results page indicates no matching securities")
                return qualifying
            logger.info(
                "Results table not ready yet (attempt %s/%s); waiting %sms",
                attempt + 1,
                empty_attempts,
                retry_delay,
            )
            await delay_ms(retry_delay)

        if not rows:
            raise SessionExpiredError("No rows found on results page after wait retries")
        total_scanned += len(rows)
        sample_principals: list[int] = []
        for row in rows:
            principal = parse_currency(row["principal_amount"])
            if principal is not None and len(sample_principals) < 5:
                sample_principals.append(principal)
            if principal is None or principal < min_principal:
                continue
            detail_url = urljoin(page.url, row["description_link"])
            qualifying.append(
                {
                    "detail_url": detail_url,
                    "description": row["description_text"],
                    "state": row["state"],
                    "principal_amount": principal,
                    "coupon": row["coupon_pct"],
                    "maturity_date": row["maturity_date"],
                    "dated_date": row["dated_date"],
                    "source_page": current_page,
                    "url_hash": detail_url.rstrip("/").split("/")[-1],
                }
            )

        checkpoint["phase2_last_page_scanned"] = current_page
        checkpoint["phase2_queue"] = qualifying
        save_checkpoint(checkpoint_path, checkpoint)
        logger.info(
            "Page %s scanned (%s rows). Qualifying so far: %s. Sample principals: %s",
            current_page,
            len(rows),
            len(qualifying),
            sample_principals,
        )

        next_button = await _find_next_button(page)
        if next_button is None:
            break
        if await _is_disabled(next_button):
            break
        await next_button.click()
        await page.wait_for_load_state("networkidle")
        await delay_ms(timing["between_pages"])
        current_page += 1

    logger.info("Phase 2 complete: %s qualifying out of %s scanned", len(qualifying), total_scanned)
    return qualifying
