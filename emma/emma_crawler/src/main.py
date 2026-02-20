from __future__ import annotations

import argparse
import asyncio
import copy
import os
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

from .results import collect_all_qualifying_securities, ensure_principal_sort_desc, set_results_per_page
from .search import execute_search, find_security_url_by_cusip
from .security_detail import process_queue
from .session_manager import recover_results_session
from .storage import (
    ensure_output_dirs,
    load_checkpoint,
    load_processing_queue,
    save_checkpoint,
    save_processing_queue,
)
from .utils import SessionExpiredError, load_yaml, logger, setup_logging


# ---------------------------------------------------------------------------
# Date chunking helpers
# ---------------------------------------------------------------------------

def _parse_date(value: str) -> datetime:
    """Parse a date string from EMMA config (MM/DD/YYYY or 'TODAY')."""
    if value.strip().upper() == "TODAY":
        return datetime.now()
    return datetime.strptime(value.strip(), "%m/%d/%Y")


def _format_date(dt: datetime) -> str:
    return dt.strftime("%-m/%-d/%Y") if os.name != "nt" else dt.strftime("%#m/%#d/%Y")


def generate_year_chunks(date_from: str, date_to: str) -> list[tuple[str, str]]:
    """Split a date range into calendar-year chunks, most recent year first."""
    start = _parse_date(date_from)
    end = _parse_date(date_to)
    if start >= end:
        return [(date_from, date_to)]
    chunks: list[tuple[str, str]] = []
    cursor = end
    while cursor > start:
        year_start = datetime(cursor.year, 1, 1)
        chunk_start = max(year_start, start)
        chunks.append((_format_date(chunk_start), _format_date(cursor)))
        cursor = datetime(cursor.year - 1, 12, 31)
    return chunks


def _get_existing_url_hashes(data_dir: Path) -> set[str]:
    """Scan output data dir for already-extracted security JSON files."""
    existing: set[str] = set()
    for json_file in data_dir.glob("*.json"):
        if json_file.name == "processing_queue.json":
            continue
        existing.add(json_file.stem)  # filename without extension = CUSIP or hash
    return existing


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="EMMA municipal bond crawler")
    parser.add_argument("--config", default="./config", help="Config directory")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--max-securities", type=int)
    parser.add_argument("--test-url")
    parser.add_argument("--test-cusip")
    parser.add_argument("--emma-username")
    parser.add_argument("--emma-password")
    parser.add_argument("--phase2-only", action="store_true")
    parser.add_argument("--phase3-only", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--retry-partial", action="store_true")
    parser.add_argument("--output-dir")
    parser.add_argument("--storage-state")
    parser.add_argument("--search-params", default="search_params.yaml",
                        help="Search params YAML filename inside config dir (default: search_params.yaml)")
    parser.add_argument("--date-from", help="Override closing_date_from (MM/DD/YYYY)")
    parser.add_argument("--date-to", help="Override closing_date_to (MM/DD/YYYY or TODAY)")
    parser.add_argument("--log-level")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_config(config_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    search_params_file = config_dir / args.search_params
    search_cfg = load_yaml(search_params_file)
    logger.info("Loaded search params from %s", search_params_file)
    # CLI date overrides
    if args.date_from:
        search_cfg.setdefault("search_filters", {}).setdefault("security_information", {})["closing_date_from"] = args.date_from
        logger.info("CLI override: closing_date_from = %s", args.date_from)
    if args.date_to:
        search_cfg.setdefault("search_filters", {}).setdefault("security_information", {})["closing_date_to"] = args.date_to
        logger.info("CLI override: closing_date_to = %s", args.date_to)
    crawler_cfg = load_yaml(config_dir / "crawler_settings.yaml")
    if args.log_level:
        crawler_cfg["logging"]["level"] = args.log_level
    username = args.emma_username or os.getenv("EMMA_USERNAME")
    password = args.emma_password or os.getenv("EMMA_PASSWORD")
    return {"search": search_cfg, "crawler": crawler_cfg, "auth": {"username": username, "password": password}}


# ---------------------------------------------------------------------------
# Single-chunk search → discover → extract
# ---------------------------------------------------------------------------

async def _run_search_chunk(
    page: Any,
    config: dict[str, Any],
    output_paths: dict[str, Path],
    timing: dict[str, Any],
    checkpoint: dict[str, Any],
    checkpoint_path: Path,
    phase2_only: bool,
    dry_run: bool,
    max_securities: int | None,
) -> str:
    """Run Phase 2 (discover) + Phase 3 (extract) for a single date-range chunk.

    Returns:
        'ok'            — chunk completed normally
        'needs_filters' — EMMA says too many results (caller should split further)
    """
    try:
        await execute_search(page, config)
    except RuntimeError as exc:
        if "Please use filters" in str(exc):
            return "needs_filters"
        raise

    await set_results_per_page(page, int(config["crawler"]["pagination"]["results_per_page"]))
    await ensure_principal_sort_desc(page, wait_ms=int(timing.get("action_delay", 2000)))

    # Reset Phase 2 pagination state so each chunk scans from page 1.
    chunk_checkpoint: dict[str, Any] = {
        "processed_urls": checkpoint.get("processed_urls", []),
        "failed_urls": checkpoint.get("failed_urls", []),
        "partial_urls": checkpoint.get("partial_urls", []),
    }
    try:
        queue_list = await collect_all_qualifying_securities(page, config, chunk_checkpoint, checkpoint_path)
    except SessionExpiredError:
        target_page = int(chunk_checkpoint.get("phase2_last_page_scanned", 0)) + 1
        recovered = await recover_results_session(page, config, target_page)
        if not recovered:
            raise
        queue_list = await collect_all_qualifying_securities(page, config, chunk_checkpoint, checkpoint_path)

    # Merge Phase 2 findings into the master checkpoint.
    checkpoint["processed_urls"] = chunk_checkpoint.get("processed_urls", [])
    checkpoint["failed_urls"] = chunk_checkpoint.get("failed_urls", [])
    checkpoint["partial_urls"] = chunk_checkpoint.get("partial_urls", [])

    save_processing_queue(output_paths["data"], queue_list)
    save_checkpoint(checkpoint_path, checkpoint)

    if not queue_list:
        logger.info("No qualifying securities in this chunk")
        return "ok"

    logger.info("Chunk discovered %s qualifying securities", len(queue_list))

    if phase2_only or dry_run:
        return "ok"

    # Phase 3: extract (checkpoint deduplication skips already-processed URLs)
    queue = {"securities": queue_list}
    await process_queue(
        page,
        queue,
        output_paths,
        timing,
        checkpoint,
        checkpoint_path,
        max_securities=max_securities,
        dry_run=dry_run,
    )
    return "ok"


# ---------------------------------------------------------------------------
# Main run loop with auto-chunking
# ---------------------------------------------------------------------------

async def run(args: argparse.Namespace) -> None:
    project_root = Path(__file__).resolve().parents[1]
    config_dir = (project_root / args.config).resolve() if not Path(args.config).is_absolute() else Path(args.config)
    config = load_config(config_dir, args)
    output_root = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else (project_root / "output")
    )
    output_paths = ensure_output_dirs(output_root)
    checkpoint_path = output_root / "checkpoint.json"
    storage_state_path = Path(args.storage_state).resolve() if args.storage_state else (output_root / "emma_storage_state.json")

    setup_logging(
        output_paths["logs"],
        config["crawler"]["logging"]["level"],
        config["crawler"]["logging"]["format"],
    )
    checkpoint = load_checkpoint(checkpoint_path) if (args.resume and checkpoint_path.exists()) else {}

    default_headless = bool(config["crawler"]["browser"].get("headless", True))
    headless = default_headless
    if args.visible:
        headless = False
    if args.headless:
        headless = True
    browser_cfg = config["crawler"]["browser"]
    timing = config["crawler"]["timing"]

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context_kwargs: dict[str, Any] = {
            "user_agent": browser_cfg["user_agent"],
            "viewport": {
                "width": int(browser_cfg["viewport_width"]),
                "height": int(browser_cfg["viewport_height"]),
            },
            "accept_downloads": True,
        }
        if storage_state_path.exists():
            context_kwargs["storage_state"] = str(storage_state_path)
        context = await browser.new_context(**context_kwargs)
        page = await context.new_page()
        page.set_default_timeout(int(timing["page_load_timeout"]))

        # --- Single-security test mode (unchanged) ---
        if args.test_url or args.test_cusip:
            test_url = args.test_url
            if not test_url and args.test_cusip:
                test_url = await find_security_url_by_cusip(
                    page,
                    args.test_cusip,
                    timeout_ms=int(timing["page_load_timeout"]),
                    username=config["auth"].get("username"),
                    password=config["auth"].get("password"),
                )
                if not test_url:
                    raise RuntimeError(f"No security URL found for CUSIP {args.test_cusip}")
            queue = {"securities": [{"detail_url": test_url, "url_hash": test_url.split("/")[-1]}]}
            await process_queue(
                page, queue, output_paths, timing, checkpoint, checkpoint_path,
                max_securities=1, dry_run=args.dry_run,
            )
            await context.storage_state(path=str(storage_state_path))
            await browser.close()
            return

        # --- Phase 3 only / retry modes (no search needed) ---
        if args.phase3_only or args.retry_failed or args.retry_partial:
            queue = load_processing_queue(output_paths["data"])
            if not queue:
                raise RuntimeError("No processing queue available. Run without --phase3-only first.")
            if args.retry_failed:
                failed_urls = set(checkpoint.get("failed_urls", []))
                queue = {"securities": [s for s in queue.get("securities", []) if s.get("detail_url") in failed_urls]}
                checkpoint["failed_urls"] = []
            elif args.retry_partial:
                partial_urls = set(checkpoint.get("partial_urls", []))
                queue = {"securities": [s for s in queue.get("securities", []) if s.get("detail_url") in partial_urls]}
                checkpoint["partial_urls"] = []
            await process_queue(
                page, queue, output_paths, timing, checkpoint, checkpoint_path,
                max_securities=args.max_securities, dry_run=args.dry_run,
            )
            await context.storage_state(path=str(storage_state_path))
            await browser.close()
            return

        # --- Normal mode: search → discover → extract (with auto-chunking) ---
        security_info = config["search"].get("search_filters", {}).get("security_information", {})
        date_from = security_info.get("closing_date_from", "1/1/2020")
        date_to = security_info.get("closing_date_to", "TODAY")

        # Build a queue of date-range chunks to process.
        # Start with the full range; if EMMA says "too many results",
        # split into year-sized chunks automatically.
        chunks: deque[tuple[str, str]] = deque()
        chunks.append((date_from, date_to))
        total_chunks_completed = 0

        while chunks:
            chunk_from, chunk_to = chunks.popleft()
            logger.info(
                "── Chunk %s: %s → %s ──────────────────────────",
                total_chunks_completed + 1, chunk_from, chunk_to,
            )

            # Apply this chunk's dates to a copy of the config.
            chunk_config = copy.deepcopy(config)
            chunk_config["search"]["search_filters"]["security_information"]["closing_date_from"] = chunk_from
            chunk_config["search"]["search_filters"]["security_information"]["closing_date_to"] = chunk_to

            result = await _run_search_chunk(
                page, chunk_config, output_paths, timing,
                checkpoint, checkpoint_path,
                phase2_only=args.phase2_only,
                dry_run=args.dry_run,
                max_securities=args.max_securities,
            )

            if result == "needs_filters":
                # Too many results — split into year-sized sub-chunks.
                year_chunks = generate_year_chunks(chunk_from, chunk_to)
                if len(year_chunks) <= 1:
                    # Already a single year (or less) and still too broad;
                    # split into half-year chunks as a last resort.
                    mid = _parse_date(chunk_from) + (
                        _parse_date(chunk_to) - _parse_date(chunk_from)
                    ) / 2
                    mid_str = _format_date(mid)
                    if mid_str != chunk_from and mid_str != chunk_to:
                        year_chunks = [(mid_str, chunk_to), (chunk_from, mid_str)]
                        logger.info(
                            "Single year still too broad; splitting into half-year chunks: %s",
                            year_chunks,
                        )
                    else:
                        logger.error(
                            "Cannot narrow date range further (%s → %s). "
                            "Add keyword filters to reduce result count.",
                            chunk_from, chunk_to,
                        )
                        continue
                else:
                    logger.info(
                        "Too many results for %s → %s; auto-splitting into %s yearly chunks",
                        chunk_from, chunk_to, len(year_chunks),
                    )
                # Prepend sub-chunks so they run in most-recent-first order.
                for sub in reversed(year_chunks):
                    chunks.appendleft(sub)
                continue

            total_chunks_completed += 1
            save_checkpoint(checkpoint_path, checkpoint)

        logger.info(
            "All chunks complete. Processed %s chunks total. "
            "%s securities extracted overall.",
            total_chunks_completed,
            len(checkpoint.get("processed_urls", [])),
        )

        await context.storage_state(path=str(storage_state_path))
        await browser.close()


def main() -> None:
    args = parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
