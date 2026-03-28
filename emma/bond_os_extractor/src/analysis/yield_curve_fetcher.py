"""AAA MMD municipal yield curve fetcher.

Fetches current AAA municipal benchmark yields by tenor from public sources.
Primary source: FMSbonds market yields page.
Fallback: manually-maintained reference curve updated periodically.

The fetcher caches results to disk so repeated calls within the same day
don't hit the network.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("bond_os_extractor.analysis.yield_curve_fetcher")

# Standard tenors in years
TENORS = [1, 2, 3, 5, 7, 10, 15, 20, 25, 30]

# Cache location (inside bond_os_extractor/data/)
_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "_market"
_CACHE_FILE = _CACHE_DIR / "aaa_mmd_cache.json"


# ---------------------------------------------------------------------------
# Reference curve (manually maintained fallback)
# ---------------------------------------------------------------------------
# Source: FMSbonds.com national AAA muni yields, March 2026 snapshot.
# Update these periodically or when the scraper successfully fetches live data.
REFERENCE_AAA_CURVE: dict[int, float] = {
    1: 2.85,
    2: 2.95,
    3: 3.10,
    5: 3.35,
    7: 3.60,
    10: 3.85,
    15: 4.15,
    20: 4.35,
    25: 4.42,
    30: 4.45,
}

# Additional rating curves (indicative, from market commentary)
REFERENCE_CURVES: dict[str, dict[int, float]] = {
    "AAA": REFERENCE_AAA_CURVE,
    "AA": {t: y + 0.20 for t, y in REFERENCE_AAA_CURVE.items()},
    "A": {t: y + 0.55 for t, y in REFERENCE_AAA_CURVE.items()},
    "BBB": {t: y + 1.30 for t, y in REFERENCE_AAA_CURVE.items()},
    "BB": {t: y + 3.00 for t, y in REFERENCE_AAA_CURVE.items()},
}

REFERENCE_DATE = "2026-03-27"


def _load_cache() -> dict[str, Any] | None:
    """Load cached yield data if fresh (same calendar day)."""
    if not _CACHE_FILE.exists():
        return None
    try:
        data = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
        cached_date = data.get("fetched_date", "")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if cached_date == today:
            logger.debug("Using cached AAA MMD curve from %s", cached_date)
            return data
        logger.debug("Cache expired (cached: %s, today: %s)", cached_date, today)
        return None
    except (json.JSONDecodeError, KeyError):
        return None


def _save_cache(data: dict[str, Any]) -> None:
    """Persist yield data to disk cache."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    _CACHE_FILE.write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


# ---------------------------------------------------------------------------
# FMSbonds scraper
# ---------------------------------------------------------------------------

def _scrape_fmsbonds() -> dict[str, Any] | None:
    """Attempt to scrape current AAA muni yields from FMSbonds.

    FMSbonds renders yield tables via JavaScript, so a simple HTTP GET
    may not capture the data.  We attempt to parse any embedded JSON
    or server-rendered table; if that fails, we return None and fall
    back to the reference curve.

    Returns a dict with keys: aaa_curve (tenor->yield), fetched_date, source.
    """
    try:
        import httpx
    except ImportError:
        logger.warning("httpx not installed — skipping FMSbonds fetch")
        return None

    url = "https://www.fmsbonds.com/market-yields/"
    try:
        resp = httpx.get(url, timeout=15, follow_redirects=True, headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        })
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        logger.warning("FMSbonds fetch failed: %s", exc)
        return None

    # Strategy 1: Look for embedded JSON data in script tags
    # Some sites embed yield data as JSON for chart libraries
    json_patterns = [
        r'var\s+yieldData\s*=\s*(\{[^;]+\});',
        r'var\s+marketData\s*=\s*(\{[^;]+\});',
        r'"yields"\s*:\s*(\[[^\]]+\])',
        r'"aaa"\s*:\s*(\[[^\]]+\])',
    ]
    for pattern in json_patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                raw = json.loads(match.group(1))
                curve = _parse_yield_json(raw)
                if curve and len(curve) >= 3:
                    logger.info("Parsed FMSbonds yields from embedded JSON")
                    return _build_result(curve, "fmsbonds_json")
            except (json.JSONDecodeError, ValueError):
                continue

    # Strategy 2: Parse HTML table rows
    # Look for table with yield percentages
    table_pattern = re.compile(
        r'<tr[^>]*>\s*<td[^>]*>([^<]*)</td>\s*'
        r'<td[^>]*>([\d.]+%?)</td>\s*'
        r'<td[^>]*>([\d.]+%?)</td>\s*'
        r'<td[^>]*>([\d.]+%?)</td>',
        re.DOTALL,
    )
    rows = table_pattern.findall(html)
    if rows:
        curve = _parse_table_rows(rows)
        if curve and len(curve) >= 3:
            logger.info("Parsed FMSbonds yields from HTML table")
            return _build_result(curve, "fmsbonds_table")

    # Strategy 3: Look for yield values near tenor keywords
    yield_hits: dict[int, float] = {}
    for tenor in TENORS:
        patterns = [
            rf'{tenor}\s*[-–]?\s*(?:yr|year|Y)\s*[:\s]*([\d.]+)\s*%',
            rf'(?:yr|year|Y)\s*{tenor}\s*[:\s]*([\d.]+)\s*%',
        ]
        for p in patterns:
            m = re.search(p, html, re.IGNORECASE)
            if m:
                yield_hits[tenor] = float(m.group(1))
                break
    if len(yield_hits) >= 3:
        logger.info("Parsed FMSbonds yields from text patterns")
        return _build_result(yield_hits, "fmsbonds_text")

    logger.info("Could not parse FMSbonds yield data — using reference curve")
    return None


def _parse_yield_json(raw: Any) -> dict[int, float] | None:
    """Attempt to extract tenor->yield mapping from parsed JSON."""
    curve: dict[int, float] = {}
    if isinstance(raw, dict):
        for key, val in raw.items():
            tenor = _extract_tenor(str(key))
            if tenor and isinstance(val, (int, float)):
                curve[tenor] = float(val)
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                tenor = _extract_tenor(
                    str(item.get("tenor", item.get("maturity", "")))
                )
                yld = item.get("yield", item.get("value"))
                if tenor and yld is not None:
                    curve[tenor] = float(yld)
    return curve if curve else None


def _parse_table_rows(
    rows: list[tuple[str, ...]],
) -> dict[int, float] | None:
    """Extract yields from HTML table row matches."""
    curve: dict[int, float] = {}
    for row in rows:
        label = row[0].strip()
        tenor = _extract_tenor(label)
        if tenor is None:
            continue
        # First numeric column is typically AAA
        for cell in row[1:]:
            val = cell.replace("%", "").strip()
            try:
                curve[tenor] = float(val)
                break
            except ValueError:
                continue
    return curve if curve else None


def _extract_tenor(text: str) -> int | None:
    """Pull a tenor in years from a label like '10 Year' or '10yr'."""
    m = re.search(r'(\d+)', text)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 40:
            return n
    return None


def _build_result(
    curve: dict[int, float], source: str
) -> dict[str, Any]:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "aaa_curve": {str(k): v for k, v in sorted(curve.items())},
        "fetched_date": today,
        "source": source,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_aaa_curve(force_refresh: bool = False) -> dict[str, Any]:
    """Get the current AAA MMD yield curve.

    Tries:
      1. Disk cache (if same day)
      2. FMSbonds live scrape
      3. Reference curve fallback

    Returns dict with:
      - aaa_curve: {tenor_str: yield_pct}  e.g. {"10": 3.85, "30": 4.45}
      - fetched_date: ISO date string
      - source: "cache" | "fmsbonds_*" | "reference"
    """
    if not force_refresh:
        cached = _load_cache()
        if cached:
            cached["source"] = "cache"
            return cached

    live = _scrape_fmsbonds()
    if live:
        _save_cache(live)
        return live

    # Fallback to reference curve
    return {
        "aaa_curve": {str(k): v for k, v in sorted(REFERENCE_AAA_CURVE.items())},
        "fetched_date": REFERENCE_DATE,
        "source": "reference",
    }


def get_yield_curves(
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Get full set of rating-tier yield curves.

    Returns:
      - curves: {rating: {tenor_str: yield_pct}}
      - aaa_source: source of base AAA curve
      - as_of: date string
    """
    base = fetch_aaa_curve(force_refresh=force_refresh)
    aaa = {int(k): v for k, v in base["aaa_curve"].items()}

    # Build rating curves from AAA base + spread table
    from .spread_table import DEFAULT_MUNI_SPREADS

    rating_groups = {
        "AAA": 0,
        "AA": DEFAULT_MUNI_SPREADS.get("AA", 20),
        "A": DEFAULT_MUNI_SPREADS.get("A", 62),
        "BBB": DEFAULT_MUNI_SPREADS.get("BBB", 145),
        "BB": DEFAULT_MUNI_SPREADS.get("BB", 340),
        "B": DEFAULT_MUNI_SPREADS.get("B", 800),
    }

    curves: dict[str, dict[str, float]] = {}
    for rating, spread_bps in rating_groups.items():
        spread_pct = spread_bps / 100.0
        curves[rating] = {
            str(t): round(y + spread_pct, 3)
            for t, y in sorted(aaa.items())
        }

    return {
        "curves": curves,
        "aaa_source": base["source"],
        "as_of": base["fetched_date"],
    }


def interpolate_yield(
    curve: dict[str, float] | dict[int, float],
    target_tenor: float,
) -> float | None:
    """Linearly interpolate a yield for a non-standard tenor.

    Args:
        curve: {tenor: yield} mapping
        target_tenor: desired tenor in years

    Returns interpolated yield, or None if out of range.
    """
    points = sorted(
        [(int(k), v) for k, v in curve.items()],
        key=lambda x: x[0],
    )
    if not points:
        return None

    # Exact match
    for t, y in points:
        if t == target_tenor:
            return y

    # Below range — flat extrapolation from shortest
    if target_tenor < points[0][0]:
        return points[0][1]

    # Above range — flat extrapolation from longest
    if target_tenor > points[-1][0]:
        return points[-1][1]

    # Linear interpolation
    for i in range(len(points) - 1):
        t0, y0 = points[i]
        t1, y1 = points[i + 1]
        if t0 <= target_tenor <= t1:
            frac = (target_tenor - t0) / (t1 - t0)
            return round(y0 + frac * (y1 - y0), 3)

    return None
