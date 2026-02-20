# Internal Readiness Report Specification

**Bond Facility Management System (BFMS)**

**Status:** FINAL (v1.0) | **Purpose:** Sponsor team operational visibility

---

## 1. DOCUMENT PURPOSE

The Internal Readiness Report is the **operational control document** for the project sponsor team. It provides complete visibility into:

- Current readiness state and trajectory
- Specific gaps blocking progress
- Actionable information requests
- Evidence audit trail
- Checklist progress by phase

This document is **NOT** for external consumption. Municipal advisors, rating agencies, and investors receive the External Advisory Package instead.

---

## 2. AUDIENCE & USE CASES

### 2.1 Primary Audience

- Project Sponsor leadership
- Operations & Innovation Manager
- Internal finance team
- Legal/compliance team

### 2.2 Use Cases

| Use Case | How Report Supports |
|---|---|
| Weekly status meetings | Readiness summary + gap priorities |
| Resource allocation | Information requests with owner assignments |
| Advisor engagement prep | Identify gaps to close before advisor meetings |
| Board reporting | High-level score + dimension breakdown |
| Audit/compliance | Evidence index with full provenance |

---

## 3. REPORT STRUCTURE

### 3.1 Section Hierarchy

```
InternalReadinessReport
├── 1. Executive Summary
│   ├── Current Readiness Score
│   ├── Score Trajectory (if history available)
│   ├── Key Achievements Since Last Report
│   └── Critical Blockers
│
├── 2. Readiness Dashboard
│   ├── Overall Score (0-10)
│   ├── Dimension Breakdown (6 dimensions × score + explanation)
│   ├── Score Interpretation
│   └── Recommended Actions
│
├── 3. Gap Analysis
│   ├── Critical Gaps (blocking progress)
│   ├── High-Priority Gaps (material impact)
│   ├── Medium-Priority Gaps (should address)
│   └── Low-Priority Gaps (nice to have)
│
├── 4. Information Requests
│   ├── Request Summary by Priority
│   ├── Requests by Owner
│   ├── Overdue Requests
│   └── Full Request Detail (expandable)
│
├── 5. Checklist Status
│   ├── Phase Summary Table
│   ├── P1: Issuer Authority & Deal Formation
│   ├── P2: Project & Technology Definition
│   ├── P3: Financial Structure & Revenue Model
│   ├── P4: Risk, Security & Disclosure
│   ├── P5: SLB Architecture & Final Modeling
│   └── P6: Advisor Engagement & Execution
│
├── 6. Evidence Index
│   ├── Summary Statistics
│   ├── Facts by Domain (grouped)
│   ├── Fact Detail Table
│   └── Conflict/Duplicate Registry
│
├── 7. Assumption Register
│   ├── Financial Assumptions
│   ├── Operational Assumptions
│   ├── Market Assumptions
│   └── Assumption Impact Analysis
│
└── 8. Appendices
    ├── A: Full Gap Detail
    ├── B: Readiness Calculation Methodology
    └── C: Version History
```

---

## 4. SECTION SPECIFICATIONS

### 4.1 Executive Summary

**Purpose:** Enable 2-minute orientation for busy executives

**Content:**

```markdown
## Executive Summary

**Project:** {project.name}
**Report Date:** {generated_at}
**Report Version:** {version}

### Current Readiness Score

**{overall_score}/10** — {score_interpretation}

{IF score >= 7.6}
✅ Ready for broad market engagement
{ELSEIF score >= 5.6}
🟡 Ready for selective advisor engagement
{ELSEIF score >= 3.1}
🟠 Structurally viable; sponsor work should continue
{ELSE}
🔴 Too early; focus on foundational work
{ENDIF}

### Key Achievements Since Last Report

{FOR achievement IN recent_achievements}
- ✓ {achievement.description} ({achievement.date})
{ENDFOR}

### Critical Blockers

{FOR blocker IN critical_gaps}
- ⚠️ **{blocker.title}**: {blocker.summary}
  - Impact: {blocker.consequences}
  - Owner: {blocker.suggested_owner}
{ENDFOR}

{IF critical_gaps.count == 0}
No critical blockers identified.
{ENDIF}
```

---

### 4.2 Readiness Dashboard

**Purpose:** Visual representation of readiness state with explanations

**Content:**

```markdown
## Readiness Dashboard

### Overall Score: {overall_score}/10

| Dimension | Weight | Score | Status |
|-----------|--------|-------|--------|
{FOR dim IN dimensions}
| {dim.name} | {dim.weight}% | {dim.score}/5.0 | {dim.status_emoji} |
{ENDFOR}

### Dimension Details

{FOR dim IN dimensions}
#### {dim.name} ({dim.score}/5.0)

**What This Measures:** {dim.what_measured}

**Current State:** {dim.current_state_explanation}

**Why It Matters:**
> {dim.why_it_matters}

**Key Evidence:**
{FOR fact IN dim.supporting_facts LIMIT 5}
- {fact.schema_path}: {fact.value} (confidence: {fact.confidence}%)
{ENDFOR}

**Gaps Affecting This Dimension:**
{FOR gap IN dim.related_gaps}
- {gap.title} ({gap.severity})
{ENDFOR}

{IF dim.score < 3.0}
⚠️ **Action Required:** {dim.recommended_action}
{ENDIF}

---
{ENDFOR}

### Score Interpretation Guide

| Score Range | Meaning | Recommended Action |
|-------------|---------|-------------------|
| 0.0-3.0 | Too Early | Focus on P1-P2; no external engagement |
| 3.1-5.5 | Structurally Viable | Continue sponsor work; selective advisor input |
| 5.6-7.5 | Ready for Selective Engagement | Engage bond counsel, FA, IE |
| 7.6-10.0 | Ready for Broad Market | Full market engagement; target closing |
```

---

### 4.3 Gap Analysis

**Purpose:** Prioritized list of what's missing with actionable context

**Content:**

```markdown
## Gap Analysis

### Summary

| Priority | Count | Impact |
|----------|-------|--------|
| 🔴 Critical | {critical_count} | Blocks deal progress |
| 🟠 High | {high_count} | Blocks next phase |
| 🟡 Medium | {medium_count} | Affects readiness score |
| 🟢 Low | {low_count} | Nice to have |

### Critical Gaps (Must Address Immediately)

{FOR gap IN gaps WHERE gap.severity == 'critical'}
#### ⚠️ {gap.title}

**Missing Information:** {gap.missing_fact_paths}

**Current State:** {gap.current_evidence_state}

**Why This Matters:**
> {gap.bond_domain_context.why_it_matters}

**Consequences if Not Addressed:**
> {gap.bond_domain_context.consequences}

**Affects:**
- Checklist Items: {gap.affected_checklist_items}
- Readiness Dimensions: {gap.affected_dimensions}

**Suggested Owner:** {gap.suggested_owner}
**Target Date:** {gap.suggested_deadline}

---
{ENDFOR}

### High-Priority Gaps

{FOR gap IN gaps WHERE gap.severity == 'high'}
...abbreviated format...
{ENDFOR}

### Medium-Priority Gaps

{FOR gap IN gaps WHERE gap.severity == 'medium'}
...abbreviated format...
{ENDFOR}

### Low-Priority Gaps

{FOR gap IN gaps WHERE gap.severity == 'low'}
- {gap.title} — {gap.summary}
{ENDFOR}
```

---

### 4.4 Information Requests

**Purpose:** Actionable task list for the team

**Content:**

```markdown
## Information Requests

### Summary

| Status | Count |
|--------|-------|
| 🔴 Open (Critical/High) | {open_critical_high} |
| 🟠 Open (Medium/Low) | {open_medium_low} |
| 🔵 In Progress | {in_progress} |
| 🟢 Resolved | {resolved} |
| ⚫ Deferred | {deferred} |

### Requests by Owner

{FOR owner IN owners}
#### {owner.name} ({owner.open_count} open)

| Request | Priority | Status | Due |
|---------|----------|--------|-----|
{FOR req IN owner.requests}
| {req.title} | {req.priority} | {req.status} | {req.target_date} |
{ENDFOR}
{ENDFOR}

### Overdue Requests

{FOR req IN requests WHERE req.is_overdue}
⚠️ **{req.title}** — Due: {req.target_date} ({req.days_overdue} days overdue)
- Owner: {req.suggested_owner}
- Impact: {req.consequences}
{ENDFOR}

### Request Detail

{FOR req IN requests ORDER BY priority DESC}
---
#### IR-{req.request_code}: {req.title}

**Priority:** {req.priority} | **Status:** {req.status} | **Owner:** {req.suggested_owner}

**What We Need:**
{req.guidance.overview}

**Specific Questions:**
{FOR q IN req.guidance.specific_questions}
- {q}
{ENDFOR}

**Why It Matters:**
> {req.bond_domain_context.why_it_matters}

**Example of What's Acceptable:**
> {req.examples[0].content_preview}

**Acceptable Sources:** {req.acceptable_sources}

**Target Date:** {req.suggested_deadline}

{IF req.linked_evidence}
**Submitted Evidence:** {req.linked_evidence.artifact_id} (pending review)
{ENDIF}

---
{ENDFOR}
```

---

### 4.5 Checklist Status

**Purpose:** Phase-by-phase operational tracking

**Content:**

```markdown
## Checklist Status

### Phase Summary

| Phase | Name | Ready | In Progress | Blocked | Not Started | Can Proceed |
|-------|------|-------|-------------|---------|-------------|-------------|
{FOR phase IN phases}
| {phase.code} | {phase.name} | {phase.ready} | {phase.in_progress} | {phase.blocked} | {phase.not_started} | {phase.can_proceed_emoji} |
{ENDFOR}

### Phase Details

{FOR phase IN phases}
## {phase.code}: {phase.name}

**Completion:** {phase.completion_percent}% ({phase.ready}/{phase.total} items ready)

**Phase Gate Status:** {phase.gate_status}

{IF NOT phase.can_proceed}
⚠️ **Cannot proceed to {phase.next_phase}:** {phase.blocking_reason}
{ENDIF}

| Item | Status | Evidence | Gaps |
|------|--------|----------|------|
{FOR item IN phase.items}
| {item.code} {item.title} | {item.status_emoji} {item.status} | {item.evidence_count} facts | {item.gap_count} gaps |
{ENDFOR}

{FOR item IN phase.items}
### {item.code}: {item.title}

**Status:** {item.status}

**Description:** {item.description}

**Required Evidence:**
{FOR path IN item.required_fact_paths}
- {path}: {path.status_emoji} {path.current_value OR "Not provided"}
{ENDFOR}

**Why This Matters:**
> {item.why_it_matters}

{IF item.status == 'blocked'}
⚠️ **Blocked By:** {item.blocking_reason}
{ENDIF}

---
{ENDFOR}
{ENDFOR}
```

---

### 4.6 Evidence Index

**Purpose:** Complete audit trail of all accepted facts

**Content:**

```markdown
## Evidence Index

### Summary

- **Total Facts:** {total_facts}
- **Accepted:** {accepted_count}
- **Proposed (Pending Review):** {proposed_count}
- **Rejected:** {rejected_count}
- **Conflicts Detected:** {conflict_count}
- **Duplicates:** {duplicate_count}

### Facts by Domain

{FOR domain IN domains}
#### {domain.name} ({domain.fact_count} facts)

| Schema Path | Value | Confidence | Source | Status |
|-------------|-------|------------|--------|--------|
{FOR fact IN domain.facts}
| {fact.schema_path} | {fact.value_truncated} | {fact.confidence}% | {fact.artifact_name} p.{fact.page} | {fact.status} |
{ENDFOR}
{ENDFOR}

### Conflicts Requiring Resolution

{FOR conflict IN conflicts}
⚠️ **Conflict in {conflict.schema_path}:**
- Value A: {conflict.value_a} (source: {conflict.source_a})
- Value B: {conflict.value_b} (source: {conflict.source_b})
- **Recommended Resolution:** {conflict.recommendation}
{ENDFOR}

### Full Fact Detail

*(Expandable in digital format; summarized in PDF)*
```

---

### 4.7 Assumption Register

**Purpose:** Track all assumptions driving models and projections

**Content:**

```markdown
## Assumption Register

### Summary

| Category | Count | Avg Confidence |
|----------|-------|----------------|
| Financial | {fin_count} | {fin_avg_conf}% |
| Operational | {ops_count} | {ops_avg_conf}% |
| Market | {mkt_count} | {mkt_avg_conf}% |

### Assumption Detail

{FOR assumption IN assumptions}
#### {assumption.name}

| Attribute | Value |
|-----------|-------|
| Value | {assumption.value} {assumption.unit} |
| Source | {assumption.source_type}: {assumption.source_ref} |
| Confidence | {assumption.confidence}% |
| Impact Category | {assumption.impact_category} |
| Last Updated | {assumption.last_updated} |

**Rationale:** {assumption.rationale}

**Sensitivity:** {assumption.sensitivity_description}

---
{ENDFOR}

### High-Impact Assumptions

{FOR assumption IN assumptions WHERE assumption.impact == 'high'}
⚠️ **{assumption.name}** — {assumption.sensitivity_description}
{ENDFOR}
```

---

## 5. GENERATION LOGIC

### 5.1 Report Generation Pipeline

```python
def generate_internal_report(project_id: UUID) -> InternalReadinessReport:
    # 1. Gather data
    facts = get_accepted_facts(project_id)
    gaps = compute_gaps(project_id)
    requests = get_information_requests(project_id)
    checklist = compute_checklist_states(project_id)
    dimensions = compute_readiness_dimensions(project_id)
    assumptions = get_assumptions(project_id)
    
    # 2. Compute derived values
    overall_score = compute_overall_score(dimensions)
    critical_blockers = filter_critical(gaps)
    
    # 3. Assemble report
    report = InternalReadinessReport(
        project_id=project_id,
        version=increment_version(project_id),
        generated_at=now(),
        
        executive_summary=build_executive_summary(
            overall_score, critical_blockers
        ),
        readiness_dashboard=build_dashboard(dimensions, overall_score),
        gap_analysis=build_gap_analysis(gaps),
        information_requests=build_request_section(requests),
        checklist_status=build_checklist_section(checklist),
        evidence_index=build_evidence_index(facts),
        assumption_register=build_assumption_section(assumptions)
    )
    
    return report
```

### 5.2 Explanation Generation

Each dimension, checklist item, and gap includes contextual explanations:

```python
DIMENSION_EXPLANATIONS = {
    "issuer_legal_authority": {
        "what_measured": "Legal foundation for bond issuance including IDA authority, inducement, and tax status",
        "why_it_matters": """
            Investor confidence begins with unambiguous legal authority. 
            Without clear issuer authorization and tax status determination, 
            bond counsel cannot issue required opinions, and the transaction 
            cannot close. This dimension gates all subsequent work.
        """
    },
    "project_technology_viability": {
        "what_measured": "Technology readiness, operating plan completeness, and site control",
        "why_it_matters": """
            Municipal advisors and rating agencies assess technology risk 
            as a primary credit driver. For novel technologies like UCS, 
            evidence of pilot performance, equipment specifications, and 
            warranty coverage is essential. Site control (lease/deed/option) 
            must be documented before financial modeling.
        """
    },
    # ... additional dimensions
}
```

---

## 6. OUTPUT FORMATS

### 6.1 Primary: Markdown

Source of truth; supports version control and diff comparison.

### 6.2 Secondary: PDF

Professional format for board presentations and archival.

### 6.3 Tertiary: HTML (Interactive)

Expandable sections, clickable links, filtering capability.

---

## 7. API SURFACE

```
POST /projects/{id}/internal-report/generate
GET /projects/{id}/internal-report
GET /projects/{id}/internal-report/export?format=md|pdf|html
GET /projects/{id}/internal-report/history
```

---

## 8. DEFINITION OF DONE

Internal Readiness Report is complete when:

- [ ] All 8 sections generate correctly
- [ ] Explanations provide bond-domain context
- [ ] Gap → Request linkage is visible
- [ ] Team can identify top priorities in <5 minutes
- [ ] Export produces professional-quality documents
- [ ] Report answers "what's blocking us?" clearly

---

**END OF SPECIFICATION**
