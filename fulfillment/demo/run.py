#!/usr/bin/env python3
"""Obligation Register runner (demo).

Inputs
  documents/            the client's closing documents (here: SYNTHETIC excerpts)
  approved-inputs.csv   obligations, clauses and dates AS APPROVED by the client's own
                        counsel / dissemination agent. This is the only source of register rows.
  vault/                evidence files the client dropped

Outputs (output/)
  register.csv          one row per obligation, fixed status vocabulary
  calendar.csv          one row per approved due date, next 24 months
  vault-index.csv       every evidence file, labeled and bound to an obligation where a pattern matches
  gaps.md               observational gap list (file present / absent vs an approved undertaking)
  refusal-log.md        every item that needs a professional determination
  candidates.csv        clauses found in the documents that are NOT on the approved list (for counsel)
  register.html         one-page human view of all of the above

Rules (Arthur ruling 2026-09-09, post-close letter 4.6 / 4.8 / 3.5; fifth status code REJECTED)
  - Status vocabulary is exactly four values: filed / not filed / evidence missing / not testable.
    A status only ever attaches to a row that has written professional input behind it.
  - Dates come only from approved-inputs.csv. Nothing is computed from a formula.
  - Blank date + a frequency of event-driven / conditional / on request / standing -> not testable
    (mechanical: no event or request was supplied, so there is nothing to compare).
  - A row whose frequency implies a date but has no approved date is NOT an obligation row yet.
    It goes to the Open Items list ("items awaiting input"), with request date and recipient.
  - Duty language found in the documents but not on the approved list also goes to Open Items,
    as a yes/no request to counsel. Never entered on its own.
  - The runner never characterises a row as needing a professional. That would itself be a
    determination. The refusal log records only judgment QUESTIONS asked of us (see ask.py).
  - The runner never says "compliant". It never decides which clause controls.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import re
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATUSES = ("filed", "not filed", "evidence missing", "not testable")
NO_DATE_FREQ = {"event-driven", "conditional", "on request", "standing"}


def read_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(p: Path, rows: list[dict], fields: list[str]) -> None:
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def period_tokens(d: date, fy_end_month: int = 12) -> dict:
    """Mechanical labels for an evidence pattern. A due date in year Y for an annual item
    refers to fiscal year Y-1 (the report is about the year that just ended)."""
    q = (d.month - 1) // 3 + 1
    # the quarter a due date belongs to is the quarter that ended before it
    prev_q = q - 1 if q > 1 else 4
    prev_q_year = d.year if q > 1 else d.year - 1
    return {"fy": str(d.year - 1), "year": str(d.year), "period": f"{prev_q_year}Q{prev_q}"}


def evidence_for(pattern: str, d: date, vault_files: set[str]) -> str | None:
    if not pattern:
        return None
    name = pattern.format(**period_tokens(d))
    for f in vault_files:
        if f.startswith(name):
            return f
    return None


def build(asof: date, horizon_months: int = 24) -> dict:
    approved = read_csv(ROOT / "approved-inputs.csv")
    vault_dir = ROOT / "vault"
    vault_files = {p.name for p in vault_dir.iterdir() if p.is_file()} if vault_dir.exists() else set()
    horizon = asof + timedelta(days=30 * horizon_months)

    register, calendar, open_items, gaps = [], [], [], []
    bound_evidence: dict[str, str] = {}

    for a in approved:
        dates = [date.fromisoformat(x) for x in a["due_dates_approved"].split(";") if x.strip()]
        rule = a["due_rule_text_verbatim"]
        freq = a["frequency"].strip().lower()
        per_date = []
        if not dates:
            if freq in NO_DATE_FREQ:
                status = "not testable"
                note = f"no calendar date ({freq}); no event or request supplied in the drop"
            else:
                # Not an obligation row yet. Written input is missing. Open Items, not the register.
                open_items.append({
                    "requested_on": asof.isoformat(), "requested_from": a["approved_by"],
                    "item": f"{a['obligation_id']} {a['obligation']}",
                    "source_document": a["source_document"], "clause": a["clause"],
                    "what_was_asked": f"Frequency is '{a['frequency']}' but no due date was supplied. Please supply the date(s) in writing.",
                })
                continue
            next_due = ""
        else:
            for d in dates:
                ev = evidence_for(a["evidence_pattern"], d, vault_files)
                if ev:
                    st = "filed"
                    bound_evidence[ev] = a["obligation_id"]
                elif d <= asof:
                    st = "evidence missing"
                    gaps.append((a["obligation_id"], a["obligation"], d.isoformat(), a["clause"], a["source_document"],
                                 a["evidence_pattern"].format(**period_tokens(d))))
                else:
                    st = "not filed"
                per_date.append((d, st, ev or ""))
                if asof - timedelta(days=365) <= d <= horizon:
                    calendar.append({
                        "due_date": d.isoformat(), "obligation_id": a["obligation_id"], "obligation": a["obligation"],
                        "recipient": a["recipient"], "clause": a["clause"], "source_document": a["source_document"],
                        "status": st, "evidence_file": ev or "", "timing": "past" if d <= asof else "future",
                    })
            past = [x for x in per_date if x[0] <= asof]
            future = [x for x in per_date if x[0] > asof]
            if past:
                missing = [x for x in past if x[1] == "evidence missing"]
                if missing:
                    status = "evidence missing"
                    note = "no evidence for " + ", ".join(x[0].isoformat() for x in missing)
                else:
                    status = past[-1][1]
                    note = f"last due {past[-1][0].isoformat()}"
            else:
                status = "not filed"
                note = "not yet due"
            next_due = future[0][0].isoformat() if future else ""

        register.append({
            "obligation_id": a["obligation_id"], "obligation": a["obligation"],
            "source_document": a["source_document"], "clause": a["clause"], "recipient": a["recipient"],
            "frequency": a["frequency"], "due_rule_text_verbatim": rule,
            "next_due": next_due, "status": status, "status_note": note,
            "evidence_files": "; ".join(x[2] for x in per_date if x[2]),
            "approved_by": a["approved_by"], "approval_ref": a["approval_ref"],
        })

    vault_index = []
    for f in sorted(vault_files):
        first = (vault_dir / f).read_text(encoding="utf-8", errors="replace").splitlines()[:1]
        vault_index.append({"file": f, "label": first[0] if first else "", "bound_to": bound_evidence.get(f, "UNBOUND")})
    calendar.sort(key=lambda r: r["due_date"])

    candidates = find_candidates(approved)
    counsel = next((a["approved_by"] for a in approved if "counsel" in a["approved_by"].lower()), "bond counsel")
    for c in candidates:
        open_items.append({
            "requested_on": asof.isoformat(), "requested_from": counsel,
            "item": f"{c['source_document']} {c['clause']}",
            "source_document": c["source_document"], "clause": c["clause"],
            "what_was_asked": "This clause carries duty language and is not on the approved list. Is it an obligation of the Borrower to be entered? Yes / no in writing.",
        })
    open_items.sort(key=lambda x: x["requested_on"])
    return {"register": register, "calendar": calendar, "vault_index": vault_index,
            "gaps": gaps, "open_items": open_items, "candidates": candidates, "asof": asof.isoformat()}


SECTION_RE = re.compile(r"^## (Section [^.]+\.?[^\n]*)$", re.M)
DUTY_RE = re.compile(r"\b(shall (deliver|provide|give|furnish|notify|retain|obtain|cause|send|maintain|pay))\b", re.I)


def find_candidates(approved: list[dict]) -> list[dict]:
    """Clauses in documents/ with a duty verb that are NOT on the approved list.
    These go to counsel. They never enter the register on their own."""
    approved_keys = {(a["source_document"], a["clause"].split(".")[0].strip()) for a in approved}
    approved_clauses = {(a["source_document"], a["clause"]) for a in approved}
    out = []
    for doc in sorted((ROOT / "documents").glob("*.md")):
        text = doc.read_text(encoding="utf-8")
        parts = SECTION_RE.split(text)
        # parts: [pre, heading1, body1, heading2, body2, ...]
        for i in range(1, len(parts) - 1, 2):
            heading, body = parts[i].strip(), parts[i + 1]
            sec = heading.split(".")[0] + "." + heading.split(".")[1] if heading.count(".") >= 1 else heading
            sec = re.match(r"Section [0-9A-Za-z.()]+", heading).group(0).rstrip(".") if re.match(r"Section [0-9A-Za-z.()]+", heading) else heading
            if not DUTY_RE.search(body):
                continue
            if any(sec.startswith(c.rstrip(".")) or c.startswith(sec) for (d, c) in approved_clauses if d == doc.name):
                continue
            m = DUTY_RE.search(body)
            snippet = body.strip().replace("\n", " ")
            out.append({"source_document": doc.name, "clause": sec, "heading": heading,
                        "duty_phrase": m.group(0), "snippet": snippet[:220]})
    return out


def render_html(r: dict) -> str:
    def esc(x):
        return html.escape(str(x))

    def table(rows, cols):
        if not rows:
            return "<p class='muted'>none</p>"
        h = "<table><thead><tr>" + "".join(f"<th>{esc(c)}</th>" for c in cols) + "</tr></thead><tbody>"
        for row in rows:
            h += "<tr>" + "".join(f"<td class='s-{esc(row.get('status','')).replace(' ','-')}'>{esc(row.get(c,''))}</td>" for c in cols) + "</tr>"
        return h + "</tbody></table>"

    counts = {s: sum(1 for x in r["register"] if x["status"] == s) for s in STATUSES}
    css = """
    :root{--bg:#fbfaf7;--fg:#1e1e1e;--muted:#6b6b6b;--line:#ddd8cf;--ok:#1f6f43;--warn:#9a5b00;--bad:#9b2226;--hold:#4a4a8a}
    body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,Segoe UI,Roboto,sans-serif;margin:0;padding:24px;max-width:1200px}
    h1{font-size:22px;margin:0 0 4px}h2{font-size:16px;margin:28px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}
    .muted{color:var(--muted)} .banner{background:#fff3cd;border:1px solid #e6c85a;padding:8px 12px;border-radius:6px;margin:12px 0}
    .never{background:#fff;border:1px solid var(--line);padding:10px 14px;border-radius:6px;margin:12px 0}
    table{border-collapse:collapse;width:100%;font-size:13px}th,td{border:1px solid var(--line);padding:5px 7px;vertical-align:top;text-align:left}
    th{background:#f1ede4;position:sticky;top:0}
    .kpi{display:flex;gap:12px;flex-wrap:wrap;margin:10px 0}.kpi div{border:1px solid var(--line);border-radius:6px;padding:8px 12px;background:#fff;min-width:150px}
    .kpi b{display:block;font-size:20px}
    .s-filed{color:var(--ok)} .s-evidence-missing{color:var(--bad);font-weight:600} .s-not-filed{color:var(--warn)}
    .s-not-testable{color:var(--muted)}
    .wrap{overflow-x:auto}
    """
    reg_cols = ["obligation_id", "obligation", "source_document", "clause", "recipient", "frequency", "next_due", "status", "status_note", "evidence_files"]
    cal_cols = ["due_date", "timing", "obligation_id", "obligation", "recipient", "clause", "status", "evidence_file"]
    gaps_rows = [{"obligation_id": g[0], "obligation": g[1], "due_date": g[2], "clause": g[3], "source_document": g[4], "expected_file": g[5]} for g in r["gaps"]]
    open_cols = ["requested_on", "requested_from", "item", "source_document", "clause", "what_was_asked"]
    refusal_md = (ROOT / "output" / "refusal-log.md")
    refusal_lines = [l[2:] for l in refusal_md.read_text(encoding="utf-8").splitlines() if l.startswith("- ")] if refusal_md.exists() else []
    refusal_html = "<ul>" + "".join(f"<li>{esc(l)}</li>" for l in refusal_lines) + "</ul>" if refusal_lines else "<p class='muted'>none asked yet</p>"
    kpis = "".join(f"<div><b>{counts[s]}</b>{esc(s)}</div>" for s in STATUSES) + f"<div><b>{len(r['open_items'])}</b>items awaiting input</div>"
    return f"""<!doctype html><meta charset='utf-8'><title>Obligation Register — SYN-HSG-AZ-2025</title><style>{css}</style>
<h1>Obligation Register — Saguaro Commons Apartments, LP — Series 2025</h1>
<div class='muted'>As of {esc(r['asof'])} · {len(r['register'])} approved obligations · {len(r['vault_index'])} evidence files · SYNTHETIC deal SYN-HSG-AZ-2025</div>
<div class='banner'><b>Synthetic demonstration.</b> Every name, amount and date is invented. The method is real; the deal is not.</div>
<div class='never'><b>What this register never does.</b> It never files. It never says "compliant". It never decides which clause controls, interprets a deadline formula, or decides whether an obligation applies. Every row below has written input from the client's own counsel or dissemination agent behind it (see <code>approval-2026-09-08.md</code>). Dates come only from that input. A row without the input it needs is not a row yet. It sits in "items awaiting input" below. Judgment questions put to us are logged, sent on, and left unanswered.</div>
<div class='kpi'>{kpis}</div>
<h2>1. Register</h2><div class='wrap'>{table(r['register'], reg_cols)}</div>
<h2>2. Calendar (past 12 months and next 24)</h2><div class='wrap'>{table(r['calendar'], cal_cols)}</div>
<h2>3. Gap list (observational only)</h2><p class='muted'>An approved undertaking names a deliverable; no file is present in the vault for it. No remediation sequence, no impact ranking.</p><div class='wrap'>{table(gaps_rows, list(gaps_rows[0].keys()) if gaps_rows else [])}</div>
<h2>4. Items awaiting input</h2><p class='muted'>What we have asked for in writing and have not received. Sorted by request date only. This list says what we asked; it says nothing about the obligation.</p><div class='wrap'>{table(r['open_items'], open_cols)}</div>
<h2>5. Refusal log</h2><p class='muted'>Every judgment question put to us: the question, the date, and where it was routed. We do not answer them.</p>{refusal_html}
<h2>6. Evidence vault index</h2><div class='wrap'>{table(r['vault_index'], ['file', 'label', 'bound_to'])}</div>
<h2>Legend</h2><p class='muted'>Four statuses. No fifth. No score, rating, colour ranking, or field that records our assessment of anything.</p><ul>
<li><b>filed</b>: an evidence file matching the approved undertaking and period is in the vault.</li>
<li><b>not filed</b>: due date is in the future. Nothing is expected yet.</li>
<li><b>evidence missing</b>: due date has passed and no matching evidence file is in the vault. An observation about the supplied file set, not about anything outside it.</li>
<li><b>not testable</b>: the undertaking has no calendar date (event-driven, conditional, on request, standing) and no event or request was supplied.</li>
</ul>
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=date.today().isoformat())
    ap.add_argument("--out", default=str(ROOT / "output"))
    args = ap.parse_args()
    asof = date.fromisoformat(args.asof)
    r = build(asof)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "register.csv", r["register"], list(r["register"][0].keys()))
    write_csv(out / "calendar.csv", r["calendar"], list(r["calendar"][0].keys()) if r["calendar"] else ["due_date"])
    write_csv(out / "vault-index.csv", r["vault_index"], ["file", "label", "bound_to"])
    write_csv(out / "candidates.csv", r["candidates"], ["source_document", "clause", "heading", "duty_phrase", "snippet"])
    (out / "gaps.md").write_text(
        "# Gap list (observational)\n\nAs of %s. An approved undertaking names a deliverable and no file is present in the vault.\n\n" % r["asof"]
        + "".join(f"- **{g[0]}** {g[1]} — due {g[2]} — {g[4]} {g[3]} — expected `{g[5]}*`\n" for g in r["gaps"]) + ("\n(none)\n" if not r["gaps"] else ""),
        encoding="utf-8")
    write_csv(out / "open-items.csv", r["open_items"], ["requested_on", "requested_from", "item", "source_document", "clause", "what_was_asked"])
    (out / "open-items.md").write_text(
        "# Items awaiting input\n\nMuni-Pal has requested the following in writing and has received no written instruction. Sorted by request date.\n\n"
        + "".join(f"- {x['requested_on']} → {x['requested_from']}: **{x['item']}** ({x['source_document']} {x['clause']}). {x['what_was_asked']}\n" for x in r["open_items"]) + ("\n(none)\n" if not r["open_items"] else ""),
        encoding="utf-8")
    refusal = out / "refusal-log.md"
    if not refusal.exists():
        refusal.write_text("# Refusal log\n\nEvery judgment question put to us: the question, the date, and where it was routed. We do not answer them.\n\n", encoding="utf-8")
    (out / "register.html").write_text(render_html(r), encoding="utf-8")
    refusals = sum(1 for l in refusal.read_text(encoding="utf-8").splitlines() if l.startswith("- "))
    (out / "summary.json").write_text(json.dumps({
        "asof": r["asof"], "obligations": len(r["register"]),
        "status_counts": {s: sum(1 for x in r["register"] if x["status"] == s) for s in STATUSES},
        "calendar_rows": len(r["calendar"]), "gaps": len(r["gaps"]), "open_items": len(r["open_items"]),
        "refusals_logged": refusals,
        "vault_files": len(r["vault_index"]), "unbound_vault_files": sum(1 for v in r["vault_index"] if v["bound_to"] == "UNBOUND"),
    }, indent=2), encoding="utf-8")
    print((out / "summary.json").read_text())


if __name__ == "__main__":
    main()
