#!/usr/bin/env python3
"""Build the SYNTHETIC fixture pack for the Obligation Register demo.

Writes documents/, approved-inputs.csv, approval-2026-09-08.md and vault/.
Every name, number and date is invented. Re-runnable; overwrites.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "documents"
VAULT = ROOT / "vault"

BANNER = "> SYNTHETIC DOCUMENT. Every name, amount and date is invented for demonstration. Not a real transaction.\n"

DOCUMENTS = {
"00-index.md": """# Closing Transcript Index — SYNTHETIC

**Saguaro Commons Apartments, LP — Series 2025**
Multifamily Housing Revenue Bonds (Saguaro Commons Apartments Project), Series 2025
Issuer: The Industrial Development Authority of the City of Mesquite Flats
Closing Date: June 26, 2025

""" + BANNER + """
| No. | Document | File |
|---|---|---|
| 01 | Indenture of Trust (excerpt) | 01-indenture-excerpt.md |
| 02 | Loan Agreement (excerpt) | 02-loan-agreement-excerpt.md |
| 03 | Continuing Disclosure Agreement | 03-continuing-disclosure-agreement.md |
| 04 | Tax Regulatory Agreement (excerpt) | 04-tax-regulatory-agreement-excerpt.md |
| 05 | Land Use Restriction Agreement (excerpt) | 05-regulatory-agreement-excerpt.md |
""",

"01-indenture-excerpt.md": """# Indenture of Trust (excerpt) — SYNTHETIC

between The Industrial Development Authority of the City of Mesquite Flats, as Issuer, and Ironwood Trust Company, N.A., as Trustee, dated as of June 1, 2025.

""" + BANNER + """
## Section 2.02. Interest Payment Dates.
Interest on the Bonds shall be payable on January 1 and July 1 of each year, commencing January 1, 2026.

## Section 7.04. Reports by Trustee.
The Trustee shall furnish to the Issuer and the Borrower, not later than thirty (30) days after the end of each Bond Year, a statement of all funds and accounts held under this Indenture.

## Section 7.06. Notice of Default.
The Trustee shall give notice to the Bondholders of any Event of Default known to the Trustee within thirty (30) days after the Trustee obtains knowledge thereof, unless such default has been cured.

## Section 9.01. Events of Default.
(a) failure to pay principal or interest on any Bond when due; (b) failure by the Borrower to observe any covenant in the Loan Agreement continuing for thirty (30) days after written notice; (c) the occurrence of an Act of Bankruptcy of the Borrower.
""",

"02-loan-agreement-excerpt.md": """# Loan Agreement (excerpt) — SYNTHETIC

between The Industrial Development Authority of the City of Mesquite Flats, as Issuer, and Saguaro Commons Apartments, LP, as Borrower, dated as of June 1, 2025.

""" + BANNER + """
## Section 6.3. Insurance.
The Borrower shall maintain the insurance required by Exhibit C. On or before each anniversary of the Closing Date, the Borrower shall deliver to the Trustee certificates evidencing that such insurance is in full force and effect.

## Section 6.5. Annual Certificate of No Default.
Within one hundred twenty (120) days after the end of each Fiscal Year, the Borrower shall deliver to the Issuer and the Trustee a certificate signed by an Authorized Borrower Representative stating that, to the best of such person's knowledge, no Event of Default has occurred and is continuing, or, if any such event has occurred, specifying the nature thereof.

## Section 6.6. Financial Statements.
The Borrower shall deliver audited financial statements for each Fiscal Year to the Trustee within one hundred eighty (180) days after the end of such Fiscal Year.

## Section 6.8. Quarterly Operating Reports.
Within forty-five (45) days after the end of each calendar quarter, the Borrower shall deliver to the Issuer and the Trustee a rent roll and an occupancy report for the Project as of the last day of such quarter.

## Section 6.9. Debt Service Coverage.
The Borrower covenants to maintain a Debt Service Coverage Ratio of not less than 1.15 to 1.00, tested annually as of the last day of each Fiscal Year on the basis of the audited financial statements delivered under Section 6.6. The Borrower shall deliver the calculation of such ratio to the Trustee together with such audited financial statements.

## Section 6.10. Other Information.
The Borrower shall furnish to the Trustee such other information regarding the Project as the Trustee may reasonably request from time to time.

## Section 6.12. Notice of Litigation.
The Borrower shall promptly notify the Issuer and the Trustee of any litigation or administrative proceeding that, if adversely determined, could reasonably be expected to have a material adverse effect on the Project.
""",

"03-continuing-disclosure-agreement.md": """# Continuing Disclosure Agreement — SYNTHETIC

This Continuing Disclosure Agreement (this "Disclosure Agreement") is executed and delivered as of June 26, 2025 by Saguaro Commons Apartments, LP (the "Borrower") and Ironwood Trust Company, N.A., as dissemination agent (the "Dissemination Agent"), in connection with the issuance of $24,500,000 Multifamily Housing Revenue Bonds (Saguaro Commons Apartments Project), Series 2025 (the "Bonds").

""" + BANNER + """
## Section 1. Purpose.
This Disclosure Agreement is being executed and delivered for the benefit of the Holders and Beneficial Owners of the Bonds and in order to assist the Participating Underwriter in complying with Rule 15c2-12.

## Section 2. Definitions.
"Annual Report" means any Annual Report provided by the Borrower pursuant to Section 4.
"Fiscal Year" means the twelve-month period ending December 31.
"Listed Events" means any of the events listed in Section 5(a).
"Business Day" means any day other than a Saturday, Sunday or a day on which the Trustee is closed.

## Section 4. Provision of Annual Reports.
(a) The Borrower shall, or shall cause the Dissemination Agent to, not later than one hundred eighty (180) days after the end of each Fiscal Year, commencing with the Fiscal Year ending December 31, 2025, provide to the MSRB through EMMA an Annual Report which is consistent with the requirements of Section 4(c).
(b) If the Borrower's audited financial statements are not available by the date required in Section 4(a), the Annual Report shall contain unaudited financial statements, and the audited financial statements shall be filed when they become available.
(c) The Annual Report shall contain or incorporate by reference: (i) the audited financial statements of the Borrower for the prior Fiscal Year; (ii) the occupancy rate of the Project as of the last day of the Fiscal Year; (iii) the Debt Service Coverage Ratio for the Fiscal Year calculated under Section 6.9 of the Loan Agreement.
(d) If the Borrower is unable to provide the Annual Report by the date required in Section 4(a), the Borrower shall, or shall cause the Dissemination Agent to, send a notice to the MSRB in substantially the form of Exhibit A.
(e) If the Borrower changes its Fiscal Year, the Borrower shall give notice of such change in the same manner as for a Listed Event under Section 5.

## Section 5. Reporting of Listed Events.
(a) The Borrower shall give, or cause to be given, notice of the occurrence of any of the following events with respect to the Bonds, in a timely manner not in excess of ten (10) Business Days after the occurrence of the event:
1. Principal and interest payment delinquencies;
2. Non-payment related defaults, if material;
3. Unscheduled draws on debt service reserves reflecting financial difficulties;
4. Unscheduled draws on credit enhancements reflecting financial difficulties;
5. Substitution of credit or liquidity providers, or their failure to perform;
6. Adverse tax opinions or other material events affecting the tax status of the Bonds;
7. Modifications to rights of Bondholders, if material;
8. Bond calls, if material, and tender offers;
9. Defeasances;
10. Release, substitution or sale of property securing repayment of the Bonds, if material;
11. Rating changes;
12. Bankruptcy, insolvency, receivership or similar event of the Borrower;
13. Consummation of a merger, consolidation or acquisition involving the Borrower, if material;
14. Appointment of a successor or additional trustee or the change of name of a trustee, if material;
15. Incurrence of a Financial Obligation of the Borrower, if material, or agreement to covenants, events of default, remedies, priority rights or other similar terms of a Financial Obligation, any of which affect security holders, if material;
16. Default, event of acceleration, termination event, modification of terms or other similar events under the terms of a Financial Obligation of the Borrower, any of which reflect financial difficulties.
(b) Whenever the Borrower obtains knowledge of the occurrence of a Listed Event, the Borrower shall determine whether such event would be material under applicable federal securities law, where materiality is a condition to reporting.

## Section 7. Dissemination Agent.
The Borrower may, from time to time, appoint or engage a Dissemination Agent to assist it in carrying out its obligations under this Disclosure Agreement. The initial Dissemination Agent shall be Ironwood Trust Company, N.A. The Dissemination Agent shall have no duty to review the content of any Annual Report or notice.

## Section 9. Termination of Reporting Obligation.
The Borrower's obligations under this Disclosure Agreement shall terminate upon the legal defeasance, prior redemption or payment in full of all of the Bonds.

## Section 11. Default.
In the event of a failure of the Borrower to comply with any provision of this Disclosure Agreement, any Holder or Beneficial Owner may take such actions as may be necessary and appropriate, including seeking mandate or specific performance by court order, to cause the Borrower to comply. A default under this Disclosure Agreement shall not be deemed an Event of Default under the Indenture or the Loan Agreement.
""",

"04-tax-regulatory-agreement-excerpt.md": """# Tax Regulatory Agreement (excerpt) — SYNTHETIC

among The Industrial Development Authority of the City of Mesquite Flats, Saguaro Commons Apartments, LP, and Ironwood Trust Company, N.A., dated June 26, 2025.

""" + BANNER + """
## Section 4.3. Annual Certification of Qualified Residential Rental Project.
On or before January 31 of each year, the Borrower shall deliver to the Issuer and the Trustee a Certificate of Continuing Program Compliance, in the form of Exhibit B, certifying as to the Project's status as a qualified residential rental project under Section 142(d) of the Code for the preceding calendar year.

## Section 5.2. Rebate Computations.
The Borrower shall cause a Rebate Analyst to compute the Rebate Amount as of each Computation Date. "Computation Date" means each fifth anniversary of the Closing Date and the date of final payment of the Bonds. The Borrower shall deliver each rebate computation to the Trustee within sixty (60) days after the applicable Computation Date, and shall pay any Rebate Amount to the United States within the time required by Section 148(f) of the Code.

## Section 6.1. Record Retention.
The Borrower shall retain all records relating to the Bonds, the Project and the investment of proceeds for the term of the Bonds plus three (3) years after the final payment of the Bonds.

## Section 6.4. Change in Use.
The Borrower shall not take any action, or omit to take any action, that would cause the Project to cease to be a qualified residential rental project, and shall notify the Issuer and Bond Counsel prior to any change in use of the Project.
""",

"05-regulatory-agreement-excerpt.md": """# Land Use Restriction Agreement (excerpt) — SYNTHETIC

between The Industrial Development Authority of the City of Mesquite Flats and Saguaro Commons Apartments, LP, recorded June 26, 2025.

""" + BANNER + """
## Section 3.1. Set-Aside Election.
The Borrower elects that not less than forty percent (40%) of the completed units in the Project shall be occupied by Low-Income Tenants whose income does not exceed sixty percent (60%) of area median income, for the Qualified Project Period.

## Section 3.4. Tenant Income Certifications.
The Borrower shall obtain an income certification from each Low-Income Tenant upon initial occupancy and annually thereafter, and shall maintain such certifications on file at the Project.

## Section 3.5. Quarterly Compliance Report to Issuer.
Within fifteen (15) days after the end of each calendar quarter, the Borrower shall deliver to the Issuer a report, in the form attached as Exhibit D, showing the number of Low-Income Units and the income certification status of each Low-Income Tenant.
""",
}

# The load-bearing control. Every row here was "approved" by the client's own
# counsel / dissemination agent (synthetic). Muni-Pal transcribes; it does not decide.
APPROVED_FIELDS = [
    "obligation_id", "obligation", "source_document", "clause", "recipient", "frequency",
    "due_rule_text_verbatim", "due_dates_approved", "approved_by", "approval_ref", "evidence_pattern",
]
COUNSEL = "Creosote & Mesa LLP (bond counsel)"
DA = "Ironwood Trust Company (dissemination agent)"
REF = "approval-2026-09-08.md"
APPROVED = [
    ("OB-01", "Annual Report to MSRB via EMMA (audited FS + occupancy + DSCR)", "03-continuing-disclosure-agreement.md", "Section 4(a)", "MSRB (EMMA)", "annual",
     "not later than one hundred eighty (180) days after the end of each Fiscal Year, commencing with the Fiscal Year ending December 31, 2025", "2026-06-29;2027-06-29", COUNSEL, REF, "annual-report-FY{fy}"),
    ("OB-02", "Audited financial statements filed when available if not in Annual Report", "03-continuing-disclosure-agreement.md", "Section 4(b)", "MSRB (EMMA)", "conditional",
     "the audited financial statements shall be filed when they become available", "", COUNSEL, REF, ""),
    ("OB-03", "Notice of failure to file Annual Report", "03-continuing-disclosure-agreement.md", "Section 4(d)", "MSRB (EMMA)", "conditional",
     "If the Borrower is unable to provide the Annual Report by the date required in Section 4(a), the Borrower shall ... send a notice to the MSRB", "", COUNSEL, REF, ""),
    ("OB-04", "Listed Event notices (16 events)", "03-continuing-disclosure-agreement.md", "Section 5(a)", "MSRB (EMMA)", "event-driven",
     "in a timely manner not in excess of ten (10) Business Days after the occurrence of the event", "", COUNSEL, REF, ""),
    ("OB-05", "Notice of change in Fiscal Year", "03-continuing-disclosure-agreement.md", "Section 4(e)", "MSRB (EMMA)", "event-driven",
     "the Borrower shall give notice of such change in the same manner as for a Listed Event", "", COUNSEL, REF, ""),
    ("OB-06", "Quarterly rent roll and occupancy report", "02-loan-agreement-excerpt.md", "Section 6.8", "Issuer; Trustee", "quarterly",
     "Within forty-five (45) days after the end of each calendar quarter", "2025-11-14;2026-02-14;2026-05-15;2026-08-14;2026-11-14;2027-02-14", DA, REF, "quarterly-report-{period}"),
    ("OB-07", "Annual Certificate of No Default", "02-loan-agreement-excerpt.md", "Section 6.5", "Issuer; Trustee", "annual",
     "Within one hundred twenty (120) days after the end of each Fiscal Year", "2026-04-30;2027-04-30", COUNSEL, REF, "no-default-cert-FY{fy}"),
    ("OB-08", "Insurance certificates", "02-loan-agreement-excerpt.md", "Section 6.3", "Trustee", "annual",
     "On or before each anniversary of the Closing Date", "2026-06-26;2027-06-26", DA, REF, "insurance-cert-{year}"),
    ("OB-09", "Audited financial statements to Trustee", "02-loan-agreement-excerpt.md", "Section 6.6", "Trustee", "annual",
     "within one hundred eighty (180) days after the end of such Fiscal Year", "2026-06-29;2027-06-29", COUNSEL, REF, "afs-FY{fy}"),
    ("OB-10", "Debt Service Coverage Ratio calculation delivered with audited FS", "02-loan-agreement-excerpt.md", "Section 6.9", "Trustee", "annual",
     "The Borrower shall deliver the calculation of such ratio to the Trustee together with such audited financial statements", "2026-06-29;2027-06-29", COUNSEL, REF, "dscr-calc-FY{fy}"),
    ("OB-11", "Other information on reasonable request", "02-loan-agreement-excerpt.md", "Section 6.10", "Trustee", "on request",
     "such other information regarding the Project as the Trustee may reasonably request from time to time", "", COUNSEL, REF, ""),
    ("OB-12", "Notice of litigation", "02-loan-agreement-excerpt.md", "Section 6.12", "Issuer; Trustee", "event-driven",
     "promptly notify ... of any litigation ... that ... could reasonably be expected to have a material adverse effect", "", COUNSEL, REF, ""),
    ("OB-13", "Certificate of Continuing Program Compliance (IRC 142(d))", "04-tax-regulatory-agreement-excerpt.md", "Section 4.3", "Issuer; Trustee", "annual",
     "On or before January 31 of each year", "2026-01-31;2027-01-31", COUNSEL, REF, "ccpc-{year}"),
    ("OB-14", "Rebate computation delivered to Trustee", "04-tax-regulatory-agreement-excerpt.md", "Section 5.2", "Trustee", "every 5th Bond Year",
     "within sixty (60) days after the applicable Computation Date; Computation Date means each fifth anniversary of the Closing Date and the date of final payment", "2030-08-25", COUNSEL, REF, "rebate-calc-{year}"),
    ("OB-15", "Record retention", "04-tax-regulatory-agreement-excerpt.md", "Section 6.1", "Borrower (internal)", "standing",
     "for the term of the Bonds plus three (3) years after the final payment of the Bonds", "", COUNSEL, REF, ""),
    ("OB-16", "Notice prior to change in use", "04-tax-regulatory-agreement-excerpt.md", "Section 6.4", "Issuer; Bond Counsel", "event-driven",
     "shall notify the Issuer and Bond Counsel prior to any change in use of the Project", "", COUNSEL, REF, ""),
    ("OB-17", "Quarterly compliance report (Low-Income Units)", "05-regulatory-agreement-excerpt.md", "Section 3.5", "Issuer", "quarterly",
     "Within fifteen (15) days after the end of each calendar quarter", "2025-10-15;2026-01-15;2026-04-15;2026-07-15;2026-10-15;2027-01-15", DA, REF, "lura-quarterly-{period}"),
    ("OB-18", "Annual tenant income certifications on file", "05-regulatory-agreement-excerpt.md", "Section 3.4", "Borrower (internal)", "annual",
     "upon initial occupancy and annually thereafter", "", COUNSEL, REF, ""),
]

APPROVAL_NOTE = """# Approval of obligation list — SYNTHETIC

**From:** Creosote & Mesa LLP, bond counsel (synthetic), and Ironwood Trust Company, N.A., dissemination agent (synthetic)
**To:** Saguaro Commons Apartments, LP; Muni-Pal
**Date:** 2026-09-08

We have reviewed the candidate obligation list extracted from the Series 2025 closing documents. The obligations, clause references and due dates in `approved-inputs.csv` are approved as stated. Where the `due_dates_approved` column is blank, no date is supplied and none should be computed. Items marked `on request`, `event-driven`, `conditional` or `standing` carry no calendar date.

Muni-Pal records what is written here. It does not decide which undertaking controls, interpret deadline formulas, or decide whether an obligation applies.
"""

# Synthetic evidence. Some present, some deliberately missing (Q1-2026 quarterly report,
# FY2025 no-default certificate) so the gap list has something to say.
VAULT = [
    ("annual-report-FY2025.txt", "Annual Report FY2025 (audited FS, occupancy, DSCR calc attached)", "2026-06-15", "MSRB via EMMA (dissemination agent confirmation)"),
    ("afs-FY2025.txt", "Audited Financial Statements FY2025", "2026-06-15", "Trustee"),
    ("dscr-calc-FY2025.txt", "DSCR calculation FY2025", "2026-06-15", "Trustee"),
    ("quarterly-report-2025Q3.txt", "Quarterly rent roll + occupancy Q3 2025", "2025-11-10", "Issuer; Trustee"),
    ("quarterly-report-2025Q4.txt", "Quarterly rent roll + occupancy Q4 2025", "2026-02-12", "Issuer; Trustee"),
    ("quarterly-report-2026Q2.txt", "Quarterly rent roll + occupancy Q2 2026", "2026-08-11", "Issuer; Trustee"),
    ("insurance-cert-2026.txt", "Insurance certificates 2026", "2026-06-20", "Trustee"),
    ("ccpc-2026.txt", "Certificate of Continuing Program Compliance 2026 (for CY2025)", "2026-01-28", "Issuer; Trustee"),
    ("lura-quarterly-2025Q3.txt", "LURA quarterly compliance report Q3 2025", "2025-10-14", "Issuer"),
    ("lura-quarterly-2025Q4.txt", "LURA quarterly compliance report Q4 2025", "2026-01-13", "Issuer"),
    ("lura-quarterly-2026Q1.txt", "LURA quarterly compliance report Q1 2026", "2026-04-14", "Issuer"),
    ("lura-quarterly-2026Q2.txt", "LURA quarterly compliance report Q2 2026", "2026-07-14", "Issuer"),
]


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    VAULT_DIR = ROOT / "vault"
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    for name, text in DOCUMENTS.items():
        (DOCS / name).write_text(text, encoding="utf-8")
    with (ROOT / "approved-inputs.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(APPROVED_FIELDS)
        w.writerows(APPROVED)
    (ROOT / "approval-2026-09-08.md").write_text(APPROVAL_NOTE, encoding="utf-8")
    for fname, title, filed, recipient in VAULT:
        (VAULT_DIR / fname).write_text(
            f"SYNTHETIC EVIDENCE FILE - {title}\nFiled/delivered: {filed}\nRecipient: {recipient}\n",
            encoding="utf-8",
        )
    print(f"documents={len(DOCUMENTS)} approved={len(APPROVED)} vault={len(VAULT)}")


if __name__ == "__main__":
    main()
