# Muni-Pal Integration Gate Protocol

**Version:** 1.0 | **Created:** 2026-02-18
**Purpose:** Defines how research agent outputs feed into the Muni-Pal platform

---

## 1. GATE ARCHITECTURE

The integration gate is the controlled boundary between the **research workspace** (exploratory, evolving, experimental) and the **Muni-Pal platform** (production, evidence-first, advisor-grade). Nothing crosses this boundary without explicit human approval.

```
RESEARCH WORKSPACE                    GATE                         MUNI-PAL PLATFORM
                                       |
research/memos/          ──→  proposed_for_review  ──→     Playbook schema paths
research/datasets/       ──→  user reviews          ──→     Readiness scoring
research/models/         ──→  approved/rejected     ──→     Extraction templates
research/corpus/         ──→                        ──→     Disclosure content
                                       |
                              Gate Status Tracking
                              in YAML frontmatter
```

---

## 2. GATE STATES

Every research artifact carries a `gate_status` field in its YAML frontmatter:

| State | Meaning | Who Sets It |
|-------|---------|-------------|
| `research_only` | Default. For internal research purposes. No integration proposed. | Agent (auto) |
| `proposed_for_review` | Agent believes this output could inform Muni-Pal. Awaiting user review. | Agent (explicit) |
| `approved_for_integration` | User has reviewed and approved. Ready to be incorporated. | User |
| `integrated` | Output has been incorporated into Muni-Pal (schema, playbook, extractor, etc.). | User |
| `rejected` | User reviewed and decided not to integrate. Remains as research. | User |

### Rules:
- The agent may set `research_only` or `proposed_for_review`
- The agent may NEVER set `approved_for_integration` or `integrated`
- A `rejected` artifact can be re-proposed after revision (new version, same base topic)
- All gate state transitions are logged in the artifact's frontmatter history

---

## 3. PROPOSAL CRITERIA

The agent should propose an artifact for integration when ALL of the following are true:

### 3.1 Confidence Threshold
- **Minimum confidence for proposal**: 0.80
- **Minimum confidence for integration**: 0.90
- Confidence reflects: data quality, source reliability, analytical rigor, and coverage completeness
- Confidence is self-assessed by the agent and reviewed by the user

### 3.2 Source Requirements
- Every factual claim must trace to a named source (EMMA filing, SEC document, rating agency publication, academic paper)
- Analytical inferences must be clearly labeled as such
- Hypotheses or estimates must be distinguished from established facts
- Minimum 3 independent sources for any benchmark metric proposed for integration

### 3.3 Relevance to Muni-Pal
The artifact must clearly inform one or more of:
- **Schema paths**: New or refined field definitions for the playbook
- **Readiness scoring**: Dimension weights, threshold values, gap classification criteria
- **Extraction templates**: New extractor definitions or prompt templates
- **Checklist items**: New or modified items for a playbook phase
- **Disclosure content**: Narrative templates, risk factor descriptions, regulatory language
- **Benchmark data**: Financial metric benchmarks for credit assessment
- **Risk factor mapping**: EMMA risk categories → readiness paths

---

## 4. SCHEMA MAPPING

### 4.1 Existing Schema Paths (Waste/Environmental)
The UCS Bond Intelligence Config Playbook (v0.3) defines ~60 schema paths organized into 14 categories:
- `project.*` — Project foundation
- `parties.*` — Parties and governance
- `technology.*` — Technology and operations
- `feedstock.*` — Feedstock and supply
- `revenue.*` — Revenue model and offtake
- `opex.*` — Operating expenses and margins
- `capital.*` — Capital structure and financing
- `cab.*` — CAB-specific terms
- `finmodel.*` — Debt service coverage and financial covenants
- `slb.*` — Sustainability-linked bond KPIs
- `risk.*` — Risk register and mitigation
- `security.*` — Security and collateral
- `permitting.*` — Permitting and regulatory compliance
- `assumptions.*` — Assumptions and uncertainty tracking

### 4.2 Healthcare Schema Paths (TO BE DEVELOPED)

The research agent should propose healthcare-specific schema paths as research progresses. Proposed initial structure:

```
# Healthcare Foundation
healthcare.facility_type           [enum: hospital|ccrc|senior_living|behavioral_health|clinic]
healthcare.bed_count               [integer, licensed beds]
healthcare.service_area            [string, primary service area description]
healthcare.system_affiliation      [string, parent health system if applicable]
healthcare.teaching_status         [enum: academic_medical_center|teaching|community|rural]
healthcare.trauma_designation      [enum: level_1|level_2|level_3|level_4|none]

# Financial Performance
healthcare.payor_mix.medicare_pct  [decimal %, Medicare as % of gross revenue]
healthcare.payor_mix.medicaid_pct  [decimal %, Medicaid as % of gross revenue]
healthcare.payor_mix.commercial_pct [decimal %, Commercial as % of gross revenue]
healthcare.payor_mix.self_pay_pct  [decimal %, Self-pay as % of gross revenue]
healthcare.case_mix_index          [decimal, CMS case mix index]
healthcare.occupancy_rate          [decimal %, average daily census / licensed beds]
healthcare.average_length_of_stay  [decimal days]
healthcare.operating_margin        [decimal %, (operating revenue - operating expense) / operating revenue]
healthcare.ebitda_margin           [decimal %]
healthcare.days_cash_on_hand       [integer days, unrestricted cash / daily operating expenses]
healthcare.debt_to_capitalization  [decimal %, long-term debt / (LTD + unrestricted net assets)]
healthcare.dscr                    [decimal, net revenue available / annual debt service]
healthcare.mads_coverage           [decimal, net revenue available / maximum annual debt service]

# CCRC-Specific
healthcare.ccrc.entrance_fee_type  [enum: refundable|partially_refundable|nonrefundable|rental]
healthcare.ccrc.entrance_fee_reserve [decimal %, actuarial reserve funded ratio]
healthcare.ccrc.waitlist_depth     [integer, number on waitlist]
healthcare.ccrc.independent_living_occupancy [decimal %]
healthcare.ccrc.assisted_living_occupancy [decimal %]
healthcare.ccrc.skilled_nursing_occupancy [decimal %]
healthcare.ccrc.actuarial_study_date [date, most recent actuarial study]

# Senior Living-Specific
healthcare.senior.revenue_per_unit [decimal $/month]
healthcare.senior.acuity_mix       [object, % by care level]
healthcare.senior.staffing_ratio   [decimal, FTEs per occupied unit]

# Behavioral Health-Specific
healthcare.behavioral.bed_utilization [decimal %]
healthcare.behavioral.avg_length_of_stay [decimal days]
healthcare.behavioral.medicaid_dependency [decimal %, Medicaid as % of patient revenue]
healthcare.behavioral.parity_compliance [boolean]

# Regulatory
healthcare.con_required            [boolean, state requires certificate of need]
healthcare.con_status              [enum: not_required|approved|pending|denied]
healthcare.licensure_status        [enum: active|conditional|provisional]
healthcare.cms_star_rating         [integer 1-5, CMS quality star rating]
healthcare.accreditation           [enum: joint_commission|dnv|hfap|none]
```

### 4.3 Mapping Research Outputs to Schema Paths

When proposing an artifact for integration, the agent must specify:
1. Which schema paths it informs (existing or proposed)
2. What values or benchmarks it provides for those paths
3. Whether it defines new paths (requiring playbook expansion)
4. Criticality tier for any new paths (CRITICAL / MATERIAL / SECONDARY)

---

## 5. INTEGRATION TOUCHPOINTS

### 5.1 Readiness Scoring → Research Benchmarks

The Muni-Pal readiness assessment scores 6 dimensions (0-10 scale). Research outputs can inform:

| Readiness Dimension | Research Input | Example |
|---------------------|---------------|---------|
| Issuer & Legal (20%) | Regulatory analysis, enabling statute research | State authorization requirements |
| Project/Tech/Ops (20%) | Sector deep dive, technology risk analysis | Commercial scale track record data |
| Revenue & Feedstock (15%) | Market analysis, comparable deal pricing | Revenue concentration benchmarks |
| CAB Financial (20%) | Financial metric benchmarks, DSCR analysis | Sector median DSCR by rating |
| Risk/Security/SLB (15%) | Risk factor analysis, enhancement comparables | Typical DSRF sizing, covenant packages |
| SLB Verification (10%) | KPI methodology research, verification protocols | ESG verification standards |

### 5.2 Risk Factor Mapping → Readiness Paths

The existing risk benchmark module maps EMMA's 21 risk categories to 5 readiness paths:

| Readiness Path | EMMA Categories | Research Expansion |
|---------------|----------------|--------------------|
| `risk.technology` | technology, cybersecurity | Technology obsolescence, commercial scale validation |
| `risk.construction` | construction, labor, force_majeure, insurance | EPC contract structures, contingency benchmarks |
| `risk.market` | market_demand, competition, financial, interest_rate, litigation | Revenue stability metrics, counterparty credit |
| `risk.regulatory` | regulatory, environmental, tax_law, political, permitting, climate | CON requirements, permitting timelines |
| `risk.feedstock` | feedstock_supply, management | Supply chain analysis, waste flow control |

For healthcare sector expansion, the risk mapping needs additional categories:
- `risk.reimbursement`: Medicare/Medicaid rate changes, payor mix shifts, managed care penetration
- `risk.utilization`: Occupancy volatility, acuity shifts, outpatient migration
- `risk.workforce`: Physician recruitment, nursing shortages, labor cost pressures
- `risk.regulatory_healthcare`: CON, licensure, CMS conditions of participation, state Medicaid programs

### 5.3 Extraction Template Expansion

When the corpus expands to a new sector (healthcare), new extraction templates are needed:

| Document Type | Fields to Extract | Existing Extractor? |
|--------------|-------------------|-------------------|
| Hospital audited financials | Revenue, expenses, DSCR, days cash, operating margin | Partial (financial_report module) |
| CAFR - health system | Net position, fund balance, debt schedules | Partial (financial_report module) |
| CMS Cost Report | Payor mix, case mix index, bed counts | No — new extractor needed |
| CON application | Service area, bed authorization, conditions | No — new extractor needed |
| Actuarial study (CCRC) | Funded ratio, assumptions, refund obligations | No — new extractor needed |
| Hospital OS/POS | All healthcare schema paths | Partial (OS extractor) |
| Continuing disclosure (healthcare) | Annual financial data, event notices | Yes (event_filing module) |

### 5.4 Playbook Expansion

As research matures, the agent should propose new playbook sections:

**Healthcare Playbook Structure** (proposed):
```
P1: Project Identification & Legal Framework
    - Facility type classification
    - State enabling statute identification
    - CON status (if required)
    - Tax-exempt eligibility analysis (501(c)(3) or PAB)

P2: Financial Assessment
    - Historical financial performance (3-5 years)
    - Payor mix analysis
    - Debt capacity assessment
    - DSCR projection under stress scenarios

P3: Market & Revenue Analysis
    - Service area demographics and competition
    - Revenue diversification assessment
    - Managed care contract analysis
    - Volume and utilization trends

P4: Security Structure
    - Revenue pledge design (gross vs. net)
    - Master trust indenture structure
    - Debt service reserve sizing
    - Additional bonds test calibration

P5: Risk Assessment
    - Risk factor inventory (map to readiness paths)
    - Rating agency alignment (Moody's/S&P/Fitch methodology comparison)
    - Mitigation strategy for each identified risk

P6: Disclosure & Compliance
    - SEC 15c2-12 continuing disclosure setup
    - Annual financial reporting requirements
    - Event notice triggers
    - Arbitrage compliance framework
```

---

## 6. PROPOSAL FORMAT

When proposing an artifact for Muni-Pal integration, the agent should produce a **gate proposal** as a separate section at the end of the research memo:

```markdown
## Integration Gate Proposal

**Artifact**: [filename]
**Gate Status**: proposed_for_review
**Confidence**: [0.80-1.00]

### What This Informs
- [Schema path 1]: [what value/benchmark it provides]
- [Schema path 2]: [what value/benchmark it provides]

### New Schema Paths Proposed
- [New path]: [definition] — Criticality: [CRITICAL/MATERIAL/SECONDARY]

### Readiness Impact
- Dimension affected: [which dimension(s)]
- Nature of impact: [new benchmark / refined threshold / new checklist item / new extraction template]

### Source Quality
- Primary sources: [list]
- Number of independent sources for key claims: [count]
- Data recency: [date range of underlying data]

### Risks of Integration
- [What could go wrong if this data is integrated prematurely]
- [What caveats should accompany the integrated data]

### Recommended Action
- [ ] Integrate as-is
- [ ] Integrate with modifications: [specify]
- [ ] Defer pending: [what additional research/data is needed]
```

---

## 7. HEALTHCARE CORPUS BOOTSTRAP SEQUENCE

Since the healthcare sector has no existing corpus, the following sequence is recommended:

1. **Sector Deep Dive** (Workflow 1): Produce comprehensive healthcare revenue bond sector analysis
2. **EMMA Data Collection** (Workflow 6): Identify and catalog healthcare bond issuances on EMMA
3. **Extraction Schema Design** (Workflow 6): Define healthcare schema paths and extraction fields
4. **Comparable Issuance Analysis** (Workflow 2): Analyze 10-15 representative healthcare deals
5. **Financial Benchmark Assembly** (Workflow 6): Compile median financial metrics by sub-sector and rating
6. **Rating Methodology Digest** (Workflow 1): Summarize Moody's/S&P/Fitch healthcare methodologies
7. **Propose Healthcare Playbook** (Gate Protocol): Package findings as proposed playbook expansion
8. **Propose Extractor Modifications** (Gate Protocol): Specify new extraction templates for healthcare docs

Each step produces a gated output; the user decides when to integrate each piece.
