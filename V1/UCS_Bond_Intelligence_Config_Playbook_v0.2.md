# Bond Intelligence Configuration Playbook v0.2
## UCS Waste-to-Energy Capital Appreciation + Sustainability-Linked Bond Architecture

**Status:** MVP Ready | **Classification:** Operations & Innovation Manager Internal Use  
**Version:** 0.2 | **Created:** 2026-01-27 | **Updated:** Pending Review  
**Archetype:** `ucswtecabslbv02` | **Scope:** El Dorado, California IDA Revenue Bond Facility

---

## 1. PLAYBOOK PURPOSE & SCOPE

### 1.1 What This Playbook Is

The Bond Intelligence Configuration Playbook is the **source of truth** for how the Bond Facility Management System (BFMS) translates messy, domain-native project inputs—RFP responses, feasibility studies, financial models, operator agreements, technology briefs—into **bond-issuance-ready structured outputs** without replacing advisory judgment.

Specifically, this playbook:
- **Defines bond readiness** for UCS waste-to-energy systems financed via CAB + SLB revenue bonds
- **Constrains what the system can extract** from uploaded documents (schema allowlists, extractors, prompts)
- **Maps evidence to checklist states and readiness dimensions** (deterministic rules, not AI inference)
- **Guides output generation** (warm handoff pack structure, explanation templates, disclosure skeleton)
- **Encodes process governance** (phases P1-P6, required facts per phase, state transitions)

### 1.2 What This Playbook Is NOT

- A trained AI model or prompt dump
- A replacement for muni bond counsel or financial advisors
- A decision engine (we never say "approved" or "ready to issue")
- A pricing or yield optimization tool
- A substitute for underwriting judgment

### 1.3 Design Principles

This playbook is intentionally:
- **Evidence-first**: Every claim traces to an accepted ExtractedFact or explicit Assumption
- **Schema-driven**: AI extraction constrained to playbook-defined paths, no hallucination fallback
- **Advisor-grade**: Outputs assume professional municipal finance expertise by recipients
- **Scope-aware**: CAB and SLB structures are non-standard; playbook encodes these structural distinctions
- **Transparent about gaps**: Missing evidence is surfaced, not smoothed over

---

## 2. BOND ARCHETYPE: UCS CAB + SLB REVENUE BONDS

### 2.1 Structural Characteristics

**Borrower Profile:**  
- Industrial Development Authority (IDA) or municipal issuer
- Private operator (Gold Seal Industries or licensed partner)
- Waste-to-commodity conversion technology (UCS)
- High CAPEX (~$50M per unit), deferred revenue ramp (5-7 year projection to steady-state)

**Bond Structure (Canonical Model):**
- **Instrument:** Taxable or Tax-Exempt Revenue Bonds with CAB and SLB features
- **Security:** First-lien equipment and real property + commodity offtake agreements + gross revenue pledge
- **Tenor:** 20 years (matches equipment useful life)
- **CAB Mechanics:** 5-7 year zero-coupon accretion period at 6.0-6.5%, converting to current-pay Years 6-20
- **SLB Features:** Dual KPIs (waste diversion rate, GHG emissions reduction), observation dates Years 3/6/9, step-up penalties 35-40 bps if target missed
- **DSCR Covenant:** Minimum 1.35x annually, calculated on gross revenues minus OM expenses
- **Turbo Redemptions:** Mandatory quarterly principal prepayment from excess cash flow

**Empirical Benchmarks (from public market data):**
- **CAB Pricing Premium:** ~75-150 bps vs. traditional equipment financing (captures deferral value)
- **SLB Greenium:** 25-43 bps reduction (sustainability premium offsets ~25-30% of taxable cost)
- **Typical CAPEX Loan Rates:** 8-10% equipment finance, 4.5-5.0% tax-exempt bonds, 6.0-6.5% taxable SLB
- **Revenue Bond Credit Spread:** 150-200 bps over Treasuries for BBB-equivalent projects

### 2.2 Why UCS Fits This Structure

1. **Deferred Cash Flow:** Zero commodity revenue Years 1-2, ramping to $10M+ by Year 5-6. CAB accretion defers principal & interest until project stabilizes.
2. **High Equipment CAPEX:** Modular containerized UCS units are tangible personal property, eligible for UCC-1 security and equipment-specific accounting.
3. **Discrete Revenue Streams:** Commodity sales (renewable diesel, biochar) are identifiable, contractible, and pledgeable to bondholders.
4. **Environmental Alignment:** Waste diversion, emissions reduction, and circular economy KPIs resonate with ESG-focused bond investors and offset 25-40 bps of cost.
5. **Scalability:** Multi-unit portfolio (Systems 1, 2, 3…) can scale via master trust indenture, cross-collateralization, and sequential debt issuance.

---

## 3. CANONICAL SCHEMA PATHS & VOCABULARY

### 3.1 Schema Path Allowlist (MVP)

The BFMS may extract and normalize ONLY the following schema paths. These are domain-native to UCS CAB+SLB bond structures; anything else is out-of-scope.

#### **3.1.1 Project Foundation**
```
project.canonicaldescription          [string, required in P1]
project.location.jurisdiction         [string, e.g., "Allegheny County, PA"]
project.location.sitecontrol          [enum: purchase|lease|option|loi, required by P2]
project.location.coordinates          [lat,lon optional]
project.operatingstatus               [enum: planned|under-construction|operational]
project.designlife                    [integer years, default 20]
```

#### **3.1.2 Parties & Governance**
```
parties.issuer.name                   [string, typically IDA]
parties.issuer.jurisdiction           [state, typically Arizona]
parties.borrower.name                 [string, project entity or operator]
parties.operator.name                 [string, technology provider e.g., Gold Seal Industries]
parties.sponsor.name                  [string, equity provider]
governance.inducement                 [enum: draft|proposed|adopted, required P1]
governance.publicpurpose              [string narrative]
```

#### **3.1.3 Technology & Operations**
```
technology.type                       [enum: ucs|thermal|biological|chemical, default "ucs"]
technology.throughput.nameplate       [integer tons/day, e.g., 100]
technology.throughput.annual          [integer tons/year, calculated as nameplate × 351 days]
technology.lifespan                   [integer years, default 20 from UCS specs]
technology.warranty.supplier          [string, OEM name]
technology.warranty.duration          [integer years, typically 20]
operations.staffing.direct            [integer headcount, e.g., 25]
operations.staffing.indirect          [integer estimate, e.g., "75-120"]
operations.maintenance.annual         [enum: routine|major, with frequency]
```

#### **3.1.4 Feedstock & Supply**
```
feedstock.type                        [enum: forestry|msw|agricultural|mixed, required]
feedstock.characterization            [string, optional description]
feedstock.volume.annual               [integer tons, e.g., 35,100]
feedstock.supply.mechanism             [enum: contract|mou|letter-of-intent|assessment, required P2]
feedstock.supply.confidence           [enum: preliminary|advanced|secured, required P3]
feedstock.transportation.logistics    [string, optional]
feedstock.acquisition.cost            [decimal $/ton, optional]
```

#### **3.1.5 Revenue Model & Offtake**
```
revenue.commodities.list              [array of {name, annual-volume, unit-price, annual-revenue}]
revenue.commodities.renewable-diesel  [decimal gallons/year, e.g., 2.25M; price $/gal, e.g., 4.50]
revenue.commodities.biochar           [decimal tons/year, e.g., 1,755; price $/ton, e.g., 100]
revenue.commodities.renewable-energy  [decimal MWh/year, e.g., 89,968; price $/kWh, e.g., 0.16]
revenue.commodities.distilled-water   [decimal gallons/year, optional]
revenue.offtake.agreements            [array of {counterparty, product, volume, tenor-years, status}]
revenue.offtake.status                [enum: executed|advanced-mou|letter-of-intent|negotiating, required P3]
revenue.pricing.assumptions           [string narrative of conservative price assumptions]
revenue.gross.annual                  [decimal, calculated from commodities × volumes × prices]
revenue.gross.growth.assumption       [decimal annual %, default 0 conservatism; can vary by commodity]
```

#### **3.1.6 Operating Expenses & Margins**
```
opex.feedstock.annual                 [decimal $/year, calculated from feedstock.acquisition.cost × volume]
opex.labor.annual                     [decimal $/year, e.g., staffing headcount × salary]
opex.utilities.annual                 [decimal $/year, e.g., 500K-1M range]
opex.maintenance.annual               [decimal $/year, e.g., 1-2M for capital equipment]
opex.insurance.annual                 [decimal $/year, e.g., 200K-500K]
opex.other.annual                     [decimal $/year, catch-all for ancillary]
opex.total.annual                     [decimal, sum of above]
opex.margin                           [decimal %, calculated as (revenue - opex) / revenue; target 45-50%]
ebitda                                [decimal, calculated as revenue - opex; for DSCR]
```

#### **3.1.7 Capital Structure & Financing**
```
capital.project-cost                  [decimal, total CAPEX, e.g., 50M]
capital.equipment-cost                [decimal, e.g., 26.9M for UCS units + generator + shredder]
capital.sitework-cost                 [decimal, e.g., 2-5M for prep, grading, storage]
capital.contingency                   [decimal % of CAPEX, default 10-15%]
capital.equity-contribution           [decimal, required by P3]
capital.equity-percent                [decimal %, calculated as equity / project-cost; target 15-20%]
capital.debt-requirement              [decimal, calculated as project-cost - equity; debt-to-project ratio]
```

#### **3.1.8 CAB-Specific Terms**
```
cab.enabled                           [boolean, true if zero-coupon capital appreciation]
cab.originalprincipial               [decimal, face value of bonds, e.g., 40-45M]
cab.accretionrate                    [decimal %, e.g., 6.35 annually]
cab.accretion.frequency              [enum: semiannually|quarterly, default semiannually]
cab.accretion.period.years           [integer, e.g., 5-7; years bonds accrete before current-pay conversion]
cab.finalmaturitydate                [date, e.g., 12/01/2046]
cab.turbo.enabled                     [boolean, true if mandatory quarterly redemptions from excess revenue]
cab.turbo.threshold                   [decimal, $1,000 minimum accreted value available triggers redemption]
cab.conversion.trigger                [enum: year-n|revenue-threshold|mandatory-conversion-date]
cab.conversion.rate                   [decimal %, interest rate at conversion to current-pay, e.g., 6.50%]
cab.expectedtotalcost                [decimal, accreted value × tenor, for financial modeling]
```

#### **3.1.9 Debt Service Coverage & Financial Covenants**
```
finmodel.inputs.revenue.annual        [decimal, gross revenue projection Year 1, e.g., 10.0M]
finmodel.inputs.revenue.ramp          [object {year: [annual-revenue]}; e.g., conservative ramp 5%/year]
finmodel.inputs.opex.annual           [decimal, annual operating expense]
finmodel.inputs.capex.maintenance     [decimal, annual major maintenance reserve target]
finmodel.inputs.dscr.minimum          [decimal, covenant floor, default 1.35x]
finmodel.outputs.noi                  [decimal, calculated net operating income = revenue - opex]
finmodel.outputs.debtservice.annual   [decimal, principal + interest per year]
finmodel.outputs.dscrbase             [decimal, calculated = NOI / annual debt service; must ≥ 1.35x]
finmodel.outputs.dscrcabramp          [object {year: dscr-value}; critical during CAB accretion period]
finmodel.outputs.dscrstress           [decimal, DSCR under -20% revenue stress scenario; must ≥ 1.15x]
```

#### **3.1.10 Sustainability-Linked Bond (SLB) KPIs & Targets**
```
slb.enabled                           [boolean, true if sustainability-linked features included]
slb.kpis.longlist                     [array of potential KPIs under consideration]
slb.kpis.shortlist                    [array of selected KPIs for inclusion in bond term; min 2, max 3]

slb.kpi.{n}.name                      [string, e.g., "Waste Diversion Rate"]
slb.kpi.{n}.definition                [string, operational definition per ICMA SLB Principles]
slb.kpi.{n}.materiality               [enum: core|material|supporting; required]
slb.kpi.{n}.unit                      [string, e.g., "% of waste processed", "metric tons CO2e", "tons/year"]
slb.kpi.{n}.baseline.year             [integer, year baseline measured, typically Year 0 or Year 1]
slb.kpi.{n}.baseline.value            [decimal, baseline value with supporting data]
slb.kpi.{n}.baseline.methodology      [string, how baseline was calculated; required for compliance]

slb.kpi.{n}.spt.year3.target          [decimal, target at Year 3 observation date]
slb.kpi.{n}.spt.year6.target          [decimal, target at Year 6 observation date]
slb.kpi.{n}.spt.year9.target          [decimal, target at Year 9 observation date]
slb.kpi.{n}.spt.ambition              [enum: conservative|moderate|ambitious; for transparency]

slb.kpi.{n}.verification.method       [string, e.g., "independent engineer certification", "third-party scale tickets"]
slb.kpi.{n}.verification.provider     [string, name of external verifier, e.g., "TUV Nord"]
slb.kpi.{n}.reporting.frequency       [enum: monthly|quarterly|annually]

slb.penalty.stepup.trigger            [decimal %, e.g., 85% of SPT = trigger 35 bps increase]
slb.penalty.stepup.magnitude          [decimal bps, e.g., 35-50 bps per observation period]
slb.penalty.stepdown.magnitude        [decimal bps, e.g., 10-15 bps if target exceeded 110%]
slb.penalty.observation.dates         [array of dates, e.g., [12/31/2029, 12/31/2032, 12/31/2035]]
slb.penalty.callprotection            [boolean, true if no optional redemption 12 months post-observation]

slb.baseline.adjustment.policy        [string, criteria under which baseline may be recalibrated; requires bondholder consent 66.7%]
```

#### **3.1.11 Risk Register & Mitigation**
```
risk.register                         [array of {risk-id, category, description, probability, impact, mitigation-strategy}]
risk.{id}.category                    [enum: technology|feedstock|revenue|permitting|regulatory|market|financial|operational]
risk.{id}.probability                 [enum: low|medium|high]
risk.{id}.impact                      [enum: low|medium|high|critical]
risk.{id}.mitigationprimary          [string, main risk control, e.g., "long-term feedstock contract"]
risk.{id}.mitigationsecondary        [string, secondary control, e.g., "feedstock diversity, 5+ suppliers"]
```

#### **3.1.12 Security & Collateral**
```
security.realproperty                 [string, location and description of mortgaged property]
security.realproperty.lienposition   [enum: first|second|pari-passu, default first]
security.equipment.schedule          [string, list of major equipment items UCC-1 filed]
security.equipment.lienposition      [enum: first|second, default first]
security.revenue.pledge               [enum: gross|net, e.g., gross pledge of all project revenues]
security.offtake.assignment          [array of assigned offtake agreement IDs; for collateral support]
security.insurance.required          [enum: yes|no; types: business-interruption, property, pollution-liability]
security.insurance.coverage          [decimal, $ amount, e.g., 120% of annual debt service]
```

#### **3.1.13 Permitting & Regulatory Compliance**
```
permitting.air-quality.status         [enum: not-started|in-progress|pending-approval|approved, required by P2]
permitting.air-quality.permittype    [string, e.g., "Title V Major Source", "Synthetic Minor"]
permitting.solidwaste.status          [enum: not-started|in-progress|pending-approval|approved, required by P2]
permitting.buildingzoning.status      [enum: not-started|in-progress|pending-approval|approved, required by P2]
permitting.stormwater.status          [enum: not-started|in-progress|pending-approval|approved, optional]
permitting.other.list                 [array of other permits, e.g., hazmat, wastewater discharge]

regulatory.tax-status                 [enum: tax-exempt-idb|tax-exempt-solidwaste|taxable, required by P1]
regulatory.tax-exemption.basis        [string, IRC section and legal rationale if tax-exempt]
regulatory.private-activity-bond      [boolean, true if eligible under IRC 144/142; affects volume cap]
regulatory.volume-cap.allocation      [decimal $, if PAB subject to state volume cap]
```

#### **3.1.14 Assumptions & Uncertainty Tracking**
```
assumptions.list                      [array of explicit assumptions underpinning model]
assumptions.{n}.name                  [string, e.g., "Feedstock Cost Escalation Rate"]
assumptions.{n}.value                 [decimal or string]
assumptions.{n}.unit                  [string, e.g., "%/year", "$/ton"]
assumptions.{n}.source                [enum: artifact|internal-estimate|market-data|expert-judgment]
assumptions.{n}.confidence            [decimal 0-1, subjective confidence; critical for low-confidence assumptions]
assumptions.{n}.rationale             [string, why this assumption; references to supporting evidence]
assumptions.{n}.sensitivity.impact    [string, how 10-20% change affects DSCR or KPI achievement]
```

### 3.2 Schema Path Criticality Tiers

**CRITICAL paths (high-review threshold, 5+ extractors validate before acceptance):**
- `cab.enabled`, `cab.accretionrate`, `cab.finalmaturitydate`
- `finmodel.inputs.revenueramp`, `finmodel.outputs.dscrbase`
- `slb.kpis.shortlist`, `slb.kpi.{n}.baseline.methodology`, `slb.kpi.{n}.verification.plan`
- `revenue.feedstock.supply.mechanism`, `revenue.offtake.status`

**MATERIAL paths (medium-review threshold, 2-3 extractors validate):**
- `project.canonicaldescription`, `parties.operator.name`
- `technology.throughput.nameplate`, `operations.staffing.direct`
- `revenue.gross.annual`, `opex.total.annual`
- `permitting.air-quality.status`, `regulatory.tax-status`

**SECONDARY paths (standard threshold, single extractor sufficient):**
- `project.location`, `project.designlife`
- `revenue.commodities.renewable-diesel`, `risk.register`

---

## 4. EXTRACTION FRAMEWORK & PROMPT TEMPLATES

### 4.1 Extractor Definitions (MVP Suite)

Each extractor is a reusable configuration defining:
- **Applicability:** Which document types and artifact roles trigger this extractor
- **Outputs:** Which schema paths it may populate (allowlist)
- **Prompt:** The question posed to AI, constrained to avoid hallucination
- **Confidence Thresholds:** When to flag for human review
- **Idempotency:** How to ensure deterministic re-runs

#### **4.1.1 ProjectDescriptionExtractor**

```yaml
ExtractorID: ProjectDescriptionExtractor
Version: 1.0
ApplicableDocTypes:
  - RFPResponse
  - FeasibilityStudy
  - ExecutiveSummary
  - TechnologyBrief
ApplicableArtifactRoles:
  - technology
  - unknown

OutputSchemaPaths:
  - project.canonicaldescription
  - project.location.jurisdiction
  - project.location.coordinates
  - project.operatingstatus
  - technology.type
  - technology.throughput.nameplate
  - technology.throughput.annual

PromptTemplate: |
  From the artifact, extract the following facts:
  1. Canonical project description (1-2 sentences describing UCS unit, location, purpose)
  2. Jurisdiction (state/county)
  3. Technology throughput nameplate (e.g., "100 tons/day")
  4. Annual throughput (nameplate × 351 operating days per year)
  5. Current operating status (planned, under construction, operational)
  
  Constraint: Only extract if explicitly stated. If not found, return null.
  Do not infer missing values. Do not estimate throughput if not stated.

ConfidenceThresholds:
  - Critical: If throughput extracted < 0.85 confidence, flag for review.
  - Standard: All other paths >= 0.70 confidence acceptable.

BulkAcceptanceThreshold: 0.80
CriticalLowConfidenceFlag: true
```

#### **4.1.2 PartiesExtractor**

```yaml
ExtractorID: PartiesExtractor
Version: 1.0
ApplicableDocTypes:
  - RFPResponse
  - Feasibility Study
  - ExecutiveSummary
  - LoanAgreement
  - OperatingAgreement
ApplicableArtifactRoles:
  - technology
  - finance
  - legal
  - unknown

OutputSchemaPaths:
  - parties.issuer.name
  - parties.issuer.jurisdiction
  - parties.borrower.name
  - parties.operator.name
  - parties.sponsor.name
  - governance.publicpurpose

PromptTemplate: |
  Extract the following from the artifact:
  1. Project issuer (typically IDA or municipal entity)
  2. Issuer jurisdiction (state)
  3. Project borrower or operator (private entity)
  4. Technology provider/OEM (e.g., Gold Seal Industries)
  5. Equity sponsor or funding source
  6. Public purpose / community benefit statement (if stated)
  
  Constraint: Cite the exact text where each party is identified.
  If role ambiguous, flag confidence < 0.80.
  Do not infer organizational structure.
```

#### **4.1.3 FeedstockSupplyExtractor**

```yaml
ExtractorID: FeedstockSupplyExtractor
Version: 1.0
ApplicableDocTypes:
  - RFPResponse
  - FeasibilityStudy
  - FeedstockAssessment
  - SupplyContract
ApplicableArtifactRoles:
  - technology
  - finance
  - unknown

OutputSchemaPaths:
  - feedstock.type
  - feedstock.characterization
  - feedstock.volume.annual
  - feedstock.supply.mechanism
  - feedstock.supply.confidence
  - feedstock.transportation.logistics
  - feedstock.acquisition.cost

PromptTemplate: |
  Extract feedstock & supply facts:
  1. Feedstock type (forestry, MSW, agricultural, mixed)
  2. Detailed feedstock characterization (e.g., "non-merchantable timber, post-harvest residues")
  3. Annual volume in tons (e.g., "35,100 tonsyear")
  4. Supply mechanism (contract executed, MOU advanced, letter of intent, assessment only)
  5. Assessment or study supporting availability (e.g., "GIS survey" "market analysis")
  6. Transportation logistics summary if stated
  7. Acquisition cost per ton if quantified
  
  Constraint: Only extract volumes and costs that are explicitly stated or clearly calculated.
  Flag supply.mechanism as "assessment only" if no contract/MOU exists.
  Do not extrapolate supply from feedstock availability studies alone.
```

#### **4.1.4 RevenueOfftakeExtractor**

```yaml
ExtractorID: RevenueOfftakeExtractor
Version: 1.0
ApplicableDocTypes:
  - RFPResponse
  - FeasibilityStudy
  - FinancialModel
  - OfftakeAgreement
  - MarketAnalysis
ApplicableArtifactRoles:
  - finance
  - technology
  - unknown

OutputSchemaPaths:
  - revenue.commodities.list
  - revenue.commodities.renewable-diesel
  - revenue.commodities.biochar
  - revenue.commodities.renewable-energy
  - revenue.commodities.distilled-water
  - revenue.offtake.agreements
  - revenue.offtake.status
  - revenue.pricing.assumptions
  - revenue.gross.annual

PromptTemplate: |
  Extract revenue & commodity facts:
  1. Commodities produced (e.g., renewable diesel, biochar, electricity, water)
  2. For each commodity:
     a. Annual volume (units: gallons/year, tons/year, MWh/year)
     b. Unit price assumption ($/gal, $/ton, $/MWh)
     c. Calculated annual revenue (volume × price)
  3. Offtake agreements: For each, extract [counterparty, product, volume, contract term (years), status]
  4. Status of offtake: Executed contract, advanced MOU, letter-of-intent, or preliminary negotiation
  5. Pricing assumptions narrative (e.g., "conservative $4.50/gal renewable diesel assumption")
  6. Total gross revenue projection (sum of commodity revenues)
  
  Constraint: Only extract prices and volumes explicitly stated in or derived from contract language.
  If prices are stated as ranges, use midpoint and flag confidence < 0.75.
  Executed contracts = high confidence. LOI or MOU = medium confidence. Preliminary = low confidence.
```

#### **4.1.5 OperatingExpenseExtractor**

```yaml
ExtractorID: OperatingExpenseExtractor
Version: 1.0
ApplicableDocTypes:
  - FinancialModel
  - OperatingPlan
  - BudgetForecast
  - FeasibilityStudy
ApplicableArtifactRoles:
  - finance
  - technology
  - unknown

OutputSchemaPaths:
  - opex.feedstock.annual
  - opex.labor.annual
  - opex.utilities.annual
  - opex.maintenance.annual
  - opex.insurance.annual
  - opex.other.annual
  - opex.total.annual
  - opex.margin

PromptTemplate: |
  Extract operating expense components:
  1. Feedstock/input material cost ($/year)
  2. Labor cost (staffing headcount × average salary, or stated total)
  3. Utilities (electricity, water, gas) ($/year)
  4. Routine & preventive maintenance ($/year)
  5. Insurance premiums (property, liability, business interruption) ($/year)
  6. Other OpEx (admin overhead, licensing, permits, miscellaneous) ($/year)
  7. Total annual OpEx (sum of above)
  8. Operating margin % (calculated as (GrossRevenue - TotalOpEx) / GrossRevenue × 100)
  
  Constraint: Extract component values as stated. If single total OpEx given without breakdown,
  extract total and flag for secondary validation.
  Operating margin should be 45-55% for UCS systems at maturity; flag outliers < 35% or > 65%.
  Do not infer salary assumptions if not stated.
```

#### **4.1.6 CABTermsExtractor**

```yaml
ExtractorID: CABTermsExtractor
Version: 1.0
ApplicableDocTypes:
  - BondTermSheet
  - Indenture
  - PrivatePlacementMemorandum
  - FinancialModel
ApplicableArtifactRoles:
  - finance
  - legal
  - unknown

OutputSchemaPaths:
  - cab.enabled
  - cab.originalprincipial
  - cab.accretionrate
  - cab.accretion.frequency
  - cab.accretion.period.years
  - cab.finalmaturitydate
  - cab.turbo.enabled
  - cab.turbo.threshold
  - cab.conversion.trigger
  - cab.conversion.rate

PromptTemplate: |
  Extract Capital Appreciation Bond (CAB) terms:
  1. Is CAB structure used? (yes/no)
  2. Original principal amount (bond face value, e.g., "$40M")
  3. Accretion rate (annual %, e.g., "6.35%")
  4. Accretion frequency (semi-annually, quarterly)
  5. Accretion period length (years before conversion to current-pay, e.g., "5 years")
  6. Final maturity date (e.g., "12/01/2046")
  7. Turbo redemption enabled? (yes/no; if yes, include threshold e.g., "$1,000 accreted value")
  8. Conversion trigger (automatic at Year N, or upon revenue threshold)
  9. Interest rate post-conversion to current-pay (e.g., "6.50%")
  
  Constraint: CAB terms are CRITICAL. Require 0.90+ confidence. Any ambiguity flags for review.
  Cross-reference term sheet, indenture, and model to validate consistency.
  If conversion rate differs materially (>50 bps) from base rate, flag for explanation.
```

#### **4.1.7 SLBMetricsExtractor**

```yaml
ExtractorID: SLBMetricsExtractor
Version: 1.0
ApplicableDocTypes:
  - SustainabilityFramework
  - BondTermSheet
  - PrivatePlacementMemorandum
  - SecondPartyOpinion
ApplicableArtifactRoles:
  - finance
  - sustainability
  - unknown

OutputSchemaPaths:
  - slb.enabled
  - slb.kpis.longlist
  - slb.kpis.shortlist
  - slb.kpi.{n}.name
  - slb.kpi.{n}.definition
  - slb.kpi.{n}.baseline.value
  - slb.kpi.{n}.baseline.methodology
  - slb.kpi.{n}.spt.year3.target
  - slb.kpi.{n}.spt.year6.target
  - slb.kpi.{n}.verification.method
  - slb.penalty.stepup.magnitude
  - slb.penalty.observation.dates

PromptTemplate: |
  Extract Sustainability-Linked Bond KPI framework:
  1. Are SLB features included? (yes/no)
  2. List all KPIs under consideration (long list)
  3. Which KPIs are selected for bond terms? (short list of 2-3)
  4. For each selected KPI:
     a. KPI name (e.g., "Waste Diversion Rate")
     b. Definition per ICMA SLB Principles
     c. Baseline value (e.g., "35% regional average")
     d. How baseline was established (e.g., "EPA WARM model", "historical data")
     e. Year 3 SPT (e.g., "50%")
     f. Year 6 SPT (e.g., "55%")
     g. Verification method (e.g., "independent engineer", "third-party scale tickets")
  5. Coupon step-up penalty if target missed (e.g., "35-40 bps")
  6. Observation dates (e.g., "12/31/2029, 12/31/2032")
  
  Constraint: SLB terms are CRITICAL for structured debt. Require 0.85+ confidence.
  Baseline methodology is particularly critical; flag any circular reasoning or unverifiable data.
  Verification method must be realistic and third-party independent.
  SPT calibration should demonstrate ambition without gaming risk.
```

#### **4.1.8 DSCRInputsExtractor**

```yaml
ExtractorID: DSCRInputsExtractor
Version: 1.0
ApplicableDocTypes:
  - FinancialModel
  - ProFormaStatement
  - BondProposal
  - FeasibilityStudy
ApplicableArtifactRoles:
  - finance
  - unknown

OutputSchemaPaths:
  - finmodel.inputs.revenue.annual
  - finmodel.inputs.revenue.ramp
  - finmodel.inputs.opex.annual
  - finmodel.inputs.dscr.minimum
  - finmodel.outputs.noi
  - finmodel.outputs.debtservice.annual
  - finmodel.outputs.dscrbase
  - finmodel.outputs.dscrcabramp

PromptTemplate: |
  Extract DSCR model inputs:
  1. Revenue projection Year 1 (e.g., "$10.0M")
  2. Revenue growth trajectory Years 1-10 (e.g., array of annual revenues or growth rate %)
  3. Annual operating expense projection (Year 1)
  4. OpEx escalation assumption (%)
  5. Minimum DSCR covenant required (e.g., "1.35x")
  6. Debt service amount (Year 1 forward, principal + interest)
  7. Calculated NOI (revenue - opex; add back depreciation for DSCR calc)
  8. Calculated DSCR by year: DSCR = NOI / Annual Debt Service
  9. Identify years 1-5 when CAB accretion means DS = 0 (NOI = NA)
  10. Identify Year 6+ when bonds convert to current-pay and DS begins
  
  Constraint: Revenue and OpEx projections often differ across source documents.
  Flag any variance > 15% between stated and calculated figures.
  DSCR covenant is material; confirm minimum 1.35x is stated in indenture.
  During CAB years, DSCR = N/A; do not attempt to calculate.
```

### 4.2 Extraction Workflow & Idempotency

**Idempotency Key Formula (for re-runs):**
```
idempotencykey = SHA256(
  artifact_sha256 +
  extractor_id +
  extractor_version +
  selected_chunk_ids
)
```

If same artifact + extractor + version combination runs again with same chunk selection, system returns cached results without re-running AI.

---

## 5. CHECKLIST FRAMEWORK (PHASES P1-P6)

### 5.1 Checklist Item States

Each ChecklistItem evaluates to ONE of:
- **`notstarted`** — No supporting facts exist for this item
- **`inprogress`** — Partial facts exist; gaps remain
- **`needsreview`** — Facts exist but require human validation or resolution of conflicts
- **`ready`** — All required facts present, accepted, conflict-free, sufficient for next phase
- **`blocked`** — Conflicting or rejected facts; cannot proceed until resolved

### 5.2 Phase P1: Issuer Authority & Deal Formation (Months 0-1)

**Purpose:** Establish legal authority, governance intent, and preliminary project scope.

| Checklist ID | Item | Required Fact Paths | Status Rule | Why It Matters |
|---|---|---|---|---|
| P1.1 | Issuer Authority & Statute | `parties.issuer.name`, `regulatory.tax-status`, `regulatory.tax-exemption.basis` | All 3 paths must be accepted, non-null | IDA authority is prerequisite for bond issuance; IRS section determines tax status |
| P1.2 | Governing Body Inducement | `governance.inducement` | Must be "adopted" or "proposed" minimum | Bond counsel will not engage until inducement resolution executed |
| P1.3 | Public Purpose Statement | `governance.publicpurpose` | Must exist, ≥50 words, cite community benefit | Required for investor disclosure and political legitimacy |
| P1.4 | Preliminary Deal Formation Memo | `parties.issuer.name`, `parties.borrower.name`, `parties.operator.name`, `parties.sponsor.name` | All 4 paths accepted | Clarity on sponsor/SPV/operator roles prevents advisor confusion later |
| P1.5 | Eligible Project Determination | `regulatory.tax-status`, `project.canonicaldescription` | If tax-exempt, IRC section 142a6 or 144a must be documented; description must align | Determines investor base and tax treatment |

**Readiness Signals:**
- ✅ Ready to proceed to P2 when P1.1-P1.5 all = `ready` AND written Inducement Resolution is in artifacts

---

### 5.3 Phase P2: Project & Technology Definition (Months 1-4)

**Purpose:** Lock project scope, technology specs, site control, permitting pathway.

| Checklist ID | Item | Required Fact Paths | Status Rule | Why It Matters |
|---|---|---|---|---|
| P2.1 | Canonical Project Description | `project.canonicaldescription`, `project.location.jurisdiction`, `project.operatingstatus` | All 3 paths non-null, description ≥100 words | Investor-grade clarity on scope; prevents downstream revision |
| P2.2 | Technology Specification | `technology.type`, `technology.throughput.nameplate`, `technology.lifespan`, `technology.warranty.supplier` | All 4 required; warranty duration ≥15 years preferred | OEM-backed warranty is material risk mitigant |
| P2.3 | Site Control | `project.location.sitecontrol` | Must be "purchase" OR "lease" OR "option" (LOI insufficient) | Fatal flaw if no legal control; triggers default |
| P2.4 | Feedstock Supply Logic | `feedstock.type`, `feedstock.volume.annual`, `feedstock.supply.mechanism`, `feedstock.supply.confidence` | All 4 paths; if supply.mechanism = "assessment only", confidence must be flagged | No feedstock = no revenue; advance beyond assessment before major capex |
| P2.5 | Permitting Pathway (Preliminary) | `permitting.air-quality.status`, `permitting.solidwaste.status` | Both must be ≥ "in-progress" OR "pending-approval" by end P2 | Controls schedule risk; no financial close without path to approvals |
| P2.6 | Operator & OM Structure | `operations.staffing.direct`, `operations.staffing.indirect`, `operations.maintenance.annual` | All 3 paths accepted; staffing assumptions must be realistic (e.g., 25 direct + 75-120 indirect for 100 TPD UCS) | Operational risk is primary driver of DSCR; investors scrutinize staffing |

**Readiness Signals:**
- ✅ Ready for P3 when P2.1-P2.6 all = `ready` AND Independent Engineer Feasibility Report supports throughput/capacity assumptions

---

### 5.4 Phase P3: Financial Structure & Revenue Model (Months 2-6)

**Purpose:** Validate revenue projections, build preliminary financial model, lock debt/equity sizing.

| Checklist ID | Item | Required Fact Paths | Status Rule | Why It Matters |
|---|---|---|---|---|
| P3.1 | Commodity Revenue Projections | `revenue.commodities.list`, `revenue.offtake.agreements`, `revenue.offtake.status`, `revenue.pricing.assumptions`, `revenue.gross.annual` | revenue.offtake.status must be ≥ "letter-of-intent"; prices must be justified via offtake or market data | Revenue is the ONLY security for bondholders; conservative assumptions essential |
| P3.2 | Operating Expense Budget | `opex.total.annual`, `opex.margin`, `opex.feedstock.annual`, `opex.labor.annual` | All 4 paths; margin must be 40-55% (flag if outside range); OpEx components must be itemized | Operating margin drives NOI and DSCR; line-item clarity enables lender monitoring |
| P3.3 | DSCR Model & Covenant | `finmodel.outputs.dscrbase`, `finmodel.inputs.dscr.minimum`, `finmodel.outputs.dscrcabramp` | DSCR Year 1-5 must be calculated during CAB accretion; minimum covenant ≥ 1.35x; stress case DSCR ≥ 1.15x | DSCR is linchpin of credit analysis; covenant breach = default |
| P3.4 | CAB Structure & Accretion Profile | `cab.enabled`, `cab.originalprincipial`, `cab.accretionrate`, `cab.accretion.period.years`, `cab.finalmaturitydate` | All 5 critical paths; accretion rate must align with revenue ramp (no more than 6.5% annually for UCS at 10M revenue) | CAB is non-standard; requires transparent accretion schedule and rationale |
| P3.5 | Debt/Equity Sizing | `capital.project-cost`, `capital.equity-contribution`, `capital.equity-percent`, `capital.debt-requirement` | Equity ≥ 15%; total debt ≤ 85% LTV; math must reconcile to sources-and-uses | Over-leverage is fatal; underwriters enforce minimum equity to absorb ramp risks |
| P3.6 | Sources & Uses | `capital.project-cost`, `capital.equipment-cost`, `capital.sitework-cost`, `capital.contingency`, `capital.equity-contribution` | All uses must sum to sources; contingency 10-15% of CAPEX | Clarity on cost allocation prevents fund shortfall mid-construction |

**Readiness Signals:**
- ✅ Ready for P4 when P3.1-P3.6 all = `ready` AND 25-year pro forma model with transparent assumptions is in artifacts

---

### 5.5 Phase P4: Risk, Security & Disclosure (Months 4-8)

**Purpose:** Map risks to mitigants, define security package, outline disclosure framework.

| Checklist ID | Item | Required Fact Paths | Status Rule | Why It Matters |
|---|---|---|---|---|
| P4.1 | Risk Register & Mitigation | `risk.register` (populated with P2-P3 findings) | Minimum 8 identified risks across categories (technology, feedstock, revenue, permitting, market, financial, operational); each with primary + secondary mitigant | Transparent risk map builds investor confidence; missed risks = disclosure violation risk |
| P4.2 | Revenue Security & Pledge | `security.revenue.pledge`, `security.offtake.assignment` | Gross revenue pledge required; material offtake agreements assigned to trustee | Gross revenue pledge (not net) is standard for revenue bonds; provides buffer |
| P4.3 | Equipment & Real Property Lien | `security.realproperty`, `security.realproperty.lienposition`, `security.equipment.schedule`, `security.equipment.lienposition` | First-lien position on all equipment + real property; UCC-1 filings and mortgages executed | UCC-1 perfection is technical requirement; any lapse invalidates security position |
| P4.4 | Insurance & Guarantees | `security.insurance.required`, `security.insurance.coverage` | Business interruption insurance for 12 months OM expenses; pollution liability; builder's risk during construction | Insurance is bondholders' only recourse during project downtime; coverage must be adequate |
| P4.5 | SLB KPI Verification & Penalties | `slb.enabled`, `slb.kpi.{n}.verification.method`, `slb.penalty.stepup.magnitude`, `slb.penalty.observation.dates` | If SLB = true: all 4 paths populated; step-up penalties ≥ 35 bps (not cosmetic); observation dates within first 50% of bond tenor | SLB structure is CRITICAL; weak penalties undermine greenwashing claims and offset pricing benefit |
| P4.6 | Disclosure Outline (Framework) | `governance.publicpurpose`, `risk.register` (key risks), `finmodel.outputs.dscrbase`, `slb.kpi.shortlist` | Framework identifies sections of OS (Official Statement) or PPM (Private Placement Memo) where facts map | Disclosure outline prevents omissions and ensures investor education |

**Readiness Signals:**
- ✅ Ready for P5 when P4.1-P4.6 all = `ready` AND Phase I ESA + permitting matrix show no material blockers

---

### 5.6 Phase P5: SLB Architecture & Final Modeling (Months 6-8)

**Purpose:** Finalize KPI baselines, calibrate SPTs, model financial consequences of penalties.

| Checklist ID | Item | Required Fact Paths | Status Rule | Why It Matters |
|---|---|---|---|---|
| P5.1 | Sustainability Objectives & Impact Logic | `slb.kpis.shortlist` (2-3 KPIs selected), `governance.publicpurpose` | KPIs must be material to core business (waste diversion, emissions reduction); link to public purpose | Material KPIs = credible ESG story; cosmetic KPIs trigger "greenwashing" allegations |
| P5.2 | KPI Baseline & Methodology | `slb.kpi.{n}.baseline.value`, `slb.kpi.{n}.baseline.methodology` | Baseline must be derived from 3+ years historical data OR independent study (e.g., EPA WARM); methodology must be verifiable | Baseline gaming is primary SLB risk per World Bank 2024; conservative baseline = credibility |
| P5.3 | SPT Calibration & Ambition | `slb.kpi.{n}.spt.year3.target`, `slb.kpi.{n}.spt.year6.target`, `slb.kpi.{n}.spt.ambition` | Targets must be beyond BAU (business-as-usual); aligned with peer performance or science-based benchmarks | Targets that are too easy trigger investor skepticism; targets too hard create unnecessary default risk |
| P5.4 | Verification & Reporting Framework | `slb.kpi.{n}.verification.method`, `slb.kpi.{n}.verification.provider`, `slb.kpi.{n}.reporting.frequency` | Independent verifier pre-identified (e.g., TUV Nord, Lloyd's); annual external limited assurance required | Third-party verification is non-negotiable; internal-only reporting = no credibility |
| P5.5 | Economic Linkage: Penalties & Call Protection | `slb.penalty.stepup.magnitude`, `slb.penalty.observation.dates`, `slb.penalty.callprotection` | Step-up penalties must be 35-50 bps minimum per observation; observation dates ≤ Year 3, 6, 9 (≤ 50% of tenor); call protection 12 months post-observation | Late observation dates or weak penalties enable issuer gaming; call protection prevents redemption to avoid penalties |
| P5.6 | Financial Model with SLB Scenarios | `finmodel.outputs.dscrbase` (base case), plus stress scenarios with step-up penalty applied | Model must demonstrate DSCR ≥ 1.25x even if 35-50 bps step-up triggered | If step-up breaks DSCR covenant, SPT was set too ambitiously; unachievable targets = default risk |

**Readiness Signals:**
- ✅ Ready for P6 when P5.1-P5.6 all = `ready` AND Second-Party Opinion (SPO) from recognized SLB verifier is executed

---

### 5.7 Phase P6: Advisor Engagement & Execution (Months 8-12+)

**Purpose:** Engage bond counsel, underwriter, rating agencies; execute transaction documents; close bonds.

| Checklist ID | Item | Required Fact Paths | Status Rule | Why It Matters |
|---|---|---|---|---|
| P6.1 | Bond Counsel Engagement | `parties.issuer.name`, `regulatory.tax-status` | Bond counsel retained; preliminary opinion issued confirming tax-exemption (if applicable) or taxable status | Bond counsel is gatekeeper; no closing without opinion |
| P6.2 | Rating Agency Engagement | `finmodel.outputs.dscrbase`, `risk.register`, `security.equipment.schedule` | If seeking rating: initial presentation complete, ratings expected by Month 12 | Rating = institutional investor access; unrated bonds = limited distribution |
| P6.3 | Underwriter/Placement Agent | `capital.debt-requirement`, `slb.enabled` | Placement agent retained; marketing strategy defines investor targets (ESG funds if SLB-emphasized) | Placement execution is critical path; speed depends on underwriter relationships |
| P6.4 | Independent Engineer Certification | `technology.throughput.nameplate`, `finmodel.outputs.dscrbase`, `risk.register` | Final IE Report (100+ pages) certifies project feasibility, DSCR supportable, risks disclosed | IE Report is gold-standard due diligence for project finance; investors require it |
| P6.5 | Closing Documents | Loan Agreement, Trust Indenture, Security Agreements, Continuing Disclosure Agreement, SLB Framework doc | All signed and recorded; UCC-1 filings effective | Closing is execution of all P1-P5 work; any gaps = delay or deal failure |
| P6.6 | Warm Handoff Pack | All prior outputs packaged into Deal Overview Memo, Readiness Gap Report, Checklist Summary, Evidence Index, Financial Tables, SLB KPI Brief, Disclosure Outline skeleton | Pack generated and reviewed for completeness | Warm handoff = bridge from sponsor internal work to advisor/investor consumption |

**Readiness Signals:**
- ✅ Deal ready for close when P6.1-P6.6 all = `ready` AND final credit facilities (equity + debt) are committed

---

## 6. READINESS DIMENSIONS & SCORING RULES

### 6.1 Readiness Dimensions (6 Total)

Each dimension is scored 0.0-5.0; weighted average = overall readiness score.

| Dimension | Weight | 0.0 (None) | 1.0 (Concept) | 2.0 (Preliminary) | 3.0 (Substantial) | 4.0 (Well-Defined) | 5.0 (Institutional) |
|---|---|---|---|---|---|---|---|
| **1. Issuer & Legal Authority** (20%) | 20% | No IDA formed; no statute cited | IDA formed; unclear authority | IDA resolution adopted; tax status uncertain | Tax status memo complete; governing body support documented | IDA fully authorized; tax exemption confirmed or taxable path clear; inducement adopted | Full legal opinion from counsel; volume cap allocated; all governance approvals executed |
| **2. Project, Technology, Ops** (20%) | 20% | Concept only; no specs | Tech specs preliminary; site TBD | Feasibility study underway; site option secured; OM plan outline | Tech specs detailed; site control document executed; staffing plan realistic | Tech validated at demo scale; detailed site plans; OM procedures documented | Full independent engineer feasibility report; site permits advancing; operator agreements signed |
| **3. Revenue & Feedstock** (15%) | 15% | Revenue projections absent | Market study preliminary; feedstock assessed informally | Commodity pricing estimated; feedstock MOU negotiated | Revenue ramp conservative; 1-2 feedstock contracts advanced | Revenue model detailed; 3+ feedstock suppliers; 2+ offtake agreements in place | Long-term offtake contracts (5+ years) executed at fixed prices; feedstock supply agreements binding |
| **4. CAB-Specific Financial** (20%) | 20% | CAB structure undefined | CAB concept described; no accretion profile | Accretion rate chosen; basic schedule drafted | Accretion schedule reconciled to revenue ramp; DSCR Year 6+ supportable | CAB terms crystallized; conversion logic transparent; turbo redemptions modeled; DSCR Year 1-5 = N/A, Years 6-20 ≥ 1.35x | CAB schedule externally validated; stress tested to 80% revenue; modeling confirms no forced conversion before maturity |
| **5. Risk, Security, SLB** (15%) | 15% | Risks not documented; security undefined; SLB cosmetic | Risk list preliminary; security concepts identified; SLB framework draft | Risk register 8+ items; security package outlined; SLB KPIs selected but baselines TBD | Risk mitigants mapped; security docs drafted; SLB SPTs calibrated with independent review | Insurance/guarantees priced; revenue pledge and UCC filings prepared; SLB penalties ≥ 35 bps with call protection | Final risk report by technical advisor; security filings completed; SLB second-party opinion issued; insurance policies bound |
| **6. SLB Architecture & Verification** (10%) | 10% | SLB not considered | SLB framework sketch; no verifier identified | KPI definitions drafted; verifier ToR prepared; observation dates TBD | SLB KPIs tied to operational metrics; verifier selected; observation dates fixed (Yr 3, 6, 9) | SLB baseline methodology locked; SPT targets externally benchmarked; reporting template finalized | Second-party opinion executed; external verifier confirmed; SLB terms incorporated into indenture; annual reporting protocol documented |

### 6.2 Scoring Rules & Gates

**Overall Readiness Score = Weighted Average of 6 Dimension Scores**

```
Score = (Issuer×0.20) + (Project×0.20) + (Revenue×0.15) + (CAB×0.20) + (Risk×0.15) + (SLB×0.10)
```

| Score Range | Interpretation | Recommended Action |
|---|---|---|
| 0.0-3.0 | **Too Early** | Focus on foundational work (P1-P2). Do not engage advisors yet. High risk of pivots/delays if external parties engaged now. |
| 3.1-5.5 | **Structurally Viable** | Sponsor-led work should continue (P3-P4). Selective advisor input welcome (e.g., bond counsel for tax opinion, IE for feasibility). Not yet ready for full market engagement. |
| 5.6-7.5 | **Ready for Selective Engagement** | Sponsor work substantially complete; bond counsel, financial advisor, and IE reports done. Market engagement can begin (underwriter conversations, initial rating agency presentations). Expect closing in 6-9 months. |
| 7.6-10.0 | **Ready for Broad Market** | All P1-P6 work complete; credit facilities committed; underwriter managing book; closing imminent. |

### 6.3 Gap Severity Rules

**Gaps are classified by dimension and impact:**

| Gap Severity | Definition | Example | Recommendation |
|---|---|---|---|
| **Low** | Secondary evidence missing; does not block next phase | Operating margin estimate differs 5%; revenue growth assumption 3% vs. 5% | Monitor; resolve if convenient; not blocking |
| **Medium** | Material gap affecting DSCR or risk profile; workable with minor effort | Feedstock supply confirmed at 85% of nameplate throughput vs. 100%; revenue ramp delayed 6 months | Priority P3-P4 work; must be resolved before advisor engagement |
| **High** | Critical path blocking; must be resolved before next phase | Site control not yet executed (only LOI); CAB accretion rate not finalized; SLB observation dates TBD | Halt phase transition until resolved; escalate to sponsor leadership |
| **Critical** | Deal-breaking; may require structural redesign | Technology fails key performance test; permitting pathway blocked by regulatory change; feedstock supply drops below 50% of nameplate | Engage advisors immediately; consider project pivot or halt |

---

## 7. EXPLANATION TEMPLATES

### 7.1 Why-It-Matters Narratives (Per Dimension)

**Dimension 1: Issuer & Legal Authority**
> Investor confidence begins with unambiguous legal authority. Industrial Development Authorities issue bonds on behalf of private projects under state statute; any uncertainty about this authority creates title risk and reduces market access. Tax-exempt qualification (IRC §142a6 for waste conversion, or §144a for manufacturing) can reduce financing costs 150-200 bps. If tax-exempt qualification is uncertain, advisors must pursue private letter ruling (6-9 month timeline, expensive), or default to taxable structure (higher cost but faster).

**Dimension 2: Project, Technology & Operations**
> Investor risk begins with project execution. Operational risk—not just technology risk—is the primary driver of debt service coverage. Can the operator staff the facility at claimed headcount? Is OM budget realistic? Independent Engineer reports are the gold standard here; they validate design life, throughput, staffing assumptions, and flag operational risks (e.g., "feedstock variability 10-20% impacts revenue projections"). If technology is at demonstration scale only, IE report must be explicit about performance assumptions.

**Dimension 3: Revenue & Feedstock**
> Revenue is the only security for bondholders. Commodity pricing must be conservative and supported by offtake agreements (not spot market assumptions). Feedstock availability is the linchpin: if feedstock supply drops 20%, revenue drops 20%. Multi-supplier strategy and long-term contracts are essential. If feedstock is secured only by informal MOUs, not binding contracts, DSCR and debt sizing must be downward-adjusted.

**Dimension 4: CAB-Specific Financial**
> Capital appreciation bonds are non-standard and require transparent justification. They defer principal and interest for 5-7 years (ideal for projects with revenue ramps), but the accreted value at maturity can be 1.5-2.0x the original face value. If the project underperforms and cash flow is insufficient, accreted bonds compound the problem. Accretion rates must be stress-tested: if revenue grows only 2% vs. projected 5%, can the project still convert to current-pay on schedule?

**Dimension 5: Risk, Security & Disclosure**
> Risk transparency is the covenant between issuer and investor. Identified risks (technology, feedstock, commodity price, permitting, market) must have documented mitigants. Security (equipment liens, real property mortgages, revenue pledges) must be first-lien and perfected under UCC. Insurance (business interruption, pollution liability) must be adequate. Disclosure must not hide risks; instead, it must explain why risks are manageable.

**Dimension 6: SLB Architecture & Verification**
> Sustainability-linked bonds are economically meaningful only if penalties are real. World Bank research (2024) found that 77% of SLBs have step-up penalties LOWER than the pricing premium (greenium), meaning issuers profit even if targets are missed. Credible SLB structure requires: (1) conservative baselines (3+ years historical data), (2) ambitious but achievable SPTs (80th percentile of expected performance), (3) sufficient penalties (≥35-40 bps), (4) early observation dates (Year 3, not Year 15), (5) call protection (no redemption within 12 months post-observation), and (6) external third-party verification. Weak SLBs are worse than no SLB (reputational damage).

### 7.2 Checklist Item Explanation Templates

**When Item = `inprogress`:**
> Partial progress on [item name]. Currently [X of Y required facts] are accepted. Missing: [list fact paths]. Recommend: [action to complete by [target date]].

**When Item = `blocked`:**
> Cannot proceed with [item name] due to [conflicting OR rejected] facts. Issue: [describe conflict]. Resolution: [who must act, what must be done, target timeline]. Impact on timeline: [days blocked].

**When Item = `ready`:**
> Sufficient evidence confirms [item name]. Supporting facts:
> - [Fact path 1]: [value] (source: [artifact ID])
> - [Fact path 2]: [value] (source: [artifact ID])
> All facts accepted without conflict. Item ready for next phase sign-off.

---

## 8. WARM HANDOFF PACK TEMPLATE STRUCTURE

### 8.1 Pack Sections

The Warm Handoff Pack is a structured, advisor-ready output assembled from WP5 (financial models) and WP4 (readiness insights). It contains:

1. **Cover & Metadata** (1 page)
   - Project name, issuer, date, playbook version, BFMS version
   - Mandatory disclaimer (see section 8.2)

2. **Deal Overview Memo** (3-5 pages, templated)
   - Subsections: Project Summary | Issuance Intent (CAB/SLB context) | Parties & Roles | Use of Proceeds | Revenue Model | Structural Notes
   - Sourced entirely from accepted ExtractedFacts; no inference
   - Declarative, not persuasive language

3. **Readiness & Gap Report** (2-3 pages)
   - Overall readiness score + dimension breakdown
   - Key blockers (high/critical severity gaps)
   - Prioritized action items with owners and deadlines
   - Sourced from WP4 dimension scores and gap analysis

4. **Checklist Status Summary** (2-4 pages, by phase P1-P6)
   - Items grouped by phase, status per item (notstarted | inprogress | needsreview | ready | blocked)
   - Expandable evidence links (fact IDs supporting each item)
   - Read-only; no ability to modify status here (that's WP4)

5. **Evidence Index** (4-8 pages)
   - Audit trail of all accepted facts
   - Columns: Schema Path | Value | Unit | Source Artifact | Page/Sheet | Chunk ID | Confidence | Review Status
   - Non-narrative, structured table format
   - Investors can drill into any claim and find source

6. **Assumption Register** (1-2 pages)
   - Table of all assumptions: Name | Value | Unit | Source | Confidence | Rationale | Impact Category
   - Assumptions driving CAB accretion rate, SLB baselines, DSCR sensitivity

7. **Financial Model Outputs** (4-6 pages)
   - Revenue projections (Year 1-20 table)
   - Operating expense breakdown
   - Debt service schedule (CAB accretion period + current-pay period)
   - DSCR by year (with note that Years 1-5 = N/A for CAB)
   - Cash flow waterfall
   - Sensitivity tables (±10%, ±20% revenue scenarios)
   - All tables include disclaimer: "These tables reflect input assumptions only and are not financing recommendations or sizing guidance."

8. **SLB KPI Brief** (1-2 pages)
   - Table: KPI Name | Baseline Value | Year 3 SPT | Year 6 SPT | Year 9 SPT | Verification Method | Step-Up Trigger
   - No penalty mechanics (those are in bond docs, not pack)
   - Focus: transparency on targets and verification rigor

9. **Disclosure Outline Skeleton** (2-3 pages)
   - Section outline for Official Statement (public) or PPM (private)
   - Headings only, no drafted prose
   - Shows how facts from evidence index map into final disclosure (e.g., "Security" section will describe [equipment liens], [real property mortgage], [revenue pledge])
   - Advisors use this as starting point for drafting

### 8.2 Mandatory Disclaimer

```
DISCLAIMER

This Warm Handoff Pack was generated by the Bond Facility Management System (BFMS)
Version [X.X] on [DATE]. It is based solely on accepted facts and explicit assumptions
extracted from uploaded project documents as of the pack generation date.

This package does NOT constitute:
- Financial advice or recommendation to proceed with financing
- Bond sizing, pricing, or yield optimization guidance  
- Legal analysis or opinion (legal review by bond counsel required)
- Replacement for professional advisory services
- Insurance against project or market risks
- Approval of this project for financing

All contents are intended for internal use by project sponsors and their advisors.
External distribution to investors or rating agencies requires legal and financial
advisor review and approval.

The financial models, readiness scores, and gap analyses reflect the information
available as of [DATE]. Material changes in project scope, market conditions, or
technology assumptions will require model updates and re-scoring.

This package must be rebuilt and reviewed if:
- Significant facts change (revenue assumptions, offtake status, permitting delays, etc.)
- More than 90 days have elapsed since pack generation
- Advisors request validation of specific facts or calculations
- New information contradicts accepted facts

Professional advisors (bond counsel, financial advisor, rating agencies) retain
full authority to modify, replace, or reject any finding in this pack based on their
independent analysis.
```

---

## 9. BOND ISSUANCE PROCESS GOVERNANCE (EMPIRICALLY-INFORMED)

### 9.1 Transaction Timeline (Canonical 12-Month Issuance)

| Month | Phase | Key Milestones | Sponsor-Led Work | Advisor-Required Work | Readiness Prerequisite |
|---|---|---|---|---|---|
| 0 | Concept | IDA board discussion; preliminary feasibility | Feasibility study commissioned | — | Readiness 0.0-2.0 |
| 1 | P1 Initiation | Inducement resolution adopted; tax status determination | Bond counsel engaged for preliminary opinion | Tax-exempt opinion (if applicable) | Readiness 2.0-3.0 |
| 2-3 | P1-P2 | Site control negotiated; OM plan drafted; preliminary feedstock assessment | IE preliminary scope; permitting pathway mapped | IE contracts executed | Readiness 3.0-4.0 |
| 3-4 | P2-P3 | Feedstock agreements advanced (MOUs); preliminary financial model built; revenue assumptions conservative | IE feasibility study underway; financial model review | IE report outline | Readiness 4.0-5.0 |
| 5-6 | P3-P4 | Offtake agreements finalized (minimum 2); DSCR model locked; risk register completed; SLB framework drafted | IE report issued (draft); credit rating discussion | Rating agency initial presentation | Readiness 5.0-6.0 |
| 6-7 | P4-P5 | SLB baselines finalized; SPTs calibrated; second-party opinion (SPO) engagement | IE final report; credit rating issued; underwriter discussions initiated | Underwriter commitment | Readiness 6.0-7.0 |
| 7-8 | P5 | Warm Handoff Pack assembled; closing document templates circulated | Bond counsel draft transaction docs; underwriter marketing strategy | Underwriter book begins | Readiness 7.0-8.0 |
| 8-9 | P6 Early | Investor education/roadshow; pricing guidance from underwriter | Closing document execution; final underwriting | Underwriter bid process (competitive) or negotiated terms | Readiness 8.0-9.0 |
| 9-10 | P6 Mid | Bond pricing, credit rating finalization; final terms locked | Closing prep (insurance, appraisals, final audit); continuing disclosure agreements | Investor allocation; rating finalized | Readiness 9.0-9.5 |
| 10-11 | P6 Late | Final regulatory approvals (air quality permit); construction budget review | Final due diligence by investors; legal closing prep | Final updates to OS/PPM; SEC compliance (if public) | Readiness 9.5-10.0 |
| 11-12 | Closing | Bond proceeds wired; construction fund funded; UCC-1 and mortgage filings effective | Project mobilization begins; trustee account setup | Final closing opinions | Readiness 10.0 |

### 9.2 Empirical Benchmarks: Costs, Timing, Market Standards

**Issuance Costs (for 40-45M taxable SLB bond):**
- Bond counsel: $150-250K
- Borrower counsel: $100-150K
- Underwriter/placement agent: $400-600K (1.0-1.5% of bond amount)
- Financial advisor: $50-100K
- Independent engineer: $75-150K
- Environmental consultant: $25-50K
- Trustee setup & annual: $25-40K first year
- Rating agency: $75-125K (if rated)
- SLB verifier (SPO + annual): $30-50K first year, $15-25K annually thereafter
- Miscellaneous (title, survey, printing): $50-100K
- **Total: $1.0M-1.6M (2.5-4.0% of bond amount)**

**Timing Benchmarks:**
- **Tax-exempt qualification timeline:** 6-9 months (IRS private letter ruling) + 9-12 months bond execution = 15-21 months total (prefer taxable if timeline urgent)
- **Taxable SLB execution:** 4-6 months from engagement to close (faster; no IRS review)
- **Independent engineer report:** 10-12 weeks after engagement; includes technology review, financial projections, risk assessment
- **Credit rating (if pursued):** 6-8 weeks from initial presentation to rating confirmation

**Empirical Debt Metrics (from public muni bonds for environmental projects):**
- **Average CAB accretion rate:** 5.5-6.5% annually (UCS default: 6.35%)
- **Average current-pay coupon post-CAB conversion:** +50 bps above treasury + spread (e.g., 6.35% accretion → 6.50% current-pay)
- **Average DSCR covenant:** 1.35x for high-CAPEX industrial projects; 1.50x if commodity exposure
- **Average SLB greenium (pricing premium):** 25-43 bps (empirical mean 29-31 bps)
- **Average SLB step-up penalty:** 35-50 bps (lower limits insufficient per World Bank research)
- **Average SLB observation date frequency:** Years 3, 6, 9 (avoid Year 15+ gaming)

---

## 10. SAMPLE INFERENCE & CONFLICT RESOLUTION RULES

### 10.1 When AI Must Flag Low Confidence or Conflicts

**Scenario A: Revenue Assumption Variance**
> Extracted Fact #1 (from RFP): "Annual renewable diesel production 2.25M gallons @ $4.50/gallon = $10.1M annual revenue"
> Extracted Fact #2 (from Feasibility Study): "Conservative revenue projection $9.5M annually assuming $4.20/gallon"
> 
> **System Action:** Flag conflict. Confidence on #1 = 0.95; confidence on #2 = 0.80. Create two ExtractedFact records with status="proposed". Notify reviewer: "Revenue assumption variance of 6% ($10.1M vs. $9.5M). Which is source of truth for financial modeling: RFP technical specs or feasibility study conservative case?"

**Scenario B: Feedstock Supply Status Ambiguity**
> Extracted Fact: "Gold Seal Industries has negotiated feedstock agreements with local forestry partners"
> 
> **System Issue:** "Negotiated" could mean LOI, MOU, or binding contract. Confidence < 0.75. Prompt reviewer to clarify: "What is the status of feedstock agreements: (A) Executed binding contract, (B) Advanced MOU with term sheet, (C) Letter of Intent framework, or (D) Preliminary discussions?" Specify tenor of agreement if known.

**Scenario C: CAB Accretion Rate Conflict**
> Extracted Fact #1 (from Term Sheet draft v1.0): "6.35% annual accretion"
> Extracted Fact #2 (from Term Sheet draft v2.0 dated 2 weeks later): "6.50% annual accretion"
> 
> **System Action:** Conflict on CRITICAL path. Flag for immediate human review: "CAB accretion rate changed from 6.35% to 6.50% (+15 bps) between v1 and v2. This impacts debt service trajectory and DSCR Year 6+. Confirm which is operative term, and document reason for change (e.g., 'market rate adjustment', 'sponsor request for lower cost').

### 10.2 Confidence Scoring Guidance for Extractors

**High Confidence (0.85-1.0):**
- Fact appears in executed/signed documents (contracts, permits, board resolutions)
- Fact appears consistently across 2+ independent sources
- Fact is objective quantitative data with clear measurement (e.g., "100 tons/day throughput per UCS spec sheet")
- Fact is supported by independent validation (e.g., feasibility study, engineer report)

**Medium Confidence (0.65-0.84):**
- Fact appears in draft documents or preliminary reports
- Fact appears once in credible source but not independently verified
- Fact is derived from reasonable assumptions clearly stated
- Fact has minor conflicts with other sources (< 10% variance)

**Low Confidence (0.40-0.64):**
- Fact appears in preliminary or informal sources (emails, meeting notes, vendor estimates)
- Fact is estimated or extrapolated (e.g., revenue based on market study, not contract)
- Fact has material conflicts with other sources (10-25% variance)
- Fact depends on unstated assumptions

**Very Low / Flag for Review (< 0.40):**
- Fact is contradicted by multiple sources
- Fact depends on unverified technical claims
- Fact is subject to material regulatory uncertainty
- Fact appears in single non-authoritative source

---

## 11. IMPLEMENTATION ROADMAP (FOR BFMS ENGINEERING)

### 11.1 MVP Deliverables (v0.2)

**Phase 1: Schema & Vocabulary (Week 1-2)**
- [ ] Finalize allowlist of 45-60 schema paths (Section 3.1)
- [ ] Assign criticality tiers to each path (Critical / Material / Secondary)
- [ ] Document rationale for each path per UCS CAB+SLB domain
- [ ] Create JSON schema definition for Postgres storage

**Phase 2: Extractor Definitions (Week 2-3)**
- [ ] Code 6-8 extractors (ProjectDescriptionExtractor, PartiesExtractor, FeedstockSupplyExtractor, RevenueOfftakeExtractor, OperatingExpenseExtractor, CABTermsExtractor, SLBMetricsExtractor, DSCRInputsExtractor)
- [ ] Populate prompt templates per section 4.1
- [ ] Define confidence thresholds and bulk acceptance rules
- [ ] Create idempotency key algorithm

**Phase 3: Checklist & Readiness Rules (Week 3-4)**
- [ ] Hardcode P1-P6 checklists as DB records (6 phases × 5-6 items per phase = 30-36 items)
- [ ] Define statusrule expressions (e.g., "all required facts non-null AND confidence > 0.80 AND no conflicts")
- [ ] Implement readiness dimension scoring logic (weighted averages, gap severity classification)
- [ ] Create explanation templates per section 7.1

**Phase 4: Warm Handoff Pack Generation (Week 4-5)**
- [ ] Template-driven pack assembly (sections 8.1)
- [ ] Implement mandate disclaimer auto-insertion (section 8.2)
- [ ] Create export functions: MD, PDF, DOCX formats
- [ ] Add versioning and regeneration tracking

**Phase 5: Testing & Validation (Week 5-6)**
- [ ] One end-to-end test with real UCS project data
  - Upload RFP response, feasibility study, financial model, term sheet
  - Run extractors; validate extracted facts map to correct schema paths
  - Run readiness calculation; confirm scores align with manual assessment
  - Generate warm handoff pack; QA against advisor readability
- [ ] Document any schema gaps or extractor errors
- [ ] Refine prompts based on test results

### 11.2 Success Criteria for MVP v0.2

- ✅ All extractors return proposed facts with confidence scores
- ✅ Checklist items compute correct states (notstarted | inprogress | needsreview | ready | blocked)
- ✅ Readiness dimensions compute weighted scores (0.0-10.0 range)
- ✅ Gap analysis identifies high/critical items for sponsor focus
- ✅ Warm Handoff Pack generates in <5 minutes, exports to PDF cleanly
- ✅ Advisor can read pack in 15 minutes and understand: project scope, DSCR outlook, key risks, SLB credibility
- ✅ All claims in pack trace back to ExtractedFacts with provenance (artifact ID, page, confidence)
- ✅ No part of pack implies approval or recommendation ("ready," "approved," "recommended" language banned)

---

## 12. FUTURE ENHANCEMENTS (v0.3+)

- **Predictive Risk Scoring:** ML model trained on historical municipal bond performance to flag project archetypes with elevated risk (tech-heavy, first-mover, commodity exposure)
- **Multi-System Scaling Models:** Playbook extension for master trust indenture scenarios (Systems 1-10 on parity basis)
- **Tax-Exempt Qualification Automation:** IRS private letter ruling checklist for IRC §142a6 vs. §144a qualification paths
- **Real-Time Covenant Monitoring:** Post-closing trustee data feeds enabling monthly DSCR tracking vs. 1.35x covenant floor
- **Investor Preference Mapping:** ESG investor alignment analysis (which investors prioritize waste diversion vs. emissions reduction; pricing impact)
- **Comparative Deal Analytics:** Benchmarking UCS CAB+SLB against peer waste conversion transactions (DC Water, California Clean Energy, etc.) on DSCR, tenor, coupon, SLB terms

---

## 13. VERSION CONTROL & GOVERNANCE

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 | 2026-01-27 | [BFMS Team] | Initial draft: schema paths, extractors, checklists P1-P6, readiness framework |
| 0.2 | 2026-01-27 | [Operations Manager] | Added empirical bond benchmarks, SLB penalty calibration guidance, timeline, warm handoff pack templates, implementation roadmap |
| — | TBD | — | Future: Add master trust scenarios, tax-exempt automation, covenant monitoring extensions |

**Maintenance Protocol:**
- Quarterly review against new municipal bond market developments
- Annual update against ICMA SLB Principles revisions (next: 2027)
- Ad-hoc amendments if UCS technology achieves material efficiency gains or permitting landscape shifts

---

## 14. APPENDIX: CRITICAL SCHEMA PATH REFERENCE

**Quick-Reference: Must-Have Facts by Phase**

| Phase | Minimum Required Paths | Acceptable Confidence | Source |
|---|---|---|---|
| P1 Close | `parties.issuer`, `regulatory.tax-status`, `governance.inducement` | ≥0.85 | Inducement resolution, attorney opinion |
| P2 Close | `project.canonicaldescription`, `technology.throughput.nameplate`, `feedstock.volume.annual`, `feedstock.supply.mechanism`, `project.location.sitecontrol` | ≥0.80 | Feasibility study, site control doc, supply MOU |
| P3 Close | `revenue.gross.annual`, `opex.total.annual`, `finmodel.outputs.dscrbase`, `cab.originalprincipial`, `capital.equity-percent` | ≥0.80 | Financial model, term sheet |
| P4 Close | `risk.register` (8+ items), `security.equipment.schedule`, `security.revenue.pledge`, `slb.kpi.shortlist` (if SLB) | ≥0.75 | Risk report, security docs, SLB framework |
| P5 Close | `slb.kpi.{n}.baseline.methodology`, `slb.penalty.stepup.magnitude`, `slb.penalty.observation.dates`, SLB observation date ≤ 50% of tenor | ≥0.85 | SPO, second-party opinion |
| P6 Ready | All P1-P5 paths + bond counsel opinion, rating (if applicable), underwriter commitment | ≥0.90 | Closing documents, rating letter, UW commitment |

---

**END OF PLAYBOOK v0.2**

---

## CLOSING NOTE FOR OPERATIONS MANAGER

This playbook encodes **what bond professionals think about waste-to-energy CAB+SLB structures**, not what the system computes. It is the bridge between your team's raw project context and the structured, advisor-ready handoff your underwriter and rating agencies expect.

Use this as your internal roadmap:
1. **Weeks 0-6:** Sponsor-led work (P1-P2) using checklist in Section 5
2. **Weeks 6-12:** Financial advisor & IE engagement (P3-P5); build readiness score to 7.0+
3. **Weeks 12-24:** Bond counsel, underwriter, rating agency; execute P6

If readiness score stalls below 5.5 for >4 weeks, escalate. It signals either:
- Technical gaps that require pivoting (e.g., feedstock supply harder than assumed)
- Advisor dependencies earlier than planned (engage bond counsel to clarify tax-exempt path)
- Market conditions shifted (raise rates, SLB investor appetite declined)

The playbook is **v0.2 and intentionally v0.1-grade**. It will evolve as your team runs one transaction end-to-end. Feedback loops from actual advisor interactions will refine the schema paths, extractor prompts, and readiness thresholds.

Good luck. You've built something genuinely novel here.

---
