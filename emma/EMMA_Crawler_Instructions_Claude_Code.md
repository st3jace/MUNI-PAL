# EMMA Municipal Bond Web Crawler — Claude Code Build Instructions

## Project: Muni-Pal Standard Model — EMMA Data Collection Module

**Version:** 1.2  
**Date:** February 6, 2026  
**Author:** Stephen Peterson, Launch Shop Operations  
**Target:** Claude Code implementation using Playwright (Python)

---

## 1. MISSION & SCOPE

Build a headless web crawler that systematically extracts municipal bond security data from the MSRB's EMMA platform (Electronic Municipal Market Access) at:

```
https://emma.msrb.org/Search/Search.aspx
```

The crawler targets **waste/solid waste revenue bonds** with **Principal Amount At Issuance ≥ $8,000,000** for the Muni-Pal Standard Model's waste sector analysis. This is the first of four sector crawlers (Healthcare, Education Facilities, Multi-Family Housing, and Waste) that will share a common architecture.

---

## 2. TECHNOLOGY STACK

```
Language:        Python 3.10+
Browser Automation: Playwright (async preferred)
Data Storage:    JSON + CSV (dual output)
PDF Downloads:   Native Playwright download handling
Config:          YAML or JSON config file for search parameters
Logging:         Python logging module (file + console)
Rate Limiting:   Built-in delays (respect EMMA servers)
```

### Install Dependencies
```bash
pip install playwright aiofiles pyyaml
playwright install chromium
```

---

## 3. ARCHITECTURE OVERVIEW

```
emma_crawler/
├── config/
│   ├── search_params.yaml        # Search filter configurations
│   └── crawler_settings.yaml     # Timing, retries, paths
├── src/
│   ├── __init__.py
│   ├── main.py                   # Entry point & orchestration
│   ├── search.py                 # Search page navigation & filter population
│   ├── results.py                # Results page pagination & filtering
│   ├── session_manager.py        # Session health, search re-execution, results recovery
│   ├── security_detail.py        # Individual security data extraction
│   ├── tab_extractors/
│   │   ├── __init__.py
│   │   ├── snapshot.py           # Security snapshot/header data
│   │   ├── interest_rate.py      # Interest Rate tab
│   │   ├── trade_activity.py     # Trade Activity tab
│   │   ├── ratings.py            # Ratings tab
│   │   └── disclosures.py        # Disclosure Documents tab + PDF downloads
│   ├── models.py                 # Data classes / Pydantic models
│   ├── storage.py                # JSON/CSV output handlers
│   └── utils.py                  # Rate limiting, retry logic, logging
├── output/
│   ├── data/                     # JSON + CSV per security
│   ├── pdfs/                     # Downloaded disclosure PDFs
│   └── logs/                     # Crawler logs
├── requirements.txt
└── README.md
```

---

## 4. CONFIGURATION FILES

### 4.1 search_params.yaml

```yaml
# EMMA Muni Search filter parameters
# These map directly to the form fields on the Search page

search_filters:
  security_information:
    state: ""                          # Leave blank for all states
    issuer_name: ""                    # Leave blank for all issuers
    issue_description: "waste"         # Keyword filter — CRITICAL
    closing_date_from: "1/1/2020"      # Start date MM/DD/YYYY
    closing_date_to: "02/06/2026"      # End date MM/DD/YYYY
    purpose_sector: "All"              # Dropdown value
    source_of_repayment: "Revenue"     # Dropdown: Revenue, GO, All, etc.
    rate_type: "All"                   # Dropdown value
    insured: "All"                     # Dropdown value
    tax_status: "All"                  # Dropdown value
    callable: "All"                    # Dropdown value

  # Additional filters (leave empty unless needed)
  dated_date_from: ""
  dated_date_to: ""
  interest_rate_from: ""
  interest_rate_to: ""
  cusip6: ""
  maturity_date_from: ""
  maturity_date_to: ""
  include_matured: false
  include_called_redeemed: false

# Filtering threshold applied to results
result_filters:
  min_principal_amount: 8000000        # $8,000,000 minimum
  
# View mode
view_mode: "SECURITIES"                # SECURITIES or ISSUES
```

### 4.2 crawler_settings.yaml

```yaml
# Crawler behavior configuration

browser:
  headless: true                       # Set false for debugging
  viewport_width: 1920
  viewport_height: 1080
  user_agent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

timing:
  page_load_timeout: 60000             # ms — EMMA can be slow
  action_delay: 2000                   # ms between actions (rate limiting)
  between_securities: 3000             # ms between security page loads
  between_pages: 2000                  # ms between result pages
  tab_switch_delay: 2000               # ms after clicking a tab
  show_more_delay: 1500                # ms after clicking Show More
  retry_delay: 5000                    # ms before retry on failure
  max_retries: 3                       # Per action

session:
  health_check_timeout: 2000           # ms to wait when checking page state
  recovery_backoff_base: 5000          # ms base delay for session recovery
  recovery_max_retries: 3              # Max recovery attempts per incident
  assume_expired_after: 300000         # ms (5 min) — if a detail page takes 
                                       # longer than this, proactively check session
                                       # health before next navigation

pagination:
  results_per_page: 50                 # Set display dropdown to 50
  # Note: EMMA allows 10, 25, 50 results per page

output:
  data_dir: "./output/data"
  pdf_dir: "./output/pdfs"
  log_dir: "./output/logs"
  checkpoint_file: "./output/checkpoint.json"  # Resume support

logging:
  level: "INFO"                        # DEBUG for development
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
```

---

## 5. DETAILED CRAWL WORKFLOW

### Phase 1: Search Page Navigation & Filter Population

**Target URL:** `https://emma.msrb.org/Search/Search.aspx`

**Step-by-step:**

1. **Navigate to search page** and wait for full DOM load
2. **Verify the "Security Information" panel is open** (it should be by default — the panel heading reads "Security Information" with the subtitle "Select criteria about an issuer or its securities...")
3. **Populate form fields in this exact order:**

```python
# Form field selectors (verify these against live DOM — IDs may change)
# The form uses ASP.NET controls, so IDs follow a pattern like:
#   ctl00$mainContentArea$searchTabContainer$tabSecurity$...

FIELD_MAP = {
    "issue_description": {
        "selector": "input[id*='txtIssueDescription']",
        "type": "text",
        "value": "waste"
    },
    "closing_date_from": {
        "selector": "input[id*='txtClosingDateFrom']",
        "type": "text",
        "value": "1/1/2020"
    },
    "closing_date_to": {
        "selector": "input[id*='txtClosingDateTo']",
        "type": "text",
        "value": "02/06/2026"
    },
    "source_of_repayment": {
        "selector": "select[id*='ddlSourceOfRepayment']",
        "type": "select",
        "value": "Revenue"
    }
}
```

4. **Click "Run Search" button** — selector: `input[id*='btnSearch']` or the blue "Run Search" button
5. **Wait for results page to load** — look for the results count text (e.g., "593 securities")

**CRITICAL NOTES:**
- EMMA uses ASP.NET Web Forms with ViewState — DO NOT try to construct POST requests manually. Use Playwright to interact with the actual DOM.
- Form fields may trigger postbacks. After changing a dropdown, wait ~1 second for any AJAX updates.
- The search page has expandable filter sections. "Security Information" should be expanded by default.

---

### Phase 2: Results Page Processing — COLLECT-FIRST STRATEGY

> **CRITICAL ARCHITECTURE DECISION: COLLECT ALL URLs FIRST, THEN PROCESS**
>
> EMMA uses ASP.NET server-side ViewState for its results pages. This means:
> - The results page is NOT a stable URL you can revisit — it's a server-side session state
> - If you navigate away to a security detail page and then try to go "Back," the ViewState may have expired
> - An expired ViewState returns an error page or dumps you back to a blank search form
> - Re-running the search and re-paginating to your previous position wastes time and hammers the server
>
> **Therefore, Phase 2 MUST fully complete before Phase 3 begins.** The crawler scans every page of results, builds a complete queue of qualifying security URLs, saves that queue to disk, and ONLY THEN begins processing individual securities via direct URL navigation.

**Expected state:** Results page showing securities list with column headers: State, Description, Coupon (%), Maturity Date, Principal Amount At Issuance ($), Dated Date, Ratings (Fitch, KBRA, Moody's, S&P)

**Step-by-step:**

1. **Set display count to 50:**
   - Locate the "Display [dropdown] results" control
   - Selector: `select[id*='ddlResultsPerPage']` or `select` near "Display" text
   - Change value to `50`
   - Wait for page to reload/update

2. **Verify VIEW mode is SECURITIES** (not ISSUES):
   - There's a toggle showing "593 SECURITIES | 209 ISSUES"
   - Ensure SECURITIES is selected (it's the default)

3. **For each results page, extract the table data:**

```python
# Results table structure
# <table> with class or id related to search results

RESULTS_TABLE_COLUMNS = [
    "state",
    "description",           # This is a clickable link
    "coupon_pct",
    "maturity_date",
    "principal_amount",      # KEY FILTER COLUMN
    "dated_date",
    "rating_fitch",
    "rating_kbra",
    "rating_moodys",
    "rating_sp"
]
```

4. **Filter rows by Principal Amount At Issuance:**
   - Parse the principal amount from each row (format: `8,000,000` — remove commas, convert to int)
   - **ONLY queue securities where principal_amount >= 8,000,000**
   - Log skipped securities with their amounts

5. **For qualifying securities, extract the link URL from the Description column:**
   - The description text is an `<a>` tag linking to the security details page
   - Extract the `href` attribute — convert relative URLs to absolute
   - **Also extract the CUSIP** from the URL or page context if available
   - Store in the processing queue

6. **Paginate through ALL result pages:**
   - Use "Next" button or page number links: `First | Previous | 1 | 2 | 3 | ... | Next | Last`
   - Selector pattern: links/buttons in the pagination area
   - Continue until "Next" is disabled or you reach "Last"
   - Track total securities found vs. qualifying securities

7. **Save the complete queue to disk before proceeding to Phase 3**

**COLLECT-FIRST IMPLEMENTATION:**
```python
async def collect_all_qualifying_securities(page, config, checkpoint):
    """
    Phase 2: Scan ALL results pages and build complete processing queue.
    
    This MUST complete fully before any security detail extraction begins.
    The queue is saved to disk so Phase 3 can operate independently of 
    the results page session state.
    
    SESSION RECOVERY: If EMMA's ViewState expires mid-pagination (e.g.,
    you've scanned pages 1-5 and the session dies on page 6), the crawler
    re-executes the search and jumps directly to the next unscanned page.
    Already-collected securities are preserved — we never re-scan pages.
    """
    qualifying_securities = []
    current_page = checkpoint.get("phase2_last_page_scanned", 0) + 1
    total_scanned = 0
    
    # If resuming mid-Phase 2, recover the session first
    if current_page > 1:
        logger.info(f"Resuming Phase 2 from page {current_page}")
        await recover_results_session(page, config, current_page)
    
    while True:
        try:
            # Extract rows from current page
            rows = await extract_results_table(page)
            total_scanned += len(rows)
            
            for row in rows:
                principal = parse_currency(row["principal_amount"])
                if principal >= config["min_principal_amount"]:
                    # Build the DIRECT URL for this security
                    detail_url = resolve_absolute_url(
                        page.url, row["description_link"]
                    )
                    qualifying_securities.append({
                        "detail_url": detail_url,          # Direct navigation URL
                        "description": row["description_text"],
                        "state": row["state"],
                        "principal_amount": principal,
                        "coupon": row["coupon_pct"],
                        "maturity_date": row["maturity_date"],
                        "dated_date": row["dated_date"],
                        "source_page": current_page,       # For logging/debugging
                    })
                else:
                    logger.debug(
                        f"Skipped: {row['description_text'][:60]}... "
                        f"(principal: ${principal:,.0f})"
                    )
            
            logger.info(
                f"Page {current_page}: scanned {len(rows)} securities, "
                f"{len(qualifying_securities)} qualifying so far"
            )
            
            # Checkpoint after each page in case of crash
            update_phase2_checkpoint(checkpoint, current_page, len(qualifying_securities))
            
            # Check for next page
            next_button = page.locator("text=Next").first
            if await next_button.is_disabled() or not await next_button.is_visible():
                break
            
            await next_button.click()
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(BETWEEN_PAGES_DELAY)
            current_page += 1
            
            # SESSION HEALTH CHECK after pagination
            # If the ViewState expired during the "Next" click, 
            # we'll land on an error page or blank search form
            healthy, page_type = await is_session_healthy(page)
            if not healthy or page_type != "results_page":
                raise SessionExpiredError(
                    f"Session expired after navigating to page {current_page}. "
                    f"Page state: {page_type}"
                )
        
        except SessionExpiredError as e:
            logger.warning(f"Session lost during Phase 2 pagination: {e}")
            logger.info(f"Recovering session and jumping to page {current_page}...")
            
            # Re-execute search and jump to where we left off
            recovered = await recover_results_session(page, config, current_page)
            if not recovered:
                logger.error("Failed to recover session. Saving partial queue.")
                break
            
            # Continue the loop — it will re-extract current_page
            continue
    
    logger.info(
        f"Phase 2 complete: {len(qualifying_securities)} qualifying "
        f"out of {total_scanned} total securities across {current_page} pages"
    )
    
    # CRITICAL: Save queue to disk before Phase 3
    save_processing_queue(qualifying_securities, config["output_dir"])
    checkpoint["phase2_complete"] = True
    save_checkpoint(checkpoint)
    
    return qualifying_securities


def save_processing_queue(securities, output_dir):
    """
    Persist the processing queue so Phase 3 can run independently.
    This protects against session loss between phases.
    
    Deduplicates by detail_url in case session recovery caused
    a page to be scanned twice during Phase 2.
    """
    # Deduplicate — session recovery can cause page re-scans
    seen_urls = set()
    deduped = []
    for s in securities:
        if s["detail_url"] not in seen_urls:
            seen_urls.add(s["detail_url"])
            deduped.append(s)
        else:
            logger.debug(f"Deduped: {s['description'][:60]}...")
    
    if len(deduped) < len(securities):
        logger.info(
            f"Deduplication removed {len(securities) - len(deduped)} "
            f"duplicate entries from queue"
        )
    
    queue_path = os.path.join(output_dir, "processing_queue.json")
    with open(queue_path, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "total_qualifying": len(deduped),
            "securities": deduped
        }, f, indent=2)
    logger.info(f"Processing queue saved: {queue_path} ({len(deduped)} securities)")


def load_processing_queue(output_dir):
    """Load a previously saved queue for resumed runs."""
    queue_path = os.path.join(output_dir, "processing_queue.json")
    if os.path.exists(queue_path):
        with open(queue_path, "r") as f:
            return json.load(f)
    return None
```

---

### Phase 3: Individual Security Detail Extraction

> **NAVIGATION STRATEGY: DIRECT URL, NEVER BROWSER BACK**
>
> Phase 3 processes each security by navigating DIRECTLY to its detail URL 
> (collected in Phase 2). The crawler NEVER uses the browser's back button 
> or tries to return to the results page. Each security is an independent 
> navigation: `page.goto(security["detail_url"])`.
>
> This completely eliminates ViewState expiry as a failure mode between securities.

> **IMPORTANT: EMMA URL PATTERN — OPAQUE HASH, NOT CUSIP-BASED**
>
> EMMA security detail URLs do NOT contain the CUSIP. They use an opaque 
> internal hash/ID:
> ```
> https://emma.msrb.org/Security/Details/A463E7B905E3D1D78EC0E5CD06C252733
> ```
> NOT the previously assumed pattern:
> ```
> https://emma.msrb.org/SecurityView/SecurityDetailView.aspx?cusip=XXXXXXXXX  ← WRONG
> ```
> This means:
> - **You CANNOT construct a URL from a CUSIP** — you must capture the actual `href` from the results table during Phase 2
> - **The CUSIP is only reliably available on the detail page itself** (in the blue card header: "CUSIP: 46245EBA4*")
> - **The URL hash serves as the tracking key** in the processing queue and checkpoint, with the CUSIP extracted after page load and used for file naming
> - **The `--test-cusip` CLI mode** must first search EMMA for the CUSIP to discover its hash URL, or accept a direct URL instead

**For each qualifying security, navigate directly to its detail URL:**

```python
async def process_all_securities(page, queue, checkpoint):
    """
    Phase 3: Process each security via direct URL navigation.
    
    Each security is independent — no dependency on results page state.
    
    Note: The CUSIP is NOT in the URL. We use the URL hash as the queue key
    and extract the CUSIP from the page content after navigation.
    """
    for i, security in enumerate(queue["securities"]):
        # Use URL hash as tracking ID (CUSIP not available until page load)
        url_hash = extract_url_hash(security["detail_url"])
        
        # Skip if already completed (resume support)
        if url_hash in checkpoint.get("completed_hashes", []):
            logger.info(f"[{i+1}/{queue['total_qualifying']}] Skipping {url_hash[:12]}... (already completed)")
            continue
        
        logger.info(
            f"[{i+1}/{queue['total_qualifying']}] Processing: "
            f"{security['description'][:60]}..."
        )
        
        try:
            # DIRECT navigation — no back button, no results page dependency
            await page.goto(security["detail_url"], wait_until="networkidle",
                           timeout=60000)
            
            # Verify we landed on a valid security detail page
            if not await verify_security_detail_page(page):
                raise NavigationError(f"Did not land on security detail page for {url_hash}")
            
            # EXTRACT CUSIP FROM PAGE CONTENT (not from URL)
            cusip = await extract_cusip_from_page(page)
            if not cusip:
                logger.warning(f"Could not extract CUSIP from page. URL hash: {url_hash}")
                cusip = url_hash[:12]  # Fallback: truncated hash as filename
            
            logger.info(f"  → CUSIP: {cusip}")
            
            # Extract all data from this security
            record = await extract_complete_security(page, cusip)
            
            # Save immediately (don't wait for batch)
            save_security_record(record, config["output_dir"])
            checkpoint_mark_complete(url_hash, cusip, checkpoint)
            
        except Exception as e:
            logger.error(f"Failed to process {url_hash}: {e}")
            checkpoint_mark_failed(url_hash, str(e), checkpoint)
        
        # Rate limiting between securities
        await asyncio.sleep(BETWEEN_SECURITIES_DELAY)


def extract_url_hash(detail_url):
    """
    Extract the opaque hash from an EMMA security URL.
    
    Example:
        Input:  https://emma.msrb.org/Security/Details/A463E7B905E3D1D78EC0E5CD06C252733
        Output: A463E7B905E3D1D78EC0E5CD06C252733
    """
    return detail_url.rstrip("/").split("/")[-1]


async def extract_cusip_from_page(page):
    """
    Extract the CUSIP from the security detail page content.
    
    The CUSIP appears in the blue card header area, typically formatted as:
        "CUSIP: 46245EBA4*"
    The asterisk may or may not be present. Strip it.
    """
    try:
        cusip_elem = page.locator("text=/CUSIP:/").first
        cusip_text = await cusip_elem.text_content()
        # Parse: "CUSIP: 46245EBA4*" → "46245EBA4"
        cusip = cusip_text.split(":")[-1].strip().rstrip("*").strip()
        if len(cusip) == 9:  # Standard CUSIP length
            return cusip
        elif len(cusip) == 6:  # CUSIP-6 (issuer only)
            return cusip
        else:
            logger.warning(f"Unexpected CUSIP format: '{cusip}' from '{cusip_text}'")
            return cusip  # Return it anyway
    except Exception as e:
        logger.error(f"Failed to extract CUSIP from page: {e}")
        return None
```

**The security detail page URL pattern (actual observed):**
```
https://emma.msrb.org/Security/Details/{OPAQUE_HASH}

Example: https://emma.msrb.org/Security/Details/A463E7B905E3D1D78EC0E5CD06C252733
```
The hash appears to be an internal EMMA identifier, not derived from the CUSIP.
These URLs ARE directly navigable (unlike results pages), which is what makes the 
collect-first architecture work.

---

#### 3A: Snapshot Data (Top Section — Blue Card)

**This is the light-blue information card at the top of the security detail page.**

**Data points to extract (BEFORE clicking Show More):**

```python
SNAPSHOT_FIELDS_VISIBLE = {
    "cusip": "",               # "CUSIP: 46245EBA4*" — parse after colon
    "security_name": "",       # Full name in blue link text
    "short_name": "",          # Shorter name below the full name
    "interest_rate": "",       # "2.21 %" — parse number
    "maturity_date": "",       # "05/01/2046"
    "dated_date": "",          # "05/28/2025"
    "principal_amount": "",    # "$8,000,000"
    "reset_period": "",        # "7 days" (if variable rate)
    "maximum_rate": "",        # "10.00 %" (if variable rate)
    "minimum_rate": "",        # "0.00 %" (if variable rate)
    "closing_date": "",        # "05/28/2025"
    "fiscal_year_end": "",     # May be "-" or a date
}
```

**CLICK THE "+Show More" LINK to reveal additional fields:**

- Selector: `a` or `span` containing text "+Show More" or "Show More"
- Wait for expansion animation/content load

**Additional fields after Show More:**

```python
SNAPSHOT_FIELDS_SHOW_MORE = {
    "minimum_denomination": "",    # "$100,000"
    "notification_period": "",     # "7 days"
    "initial_offering_price": "",  # "100% / 100%"
    "remarketing_agent": "",       # "Thornton Farish Inc."
    "time_formal_award": "",       # "05/23/2025 09:00 AM"
    "time_first_execution": "",    # "05/23/2025 11:41 AM"
    "liquidity_facility": "",      # "LOC"
    "provider_identity": "",       # "CoBank"
    "expiration": "",              # "09/01/2026"
    "tender_agents": "",           # "BOKF"
}
```

**EXTRACTION STRATEGY:**

The snapshot section uses a key-value layout. The most reliable extraction approach:

```python
async def extract_snapshot(page):
    """Extract all snapshot data from the security detail page."""
    snapshot = {}
    
    # Method 1: Parse key-value pairs from the blue card
    # Look for label:value patterns in the container
    # The fields are typically in <strong> or <span> tags with labels
    
    # Extract CUSIP from header area
    cusip_elem = await page.query_selector("text=/CUSIP:/")
    # ...
    
    # Click Show More
    show_more = page.locator("text=Show More").first
    if await show_more.is_visible():
        await show_more.click()
        await asyncio.sleep(SHOW_MORE_DELAY)
    
    # Method 2: Get the entire HTML of the snapshot container
    # and parse with BeautifulSoup or regex
    snapshot_html = await page.locator(".security-detail-header").inner_html()
    # Parse key-value pairs from HTML
    
    return snapshot
```

**IMPORTANT:** The snapshot layout varies by security type:
- **Fixed rate bonds:** Show Interest Rate, no Reset Period/Max/Min Rate
- **Variable rate demand bonds:** Show Reset Period, Max Rate, Min Rate, Liquidity Facility
- **Some fields may be absent** — always handle missing fields gracefully

---

#### 3B: Interest Rate Tab

**Click the "Interest Rate" tab** (first tab in the row of tabs below the snapshot)

**Tab selector:** Look for tab elements — typically `<a>` or `<li>` elements in a tab bar. The tabs are:
- Interest Rate (active/selected by default in some cases)
- Trade Activity
- Ratings
- Disclosure Documents
- Final Scale
- Compare

**For Variable Rate securities**, this tab shows a table of rate resets:

```python
INTEREST_RATE_TABLE_COLUMNS = [
    "reset_date_time",           # "02/04/2026 03:11 PM"
    "interest_rate",             # "2.21" (numeric)
    "rate_type",                 # "R" (displayed as blue badge)
    "rate_effective_date",       # "02/05/2026"
    "aggregate_par_bank_bonds",  # "-" or dollar amount
    "aggregate_par_investors",   # "$8,000,000.00"
]
```

**CRITICAL — Pagination within the tab:**
- The default display is often 10 results
- **Change the display dropdown to 50 or 100** (look for `select` near "Display [X] results")
- If there are multiple pages, paginate through ALL of them
- Use the same First/Previous/1/2.../Next/Last pagination pattern

**For Fixed Rate securities**, this tab may show different content or be less populated.

```python
async def extract_interest_rate_tab(page):
    """Extract all interest rate data, handling pagination."""
    
    # Click Interest Rate tab
    await page.click("text=Interest Rate")  # or more specific selector
    await asyncio.sleep(TAB_SWITCH_DELAY)
    
    # Change display to max results
    display_select = page.locator("select").filter(has_text="results").first
    # Or locate by proximity to "Display" text
    await display_select.select_option("50")
    await page.wait_for_load_state("networkidle")
    
    all_rows = []
    
    while True:
        # Extract table rows
        rows = await extract_table_rows(page, "interest_rate")
        all_rows.extend(rows)
        
        # Check for next page within this tab
        next_btn = page.locator("text=Next").first
        if not await next_btn.is_visible() or await next_btn.is_disabled():
            break
        await next_btn.click()
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(BETWEEN_PAGES_DELAY)
    
    return all_rows
```

---

#### 3C: Trade Activity Tab

**Click the "Trade Activity" tab**

This tab contains trade history. The **Trade Details** are what we need.

```python
TRADE_ACTIVITY_COLUMNS = [
    "trade_date_time",       # Date and time of trade
    "trade_type",            # e.g., "Customer Bought", "Customer Sold", "Inter-dealer"
    "price",                 # Trade price
    "yield_pct",             # Yield percentage
    "par_traded",            # Par amount
    "dollar_price",          # Dollar price (may differ from price for some calcs)
    "settlement_date",       # Settlement date
]
```

**SAME PAGINATION HANDLING as Interest Rate tab:**
- Change display dropdown to 50/100
- Paginate through all pages
- The Trade Activity section may also have sub-views (Summary vs. Details) — ensure you're on the **Details** view

```python
async def extract_trade_activity_tab(page):
    """Extract all trade activity details."""
    
    # Click Trade Activity tab
    await page.click("text=Trade Activity")
    await asyncio.sleep(TAB_SWITCH_DELAY)
    
    # Ensure Trade Details view is selected (not Summary)
    # Look for a "Trade Details" link or view toggle
    trade_details_link = page.locator("text=Trade Details")
    if await trade_details_link.is_visible():
        await trade_details_link.click()
        await asyncio.sleep(1000)
    
    # Change display to max
    # ... same pagination pattern as interest rate ...
    
    all_rows = []
    # ... extract and paginate ...
    
    return all_rows
```

---

#### 3D: Ratings Tab

**Click the "Ratings" tab**

This tab shows credit rating history from the major agencies.

```python
RATINGS_DATA = {
    "current_ratings": {
        "fitch": "",           # Current Fitch rating
        "kbra": "",            # Current KBRA rating
        "moodys": "",          # Current Moody's rating
        "sp": "",              # Current S&P rating
    },
    "rating_history": [
        # Table of historical rating changes
        {
            "agency": "",       # Fitch, KBRA, Moody's, S&P
            "rating": "",       # e.g., "Aa3", "A", "BBB+"
            "rating_type": "",  # e.g., "Long-Term"
            "effective_date": "",
            "action": "",       # e.g., "New", "Upgrade", "Downgrade"
        }
    ]
}
```

```python
async def extract_ratings_tab(page):
    """Extract all ratings data."""
    
    await page.click("text=Ratings")
    await asyncio.sleep(TAB_SWITCH_DELAY)
    
    # Ratings tab typically has:
    # 1. Current ratings summary
    # 2. Historical ratings table
    
    # Extract both sections
    # ... parsing logic ...
    
    return ratings_data
```

---

#### 3E: Disclosure Documents Tab

**Click the "Disclosure Documents" tab**

**This is the most complex tab — it contains downloadable PDF documents.**

```python
DISCLOSURE_TYPES = [
    "Official Statement",
    "Preliminary Official Statement",
    "Letter of Credit",
    "Continuing Disclosure",
    "Annual Financial Information",
    "Material Event Notice",
    "Variable Rate Security Document",
    "Other",  # Catch-all
]
```

**Step-by-step for this tab:**

1. Click "Disclosure Documents" tab
2. Wait for document list to load
3. The documents are listed with:
   - Document type/description
   - Filing date
   - A clickable link (usually the document name or a PDF icon)
4. **Change display to show all documents** if paginated
5. For each document:
   - Record the document type, description, and filing date
   - Click the PDF link to download
   - Save to `output/pdfs/{CUSIP}/{document_type}_{date}.pdf`

```python
async def extract_disclosures_tab(page, cusip, pdf_dir):
    """Extract disclosure document metadata and download PDFs."""
    
    await page.click("text=Disclosure Documents")
    await asyncio.sleep(TAB_SWITCH_DELAY)
    
    # Change display to show all if needed
    # ...
    
    disclosures = []
    
    # Find all document rows
    doc_rows = await page.query_selector_all(".disclosure-row")  # Adjust selector
    
    for row in doc_rows:
        doc_info = {
            "type": await row.query_selector(".doc-type").inner_text(),
            "description": await row.query_selector(".doc-desc").inner_text(),
            "filing_date": await row.query_selector(".filing-date").inner_text(),
        }
        
        # Download PDF
        pdf_link = await row.query_selector("a[href*='.pdf']")
        if pdf_link:
            href = await pdf_link.get_attribute("href")
            doc_info["pdf_url"] = href
            doc_info["local_path"] = await download_pdf(
                page, href, cusip, doc_info["type"], doc_info["filing_date"], pdf_dir
            )
        
        disclosures.append(doc_info)
    
    return disclosures


async def download_pdf(page, url, cusip, doc_type, date, pdf_dir):
    """Download a PDF from EMMA disclosure documents."""
    
    # Create directory for this CUSIP
    cusip_dir = os.path.join(pdf_dir, cusip)
    os.makedirs(cusip_dir, exist_ok=True)
    
    # Sanitize filename
    safe_type = doc_type.replace(" ", "_").replace("/", "-")
    safe_date = date.replace("/", "-")
    filename = f"{safe_type}_{safe_date}.pdf"
    filepath = os.path.join(cusip_dir, filename)
    
    # Use Playwright download handling
    # EMMA PDFs may open in new tab or trigger download
    async with page.expect_download() as download_info:
        await page.click(f"a[href='{url}']")
    download = await download_info.value
    await download.save_as(filepath)
    
    # Alternative: If PDF opens in new tab instead of downloading
    # Use page.context.expect_page() to catch new tabs
    # Then save the content
    
    return filepath
```

**PDF DOWNLOAD EDGE CASES:**
- Some PDFs open in a new browser tab rather than triggering a download — handle both scenarios
- Some documents may be hosted on external URLs (not emma.msrb.org) — follow redirects
- Large official statements can be 200+ pages — set appropriate timeouts
- If a download fails, log it and continue (don't halt the entire crawl)

---

## 6. DATA MODELS

### 6.1 Security Record (Complete)

```python
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class SecuritySnapshot:
    cusip: str
    security_name: str
    short_name: str
    state: str
    interest_rate: Optional[float]
    maturity_date: str
    dated_date: str
    principal_amount: float
    closing_date: str
    fiscal_year_end: Optional[str]
    # Variable rate fields (may be None for fixed)
    reset_period: Optional[str]
    maximum_rate: Optional[float]
    minimum_rate: Optional[float]
    # Show More fields
    minimum_denomination: Optional[float]
    notification_period: Optional[str]
    initial_offering_price_yield: Optional[str]
    remarketing_agent: Optional[str]
    time_formal_award: Optional[str]
    time_first_execution: Optional[str]
    liquidity_facility: Optional[str]
    provider_identity: Optional[str]
    provider_expiration: Optional[str]
    tender_agents: Optional[str]
    # Source metadata
    emma_url: str
    crawl_timestamp: str

@dataclass
class InterestRateRecord:
    reset_date_time: str
    interest_rate: float
    rate_type: str
    rate_effective_date: str
    aggregate_par_bank_bonds: Optional[float]
    aggregate_par_investors: Optional[float]

@dataclass
class TradeRecord:
    trade_date_time: str
    trade_type: str
    price: Optional[float]
    yield_pct: Optional[float]
    par_traded: Optional[float]
    dollar_price: Optional[float]
    settlement_date: Optional[str]

@dataclass
class RatingRecord:
    agency: str
    rating: str
    rating_type: str
    effective_date: str
    action: Optional[str]

@dataclass
class DisclosureDocument:
    doc_type: str
    description: str
    filing_date: str
    pdf_url: Optional[str]
    local_pdf_path: Optional[str]
    download_success: bool

@dataclass
class SecurityComplete:
    snapshot: SecuritySnapshot
    interest_rates: List[InterestRateRecord] = field(default_factory=list)
    trades: List[TradeRecord] = field(default_factory=list)
    ratings: List[RatingRecord] = field(default_factory=list)
    disclosures: List[DisclosureDocument] = field(default_factory=list)
```

---

## 7. CHECKPOINT & RESUME SYSTEM

**The crawler MUST support resume capability.** EMMA crawls can take hours and connections may drop.

```python
# checkpoint.json structure
{
    "search_params_hash": "abc123",        # Hash of search params to detect config changes
    
    # Phase 2 status
    "phase2_complete": true,               # Has the full queue been collected?
    "phase2_last_page_scanned": 12,        # Last results page successfully scanned
    "phase2_securities_queued": 45,        # Total qualifying securities found
    "processing_queue_file": "output/processing_queue.json",  # Path to saved queue
    
    # Phase 3 status — keyed by URL hash (CUSIP not available until page load)
    "completed_hashes": [                  # Successfully processed (URL hashes)
        "A463E7B905E3D1D78EC0E5CD06C252733",
        "B812F9C304D2A1E67FA1B4DE15D363844"
    ],
    "hash_to_cusip": {                     # Mapping discovered during extraction
        "A463E7B905E3D1D78EC0E5CD06C252733": "46245EBA4",
        "B812F9C304D2A1E67FA1B4DE15D363844": "12345XYZ1"
    },
    "failed_hashes": {                     # Failed with error info
        "C999F0D405E3B2F78GC2C6EF17E474955": {
            "error": "Timeout on Trade Activity tab",
            "phase": "detail_extraction",
            "attempts": 3,
            "last_attempt": "2026-02-06T10:30:00",
            "cusip": "99999ABC0",          # May be null if failed before CUSIP extraction
            "partial_data_saved": true
        }
    },
    "partial_hashes": {                    # Completed but with incomplete tab data
        "D555E1E506F4C3G89HD3D7FG28F585066": {
            "cusip": "55555DEF0",
            "missing_tabs": ["trade_activity"],
            "reason": "session_loss_mid_tab"
        }
    },
    "last_updated": "2026-02-06T10:30:00"
}
```

**Resume logic:**
1. On startup, check for existing checkpoint file
2. If `phase2_complete` is `false`: resume Phase 2 from `phase2_last_page_scanned`
   - Use `recover_results_session()` to re-execute search and jump to that page
3. If `phase2_complete` is `true`: load the `processing_queue_file` from disk
4. Skip securities whose URL hash is in `completed_hashes`
5. Retry securities in `failed_hashes` that haven't exceeded max_retries
6. Optionally re-attempt `partial_hashes` to fill in missing tabs
7. Log resume status clearly:
   ```
   [RESUME] Phase 2: COMPLETE (45 securities queued)
   [RESUME] Phase 3: 28/45 completed, 2 failed, 1 partial, 14 remaining
   [RESUME] Known CUSIPs: 46245EBA4, 12345XYZ1, ... (28 mapped)
   ```

---

## 8. ERROR HANDLING & RESILIENCE

### 8.1 Session & ViewState Management

> **THE #1 FAILURE MODE: EMMA's ASP.NET ViewState Expiry**
>
> EMMA's results pages are stateful server-side objects. They are NOT bookmarkable URLs.
> When you navigate away (to a security detail page) and try to come back, the server 
> may have already discarded that session state. This manifests as:
> - A ViewState validation error page
> - A redirect to the blank search form
> - A generic ASP.NET error page
> - A page that loads but shows no results
>
> The **collect-first architecture** (Phase 2 completes fully before Phase 3 starts) 
> eliminates this as a problem between securities. However, session expiry CAN still 
> occur DURING Phase 2 pagination or DURING a long security detail extraction.

**Session Health Detection:**

```python
async def is_session_healthy(page):
    """
    Check if we're still on a valid EMMA page with an active session.
    Returns (healthy: bool, page_type: str)
    """
    current_url = page.url
    
    # Check for known error states
    error_indicators = [
        # ASP.NET ViewState validation failure
        page.locator("text=Validation of viewstate MAC failed"),
        # Generic ASP.NET error
        page.locator("text=Server Error in"),
        page.locator("text=Runtime Error"),
        # Session timeout redirect
        page.locator("text=Your session has expired"),
        # Blank/reset search form (unexpected redirect)
    ]
    
    for indicator in error_indicators:
        if await indicator.is_visible(timeout=1000):
            return False, "error_page"
    
    # Identify what page we're on
    if "Search.aspx" in current_url:
        # Check if this is the search form (blank) or has results
        results_count = page.locator("text=/\\d+ securities/i")
        if await results_count.is_visible(timeout=2000):
            return True, "results_page"
        else:
            return True, "search_form"  # May need to re-run search
    
    if "SecurityDetail" in current_url:
        cusip_elem = page.locator("text=/CUSIP:/")
        if await cusip_elem.is_visible(timeout=2000):
            return True, "security_detail"
        else:
            return False, "broken_detail"
    
    return False, "unknown"
```

**Recovery During Phase 2 (Results Pagination):**

If the session expires while paginating through results, the crawler must re-execute the search and re-navigate to the correct page:

```python
async def recover_results_session(page, config, target_page):
    """
    Re-execute the search and navigate back to a specific results page.
    
    This is needed when EMMA's ViewState expires during Phase 2 pagination.
    For example: you've scanned pages 1-5, the session expires on page 6,
    so you re-run the search and jump directly to page 6.
    """
    logger.warning(f"Session expired during results pagination. Recovering to page {target_page}...")
    
    # Step 1: Navigate fresh to search page
    await page.goto("https://emma.msrb.org/Search/Search.aspx", 
                    wait_until="networkidle", timeout=60000)
    
    # Step 2: Re-populate search filters
    await populate_search_filters(page, config["search_filters"])
    
    # Step 3: Execute search
    await click_run_search(page)
    await page.wait_for_load_state("networkidle")
    
    # Step 4: Set display to 50 results per page
    await set_results_per_page(page, 50)
    
    # Step 5: Navigate to the target page
    if target_page > 1:
        # Try clicking the page number directly if visible
        page_link = page.locator(f"a:text-is('{target_page}')").first
        if await page_link.is_visible(timeout=2000):
            await page_link.click()
            await page.wait_for_load_state("networkidle")
        else:
            # Navigate page by page (slower but reliable)
            for p in range(1, target_page):
                next_btn = page.locator("text=Next").first
                await next_btn.click()
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(1)
    
    # Step 6: Verify we're on the right page
    logger.info(f"Session recovered. Now on results page {target_page}")
    return True
```

**Recovery During Phase 3 (Security Detail Pages):**

Phase 3 uses direct URL navigation, so ViewState expiry on the results page is irrelevant. However, EMMA may still have issues loading individual security pages:

```python
async def navigate_to_security_with_recovery(page, detail_url, max_retries=3):
    """
    Navigate to a security detail page with session-aware recovery.
    
    Unlike results pages, security detail pages ARE directly addressable 
    by URL, so recovery simply means retrying the navigation.
    """
    for attempt in range(max_retries):
        try:
            await page.goto(detail_url, wait_until="networkidle", timeout=60000)
            
            healthy, page_type = await is_session_healthy(page)
            
            if healthy and page_type == "security_detail":
                return True
            
            if page_type == "error_page":
                logger.warning(
                    f"EMMA error page on attempt {attempt+1}. "
                    f"Waiting before retry..."
                )
                # Clear the error state with a fresh navigation
                await page.goto("https://emma.msrb.org", wait_until="networkidle")
                await asyncio.sleep(5 * (attempt + 1))  # Escalating backoff
                continue
            
            if page_type == "search_form":
                logger.warning(
                    f"Redirected to search form on attempt {attempt+1}. "
                    f"Session may have expired. Retrying direct URL..."
                )
                await asyncio.sleep(3)
                continue
            
            # Unexpected state
            logger.warning(f"Unexpected page state: {page_type}. Retrying...")
            await asyncio.sleep(3)
            
        except Exception as e:
            logger.warning(f"Navigation error on attempt {attempt+1}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5 * (attempt + 1))
    
    return False
```

**Within-Tab Session Handling:**

Even within a single security detail page, extracting data from multiple tabs with heavy pagination (e.g., 200+ trade records across many pages) can take long enough for EMMA to get unhappy. Handle this per-tab:

```python
async def extract_tab_with_session_guard(page, tab_name, extractor_func, cusip):
    """
    Wrapper that detects mid-extraction session loss within a tab.
    
    If the session dies while paginating within a tab (e.g., page 3 of 8 
    in Trade Activity), the crawler saves what it has and marks the 
    extraction as partial rather than crashing.
    """
    try:
        data = await extractor_func(page)
        return {"status": "success", "data": data}
    
    except Exception as e:
        # Check if this is a session issue
        healthy, page_type = await is_session_healthy(page)
        
        if not healthy:
            logger.error(
                f"Session lost during {tab_name} extraction for {cusip}. "
                f"Page state: {page_type}. Saving partial data."
            )
            return {"status": "partial_session_loss", "data": [], "error": str(e)}
        
        # Not a session issue — some other error
        logger.error(f"Error in {tab_name} for {cusip}: {e}")
        return {"status": "failed", "data": [], "error": str(e)}
```

### 8.2 Retry Strategy

```python
# Exponential backoff with jitter
import random

async def retry_with_backoff(func, max_retries=3, base_delay=5):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying in {delay:.1f}s")
            await asyncio.sleep(delay)
```

### 8.3 Common Failure Scenarios

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| **ViewState expired (results page)** | Error page or redirect to blank search on pagination | `recover_results_session()` — re-run search, jump to target page |
| **ViewState expired (back navigation)** | Error page when trying to return to results | N/A — architecture eliminates this by never going back |
| **Session expired (detail page load)** | Redirect to search form or error page on `goto()` | Retry direct URL up to 3x with escalating backoff |
| **Session lost mid-tab extraction** | Error or redirect during tab pagination | Save partial data, mark tab as `partial_session_loss` |
| EMMA server timeout | `TimeoutError` on navigation | Retry with longer timeout |
| Empty results table | No `<tr>` elements in table body | Log warning, check selectors |
| Missing tab content | Tab click produces no table | Log as partial data, continue |
| PDF download failure | Download timeout or HTTP error | Log failure, continue to next doc |
| CAPTCHA/bot detection | Unusual page content | Pause, alert user, increase delays |
| Stale element reference | `Element detached` error | Re-query the element |
| Principal amount parse error | Non-numeric text in amount column | Log warning, skip row |

### 8.4 Graceful Degradation

If a specific tab fails for a security, **still save the data from other tabs**. The record should indicate which tabs were successfully extracted:

```python
security_record = {
    "cusip": "46245EBA4",
    "extraction_status": {
        "snapshot": "success",
        "interest_rate": "success",
        "trade_activity": "failed",     # Still save what we got
        "ratings": "success",
        "disclosures": "partial"        # Some PDFs failed
    }
}
```

---

## 9. OUTPUT FORMAT

### 9.1 Per-Security JSON

Save one JSON file per security: `output/data/{CUSIP}.json`

```json
{
    "cusip": "46245EBA4",
    "crawl_metadata": {
        "crawl_timestamp": "2026-02-06T10:30:00",
        "emma_url": "https://emma.msrb.org/...",
        "extraction_status": {
            "snapshot": "success",
            "interest_rate": "success",
            "trade_activity": "success",
            "ratings": "success",
            "disclosures": "success"
        }
    },
    "snapshot": {
        "security_name": "IOWA FINANCE AUTHORITY VARIABLE RATE DEMAND...",
        "interest_rate": 2.21,
        "maturity_date": "05/01/2046",
        "principal_amount": 8000000,
        "...": "..."
    },
    "interest_rates": [
        {
            "reset_date_time": "02/04/2026 03:11 PM",
            "interest_rate": 2.21,
            "rate_type": "R",
            "rate_effective_date": "02/05/2026",
            "aggregate_par_bank_bonds": null,
            "aggregate_par_investors": 8000000
        }
    ],
    "trades": [...],
    "ratings": [...],
    "disclosures": [
        {
            "doc_type": "Official Statement",
            "filing_date": "05/28/2025",
            "pdf_url": "https://...",
            "local_pdf_path": "output/pdfs/46245EBA4/Official_Statement_05-28-2025.pdf",
            "download_success": true
        }
    ]
}
```

### 9.2 Summary CSV

Also produce a master CSV: `output/data/waste_bonds_summary.csv`

Columns:
```
cusip, security_name, state, principal_amount, coupon_pct, maturity_date, dated_date,
closing_date, interest_rate_current, rate_type, source_of_repayment,
rating_fitch, rating_kbra, rating_moodys, rating_sp,
liquidity_facility, provider_identity, remarketing_agent,
num_trades, num_rate_resets, num_disclosures,
emma_url, crawl_timestamp
```

---

## 10. SELECTOR DISCOVERY STRATEGY

**EMMA's DOM structure uses ASP.NET Web Forms, which means element IDs are long and auto-generated.** The crawler should use a MULTI-STRATEGY approach for finding elements:

### Priority Order for Element Location:

1. **Semantic text content:** `page.locator("text=Run Search")` — most resilient to ID changes
2. **Partial ID match:** `page.locator("[id*='txtIssueDescription']")` — catches ASP.NET generated IDs
3. **Label association:** Find label text, then locate adjacent input
4. **CSS class selectors:** Less reliable on EMMA but useful for containers
5. **XPath (last resort):** For complex structural relationships

### Discovery Script

**Before building the full crawler, create a discovery script** that:

```python
async def discover_selectors(page):
    """
    Navigate to each page state and dump the DOM structure
    to identify reliable selectors.
    """
    # 1. Search page — dump form element IDs
    await page.goto("https://emma.msrb.org/Search/Search.aspx")
    form_elements = await page.query_selector_all("input, select, button, a")
    for el in form_elements:
        id_attr = await el.get_attribute("id")
        name_attr = await el.get_attribute("name")
        type_attr = await el.get_attribute("type")
        text = await el.inner_text() if await el.is_visible() else ""
        print(f"ID: {id_attr}, Name: {name_attr}, Type: {type_attr}, Text: {text[:50]}")
    
    # 2. Save full page HTML for offline analysis
    html = await page.content()
    with open("emma_search_page.html", "w") as f:
        f.write(html)
    
    # ... repeat for results page and security detail page
```

**Run this discovery script FIRST and use the output to refine all selectors before building the full crawler.**

---

## 11. RATE LIMITING & ETHICAL CRAWLING

### MANDATORY Rules:

1. **Minimum 2-second delay between page loads** — EMMA is a public service, not a commercial API
2. **Minimum 3-second delay between security detail pages** — these are the heaviest pages
3. **Maximum 1 concurrent request** — never parallelize against EMMA
4. **Respect robots.txt** — check `https://emma.msrb.org/robots.txt` first
5. **Set a descriptive User-Agent** — identify the crawler purpose
6. **If you receive HTTP 429 or detect throttling** — back off exponentially, minimum 30 seconds
7. **Run during off-peak hours** (evenings/weekends Eastern time) when possible
8. **Do NOT run multiple instances** of the crawler simultaneously

### Session Management:

```python
# EMMA may use session cookies — preserve them
context = await browser.new_context(
    user_agent="MuniPal-StandardModel/1.0 (Research; contact: stephen@launchshop.com)",
    accept_downloads=True,
)
```

---

## 12. TESTING & VALIDATION

### 12.1 Unit Test Approach

Test each module independently:

```python
# Test search filter population
async def test_search_filters():
    # Navigate to search page
    # Populate one filter at a time
    # Verify field values are set correctly
    # Run search with known parameters
    # Verify expected result count

# Test results parsing
async def test_results_extraction():
    # Navigate to known search results
    # Extract one page
    # Verify column parsing
    # Verify principal amount filtering

# Test security detail extraction
async def test_security_detail():
    # Navigate directly to KNOWN security URL:
    #   https://emma.msrb.org/Security/Details/A463E7B905E3D1D78EC0E5CD06C252733
    # Extract CUSIP from page content — verify it equals "46245EBA4"
    # Extract snapshot — verify against known values:
    #   Interest Rate: 2.21%
    #   Maturity: 05/01/2046
    #   Principal: $8,000,000
    #   Provider: CoBank
    # Extract each tab
    # Verify data integrity
```

### 12.2 Known Test Security

Use **CUSIP 46245EBA4** (Iowa Finance Authority Variable Rate Demand Solid Waste Disposal Revenue Bonds) as the validation benchmark.

**Known EMMA URL:** `https://emma.msrb.org/Security/Details/A463E7B905E3D1D78EC0E5CD06C252733`

> **Note:** The URL hash above was captured from live EMMA browsing. If EMMA regenerates 
> internal IDs, this URL may stop working. In that case, use `--test-cusip 46245EBA4` 
> which will search EMMA for the CUSIP and discover its current URL.

```python
KNOWN_SECURITY = {
    "cusip": "46245EBA4",
    "emma_url": "https://emma.msrb.org/Security/Details/A463E7B905E3D1D78EC0E5CD06C252733",
    "url_hash": "A463E7B905E3D1D78EC0E5CD06C252733",
    "interest_rate": 2.21,
    "maturity_date": "05/01/2046",
    "dated_date": "05/28/2025",
    "principal_amount": 8000000,
    "reset_period": "7 days",
    "maximum_rate": 10.00,
    "minimum_rate": 0.00,
    "closing_date": "05/28/2025",
    "minimum_denomination": 100000,
    "remarketing_agent": "Thornton Farish Inc.",
    "liquidity_facility": "LOC",
    "provider_identity": "CoBank",
    "expiration": "09/01/2026",
    "tender_agents": "BOKF",
}
```

### 12.3 Validation Checks

After a full crawl run, validate:
- [ ] All qualifying securities have snapshot data
- [ ] No duplicate CUSIPs in output
- [ ] All principal amounts >= $8,000,000
- [ ] JSON files are valid and parseable
- [ ] CSV summary row count matches JSON file count
- [ ] PDF files are valid (non-zero size, valid PDF headers)
- [ ] Checkpoint file is consistent with actual output

---

## 13. EXECUTION INSTRUCTIONS

### Initial Development Run:

```bash
# Step 1: Run selector discovery
python src/discover_selectors.py --save-html

# Step 2: Test with single known security by direct URL (not CUSIP)
#   Use a URL captured from manual browsing or a previous Phase 2 run
python src/main.py --test-url "https://emma.msrb.org/Security/Details/A463E7B905E3D1D78EC0E5CD06C252733"

# Step 2b: Alternatively, search for a CUSIP and test the first match
#   This runs a search, finds the security, then extracts its data
python src/main.py --test-cusip 46245EBA4

# Step 3: Run Phase 2 only (collect queue without extracting details)
python src/main.py --phase2-only

# Step 4: Run Phase 3 on first 3 qualifying securities from saved queue
python src/main.py --phase3-only --max-securities 3

# Step 5: Full crawl (Phase 2 + Phase 3)
python src/main.py

# Step 6: Resume interrupted crawl (auto-detects phase from checkpoint)
python src/main.py --resume

# Step 7: Retry only failed securities
python src/main.py --retry-failed

# Step 8: Re-attempt partial extractions (fill in missing tabs)
python src/main.py --retry-partial
```

### CLI Arguments:

```
--config PATH           Path to config directory (default: ./config/)
--headless / --visible  Browser visibility (default: headless)
--max-securities N      Limit processing to N securities (for testing)
--test-url URL          Test extraction on a single security by direct EMMA URL
--test-cusip CUSIP      Search EMMA for this CUSIP, find its URL, then test extraction
                        (Note: this runs a quick search, NOT a URL construction — 
                        EMMA URLs use opaque hashes, not CUSIPs)
--phase2-only           Only run Phase 2: collect qualifying URLs into queue
--phase3-only           Only run Phase 3: process securities from saved queue
--resume                Resume from checkpoint (auto-detects current phase)
--retry-failed          Retry only previously failed securities
--retry-partial         Re-attempt securities with partial tab data
--output-dir PATH       Override output directory
--log-level LEVEL       Override log level (DEBUG, INFO, WARNING)
--dry-run               Parse results but don't extract details (like phase2-only)
```

> **Implementation note for `--test-cusip`:**
> Since EMMA URLs don't contain CUSIPs, `--test-cusip 46245EBA4` must:
> 1. Navigate to EMMA search
> 2. Enter the CUSIP in the appropriate search field (EMMA has a CUSIP search)
> 3. Find the matching security in results
> 4. Capture its opaque hash URL
> 5. Then proceed with normal Phase 3 extraction on that URL
>
> `--test-url` is simpler and preferred for development since it skips the search step.

---

## 14. FUTURE EXTENSIBILITY

This crawler architecture should be designed for reuse across the four Standard Model sectors:

| Sector | Issue Description Filter | Source of Repayment | Additional Filters |
|--------|-------------------------|--------------------|--------------------|
| Waste | "waste" | Revenue | — |
| Healthcare | "hospital" OR "health" | Revenue | — |
| Education | "school" OR "university" | Revenue or GO | — |
| Multi-Family | "multi-family" OR "housing" | Revenue | — |

The `search_params.yaml` config file should be the ONLY thing that changes between sector crawls. All extraction logic remains the same.

---

## 15. CRITICAL REMINDERS FOR CLAUDE CODE

1. **NEVER USE THE BROWSER BACK BUTTON** — This is the single most important rule. EMMA's ASP.NET ViewState means the results page cannot be revisited after navigating away. The architecture uses collect-first (Phase 2 scans all results pages into a queue) then process (Phase 3 navigates directly to each security URL). There is no "return to results" in Phase 3.

2. **IGNORE EMMA's "Return to Search Results" LINK** — EMMA's security detail pages may display a "Return to Search Results" or similar link. **DO NOT USE IT.** It relies on the same server-side ViewState as browser back, and will fail unpredictably — sometimes it works (session is still alive), sometimes it returns a ViewState error, sometimes it dumps you to a blank search form. The crawler must never depend on it.

3. **Two-phase execution is mandatory** — Phase 2 (collect qualifying URLs) MUST fully complete and save `processing_queue.json` to disk BEFORE Phase 3 (extract security details) begins. This decouples detail extraction from results page session state entirely.

3. **Direct URL navigation only** — In Phase 3, every security is accessed via `page.goto(detail_url)`. Never click links on the results page to reach securities. The results page may not even exist anymore.

4. **Session health checks** — Before extracting data on any page, verify you're actually on the expected page. EMMA can silently redirect to the search form or an error page. Use `is_session_healthy()` before every extraction step.

5. **Save early, save often** — Each security's data is saved to disk immediately after extraction, not batched. If the crawler crashes on security #30 of 45, you still have 29 complete records.

6. **ASP.NET ViewState** — EMMA uses server-side state management. Never try to bypass the form; always interact through the DOM.

7. **Dynamic element IDs** — ASP.NET generates IDs like `ctl00$mainContentArea$...`. Use partial ID matching (`[id*='keyword']`) rather than exact IDs.

8. **Postback handling** — Dropdown changes may trigger full or partial page reloads. Always wait for `networkidle` after changing form values.

9. **Tab content is lazy-loaded** — Tab content only appears after clicking the tab. Don't try to extract all tabs from the initial page HTML.

10. **"Show More" is a toggle** — It changes to "Show Less" after clicking. Don't click it again or the content will collapse.

11. **Principal Amount format** — Values in the results table are formatted as `8,000,000` (no dollar sign, with commas). On the detail page they're `$8,000,000` (with dollar sign). Handle both formats.

12. **Variable vs. Fixed rate** — The page layout differs between security types. Build extraction logic that handles both gracefully.

13. **PDF downloads** — EMMA disclosure PDFs may open in a new tab OR trigger a download depending on browser config. Configure Playwright to handle downloads:
    ```python
    context = await browser.new_context(accept_downloads=True)
    ```

14. **EMMA server stability** — EMMA occasionally has slow response times or brief outages. Build in generous timeouts (60s+) and retry logic.

15. **Data integrity** — Always verify extracted data makes sense (e.g., interest rates between 0-100, dates are valid, principal amounts are positive numbers).

16. **Mid-tab session loss** — If extracting a tab with many pages of data (e.g., 200+ trades across 4 pages), the session can expire between pagination clicks within the tab. The crawler should save partial tab data rather than discarding it, and mark the tab as `partial_session_loss` in the extraction status.

---

## APPENDIX A: EMMA URL PATTERNS

```
Search Page:
https://emma.msrb.org/Search/Search.aspx

Security Detail (OPAQUE HASH — not CUSIP-based):
https://emma.msrb.org/Security/Details/{INTERNAL_HASH}
Example: https://emma.msrb.org/Security/Details/A463E7B905E3D1D78EC0E5CD06C252733

IMPORTANT: The hash is an internal EMMA identifier, NOT derived from the CUSIP.
You CANNOT construct this URL from a CUSIP. You MUST capture the href 
from the results table during Phase 2. These URLs ARE directly navigable
(unlike the results page), which is what makes the collect-first architecture work.

Issuer Homepage:
https://emma.msrb.org/IssuerView/IssuerHomePage.aspx?issuerId={ID}

Issue Detail:
https://emma.msrb.org/IssuerView/IssueDetail.aspx?issueId={ID}

Disclosure Document (PDF):
https://emma.msrb.org/ES{DOCUMENT_ID}.pdf
(or similar pattern — varies by document; capture actual href from Disclosures tab)
```

> **URL Discovery Notes for Claude Code:**
> - During selector discovery (Step 1), inspect the `<a>` tags in the results table 
>   to confirm the actual href pattern. It may be a relative URL like 
>   `/Security/Details/A463E7B9...` that needs to be resolved against the base URL.
> - The hash length and character set may vary — don't assume a fixed length.
> - If EMMA changes the URL pattern, the crawler should still work because it 
>   captures whatever href is in the results table rather than constructing URLs.

## APPENDIX B: SAMPLE RATE RESET DATA (For Validation)

From CUSIP 46245EBA4 Interest Rate tab:

| Reset Date/Time | Rate | Type | Effective Date | Bank Bonds | Investors & Remarketing |
|---|---|---|---|---|---|
| 02/04/2026 03:11 PM | 2.21 | R | 02/05/2026 | - | $8,000,000.00 |
| 01/28/2026 03:01 PM | 2.32 | R | 01/29/2026 | - | $8,000,000.00 |
| 01/21/2026 03:11 PM | 1.34 | R | 01/22/2026 | - | $8,000,000.00 |
| 01/14/2026 03:09 PM | 1.32 | R | 01/15/2026 | - | $8,000,000.00 |
| 01/07/2026 03:13 PM | 1.41 | R | 01/08/2026 | - | $8,000,000.00 |
| 12/31/2025 12:15 PM | 2.45 | R | 01/01/2026 | - | $8,000,000.00 |
| 12/24/2025 11:49 AM | 3.36 | R | 12/25/2025 | - | $8,000,000.00 |
| 12/17/2025 03:33 PM | 3.31 | R | 12/18/2025 | - | $8,000,000.00 |
| 12/10/2025 03:33 PM | 3.16 | R | 12/11/2025 | - | $8,000,000.00 |
| 12/03/2025 04:11 PM | 1.96 | R | 12/04/2025 | - | $8,000,000.00 |
| 11/26/2025 12:55 PM | 2.83 | R | 11/27/2025 | - | $8,000,000.00 |
| 11/19/2025 03:44 PM | 2.82 | R | 11/20/2025 | - | $8,000,000.00 |
| 11/12/2025 03:25 PM | 2.49 | R | 11/13/2025 | - | $8,000,000.00 |
