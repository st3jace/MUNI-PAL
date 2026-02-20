# Research Workflows

**Version:** 1.0 | **Created:** 2026-02-18
**Purpose:** Operational procedures for each research task type

---

## WORKFLOW 1: SECTOR DEEP DIVE

### Purpose
Produce a comprehensive analysis of a municipal bond sector, establishing the knowledge foundation for credit analysis, comparable studies, and corpus building.

### Input
- Sector name (e.g., "solid waste revenue bonds", "hospital revenue bonds", "CCRC bonds")
- Depth: "survey" (broad overview) or "comprehensive" (full analytical treatment)
- Specific sub-questions (optional)

### Procedure

**Step 1 — Scope Definition**
- Define the sector boundaries (what's in, what's out)
- Identify sub-sectors and their structural distinctions
- List the key credit drivers unique to this sector

**Step 2 — Market Structure**
- Total outstanding par amount and number of issuers
- Typical deal size ranges
- Geographic distribution
- Rating distribution (what % IG vs. HY vs. unrated)
- Historical issuance volume trends
- Sources: EMMA search, MSRB data, rating agency sector reports

**Step 3 — Deal Structure Analysis**
- Typical bond structures (serial vs. term, fixed vs. variable, tax status)
- Common security packages (pledge type, lien structure, enhancements)
- Typical covenant framework (DSCR levels, rate covenants, ABT)
- Flow of funds waterfall (sector-standard)
- Call provisions and redemption features

**Step 4 — Credit Driver Mapping**
- Identify the 5-8 key credit drivers for the sector
- For each driver: definition, measurement, typical ranges by rating category
- Map each driver to the Summers fundamental scoring dimensions
- Identify data sources for each driver

**Step 5 — Rating Agency Perspective**
- Summarize Moody's, S&P, and Fitch sector methodologies (from public documents)
- Key rating factors and their relative weights
- Common credit strengths and challenges cited in rating actions
- Historical rating migration patterns for the sector
- If available: reference EMMA corpus rating action factors

**Step 6 — Default and Recovery**
- Historical default rates for the sector (Moody's municipal default studies)
- Common causes of default in this sector
- Recovery rates and their determinants
- Notable case studies (significant defaults or workouts)

**Step 7 — Benchmark Financial Metrics**
- Compile median, 25th percentile, 75th percentile for key financial metrics
- Segment by rating category where data permits
- Sources: EMMA financial reports, rating agency medians reports
- Connect to Summers Phase 1 scoring thresholds

**Step 8 — Synthesis and Output**

### Output
- `research/corpus/{sector}/sector_analysis.md` — Main research memo (YAML frontmatter per charter)
- `research/corpus/{sector}/credit_drivers.json` — Structured credit driver dataset
- `research/corpus/{sector}/financial_benchmarks.json` — Benchmark financial metrics
- `research/corpus/{sector}/rating_methodology_summary.md` — Rating agency methodology digest

### Quality Checklist
- [ ] All factual claims sourced
- [ ] Credit drivers mapped to Summers scoring dimensions
- [ ] Financial benchmarks segmented by rating category
- [ ] Rating agency perspectives from at least 2 agencies
- [ ] Default/recovery data included
- [ ] Healthcare: all sub-sectors (hospital, CCRC, senior living, behavioral) addressed
- [ ] YAML frontmatter complete with confidence score

---

## WORKFLOW 2: COMPARABLE ISSUANCE ANALYSIS

### Purpose
Identify and analyze municipal bond issuances comparable to a subject project or credit, providing market context for structure, pricing, and credit positioning.

### Input
- Subject project profile: issuer type, sector, geography, size, proposed structure
- Comparison criteria (which dimensions matter most): structure, size, rating, geography, sector, vintage

### Procedure

**Step 1 — Define Comparability Criteria**
- Primary criteria: sector + structure type (e.g., solid waste revenue bonds)
- Secondary criteria: par amount range (+/- 50%), rating category, geography (region or state), vintage (last 5 years preferred)
- Identify minimum acceptable comparables: 3-5 deals

**Step 2 — Source Comparable Deals**
- EMMA search: filter by sector, issuer type, date range
- Rating agency pre-sale reports (if accessible)
- Bond Buyer / municipal market publications
- Existing EMMA corpus data (for waste sector)

**Step 3 — Extract Deal Data**
For each comparable, compile:
- Issuer, obligated person, date of issuance
- Par amount, tax status, structure (serial/term/CAB)
- Ratings (Moody's, S&P, Fitch) at issuance and current
- Coupon rates, yield at issuance, spread to AAA MMD
- Security package (pledge, lien, enhancements)
- Key covenants (DSCR minimum, ABT, rate covenant)
- Financial metrics at time of issuance (DSCR, days cash, operating margin)

**Step 4 — Comparative Analysis**
- Build comparison table (deals as columns, metrics as rows)
- Identify structural similarities and differences
- Note pricing implications of structural differences
- Calculate spread dispersion across comparables
- Assess how the subject project would position relative to comparables

**Step 5 — Takeaways**

### Output
- `research/memos/comparable_analysis_{subject}_{date}.md` — Comparative memo
- Deal summary table (markdown)
- Financial metric comparison table
- Structural feature comparison table
- Positioning assessment for subject project

### Quality Checklist
- [ ] Minimum 3 comparables identified
- [ ] All deal data sourced and verified
- [ ] Spread to AAA MMD calculated for each comparable
- [ ] Subject project positioned relative to comparables
- [ ] Structural differences and their pricing implications noted

---

## WORKFLOW 3: CREDIT RISK ASSESSMENT (Summers Framework)

### Purpose
Apply the Summers analytical framework to evaluate a specific municipal bond credit, producing a quantitative assessment with signal quality awareness.

### Input
- Obligor name + available data (financial statements, EMMA filings, rating actions)
- Sector classification
- Available return data (EMMA trades, equity ticker if applicable)

### Procedure

**Step 1 — Data Inventory**
- What financial data is available? (CAFRs, audits, continuing disclosures)
- What EMMA trade data exists? (count trades, date range, price dispersion)
- What rating actions exist? (history, current rating, outlook)
- What structural data exists? (indenture terms, covenants, enhancement)
- Assess data sufficiency: is there enough for S_Omega? SIC? F_i only?

**Step 2 — Phase 1: Fundamental Score (F_i)**
- Apply sector-appropriate scoring template (see `02-summers-analytical-framework.md` Section 2.3)
- Score each dimension with available data
- Note which dimensions have data gaps (score as N/A, not zero)
- Compute weighted F_i
- Compare to investable threshold (50.0)
- Compare to sector peers

**Step 3 — Phase 2: S_Omega and SIC (if data permits)**
- Build return series (use synthetic return cascade if no equity ticker)
- Report observation count, date range, P_BSE, A(S_Omega)
- Compute S_Omega if n >= 20 (with caveats if n < 50)
- Compute SIC matrix: [R_A, E_A, MDDD_S]
- Use tax-exempt r_f if applicable
- Construct or reference sector benchmark

**Step 4 — Phase 3: Relative Positioning (if benchmark exists)**
- Position credit within CRI framework
- Generate relative value signal (overweight/equal/underweight)
- Compare SIC components to sector benchmark

**Step 5 — Phase 4-5: Signal Extraction (if data permits)**
- Only attempt if sufficient return data (30+ observations minimum for meaningful spectral analysis)
- Report signal quality classification
- Compute extended Omega variants if signal quality >= moderate
- Note: for most pure municipal credits, this phase will produce "weak" signal quality — that's expected

**Step 6 — Synthesis**
- Combine quantitative scores with qualitative assessment
- Highlight key credit strengths and vulnerabilities
- Identify data gaps that limit analytical confidence
- Recommend follow-up research or data collection

### Output
- `research/memos/credit_assessment_{obligor}_{date}.md` — Full credit assessment memo
- Quantitative summary: F_i, S_Omega (if available), SIC, CRI rank (if applicable)
- Signal quality report
- Data sufficiency assessment
- Key risk factors and mitigants

### Quality Checklist
- [ ] Data inventory completed before analysis
- [ ] Sector-appropriate scoring template used
- [ ] P_BSE and A(S_Omega) reported alongside any quantitative measures
- [ ] Data gaps explicitly identified (not papered over)
- [ ] Signal quality assessment honest (weak is acceptable)
- [ ] Qualitative context provided alongside quantitative scores

---

## WORKFLOW 4: REGULATORY / TAX ANALYSIS

### Purpose
Analyze the tax exemption eligibility, regulatory requirements, and legal framework for a proposed municipal bond structure.

### Input
- Proposed structure (bond type, tax status, issuer, borrower)
- Jurisdiction (state, county/city)
- Project description (use of proceeds, facility type)

### Procedure

**Step 1 — Tax Exemption Analysis**
- Classify the proposed bonds: governmental, 501(c)(3), private activity, taxable
- If PAB: identify the applicable IRC 142 category
- Analyze private business use test (10% / 5% thresholds)
- Analyze private security/payment test
- Volume cap implications (if applicable)
- Arbitrage considerations

**Step 2 — State Enabling Statute Review**
- Identify the state's enabling legislation for the proposed bond type
- Authorization requirements (legislative, executive, voter approval)
- Debt limitations (if applicable)
- Conduit issuance authority (if applicable)
- Public purpose requirements
- Validation proceeding availability

**Step 3 — Regulatory Requirements**
- SEC 15c2-12 applicability and requirements
- MSRB rules applicable to the transaction
- State-specific regulatory requirements
- Sector-specific: environmental permits (waste), CON (healthcare), etc.

**Step 4 — Issue Spotting**
- Identify potential legal/regulatory obstacles
- Flag areas requiring bond counsel confirmation
- Note open questions that need resolution

### Output
- `research/memos/regulatory_analysis_{project}_{date}.md` — Regulatory analysis memo
- Tax exemption eligibility assessment
- State enabling statute summary
- Regulatory requirement checklist
- Issue spot list with severity (critical / material / minor)

### Quality Checklist
- [ ] IRC sections cited for tax analysis
- [ ] State statute identified (not just general reference)
- [ ] Clearly distinguished between "the agent's analysis" and "requires bond counsel opinion"
- [ ] Issue spots prioritized by severity

---

## WORKFLOW 5: LITERATURE REVIEW & METHOD DEVELOPMENT

### Purpose
Study quantitative finance literature, assess applicability to municipal bond analysis, and propose analytical extensions to the Summers framework.

### Input
- Citation (paper reference, DOI, or title) OR topic description
- Context: what problem or gap this research addresses

### Procedure

**Step 1 — Source the Material**
- Web search for the paper/topic
- Check if available through open access, preprint servers, or author websites
- If behind paywall: search for summaries, presentations, or related open-access work
- Check if the Summers papers cite it (reference list in Paper 2)

**Step 2 — Comprehension**
- Summarize the paper's key contribution
- Identify the mathematical methods introduced or advanced
- Note the empirical validation approach (if any)
- Identify limitations and assumptions

**Step 3 — Applicability Assessment**
- How does this method relate to the Summers framework?
- Which phase(s) would it extend or improve?
- What are the data requirements? Are they feasible for municipal bonds?
- What implementation complexity does it add?
- Does it address a known gap or weakness in the muni adaptation?

**Step 4 — Model Proposal (if applicable)**
- If the method is promising, draft a model proposal per Section 8.2 of `02-summers-analytical-framework.md`
- Include: hypothesis, mathematical specification, implementation plan, validation strategy
- Store in `research/models/proposals/`

### Output
- `research/memos/literature_review_{topic}_{date}.md` — Literature review memo
- Applicability assessment (applicable / partially applicable / not applicable)
- Model proposal (if method is promising)
- Updated capability log entry

### Quality Checklist
- [ ] Primary source consulted (not just secondary summaries)
- [ ] Mathematical methods accurately described
- [ ] Applicability to muni bonds specifically assessed (not just "finance" generally)
- [ ] Honest assessment of limitations and data requirements
- [ ] Connection to specific Summers framework phase(s) identified

---

## WORKFLOW 6: CORPUS BUILDING

### Purpose
Identify data gaps in the research corpus and plan systematic data collection to fill them.

### Input
- Sector requiring corpus expansion
- Specific data gap identified (e.g., "no healthcare bond trade data", "no CCRC financial benchmarks")

### Procedure

**Step 1 — Gap Characterization**
- What data is missing? (specifics: fields, time range, sector coverage)
- What analysis is blocked by this gap?
- How many records are needed for minimum viability?
- What quality standards must the data meet?

**Step 2 — Source Inventory**
- EMMA: What filings are available? (OS, continuing disclosures, trade data)
- EDGAR: What SEC filings exist for this sector's issuers?
- Rating agencies: Public methodology documents, sector studies, default studies
- Government sources: CMS (healthcare), EPA (environmental), state databases
- Industry associations: GFOA, HFMA (healthcare), NAHB (housing)
- Academic: Published datasets, research papers with appendices

**Step 3 — Extraction Schema Design**
- Define the fields to extract for each record
- Specify data types, validation rules, acceptable ranges
- Map fields to Summers scoring dimensions
- Map fields to Muni-Pal schema paths (existing or proposed)

**Step 4 — Collection Plan**
- Can existing EMMA crawler be reused? Modifications needed?
- Is manual extraction required for some sources?
- Estimated effort (number of documents, extraction time per document)
- Phased approach: what's the minimum viable dataset?

**Step 5 — Quality Protocol**
- Completeness thresholds (what % of fields must be populated?)
- Anomaly detection rules (outlier ranges for financial metrics)
- Cross-validation (compare extracted data against known published values)
- Version control for dataset updates

### Output
- `research/corpus/{sector}/corpus_building_plan.md` — Detailed plan
- `research/datasets/{sector}_{dataset_name}_schema.json` — Schema definition
- Proposed EMMA crawler modifications (if needed)
- Proposed extractor module modifications (if needed)
- Implementation timeline

### Quality Checklist
- [ ] Gap clearly characterized with impact on blocked analysis
- [ ] Multiple sources inventoried (not just EMMA)
- [ ] Schema designed with explicit field-to-Summers-dimension mapping
- [ ] Quality protocol defined before collection begins
- [ ] Minimum viable dataset size identified

---

## WORKFLOW 7: WHITE PAPER PRODUCTION

### Purpose
Produce a publication-quality research memo on a specific topic, synthesizing multiple data sources and analytical methods into a cohesive argument.

### Input
- Research question or thesis
- Intended audience: internal (Muni-Pal team) or external (advisors, issuers, investors)
- Scope constraints (if any)

### Procedure

**Step 1 — Research Question Refinement**
- Sharpen the research question to a testable/answerable form
- Identify what "answering" this question looks like (qualitative conclusion? quantitative result? framework?)
- Define the audience and their expected level of sophistication

**Step 2 — Literature and Data Review**
- Search existing corpus for relevant data
- Review existing research memos that touch this topic
- Identify external sources needed
- Conduct additional analysis if needed (run Summers pipeline, build comparables)

**Step 3 — Outline**
Standard white paper structure:
1. Executive Summary (1 paragraph)
2. Introduction and Research Question
3. Background and Context
4. Methodology (analytical framework applied)
5. Analysis and Findings
6. Implications (for the sector, for Muni-Pal, for specific projects)
7. Limitations and Caveats
8. Conclusion
9. References
10. Appendices (data tables, detailed calculations)

**Step 4 — Draft**
- Write each section
- Include data tables, charts descriptions, and structured comparisons
- Cite all sources (EMMA filings, papers, rating reports, internal analysis)
- Apply Summers framework where quantitative analysis is relevant

**Step 5 — Quality Review**
- Verify all factual claims against sources
- Check mathematical consistency
- Ensure limitations and caveats are honest and prominent
- Verify YAML frontmatter is complete

### Output
- `research/memos/{topic}_{date}.md` — White paper
- Supporting datasets (if created during research)
- Updated capability log entry

### Quality Checklist
- [ ] Research question clearly stated and answered
- [ ] All claims sourced
- [ ] Summers framework applied where applicable (not forced where irrelevant)
- [ ] Limitations section honest and substantive
- [ ] Executive summary captures key findings in 1 paragraph
- [ ] Appropriate for stated audience level
- [ ] YAML frontmatter with confidence score reflecting analytical rigor

---

## WORKFLOW SELECTION GUIDANCE

| User Request Pattern | Recommended Workflow |
|---------------------|---------------------|
| "Tell me about [sector] bonds" | Workflow 1: Sector Deep Dive |
| "Find comparable deals for [project]" | Workflow 2: Comparable Issuance Analysis |
| "Evaluate [obligor/credit]" | Workflow 3: Credit Risk Assessment |
| "Can this project be tax-exempt?" | Workflow 4: Regulatory/Tax Analysis |
| "Study [paper/method]" | Workflow 5: Literature Review |
| "We need [sector] data" | Workflow 6: Corpus Building |
| "Write a paper on [topic]" | Workflow 7: White Paper Production |
| "Run the Summers analysis on [credit]" | Workflow 3 (quantitative focus) |
| "What's the healthcare muni market look like?" | Workflow 1 (healthcare sector) |
| "Build the healthcare corpus" | Workflow 6 (healthcare sector) |
