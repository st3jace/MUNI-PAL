# Data Sources, Tools, and File Conventions

**Version:** 1.0 | **Created:** 2026-02-18
**Purpose:** Everything the research agent can access and how to use it

---

## 1. LOCAL DATA SOURCES

### 1.1 EMMA Bond Corpus (SQLite)

**Path**: `emma/bond_os_extractor/data/bond_corpus.db`

The primary structured data source for the waste/environmental sector. Contains extracted data from 200 EMMA bond issues (3,160 PDFs processed).

| Table | Records | Contents |
|-------|---------|----------|
| `official_statements` | 31 | Full OS extraction: CUSIP, par amount, dates, ratings, structure, covenants, financials |
| `risk_factors` | 311 | Categorized risk factors with severity and mitigation status |
| `rating_actions` | 370 | Rating agency actions with factors cited |
| `security_packages` | 104 | Security/collateral details with pledge types and enhancements |
| `financial_reports` | 116 | Extracted financial data (revenue, expenses, assets, liabilities, margins) |
| `rationale_summaries` | 31 | Credit rationale narratives |
| `credit_enhancements` | 26 | Enhancement type, provider, terms |
| `document_index` | ~3,160 | Cross-module document tracking (type routing, processing status) |
| `ai_cache` | varies | Cached AI extraction responses (keyed by doc_hash + section + extractor) |

**Access**: Direct SQLite queries via Python's `sqlite3` module, or through the data loader functions in `analysis/data_loader.py`.

**Key data loader functions** (in `emma/bond_os_extractor/src/analysis/data_loader.py`):
- `load_bond_corpus(db_path)` — All official statement extractions
- `load_risk_factors(db_path)` — Risk factors with categories and severity
- `load_rating_action_factors(db_path)` — Rating action factors by agency
- `load_security_packages(db_path)` — Security packages with pledge descriptions
- `load_financial_reports(db_path)` — Extracted financial report data
- `load_rationale_summaries(db_path)` — Credit rationale narratives
- `load_credit_enhancements(db_path)` — Enhancement details
- `load_equity_data(ticker_dir)` — Equity ticker price history and financials

### 1.2 Analysis Pipeline Outputs

**Path**: `emma/bond_os_extractor/data/analysis/`

JSON files produced by Phases 1-6 of the Summers methodology pipeline:

| File | Phase | Contents |
|------|-------|----------|
| `fundamental_scores.json` | 1 | F_i scores for 40 obligors across 5 dimensions |
| `s_omega_results.json` | 2 | S_Omega, SIC matrix, P_BSE for investable assets |
| `benchmark_results.json` | 3 | CRI rankings, relative value signals, benchmark composition |
| `hilbert_results.json` | 4 | Spectral entropy, SNR, wavelet coefficients, DMD eigenvalues |
| `extended_risk_results.json` | 5 | Spectral/Wavelet/Dynamic Omega, IRS scores |
| `risk_benchmark_report.json` | Risk | Corpus risk benchmarks by category |
| `risk_comparison_report.json` | Risk | Project vs. corpus comparison |
| `risk_implementation_guide.json` | Risk | Evidence-based implementation recommendations |

These files also have `.md` counterparts (human-readable reports) where applicable.

### 1.3 Equity Ticker Data (Waste Sector)

**Path**: `C:\Users\st3ja\OneDrive\Documents\PROJECTS\AZRFO\QF\WTE\waste_tickers\`

19 waste management sector equity tickers with associated data files:

| Ticker | Company | Data Available |
|--------|---------|---------------|
| WM | Waste Management | CSV financials + price history |
| RSG | Republic Services | XLSX + price history |
| GFL | GFL Environmental | XLSX + price history |
| CWST | Casella Waste Systems | XLSX + price history |
| CLH | Clean Harbors | XLSX + price history |
| WCN | Waste Connections | XLSX + price history |
| NVRI | Enviri Corporation | XLSX + price history |
| VLTO | Veralto | XLSX + price history |
| XYL | Xylem | XLSX + price history |
| ZWS | Zurn Elkay Water Solutions | XLSX + price history |
| WTTR | Select Water Solutions | XLSX + price history |
| SCWO | 374Water | XLSX + price history |
| QRHC | Quest Resource | XLSX + price history |
| MEG | Montrose Environmental | XLSX + price history |
| ESGL | ESGL Holdings | XLSX + price history |
| DXST | Daxos Therapeutics | XLSX + price history |
| CREG | China Recycling Energy | CSV financials + price history |
| YDDL | YDDL Holdings | XLSX + price history |

**Note**: Only WM and CREG have CSV-format financials directly consumable by the data loader. Others have XLSX financials requiring pandas/openpyxl for parsing. All have CSV price history files.

**File naming convention**: `{TICKER}/` subdirectory containing:
- `{TICKER}_history.csv` — Daily OHLCV price history
- `{TICKER}_financials.csv` or `{TICKER}_financials.xlsx` — Quarterly/annual financials

### 1.4 EMMA Crawler Output

**Path**: `emma/emma_crawler/output/`

| Resource | Path | Description |
|----------|------|-------------|
| Bond summary | `output/data/waste_bonds_summary.csv` | 200 waste sector bond issues with metadata |
| Downloaded PDFs | `output/downloads/{CUSIP9}/` | PDFs organized by 9-digit CUSIP |
| Trade data | `output/data/trades/` | Secondary market trade records |
| Rating history | `output/data/ratings/` | Historical rating data by issue |

### 1.5 Source PDFs

**Path**: `pdfs/`

Contains source PDF documents used for extraction testing. Note: these are generated report PDFs, not real official statement documents — extraction completeness will be lower than for authentic EMMA documents.

### 1.6 Summers Papers

**Path**: `files/`

| File | Paper |
|------|-------|
| `An Intuitive Total Risk-Adjusted Performance Measure and Characteristics Matrix-1.pdf` | Paper 1: S_Omega derivation, SIC matrix, MDDD_S |
| `Standard_Model_of_Complex_Economic_Systems.pdf.pdf` | Paper 2: Standard Model, Hilbert space methods, 95 citations |

Extractable via `pymupdf` (fitz). Both papers have been fully internalized into the analytical framework specification (`02-summers-analytical-framework.md`).

### 1.7 Configuration Playbook

**Path**: `UCS_Bond_Intelligence_Config_Playbook_v0.3.md`

The source of truth for Muni-Pal schema paths, extractor definitions, checklist framework, and readiness scoring dimensions. Contains:
- ~60 schema paths in 14 categories with criticality tiers (CRITICAL / MATERIAL / SECONDARY)
- Extractor definitions with confidence thresholds
- Phase-gated checklist items (P1-P6)
- Readiness dimension weights and scoring methodology

Previous version at `V1/UCS_Bond_Intelligence_Config_Playbook_v0.2.md`.

### 1.8 BFMS Build Specification

**Path**: `Muni-Pal — Bond Facility Management System (BFMS).md`

System architecture document defining invariants, evidence-first principles, and contract-first API design for the Muni-Pal platform.

### 1.9 Reference Books (DRM-Protected)

**Path**: `C:\Users\st3ja\OneDrive\Documents\My Digital Editions\`

CDFA guides and bond finance references protected by Adobe Digital Editions DRM (`EBX_HANDLER` encryption). These **cannot be read programmatically**.

**Protocol for DRM-protected references**:
1. The agent cannot access these files directly
2. If a reference book is needed, request the user provide relevant excerpts
3. The user can manually copy passages and paste them into the conversation or save them as plaintext in `research/corpus/references/`
4. Any excerpts provided should be cited with book title, chapter, and page number

---

## 2. TOOLS AND CLI

### 2.1 Bond OS Extractor CLI

**Working directory**: `emma/bond_os_extractor/`
**Invocation**: `python -m src.cli <command>`

#### Ingestion Commands

| Command | Description | Key Options |
|---------|-------------|-------------|
| `ingest <path>` | Ingest one PDF or directory of PDFs | `--no-ai`, `--no-db` |
| `ingest-all <path>` | Ingest all document types using module routing | `--all-types` |
| `test-ingest <path>` | Test PDF ingestion only (no extraction) | — |
| `clear-cache` | Clear AI response cache | `--older-than <days>` |

#### Corpus Query Commands

| Command | Description | Key Options |
|---------|-------------|-------------|
| `status` | Show corpus statistics | — |
| `module-status` | Show document module statistics | — |
| `search` | Search corpus with filters | `--bond-type`, `--state`, `--par-min`, `--par-max` |
| `export` | Export corpus data | `--format json\|csv` |

#### Summers Analysis Commands (Phases 1-5)

| Command | Phase | Description |
|---------|-------|-------------|
| `score` | 1 | Score obligor universe (fundamental screening, F_i) |
| `score-detail <obligor>` | 1 | Detailed scoring breakdown for one obligor |
| `s-omega` | 2 | Compute S_Omega for investable universe |
| `s-omega-detail <ticker>` | 2 | Detailed S_Omega analysis for one asset |
| `benchmark` | 3 | Construct sector benchmark and CRI ranking |
| `benchmark-detail <ticker>` | 3 | Detailed benchmark analysis for one asset |
| `signals` | 4 | Extract Hilbert space signals |
| `signal-detail <ticker>` | 4 | Detailed signal analysis for one asset |
| `full-analysis` | 1-5 | Run complete pipeline (Phases 1 through 5) |
| `bond-returns <obligor>` | 6 | Build synthetic bond return series |

#### Risk Benchmarking Commands

| Command | Description |
|---------|-------------|
| `risk-benchmark` | Build risk benchmarks from EMMA corpus |
| `risk-compare` | Compare project risk profile against corpus benchmarks |
| `risk-guide` | Generate risk mitigation implementation guide |

### 2.2 EMMA Crawler

**Working directory**: `emma/emma_crawler/`
**Entry point**: `src/main.py`

Playwright-based automated scraper for MSRB's EMMA portal. Capabilities:
- Multi-phase extraction (search → security detail → document download)
- Config-driven via YAML files (`search_params.yaml`, `crawler_settings.yaml`)
- Resume capability for interrupted crawls
- Retry logic for failed/partial extractions
- Tab-specific extractors: snapshot, trade_activity, ratings, disclosures, interest_rate

**Key modules**:
- `src/search.py` — EMMA search execution
- `src/results.py` — Results collection and processing
- `src/security_detail.py` — Security detail page extraction
- `src/session_manager.py` — Browser session management
- `src/storage.py` — Data persistence (CSV output)
- `src/tab_extractors/` — Individual tab extraction logic

**Usage note**: The crawler requires Playwright browsers installed (`playwright install chromium`). Crawling EMMA at scale should be done respectfully with appropriate delays to avoid rate limiting.

### 2.3 Analysis Modules (Python)

**Path**: `emma/bond_os_extractor/src/analysis/`

| Module | Purpose | Key Functions/Classes |
|--------|---------|----------------------|
| `scoring_engine.py` | Phase 1: Fundamental scoring (F_i) | `score_obligor()`, `score_universe()` |
| `omega.py` | Phase 2: S_Omega computation | `compute_s_omega()`, `compute_sic_matrix()` |
| `return_series.py` | Return series construction | `build_return_series()`, `merge_return_series()` |
| `benchmark.py` | Phase 3: CRI ranking | `construct_benchmark()`, `compute_cri()` |
| `hilbert.py` | Phase 4: Signal extraction | `fft_spectral()`, `dwt_wavelet()`, `dmd_koopman()` |
| `extended_risk.py` | Phase 5: Extended Omega variants | `compute_extended_risk()`, `compute_irs()` |
| `synthetic_returns.py` | Phase 6: Synthetic bond returns | `build_synthetic_returns()` (4-priority cascade) |
| `spread_table.py` | Rating-to-spread conversion | `get_spread_bps()` (S&P + Moody's scales) |
| `risk_benchmark.py` | Risk benchmarking | `build_risk_benchmark()`, `compare_project()`, `generate_guide()` |
| `data_loader.py` | Unified data loading | All `load_*()` functions (see Section 1.1) |
| `obligor_mapping.py` | Obligor identification | 18 known obligors with alias matching |
| `models.py` | Data models | Dataclasses for scoring, returns, signals |

### 2.4 Document Extraction Modules

**Path**: `emma/bond_os_extractor/src/modules/`

Pluggable module system with `DocumentModule` abstract base class and auto-discovery via `get_registry()`.

| Module | Path | Handles |
|--------|------|---------|
| `rating_action` | `modules/rating_action/` | Rating agency action notices |
| `event_filing` | `modules/event_filing/` | EMMA event filings (continuing disclosures) |
| `financial_report` | `modules/financial_report/` | 10-K/10-Q, municipal CAFRs |

Each module contains: `schema.py`, `extractor.py`, `storage.py`, `__init__.py`

Filename-based routing handles 90%+ of document classification without AI. OS-priority keywords bypass module routing.

### 2.5 Web Search

The agent has access to web search for:
- Current market data and conditions
- Rating agency publications and methodology updates
- Regulatory changes and new guidance
- Academic papers and preprints
- EMMA portal queries (for sectors not yet crawled)
- Industry association publications (GFOA, HFMA, NAHB)

**Best practices**:
- Always cite the source URL and access date
- Prefer official sources (MSRB, SEC, IRS, rating agencies) over secondary reporting
- For academic papers, check arXiv, SSRN, and author websites for open-access versions
- Cross-validate market data from multiple sources

### 2.6 SEC EDGAR

Accessible via web for:
- Continuing disclosure filings (annual reports, event notices)
- Municipal issuer financial statements
- 15c2-12 compliance filings
- CAFR and audit reports uploaded to EDGAR

**EDGAR search**: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=&dateb=&owner=include&count=40`

### 2.7 Muni-Pal Platform (Read-Only Reference)

The research agent does **not** modify the Muni-Pal platform code or database. However, it can reference the platform's structure for integration planning:

| Component | Path | Purpose |
|-----------|------|---------|
| Backend API | `src/munipal/` | FastAPI + SQLAlchemy + PostgreSQL |
| Frontend | `frontend/` | React 18 + TypeScript + Vite + Tailwind |
| Schemas | `src/munipal/core/schemas/` | Pydantic models for API contracts |
| Models | `src/munipal/core/models/` | SQLAlchemy ORM models |
| Services | `src/munipal/services/` | Business logic layer |
| Playbook data | `src/munipal/services/playbook_data.py` | Playbook phase definitions |
| Readiness scoring | `src/munipal/services/readiness_service.py` | 6-dimension readiness assessment |
| Routes | `src/munipal/api/routes/` | API endpoint definitions |

---

## 3. EXTERNAL DATA SOURCES (Web-Accessible)

### 3.1 MSRB EMMA Portal

**URL**: `https://emma.msrb.org/`

The Electronic Municipal Market Access system — primary source for:
- Official statements and preliminary official statements
- Continuing disclosures (annual financial information, event notices)
- Trade data (price, yield, par traded, trade date/time)
- Issuer information
- Credit ratings and rating actions

**Search capabilities**: By CUSIP, issuer name, state, bond type, date range, document type.

### 3.2 Rating Agency Public Resources

| Agency | Public Methodology Access | Municipal Sectors Covered |
|--------|--------------------------|---------------------------|
| Moody's | `moodys.com/research` | US Public Finance (hospitals, solid waste, state/local GOs, higher ed, utilities) |
| S&P Global | `spglobal.com/ratings` | US Public Finance criteria (health care, waste, water/sewer, special tax) |
| Fitch Ratings | `fitchratings.com` | US Public Finance (hospitals, senior living, solid waste, utilities) |
| Kroll (KBRA) | `kbra.com` | Emerging presence in municipal ratings |

**Key documents to seek**:
- Sector methodology reports (updated periodically)
- Rating criteria summaries
- Sector outlook reports (annual)
- Default and recovery studies (Moody's annual municipal default research)
- Median financial ratio reports (Moody's publishes annually for hospitals, higher ed, utilities)

### 3.3 Government Data Sources

| Source | URL | Data Available |
|--------|-----|---------------|
| IRS (Tax-Exempt Bonds) | `irs.gov/tax-exempt-bonds` | IRC guidance, TEB compliance, arbitrage rules |
| SEC (Municipal Securities) | `sec.gov/municipal` | 15c2-12 amendments, enforcement actions, MCDC initiative |
| CMS (Healthcare) | `cms.gov` | Hospital cost reports, star ratings, payor data |
| EPA (Environmental) | `epa.gov` | Environmental compliance, permits, Superfund |
| Census Bureau | `census.gov` | Demographic data for service area analysis |
| BLS | `bls.gov` | Employment, wages, CPI for economic base analysis |
| Federal Reserve (FRED) | `fred.stlouisfed.org` | Interest rates, economic indicators, municipal indices |

### 3.4 Industry Associations

| Organization | Focus Area | Key Publications |
|-------------|-----------|-----------------|
| GFOA | Government finance best practices | CAFR guidelines, debt management policies |
| HFMA | Healthcare finance | Hospital financial benchmarks, regulatory updates |
| NAHB | Housing | Multi-family market data |
| CDFA | Development finance | Bond finance guides, NMTC resources |
| NACo | County government | County financial data and governance |
| ICMA | City/county management | Local government benchmarks |

### 3.5 Market Data

| Source | Data Type | Access |
|--------|-----------|--------|
| AAA MMD Curve | Benchmark yield curve for tax-exempt munis | Published daily (Thomson Reuters) |
| BVAL Curve | Bloomberg valuation curve | Bloomberg terminal (limited web access) |
| SIFMA Index | Variable rate demand obligation benchmark | Weekly reset, published at sifma.org |
| Bond Buyer Indices | 20-Bond GO, 25-Bond Revenue, 11-Bond GO | Published weekly at bondbuyer.com |

---

## 4. FILE CONVENTIONS

### 4.1 Research Memos

**Location**: `research/memos/` or `research/corpus/{sector}/`
**Format**: Markdown with YAML frontmatter

```yaml
---
title: "Title of the Research Memo"
date: 2026-MM-DD
author: "Muni-Pal Research Agent"
sector: waste-environmental | healthcare | cross-sector
sub_sector: solid-waste | hazardous-waste | hospital | ccrc | senior-living | behavioral-health
type: sector-analysis | comparable-analysis | credit-assessment | regulatory-analysis | literature-review | white-paper | method-proposal
confidence: 0.0-1.0
schema_paths_touched: []
gate_status: research_only | proposed_for_review
references: []
---
```

**Naming convention**: `{type}_{subject}_{YYYY-MM-DD}.md`
- Example: `sector_analysis_solid_waste_revenue_bonds_2026-02-18.md`
- Example: `credit_assessment_waste_management_inc_2026-03-01.md`
- Example: `literature_review_omega_ratio_extensions_2026-02-20.md`

### 4.2 Datasets

**Location**: `research/datasets/`
**Format**: JSON with embedded schema documentation

```json
{
  "metadata": {
    "name": "dataset_name",
    "version": "1.0",
    "created": "2026-MM-DD",
    "updated": "2026-MM-DD",
    "sector": "waste-environmental",
    "description": "What this dataset contains and how it was assembled",
    "sources": ["EMMA", "SEC EDGAR", "Moody's published medians"],
    "record_count": 0,
    "completeness": 0.0,
    "schema": {
      "field_name": {
        "type": "string|integer|decimal|date|boolean|enum|object",
        "description": "What this field represents",
        "source": "Where this data comes from",
        "summers_dimension": "Which scoring dimension this informs (if any)",
        "muni_pal_path": "Schema path in Muni-Pal (if mapped)"
      }
    }
  },
  "records": []
}
```

**Naming convention**: `{sector}_{dataset_name}_v{version}.json`
- Example: `waste_financial_benchmarks_v1.json`
- Example: `healthcare_hospital_comparable_deals_v1.json`

### 4.3 Analytical Models

**Location**: `research/models/`
**Format**: Python files with structured docstrings

```python
"""
Model: [Name]
Version: [X.Y]
Based on: [Summers Paper X, Section Y.Z] or [Citation]
Purpose: [What problem this model solves]

Inputs:
  - [parameter]: [type] — [description]

Outputs:
  - [field]: [type] — [description]

Validation:
  - [How the model was validated]
  - [Results of validation]

Limitations:
  - [Known limitations]

Changelog:
  - v1.0 (2026-MM-DD): Initial implementation
"""
```

**Naming convention**: `{method_name}_v{version}.py`
- Example: `muni_omega_adjusted_v1.py`
- Example: `healthcare_dscr_stress_model_v1.py`

### 4.4 Corpus Files

**Location**: `research/corpus/{sector}/`

Each sector directory may contain:
- `sector_analysis.md` — Comprehensive sector overview
- `credit_drivers.json` — Structured credit driver data
- `financial_benchmarks.json` — Benchmark financial metrics by rating
- `rating_methodology_summary.md` — Rating agency methodology digest
- `corpus_building_plan.md` — Data collection strategy
- Additional analysis files as research progresses

### 4.5 Capability Log

**Location**: `research/agent/capability_log.md`

Running log tracking:
- Methods studied and applicability assessed
- Models proposed, built, and validated
- Datasets created and their current state
- Sector coverage expansion progress

Format:
```markdown
## [Date] — [Action Type]

**Topic**: [What was studied/built/proposed]
**Status**: [studied | proposed | implemented | validated | rejected]
**Files**: [List of files created or modified]
**Notes**: [Key findings or decisions]
```

---

## 5. ENVIRONMENT NOTES

### 5.1 Python Environment

- Python packages available: `pdfplumber`, `pymupdf` (fitz), `click`, `pydantic`, `anthropic`, `sqlite3` (stdlib), `dateutil`, `numpy` (if installed)
- Anthropic model for AI extraction: `claude-sonnet-4-20250514` (configured in `.env`)
- The `.env` file at project root contains API keys (Anthropic, PostgreSQL, Redis, JWT)

### 5.2 Windows-Specific

- Paths use backslashes but shell commands should use forward slashes (bash environment)
- `cp1252` encoding: avoid Unicode box-drawing characters in CLI output; use ASCII equivalents
- Paths with spaces require quoting in shell commands
- Tesseract OCR must be installed separately for OCR fallback in extraction

### 5.3 Project Root

All relative paths in this document are relative to:
```
c:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\MUNI-PAL\
```

### 5.4 Research Directory Tree

```
research/
  agent/                              # These instruction files
    00-agent-charter.md
    01-municipal-bond-ontology.md
    02-summers-analytical-framework.md
    03-research-workflows.md
    04-munipal-integration-gate.md
    05-data-sources-and-tools.md       # This file
    capability_log.md                  # Created as research progresses
  corpus/
    waste-environmental/              # Waste sector research outputs
    healthcare/                       # Healthcare sector research outputs
    references/                       # User-provided excerpts from DRM sources
  models/                            # Agent-developed analytical models
    proposals/                        # Model proposals awaiting approval
  datasets/                          # Agent-curated structured datasets
  memos/                             # Research memos and white papers
```

---

## 6. QUICK REFERENCE: COMMON OPERATIONS

### Run the full Summers pipeline
```bash
cd emma/bond_os_extractor
python -m src.cli full-analysis
```

### Check a specific obligor's fundamental score
```bash
cd emma/bond_os_extractor
python -m src.cli score-detail "Waste Management"
```

### Inspect synthetic bond returns for a municipal obligor
```bash
cd emma/bond_os_extractor
python -m src.cli bond-returns "City of Los Angeles"
```

### Generate risk benchmark report
```bash
cd emma/bond_os_extractor
python -m src.cli risk-benchmark
```

### Search the EMMA corpus
```bash
cd emma/bond_os_extractor
python -m src.cli search --state CA --bond-type revenue
```

### Export corpus data
```bash
cd emma/bond_os_extractor
python -m src.cli export --format json
```

### Check corpus statistics
```bash
cd emma/bond_os_extractor
python -m src.cli status
python -m src.cli module-status
```
