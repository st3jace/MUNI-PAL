# Bond OS Extractor -- CLI Reference

All commands run from the `emma/bond_os_extractor/` directory:

```
cd emma/bond_os_extractor
python -m src.cli <command> [options]
```

Global option: `--log-level DEBUG|INFO|WARNING|ERROR`

---

## 1. PDF Ingestion & Management

### `ingest` -- Ingest one PDF or all PDFs in a directory

```bash
python -m src.cli ingest <path>
python -m src.cli ingest ./pdfs/AB4139C8/
python -m src.cli ingest ./pdfs/AB4139C8/some_document.pdf
python -m src.cli ingest <path> --no-ai        # skip AI (Tier 2) extraction
python -m src.cli ingest <path> --no-db         # skip database storage
```

### `ingest-all` -- Ingest all document types with module routing

Routes each PDF to the appropriate extraction module (rating action, event filing, financial report) or falls back to the OS extractor.

```bash
python -m src.cli ingest-all <directory>
python -m src.cli ingest-all ./pdfs/AB4139C8/
python -m src.cli ingest-all <directory> --dry-run   # preview routing without extracting
python -m src.cli ingest-all <directory> --no-db      # skip database storage
```

### `test-ingest` -- Test PDF ingestion only (no extraction)

```bash
python -m src.cli test-ingest ./pdfs/some_document.pdf
```

### `clear-cache` -- Clear AI response cache

```bash
python -m src.cli clear-cache
python -m src.cli clear-cache --older-than 30   # only entries older than 30 days
```

---

## 2. Corpus Search & Export

### `status` -- Show corpus statistics

```bash
python -m src.cli status
```

### `module-status` -- Show statistics for document modules

```bash
python -m src.cli module-status
python -m src.cli module-status --module rating_action
python -m src.cli module-status --module financial_report
python -m src.cli module-status --module event_filing
```

### `search` -- Search the corpus with filters

```bash
python -m src.cli search
python -m src.cli search --state CA
python -m src.cli search --type revenue
python -m src.cli search --min-par 1000000 --max-par 50000000
python -m src.cli search --cab                  # CAB bonds only
python -m src.cli search --slb                  # SLB bonds only
```

### `export` -- Export corpus data

```bash
python -m src.cli export
python -m src.cli export --format json --output ./export.json
python -m src.cli export --format csv --output ./export.csv
```

---

## 3. Summers Methodology -- Phase 1: Fundamental Scoring

Scores obligors (0-100) across 5 dimensions: Financial Stability, Profitability, Credit Quality, Structural Quality, Growth/Momentum.

### `score` -- Score the obligor universe

```bash
python -m src.cli score
python -m src.cli score --threshold 60           # custom investable threshold (default 50)
python -m src.cli score --ticker-dir "C:\path\to\waste_tickers"
python -m src.cli score --output ./scores.json
```

### `score-detail` -- Detailed breakdown for one obligor

```bash
python -m src.cli score-detail WM               # by ticker
python -m src.cli score-detail RSG
python -m src.cli score-detail "Republic"        # by issuer name substring
python -m src.cli score-detail "Brevard"
```

---

## 4. Summers Methodology -- Phase 2: S_Omega Return Series

Computes Summers' S_Omega, Omega ratio, and SIC matrix for each investable obligor.

### `s-omega` -- Compute S_Omega for investable universe

```bash
python -m src.cli s-omega
python -m src.cli s-omega --rf 0.05              # custom risk-free rate (default 4.5%)
python -m src.cli s-omega --start-date 2021-01-01
python -m src.cli s-omega --output ./omega.json
```

### `s-omega-detail` -- Detailed S_Omega for a single ticker

```bash
python -m src.cli s-omega-detail RSG
python -m src.cli s-omega-detail WM --rf 0.05
python -m src.cli s-omega-detail CWST --start-date 2021-01-01
```

---

## 5. Summers Methodology -- Phase 3: Benchmark & Composite Ranking

Constructs sector benchmark, SIC efficiency frontier, and Composite Ranking Index (CRI).

### `benchmark` -- Build sector benchmark

```bash
python -m src.cli benchmark
python -m src.cli benchmark --output ./benchmark.json
```

### `benchmark-detail` -- Detailed benchmark for one constituent

```bash
python -m src.cli benchmark-detail RSG
python -m src.cli benchmark-detail WM
```

---

## 6. Summers Methodology -- Phase 4: Hilbert Space Signal Extraction

FFT spectral analysis, DWT/MRA wavelet decomposition, and DMD/Koopman mode extraction.

### `signals` -- Extract signals from investable universe

```bash
python -m src.cli signals
python -m src.cli signals --output ./signals.json
```

### `signal-detail` -- Detailed signal extraction for one ticker

```bash
python -m src.cli signal-detail RSG
python -m src.cli signal-detail WM --start-date 2021-01-01
```

---

## 7. Summers Methodology -- Phase 5: Full Pipeline

Runs the complete Phase 1 > 2 > 3 > 4 > 5 pipeline with extended Omega measures and Integrated Risk Score.

### `full-analysis` -- Run complete Summers methodology

```bash
python -m src.cli full-analysis
python -m src.cli full-analysis --threshold 60
python -m src.cli full-analysis --rf 0.05 --start-date 2021-01-01
python -m src.cli full-analysis --output ./full_results.json
```

---

## 8. Phase 6: Synthetic Bond Return Series

Builds synthetic return series for obligors without equity tickers using EMMA trade data, rating events, fundamental drift, and coupon carry.

### `bond-returns` -- Display synthetic bond returns for an obligor

```bash
python -m src.cli bond-returns "Mission"
python -m src.cli bond-returns "Republic"
python -m src.cli bond-returns "Brevard" --start-date 2021-01-01
python -m src.cli bond-returns "City of Los Angeles" --max-rows 100
python -m src.cli bond-returns "Mission" --output ./mission_returns.json
```

---

## 9. Risk Benchmarking (EMMA Corpus -> Readiness Bridge)

Bridges EMMA-extracted bond corpus data with the Muni-Pal readiness assessment framework across 5 risk dimensions: technology, construction, market, regulatory, feedstock.

### `risk-benchmark` -- Build corpus-wide risk benchmarks

Aggregates 311 risk factors, 370 rating agency factors, 104 security packages, and 116 financial reports into readiness-aligned benchmarks.

```bash
python -m src.cli risk-benchmark
python -m src.cli risk-benchmark -o ./benchmarks.json
```

### `risk-compare` -- Compare a project against corpus benchmarks

Produces gap assessments with severity ratings (critical/material/acceptable) and priority actions.

```bash
# Minimal
python -m src.cli risk-compare -p "GSI Caldor UCS"

# With financial metrics
python -m src.cli risk-compare -p "GSI Caldor UCS" \
    --dscr 1.34 \
    --revenue 10000000 \
    --coverage-ratio 1.20

# With risk disclosure flags
python -m src.cli risk-compare -p "GSI Caldor UCS" \
    --dscr 1.34 \
    --revenue 10000000 \
    --has-technology-risk \
    --has-construction-risk \
    --has-market-risk \
    --has-regulatory-risk

# With both risk descriptions and mitigants
python -m src.cli risk-compare -p "GSI Caldor UCS" \
    --has-technology-risk --has-technology-mitigants \
    --has-market-risk --has-market-mitigants \
    -o ./comparison.json
```

### `risk-guide` -- Generate Risk Mitigation Implementation Guide

Combines corpus evidence, rating agency perspectives (by issuer), structural protections, and playbook guidance into an actionable implementation plan with prioritized actions.

```bash
# Full example with all flags
python -m src.cli risk-guide -p "GSI Caldor UCS" \
    --dscr 1.34 \
    --revenue 10000000 \
    --has-technology-risk \
    --has-construction-risk \
    --has-market-risk \
    --has-regulatory-risk

# JSON only
python -m src.cli risk-guide -p "GSI Caldor UCS" --dscr 1.34 --format json

# Markdown only
python -m src.cli risk-guide -p "GSI Caldor UCS" --dscr 1.34 --format markdown

# Both (default)
python -m src.cli risk-guide -p "GSI Caldor UCS" --dscr 1.34 --format both

# Custom output prefix
python -m src.cli risk-guide -p "GSI Caldor UCS" --dscr 1.34 -o ./guide
```

---

## Risk Disclosure Flags Reference

The `risk-compare` and `risk-guide` commands accept flags for each of the 5 risk dimensions. Each dimension has a description flag and a mitigants flag:

| Dimension | Description Flag | Mitigants Flag |
|-----------|-----------------|----------------|
| Technology | `--has-technology-risk` | `--has-technology-mitigants` |
| Construction | `--has-construction-risk` | `--has-construction-mitigants` |
| Market/Revenue | `--has-market-risk` | `--has-market-mitigants` |
| Regulatory | `--has-regulatory-risk` | `--has-regulatory-mitigants` |
| Feedstock/Supply | `--has-feedstock-risk` | `--has-feedstock-mitigants` |

**Status mapping:**
- Neither flag set = "missing" (no disclosure)
- Description only = "partial" (risk identified but no mitigants)
- Both flags set = "addressed" (risk identified with mitigants)

---

## Output Locations

All analysis outputs are saved to `data/analysis/`:

| Command | Output File |
|---------|-------------|
| `score` | `data/analysis/fundamental_scores.json` |
| `s-omega` | `data/analysis/s_omega_results.json` |
| `benchmark` | `data/analysis/benchmark_results.json` |
| `signals` | `data/analysis/hilbert_results.json` |
| `full-analysis` | `data/analysis/extended_risk_results.json` |
| `risk-benchmark` | `data/analysis/risk_benchmark_report.json` |
| `risk-compare` | `data/analysis/risk_comparison_report.json` |
| `risk-guide` | `data/analysis/risk_implementation_guide.json` + `.md` |

Previously generated markdown reports:
- `data/analysis/risk_benchmark_report.md`
- `data/analysis/risk_comparison_report.md`
- `data/analysis/risk_implementation_guide.md`

---

## Common Workflows

### Ingest a new CUSIP folder

```bash
python -m src.cli ingest-all ./pdfs/NEW_CUSIP/ --dry-run   # preview first
python -m src.cli ingest-all ./pdfs/NEW_CUSIP/              # run for real
python -m src.cli module-status                              # verify results
```

### Run complete Summers analysis pipeline

```bash
python -m src.cli full-analysis
```

### Assess a new project against corpus benchmarks

```bash
# Step 1: See what the corpus looks like
python -m src.cli risk-benchmark

# Step 2: Compare your project
python -m src.cli risk-compare -p "My Project" \
    --dscr 1.50 --revenue 25000000 \
    --has-technology-risk --has-market-risk

# Step 3: Get implementation guide
python -m src.cli risk-guide -p "My Project" \
    --dscr 1.50 --revenue 25000000 \
    --has-technology-risk --has-market-risk
```

### Inspect a specific obligor

```bash
python -m src.cli score-detail WM
python -m src.cli s-omega-detail WM
python -m src.cli benchmark-detail WM
python -m src.cli signal-detail WM
python -m src.cli bond-returns "Waste Management"
```
