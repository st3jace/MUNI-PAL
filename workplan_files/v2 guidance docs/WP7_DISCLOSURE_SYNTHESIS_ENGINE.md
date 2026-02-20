# WP7 — Disclosure Synthesis Engine

**Bond Facility Management System (BFMS)**

**Status:** FINAL (v1.0) | **Depends on:** WP1-WP5, Playbook v0.2+

---

## WP7 PURPOSE

WP7 transforms the skeletal "Disclosure Outline" into a **substantive disclosure document** by synthesizing extracted facts into coherent, disclosure-ready prose. This is the primary external deliverable for municipal advisory engagement.

WP7 answers: **"What can we defensibly say to sophisticated bond professionals based on our evidence?"**

It does NOT answer: "What should we say?" or "Is this disclosure complete?" — those remain advisor judgments.

---

## WP7 SCOPE (STRICT)

### In Scope

- Template-driven prose synthesis from accepted ExtractedFacts
- Section-by-section disclosure document generation
- TBD marker insertion for insufficient evidence
- Confidence scoring per section
- Fact linkage and provenance preservation
- Professional, neutral language generation

### Out of Scope

- Generative AI content creation (all content derives from templates + facts)
- Legal opinion or compliance assessment
- Investment recommendations
- Completeness certification
- Replacement for bond counsel review

---

## 1. CORE PRINCIPLES (NON-NEGOTIABLE)

### 1.1 Evidence-Only Synthesis

Every sentence in the disclosure document must satisfy one of:

1. **Fact-derived**: Maps directly to one or more accepted ExtractedFacts
2. **Templated qualifier**: Standard language that frames facts (e.g., "Based on the feasibility study...")
3. **TBD marker**: Explicit acknowledgment of missing information

**Prohibited:**
- Invented claims not traceable to facts
- Promotional adjectives ("excellent," "industry-leading," "proven")
- Forward-looking statements without qualification
- Opinions or recommendations

### 1.2 Conditional Language

All synthesis uses conditional/qualified language:

| Instead of... | Use... |
|---|---|
| "The project will generate $10M" | "Based on feasibility study projections, annual revenue is estimated at $10M" |
| "The technology is proven" | "The technology has operated at pilot scale for [X] months" |
| "Risk is minimal" | "The following risk factors have been identified and mitigants documented" |

### 1.3 Transparency About Gaps

When evidence is insufficient for a section:

- Insert `[TBD: {reason}]` marker in prose
- Track marker in `tbd_items` array
- Do NOT generate placeholder content that implies existence of evidence

---

## 2. DISCLOSURE DOCUMENT STRUCTURE

### 2.1 Section Hierarchy

```
DisclosureDocument
├── Introduction and Summary
├── The Issuer
├── The Project
│   ├── Technology Description
│   ├── Operating Plan
│   ├── Construction Timeline
│   └── Permitting Status
├── Security and Sources of Payment
│   ├── Revenue Pledge
│   ├── Collateral Package
│   └── Reserve Requirements
├── Financial Information
│   ├── Pro Forma Projections
│   ├── DSCR Analysis
│   └── Sensitivity Analysis
├── Risk Factors
│   ├── Technology Risk
│   ├── Construction Risk
│   ├── Market/Offtake Risk
│   ├── Regulatory Risk
│   └── Environmental Risk
└── Sustainability-Linked Features (if SLB enabled)
    ├── KPI Descriptions
    ├── SPT Targets
    ├── Verification Procedures
    └── Step-up/Step-down Mechanics
```

### 2.2 Section Configuration

Each section is defined by:

```python
class DisclosureSectionConfig:
    section_id: str
    title: str
    required_fact_paths: List[str]  # Must have these for meaningful content
    optional_fact_paths: List[str]  # Enhance if present
    minimum_confidence: float  # Threshold for inclusion
    template_key: str  # Reference to synthesis template
    subsections: List[DisclosureSectionConfig]  # Nested sections
    conditional_on: Optional[str]  # e.g., "slb.enabled == True"
```

---

## 3. SYNTHESIS TEMPLATES

### 3.1 Template Structure

Each template is a structured pattern that combines:
- **Static prose**: Framing language that doesn't change
- **Fact slots**: Placeholders filled from ExtractedFacts
- **Conditional blocks**: Content included only if facts exist
- **TBD fallbacks**: Markers inserted when facts are missing

### 3.2 Example: Introduction and Summary

```yaml
template_id: introduction_summary
required_facts:
  - project.canonicaldescription
  - parties.issuer.name
  - capital.project-cost
  - security.revenue.pledge
  
template: |
  ## Introduction and Summary
  
  This document provides preliminary disclosure information for a proposed 
  revenue bond issuance by {parties.issuer.name:TBD: Issuer not specified}.
  
  **Project Overview**
  
  {project.canonicaldescription:TBD: Project description pending}
  
  **Transaction Summary**
  
  The proposed financing contemplates {IF cab.enabled}Capital Appreciation Bonds 
  with an accretion rate of {cab.accretionrate}%{ENDIF}{IF slb.enabled} incorporating 
  Sustainability-Linked Bond features{ENDIF}.
  
  - **Total Project Cost:** ${capital.project-cost:formatted:TBD}
  - **Proposed Bond Amount:** ${cab.originalprincipial:formatted:TBD}
  - **Security:** Gross revenue pledge{IF security.revenue.pledge} of 
    ${security.revenue.pledge:formatted}{ENDIF}
  
  {IF capital.equity-percent}
  Equity contribution of {capital.equity-percent:percent}% 
  (${capital.equity-contribution:formatted}) has been {IF equity.status == 'committed'}
  committed{ELSE}identified{ENDIF}.
  {ENDIF}
```

### 3.3 Fact Slot Syntax

```
{schema_path}                    — Direct value insertion
{schema_path:formatted}          — Apply formatting (currency, percent, etc.)
{schema_path:TBD}               — Insert TBD marker if missing
{schema_path:TBD: reason}       — Insert TBD with specific reason
{IF condition}...{ENDIF}        — Conditional inclusion
{IF condition}...{ELSE}...{ENDIF} — Conditional with alternative
```

---

## 4. SECTION SYNTHESIS SPECIFICATIONS

### 4.1 Section 1: Introduction and Summary

**Purpose:** Provide quick orientation for bond professionals

**Required Facts:**
- `project.canonicaldescription`
- `parties.issuer.name`
- `parties.borrower.name` (optional)
- `capital.project-cost`
- `cab.enabled`
- `slb.enabled`
- `security.revenue.pledge`

**Synthesis Rules:**
1. Lead with issuer and project description
2. State bond structure type (CAB, SLB, or both)
3. Include high-level financials (cost, bond amount, equity)
4. Reference security structure
5. Note any key distinguishing features

**Confidence Threshold:** 0.70 (can generate with partial info)

---

### 4.2 Section 2: The Issuer

**Purpose:** Establish legal authority and governance

**Required Facts:**
- `parties.issuer.name`
- `parties.issuer.jurisdiction`
- `governance.inducement`
- `regulatory.tax-status`

**Synthesis Rules:**
1. Name issuer and legal form (IDA, municipal authority, etc.)
2. State jurisdiction and enabling authority
3. Note inducement status (draft, proposed, adopted)
4. State tax status determination (tax-exempt, taxable, pending)
5. Reference governance approvals

**Confidence Threshold:** 0.80 (legal matters require higher confidence)

**Template Fragment:**
```
## The Issuer

The bonds are expected to be issued by {parties.issuer.name}, an industrial 
development authority organized under the laws of {parties.issuer.jurisdiction:TBD: 
Jurisdiction pending}.

**Legal Authority**

{IF governance.inducement == 'adopted'}
An inducement resolution has been adopted by the issuer's governing body.
{ELSEIF governance.inducement == 'proposed'}
An inducement resolution has been proposed and is pending adoption.
{ELSE}
[TBD: Inducement resolution status to be confirmed]
{ENDIF}

**Tax Status**

{IF regulatory.tax-status}
The bonds are expected to be {regulatory.tax-status}. {IF regulatory.tax-status 
== 'tax-exempt'}Tax exemption is subject to receipt of an unqualified opinion 
from bond counsel.{ENDIF}
{ELSE}
[TBD: Tax status determination pending bond counsel analysis]
{ENDIF}
```

---

### 4.3 Section 3: The Project

**Purpose:** Describe technology, operations, and development status

#### 4.3.1 Technology Description

**Required Facts:**
- `technology.type`
- `technology.throughput.nameplate`
- `technology.throughput.annual`
- `technology.lifespan`
- `technology.warranty.duration`

**Synthesis Rules:**
1. Name technology type with technical accuracy
2. State throughput capacity (daily, annual)
3. Reference useful life and warranty coverage
4. Describe modular/scalable characteristics if applicable
5. Note any technology certifications or validations

**Template Fragment:**
```
### Technology Description

The project utilizes {technology.type:TBD: Technology type not specified} 
technology with a nameplate capacity of {technology.throughput.nameplate:TBD} 
tons per day, translating to an annual throughput of approximately 
{technology.throughput.annual:TBD} tons per year.

The technology has an expected useful life of {technology.lifespan:20} years, 
supported by manufacturer warranty coverage of {technology.warranty.duration:TBD} 
years.

{IF technology.type == 'Ultimate Conversion System (UCS)'}
The Ultimate Conversion System employs electromagnetic arc decomposition to 
convert organic feedstock into multiple commodity outputs including renewable 
diesel, biochar, and renewable electricity. The system is designed as modular, 
containerized units enabling deployment flexibility and scalability.
{ENDIF}
```

#### 4.3.2 Operating Plan

**Required Facts:**
- `project.operatingstatus`
- `operations.staffing.direct`
- `operations.maintenance.annual`
- `feedstock.volume.annual`
- `feedstock.type`

**Synthesis Rules:**
1. State current operating status
2. Describe feedstock supply arrangements
3. Note staffing requirements
4. Reference maintenance regime

#### 4.3.3 Construction Timeline

**Required Facts:**
- `project.construction.start`
- `project.construction.completion`
- `project.commercial.operation.date`

**Note:** If facts missing, insert TBD with note that timeline is subject to development.

#### 4.3.4 Permitting Status

**Required Facts:**
- `permitting.air-quality.status`
- `permitting.solidwaste.status`
- `permitting.environmental.status`

**Synthesis Rules:**
1. List permits obtained with issuing authority
2. Note permits pending with expected timeline
3. Reference any regulatory exemptions
4. State CEQA/NEPA status if applicable

---

### 4.4 Section 4: Security and Sources of Payment

**Purpose:** Detail bondholder protections

**Required Facts:**
- `security.revenue.pledge`
- `security.equipment.schedule`
- `security.realproperty`
- `capital.debt-requirement`

**Synthesis Rules:**
1. Describe revenue pledge (gross vs. net)
2. Detail collateral package (equipment liens, real property)
3. Note UCC filing status
4. Reference reserve fund requirements
5. Describe flow of funds (waterfall)

**Template Fragment:**
```
## Security and Sources of Payment

### Revenue Pledge

The bonds are secured by a {IF security.pledge.type == 'gross'}gross{ELSE}net{ENDIF} 
revenue pledge. {IF security.revenue.pledge}Based on current projections, pledged 
revenues are estimated at ${security.revenue.pledge:formatted} annually.{ENDIF}

### Collateral Package

{IF security.equipment.schedule}
The bonds are further secured by a first-priority security interest in all 
project equipment pursuant to a UCC-1 financing statement.
{ELSE}
[TBD: Equipment security arrangements to be documented]
{ENDIF}

{IF security.realproperty}
{security.realproperty}
{ENDIF}

### Reserve Requirements

[TBD: Debt service reserve fund requirements to be determined in consultation 
with bond counsel and underwriter]
```

---

### 4.5 Section 5: Financial Information

**Purpose:** Present pro forma projections and coverage metrics

**Required Facts:**
- `revenue.gross.annual`
- `opex.total.annual`
- `finmodel.outputs.dscrbase`
- `finmodel.outputs.dscrstress`
- `finmodel.inputs.dscr.minimum`

**Synthesis Rules:**
1. Present revenue projections with conservative basis noted
2. Show operating expense summary
3. Calculate and present DSCR (base and stress cases)
4. Reference sensitivity analysis
5. Note all figures are projections subject to advisor verification

**Critical:** All financial figures must include disclaimer that they are preliminary and subject to independent verification.

---

### 4.6 Section 6: Risk Factors

**Purpose:** Disclose material risks and mitigants

**Required Facts:**
- `risk.register[]` (array of identified risks)

**Synthesis Rules:**
1. Group risks by category (technology, construction, market, regulatory, environmental)
2. For each risk: state the risk, describe potential impact, note mitigant
3. Use factual language, not minimizing language
4. Reference supporting documentation where available

**Template Pattern:**
```
### {Risk Category} Risk

**{Risk Title}**

{Risk description from risk.register entry}

*Potential Impact:* {Impact description}

*Mitigant:* {Mitigant description if available, else [TBD: Mitigant to be documented]}
```

---

### 4.7 Section 7: Sustainability-Linked Features

**Conditional:** Only generated if `slb.enabled == True`

**Required Facts:**
- `slb.kpis.shortlist`
- `slb.kpi.{n}.name`
- `slb.kpi.{n}.baseline.value`
- `slb.kpi.{n}.baseline.methodology`
- `slb.penalty.stepup.magnitude`
- `slb.penalty.observation.dates`

**Synthesis Rules:**
1. Introduce SLB framework and alignment with ICMA principles
2. List selected KPIs with definitions
3. State baseline values and methodology
4. Describe SPT targets (if defined)
5. Note verification procedures
6. Describe step-up/step-down mechanics

**Template Fragment:**
```
## Sustainability-Linked Features

This bond issuance incorporates Sustainability-Linked Bond (SLB) features 
aligned with the International Capital Market Association (ICMA) Sustainability-Linked 
Bond Principles (2023).

### Key Performance Indicators

The following KPIs have been selected to measure sustainability performance:

{FOR kpi IN slb.kpis.shortlist}
**{kpi.name}**
- Baseline Value: {kpi.baseline.value:TBD}
- Measurement Methodology: {kpi.baseline.methodology:TBD: Methodology pending}
- Verification: {kpi.verification.method:TBD: Verification method to be established}
{ENDFOR}

### Economic Linkage

{IF slb.penalty.stepup.magnitude}
Failure to meet Sustainability Performance Targets will result in a coupon 
step-up of {slb.penalty.stepup.magnitude} basis points, effective following 
each observation date.
{ELSE}
[TBD: Step-up magnitude to be determined]
{ENDIF}

Observation dates are scheduled for {slb.penalty.observation.dates:TBD: Years 3, 6, and 9 
(subject to confirmation)}.
```

---

## 5. SYNTHESIS ENGINE IMPLEMENTATION

### 5.1 Processing Pipeline

```
1. Load section configurations from playbook
2. For each section:
   a. Retrieve required facts from accepted ExtractedFacts
   b. Check confidence thresholds
   c. Evaluate conditional blocks
   d. Fill fact slots (or insert TBD markers)
   e. Generate prose content
   f. Record supporting fact IDs
   g. Calculate section confidence score
3. Assemble complete document
4. Generate TBD summary
5. Calculate overall completeness score
```

### 5.2 Confidence Calculation

**Section Confidence:**
```
section_confidence = (
    count(facts_present) / count(required_facts) * 0.7 +
    average(fact_confidences) * 0.3
)
```

**Document Completeness:**
```
completeness = (
    sum(section_confidence * section_weight) / sum(section_weights)
)
```

### 5.3 TBD Marker Generation

When a required fact is missing:

```python
def generate_tbd_marker(fact_path: str, section: str) -> TBDMarker:
    return TBDMarker(
        location=f"{section}",
        missing_fact_paths=[fact_path],
        reason=get_reason_for_missing(fact_path),
        severity=get_severity_for_fact(fact_path)
    )

def get_reason_for_missing(fact_path: str) -> str:
    # Map fact paths to human-readable reasons
    reasons = {
        "governance.inducement": "Inducement resolution status not yet confirmed",
        "regulatory.tax-status": "Tax status determination pending bond counsel analysis",
        "slb.kpi.1.verification.method": "Third-party verification method not yet established",
        # ... comprehensive mapping
    }
    return reasons.get(fact_path, f"Information for {fact_path} not yet available")
```

---

## 6. API SURFACE (WP7)

### 6.1 Endpoints

**Generate Disclosure Document:**
```
POST /projects/{id}/disclosure/generate
Response: DisclosureDocument
```

**Get Disclosure Document:**
```
GET /projects/{id}/disclosure
Response: DisclosureDocument (latest version)
```

**Get Section Preview:**
```
GET /projects/{id}/disclosure/sections/{section_id}/preview
Response: DisclosureSectionPreview
```

**Export Disclosure:**
```
GET /projects/{id}/disclosure/export?format=md|pdf|docx
Response: File download
```

---

## 7. EXPLICIT NON-GOALS (WP7)

Bots must **not**:

- Generate content not traceable to ExtractedFacts
- Use generative AI for prose creation
- Certify completeness or sufficiency
- Provide legal opinions
- Make investment recommendations
- Minimize or hide gaps
- Use promotional language

---

## 8. DEFINITION OF DONE (WP7)

WP7 is complete when:

- [ ] All 7 disclosure sections have synthesis templates defined
- [ ] Templates populate correctly from accepted facts
- [ ] TBD markers insert appropriately for missing facts
- [ ] Confidence scores calculate correctly
- [ ] Every sentence in output traces to fact(s) or template
- [ ] Export produces professional-quality documents
- [ ] Municipal advisor can read disclosure in 10-15 minutes
- [ ] No promotional or forward-looking language without qualification

---

## 9. INTEGRATION WITH WP6

WP7 outputs feed into the **External Advisory Package** (modified WP6):

```
ExternalAdvisoryPackage
├── CoverPage
├── DealOverviewMemo (existing WP6)
├── DisclosureDocument ← WP7 OUTPUT
├── FinancialModelOutputs (existing WP5/WP6)
├── SLBKPIBrief (existing WP6)
├── KeyAssumptions (filtered from WP5)
└── Disclaimer
```

---

**END OF WP7**
