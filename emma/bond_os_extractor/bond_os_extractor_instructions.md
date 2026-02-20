# Bond Official Statement PDF Extractor & Learning Engine
## Claude Code Build Instructions

**Purpose:** Build a system that ingests bond Official Statements (OS) and Preliminary Official Statements (POS) — including locked/encrypted PDFs — extracts structured deal data, classifies it into a normalized schema, and feeds a pattern analysis and synthetic data engine for the Bond Facility Management System (BFMS).

**Constraint:** Never modify, decrypt, re-encrypt, or alter source PDFs. Read-only extraction. All files remain bit-for-bit identical after processing.

---

## PHASE 1 — PROJECT SCAFFOLD & PDF INGESTION ENGINE

### 1.1 Initialize Project

```
Create a Python project called `bond-os-extractor` with the following structure:

bond-os-extractor/
├── src/
│   ├── ingestion/          # PDF reading, OCR, text extraction
│   ├── extraction/         # Field-level extractors (one per domain)
│   ├── classification/     # Deal type classifier, taxonomy engine
│   ├── schema/             # Pydantic models for all extracted data
│   ├── storage/            # SQLite + JSON output layer
│   ├── analysis/           # Pattern detection, comp engine
│   ├── synthetic/          # Synthetic data generation
│   └── cli.py              # Command-line interface
├── data/
│   ├── raw_pdfs/           # Drop zone for OS/POS PDFs (never modified)
│   ├── extracted/          # JSON outputs per document
│   ├── corpus/             # Normalized corpus for pattern analysis
│   └── synthetic/          # Generated synthetic deal data
├── configs/
│   └── schema_config.yaml  # Field definitions, extraction rules
├── tests/
└── requirements.txt

Use Python 3.11+. Key dependencies:
- pdfplumber (primary text extraction — handles most locked PDFs for reading)
- pymupdf (fitz) (secondary extractor — strong on locked PDFs, image-based pages)
- pytesseract + Pillow (OCR fallback for scanned/image-only pages)
- pydantic (schema validation)
- sqlite3 (built-in, for structured storage)
- anthropic (Claude API for intelligent field extraction)
- tabula-py (table extraction from PDFs)
- pandas (data manipulation)
- numpy (statistical analysis)
- jinja2 (report templating)

Do NOT install or use any library that modifies, decrypts, or re-saves PDFs.
The tools above are all read-only extraction tools.
```

### 1.2 PDF Ingestion Pipeline (Handles Locked PDFs)

```
Build src/ingestion/pdf_reader.py with a cascading extraction strategy:

The key insight: "locked" or "encrypted" municipal bond PDFs almost always have
an empty owner password with print/copy restrictions. The content is NOT truly
encrypted — it's DRM-restricted. Both pdfplumber and pymupdf can read the text
content without needing to decrypt or alter the file.

Implement this cascade:

ATTEMPT 1 — pdfplumber (preferred)
  Try opening with pdfplumber.open(filepath).
  pdfplumber reads text layers directly and ignores DRM restrictions.
  Extract text page by page, preserving page numbers.
  Also extract tables using pdfplumber's table detection.
  If this returns meaningful text (not empty/garbled), use it.

ATTEMPT 2 — pymupdf (fitz)
  If pdfplumber returns empty or garbled text, try pymupdf.
  Open with fitz.open(filepath).
  pymupdf handles more encryption schemes for read-only access.
  Extract text with page.get_text("text") for each page.
  Also try page.get_text("dict") for structured block-level extraction.

ATTEMPT 3 — OCR fallback
  If both text extractors fail (likely a scanned image PDF), convert each page
  to an image using pymupdf's page.get_pixmap(), then run pytesseract.
  Flag these documents as "ocr_extracted" with a confidence penalty.

ATTEMPT 4 — Hybrid
  Some OS documents mix text pages with scanned appendix pages.
  Implement per-page detection: if a page yields < 50 characters of text
  from Attempts 1-2, run OCR on that specific page only.

For each PDF, produce an IngestionResult object:
{
  "source_file": "original_filename.pdf",
  "source_hash": "sha256 of original file (proves no modification)",
  "extraction_method": "pdfplumber" | "pymupdf" | "ocr" | "hybrid",
  "page_count": int,
  "pages": [
    {
      "page_number": int,
      "text": str,
      "tables": [extracted table data as list-of-lists],
      "extraction_method": str,
      "confidence": float  # 1.0 for text extraction, 0.7-0.9 for OCR
    }
  ],
  "metadata": {
    "title": str or null,    # from PDF metadata if available
    "author": str or null,
    "creation_date": str or null,
    "is_locked": bool,
    "encryption_type": str or null
  }
}

CRITICAL: After extraction, compute sha256 of the source file again and compare
to the hash taken before processing. Assert they match. This proves the file was
never modified. Log this verification.
```

### 1.3 Document Sectioning Engine

```
Build src/ingestion/section_detector.py

Municipal bond OS documents follow a highly predictable structure with
standard section headings. Build a section detector that identifies
and segments the document into logical sections using heading detection.

Standard OS sections to detect (in typical order):

COVER_PAGE
INTRODUCTION_AND_SUMMARY
TABLE_OF_CONTENTS
THE_BONDS (or "DESCRIPTION OF THE BONDS")
PLAN_OF_FINANCE (or "PLAN OF FINANCING")
SOURCES_AND_USES
THE_ISSUER
THE_PROJECT (or "THE FACILITY", "THE SYSTEM")
THE_BORROWER (or "THE COMPANY", "THE OBLIGOR")
SECURITY_FOR_THE_BONDS (or "SECURITY AND SOURCES OF PAYMENT")
FLOW_OF_FUNDS
RATE_COVENANT
ADDITIONAL_BONDS_TEST
DEBT_SERVICE_SCHEDULE
FINANCIAL_INFORMATION (or "FINANCIAL STATEMENTS")
RISK_FACTORS
TAX_MATTERS (or "TAX EXEMPTION")
LEGAL_MATTERS
UNDERWRITING
CONTINUING_DISCLOSURE
RATINGS
MISCELLANEOUS
APPENDIX_A (typically financial statements)
APPENDIX_B (typically indenture summary)
APPENDIX_C (typically legal opinion)
APPENDIX_D (typically continuing disclosure agreement)
APPENDIX_E (typically feasibility study or engineer's report)

For each detected section, store:
{
  "section_id": "SECURITY_FOR_THE_BONDS",
  "heading_text": "SECURITY AND SOURCES OF PAYMENT FOR THE BONDS",
  "start_page": int,
  "end_page": int,
  "text": full extracted text for this section,
  "subsections": [array of detected subsections with same structure]
}

Use regex patterns for heading detection (ALL CAPS lines, centered text,
numbered sections) combined with known heading vocabulary. Don't rely
solely on formatting — some PDFs lose formatting during extraction.
```

---

## PHASE 2 — EXTRACTION SCHEMA (THE DATA MODEL)

### 2.1 Core Deal Identity Schema

```
Build src/schema/deal_identity.py using Pydantic models.

This captures WHO, WHAT, WHERE, and WHEN for every deal:

class DealIdentity(BaseModel):
    # Document identification
    cusip_base: str | None          # 6-digit base CUSIP
    cusip_series: list[str]         # Individual CUSIP numbers per maturity
    document_type: Literal["OS", "POS", "supplement", "remarketing"]
    dated_date: date | None         # The "Dated Date" of the bonds
    sale_date: date | None          # Date bonds were sold
    delivery_date: date | None      # Closing/delivery date
    
    # Parties
    issuer_name: str                # Legal name of issuer
    issuer_type: Literal[
        "state", "county", "city", "town", "village",
        "special_district", "authority", "ida",
        "school_district", "utility", "housing", "health"
    ]
    issuer_state: str               # Two-letter state code
    issuer_county: str | None
    
    borrower_name: str | None       # Conduit borrower (if conduit deal)
    borrower_type: str | None       # Corporate, nonprofit, 501c3, etc.
    
    trustee_name: str | None
    bond_counsel: str | None
    underwriter_names: list[str]
    underwriter_counsel: str | None
    municipal_advisor: str | None
    disclosure_counsel: str | None
    paying_agent: str | None
    registrar: str | None
    verification_agent: str | None  # For SLB/green bonds
    
    # Series identification
    series_name: str                # e.g., "Series 2024A"
    official_title: str             # Full bond title from cover

WHY THIS MATTERS FOR BFMS:
- cusip_series lets you track secondary market trading and pricing comps
- Party identification lets you build an advisor/counsel network map
- issuer_type classification is critical for determining legal authority pathways
- borrower_type determines conduit vs. direct issuance analysis
- municipal_advisor tracking builds competitive intelligence
```

### 2.2 Deal Structure Schema

```
Build src/schema/deal_structure.py

class DealStructure(BaseModel):
    # Par amount and denomination
    par_amount: Decimal              # Total par amount
    denomination: Decimal            # Minimum denomination (typically $5,000)
    authorized_amount: Decimal | None # Max authorized if different from issued
    
    # Bond type classification
    bond_type: Literal[
        "general_obligation", "revenue", "conduit_revenue",
        "special_assessment", "tax_increment", "moral_obligation",
        "double_barrel", "lease_revenue", "certificates_of_participation",
        "industrial_development", "private_activity", "qualified_501c3"
    ]
    
    tax_status: Literal[
        "tax_exempt", "taxable", "alternative_minimum_tax",
        "bank_qualified", "federally_taxable_state_exempt"
    ]
    
    # Interest structure
    interest_type: Literal[
        "fixed_rate", "variable_rate", "capital_appreciation",
        "convertible_cab", "zero_coupon", "stepped_coupon",
        "index_linked", "auction_rate"
    ]
    
    # CAB-specific (extract when present)
    cab_enabled: bool
    cab_accretion_rate: Decimal | None
    cab_accretion_frequency: str | None     # "semiannual", "annual"
    cab_accretion_period_years: int | None
    cab_conversion_date: date | None
    cab_maturity_value: Decimal | None      # Accreted value at maturity
    cab_original_issue_price: Decimal | None
    
    # Sustainability / ESG features
    slb_enabled: bool
    green_bond: bool
    social_bond: bool
    sustainability_bond: bool
    slb_kpis: list[SLBKpi]                 # Defined below
    slb_step_up_bps: Decimal | None
    slb_step_down_bps: Decimal | None
    slb_observation_dates: list[date]
    slb_verification_agent: str | None
    slb_second_party_opinion: str | None   # Provider name
    
    # Maturity structure
    maturity_type: Literal[
        "serial", "term", "serial_and_term", "bullet",
        "capital_appreciation", "convertible"
    ]
    final_maturity_date: date
    weighted_average_maturity: Decimal | None  # In years
    
    # Call provisions
    optional_redemption_date: date | None
    optional_redemption_price: Decimal | None  # As % of par
    make_whole_call: bool
    extraordinary_redemption: bool
    mandatory_sinking_fund: bool
    turbo_redemption: bool                     # Excess cash flow sweep
    
    # Credit enhancement
    credit_enhancement_type: Literal[
        "none", "bond_insurance", "letter_of_credit",
        "standby_purchase_agreement", "state_enhancement",
        "moral_obligation", "federal_guarantee"
    ] | None
    credit_enhancer_name: str | None
    insurer_rating: str | None

WHY THIS MATTERS FOR BFMS:
- interest_type classification feeds directly into your CAB detection logic
- slb_kpis provide the sustainability framework your system needs to structure
  UCS deals with verifiable environmental targets
- Call provisions determine refinancing optionality for multi-system scaling
- credit_enhancement_type affects pricing spread analysis
- turbo_redemption is specific to project finance revenue bonds and maps directly
  to your existing schema's cab.turbo.enabled path
```

### 2.3 Maturity Schedule Schema

```
Build src/schema/maturity_schedule.py

class MaturityRow(BaseModel):
    maturity_date: date
    par_amount: Decimal
    coupon_rate: Decimal           # As percentage
    yield_to_maturity: Decimal | None
    price: Decimal | None          # As percentage of par (e.g., 100.00)
    cusip: str | None
    serial_or_term: Literal["serial", "term"]
    accreted_value: Decimal | None  # For CABs at maturity
    original_issue_discount: bool
    original_issue_premium: bool

class MaturitySchedule(BaseModel):
    rows: list[MaturityRow]
    total_par: Decimal
    true_interest_cost: Decimal | None   # TIC as percentage
    net_interest_cost: Decimal | None    # NIC as percentage
    all_in_tic: Decimal | None           # Including costs of issuance
    average_coupon: Decimal | None
    average_life: Decimal | None         # In years

WHY THIS MATTERS FOR BFMS:
- The maturity schedule IS the deal's DNA. Every comp, every pricing analysis,
  every synthetic deal generation starts from maturity schedules.
- Extracting yield curves from multiple OS documents lets you build empirical
  spread curves for your specific deal type (IDA revenue bonds).
- Accreted values for CABs feed directly into your accretion schedule logic.
- TIC/NIC are the universal cost-of-capital benchmarks.
```

### 2.4 Security & Collateral Schema

```
Build src/schema/security.py

class SecurityPackage(BaseModel):
    # Revenue pledge
    pledge_type: Literal["gross_revenue", "net_revenue", "specific_revenue", "none"]
    pledged_revenues_description: str        # Narrative description of what's pledged
    
    # Lien position
    lien_position: Literal["first", "second", "pari_passu", "subordinate"]
    senior_debt_outstanding: Decimal | None  # Amount of senior liens if subordinate
    
    # Real property security
    real_property_mortgage: bool
    real_property_description: str | None
    
    # Equipment / personal property
    equipment_security_interest: bool        # UCC-1 filing
    equipment_description: str | None
    
    # Revenue-specific pledges
    offtake_agreements_assigned: bool
    offtake_counterparties: list[str]
    
    # Financial covenants (these are critical for pattern analysis)
    rate_covenant: RateCovenant | None
    additional_bonds_test: AdditionalBondsTest | None
    
    # Reserve requirements
    debt_service_reserve_fund: DebtServiceReserve | None
    operating_reserve: Decimal | None
    renewal_replacement_fund: Decimal | None
    
    # Insurance requirements
    required_insurance_types: list[str]      # Property, liability, BI, etc.
    minimum_coverage_amount: Decimal | None

class RateCovenant(BaseModel):
    """The rate covenant is the issuer's promise to maintain sufficient rates/fees
    to generate enough revenue to meet debt service coverage requirements."""
    covenant_type: Literal["rate", "coverage", "rate_and_coverage"]
    minimum_coverage_ratio: Decimal          # e.g., 1.25x
    coverage_calculation_basis: str          # How net revenues are defined
    additional_revenue_test: Decimal | None  # For additional bonds
    consultant_rate_study_required: bool
    cure_period_days: int | None

class AdditionalBondsTest(BaseModel):
    """Rules governing when the issuer can issue additional parity debt."""
    historical_coverage_required: Decimal | None   # e.g., 1.25x on historical
    projected_coverage_required: Decimal | None    # e.g., 1.20x on projected
    lookback_period_years: int | None
    projection_period_years: int | None
    consultant_certification_required: bool
    
class DebtServiceReserve(BaseModel):
    requirement_type: Literal[
        "maximum_annual_debt_service", "average_annual_debt_service",
        "percent_of_par", "fixed_amount", "lesser_of_three_prong"
    ]
    amount: Decimal | None
    funded_at_closing: bool
    surety_bond_permitted: bool

WHY THIS MATTERS FOR BFMS:
- DSCR covenants are THE most important structural comparator across deals.
  Your system already uses 1.35x as the UCS target — pattern analysis across
  hundreds of OS documents will tell you where that sits in the market.
- Additional bonds tests determine scaling capacity for multi-system issuance.
- Reserve requirements affect sizing. The "lesser of three prong" test is the
  IRC §148(d) standard — extracting this tells you if a deal was tax-exempt.
- Rate covenant structures reveal how aggressive or conservative the issuer is.
```

### 2.5 Financial Performance Schema

```
Build src/schema/financials.py

class HistoricalFinancials(BaseModel):
    """Extracted from Appendix A or Financial Information section."""
    fiscal_year_end: str                     # e.g., "June 30" or "December 31"
    years_reported: list[int]                # e.g., [2019, 2020, 2021, 2022, 2023]
    
    # Revenue data by year
    gross_revenues: dict[int, Decimal]
    operating_expenses: dict[int, Decimal]
    net_revenues: dict[int, Decimal]         # Gross - O&M
    
    # Debt service coverage history
    annual_debt_service: dict[int, Decimal]
    dscr_historical: dict[int, Decimal]      # Net Revenue / Debt Service
    
    # Other key metrics
    operating_ratio: dict[int, Decimal] | None  # O&M / Gross Revenue
    days_cash_on_hand: dict[int, int] | None
    
    # Audit information
    auditor_name: str | None
    audit_opinion_type: Literal[
        "unmodified", "qualified", "adverse", "disclaimer"
    ] | None
    going_concern_flag: bool

class ProjectedFinancials(BaseModel):
    """Extracted from feasibility study or financial projections section."""
    projection_years: list[int]
    projected_revenues: dict[int, Decimal]
    projected_expenses: dict[int, Decimal]
    projected_net_revenues: dict[int, Decimal]
    projected_debt_service: dict[int, Decimal]
    projected_dscr: dict[int, Decimal]
    
    # Assumptions underpinning projections
    revenue_growth_rate: Decimal | None
    expense_escalation_rate: Decimal | None
    inflation_assumption: Decimal | None
    capacity_utilization_assumed: Decimal | None

class DebtServiceSchedule(BaseModel):
    """Year-by-year debt service table — almost always present in an OS."""
    rows: list[DebtServiceRow]
    total_principal: Decimal
    total_interest: Decimal
    total_debt_service: Decimal
    maximum_annual_debt_service: Decimal    # "MADS" — critical for reserve sizing

class DebtServiceRow(BaseModel):
    fiscal_year: int
    principal: Decimal
    interest: Decimal
    total: Decimal
    outstanding_balance: Decimal | None

WHY THIS MATTERS FOR BFMS:
- Historical DSCR trends across comparable deals provide the empirical basis
  for setting your UCS covenant at 1.35x (or adjusting it).
- Operating ratios tell you how efficient comparable projects are — your
  UCS system targets 58.7% operating margin; pattern data validates this.
- MADS determines reserve requirements and affects bond sizing.
- Audit opinion types flag credit risk — going concern flags are deal-killers.
- Projected vs. actual performance (from refunding OS documents that show
  historical actuals on previously projected projects) is gold for calibrating
  your own financial model assumptions.
```

### 2.6 Risk Factors Schema

```
Build src/schema/risk_factors.py

class RiskFactor(BaseModel):
    category: Literal[
        "construction", "technology", "market_demand", "regulatory",
        "environmental", "competition", "management", "financial",
        "interest_rate", "tax_law", "force_majeure", "political",
        "feedstock_supply", "offtake_counterparty", "permitting",
        "litigation", "labor", "insurance", "cybersecurity",
        "climate", "pandemic"
    ]
    title: str                               # Short risk title
    description: str                         # Full risk description
    severity_implied: Literal[               # Inferred from language/position
        "boilerplate", "material", "significant"
    ]
    mitigation_described: bool               # Does the OS describe mitigation?
    mitigation_text: str | None
    
class RiskFactorProfile(BaseModel):
    risks: list[RiskFactor]
    total_risk_factors_count: int
    unique_categories: list[str]
    has_project_specific_risks: bool         # Beyond standard boilerplate
    has_technology_risk: bool                # Critical for UCS comps
    has_construction_risk: bool
    has_environmental_compliance_risk: bool

WHY THIS MATTERS FOR BFMS:
- Risk factor language is heavily templated across deals, but project-specific
  risk factors reveal what's truly different about a deal.
- For UCS, technology risk and feedstock supply risk are your highest-priority
  comparators. Finding how other deals with novel technology disclosed these
  risks gives you disclosure drafting templates.
- The severity classification (boilerplate vs. material vs. significant) based
  on language intensity and ordering position helps you calibrate your own
  risk factor drafting for the disclosure outline.
```

### 2.7 Sources & Uses Schema

```
Build src/schema/sources_uses.py

class SourcesAndUses(BaseModel):
    # Sources
    bond_proceeds: Decimal
    original_issue_premium: Decimal | None
    original_issue_discount: Decimal | None
    equity_contribution: Decimal | None
    other_sources: dict[str, Decimal]        # Named sources
    total_sources: Decimal
    
    # Uses
    project_fund_deposit: Decimal | None     # Construction/acquisition
    debt_service_reserve_deposit: Decimal | None
    capitalized_interest: Decimal | None     # Important for CABs
    costs_of_issuance: Decimal | None
    underwriter_discount: Decimal | None
    other_uses: dict[str, Decimal]
    total_uses: Decimal
    
    # Derived metrics (calculate after extraction)
    cost_of_issuance_percentage: Decimal | None  # COI / Par Amount
    underwriter_spread_per_bond: Decimal | None  # Discount / Par * 1000

WHY THIS MATTERS FOR BFMS:
- Costs of issuance as a percentage of par is your best benchmarking metric
  for estimating deal costs before you have underwriter bids.
- Capitalized interest reveals how long the project expects zero cash flow —
  directly comparable to your CAB accretion period assumptions.
- Equity contribution percentages across deals tell you what the market
  expects for leverage in project finance revenue bonds.
```

### 2.8 Additional Fields You Should Extract (Not Referenced But Critical)

```
Build src/schema/additional_intelligence.py

These fields are NOT typically requested but provide outsized analytical value
for a bond facility management system:

class ContinuingDisclosureProfile(BaseModel):
    """What ongoing reporting the issuer committed to — this tells you what
    data will be publicly available post-issuance for monitoring."""
    annual_filing_required: bool
    annual_filing_contents: list[str]        # What's included
    material_event_notices: bool
    emma_filing_commitment: bool             # MSRB EMMA system
    prior_compliance_history: str | None     # "No failures" or description
    
class RatingProfile(BaseModel):
    """Credit ratings at issuance — the single best credit quality signal."""
    ratings: list[Rating]
    underlying_rating: str | None            # Before enhancement
    enhanced_rating: str | None              # After insurance/LOC
    outlook: str | None                      # Stable, positive, negative
    
class Rating(BaseModel):
    agency: Literal["moodys", "sp", "fitch", "kroll"]
    rating: str                              # e.g., "Baa2", "BBB+", "A-"
    outlook: str | None
    
class FlowOfFunds(BaseModel):
    """The cash waterfall — priority of payments from pledged revenues.
    This is the structural backbone of any revenue bond."""
    waterfall_steps: list[WaterfallStep]
    trapped_cash_provisions: bool
    sweep_to_equity_permitted: bool
    
class WaterfallStep(BaseModel):
    priority: int                            # 1 = highest priority
    fund_name: str                           # e.g., "Revenue Fund", "O&M Fund"
    description: str
    amount_or_formula: str                   # e.g., "1/12 of annual DS"

class LegalProvisions(BaseModel):
    """Key legal terms that affect deal flexibility and risk."""
    governing_law_state: str
    events_of_default: list[str]             # Enumerated default triggers
    remedies_upon_default: list[str]         # Acceleration, receivership, etc.
    bondholders_rights: str | None           # Percentage needed for action
    amendment_provisions: str | None         # Consent thresholds
    defeasance_permitted: bool               # Can bonds be defeased?
    defeasance_type: Literal[
        "legal", "economic", "crossover", "not_permitted"
    ] | None
    
class DemographicContext(BaseModel):
    """For GO and essential-service revenue bonds, demographic and economic
    data about the service area. Useful for credit comparisons."""
    population: int | None
    median_household_income: Decimal | None
    unemployment_rate: Decimal | None
    top_taxpayers: list[str] | None
    top_employers: list[str] | None
    assessed_valuation: Decimal | None       # For GO/tax-backed bonds
    
class RefundingInfo(BaseModel):
    """If this is a refunding deal, what's being refunded.
    Refunding deals reveal actual vs. projected performance of prior bonds."""
    is_refunding: bool
    refunding_type: Literal[
        "advance_refunding", "current_refunding", 
        "crossover_refunding", "none"
    ]
    refunded_bonds_series: list[str]
    refunded_bonds_original_par: Decimal | None
    present_value_savings: Decimal | None
    savings_as_percentage: Decimal | None
    negative_arbitrage: Decimal | None

class UnderwritingTerms(BaseModel):
    """Pricing and distribution details — feeds market intelligence."""
    sale_type: Literal["competitive", "negotiated", "private_placement"]
    underwriter_discount_per_bond: Decimal | None  # Per $1,000
    management_fee: Decimal | None
    takedown: Decimal | None
    total_spread: Decimal | None
    reoffering_yields: list[Decimal] | None        # Yield curve at reoffering

WHY THESE MATTER:
- Continuing disclosure commitments tell you what monitoring data will exist on EMMA.
- Ratings are the market's credit assessment — build a lookup table of ratings 
  by deal type, size, and structure for your own credit positioning.
- Flow of funds waterfall is essential for structuring your UCS cash flow cascade.
  Extracting these from 50+ deals gives you the patterns to model correctly.
- Defeasance provisions matter for multi-system scaling — if System 1 bonds can
  be defeased when System 3 comes online, your revolving structure works.
- Refunding deals are information goldmines: they contain both the original deal
  terms AND actual performance history, letting you validate financial projections.
- Underwriting spreads by deal type and size give you cost-of-issuance estimates
  before engaging an underwriter.
```

---

## PHASE 3 — INTELLIGENT EXTRACTION ENGINE

### 3.1 Extraction Architecture

```
Build src/extraction/base_extractor.py

Design the extraction engine with two tiers:

TIER 1 — DETERMINISTIC EXTRACTORS (regex + table parsing)
  These handle structured, predictable data that appears in standard formats:
  - CUSIP numbers (regex: 6-character base + 3-character suffix)
  - Par amounts from cover page (regex: "$XX,XXX,XXX")
  - Maturity tables (tabula-py or pdfplumber table extraction)
  - Debt service schedules (table extraction)
  - Sources & Uses tables (table extraction)
  - Dated date, delivery date, sale date (date regex in known locations)
  - Rating mentions ("Moody's: Baa2", "S&P: BBB+")
  
TIER 2 — AI-ASSISTED EXTRACTORS (Claude API)
  These handle unstructured narrative text requiring comprehension:
  - Security package description (complex legal narrative)
  - Covenant terms and thresholds
  - Risk factor classification
  - Flow of funds waterfall (narrative descriptions of priority)
  - SLB KPI definitions and targets
  - Party identification from cover/intro
  - Borrower/project descriptions
  - Legal provisions (default, remedies, defeasance)

For Tier 2, use the Anthropic API with structured outputs.
Build each AI extractor as a class that:
  1. Receives the relevant section text (not the whole document)
  2. Sends a constrained prompt to Claude asking for specific fields
  3. Requires JSON output matching the Pydantic schema
  4. Validates the response against the schema
  5. Assigns a confidence score (0.0-1.0) to each extracted field
  6. Flags low-confidence extractions for human review

Example AI extractor prompt pattern:

  SYSTEM: You are a municipal bond analyst extracting structured data from
  Official Statement text. Extract ONLY what is explicitly stated. If a field
  is not present in the text, return null. Never infer or estimate values.
  
  USER: Extract the security package from the following Official Statement
  section titled "SECURITY AND SOURCES OF PAYMENT":
  
  [section text]
  
  Return a JSON object with these exact fields:
  {
    "pledge_type": "gross_revenue" | "net_revenue" | "specific_revenue" | "none",
    "pledged_revenues_description": "description or null",
    "lien_position": "first" | "second" | "pari_passu" | "subordinate",
    ...
  }
  
  For each field, also provide a confidence score 0.0-1.0 in a parallel
  "_confidence" object.

CRITICAL CONSTRAINT: Each AI extractor must include in its system prompt:
"Do not hallucinate. Do not infer. If the text does not explicitly state a
value, return null. A null extraction is always preferable to a guessed one."

This aligns with your BFMS's evidence-first principle.
```

### 3.2 Table Extraction Engine

```
Build src/extraction/table_extractor.py

Municipal bond OS documents contain several critical tables that MUST be
extracted accurately. These are the highest-value structured data:

TABLE TYPE 1: Maturity Schedule (appears on cover or early pages)
  - Columns: Maturity Date | Amount | Rate | Yield | Price | CUSIP
  - Detect by: proximity to "MATURITY SCHEDULE" heading, or presence of
    CUSIP-formatted strings in a table
  - Handle: CAB tables where "Yield" column becomes "Accreted Value at Maturity"
  - Handle: Split serial/term bond tables

TABLE TYPE 2: Debt Service Schedule (usually in body or appendix)
  - Columns: Year | Principal | Interest | Total | Balance
  - Detect by: heading "DEBT SERVICE SCHEDULE" or "ANNUAL DEBT SERVICE"
  - Special: Aggregate debt service tables that include existing + new debt

TABLE TYPE 3: Sources and Uses (early in document)
  - Two-column format: Sources on left, Uses on right (or stacked)
  - Detect by: heading or "$" amounts with "Bond Proceeds", "Project Fund"

TABLE TYPE 4: Historical Financial Data (Appendix A or Financial section)
  - Multi-year tables of revenues, expenses, coverage
  - Detect by: 3-5 column year headers, revenue/expense line items

TABLE TYPE 5: Top Taxpayers / Top Employers (demographic section)
  - Names and assessed values or employee counts
  - Detect by: "TEN LARGEST" heading pattern

For each table type, implement:
  1. Detection: Is this table present? Which pages?
  2. Extraction: Parse rows/columns into structured data
  3. Validation: Do columns sum correctly? Do totals match stated totals?
  4. Normalization: Convert to the matching Pydantic schema

Handle common table extraction failures:
  - Merged cells (especially in header rows)
  - Footnote rows that break table structure
  - Tables that span page breaks
  - Tables with subtotal rows that shouldn't be treated as data rows
  - Dollar amounts with parentheses indicating negative values
```

### 3.3 Extraction Orchestrator

```
Build src/extraction/orchestrator.py

The orchestrator manages the full extraction pipeline for one document:

1. INGEST: Read PDF → get IngestionResult with page-level text + tables
2. SECTION: Run section detector → get SectionMap
3. EXTRACT-DETERMINISTIC: Run all Tier 1 extractors on their target sections
4. EXTRACT-AI: Run all Tier 2 extractors on their target sections
5. CROSS-VALIDATE: Compare deterministic vs. AI results where overlap exists
6. ASSEMBLE: Merge all extractions into a single DealRecord
7. SCORE: Compute completeness score (% of schema fields populated)
8. EXPORT: Write to JSON + SQLite

The DealRecord is the master output object:

class DealRecord(BaseModel):
    # Metadata
    extraction_id: str                       # UUID
    source_file: str
    source_hash: str
    extraction_timestamp: datetime
    extraction_version: str                  # Software version
    completeness_score: float                # 0.0-1.0
    confidence_scores: dict[str, float]      # Per-field confidence
    
    # Extracted content
    identity: DealIdentity
    structure: DealStructure
    maturity_schedule: MaturitySchedule | None
    security: SecurityPackage | None
    financials_historical: HistoricalFinancials | None
    financials_projected: ProjectedFinancials | None
    debt_service: DebtServiceSchedule | None
    risk_factors: RiskFactorProfile | None
    sources_uses: SourcesAndUses | None
    flow_of_funds: FlowOfFunds | None
    legal_provisions: LegalProvisions | None
    continuing_disclosure: ContinuingDisclosureProfile | None
    ratings: RatingProfile | None
    demographics: DemographicContext | None
    refunding: RefundingInfo | None
    underwriting: UnderwritingTerms | None
    
    # Fields needing human review
    review_flags: list[ReviewFlag]

class ReviewFlag(BaseModel):
    field_path: str                          # e.g., "security.rate_covenant.minimum_coverage_ratio"
    issue: str                               # e.g., "Value extracted as 1.25 but also found 1.20 in different section"
    confidence: float
    suggested_value: Any
    alternative_value: Any | None
```

---

## PHASE 4 — CLASSIFICATION & PATTERN ENGINE

### 4.1 Deal Classifier

```
Build src/classification/deal_classifier.py

After extraction, classify each deal into a taxonomy for pattern analysis:

PRIMARY CLASSIFICATION (by security type):
  GO_UNLIMITED, GO_LIMITED, REVENUE_WATER_SEWER, REVENUE_ELECTRIC,
  REVENUE_HEALTHCARE, REVENUE_HIGHER_ED, REVENUE_HOUSING,
  REVENUE_TRANSPORTATION, REVENUE_AIRPORT, REVENUE_PORT,
  REVENUE_SOLID_WASTE, REVENUE_INDUSTRIAL_DEVELOPMENT,
  TAX_INCREMENT, SPECIAL_ASSESSMENT, LEASE_REVENUE, COPs,
  CONDUIT_501C3, CONDUIT_INDUSTRIAL, PRIVATE_ACTIVITY

SECONDARY CLASSIFICATION (by structural features):
  FIXED_RATE, VARIABLE_RATE, CAB, CONVERTIBLE_CAB,
  GREEN_BOND, SOCIAL_BOND, SUSTAINABILITY_LINKED,
  REFUNDING_ADVANCE, REFUNDING_CURRENT, NEW_MONEY,
  COMBINED_REFUNDING_NEW_MONEY

TERTIARY CLASSIFICATION (by credit quality):
  INVESTMENT_GRADE_HIGH (AAA-AA), INVESTMENT_GRADE_MID (A),
  INVESTMENT_GRADE_LOW (BBB), NON_RATED, BELOW_INVESTMENT_GRADE

SIZE CLASSIFICATION:
  MICRO (<$10M), SMALL ($10-50M), MEDIUM ($50-250M),
  LARGE ($250M-1B), JUMBO (>$1B)

Store classification alongside the DealRecord for filtering and comparison.
```

### 4.2 Comparable Deal Engine

```
Build src/analysis/comp_engine.py

Given a target deal profile (e.g., your UCS CAB+SLB revenue bond), find and
rank the most comparable deals from the extracted corpus:

COMPARISON DIMENSIONS (weighted):
  1. Bond type match (0.25 weight)
  2. Tax status match (0.15)
  3. Size similarity (0.15)
  4. Interest structure match (0.15) — CAB to CAB is high-value comp
  5. Issuer type match (0.10) — IDA to IDA
  6. Geographic proximity (0.05)
  7. Credit quality match (0.10)
  8. ESG/SLB feature match (0.05) — SLB to SLB

For each comparable deal, compute:
  - Overall similarity score (0.0-1.0)
  - Spread to benchmark (if yield data available)
  - DSCR covenant comparison
  - Cost of issuance comparison
  - Structure comparison narrative (AI-generated)

Output format:
{
  "target_deal": "UCS CAB+SLB Revenue Bonds, Series 2026",
  "comparables": [
    {
      "deal_name": "...",
      "similarity_score": 0.87,
      "key_similarities": ["CAB structure", "IDA issuer", "similar par amount"],
      "key_differences": ["No SLB features", "Term bonds only"],
      "pricing_data": { ... },
      "covenant_comparison": { ... }
    }
  ]
}
```

### 4.3 Pattern Detection

```
Build src/analysis/pattern_detector.py

Run statistical analysis across the corpus to surface patterns:

PATTERN TYPE 1: Covenant Norms
  - Median DSCR covenant by deal type and size
  - Median additional bonds test by deal type
  - Reserve fund sizing norms (MADS vs. AADS vs. % of par)
  - Distribution charts of covenant levels

PATTERN TYPE 2: Pricing Patterns
  - Spread relationships: CAB vs. fixed rate for similar credit
  - SLB greenium quantification (with vs. without ESG features)
  - Size premium/discount effects
  - State/regional pricing differences

PATTERN TYPE 3: Structural Patterns
  - Most common call provisions by deal type
  - Typical capitalized interest periods for project finance bonds
  - Common flow-of-funds structures for revenue bonds
  - Insurance usage rates by credit quality tier

PATTERN TYPE 4: Disclosure Patterns
  - Most common risk factor categories by deal type
  - Risk factor count norms by deal complexity
  - Appendix structure patterns
  - Continuing disclosure commitment patterns

Store pattern results as versioned snapshots so trends over time are visible.
```

---

## PHASE 5 — SYNTHETIC DATA ENGINE

### 5.1 Synthetic Deal Generator

```
Build src/synthetic/deal_generator.py

Purpose: Generate realistic but fictional bond deal structures for testing,
training, and scenario analysis. Every synthetic deal should be plausible
but never represent a real transaction.

GENERATION APPROACH:

1. DISTRIBUTION-BASED GENERATION
   From the extracted corpus, compute distributions for every numeric field:
   - Par amount distributions by deal type
   - Coupon rate distributions by credit quality and maturity
   - DSCR covenant distributions by bond type
   - Cost of issuance percentages
   - Revenue/expense ratio distributions
   
   Use these distributions to sample realistic values for new synthetic deals.

2. STRUCTURAL COHERENCE RULES
   Enforce internal consistency:
   - Sources must equal Uses
   - Debt service schedule must amortize to zero
   - DSCR must be calculable from revenue and debt service
   - Maturity schedule par amounts must sum to total par
   - Interest amounts must be mathematically correct given coupon rates
   - CAB accretion values must follow compound interest formula
   - SLB step-up penalties should be in the empirical range (25-50 bps)

3. SCENARIO MODES
   Allow generation of synthetic deals in specific modes:
   
   MODE A — "Clone with variations"
     Take a real DealRecord, perturb key parameters (par amount ±20%,
     coupons ±50bps, DSCR ±0.10x), change all identifying information.
   
   MODE B — "Archetype generation"
     Given a deal type + credit quality + size band, generate a complete
     synthetic deal that matches the statistical profile of that category.
   
   MODE C — "Stress scenarios"
     Generate synthetic deals that represent edge cases:
     - Minimum DSCR (just barely meeting covenant)
     - Maximum leverage (minimum equity)
     - Worst-case revenue ramp (delayed 2 years)
     - Interest rate shock (+200bps)

4. OUTPUT
   Each synthetic deal gets a DealRecord with:
   - is_synthetic: true
   - generation_mode: str
   - seed_deal_hash: str or null (if cloned from real deal)
   - All the same schema fields as a real extraction
   
   Synthetic deals are stored separately in data/synthetic/ and are
   clearly marked to prevent contamination of the real corpus.
```

---

## PHASE 6 — STORAGE & CLI

### 6.1 SQLite Storage Layer

```
Build src/storage/database.py

Create a SQLite database (bond_corpus.db) with tables mirroring the schemas:

Core tables:
  deals              — One row per DealRecord (deal_id, source_file, hash, etc.)
  deal_identities    — Party information, CUSIPs
  deal_structures    — Bond type, tax status, CAB/SLB features
  maturity_rows      — One row per maturity date (linked to deal_id)
  security_packages  — Pledge type, liens, covenants
  covenant_details   — Rate covenants, additional bonds tests
  financials         — Historical and projected by year
  debt_service_rows  — Annual debt service by year
  risk_factors       — One row per risk factor per deal
  sources_uses       — Sources and uses line items
  flow_of_funds      — Waterfall steps by deal
  ratings            — Rating by agency per deal
  classifications    — Deal type, size, credit classifications

Lookup tables:
  issuers            — Deduplicated issuer names/states
  parties            — Deduplicated trustees, counsel, underwriters
  
Synthetic table:
  synthetic_deals    — Same structure as deals but clearly separated

Index heavily on:
  - bond_type, tax_status, interest_type (for comp queries)
  - issuer_state, par_amount (for filtering)
  - dscr_covenant (for pattern analysis)
  - extraction_timestamp (for corpus versioning)

Include views:
  - v_deal_summary: One-row-per-deal with key metrics flattened
  - v_covenant_comparison: DSCR and ABT across all deals
  - v_pricing_comps: Yield/spread data for extracted deals
```

### 6.2 CLI Interface

```
Build src/cli.py using argparse or click:

Commands:

  bond-extract ingest <pdf_path_or_directory>
    Runs the full pipeline on one PDF or all PDFs in a directory.
    Outputs JSON to data/extracted/ and inserts into SQLite.
    
  bond-extract status
    Shows corpus statistics: total deals, by type, completeness scores.
    
  bond-extract search --type <bond_type> --min-par <amount> --max-par <amount>
      --state <state> --cab --slb --min-dscr <ratio>
    Queries the corpus with filters, returns matching deals.
    
  bond-extract comps --target <deal_id_or_json>
    Runs the comparable deal engine against the corpus.
    
  bond-extract patterns --type <bond_type>
    Runs pattern analysis and outputs statistical summaries.
    
  bond-extract synthesize --mode <clone|archetype|stress>
      --type <bond_type> --count <n>
    Generates synthetic deals.
    
  bond-extract export --format <json|csv|xlsx> --query <filter>
    Exports filtered corpus data for external use.

  bond-extract validate <deal_id>
    Re-validates a previously extracted deal against current schema.
    Useful after schema updates.
```

---

## PHASE 7 — INTEGRATION HOOKS FOR BFMS

### 7.1 Schema Mapping to Existing BFMS Paths

```
Build src/integration/bfms_mapper.py

Map extracted fields to your existing BFMS schema paths so the extractor
output can feed directly into the Bond Intelligence system:

EXTRACTION FIELD                    → BFMS SCHEMA PATH
-------------------------------------------------------------------
structure.cab_enabled               → cab.enabled
structure.cab_accretion_rate        → cab.accretionrate
structure.cab_accretion_period      → cab.accretion.period.years
structure.cab_conversion_date       → cab.conversion.trigger
identity.par_amount                 → cab.originalprincipal
structure.final_maturity_date       → cab.finalmaturitydate
structure.turbo_redemption          → cab.turbo.enabled
structure.slb_enabled               → slb.enabled
structure.slb_kpis                  → slb.kpis.shortlist
structure.slb_step_up_bps           → slb.penalty.stepup.magnitude
security.pledge_type                → security.revenue.pledge
security.real_property_mortgage     → security.realproperty
security.equipment_security         → security.equipment.schedule
financials.dscr_historical          → finmodel.outputs.dscrbase
security.rate_covenant.min_coverage → finmodel.inputs.dscr.minimum
financials.gross_revenues           → revenue.gross.annual
financials.operating_expenses       → opex.total.annual

This mapping layer allows you to:
1. Import comparable deal data into your existing BFMS for side-by-side analysis
2. Pre-populate BFMS schema paths from a comparable deal template
3. Validate your UCS deal parameters against market norms
```

---

## IMPLEMENTATION NOTES

### Execution Order

Build and test in this sequence:
1. Phase 1 (ingestion) — verify you can read locked PDFs
2. Phase 2 (schemas) — define all Pydantic models
3. Phase 3.2 (tables) — tables are highest-value, most deterministic
4. Phase 3.1 (AI extractors) — one extractor at a time, test against real OS docs
5. Phase 3.3 (orchestrator) — wire everything together
6. Phase 6 (storage + CLI) — make it usable
7. Phase 4 (analysis) — only after you have 10+ deals extracted
8. Phase 5 (synthetic) — only after patterns are validated
9. Phase 7 (BFMS integration) — after extraction is stable

### Testing Strategy

For each phase, test against at least 3 real OS PDFs with different characteristics:
- One "clean" text-based PDF (easy case)
- One locked/restricted PDF (DRM test)
- One with scanned appendix pages (OCR test)

Municipal bond OS documents are publicly available on EMMA (emma.msrb.org).
Download a variety for testing.

### API Cost Management

The Claude API calls in Tier 2 extraction should be managed carefully:
- Send only the relevant section text, not the whole document
- Cache responses keyed by document hash + section hash + extractor version
- Use claude-sonnet-4-20250514 for extraction tasks (cost-effective, accurate)
- Reserve opus for ambiguous cross-validation tasks
- Estimated: ~$0.10-0.30 per OS document fully extracted

### Error Handling

Every extraction should be fault-tolerant:
- If one field fails, extract everything else
- Log failures with section text for debugging
- Never fail the whole document because one extractor errors
- Maintain a "partial extraction" state with completeness < 1.0
