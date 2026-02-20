from __future__ import annotations

import asyncio
import logging
import random
import re
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable

import yaml


logger = logging.getLogger("emma_crawler")


class SessionExpiredError(RuntimeError):
    pass


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def setup_logging(log_dir: Path, level: str, fmt: str) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    logfile = log_dir / "crawler.log"
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        handlers=[logging.FileHandler(logfile, encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )


def sanitize_filename(value: str) -> str:
    value = re.sub(r"[^\w.\- ]", "_", value).strip()
    return re.sub(r"\s+", "_", value)[:200] or "unknown"


def normalize_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def normalize_header(value: str | None) -> str:
    raw = normalize_text(value).lower()
    raw = raw.replace("%", " pct ").replace("$", " amount ")
    raw = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    return raw


def is_valid_cusip(value: str | None) -> bool:
    if not value:
        return False
    v = value.strip()
    # 9 alphanumeric chars; last char (check digit) is always 0-9.
    return re.fullmatch(r"[0-9A-Z]{8}[0-9]", v) is not None


def parse_currency(value: str | None) -> int | None:
    if value is None:
        return None
    text = value.strip()
    if not text or text == "-":
        return None
    text = text.replace("$", "").replace(",", "").strip()
    try:
        return int(float(text))
    except ValueError:
        return None


async def delay_ms(ms: int) -> None:
    await asyncio.sleep(ms / 1000.0)


async def retry_with_backoff(
    fn: Callable[[], Awaitable[Any]],
    max_retries: int = 3,
    base_delay_seconds: float = 5.0,
) -> Any:
    for attempt in range(max_retries):
        try:
            return await fn()
        except Exception:
            if attempt == max_retries - 1:
                raise
            jitter = random.uniform(0, 1)
            sleep_seconds = base_delay_seconds * (2**attempt) + jitter
            logger.warning("Retrying in %.1fs (%s/%s)", sleep_seconds, attempt + 1, max_retries)
            await asyncio.sleep(sleep_seconds)


async def first_visible_locator(page: Any, selectors: Iterable[str]) -> Any | None:
    for selector in selectors:
        locator = page.locator(selector).first
        if await locator.count() == 0:
            continue
        try:
            if await locator.is_visible():
                return locator
        except Exception:
            continue
    return None


async def is_session_healthy(page: Any) -> tuple[bool, str]:
    url = (page.url or "").lower()
    title = ((await page.title()) if hasattr(page, "title") else "").lower()
    if "403" in title or "forbidden" in title:
        return (False, "blocked")
    if "search/search.aspx" in url:
        has_search_button = await page.locator("text=Run Search").first.is_visible()
        return (has_search_button, "search_page")
    if "/security/details/" in url:
        has_header = await page.locator("text=/CUSIP\\s*:/").first.count() > 0
        return (has_header, "security_detail")
    if "search/results" in url or "search.aspx" in url:
        has_next = await page.locator("text=Next").first.count() > 0
        has_table = await page.locator("table").first.count() > 0
        return (has_next or has_table, "results_page")
    return (False, "unknown")


async def is_access_blocked(page: Any) -> bool:
    title = (await page.title()).lower()
    if "403" in title or "forbidden" in title:
        return True
    body = (await page.inner_text("body")).lower()
    indicators = [
        "403 forbidden",
        "access denied",
        "request blocked",
        "captcha",
        "attention required",
    ]
    return any(token in body for token in indicators)
