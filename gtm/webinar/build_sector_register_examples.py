"""Build the made-up education and healthcare-center register examples.

The examples are workshop/public artifacts, not legal templates. Every entity,
clause label, date, and file name is invented. Run from the repository root:

    python gtm/webinar/build_sector_register_examples.py
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "samples"
AS_OF = "2026-09-17"


@dataclass(frozen=True)
class Row:
    obligation_id: str
    obligation: str
    source_document: str
    clause: str
    recipient: str
    frequency: str
    next_due: str
    status: str
    status_note: str
    evidence_file: str = ""


@dataclass(frozen=True)
class Example:
    slug: str
    sector: str
    deal_id: str
    title: str
    rows: tuple[Row, ...]
    open_items: tuple[tuple[str, str, str, str, str], ...]
    refusal: str


EXAMPLES = (
    Example(
        slug="education",
        sector="Education",
        deal_id="SYN-EDU-AZ-2024",
        title="Desert Bridge Learning Center, Inc. — Series 2024",
        rows=(
            Row("OB-01", "Annual report: audited financial statements and enrollment summary", "03-continuing-disclosure-agreement.md", "Section 4(a)", "MSRB via public filing system", "annual", "2027-05-30", "filed", "FY2025 report is in the supplied file set", "annual-report-FY2025.txt"),
            Row("OB-02", "Quarterly enrollment and waitlist report", "02-loan-agreement-excerpt.md", "Section 6.7", "Issuer; Trustee", "quarterly", "2026-08-15", "evidence missing", "due date passed; no matching file in the supplied file set"),
            Row("OB-03", "Quarterly unaudited financial statements and covenant certificate", "02-loan-agreement-excerpt.md", "Section 6.8", "Trustee", "quarterly", "2026-11-15", "not filed", "next approved due date is in the future"),
            Row("OB-04", "Listed-event notices", "03-continuing-disclosure-agreement.md", "Section 5(a)", "MSRB via public filing system", "conditional", "", "not testable", "no event or request was supplied"),
            Row("OB-05", "Annual insurance certificate", "02-loan-agreement-excerpt.md", "Section 6.4", "Trustee", "annual", "2027-01-31", "filed", "2026 certificate is in the supplied file set", "insurance-certificate-2026.txt"),
            Row("OB-06", "Notice concerning charter authorization", "02-loan-agreement-excerpt.md", "Section 6.11", "Issuer; Trustee", "event-driven", "", "not testable", "no event or request was supplied"),
            Row("OB-07", "Rebate computation", "04-tax-certificate-excerpt.md", "Section 5.2", "Trustee", "five-year", "2029-08-01", "not filed", "approved due date is in the future"),
            Row("OB-08", "Annual certificate of no default", "02-loan-agreement-excerpt.md", "Section 6.5", "Trustee", "annual", "2027-04-30", "filed", "FY2025 certificate is in the supplied file set", "no-default-certificate-FY2025.txt"),
        ),
        open_items=(
            ("2026-09-17", "bond counsel", "Section 6.11", "Please confirm in writing whether the charter-authorization notice belongs in the borrower's approved list.", "02-loan-agreement-excerpt.md"),
            ("2026-09-17", "dissemination agent", "Section 4(a)", "Please confirm the approved date for the next annual report.", "03-continuing-disclosure-agreement.md"),
        ),
        refusal='"Does the enrollment decline trigger a notice?" Sent to bond counsel / dissemination agent; not answered by Muni-Pal.',
    ),
    Example(
        slug="healthcare-center",
        sector="Healthcare center",
        deal_id="SYN-HCC-AZ-2023",
        title="Sunrise Community Health Center, Inc. — Series 2023",
        rows=(
            Row("OB-01", "Annual report: audited financial statements, patient visits, and payer mix", "03-continuing-disclosure-agreement.md", "Section 4(a)", "MSRB via public filing system", "annual", "2027-06-29", "filed", "FY2025 report is in the supplied file set", "annual-report-FY2025.txt"),
            Row("OB-02", "Quarterly patient-volume and payer-mix report", "02-loan-agreement-excerpt.md", "Section 6.9", "Issuer; Trustee", "quarterly", "2026-08-15", "evidence missing", "due date passed; no matching file in the supplied file set"),
            Row("OB-03", "Quarterly unaudited financial statements and debt-service-coverage certificate", "02-loan-agreement-excerpt.md", "Section 6.8", "Trustee", "quarterly", "2026-11-15", "filed", "2026 Q2 report is in the supplied file set", "quarterly-financials-2026Q2.txt"),
            Row("OB-04", "Listed-event notices", "03-continuing-disclosure-agreement.md", "Section 5(a)", "MSRB via public filing system", "conditional", "", "not testable", "no event or request was supplied"),
            Row("OB-05", "Annual insurance certificate", "02-loan-agreement-excerpt.md", "Section 6.4", "Trustee", "annual", "2027-01-31", "filed", "2026 certificate is in the supplied file set", "insurance-certificate-2026.txt"),
            Row("OB-06", "Notice concerning facility license or accreditation", "02-loan-agreement-excerpt.md", "Section 6.12", "Issuer; Trustee", "event-driven", "", "not testable", "no event or request was supplied"),
            Row("OB-07", "Rebate computation", "04-tax-certificate-excerpt.md", "Section 5.2", "Trustee", "five-year", "2028-09-01", "not filed", "approved due date is in the future"),
            Row("OB-08", "Annual certificate of no default", "02-loan-agreement-excerpt.md", "Section 6.5", "Trustee", "annual", "2026-04-30", "evidence missing", "due date passed; no matching file in the supplied file set"),
        ),
        open_items=(
            ("2026-09-17", "bond counsel", "Section 6.12", "Please confirm in writing whether the license-or-accreditation notice belongs in the borrower's approved list.", "02-loan-agreement-excerpt.md"),
            ("2026-09-17", "dissemination agent", "Section 4(a)", "Please confirm the approved date for the next annual report.", "03-continuing-disclosure-agreement.md"),
        ),
        refusal='"Does the change in payer mix require an event notice?" Sent to bond counsel / dissemination agent; not answered by Muni-Pal.',
    ),
)

CSS = """
:root{--bg:#fbfaf7;--fg:#1e1e1e;--muted:#626b76;--line:#ddd8cf;--navy:#1b3a5c;--teal:#1e8c8a;--ok:#1f6f43;--warn:#9a5b00;--bad:#9b2226}
*{box-sizing:border-box}body{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,"Segoe UI",Roboto,sans-serif;margin:0;padding:24px;max-width:1240px}a{color:var(--navy)}nav{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:18px}h1{font-size:24px;color:var(--navy);margin:0 0 4px}h2{font-size:17px;color:var(--navy);margin:28px 0 8px;border-bottom:1px solid var(--line);padding-bottom:4px}.muted{color:var(--muted)}.banner{background:#fff3cd;border:1px solid #e6c85a;padding:10px 12px;border-radius:6px;margin:12px 0}.never{background:#fff;border:1px solid var(--line);padding:11px 14px;border-radius:6px;margin:12px 0}.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:10px 0}.kpi div{border:1px solid var(--line);border-radius:6px;padding:8px 12px;background:#fff;min-width:140px}.kpi b{display:block;font-size:20px;color:var(--navy)}.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:13px;background:#fff}th,td{border:1px solid var(--line);padding:6px 8px;vertical-align:top;text-align:left}th{background:#f1ede4}.s-filed{color:var(--ok)}.s-evidence-missing{color:var(--bad);font-weight:600}.s-not-filed{color:var(--warn)}.s-not-testable{color:var(--muted)}code{font-size:12px}@media print{nav{display:none}body{padding:0;max-width:none}}
""".strip()


def cells(values: tuple[str, ...], cls: str = "") -> str:
    return "".join(f"<td class='{cls}'>{escape(value)}</td>" for value in values)


def render(example: Example) -> str:
    counts = {status: sum(row.status == status for row in example.rows) for status in ("filed", "not filed", "evidence missing", "not testable")}
    register_rows = "\n".join(
        "<tr>" + cells((row.obligation_id, row.obligation, row.source_document, row.clause, row.recipient, row.frequency, row.next_due or "—", row.status, row.status_note, row.evidence_file or "—"), "s-" + row.status.replace(" ", "-")) + "</tr>"
        for row in example.rows
    )
    calendar_rows = "\n".join(
        "<tr>" + cells((row.next_due, row.obligation_id, row.obligation, row.recipient, row.clause, row.status, row.evidence_file or "—"), "s-" + row.status.replace(" ", "-")) + "</tr>"
        for row in example.rows if row.next_due
    )
    gaps = [row for row in example.rows if row.status == "evidence missing"]
    gap_rows = "\n".join("<tr>" + cells((row.obligation_id, row.obligation, row.next_due, row.clause, row.source_document, "No matching file in supplied set")) + "</tr>" for row in gaps)
    open_rows = "\n".join("<tr>" + cells(item) + "</tr>" for item in example.open_items)
    evidence = [row for row in example.rows if row.evidence_file]
    evidence_rows = "\n".join("<tr>" + cells((row.evidence_file, f"MADE-UP EVIDENCE FILE — {row.obligation}", row.obligation_id)) + "</tr>" for row in evidence)
    kpis = "".join(f"<div><b>{counts[status]}</b>{status}</div>" for status in counts) + f"<div><b>{len(example.open_items)}</b>items awaiting input</div>"
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Made-up {escape(example.sector)} Obligation Register — {escape(example.deal_id)}</title><style>{CSS}</style></head><body>
<nav><a href='/samples/'>All examples</a><a href='/samples/obligation-register-sample.html'>Housing</a><a href='/samples/obligation-register-education-sample.html'>Education</a><a href='/samples/obligation-register-healthcare-center-sample.html'>Healthcare center</a></nav>
<h1>Obligation Register — {escape(example.title)}</h1>
<div class='muted'>As of {AS_OF} · {len(example.rows)} approved obligations · {len(evidence)} evidence files · MADE-UP {escape(example.sector)} DEAL {escape(example.deal_id)}</div>
<div class='banner'><b>Made-up demonstration.</b> Every entity, clause label, amount, date, and file name is invented. This is not a legal template. The method is real; the deal is not.</div>
<div class='never'><b>What this register never does.</b> It never files. It never says “compliant.” It never decides which clause controls, interprets a deadline formula, or decides whether an obligation applies. The rows and dates below are treated as if they had been approved in writing for purposes of the example. Questions requiring judgment are logged and sent to the appropriate professional.</div>
<div class='kpi'>{kpis}</div>
<h2>1. Register</h2><div class='wrap'><table><thead><tr><th>row</th><th>reporting promise</th><th>source document</th><th>clause</th><th>recipient</th><th>frequency</th><th>next due</th><th>status</th><th>status note</th><th>evidence file</th></tr></thead><tbody>{register_rows}</tbody></table></div>
<h2>2. Calendar</h2><p class='muted'>Only the made-up dates treated as approved for this example appear here.</p><div class='wrap'><table><thead><tr><th>due date</th><th>row</th><th>reporting promise</th><th>recipient</th><th>clause</th><th>status</th><th>evidence file</th></tr></thead><tbody>{calendar_rows}</tbody></table></div>
<h2>3. Gap list — observational only</h2><p class='muted'>A row calls for a record; no matching file appears in this made-up file set. No ranking, conclusion, or fix is implied.</p><div class='wrap'><table><thead><tr><th>row</th><th>reporting promise</th><th>due date</th><th>clause</th><th>source document</th><th>observation</th></tr></thead><tbody>{gap_rows}</tbody></table></div>
<h2>4. Items awaiting input</h2><p class='muted'>What was asked in writing and has not been answered in this example. The list says nothing about whether the item applies.</p><div class='wrap'><table><thead><tr><th>requested on</th><th>requested from</th><th>clause</th><th>question</th><th>source document</th></tr></thead><tbody>{open_rows}</tbody></table></div>
<h2>5. Refusal log</h2><p>{escape(AS_OF)} · {escape(example.refusal)}</p>
<h2>6. Evidence vault index</h2><div class='wrap'><table><thead><tr><th>file</th><th>label</th><th>bound to</th></tr></thead><tbody>{evidence_rows}</tbody></table></div>
<h2>Legend</h2><ul><li><b>filed:</b> a matching file is in the supplied set.</li><li><b>not filed:</b> the approved due date is in the future.</li><li><b>evidence missing:</b> the approved date passed and no matching file is in the supplied set.</li><li><b>not testable:</b> there is no date to check and no event or request was supplied.</li></ul>
</body></html>"""


def render_index() -> str:
    cards = (
        ("Housing", "Saguaro Commons Apartments, LP", "Rent rolls, occupancy reports, and set-aside reporting.", "obligation-register-sample.html"),
        ("Education", "Desert Bridge Learning Center, Inc.", "Enrollment, waitlist, financial, and charter-related records.", "obligation-register-education-sample.html"),
        ("Healthcare center", "Sunrise Community Health Center, Inc.", "Patient volume, payer mix, financial, and facility-license records.", "obligation-register-healthcare-center-sample.html"),
    )
    card_html = "".join(f"<a class='card' href='{escape(href)}'><span>{escape(sector)}</span><h2>{escape(name)}</h2><p>{escape(copy)}</p><b>Open example →</b></a>" for sector, name, copy, href in cards)
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Made-up Obligation Register Examples</title><style>
:root{{--navy:#1b3a5c;--teal:#1e8c8a;--paper:#f7f5f1;--line:#dcd6cb;--ink:#0b1b2e}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:17px/1.5 system-ui,"Segoe UI",sans-serif}}main{{max-width:1100px;margin:auto;padding:64px 32px}}.eyebrow{{color:var(--teal);font-size:13px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}}h1{{color:var(--navy);font-size:44px;line-height:1.08;max-width:18ch;margin:.25em 0}}.lead{{max-width:66ch;color:#52606d}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:36px}}.card{{display:block;background:#fff;border:1px solid var(--line);border-radius:10px;padding:24px;color:inherit;text-decoration:none}}.card:hover{{border-color:var(--teal);transform:translateY(-2px)}}.card span{{color:var(--teal);font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.08em}}.card h2{{color:var(--navy);font-size:22px;margin:.45em 0}}.card p{{min-height:78px}}.card b{{color:var(--navy)}}.note{{margin-top:28px;padding:16px 18px;background:#fff3cd;border:1px solid #e6c85a;border-radius:8px;font-size:14px}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}.card p{{min-height:0}}}}
</style></head><body><main><p class='eyebrow'>Muni-Pal · workshop examples</p><h1>Same functions. Different sector records.</h1><p class='lead'>The job titles and documents vary. The operational functions remain: keep each approved promise visible, route the right record, and preserve proof. These three made-up registers show that pattern across housing, education, and healthcare centers.</p><div class='grid'>{card_html}</div><div class='note'><b>Made-up examples.</b> Every entity, clause label, amount, date, and file name is invented. These are not legal templates and do not determine what applies to any real financing.</div></main></body></html>"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for example in EXAMPLES:
        path = OUT / f"obligation-register-{example.slug}-sample.html"
        path.write_text(render(example), encoding="utf-8", newline="\n")
        print(path.relative_to(ROOT))
    index = OUT / "index.html"
    index.write_text(render_index(), encoding="utf-8", newline="\n")
    print(index.relative_to(ROOT))


if __name__ == "__main__":
    main()
