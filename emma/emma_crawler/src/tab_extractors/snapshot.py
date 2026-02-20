from __future__ import annotations

import re
from typing import Any

from ..utils import is_valid_cusip, normalize_text, parse_currency


async def extract_snapshot(page: Any) -> dict[str, Any]:
    name = ""
    for selector in ("h1", "h2", ".security-header h1", ".security-header h2"):
        loc = page.locator(selector).first
        if await loc.count() > 0:
            candidate = normalize_text(await loc.inner_text())
            if candidate and candidate.lower() not in {"security details", "details"}:
                name = candidate
                break
    body_text = await page.inner_text("body")
    cleaned_lines = [normalize_text(line) for line in body_text.splitlines() if normalize_text(line)]

    cusip = ""
    principal = None
    maturity_date = ""
    dated_date = ""
    coupon_pct = ""
    closing_date = ""
    fiscal_year_end_date = ""
    initial_offering_price_yield = ""
    time_of_formal_award = ""
    time_of_first_execution = ""
    pending_key = ""
    for line in cleaned_lines:
        if line.endswith(":"):
            pending_key = line[:-1].strip().lower()
            continue
        if pending_key:
            if pending_key == "closing date" and not closing_date:
                closing_date = line
            elif pending_key == "fiscal year end date" and not fiscal_year_end_date:
                fiscal_year_end_date = line
            elif pending_key == "initial offering price/yield" and not initial_offering_price_yield:
                initial_offering_price_yield = line
            elif pending_key == "time of formal award" and not time_of_formal_award:
                time_of_formal_award = line
            elif pending_key == "time of first execution" and not time_of_first_execution:
                time_of_first_execution = line
            elif pending_key == "dated date" and not dated_date:
                dated_date = line
            elif pending_key == "maturity date" and not maturity_date:
                maturity_date = line
            elif pending_key == "coupon" and not coupon_pct:
                coupon_pct = line
            elif "principal amount at issuance" in pending_key and principal is None:
                principal = parse_currency(line)
            elif pending_key == "cusip" and not cusip:
                # Only accept short lines that look like a CUSIP, not long
                # descriptions that happen to follow a "CUSIP:" label.
                if len(line) <= 20:
                    candidate = re.sub(r"[^0-9A-Z]", "", line.upper())
                    if len(candidate) >= 9:
                        candidate = candidate[:9]
                        if is_valid_cusip(candidate):
                            cusip = candidate
            pending_key = ""

        if not cusip:
            match = re.search(r"CUSIP\s*[#*]?\s*:\s*([0-9A-Za-z\s\*\-]{6,15})", line)
            if match:
                candidate = re.sub(r"[^0-9A-Z]", "", match.group(1).upper())
                if len(candidate) >= 9:
                    candidate = candidate[:9]
                if is_valid_cusip(candidate):
                    cusip = candidate
        if principal is None and "Principal Amount" in line:
            principal = parse_currency(line.split(":")[-1])
        if not maturity_date and "Maturity Date" in line:
            maturity_date = normalize_text(line.split(":")[-1])
        if not dated_date and line.startswith("Dated Date"):
            dated_date = normalize_text(line.split(":")[-1])
        if not coupon_pct and line.startswith("Coupon"):
            coupon_pct = normalize_text(line.split(":")[-1])
        if not closing_date and line.startswith("Closing Date"):
            closing_date = normalize_text(line.split(":")[-1])
        if not fiscal_year_end_date and line.startswith("Fiscal Year End Date"):
            fiscal_year_end_date = normalize_text(line.split(":")[-1])
        if not initial_offering_price_yield and "Initial Offering Price/Yield" in line:
            initial_offering_price_yield = normalize_text(line.split(":")[-1])
        if not time_of_formal_award and "Time of Formal Award" in line:
            time_of_formal_award = normalize_text(line.split(":")[-1])
        if not time_of_first_execution and "Time of First Execution" in line:
            time_of_first_execution = normalize_text(line.split(":")[-1])

    if not cusip:
        match = re.search(r"CUSIP\s*[#*]?\s*:\s*([0-9A-Za-z\s\*\-]{6,15})", body_text)
        if match:
            candidate = re.sub(r"[^0-9A-Z]", "", match.group(1).upper())
            if len(candidate) >= 9:
                candidate = candidate[:9]
            if is_valid_cusip(candidate):
                cusip = candidate
    return {
        "security_name": name,
        "cusip": cusip,
        "principal_amount": principal,
        "maturity_date": maturity_date,
        "dated_date": dated_date,
        "coupon_pct": coupon_pct,
        "closing_date": closing_date,
        "fiscal_year_end_date": fiscal_year_end_date,
        "initial_offering_price_yield": initial_offering_price_yield,
        "time_of_formal_award": time_of_formal_award,
        "time_of_first_execution": time_of_first_execution,
    }
