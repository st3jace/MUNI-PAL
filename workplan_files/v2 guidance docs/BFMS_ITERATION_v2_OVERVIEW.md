# BFMS Iteration v2.0 — Strategic Implementation Guide

**Status:** Implementation Ready | **Version:** 2.0 | **Created:** 2026-01-31
**Purpose:** Guide Claude Code through structural improvements to the Bond Facility Management System

---

## 1. EXECUTIVE SUMMARY

### 1.1 What This Document Is

This guide directs the next iteration of the Bond Facility Management System (BFMS) focused on three transformational improvements:

1. **Bifurcated Deliverables** — Split the current monolithic handoff pack into:
   - **Internal Readiness Report** (for sponsor team use)
   - **External Advisory Package** (for municipal advisor consumption)

2. **Disclosure Synthesis Engine** — Transform the skeletal "Disclosure Outline" into a substantive, populated document that synthesizes extracted facts into disclosure-ready prose

3. **Information Request System** — Generate structured prompts that guide the team toward producing/procuring missing information with context on why it matters

### 1.2 Why These Changes Matter

The current handoff pack conflates internal project management (checklist status, evidence index, gap tracking) with external professional communication (disclosure outline, deal overview). Municipal advisors don't need to see our internal gap analysis — they need a clean, professional package that demonstrates we've done our homework and are ready for sophisticated engagement.

Meanwhile, the Disclosure Outline at the end of the current pack is actually the most valuable deliverable for external consumption, but it's currently just headings. The system should synthesize actual content from extracted facts.

### 1.3 Architectural Philosophy

These changes extend (not replace) WP1-WP6. They introduce:

- **WP7** — Disclosure Synthesis Engine
- **WP8** — Information Request System  
- **Modified WP6** — Bifurcated pack assembly

The core principle remains: **evidence-first, human-reviewed, no hallucination**.

---

## 2. CURRENT STATE ANALYSIS

### 2.1 What Works Well (Preserve)

- ExtractedFact → Evidence linkage architecture
- Schema-driven extraction with playbook constraints
- Deterministic readiness scoring
- Checklist phase logic (P1-P6)
- Provenance preservation

### 2.2 What Needs Improvement

| Current Limitation | Impact | Target State |
|---|---|---|
| Single handoff pack serves two audiences | Advisors see internal gap tracking; sponsors see disclosure skeleton | Separate Internal Report and External Package |
| Disclosure Outline is headings-only | No synthesized content for advisors to react to | Populated prose sections from extracted facts |
| Gap analysis is binary (missing/present) | Team doesn't know HOW to fill gaps | Structured prompts with context, examples, guidance |
| Readiness explanations are generic | Team doesn't understand WHY requirements exist | Bond-domain explanations per requirement |

### 2.3 Handoff Pack Section Disposition

| Current Section | Destination | Rationale |
|---|---|---|
| Readiness Summary | Internal Report | Operational metric, not advisor content |
| Deal Overview Memo | External Package | Advisor-oriented orientation |
| Checklist Status | Internal Report | Project management, not disclosure |
| Evidence Index | Internal Report | Audit trail, not advisor content |
| Assumption Register | Both (modified) | Internal: full detail; External: key assumptions only |
| Financial Model Outputs | External Package | Advisor-grade tables |
| SLB KPI Brief | External Package | Disclosure-relevant |
| Disclosure Outline | External Package (enhanced) | Transform to synthesized content |

---

## 3. IMPLEMENTATION PRIORITIES

### 3.1 Phase 1: Bifurcate Deliverables (Week 1-2)

**Objective:** Create two distinct output paths from the same underlying data

**Tasks:**
1. Define `InternalReadinessReport` data structure
2. Define `ExternalAdvisoryPackage` data structure
3. Modify WP6 pack assembly to generate both
4. Create separate export endpoints

**Success Criteria:**
- Internal Report contains all operational/gap content
- External Package contains only advisor-ready content
- Same underlying facts feed both outputs
- Advisor can consume External Package without seeing internal gaps

### 3.2 Phase 2: Disclosure Synthesis Engine (Week 2-4)

**Objective:** Generate actual prose content for disclosure sections from extracted facts

**Tasks:**
1. Define disclosure section templates with fact-to-prose mappings
2. Implement synthesis logic per section (rules-based, not generative AI)
3. Create confidence thresholds for inclusion
4. Generate placeholder language for insufficient evidence

**Success Criteria:**
- Each disclosure section populated with defensible prose
- Every sentence traces to an ExtractedFact
- Missing information flagged with "[TBD: reason]" markers
- No invented claims; no promotional language

### 3.3 Phase 3: Information Request System (Week 3-5)

**Objective:** Generate actionable prompts that help the team fill gaps

**Tasks:**
1. Define `InformationRequest` data structure
2. Map gaps to request templates
3. Include: what's missing, why it matters, how to obtain it, examples
4. Create priority scoring and assignment logic

**Success Criteria:**
- Every gap produces a structured request
- Requests are assignable to team members
- Context explains bond-domain significance
- Examples show what "good" looks like

### 3.4 Phase 4: Enhanced Readiness Explanations (Week 4-5)

**Objective:** Provide bond-domain context for every readiness requirement

**Tasks:**
1. Extend ReadinessDimension with explanation templates
2. Create "Why It Matters" narratives per checklist item
3. Link requirements to bond issuance process gates
4. Show consequences of gaps

**Success Criteria:**
- Team understands WHY each requirement exists
- Explanations reference real bond market practices
- Consequences are specific (e.g., "rating agencies require this")

---

## 4. DATA CONTRACTS (NEW/MODIFIED)

### 4.1 New: InternalReadinessReport

```python
class InternalReadinessReport:
    id: UUID
    project_id: UUID
    version: int
    generated_at: datetime
    
    # Operational Sections
    readiness_summary: ReadinessSummary
    dimension_scores: List[DimensionScore]
    checklist_status: List[PhaseStatus]
    evidence_index: List[EvidenceEntry]
    gap_analysis: List[GapRecord]
    information_requests: List[InformationRequest]
    assumption_register: List[Assumption]  # Full detail
    
    # Metadata
    playbook_version: str
    bfms_version: str
```

### 4.2 New: ExternalAdvisoryPackage

```python
class ExternalAdvisoryPackage:
    id: UUID
    project_id: UUID
    version: int
    generated_at: datetime
    
    # Advisor-Facing Sections
    cover_page: CoverPage
    deal_overview: DealOverviewMemo
    disclosure_document: DisclosureDocument  # NEW: synthesized content
    financial_tables: FinancialModelOutputs
    slb_brief: SLBKPIBrief
    key_assumptions: List[Assumption]  # Filtered subset
    
    # Metadata
    disclaimer: str  # Mandatory legal disclaimer
    playbook_version: str
```

### 4.3 New: DisclosureDocument

```python
class DisclosureDocument:
    id: UUID
    sections: List[DisclosureSection]
    completeness_score: float  # 0.0-1.0
    tbd_items: List[TBDMarker]

class DisclosureSection:
    section_id: str  # e.g., "issuer", "project", "security"
    title: str
    content_md: str  # Synthesized prose
    supporting_facts: List[UUID]  # ExtractedFact IDs
    confidence: float
    tbd_markers: List[TBDMarker]

class TBDMarker:
    location: str
    missing_fact_paths: List[str]
    reason: str
    severity: str  # low | medium | high | critical
```

### 4.4 New: InformationRequest

```python
class InformationRequest:
    id: UUID
    project_id: UUID
    
    # What's Missing
    gap_id: UUID
    missing_fact_paths: List[str]
    current_evidence_state: str  # none | partial | conflicting
    
    # Why It Matters
    bond_domain_context: str
    affected_checklist_items: List[str]
    affected_dimensions: List[str]
    consequences_if_unfilled: str
    
    # How to Fill It
    guidance: str
    examples: List[str]
    acceptable_sources: List[str]
    minimum_confidence_required: float
    
    # Assignment
    priority: str  # low | medium | high | critical
    suggested_owner: str
    target_date: Optional[date]
    status: str  # open | in_progress | resolved | deferred
```

---

## 5. IMPLEMENTATION SEQUENCE

### 5.1 Recommended Order

```
1. WP7 (Disclosure Synthesis) — Creates the core external value
2. WP8 (Information Requests) — Operationalizes gap analysis
3. Modified WP6 (Bifurcation) — Restructures outputs
4. Enhanced Explanations — Improves team understanding
```

### 5.2 Dependency Map

```
WP1-WP5 (existing) → WP7 (new) → Modified WP6 (new outputs)
                  ↘
                    WP8 (new) → Modified WP6 (internal report)
```

### 5.3 Risk Mitigation

| Risk | Mitigation |
|---|---|
| Synthesis produces incorrect claims | All prose must map to ExtractedFact IDs; no generative AI |
| Information requests are too generic | Use bond-domain templates with specific examples |
| External package reveals internal gaps | Clear separation; gaps only in Internal Report |
| Team ignores requests | Priority scoring; deadline tracking; escalation logic |

---

## 6. SUCCESS METRICS

### 6.1 External Advisory Package Quality

- Advisor can understand project in <15 minutes
- Every claim in disclosure sections traces to evidence
- No "[TBD]" markers in sections with sufficient facts
- Professional, neutral tone throughout

### 6.2 Internal Readiness Report Utility

- Team knows exactly what's missing
- Information requests are actionable
- Gap → Request → Resolution workflow is clear
- Readiness score improvements are predictable

### 6.3 Information Request Effectiveness

- 80%+ of requests result in new evidence within 2 weeks
- Team reports requests are "helpful" or "very helpful"
- Reduced back-and-forth with advisors on missing information

---

## 7. FILES IN THIS PACKAGE

This iteration guide is accompanied by:

1. **WP7_DISCLOSURE_SYNTHESIS_ENGINE.md** — Full specification for disclosure content generation
2. **WP8_INFORMATION_REQUEST_SYSTEM.md** — Full specification for gap-driven prompts
3. **INTERNAL_READINESS_REPORT_SPEC.md** — Detailed structure for internal deliverable
4. **EXTERNAL_ADVISORY_PACKAGE_SPEC.md** — Detailed structure for advisor deliverable

Each file is self-contained and bot-ready for implementation.

---

## 8. GUIDING PRINCIPLES FOR IMPLEMENTATION

### 8.1 Evidence Integrity (Non-Negotiable)

- Every synthesized sentence must trace to ExtractedFact(s)
- "[TBD]" markers are mandatory when evidence is insufficient
- No promotional language; no forward-looking claims without qualification
- Confidence thresholds must be respected

### 8.2 Audience Separation (Non-Negotiable)

- External Package never reveals internal gaps, conflicts, or operational status
- Internal Report contains full operational detail
- Same underlying facts, different presentations

### 8.3 Actionability (Non-Negotiable)

- Information Requests must be specific enough to act on
- "Why it matters" must reference real bond market requirements
- Examples must show what success looks like

### 8.4 Transparency (Non-Negotiable)

- TBD markers in External Package acknowledge limitations without exposing gaps
- Assumptions are clearly separated from facts
- Disclaimer language is mandatory and prominent

---

**END OF OVERVIEW**

Proceed to implementation files for detailed specifications.
