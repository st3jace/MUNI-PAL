from __future__ import annotations

from typing import Any

from ..utils import normalize_header, normalize_text


async def click_tab(page: Any, tab_name: str) -> bool:
    # Scroll to top so the tab bar is visible after prior pagination / scrolling.
    try:
        await page.evaluate("window.scrollTo(0, 0)")
    except Exception:
        pass
    selectors = [
        f"role=tab[name*='{tab_name}']",
        f"li[role='tab']:has-text('{tab_name}')",
        f"a[role='tab']:has-text('{tab_name}')",
        f"text={tab_name}",
    ]
    for attempt in range(2):
        for selector in selectors:
            locator = page.locator(selector).first
            if await locator.count() == 0:
                continue
            try:
                await locator.click()
                await page.wait_for_load_state("networkidle")
                return True
            except Exception:
                continue
        if attempt == 0:
            try:
                await page.wait_for_timeout(1000)
            except Exception:
                pass
    return False


async def parse_first_table(page: Any) -> list[dict[str, str]]:
    tables = page.locator("table")
    table_count = await tables.count()
    if table_count == 0:
        return []
    # Choose table with the most body rows to avoid nav/layout tables.
    best_table = None
    best_rows = -1
    for i in range(table_count):
        t = tables.nth(i)
        rows = await t.locator("tbody tr").count()
        if rows > best_rows:
            best_rows = rows
            best_table = t
    if best_table is None:
        return []
    table = best_table
    headers = table.locator("thead th")
    header_count = await headers.count()
    if header_count == 0:
        first_row_headers = table.locator("tbody tr").first.locator("th, td")
        header_count = await first_row_headers.count()
        if header_count == 0:
            return []
        keys = [f"col_{idx + 1}" for idx in range(header_count)]
    else:
        keys = []
        for idx in range(header_count):
            try:
                keys.append(normalize_header(await headers.nth(idx).inner_text(timeout=5000)) or f"col_{idx + 1}")
            except Exception:
                keys.append(f"col_{idx + 1}")

    records: list[dict[str, str]] = []
    rows = table.locator("tbody tr")
    row_count = await rows.count()
    for row_idx in range(row_count):
        row = rows.nth(row_idx)
        td_count = await row.locator("td").count()
        if td_count == 0:
            continue
        cells = row.locator("td, th")
        cell_count = await cells.count()
        if cell_count == 0:
            continue
        rec: dict[str, str] = {}
        for col_idx in range(min(cell_count, len(keys))):
            value = normalize_text(await cells.nth(col_idx).inner_text())
            rec[keys[col_idx]] = value
            rec[f"col_{col_idx + 1}"] = value
        link = row.locator("a").first
        if await link.count() > 0:
            href = await link.get_attribute("href")
            if href:
                rec["_href"] = href
        meaningful = any(v for k, v in rec.items() if k != "_href" and not k.startswith("col_"))
        if meaningful or rec.get("_href"):
            records.append(rec)
    return records


async def parse_table_by_header_tokens(page: Any, tokens: list[str]) -> list[dict[str, str]]:
    tables = page.locator("table")
    table_count = await tables.count()
    tokens_norm = [normalize_header(t) for t in tokens]
    best = None
    best_score = -1
    best_body_count = -1
    for i in range(table_count):
        table = tables.nth(i)
        headers = table.locator("thead th")
        h_count = await headers.count()
        if h_count == 0:
            continue
        header_values: list[str] = []
        for j in range(h_count):
            try:
                header_values.append(normalize_header(await headers.nth(j).inner_text(timeout=5000)))
            except Exception:
                header_values.append("")
        score = 0
        joined = " ".join(header_values)
        for token in tokens_norm:
            if token and token in joined:
                score += 1
        body_count = await table.locator("tbody tr").count()
        # When header scores tie, prefer the table with more data rows.
        if score > best_score or (score == best_score and body_count > best_body_count):
            best = table
            best_score = score
            best_body_count = body_count
    if best is None or best_score <= 0:
        return []

    headers = best.locator("thead th")
    header_count = await headers.count()
    keys = []
    for idx in range(header_count):
        try:
            keys.append(normalize_header(await headers.nth(idx).inner_text(timeout=5000)) or f"col_{idx + 1}")
        except Exception:
            keys.append(f"col_{idx + 1}")
    out: list[dict[str, str]] = []
    rows = best.locator("tbody tr")
    row_count = await rows.count()
    if row_count == 0:
        rows = best.locator("tr")
        row_count = await rows.count()
    for r in range(row_count):
        row = rows.nth(r)
        # Skip pure-header rows (rows with only <th> cells and no <td> cells).
        td_count = await row.locator("td").count()
        if td_count == 0:
            continue
        cells = row.locator("td, th")
        cell_count = await cells.count()
        if cell_count == 0:
            continue
        rec: dict[str, str] = {}
        for c in range(min(cell_count, len(keys))):
            value = normalize_text(await cells.nth(c).inner_text())
            rec[keys[c]] = value
            rec[f"col_{c + 1}"] = value  # positional fallback key
        link = row.locator("a").first
        if await link.count() > 0:
            href = await link.get_attribute("href")
            if href:
                rec["_href"] = href
        meaningful = any(v for k, v in rec.items() if k != "_href" and not k.startswith("col_"))
        if meaningful or rec.get("_href"):
            out.append(rec)
    return out
