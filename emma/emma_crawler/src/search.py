from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from .utils import delay_ms, first_visible_locator, logger


SEARCH_URL = "https://emma.msrb.org/Search/Search.aspx"


FIELD_MAP = {
    "state": [
        "select[id*='ddlState']",
        "select[name*='State']",
    ],
    "issuer_name": [
        "input[id*='txtIssuerName']",
        "input[name*='IssuerName']",
    ],
    "issue_description": [
        "input[id*='txtIssueDescription']",
        "input[name*='IssueDescription']",
    ],
    "closing_date_from": [
        "input[id*='txtClosingDateFrom']",
        "input[name*='ClosingDateFrom']",
        "xpath=//*[contains(normalize-space(.), 'Closing Date')]/following::input[1]",
        "xpath=//*[contains(normalize-space(.), 'Close Date')]/following::input[1]",
    ],
    "closing_date_to": [
        "input[id*='txtClosingDateTo']",
        "input[name*='ClosingDateTo']",
        "xpath=//*[contains(normalize-space(.), 'Closing Date')]/following::input[2]",
        "xpath=//*[contains(normalize-space(.), 'Close Date')]/following::input[2]",
    ],
    "purpose_sector": [
        "select[id*='ddlPurposeSector']",
        "select[id*='ddlPurpose']",
        "select[name*='PurposeSector']",
        "select[name*='Purpose']",
    ],
    "source_of_repayment": [
        "select[id*='ddlSourceOfRepayment']",
        "select[name*='SourceOfRepayment']",
    ],
}


async def ensure_security_panel_open(page: Any) -> None:
    panel_headers = [
        "text=Security Information",
        "button:has-text('Security Information')",
        "a:has-text('Security Information')",
    ]
    header = await first_visible_locator(page, panel_headers)
    if header is None:
        return
    try:
        expanded = await header.get_attribute("aria-expanded")
        if expanded == "false":
            await header.click()
            await page.wait_for_load_state("networkidle")
    except Exception:
        # If aria-expanded is unavailable, a single click attempt is harmless.
        try:
            await header.click(timeout=1000)
            await page.wait_for_load_state("networkidle")
        except Exception:
            pass


def _roots(page: Any) -> list[Any]:
    return [page, *page.frames]


async def _first_visible_in_roots(page: Any, selectors: list[str]) -> Any | None:
    for root in _roots(page):
        loc = await first_visible_locator(root, selectors)
        if loc is not None:
            return loc
    return None


async def _find_by_label(page: Any, label_text: str, is_select: bool = False) -> Any | None:
    label_selectors = [
        f"label:has-text('{label_text}')",
        f"td:has-text('{label_text}')",
        f"th:has-text('{label_text}')",
        f"span:has-text('{label_text}')",
    ]
    target_tag = "select" if is_select else "input"
    for root in _roots(page):
        for selector in label_selectors:
            node = root.locator(selector).first
            if await node.count() == 0:
                continue
            try:
                html_for = await node.get_attribute("for")
            except Exception:
                html_for = None
            if html_for:
                by_for = root.locator(f"#{html_for}").first
                if await by_for.count() > 0:
                    return by_for
            sibling = node.locator(f"xpath=following::{target_tag}[1]").first
            if await sibling.count() > 0:
                return sibling
    return None


async def _find_close_date_input(page: Any, which: str) -> Any | None:
    """
    EMMA can render Close Date as one label with two adjacent inputs (from/to).
    `which` is 'from' or 'to'.
    """
    for root in _roots(page):
        for label_text in ("Closing Date", "Close Date"):
            label = root.locator(
                f"label:has-text('{label_text}'), td:has-text('{label_text}'), span:has-text('{label_text}'), div:has-text('{label_text}')"
            ).first
            if await label.count() == 0:
                continue
            inputs = label.locator("xpath=following::input[position()<=2]")
            count = await inputs.count()
            if count == 0:
                continue
            if which == "from":
                return inputs.nth(0)
            if which == "to" and count > 1:
                return inputs.nth(1)
    return None


async def navigate_to_search(page: Any, timeout_ms: int) -> None:
    await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=timeout_ms)
    await page.wait_for_load_state("networkidle", timeout=timeout_ms)
    logger.info("Loaded search page")


async def _accept_terms_if_present(page: Any) -> bool:
    accept_selectors = [
        "button:has-text('I Agree')",
        "button:has-text('Accept')",
        "button:has-text('Agree')",
        "input[type='submit'][value*='Agree']",
        "input[type='submit'][value*='Accept']",
        "a:has-text('I Agree')",
        "a:has-text('Accept')",
    ]
    checkbox_selectors = [
        "input[type='checkbox'][id*='agree']",
        "input[type='checkbox'][name*='agree']",
        "input[type='checkbox'][id*='terms']",
        "input[type='checkbox'][name*='terms']",
    ]

    changed = False
    for cb_selector in checkbox_selectors:
        cb = page.locator(cb_selector).first
        if await cb.count() > 0 and await cb.is_visible():
            try:
                await cb.check()
                changed = True
            except Exception:
                pass

    # Accept/agree controls can appear multiple times (cookie banner + modal + hidden copies).
    # Try each candidate quickly and never block the whole run on one stale/off-screen element.
    clicked_any = False
    for selector in accept_selectors:
        loc = page.locator(selector)
        count = await loc.count()
        if count == 0:
            continue
        for idx in range(count):
            candidate = loc.nth(idx)
            try:
                if not await candidate.is_visible():
                    continue
            except Exception:
                continue
            try:
                await candidate.click(timeout=1500, force=True)
                await page.wait_for_load_state("networkidle", timeout=5000)
                clicked_any = True
            except Exception:
                # Ignore unreachable/out-of-viewport duplicates and move on.
                continue

    if clicked_any:
        changed = True
        logger.info("Accepted terms/entry gate")
    return changed


async def _login_if_present(page: Any, username: str | None, password: str | None) -> bool:
    user_field = await first_visible_locator(
        page,
        [
            "input[type='email']",
            "input[id*='user']",
            "input[name*='user']",
            "input[id*='login']",
            "input[name*='login']",
            "input[id*='email']",
            "input[name*='email']",
        ],
    )
    pass_field = await first_visible_locator(
        page,
        [
            "input[type='password']",
            "input[id*='pass']",
            "input[name*='pass']",
        ],
    )
    if user_field is None or pass_field is None:
        return False
    if not username or not password:
        logger.warning("Login form detected but no credentials were provided")
        return False
    await user_field.fill(username)
    await pass_field.fill(password)
    submit = await first_visible_locator(
        page,
        [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Sign In')",
            "button:has-text('Log In')",
            "button:has-text('Login')",
        ],
    )
    if submit is None:
        logger.warning("Login form detected but submit button not found")
        return False
    await submit.click()
    await page.wait_for_load_state("networkidle")
    logger.info("Submitted login form")
    return True


async def ensure_search_ready(
    page: Any,
    timeout_ms: int,
    username: str | None = None,
    password: str | None = None,
) -> None:
    # EMMA can gate with terms and/or login before the search form is visible.
    for attempt in range(5):
        issue_field = await first_visible_locator(page, FIELD_MAP["issue_description"])
        run_button = await first_visible_locator(
            page,
            [
                "input[id*='btnSearch']",
                "button:has-text('Run Search')",
                "text=Run Search",
            ],
        )
        if issue_field is not None or run_button is not None:
            return
        changed_terms = await _accept_terms_if_present(page)
        changed_login = await _login_if_present(page, username=username, password=password)
        if not changed_terms and not changed_login:
            break
        await page.wait_for_load_state("networkidle", timeout=timeout_ms)
        await delay_ms(1200)
        logger.debug("Search gate handling attempt %s complete", attempt + 1)


async def populate_search_filters(page: Any, search_filters: dict[str, Any], action_delay_ms: int) -> None:
    security_filters = search_filters.get("security_information", {})
    await ensure_security_panel_open(page)

    label_map = {
        "state": ("State", True),
        "issuer_name": ("Issuer Name", False),
        "issue_description": ("Issue Description", False),
        "closing_date_from": ("Closing Date", False),
        "closing_date_to": ("Closing Date", False),
        "purpose_sector": ("Purpose", True),
        "source_of_repayment": ("Source of Repayment", True),
    }

    for key, selectors in FIELD_MAP.items():
        value = security_filters.get(key)
        if value in (None, ""):
            continue
        if isinstance(value, str) and value.strip().upper() == "TODAY":
            value = datetime.now().strftime("%m/%d/%Y")
        locator = None
        for _ in range(5):
            locator = await _first_visible_in_roots(page, selectors)
            if locator is not None:
                break
            await delay_ms(800)
        if locator is None and key == "closing_date_from":
            locator = await _find_close_date_input(page, "from")
        if locator is None and key == "closing_date_to":
            locator = await _find_close_date_input(page, "to")
        if locator is None and key in label_map:
            label, is_select = label_map[key]
            locator = await _find_by_label(page, label_text=label, is_select=is_select)
        if locator is None:
            logger.warning("Search field not found for %s", key)
            continue
        tag_name = (await locator.evaluate("el => el.tagName")).lower()
        if tag_name == "select":
            try:
                await locator.select_option(label=str(value))
            except Exception:
                try:
                    await locator.select_option(value=str(value))
                except Exception:
                    options = locator.locator("option")
                    opt_count = await options.count()
                    selected = False
                    for i in range(opt_count):
                        opt = options.nth(i)
                        txt = ((await opt.inner_text()) or "").strip().lower()
                        if str(value).lower() in txt:
                            opt_val = await opt.get_attribute("value")
                            if opt_val is not None:
                                await locator.select_option(value=opt_val)
                                selected = True
                                break
                    if not selected:
                        logger.warning("Could not map select option for %s=%s", key, value)
        else:
            await locator.fill(str(value))
        logger.info("Applied filter %s=%s", key, value)
        await delay_ms(action_delay_ms)
    await page.wait_for_load_state("networkidle")


async def run_search(page: Any, timeout_ms: int) -> None:
    run_button = await _first_visible_in_roots(
        page,
        ["input[id*='btnSearch']", "button:has-text('Run Search')", "text=Run Search"],
    )
    if run_button is None:
        raise RuntimeError("Run Search button not found")
    await run_button.click()
    await page.wait_for_load_state("networkidle", timeout=timeout_ms)
    logger.info("Search submitted")


async def wait_for_results_ready(
    page: Any,
    timeout_ms: int = 180000,
    poll_interval_ms: int = 1000,
) -> str:
    """
    Wait until the page is clearly in one of these states:
    - results_table: table rows exist
    - no_results: explicit no-results text is visible
    - result_count: count text like '593 securities' appears
    """
    checks = [
        ("results_table", "table tbody tr"),
        ("no_results", "text=/No\\s+results|0\\s+securities|No\\s+records/i"),
        ("needs_filters", "text=/Please\\s+use\\s+filters\\s+to\\s+narrow\\s+your\\s+search/i"),
        ("result_count", "text=/\\d+[\\d,]*\\s+securities/i"),
    ]

    deadline = asyncio.get_event_loop().time() + (timeout_ms / 1000.0)
    while asyncio.get_event_loop().time() < deadline:
        for state, selector in checks:
            loc = page.locator(selector).first
            try:
                if await loc.count() > 0 and await loc.is_visible():
                    return state
            except Exception:
                continue
        await delay_ms(poll_interval_ms)
    return "timeout"


async def execute_search(page: Any, config: dict[str, Any]) -> None:
    timing = config["crawler"]["timing"]
    search_filters = config["search"]["search_filters"]
    auth = config.get("auth", {})
    await navigate_to_search(page, timing["page_load_timeout"])
    await ensure_search_ready(
        page,
        timeout_ms=int(timing["page_load_timeout"]),
        username=auth.get("username"),
        password=auth.get("password"),
    )
    await populate_search_filters(page, search_filters, timing["action_delay"])
    await run_search(page, timing["page_load_timeout"])
    ready_state = await wait_for_results_ready(
        page,
        timeout_ms=int(timing.get("results_ready_timeout", timing["page_load_timeout"])),
    )
    logger.info("Post-search readiness state: %s", ready_state)
    if ready_state == "needs_filters":
        raise RuntimeError("EMMA reports filters were not applied: 'Please use filters to narrow your search'")


async def find_security_url_by_cusip(
    page: Any,
    cusip: str,
    timeout_ms: int = 60000,
    username: str | None = None,
    password: str | None = None,
) -> str | None:
    await navigate_to_search(page, timeout_ms)
    await ensure_search_ready(page, timeout_ms=timeout_ms, username=username, password=password)
    cusip_field = await first_visible_locator(
        page,
        [
            "input[id*='txtCUSIP']",
            "input[id*='txtCusip']",
            "input[name*='CUSIP']",
            "input[placeholder*='CUSIP']",
        ],
    )
    if cusip_field is None:
        logger.warning("CUSIP field not found on search page")
        return None
    await cusip_field.fill(cusip)
    await run_search(page, timeout_ms)
    first_link = await first_visible_locator(
        page,
        [
            "table tbody tr td:nth-child(2) a",
            "table tbody tr a[href*='/Security/Details/']",
            "a[href*='/Security/Details/']",
        ],
    )
    if first_link is None:
        return None
    href = await first_link.get_attribute("href")
    if not href:
        return None
    return urljoin(page.url, href)
