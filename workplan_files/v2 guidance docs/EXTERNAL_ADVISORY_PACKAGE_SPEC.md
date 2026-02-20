# External Advisory Package Specification

**Bond Facility Management System (BFMS)**

**Status:** FINAL (v1.0) | **Purpose:** Municipal Advisor Deliverable

---

## 1. DOCUMENT PURPOSE

The External Advisory Package is the **professional deliverable** provided to municipal advisors, bond counsel, underwriters, and rating agencies. It demonstrates that the project sponsor has done substantive preparation work and is ready for sophisticated engagement.

This package is designed for **external consumption**. It presents validated evidence in a professional format without revealing internal operational details, gap tracking, or work-in-progress status.

---

## 2. CORE PRINCIPLES

### 2.1 Professional Neutrality

- Factual, declarative language only
- No promotional adjectives
- No forward-looking claims without qualification
- Balanced presentation of opportunities and risks

### 2.2 Evidence Transparency

- Every claim traces to documented evidence
- Sources are identified (not hidden)
- Assumptions are clearly labeled
- TBD markers acknowledge limitations honestly

### 2.3 Audience Respect

- Assumes bond professional expertise
- Doesn't explain basic bond concepts
- Provides information advisors need to do their job
- Avoids unnecessary repetition

### 2.4 Gap Concealment (Appropriate)

The External Package does NOT reveal:
- Internal gap tracking or scoring details
- Operational checklist status
- Information request workflows
- Team assignments or deadlines
- Internal debates or conflicts

Gaps appear only as "[TBD]" markers in disclosure sections, signaling that information is pending without exposing internal process.

---

## 3. AUDIENCE & USE CASES

### 3.1 Primary Audience

| Audience | What They Need |
|----------|----------------|
| Municipal Advisor | Deal overview, financials, structure |
| Bond Counsel | Legal authority, tax status, parties |
| Underwriter | Credit profile, marketing angles |
| Rating Agency | Risk factors, financial metrics |
| Independent Engineer | Technology specs, operating plan |

### 3.2 Use Cases

| Use Case | Package Section |
|----------|-----------------|
| Initial advisor engagement meeting | Deal Overview + Executive Summary |
| Credit analysis | Financial Tables + Disclosure Document |
| Tax opinion preparation | Disclosure: The Issuer |
| Marketing preparation | Disclosure: Project + SLB Features |
| Risk assessment | Disclosure: Risk Factors |

---

## 4. PACKAGE STRUCTURE

### 4.1 Section Hierarchy

```
ExternalAdvisoryPackage
├── Cover Page
├── Executive Summary (1 page)
├── Deal Overview Memo (3-5 pages)
│   ├── Project Summary
│   ├── Issuance Intent
│   ├── Transaction Parties
│   ├── Use of Proceeds
│   ├── Revenue Model Summary
│   └── Structural Notes
│
├── Disclosure Document (10-15 pages) ← WP7 OUTPUT
│   ├── Introduction and Summary
│   ├── The Issuer
│   ├── The Project
│   ├── Security and Sources of Payment
│   ├── Financial Information
│   ├── Risk Factors
│   └── Sustainability-Linked Features
│
├── Financial Tables (4-6 pages)
│   ├── Capital Structure Summary
│   ├── Revenue Projections
│   ├── Operating Expense Summary
│   ├── Debt Service Schedule
│   ├── DSCR Analysis
│   └── Sensitivity Tables
│
├── SLB KPI Brief (1-2 pages)
│   ├── Selected KPIs
│   ├── Baseline Values
│   ├── SPT Targets
│   └── Verification Framework
│
├── Key Assumptions (1 page)
│   └── Material Assumptions Summary
│
└── Mandatory Disclaimer (1 page)
```

---

## 5. SECTION SPECIFICATIONS

### 5.1 Cover Page

**Purpose:** Professional presentation with clear identification

**Content:**
```
─────────────────────────────────────────
         ADVISORY INFORMATION PACKAGE
─────────────────────────────────────────

              [PROJECT NAME]

        [Location, State] Revenue Bonds
        
    Capital Appreciation Bond Structure with
    Sustainability-Linked Bond Features

─────────────────────────────────────────

              Prepared for:
         Municipal Advisor Review

             [Date Prepared]

─────────────────────────────────────────

    Prepared by: [Sponsor Name]
    With support from: Bond Facility Management System

─────────────────────────────────────────

    PRELIMINARY — FOR DISCUSSION PURPOSES ONLY
    
    This document does not constitute an offering 
    of securities or a recommendation to proceed.

─────────────────────────────────────────
```

---

### 5.2 Executive Summary

**Purpose:** One-page orientation for busy professionals

**Content:**

```markdown
## Executive Summary

### Transaction Overview

{parties.issuer.name} proposes to issue revenue bonds to finance a 
{project.canonicaldescription_short}. The proposed structure incorporates 
{IF cab.enabled}Capital Appreciation Bond (CAB) features{ENDIF}
{IF slb.enabled} with Sustainability-Linked Bond (SLB) components{ENDIF}.

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Project Cost | ${capital.project-cost:formatted} |
| Proposed Bond Amount | ${cab.originalprincipial:formatted} |
| Equity Contribution | ${capital.equity-contribution:formatted} ({capital.equity-percent:percent}%) |
| Base Case DSCR | {finmodel.outputs.dscrbase:formatted}x |
| Bond Tenor | {cab.finalmaturitydate} years |

### Structural Highlights

- **CAB Accretion Period:** {cab.accretion.period.years} years at {cab.accretionrate}%
- **SLB KPIs:** {slb.kpis.shortlist}
- **Security:** First-lien equipment and gross revenue pledge

### Information Pending

The following items are in development and will be provided in subsequent packages:
{FOR tbd IN tbd_items WHERE tbd.severity IN ['critical', 'high']}
- {tbd.reason}
{ENDFOR}

### Next Steps

This package is provided to support preliminary discussions with the municipal 
advisory team. We are prepared to provide additional detail on any section 
and to schedule follow-up meetings as appropriate.
```

---

### 5.3 Deal Overview Memo

**Purpose:** Detailed orientation without disclosure-level formality

This section is largely preserved from existing WP6, with refinements:

- Remove internal references
- Enhance party descriptions
- Add structural rationale
- Include timeline overview

**Content Sections:**

1. **Project Summary** — Technology, location, capacity, operating status
2. **Issuance Intent** — Why CAB? Why SLB? Strategic rationale
3. **Transaction Parties** — Issuer, borrower, operator, sponsor, advisors
4. **Use of Proceeds** — Sources & uses table
5. **Revenue Model Summary** — Commodity mix, offtake status, pricing basis
6. **Structural Notes** — CAB mechanics, SLB framework, covenant structure

---

### 5.4 Disclosure Document

**Purpose:** Preliminary disclosure content for advisor review

**Source:** WP7 Disclosure Synthesis Engine output

**Key Characteristics:**

- Synthesized prose from extracted facts
- [TBD] markers for incomplete information
- Every claim traceable to evidence
- Professional, neutral language
- Risk factors presented factually

**Integration:**
```python
def build_disclosure_section(project_id: UUID) -> DisclosureDocument:
    # Generate via WP7
    return generate_disclosure_document(project_id)
```

---

### 5.5 Financial Tables

**Purpose:** Structured financial data for advisor analysis

**Source:** WP5 Financial Model Outputs

**Tables Included:**

#### Table 1: Capital Structure

| Item | Amount | % of Total |
|------|--------|------------|
| Total Project Cost | ${} | 100% |
| Equipment Cost | ${} | {}% |
| Site & Construction | ${} | {}% |
| Soft Costs | ${} | {}% |
| Contingency | ${} | {}% |
| **Sources:** | | |
| CAB Proceeds | ${} | {}% |
| Equity Contribution | ${} | {}% |

#### Table 2: Revenue Projections (Years 1-20)

| Year | Gross Revenue | Operating Expense | Net Revenue | DSCR |
|------|--------------|-------------------|-------------|------|
| 1 | ${} | ${} | ${} | N/A (CAB) |
| ... | | | | |
| 20 | ${} | ${} | ${} | {}x |

#### Table 3: CAB Accretion Schedule

| Year | Beginning Principal | Accretion | Ending Principal |
|------|---------------------|-----------|------------------|
| 1 | ${} | ${} | ${} |
| ... | | | |

#### Table 4: Debt Service Schedule (Post-Conversion)

| Year | Principal | Interest | Total Debt Service |
|------|-----------|----------|-------------------|
| {} | ${} | ${} | ${} |
| ... | | | |

#### Table 5: DSCR Analysis

| Scenario | Year 6 | Year 10 | Year 15 | Year 20 |
|----------|--------|---------|---------|---------|
| Base Case | {}x | {}x | {}x | {}x |
| Stress (-20% Revenue) | {}x | {}x | {}x | {}x |
| Minimum Covenant | 1.35x | 1.35x | 1.35x | 1.35x |

#### Table 6: Revenue Sensitivity

| Revenue Scenario | DSCR Impact | Covenant Cushion |
|------------------|-------------|------------------|
| Base Case | {}x | {}% |
| -10% | {}x | {}% |
| -20% | {}x | {}% |
| +10% | {}x | {}% |

**Disclaimer Footer:**
```
These financial projections are preliminary and based on assumptions 
documented in the Key Assumptions section. All figures are subject to 
independent verification by the financial advisor and Independent Engineer.
```

---

### 5.6 SLB KPI Brief

**Purpose:** Summary of sustainability-linked features for ESG-focused review

**Content:**

```markdown
## Sustainability-Linked Bond Features

### Framework Alignment

This bond issuance incorporates Sustainability-Linked Bond (SLB) features 
aligned with the International Capital Market Association (ICMA) 
Sustainability-Linked Bond Principles (2023).

### Selected Key Performance Indicators

| KPI | Baseline | Year 3 SPT | Year 6 SPT | Year 9 SPT |
|-----|----------|------------|------------|------------|
| {kpi.1.name} | {kpi.1.baseline} | {kpi.1.spt_y3} | {kpi.1.spt_y6} | {kpi.1.spt_y9} |
| {kpi.2.name} | {kpi.2.baseline} | {kpi.2.spt_y3} | {kpi.2.spt_y6} | {kpi.2.spt_y9} |

### KPI 1: {slb.kpi.1.name}

**Definition:** {slb.kpi.1.definition}

**Baseline Value:** {slb.kpi.1.baseline.value}

**Measurement Methodology:** {slb.kpi.1.baseline.methodology}

**Verification:** {slb.kpi.1.verification.method OR "[TBD: Verification method to be established]"}

### Economic Linkage

| Event | Consequence |
|-------|-------------|
| SPT Met | No coupon adjustment |
| SPT Missed | +{slb.penalty.stepup.magnitude} bps coupon step-up |

### Observation Schedule

- Year 3: First observation date
- Year 6: Second observation date  
- Year 9: Third observation date

### Verification Protocol

{IF slb.verification.protocol}
{slb.verification.protocol}
{ELSE}
Verification protocol to be finalized in consultation with Second-Party 
Opinion provider. Annual reporting with third-party assurance anticipated.
{ENDIF}
```

---

### 5.7 Key Assumptions

**Purpose:** Explicit listing of material assumptions (filtered from full register)

**Content:**

```markdown
## Key Assumptions

The financial projections and disclosure content in this package are based 
on the following material assumptions. These assumptions are subject to 
validation by the financial advisor and Independent Engineer.

### Financial Assumptions

| Assumption | Value | Basis |
|------------|-------|-------|
| CAB Accretion Rate | {cab.accretionrate}% | Market comparable analysis |
| Revenue Growth Rate | {finmodel.inputs.revenue_ramp}% | Feasibility study |
| Operating Margin | {opex.margin}% | Operator projections |
| Inflation Rate | {}% | Industry standard |

### Operational Assumptions

| Assumption | Value | Basis |
|------------|-------|-------|
| Annual Throughput | {feedstock.volume.annual} tons | Nameplate × 351 days |
| Capacity Factor | {}% | Conservative estimate |
| Equipment Useful Life | {technology.lifespan} years | Manufacturer specification |

### Market Assumptions

| Assumption | Value | Basis |
|------------|-------|-------|
| Renewable Diesel Price | ${}/gallon | OPIS index (conservative) |
| Biochar Price | ${}/ton | Market survey |
| Power Price | ${}/kWh | Utility rate schedule |

### Assumption Sensitivity

Material adverse changes to these assumptions may affect:
- Debt service coverage ratios
- Revenue projections
- Project feasibility

Sensitivity analysis is provided in the Financial Tables section.
```

---

### 5.8 Mandatory Disclaimer

**Purpose:** Legal protection and professional boundary-setting

**Content:**

```markdown
## Important Notices and Disclaimer

─────────────────────────────────────────────────────────────────────────

**THIS DOCUMENT IS PRELIMINARY AND FOR DISCUSSION PURPOSES ONLY**

─────────────────────────────────────────────────────────────────────────

### Not an Offering

This Advisory Information Package does not constitute:
- An offer to sell or solicitation of an offer to buy any securities
- A commitment to proceed with the proposed financing
- Investment advice or a recommendation to purchase securities
- A substitute for independent professional advice

### No Reliance

Recipients should not rely on this document for:
- Investment decisions
- Legal, tax, or accounting advice
- Verification of facts or projections
- Assessment of creditworthiness

### Information Sources

Information in this package has been prepared from:
- Project documents provided by the sponsor
- Public sources believed to be reliable
- Preliminary analyses and projections

No representation is made as to the accuracy or completeness of any 
information contained herein. All facts, figures, and projections are 
subject to verification by qualified professionals.

### Forward-Looking Statements

This document contains forward-looking statements based on current 
expectations and assumptions. Actual results may differ materially due to:
- Market conditions
- Regulatory changes
- Technology performance
- Operational factors
- Economic conditions

### Professional Review Required

Before any financing transaction:
- Bond counsel must provide required legal opinions
- Financial advisor must validate financial projections
- Independent Engineer must certify project feasibility
- Rating agencies (if applicable) must complete credit analysis
- Underwriter must complete due diligence

### Document Validity

This document reflects information available as of {generated_date}. 
Material changes occurring after this date may require revision.

This package should be updated if:
- More than 90 days have elapsed since generation
- Significant facts have changed
- Advisors request updated information

─────────────────────────────────────────────────────────────────────────

**Prepared by:** {sponsor.name}

**Package Version:** {version}

**Generated:** {generated_date}

**BFMS Version:** {bfms_version}

─────────────────────────────────────────────────────────────────────────
```

---

## 6. GENERATION LOGIC

### 6.1 Package Assembly Pipeline

```python
def generate_external_package(project_id: UUID) -> ExternalAdvisoryPackage:
    # 1. Generate WP7 disclosure document
    disclosure = generate_disclosure_document(project_id)
    
    # 2. Get WP5 financial outputs
    financials = get_financial_model_outputs(project_id)
    
    # 3. Get SLB data (if enabled)
    slb_brief = generate_slb_brief(project_id) if slb_enabled(project_id) else None
    
    # 4. Filter assumptions to key items only
    key_assumptions = filter_key_assumptions(get_assumptions(project_id))
    
    # 5. Build deal overview (modified WP6)
    deal_overview = build_deal_overview(project_id)
    
    # 6. Assemble package
    package = ExternalAdvisoryPackage(
        project_id=project_id,
        version=increment_version(project_id),
        generated_at=now(),
        
        cover_page=build_cover_page(project_id),
        executive_summary=build_executive_summary(project_id, disclosure.tbd_items),
        deal_overview=deal_overview,
        disclosure_document=disclosure,
        financial_tables=financials,
        slb_brief=slb_brief,
        key_assumptions=key_assumptions,
        disclaimer=MANDATORY_DISCLAIMER
    )
    
    return package
```

### 6.2 TBD Handling for External Package

TBD markers from WP7 are included but summarized:

```python
def format_tbd_for_external(tbd_items: List[TBDMarker]) -> str:
    # Group by severity
    critical_high = [t for t in tbd_items if t.severity in ['critical', 'high']]
    
    if not critical_high:
        return "No material information gaps identified."
    
    return "The following items are in development:\n" + "\n".join(
        f"- {t.reason}" for t in critical_high
    )
```

---

## 7. OUTPUT FORMATS

### 7.1 Primary: PDF

Professional format for distribution; mandatory for external sharing.

### 7.2 Secondary: DOCX

Editable format for advisor comments and markup.

### 7.3 Tertiary: Markdown

Source format for version control.

---

## 8. API SURFACE

```
POST /projects/{id}/advisory-package/generate
GET /projects/{id}/advisory-package
GET /projects/{id}/advisory-package/export?format=pdf|docx|md
GET /projects/{id}/advisory-package/history
```

---

## 9. QUALITY GATES

Before external distribution, the package must pass:

| Gate | Requirement |
|------|-------------|
| Minimum Score | Readiness ≥ 5.0 (recommended) |
| Critical TBDs | ≤ 3 critical items pending |
| Financial Tables | All required tables populated |
| Disclaimer | Present and unmodified |
| Version | Package version ≥ 1.0 |

```python
def validate_for_distribution(package: ExternalAdvisoryPackage) -> ValidationResult:
    issues = []
    
    if package.disclosure_document.completeness_score < 0.5:
        issues.append("Disclosure completeness below 50%")
    
    critical_tbds = count_critical_tbds(package)
    if critical_tbds > 3:
        issues.append(f"Too many critical TBDs ({critical_tbds})")
    
    if not package.disclaimer:
        issues.append("Missing mandatory disclaimer")
    
    return ValidationResult(
        ready_for_distribution=len(issues) == 0,
        issues=issues
    )
```

---

## 10. DEFINITION OF DONE

External Advisory Package is complete when:

- [ ] All 8 sections generate correctly
- [ ] Disclosure document synthesized from WP7
- [ ] Financial tables populated from WP5
- [ ] No internal gap/checklist details exposed
- [ ] TBD markers present but not alarming
- [ ] Disclaimer is mandatory and uneditable
- [ ] PDF export is professional quality
- [ ] Municipal advisor can orient in <15 minutes
- [ ] Package passes quality gates

---

**END OF SPECIFICATION**
