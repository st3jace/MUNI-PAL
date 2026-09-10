#!/usr/bin/env python3
"""Ingest the Phoenix IDA published bond-transaction list (PDF) into a sourcing CSV.

Source: https://phoenixida.com/bond-financing-process/bond-transactions/
        -> "download full list of bond transactions" (PDF). Public, issuer-published, not EMMA.

Every row is a CLOSED conduit transaction (Q3 = yes by construction). The project name is the
property or borrower; the obligated person / sponsor is resolved in the next step (Clay or the
state corporation registry). Nothing here decides eligibility; it records what the issuer published.

Usage:
  python ingest_phoenix_ida.py <pdf> <out.csv>
"""
from __future__ import annotations

import csv
import re
import sys
from datetime import date
from pathlib import Path

import fitz  # PyMuPDF

SOURCE_URL = "https://phoenixida.com/bond-financing-process/bond-transactions/"
ISSUER = "Phoenix Industrial Development Authority"

DATE_RE = re.compile(r"^(Jan|Feb|Mar|Apr|May|June?|July?|Aug|Sept?|Oct|Nov|Dec)[a-z]*-(\d{2})(?:\s+\d+)?$", re.I)
AMOUNT_RE = re.compile(r"^\$\s*([\d,]+)\s*$")

SECTOR_HINTS = [
    (re.compile(r"apartment|terrace|village|residences|heights|towers|farms|crossing|commons|senior|assisted|living|homes|place|park|court|manor|lofts|gardens|estates|villas|pointe|square|plaza", re.I), "housing"),
    (re.compile(r"school|academy|charter|prep|basis|great hearts|legacy traditional|arts|university|college|education", re.I), "education"),
    (re.compile(r"hospital|health|medical|rehab|clinic|care|mayo|banner|hospice", re.I), "healthcare"),
    (re.compile(r"goodwill|industrial|manufactur|recycl|waste|energy|solar|llc\)|retail|store|center", re.I), "industrial_or_other"),
]


def sector_guess(name: str) -> str:
    for rx, s in SECTOR_HINTS:
        if rx.search(name):
            return s
    return "unknown"


def parse(pdf: Path) -> list[dict]:
    lines: list[str] = []
    for page in fitz.open(pdf):
        lines += [l.strip() for l in page.get_text().splitlines()]
    lines = [l for l in lines if l and l.lower() != "www.phoenixida.com"]
    rows, i = [], 0
    while i < len(lines):
        m = DATE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        mon, yy = m.group(1), m.group(2)
        # collect until an amount line; project = first line, address = the rest joined
        j = i + 1
        block = []
        while j < len(lines) and not AMOUNT_RE.match(lines[j]) and not DATE_RE.match(lines[j]):
            block.append(lines[j])
            j += 1
        amount = ""
        if j < len(lines) and AMOUNT_RE.match(lines[j]):
            amount = AMOUNT_RE.match(lines[j]).group(1).replace(",", "")
            j += 1
        if block:
            project = block[0]
            address = " ".join(block[1:]).strip()
            state = ""
            sm = re.search(r",\s*([A-Z]{2})\s*$", address)
            if sm:
                state = sm.group(1)
            rows.append({
                "issuer": ISSUER,
                "closing_month": f"{mon[:3].title()}-20{yy}",
                "project": project,
                "address": address,
                "state": state or "AZ",
                "amount_financed": amount,
                "sector_guess": sector_guess(project),
                "closed": "Y",
                "entity_type": "unknown_until_sponsor_resolved",
                "sponsor": "",
                "source": "issuer-published transaction list",
                "source_url": SOURCE_URL,
                "retrieved": date.today().isoformat(),
            })
        i = j
    return rows


def main() -> None:
    pdf, out = Path(sys.argv[1]), Path(sys.argv[2])
    rows = parse(pdf)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    by = {}
    for r in rows:
        by[r["sector_guess"]] = by.get(r["sector_guess"], 0) + 1
    print(f"{len(rows)} rows -> {out}")
    print("sector_guess:", by)
    years = sorted({r["closing_month"][-4:] for r in rows})
    print("years:", years[0], "to", years[-1])


if __name__ == "__main__":
    main()
