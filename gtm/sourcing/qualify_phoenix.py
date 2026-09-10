#!/usr/bin/env python3
"""Qualify the Phoenix IDA sponsor rows and merge them into the prospect file.

Rules (Hermosillo 2026-09-09 §1.2, applied mechanically from the research columns):
  Q1  municipal_or_public            -> holds.csv, reason=municipal (nurture file, never prospect)
  Q3  closed                          -> all rows: closed by construction (issuer transaction list)
  Q6  new_issuance_2025_2026 == Y     -> holds.csv, reason=q6_new_issuance (re-check after it closes)
      sponsor unknown                 -> holds.csv, reason=sponsor_unknown
      defunct / bondholder loss       -> holds.csv, reason=defunct
  Q8  healthcare                      -> not in this batch (held upstream)
Everything else becomes ONE prospect row per sponsor (deals rolled up), source cited.

Usage: python3 qualify_phoenix.py <phoenix-sponsors.csv> <prospects.csv> <holds.csv>
"""
from __future__ import annotations

import csv
import sys
from collections import OrderedDict
from datetime import date

DEFUNCT = {"Vieste"}
# Contacts Clay returned today (unfiltered search; no title filter available). Not the CFO yet.
CLAY_CONTACTS = {
    "nationalchurchresidences.org": "Jill Bowers, Senior Asset Manager (asset mgmt owns the calendar); Susan DiMickele, President & CEO",
    "reliantgroup.com": "Sanj Kakar, Chief Acquisitions Officer (not the buyer; find controller)",
}
PRIORITY = {  # icp_fit by hand, from the research notes
    "goodwillaz.org": "high", "cplc.org": "high", "nationalchurchresidences.org": "high",
    "pacificap.com": "medium", "umom.org": "medium", "reliantgroup.com": "medium",
    "solterraseniorliving.com": "low", "fhrtucson.org": "low", "rebuildamericainc.com": "low",
    "girlscoutsaz.org": "low", "hampstead.com": "low", "dunnedwards.com": "low", "gore.com": "low", "accel.org": "low",
}
CAUTION = {"solterraseniorliving.com": "unverified 2025 reviews allege payroll/vendor trouble; verify before any touch"}

PROSPECT_FIELDS = ["name", "org", "role", "segment", "icp_fit", "entity_type", "has_issued", "disclosure_live",
                   "channel", "contact", "last_touch", "touches", "status", "source", "notes"]


def main() -> None:
    src, prospects_path, holds_path = sys.argv[1:4]
    rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
    today = date.today().isoformat()

    holds, by_sponsor = [], OrderedDict()
    for r in rows:
        sponsor = r["sponsor"].split("(")[0].strip()
        reason = ""
        if r["entity_type"] == "municipal_or_public":
            reason = "municipal"
        elif r["new_issuance_2025_2026"].strip().upper() == "Y":
            reason = "q6_new_issuance_2025_2026"
        elif any(d in sponsor for d in DEFUNCT):
            reason = "defunct"
        elif r["sponsor_domain"] in ("", "unknown") or sponsor.lower().startswith("unknown"):
            reason = "sponsor_unknown"
        if reason:
            holds.append({"closing_month": r["closing_month"], "project": r["project"], "sponsor": sponsor,
                          "reason": reason, "recheck": "after the new deal closes" if reason.startswith("q6") else "",
                          "source_url": r["source_url"], "notes": r["notes"][:200]})
            continue
        key = r["sponsor_domain"]
        by_sponsor.setdefault(key, {"sponsor": sponsor, "entity_type": r["entity_type"], "deals": [], "sector": r["sector"], "url": r["source_url"], "notes": r["notes"]})
        by_sponsor[key]["deals"].append(f"{r['project'].strip()} ({r['closing_month']})")

    existing = list(csv.DictReader(open(prospects_path, encoding="utf-8-sig")))
    existing_orgs = {e["org"].lower() for e in existing}
    added = []
    for domain, s in by_sponsor.items():
        if s["sponsor"].lower() in existing_orgs:
            continue
        old = all(int(d[-5:-1]) <= 2013 for d in s["deals"])
        added.append({
            "name": "TBD", "org": s["sponsor"], "role": "CFO / controller / asset manager (find in Clay by title)",
            "segment": "cold", "icp_fit": PRIORITY.get(domain, "low"),
            "entity_type": "obligated_person" if s["entity_type"] != "unknown" else "unclear",
            "has_issued": "Y", "disclosure_live": "unknown",
            "channel": "email", "contact": CLAY_CONTACTS.get(domain, f"domain: {domain}"),
            "last_touch": "", "touches": "0", "status": "new",
            "source": "Phoenix IDA published transaction list + public sponsor research 2026-09-10 (no EMMA)",
            "notes": ("Deals: " + "; ".join(s["deals"]) + f". Sector: {s['sector']}. Entity: {s['entity_type']}. Source: {s['url']}."
                      + (" OLD DEALS (<=2013): verify bonds still outstanding before any touch." if old else "")
                      + (f" CAUTION: {CAUTION[domain]}" if domain in CAUTION else "")),
        })

    with open(prospects_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PROSPECT_FIELDS)
        w.writeheader()
        for e in existing:
            w.writerow({k: e.get(k, "") for k in PROSPECT_FIELDS})
        for a in added:
            w.writerow(a)
    with open(holds_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["closing_month", "project", "sponsor", "reason", "recheck", "source_url", "notes"])
        w.writeheader()
        w.writerows(holds)

    print(f"prospects: {len(existing)} existing + {len(added)} added = {len(existing) + len(added)}")
    for a in added:
        print(f"  + {a['org']:45} {a['icp_fit']:6} {a['entity_type']}")
    print(f"holds: {len(holds)}")
    for h in holds:
        print(f"  - {h['sponsor'][:40]:40} {h['reason']}")


if __name__ == "__main__":
    main()
