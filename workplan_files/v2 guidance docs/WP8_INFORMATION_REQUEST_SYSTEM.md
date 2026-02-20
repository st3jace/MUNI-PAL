# WP8 — Information Request System

**Bond Facility Management System (BFMS)**

**Status:** FINAL (v1.0) | **Depends on:** WP1-WP4, Playbook v0.2+

---

## WP8 PURPOSE

WP8 transforms gap analysis from binary indicators ("missing/present") into **actionable information requests** that guide the team toward producing or procuring the specific evidence needed for bond readiness.

WP8 answers: **"What exactly do we need, why does it matter, and how do we get it?"**

It does NOT answer: "Is this good enough?" or "Should we proceed anyway?" — those remain human judgments.

---

## WP8 SCOPE (STRICT)

### In Scope

- Structured information request generation from gaps
- Bond-domain context for each requirement
- Guidance on acceptable evidence sources
- Examples of what "good" looks like
- Priority scoring and assignment logic
- Request lifecycle tracking (open → resolved)

### Out of Scope

- Automated evidence creation
- Quality assessment of submitted evidence
- Approval workflows
- External stakeholder communication
- Deadline enforcement

---

## 1. CORE PRINCIPLES (NON-NEGOTIABLE)

### 1.1 Actionable Specificity

Every information request must be specific enough that:
- The assigned person knows exactly what to produce
- Success criteria are clear
- The deliverable format is defined

**Prohibited:**
- Vague requests ("provide more financial information")
- Undefined success criteria ("ensure adequate documentation")
- Open-ended scopes ("gather all relevant permits")

### 1.2 Bond-Domain Context

Every request must explain:
- WHY this information matters for bond issuance
- WHO will consume this information (advisor, rating agency, investor)
- WHAT happens if it's not provided (blocked checklist, lower score, deal risk)

### 1.3 Guidance Over Judgment

Requests provide guidance on HOW to satisfy requirements, but do not judge the quality of responses. Quality assessment happens in the fact review workflow (WP3).

---

## 2. INFORMATION REQUEST DATA MODEL

### 2.1 Core Schema

```python
class InformationRequest:
    # Identity
    id: UUID
    project_id: UUID
    request_code: str  # e.g., "IR-P2.3-001"
    
    # What's Missing
    gap_id: UUID  # Link to WP4 gap record
    missing_fact_paths: List[str]  # Schema paths needed
    current_state: EvidenceState  # none | partial | conflicting | weak
    
    # Context
    title: str  # Human-readable request title
    bond_domain_context: BondDomainContext
    affected_items: AffectedItems
    
    # Guidance
    guidance: RequestGuidance
    examples: List[EvidenceExample]
    acceptable_sources: List[str]
    minimum_confidence: float
    expected_format: str
    
    # Assignment
    priority: Priority  # low | medium | high | critical
    suggested_owner: str
    suggested_deadline: Optional[date]
    
    # Lifecycle
    status: RequestStatus  # open | in_progress | submitted | resolved | deferred
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    resolution_notes: Optional[str]

class EvidenceState(Enum):
    NONE = "none"  # No evidence exists
    PARTIAL = "partial"  # Some evidence, incomplete
    CONFLICTING = "conflicting"  # Multiple contradictory facts
    WEAK = "weak"  # Evidence exists but low confidence

class Priority(Enum):
    LOW = "low"  # Nice to have, doesn't block progress
    MEDIUM = "medium"  # Material gap, should address before advisor engagement
    HIGH = "high"  # Critical path, blocks next phase
    CRITICAL = "critical"  # Deal-blocking, requires immediate escalation
```

### 2.2 Bond Domain Context

```python
class BondDomainContext:
    why_it_matters: str  # 2-3 sentences explaining bond relevance
    who_needs_it: List[str]  # e.g., ["Municipal Advisor", "Rating Agency"]
    when_needed: str  # e.g., "Before P3 close", "Prior to pricing"
    consequences: str  # What happens if not provided
    related_requirements: List[str]  # Other items this unlocks
    regulatory_reference: Optional[str]  # SEC, MSRB, ICMA reference if applicable
```

### 2.3 Request Guidance

```python
class RequestGuidance:
    overview: str  # What we're asking for
    specific_questions: List[str]  # Concrete questions to answer
    data_points_needed: List[str]  # Specific values required
    suggested_approach: str  # How to gather this
    common_pitfalls: List[str]  # What to avoid
    time_estimate: str  # Expected effort

class EvidenceExample:
    description: str  # What this example shows
    content_preview: str  # Excerpt or summary
    why_acceptable: str  # Why this meets the standard
    source_type: str  # e.g., "Feasibility Study", "LOI", "Engineering Report"
```

---

## 3. GAP-TO-REQUEST MAPPING

### 3.1 Mapping Logic

Each gap type maps to a request template:

```python
def generate_request(gap: GapRecord) -> InformationRequest:
    # Find applicable template
    template = find_template(gap.missing_fact_paths, gap.severity)
    
    # Populate template with gap specifics
    request = populate_template(template, gap)
    
    # Calculate priority
    request.priority = calculate_priority(gap)
    
    # Suggest owner based on fact domain
    request.suggested_owner = suggest_owner(gap.missing_fact_paths)
    
    return request
```

### 3.2 Priority Calculation

```python
def calculate_priority(gap: GapRecord) -> Priority:
    # Critical if blocks multiple high-weight dimensions
    if gap.severity == "critical" or len(gap.affected_dimensions) >= 3:
        return Priority.CRITICAL
    
    # High if blocks next phase
    if gap.blocks_phase_transition:
        return Priority.HIGH
    
    # Medium if affects readiness score by >0.5 points
    if gap.readiness_impact > 0.5:
        return Priority.MEDIUM
    
    return Priority.LOW
```

### 3.3 Owner Suggestion

```python
OWNER_MAP = {
    "parties.*": "Sponsor / Legal",
    "governance.*": "Sponsor / Legal",
    "technology.*": "Technology Provider / Engineering",
    "feedstock.*": "Operations / Sponsor",
    "revenue.*": "Finance / Sponsor",
    "finmodel.*": "Finance",
    "security.*": "Legal / Finance",
    "permitting.*": "Environmental Consultant / Operations",
    "slb.*": "Sustainability / ESG Advisor",
    "risk.*": "Risk Manager / Sponsor",
    "cab.*": "Finance / Advisor"
}

def suggest_owner(fact_paths: List[str]) -> str:
    # Find most common domain
    domains = [path.split('.')[0] for path in fact_paths]
    primary_domain = most_common(domains)
    
    for pattern, owner in OWNER_MAP.items():
        if matches(primary_domain, pattern):
            return owner
    
    return "Sponsor"
```

---

## 4. REQUEST TEMPLATES BY DOMAIN

### 4.1 Template: Issuer Authority (P1)

**Trigger:** Missing `governance.inducement` or `regulatory.tax-status`

```yaml
template_id: issuer_authority_001
title: "Inducement Resolution and Tax Status Confirmation"

bond_domain_context:
  why_it_matters: |
    Municipal bond issuance requires explicit legal authority from the issuing 
    entity. The inducement resolution formally authorizes the issuer to proceed 
    with bond financing for this specific project. Tax status determination 
    (tax-exempt vs. taxable) affects investor base, pricing, and disclosure 
    requirements. Without these, bond counsel cannot issue required opinions.
  
  who_needs_it:
    - Bond Counsel (for legal opinion)
    - Municipal Advisor (for structuring)
    - Underwriter (for pricing and marketing)
  
  when_needed: "Before Phase 1 close; required for advisor engagement"
  
  consequences: |
    Without inducement and tax status determination:
    - Cannot engage bond counsel for formal opinion
    - Cannot size or price the transaction
    - Advisor engagement limited to preliminary discussions only
    - Checklist items P1.1-P1.3 remain blocked
  
  regulatory_reference: "IRC §103 (tax exemption); State enabling statutes"

guidance:
  overview: |
    Obtain formal documentation of the issuer's authorization to proceed 
    with this bond financing and determination of tax status.
  
  specific_questions:
    - "Has the IDA governing body adopted an inducement resolution for this project?"
    - "If not adopted, what is the expected timeline for board consideration?"
    - "Has bond counsel provided preliminary guidance on tax-exempt eligibility?"
    - "What is the expected tax status (tax-exempt, taxable, or hybrid)?"
  
  data_points_needed:
    - Inducement resolution date and reference number
    - IDA board vote record
    - Bond counsel preliminary tax opinion or memo
    - Applicable statutory authority cited
  
  suggested_approach: |
    1. Request IDA staff to circulate draft inducement resolution
    2. Schedule board meeting for formal adoption
    3. Engage bond counsel for preliminary tax analysis
    4. Document governing body approval in meeting minutes
  
  common_pitfalls:
    - "Informal board discussion does not constitute inducement"
    - "Tax status cannot be assumed based on project type; counsel analysis required"
    - "IDA authority may be limited by volume cap allocation"
  
  time_estimate: "2-4 weeks for resolution adoption; 1-2 weeks for tax memo"

examples:
  - description: "Sample inducement resolution language"
    content_preview: |
      "WHEREAS, [Borrower] has requested assistance from the Authority in 
      financing a [project type] facility... NOW THEREFORE BE IT RESOLVED 
      that the Authority expresses its intent to issue revenue bonds..."
    why_acceptable: "Formal resolution with specific project identification and board approval"
    source_type: "Board Resolution"

acceptable_sources:
  - "Executed board resolution with meeting minutes"
  - "Bond counsel preliminary opinion letter"
  - "IDA staff confirmation with resolution reference"

minimum_confidence: 0.90
expected_format: "PDF of executed resolution; attorney memo"
priority: CRITICAL
suggested_owner: "Sponsor / Legal"
```

---

### 4.2 Template: Feedstock Supply (P2)

**Trigger:** Missing `feedstock.supply.mechanism` or `feedstock.supply.confidence`

```yaml
template_id: feedstock_supply_002
title: "Feedstock Supply Documentation and Confidence Assessment"

bond_domain_context:
  why_it_matters: |
    Revenue bonds are repaid from project cash flows. If feedstock supply is 
    uncertain, revenue projections become speculative and bondholders face 
    elevated risk. Rating agencies and investors scrutinize feedstock 
    arrangements as a primary credit driver. For waste-to-energy projects, 
    feedstock is the equivalent of "fuel supply" for a power plant.
  
  who_needs_it:
    - Independent Engineer (for feasibility validation)
    - Rating Agency (for credit assessment)
    - Underwriter (for investor marketing)
    - Bond Counsel (for disclosure review)
  
  when_needed: "Before Phase 2 close; material for financial model inputs"
  
  consequences: |
    Without documented feedstock supply:
    - Financial model revenue assumptions are unsupported
    - Independent Engineer cannot certify feasibility
    - Rating agencies will apply significant haircuts or decline to rate
    - DSCR projections lack credibility
    - Dimension 3 (Revenue & Operational Readiness) capped at 2.0/5.0

guidance:
  overview: |
    Document the arrangements by which the project will obtain sufficient 
    feedstock to operate at projected capacity, including volume commitments, 
    pricing (if applicable), and term.
  
  specific_questions:
    - "What entities will supply feedstock to the facility?"
    - "What is the committed annual volume (tons/year)?"
    - "What is the term of supply arrangements (years)?"
    - "Is feedstock provided at cost, free, or revenue-generating (tipping fees)?"
    - "What is the confidence level of supply (preliminary, advanced, secured)?"
  
  data_points_needed:
    - Supplier name(s)
    - Annual volume commitment (tons)
    - Contract term (years)
    - Pricing mechanism (tipping fee, cost pass-through, etc.)
    - Current status (LOI, MOU, executed agreement)
  
  suggested_approach: |
    1. Identify all potential feedstock sources (forestry, municipal, commercial)
    2. Obtain letters of intent (LOI) or memoranda of understanding (MOU)
    3. Progress LOIs to binding agreements where possible
    4. Document feedstock characterization (type, moisture content, contamination)
    5. Calculate annual availability vs. project requirements
  
  common_pitfalls:
    - "Verbal commitments without documentation are insufficient"
    - "LOIs must specify volume and term, not just 'willingness to discuss'"
    - "Feedstock availability studies ≠ supply commitments"
    - "Municipal waste streams may require procurement processes"
  
  time_estimate: "4-8 weeks for LOI execution; 3-6 months for binding agreements"

examples:
  - description: "Acceptable LOI language"
    content_preview: |
      "[Supplier] hereby confirms its intent to supply up to 25,000 tons per 
      year of forest biomass to [Project] for a minimum term of 10 years, 
      subject to execution of a definitive supply agreement..."
    why_acceptable: "Specifies volume, term, and path to binding commitment"
    source_type: "Letter of Intent"
  
  - description: "Feedstock characterization summary"
    content_preview: |
      "Feedstock assessment conducted across 5 representative sources indicates 
      average moisture content of 35%, BTU value of 4,500/lb, contamination 
      rate <2%, consistent with equipment specifications..."
    why_acceptable: "Technical validation of feedstock quality"
    source_type: "Feasibility Study"

acceptable_sources:
  - "Executed feedstock supply agreement"
  - "Letter of Intent with specific terms"
  - "Memorandum of Understanding with volume commitments"
  - "Feasibility study feedstock assessment section"
  - "Stewardship agreement with land manager"

minimum_confidence: 0.80
expected_format: "Executed LOI/MOU (PDF); supply assessment narrative"
priority: HIGH
suggested_owner: "Operations / Sponsor"
```

---

### 4.3 Template: Offtake/Revenue (P3)

**Trigger:** Missing `revenue.offtake.status` or insufficient `revenue.commodities.list`

```yaml
template_id: offtake_revenue_003
title: "Commodity Offtake Arrangements and Revenue Validation"

bond_domain_context:
  why_it_matters: |
    Bond repayment depends on the project's ability to convert commodities 
    into cash. Offtake agreements represent contracted revenue—the more 
    certain the offtake, the more reliable the debt service coverage. 
    Without documented offtake, revenue projections are market assumptions, 
    not contractual commitments.
  
  who_needs_it:
    - Financial Advisor (for sizing and structuring)
    - Independent Engineer (for revenue validation)
    - Rating Agency (for credit assessment)
    - Investors (for underwriting decision)
  
  when_needed: "Before Phase 3 close; required for financial model finalization"
  
  consequences: |
    Without documented offtake:
    - Revenue model relies entirely on market assumptions
    - DSCR coverage is speculative
    - Rating agencies will apply 20-40% revenue haircuts
    - Investor appetite limited to higher-risk buyers
    - Checklist item P3.4 remains blocked

guidance:
  overview: |
    Document the arrangements for selling each commodity product, including 
    counterparty, volume, pricing, and term. Focus on the top 2-3 revenue 
    drivers (typically renewable diesel and biochar for UCS projects).
  
  specific_questions:
    - "Who are the expected purchasers of each commodity output?"
    - "What volume commitments exist (gallons, tons, MWh per year)?"
    - "What pricing mechanisms apply (fixed, indexed, market)?"
    - "What is the term of offtake arrangements?"
    - "What is the current status (negotiating, LOI, executed)?"
  
  data_points_needed:
    - Counterparty name per commodity
    - Annual volume commitment
    - Pricing mechanism and illustrative pricing
    - Contract term (years)
    - Status (LOI, MOU, executed agreement)
    - Creditworthiness of counterparty
  
  suggested_approach: |
    1. Identify target offtakers by commodity type
    2. Execute LOIs with minimum 2 creditworthy counterparties
    3. Document pricing basis (index, negotiated, regulatory)
    4. Progress LOIs toward binding agreements during P3-P4
    5. Obtain counterparty credit information
  
  common_pitfalls:
    - "Market studies ≠ offtake commitments"
    - "LOIs without pricing mechanisms have limited value"
    - "Small or non-creditworthy counterparties require credit support"
    - "Volume must align with production projections"

examples:
  - description: "Renewable diesel offtake LOI"
    content_preview: |
      "[Fuel distributor] agrees to purchase up to 2.0 million gallons per 
      year of renewable diesel at OPIS-indexed pricing less $0.15/gallon 
      for logistics, for a term of 7 years..."
    why_acceptable: "Specific volume, pricing mechanism, and term"
    source_type: "Letter of Intent"

acceptable_sources:
  - "Executed offtake agreement"
  - "Letter of Intent with volume and pricing terms"
  - "MOU with creditworthy counterparty"
  - "Regulated rate schedule (for power sales)"

minimum_confidence: 0.80
expected_format: "Executed LOI (PDF); counterparty credit summary"
priority: HIGH
suggested_owner: "Sponsor / Business Development"
```

---

### 4.4 Template: SLB Verification (P5)

**Trigger:** Missing `slb.kpi.{n}.verification.method`

```yaml
template_id: slb_verification_004
title: "SLB KPI Verification Methodology and Third-Party Verifier"

bond_domain_context:
  why_it_matters: |
    Sustainability-linked bonds lose credibility without independent 
    verification. The 2024 World Bank study found 77% of SLBs have weak 
    verification, enabling issuers to claim greenium without accountability. 
    Credible SLB structures require: (1) measurable KPIs, (2) conservative 
    baselines, (3) external verification, and (4) meaningful penalties. 
    Without verification methodology, SLB features are marketing—not structure.
  
  who_needs_it:
    - Second-Party Opinion Provider (for SLB framework assessment)
    - ESG Investors (for greenwashing due diligence)
    - Rating Agency (if ESG rating sought)
    - Bond Counsel (for disclosure of verification procedures)
  
  when_needed: "Before Phase 5 close; required for SLB framework finalization"
  
  consequences: |
    Without verification methodology:
    - Second-party opinion provider cannot opine on framework credibility
    - ESG-focused investors will decline or discount
    - SLB greenium (25-40 bps) is lost
    - Reputational risk if targets later disputed
    - Checklist item P5.4 remains blocked

guidance:
  overview: |
    Define how each selected KPI will be measured, reported, and independently 
    verified. Identify the third-party verifier and establish verification 
    protocol.
  
  specific_questions:
    - "What data sources will measure each KPI?"
    - "How frequently will data be collected and reported?"
    - "Who will serve as the independent third-party verifier?"
    - "What verification standard will apply (ISAE 3000, ISO 14064, etc.)?"
    - "What is the timeline for annual verification reports?"
  
  data_points_needed:
    - KPI measurement methodology (data sources, calculation)
    - Reporting frequency and responsible party
    - Third-party verifier name and qualifications
    - Verification standard reference
    - Verification report timeline
    - Cost estimate for verification services
  
  suggested_approach: |
    1. Document data collection procedures for each KPI
    2. Identify qualified third-party verifiers (ESG firms, accounting firms)
    3. Request proposals from 2-3 verifiers
    4. Select verifier and execute engagement letter
    5. Document verification protocol in SLB framework
  
  common_pitfalls:
    - "Self-reported data without third-party review is insufficient"
    - "Verifier must be independent of project sponsor"
    - "Verification must occur BEFORE step-up trigger dates"
    - "Verification costs must be budgeted in O&M"

examples:
  - description: "Verification methodology for waste diversion KPI"
    content_preview: |
      "Waste diversion rate calculated as: (scale ticket weight IN - residual 
      waste OUT) / scale ticket weight IN. Data source: facility scale tickets 
      with IoT integration. Verification: Annual ISAE 3000 limited assurance 
      engagement by [Verifier Name]..."
    why_acceptable: "Specific calculation, data source, and verification standard"
    source_type: "SLB Framework"

acceptable_sources:
  - "SLB Framework document with verification section"
  - "Third-party verifier engagement letter"
  - "Verification protocol specification"
  - "Data management system documentation"

minimum_confidence: 0.85
expected_format: "SLB Framework section (PDF); verifier engagement letter"
priority: HIGH
suggested_owner: "Sustainability / ESG Advisor"
```

---

## 5. REQUEST LIFECYCLE MANAGEMENT

### 5.1 Status Transitions

```
OPEN → IN_PROGRESS → SUBMITTED → RESOLVED
                  ↘ DEFERRED (with reason)
```

### 5.2 Lifecycle Rules

| Transition | Trigger | Action |
|---|---|---|
| OPEN → IN_PROGRESS | Owner acknowledges request | Record start date |
| IN_PROGRESS → SUBMITTED | Evidence uploaded | Link to artifact; await review |
| SUBMITTED → RESOLVED | Fact(s) accepted via WP3 | Record resolution; update gap status |
| SUBMITTED → IN_PROGRESS | Fact(s) rejected/edited | Return for additional work |
| * → DEFERRED | Explicit deferral decision | Record reason; set review date |

### 5.3 Stale Request Handling

Requests open >14 days without progress:
- Auto-escalate priority one level
- Notify suggested owner and project lead
- Flag in Internal Readiness Report

---

## 6. API SURFACE (WP8)

### 6.1 Endpoints

**Generate Requests:**
```
POST /projects/{id}/information-requests/generate
Response: List[InformationRequest]
```

**List Requests:**
```
GET /projects/{id}/information-requests?status=open&priority=high
Response: List[InformationRequest]
```

**Get Request Detail:**
```
GET /information-requests/{request_id}
Response: InformationRequest (full detail)
```

**Update Request Status:**
```
PATCH /information-requests/{request_id}
Body: { status: "in_progress", notes: "..." }
Response: InformationRequest
```

**Link Evidence:**
```
POST /information-requests/{request_id}/evidence
Body: { artifact_id: UUID, notes: "..." }
Response: Updated request with linked evidence
```

---

## 7. EXPLICIT NON-GOALS (WP8)

Bots must **not**:

- Auto-resolve requests without human review
- Generate evidence content
- Assess quality of submitted evidence
- Enforce deadlines
- Send external communications
- Override priority assignments without human input

---

## 8. DEFINITION OF DONE (WP8)

WP8 is complete when:

- [ ] All gap types produce structured requests
- [ ] Bond domain context is populated for all critical gaps
- [ ] Guidance includes specific questions and examples
- [ ] Priority calculation aligns with readiness impact
- [ ] Owner suggestions map to appropriate roles
- [ ] Lifecycle tracking works end-to-end
- [ ] Internal Report includes actionable request list
- [ ] Team reports requests are "actionable" in user testing

---

## 9. INTEGRATION POINTS

### 9.1 WP4 (Gap Analysis) → WP8 (Requests)

```python
# After gap analysis completes
for gap in gaps:
    request = generate_information_request(gap)
    save_request(request)
```

### 9.2 WP8 (Requests) → WP3 (Fact Review)

```python
# When evidence is submitted for a request
artifact = upload_artifact(file, request_id)
# Trigger extraction
job = create_extraction_job(artifact)
# On fact acceptance, resolve request
if all_required_facts_accepted(request):
    resolve_request(request)
```

### 9.3 WP8 → Internal Readiness Report

```python
# Include in report generation
report.information_requests = get_open_requests(project_id)
report.request_summary = summarize_by_priority(requests)
```

---

**END OF WP8**
