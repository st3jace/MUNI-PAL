from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import SecurityRecord
from .storage import append_summary_row, save_checkpoint, save_json
from .tab_extractors.disclosures import extract_disclosures
from .tab_extractors.interest_rate import extract_interest_rates
from .tab_extractors.ratings import extract_ratings
from .tab_extractors.snapshot import extract_snapshot
from .tab_extractors.trade_activity import extract_trade_activity
from .utils import (
    delay_ms,
    is_access_blocked,
    is_session_healthy,
    is_valid_cusip,
    logger,
    retry_with_backoff,
    sanitize_filename,
)


async def extract_security(page: Any, security: dict[str, Any], output_paths: dict[str, Path]) -> SecurityRecord:
    detail_url = security["detail_url"]
    await page.goto(detail_url, wait_until="domcontentloaded", timeout=90000)
    await page.wait_for_load_state("networkidle", timeout=90000)
    if await is_access_blocked(page):
        raise RuntimeError(f"Access blocked while loading detail page: {detail_url}")
    # Allow delayed hydration on EMMA detail pages.
    try:
        await page.locator("text=/CUSIP\\s*:/").first.wait_for(state="visible", timeout=15000)
    except Exception:
        pass
    healthy, page_type = await is_session_healthy(page)
    if not healthy:
        raise RuntimeError(f"Unexpected page after detail navigation: {page_type} ({page.url})")
    snapshot = await extract_snapshot(page)
    extracted_cusip = snapshot.get("cusip")
    cusip = extracted_cusip if is_valid_cusip(extracted_cusip) else (security.get("url_hash") or sanitize_filename(detail_url))
    # Fallback to Phase 2 row values when detail header parsing is sparse.
    if not snapshot.get("security_name"):
        snapshot["security_name"] = security.get("description", "")
    if not snapshot.get("principal_amount"):
        snapshot["principal_amount"] = security.get("principal_amount")
    if not snapshot.get("maturity_date"):
        snapshot["maturity_date"] = security.get("maturity_date", "")
    if not snapshot.get("dated_date"):
        snapshot["dated_date"] = security.get("dated_date", "")
    if not snapshot.get("coupon_pct"):
        snapshot["coupon_pct"] = security.get("coupon", "")
    if not snapshot.get("state"):
        snapshot["state"] = security.get("state", "")
    if not snapshot.get("cusip") and is_valid_cusip(cusip):
        snapshot["cusip"] = cusip

    record = SecurityRecord(cusip=cusip, emma_url=detail_url)
    record.snapshot = snapshot
    record.interest_rates = await extract_interest_rates(page)
    record.trades = await extract_trade_activity(page)
    record.ratings = await extract_ratings(page)
    record.disclosures = await extract_disclosures(page, output_paths["pdfs"] / cusip, cusip)
    record.extraction_status = {
        "snapshot": "success" if (record.snapshot and any(record.snapshot.values())) else "failed",
        "interest_rate": "success" if record.interest_rates else "empty",
        "trade_activity": "success" if record.trades else "empty",
        "ratings": "success" if record.ratings else "empty",
        "disclosures": "success" if record.disclosures else "empty",
    }
    return record


def _build_summary_row(record: SecurityRecord) -> dict[str, Any]:
    snapshot = record.snapshot or {}
    first_rating = (record.ratings or [{}])[0]
    first_rate = (record.interest_rates or [{}])[0]
    return {
        "cusip": record.cusip,
        "security_name": snapshot.get("security_name", ""),
        "state": snapshot.get("state", ""),
        "principal_amount": snapshot.get("principal_amount", ""),
        "coupon_pct": snapshot.get("coupon_pct", ""),
        "maturity_date": snapshot.get("maturity_date", ""),
        "dated_date": snapshot.get("dated_date", ""),
        "closing_date": snapshot.get("closing_date", ""),
        "interest_rate_current": first_rate.get("interest_rate", ""),
        "rate_type": first_rate.get("rate_type", ""),
        "source_of_repayment": snapshot.get("source_of_repayment", ""),
        "rating_fitch": first_rating.get("fitch", ""),
        "rating_kbra": first_rating.get("kbra", ""),
        "rating_moodys": first_rating.get("moodys", ""),
        "rating_sp": first_rating.get("sp", ""),
        "liquidity_facility": snapshot.get("liquidity_facility", ""),
        "provider_identity": snapshot.get("provider_identity", ""),
        "remarketing_agent": snapshot.get("remarketing_agent", ""),
        "num_trades": len(record.trades),
        "num_rate_resets": len(record.interest_rates),
        "num_disclosures": len(record.disclosures),
        "emma_url": record.emma_url,
        "crawl_timestamp": record.crawl_timestamp,
    }


async def process_queue(
    page: Any,
    queue: dict[str, Any],
    output_paths: dict[str, Path],
    timing: dict[str, Any],
    checkpoint: dict[str, Any],
    checkpoint_path: Path,
    max_securities: int | None = None,
    dry_run: bool = False,
) -> None:
    securities = queue.get("securities", [])
    if max_securities is not None:
        securities = securities[:max_securities]
    summary_csv = output_paths["data"] / "bonds_summary.csv"
    processed = set(checkpoint.get("processed_urls", []))

    for index, security in enumerate(securities, start=1):
        detail_url = security["detail_url"]
        if detail_url in processed:
            continue
        logger.info("Processing %s/%s: %s", index, len(securities), detail_url)
        try:
            if dry_run:
                processed.add(detail_url)
                checkpoint["processed_urls"] = sorted(processed)
                checkpoint["phase3_last_processed_url"] = detail_url
                save_checkpoint(checkpoint_path, checkpoint)
                continue

            async def _extract() -> SecurityRecord:
                return await extract_security(page, security, output_paths)

            record = await retry_with_backoff(_extract, max_retries=3, base_delay_seconds=5.0)
            save_json(output_paths["data"] / f"{record.cusip}.json", record.to_dict())
            append_summary_row(summary_csv, _build_summary_row(record))
            processed.add(detail_url)
            checkpoint["processed_urls"] = sorted(processed)
            checkpoint["phase3_last_processed_url"] = detail_url
            if "failed_urls" in checkpoint:
                failed = set(checkpoint.get("failed_urls", []))
                if detail_url in failed:
                    failed.remove(detail_url)
                    checkpoint["failed_urls"] = sorted(failed)
            if any(v != "success" for v in record.extraction_status.values()):
                partial = set(checkpoint.get("partial_urls", []))
                partial.add(detail_url)
                checkpoint["partial_urls"] = sorted(partial)
            elif "partial_urls" in checkpoint:
                partial = set(checkpoint.get("partial_urls", []))
                if detail_url in partial:
                    partial.remove(detail_url)
                    checkpoint["partial_urls"] = sorted(partial)
            save_checkpoint(checkpoint_path, checkpoint)
        except Exception as exc:
            logger.exception("Failed to process security %s: %s", detail_url, exc)
            failed = checkpoint.get("failed_urls", [])
            failed.append(detail_url)
            checkpoint["failed_urls"] = sorted(set(failed))
            save_checkpoint(checkpoint_path, checkpoint)
        await delay_ms(timing["between_securities"])
