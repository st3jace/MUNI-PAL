# EMMA Crawler — Quick Reference

> **PowerShell note:** Use `;` (not `&&`) to chain commands. Or run `cd` first, then the python command on a separate line.

## Startup Commands

### Full crawl (discover + extract)

```powershell
cd "c:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\MUNI-PAL\emma\emma_crawler"; python -m src.main --visible
```

### Phase 3 only (extract from existing queue)

```powershell
cd "c:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\MUNI-PAL\emma\emma_crawler"; python -m src.main --phase3-only --visible
```

### Test a single security by URL

```powershell
cd "c:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\MUNI-PAL\emma\emma_crawler"; python -m src.main --test-url "https://emma.msrb.org/Security/Details/AAB4AB7DB419BB830DCC3293F13AAD8D6" --visible
```

### Test a single security by CUSIP

```powershell
cd "c:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\MUNI-PAL\emma\emma_crawler"; python -m src.main --test-cusip "123456789" --visible
```

---

## CLI Flags

| Flag | Purpose |
|------|---------|
| `--visible` | Show the browser window (default is headless) |
| `--headless` | Run without browser window |
| `--max-securities N` | Limit extraction to N securities |
| `--phase2-only` | Only discover securities, skip extraction |
| `--phase3-only` | Only extract from existing `processing_queue.json` |
| `--resume` | Resume from last checkpoint |
| `--retry-failed` | Re-process previously failed securities |
| `--retry-partial` | Re-process securities with partial extractions |
| `--dry-run` | Discover without writing data |
| `--log-level DEBUG` | Verbose logging |
| `--config <path>` | Config directory (default: `./config`) |
| `--search-params <file>` | Search params YAML filename in config dir (default: `search_params.yaml`) |
| `--date-from MM/DD/YYYY` | Override `closing_date_from` at runtime |
| `--date-to MM/DD/YYYY` | Override `closing_date_to` at runtime (accepts `TODAY`) |
| `--output-dir <path>` | Output directory (default: `./output`) |
| `--storage-state <path>` | Browser session storage file |
| `--emma-username` | EMMA login username (or set `EMMA_USERNAME` env var) |
| `--emma-password` | EMMA login password (or set `EMMA_PASSWORD` env var) |

---

## Output Locations

| Path | Contents |
|------|----------|
| `output/data/<security_id>.json` | Extracted security data (snapshot, trades, ratings, disclosures) |
| `output/pdfs/<security_id>/` | Downloaded disclosure PDFs |
| `output/logs/crawler.log` | Crawl log |
| `output/data/processing_queue.json` | Phase 2 discovery queue (input for Phase 3) |
| `output/checkpoint.json` | Resume checkpoint |

---

## JSON Output Schema

Each security JSON file contains:

```json
{
  "cusip": "<EMMA security ID>",
  "crawl_metadata": {
    "crawl_timestamp": "ISO-8601",
    "emma_url": "https://emma.msrb.org/Security/Details/...",
    "extraction_status": {
      "snapshot": "success|empty|error",
      "interest_rate": "success|empty|error",
      "trade_activity": "success|empty|error",
      "ratings": "success|empty|error",
      "disclosures": "success|empty|error"
    }
  },
  "snapshot": {
    "security_name": "",
    "cusip": "",
    "principal_amount": 0,
    "maturity_date": "",
    "dated_date": "",
    "coupon_pct": "",
    "closing_date": "",
    "fiscal_year_end_date": "",
    "initial_offering_price_yield": "",
    "time_of_formal_award": "",
    "time_of_first_execution": "",
    "state": ""
  },
  "interest_rates": [],
  "trades": [
    {
      "trade_date": "MM/DD/YYYY HH:MM AM/PM",
      "settlement_date": "MM/DD/YYYY",
      "price": "94.413",
      "yield": "5.123",
      "calculation_date_price": "MM/DD/YYYY @ 100",
      "trade_amount": "4,125,000",
      "trade_type": "Customer bought|Customer sold|Inter-dealer trade",
      "special_condition": ""
    }
  ],
  "ratings": [
    {
      "agency": "Fitch|KBRA|Moody's|S&P",
      "rating": "",
      "outlook": "",
      "as_of": "",
      "note": ""
    }
  ],
  "disclosures": [
    {
      "doc_type": "Official Statement|Disclosure",
      "filing_date": "MM/DD/YYYY",
      "pdf_url": "https://emma.msrb.org/...",
      "local_pdf_path": "C:\\...\\output\\pdfs\\...\\file.pdf",
      "download_success": true
    }
  ]
}
```

---

## Search Configuration

Edit `config/search_params.yaml` to change bond search criteria:

```yaml
search_filters:
  security_information:
    state: ""                        # e.g. "AL", "CA"
    issuer_name: ""                  # partial match
    issue_description: "Waste"       # keyword in description
    closing_date_from: "1/1/2020"
    closing_date_to: "TODAY"
    purpose_sector: "All"
    source_of_repayment: "Revenue"   # Revenue, General Obligation, etc.
    rate_type: "All"
    insured: "All"
    tax_status: "All"
    callable: "All"
result_filters:
  min_principal_amount: 8000000      # minimum $8M
view_mode: "SECURITIES"
```

---

## Crawler Settings

Edit `config/crawler_settings.yaml` for browser and timing:

```yaml
browser:
  headless: true
  viewport_width: 1920
  viewport_height: 1080
  user_agent: "MuniPal-StandardModel/1.0 (Research crawler)"
timing:
  page_load_timeout: 120000   # 2 min
  action_delay: 2000          # between actions
  between_securities: 3000    # pause between securities
  tab_switch_delay: 2000
  max_retries: 3
pagination:
  results_per_page: 50
```

---

## Validation

Quick validation after a crawl:

```powershell
# PowerShell one-liner
Get-ChildItem .\output\data\*.json -Exclude processing_queue.json | ForEach-Object {
    $d = Get-Content $_.FullName | ConvertFrom-Json
    [PSCustomObject]@{
        File        = $_.Name
        CUSIP       = $d.snapshot.cusip
        Trades      = $d.trades.Count
        Ratings     = $d.ratings.Count
        Disclosures = $d.disclosures.Count
    }
} | Format-Table -AutoSize
```

---

## Crawl Phases

1. **Phase 2 — Discovery**: Searches EMMA, collects qualifying security URLs, saves `processing_queue.json`
2. **Phase 3 — Extraction**: Visits each security detail page, extracts all tabs (snapshot, interest rates, trade activity, ratings, disclosures), downloads PDFs

Typical workflow:
- First run: `python -m src.main --visible` (both phases)
- Re-extract only: `python -m src.main --phase3-only --visible`
- Fix failures: `python -m src.main --retry-failed --visible`
- Test one bond: `python -m src.main --test-url "<url>" --visible`

---

## Healthcare Sector Crawl

Healthcare output goes into `output/healthcare/` to stay separate from waste sector data.

### Step 1 — Broad pass (EMMA "Health" sector, chunked by year)

EMMA caps broad queries, so the Health-sector pass must be chunked by year using `--date-from` / `--date-to`:

```powershell
cd "c:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\MUNI-PAL\emma\emma_crawler"

# 2020
python -m src.main --search-params search_params_healthcare.yaml --output-dir ./output/healthcare --date-from "1/1/2020" --date-to "12/31/2020" --visible

# 2021
python -m src.main --search-params search_params_healthcare.yaml --output-dir ./output/healthcare --date-from "1/1/2021" --date-to "12/31/2021" --visible

# 2022
python -m src.main --search-params search_params_healthcare.yaml --output-dir ./output/healthcare --date-from "1/1/2022" --date-to "12/31/2022" --visible

# 2023
python -m src.main --search-params search_params_healthcare.yaml --output-dir ./output/healthcare --date-from "1/1/2023" --date-to "12/31/2023" --visible

# 2024
python -m src.main --search-params search_params_healthcare.yaml --output-dir ./output/healthcare --date-from "1/1/2024" --date-to "12/31/2024" --visible

# 2025
python -m src.main --search-params search_params_healthcare.yaml --output-dir ./output/healthcare --date-from "1/1/2025" --date-to "12/31/2025" --visible

# 2026 (YTD)
python -m src.main --search-params search_params_healthcare.yaml --output-dir ./output/healthcare --date-from "1/1/2026" --date-to "TODAY" --visible
```

All passes write to the same `output/healthcare/` directory. Security JSON files are keyed by URL hash, so duplicates are naturally deduplicated.

### Step 2 — Targeted keyword passes

Run each pass to catch healthcare securities mislabeled under other sectors. Each writes to the same `output/healthcare/` directory.

```powershell
# Hospital
python -m src.main --search-params search_params_healthcare_hospital.yaml --output-dir ./output/healthcare --visible

# Continuing Care / CCRC
python -m src.main --search-params search_params_healthcare_ccrc.yaml --output-dir ./output/healthcare --visible

# Senior Living
python -m src.main --search-params search_params_healthcare_senior.yaml --output-dir ./output/healthcare --visible

# Behavioral Health
python -m src.main --search-params search_params_healthcare_behavioral.yaml --output-dir ./output/healthcare --visible

# Medical Centers / Specialty
python -m src.main --search-params search_params_healthcare_medical.yaml --output-dir ./output/healthcare --visible

# Clinics
python -m src.main --search-params search_params_healthcare_clinic.yaml --output-dir ./output/healthcare --visible
```

### Healthcare config files

| File | Strategy | Keyword |
|------|----------|---------|
| `search_params_healthcare.yaml` | Broad — `purpose_sector: "Health"` | *(blank)* |
| `search_params_healthcare_hospital.yaml` | Keyword — `purpose_sector: "All"` | `Hospital` |
| `search_params_healthcare_ccrc.yaml` | Keyword | `Continuing Care` |
| `search_params_healthcare_senior.yaml` | Keyword | `Senior Living` |
| `search_params_healthcare_behavioral.yaml` | Keyword | `Behavioral` |
| `search_params_healthcare_medical.yaml` | Keyword | `Medical` |
| `search_params_healthcare_clinic.yaml` | Keyword | `Clinic` |

### Healthcare output structure

```
output/healthcare/
├── data/
│   ├── <security_id>.json        # Extracted security data
│   └── processing_queue.json     # Discovery queue (overwritten per pass)
├── pdfs/
│   └── <security_id>/            # Downloaded disclosure PDFs
└── logs/
    └── crawler.log
```

> **Note:** Each keyword pass overwrites `processing_queue.json`. The extracted security JSON files accumulate across passes since filenames are unique per security. Duplicate securities discovered by multiple passes are naturally deduplicated because the `--resume` checkpoint skips already-completed URL hashes.
