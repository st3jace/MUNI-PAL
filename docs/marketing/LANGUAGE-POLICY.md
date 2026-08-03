# Muni-Pal Public Language & Data-Provenance Policy

**Status:** v0.1 DRAFT — pending Stephen approval (Linear ART-120)
**Owner:** Stephen (approver) · COS (author) · Arthur (bond-intelligence reviewer)
**Scope:** every public surface — muni-pal.io pages, meta/OG/SEO tags, PDF/report
exports, emails, decks, social posts, and any client deliverable.
**Basis:** ART-121 research memo (`braintrust/workspace/arthur/2026-08-emma-permission-track.md`),
EMMA Website User Agreement (emma.msrb.org/AboutEmma/UserAgreement), MSRB Website
Terms of Use. Decision of record 2026-08-03: **no MSRB subscription** — we operate
on the compliant-workaround posture defined here.

---

## 1. The brand rule (absolute)

**"EMMA," "MSRB," and any MSRB mark or logo never appear on a public surface.**
The marks are MSRB trademarks; both ToU bar use without prior written consent.
This is not a tone choice — it is a legal posture, and it applies to meta tags,
alt text, filenames, and exported documents, not just visible copy.

There is no internal-doc ban: engineering docs, tickets, and this file may name
EMMA factually. The line is *public surfaces*.

## 2. Replacement lexicon

| Current phrasing | Approved replacement |
|---|---|
| "866 actual EMMA transactions" | "866 actual municipal bond transactions" |
| "the EMMA corpus" / "EMMA municipal bond corpus" | "our municipal bond corpus" |
| "real EMMA data" | "real public-disclosure data" |
| "EMMA filings" / "EMMA official statements" | "public municipal securities disclosures" / "public official statements" |
| "filed with EMMA" (issuer-obligation context) | "filed in the public municipal disclosure system" |
| "MSRB EMMA municipal bond corpus" (export attribution) | "our corpus of public municipal securities disclosures" |
| "EMMA Corpus: Observed Spreads" (section title) | "Observed Spreads" |
| "Run the EMMA crawler on the {sector} sector…" (empty state) | "Observed data for this sector is coming soon." |
| "As the EMMA crawler discovers and extracts…" (empty state) | "As sector data is added, trades will appear here." |

Generic descriptions that are always safe: *"public municipal securities
disclosures," "public primary-market and continuing-disclosure filings,"
"observed market data."* These are factual source descriptions, not brand uses.

Internal tooling words (**crawler, corpus-pipeline, sensing, extractor,
archetype, playbook**) never appear in visitor-facing copy — see COPY-STANDARD §4.

## 3. Data-provenance classes

Every dataset and every public number belongs to exactly one class. The class
determines what we may do with it.

**Class A — Our own deal record.** SVIDA pipeline documents (official statements,
fee terms, closing sets we were party to). *Unrestricted use, internal and
public,* subject only to client confidentiality (strip names/amounts per the
V1/V2/V3 report-version standard).

**Class B — Manually retrieved public disclosures.** Individual OS/CD documents a
human retrieves at human pace from the public disclosure system for internal
analysis. *Expressly permitted by the ToU.* Rules: no automation, no bulk
collection, facts extracted (par, coupon, DSCR, enrollment — facts are not
copyrightable) go into analysis as **facts with citations**, not as a
redistributed document database. Public numbers derived from Class B must be
**aggregated and non-reproducing** (ranges, medians — never a reconstructable
per-deal dataset).

**Class C — Independently licensed-free public sources.** Sources with no
EMMA-ToU exposure, to be inventoried and vetted individually (ART-121 pivot):
state COI transparency databases (e.g., California CDIAC, Texas Bond Review
Board), state DOE / charter-authorizer financial reports, issuer and trustee
public postings, SEC EDGAR, IRS 8038 statistics, Census of Governments,
FRED/Treasury/CBOE (already vetted estate-side). *Each source is used under its
own terms; a source enters Class C only after its terms are checked and logged
in the source register.*

**Class D — Automated EMMA retrieval and EMMA-derived databases. PROHIBITED.**
No crawling, no scraping, no bulk automated pulls, no derived-benchmark database
built from the free EMMA site — internal or public, paid decision of 2026-08-03
notwithstanding future revisit. The existing housing/healthcare crawls are HELD
(scheduled tasks gated 2026-08-03).

**Legacy corpus (the 866-transaction healthcare corpus and housing corpus):**
collected under Class D methods before this policy. Posture: **quarantined for
NEW public claims** — existing published numbers are reviewed claim-by-claim in
the CLAIMS-REGISTER (ART-129), where each is either (a) re-derived from Class
A/B/C provenance, (b) relabeled as methodology-derived, or (c) removed. The
audit decides; this policy only forbids *adding* public claims on Class D
provenance.

## 4. Numbers policy

- Counts of our own analytical work ("866 transactions analyzed") may be stated;
  attribution follows §2 (never to EMMA).
- **Observed vs. methodology-derived is always labeled honestly.** A number from
  a thin sample or synthetic modeling is presented as methodology-derived
  ("typical ranges based on our deal experience and published sector data"),
  never dressed as observed market data. (Housing playbook precedent.)
- Every public quantitative claim requires a CLAIMS-REGISTER row: claim → source
  artifact → provenance class → status. No row, no claim. (ART-129.)

## 5. Flagged, not decided here

- **MSRB Rule G-42 / advisor-status disclaimer.** The live landing page carries
  no G-42 disclaimer; undeployed drafts (variant-b/c) do. Whether to add one is
  a legal question for Stephen/licensed counsel — out of scope for this policy,
  and G-42 language would itself name MSRB (a §1 tension to resolve with
  counsel). Do not silently add or remove.
- **Future licensing revisit.** If economics change, the Primary Market
  Subscription path (ART-121 memo §4) reopens Class D cleanly. The draft
  outreach letter is on file; nothing sent.

## 6. Enforcement

- **Build gate:** `git grep -i -e emma -e msrb` over `frontend/src/pages/tools`,
  `frontend/index*.html`, and built bundles must return zero user-visible hits
  (ART-126 makes this a deploy verification; candidate CI check).
- **Copy gate:** every page rewrite passes the COPY-STANDARD checklist, which
  includes "provenance class recorded for every number."
- **Standing reviewer:** Arthur certifies the claims register and any new public
  benchmark before it ships.
