# Muni-Pal Pilot Navigation System

**Status:** Draft v1.0
**Date:** 2026-04-09
**Owner:** CEO + CTO
**Purpose:** Operational playbook for deploying Muni-Pal's Bond Facility Management System to pilot cohorts. Every section is actionable: checklists, step-by-step instructions, or decision matrices. This document is the single source of truth for how we go from "prospect" to "paying client" to "delivered service."

---

## 0. Document Map & Cross-References

This document does not duplicate existing docs — it connects them. Every section references its authoritative source.

| Section | Depends On | Source File |
|---------|-----------|-------------|
| Pre-Pilot Checklist (§2) | Measurement Protocol §9 | `docs/pilot-measurement-protocol.md` |
| Legal Gates (§2.1) | Counsel Briefing | `docs/counsel-briefing-ma-status.md` |
| Engagement Letter (§2.2) | Pilot Engagement Letter | `docs/pilot-engagement-letter.md` |
| Domain Corrections (§2, §5) | Strategist Review | `docs/bond-strategist-pilot-review.md` |
| Pricing (§8) | 3-Tier Structure | `docs/three-tier-pricing-structure.md` |
| Baseline Interview (§7) | Interview Script | `docs/pilot-baseline-interview.md` |
| BFMS Pipeline (§1, §5, §6) | Build Spec | `Muni-Pal — Bond Facility Management System (BFMS).md` |
| COI Model (§7) | Track 2 Spec | `docs/track2-coi-model-upgrade-spec.md` |
| Credit Spreads (§6) | Monitor Guide | `docs/credit-spread-monitor-guide.md` |
| Test Entities (§5) | Synthetic Data | `Bond Facility Development/000_Oakport_*` |
| Onboarding Packages (§4) | Client Launch Skill | `EDRS/client-launch-protocol-skill/` |
| Brand (all outputs) | Brand Guidelines | `BRAND-GUIDELINES.md` |

---

## 1. Service Architecture & Feature Toggle Matrix

### 1.1 BFMS Component Inventory

Every capability the platform can deliver, organized by pipeline stage:

| # | Component | WP Stage | Description | Delivery Mode | Primary Cost Driver |
|---|-----------|----------|-------------|---------------|---------------------|
| 1 | Project Setup + Playbook Assignment | WP1 | Create workspace, assign sector playbook (healthcare/waste), define schema paths | Automated | Infrastructure |
| 2 | Artifact Vault (upload, chunk, hash) | WP2 | Document ingestion, SHA-256 hashing, immutable chunking, storage | Automated | Infrastructure + Storage |
| 3 | AI Extraction Pipeline | WP3 | 14 sector-specific extractors propose facts from documents with confidence scores | AI Compute | Claude API tokens |
| 4 | Human Fact Review | WP3 | Bond Strategist accepts/rejects/flags proposed facts; full provenance chain | Labor | Bond Strategist hours |
| 5 | Readiness Checklist (19-item) | WP4 | 7-phase bond deal flow checklist (P1-P7), evidence-linked status tracking | Automated | Compute |
| 6 | Readiness Scoring (8 dimensions) | WP4 | Weighted composite score (0-10) across Financial Strength, Revenue Stability, Debt Profile, Legal, Project, Operational, Market, Insurance | Automated | Compute |
| 7 | Gap Analysis | WP4 | Identify missing/weak evidence against checklist requirements, severity-ranked | Automated | Compute |
| 8 | Financial Models (DSCR, Revenue, Sensitivity) | WP5 | Revenue projection, DSCR analysis, 3-scenario sensitivity testing, assumption register | Hybrid | Labor + Compute |
| 9 | Handoff Pack Assembly | WP6 | 7-section advisor-ready deliverable with full evidence index | Automated | Compute |
| 10 | Legal Document Templates | WP6 | 11 templates (engagement letter, indenture, loan agreement, closing cert, etc.) | Automated | Compute |
| 11 | Market Intelligence Report (MIR) | Sensing | Sector snapshot from 866+ healthcare / 198+ waste deal corpus | Automated | Compute |
| 12 | Readiness Assessment (167-item self-serve) | Sensing | Healthcare-specific readiness scoring tool (hospital: 69, SL: 72, FQHC: 68 items) | Automated | Compute |
| 13 | COI Benchmarking | Sensing | Historical cost-of-issuance ranges from 39-deal itemized dataset, sliced by sub-sector | Automated | Compute |
| 14 | Credit Spread Monitor | Sensing | Live AAA benchmark yields + EMMA trade data + issuer fee structures = all-in TIC grid | Automated | Infrastructure (scraping) |
| 15 | Advisor Agent (Claude chat) | Advisory | Claude-powered deal guidance with tool access to project facts, templates, documents | AI Compute | Claude API tokens |
| 16 | Deal Document Management + VDR | DocMgmt | Document state machine, versioning, virtual data room | Hybrid | Infrastructure + Labor |
| 17 | Information Request Routing | Advisory | Organize/route info requests between borrower, UW, counsel, MA | Hybrid | Labor + Compute |
| 18 | Advisory Packages | Advisory | Deal coordination workflows, milestone tracking | Labor | Bond Strategist hours |
| 19 | Disclosure Tracking (SEC 15c2-12) | Compliance | EMMA filing tracker, continuing disclosure calendar | Automated | Compute |
| 20 | Risk Reporting | Analytics | Credit scoring matrices, risk visualization, peer comparison | Automated | Compute |
| 21 | Revenue Diversification Analysis | Analytics | D3-based revenue visualization, payer mix analysis | Automated | Compute |
| 22 | Report Export (PDF/Excel) | Delivery | Client-facing report generation from platform data | Automated | Compute |

### 1.2 Feature Toggle Matrix

The operating table. Each cell indicates whether the component is available at that tier. Use this matrix to configure client access and to scope engagements.

| # | Component | Free (Lead Gen) | Subscription ($20K/yr) | Tier 1: Diagnostic (+$15-25K) | Tier 2: Standard ($40-50K) | Tier 3: Accelerator ($75K+) | Partner (Custom) |
|---|-----------|----------------|----------------------|-------------------------------|----------------------------|-----------------------------|-------------------|
| 1 | Project Setup | OFF | ON | ON | ON | ON | ON |
| 2 | Artifact Vault | OFF | ON (5 docs) | ON (unlimited) | ON | ON | ON |
| 3 | AI Extraction | OFF | OFF | ON | ON | ON | ON |
| 4 | Human Fact Review | OFF | OFF | ON | ON | ON | ON |
| 5 | Readiness Checklist | OFF | ON (view-only) | ON | ON | ON | ON |
| 6 | Readiness Scoring | OFF | ON | ON | ON | ON | ON |
| 7 | Gap Analysis | OFF | ON (summary) | ON (detailed) | ON | ON | ON |
| 8 | Financial Models | OFF | OFF | ON (read-only) | ON | ON | ON |
| 9 | Handoff Pack | OFF | OFF | OFF | ON | ON | ON |
| 10 | Legal Templates | OFF | OFF | OFF | GATED | ON | ON |
| 11 | MIR | **ON** | ON | ON | ON | ON | ON |
| 12 | Readiness Assessment | **ON** | ON | ON | ON | ON | ON |
| 13 | COI Benchmarking | OFF | ON | ON | ON | ON | ON |
| 14 | Credit Spread Monitor | **ON** (read-only) | ON | ON | ON | ON | ON |
| 15 | Advisor Agent | OFF | GATED | GATED | ON | ON | ON |
| 16 | Document Mgmt + VDR | OFF | OFF | OFF | GATED | ON | ON |
| 17 | Info Request Routing | OFF | OFF | OFF | ON | ON | ON |
| 18 | Advisory Packages | OFF | OFF | OFF | ON | ON | ON |
| 19 | Disclosure Tracking | OFF | OFF | OFF | OFF | ON | ON |
| 20 | Risk Reporting | OFF | ON (basic) | ON | ON | ON | ON |
| 21 | Revenue Diversification | OFF | ON | ON | ON | ON | ON |
| 22 | Report Export | OFF | ON (1/mo) | ON | ON | ON | ON |

**Legend:**
- **ON** = Available, no restrictions
- **OFF** = Not available at this tier
- **GATED** = Capability exists but requires manual activation by CTO/CEO
- **ON (qualifier)** = Available with noted restriction

**Notes:**
- Free tier = lead generation only. Three tools (MIR, Readiness Assessment, Credit Spread Monitor) drive awareness and capture emails.
- Subscription tier = platform access. Ongoing value without per-deal engagement. Think of this as the "between deals" tier.
- Tier 1 adds diagnostic depth (extraction, human review, full gap analysis). One-time per-deal engagement layered on subscription.
- Tier 2 adds active deal coordination. This is where labor scales with the deal.
- Tier 3 adds remediation support, UW benchmarking, timeline optimization. Highest labor intensity.
- Partner tier includes infrastructure installation and ongoing operation. True partnerships only.

### 1.3 Platform Readiness Status

Current state of each component against "sell-ready" (can deliver to a paying client without embarrassment):

| Component | Build Status | Sell-Ready? | Gap | Remediation |
|-----------|-------------|-------------|-----|-------------|
| MIR | Shipped (Apr 5) | YES | None | Maintain |
| Readiness Assessment | Shipped (Apr 5) | YES | None | Maintain |
| Credit Spread Monitor | Live | YES (with caveats) | AAA curve manual fallback | Automate scraping reliability |
| COI Benchmarking | Backend exists | PARTIAL | UI 70% complete (LAU-286) | Complete frontend wiring |
| AI Extraction (WP3) | Pipeline functional | PARTIAL | Not tested against live client docs | 000_Oakport test (§5) |
| Human Fact Review | UI exists (FactsReview.tsx) | PARTIAL | Workflow not battle-tested | Pilot validation |
| Financial Models | Pipeline functional | PARTIAL | Need domain accuracy review | Bond Strategist validation |
| Handoff Pack | Pipeline functional | PARTIAL | Export formats need polish | Template refinement |
| Advisor Agent | Working | NO | Unmonitored, no guardrails | Guardrail system needed |
| Document Mgmt + VDR | Planned (PLAN.md) | NO | 11 new tables, not built | Phase 2 build |
| Advisory Packages | Route exists | PARTIAL | 57KB service, complex workflows | Integration testing |
| Pricing Page | In progress (LAU-324) | NO | CTO building | Complete implementation |
| Feature Toggles | Not built | NO | Only `auth_enforcement_v2` exists | Build per-tier toggle system |

**Bottom line:** Free-tier tools are sell-ready. Subscription-tier components are partially ready. Tier 1+ requires the 000_Oakport end-to-end test (§5) to validate before live pilot.

---

## 2. Pre-Pilot Checklist

**Rule: Pilot cannot start until ALL gates in §2.1–§2.5 are GREEN.** No exceptions. A failed gate is a blocker, not a risk to manage.

### 2.1 Legal Gates

| # | Gate | Status | Owner | Cross-ref |
|---|------|--------|-------|-----------|
| L1 | Counsel briefing document sent | [ ] | CEO | `docs/counsel-briefing-ma-status.md` |
| L2 | Written opinion received: per-activity rulings on Activities #1–#8 | [ ] | Counsel | Same, §4 |
| L3 | Section 15B(e)(4)(C) vs IRMA path determined | [ ] | Counsel | Same, §5 |
| L4 | Activity #5 (COI prediction) separately addressed — this is the highest legal risk | [ ] | Counsel | Same, §4 Activity 5 |
| L5 | Free activities (MIR + Readiness Scan) assessed for MA risk | [ ] | Counsel | `docs/three-tier-pricing-structure.md` §Caution |
| L6 | Engagement letter §1 narrowed: "review" → "routing" per Bond Strategist | [ ] | CEO | `docs/bond-strategist-pilot-review.md` §3 |
| L7 | Engagement letter §7 updated with MA acknowledgment as condition precedent | [ ] | CEO | Same |
| L8 | Data security clause (§7A) reviewed — Adventist is large health system | [ ] | CTO | `docs/pilot-engagement-letter.md` §7A |
| L9 | COI prediction language qualified: "statistical ranges from historical comparables" | [ ] | CEO | `docs/three-tier-pricing-structure.md` §All Tiers |

> **Warning:** Per Bond Strategist review, §7 disclaimer alone cannot cure activity that is in fact municipal advisory. Legal clearance on scope is load-bearing, not cosmetic.

### 2.2 Engagement & Counterpart Gates

| # | Gate | Status | Owner |
|---|------|--------|-------|
| E1 | Adventist counterpart identified (CFO or VP Finance) | [ ] | CEO |
| E2 | Adventist's registered MA confirmed on THIS deal (not prior deal) | [ ] | CEO + Bond Strategist |
| E3 | MA notified in writing of Launch Shop's role | [ ] | CEO |
| E4 | UW notified in writing of Launch Shop's role | [ ] | CEO |
| E5 | MA written acknowledgment obtained (§7 condition precedent): MA confirms (a) providing advice, (b) aware of Launch Shop role, (c) does not object to §1 scope | [ ] | CEO |
| E6 | Engagement letter signed by both parties | [ ] | CEO |
| E7 | Adventist instrumentation consent obtained in writing | [ ] | CEO |
| E8 | Vendor procurement timeline assessed: SOC 2 / BAA / IT security review required? | [ ] | CTO |
| E9 | If procurement required: timeline incorporated into pilot schedule (3–6 months possible) | [ ] | CTO + CEO |

> **Warning:** Per baseline interview script Part 4 — large health systems have procurement processes. If Adventist requires SOC 2 Type II, pilot timeline could slip by months. Discover this in baseline interview, not after signing.

### 2.3 Platform Readiness Gates

| # | Gate | Status | Owner |
|---|------|--------|-------|
| P1 | 000_Oakport end-to-end test PASSED (all 6 WP stages — see §5) | [ ] | CTO + Bond Strategist |
| P2 | Domain errors resolved from synthetic run (feedstock_supply removed, DSCR corrections, Five Cs factors correct) | [ ] | Bond Strategist |
| P3 | Platform produces correct outputs for Adventist-like synthetic profile (2-hour exercise) | [ ] | Bond Strategist |
| P4 | Feature toggles configured for Adventist's tier | [ ] | CTO |
| P5 | Client workspace provisioned with encryption at rest + in transit | [ ] | CTO |
| P6 | Access controls limited to assigned personnel only | [ ] | CTO |
| P7 | Pricing page live and accepting payments (if charging pilot) | [ ] | CTO (LAU-324) |

### 2.4 Measurement Infrastructure Gates

| # | Gate | Status | Owner | Cross-ref |
|---|------|--------|-------|-----------|
| M1 | Protocol signed by CEO + Bond Strategist | [ ] | CEO | `docs/pilot-measurement-protocol.md` §9 |
| M2 | Baseline interview completed | [ ] | CEO + Bond Strategist | `docs/pilot-baseline-interview.md` |
| M3 | Baseline data filed in `pilot/adventist-2026/baseline.md` | [ ] | CEO | Interview script §After the call |
| M4 | Frozen predictions filed in `pilot/adventist-2026/frozen-predictions.md` | [ ] | Bond Strategist | Protocol §5 |
| M5 | Task log infrastructure live + tested with dummy task | [ ] | CTO | Protocol §4.1 |
| M6 | Hours diary template sent to Adventist counterpart | [ ] | CEO | Protocol §4.2 |
| M7 | Week 1 diary reminder scheduled | [ ] | Executive Assistant | Protocol §4.2 |
| M8 | Abort criteria reviewed: if no pricing within 16 weeks, report as inconclusive | [ ] | CEO | Protocol §7 |
| M9 | COI v2 model frozen prediction computed from Track 2 output | [ ] | Bond Strategist | `docs/track2-coi-model-upgrade-spec.md` §7 |

### 2.5 Pricing & Commercial Gates

| # | Gate | Status | Owner |
|---|------|--------|-------|
| C1 | Pilot pricing decision documented: free or paid, and at what rate | [ ] | CEO |
| C2 | If charging: engagement letter §2 rewritten (currently says "zero fee") | [ ] | CEO |
| C3 | If charging: invoice/payment infrastructure ready | [ ] | CTO |
| C4 | If charging: reconcile measurement-rights-as-consideration framing with payment | [ ] | CEO |
| C5 | Tier assignment for Adventist determined based on baseline interview pricing signal | [ ] | CEO |

---

## 3. Lead Generation & Funnel Architecture

### 3.1 Funnel Overview

```
AWARENESS              ENGAGEMENT            QUALIFICATION          CONVERSION
+------------------+   +----------------+   +-----------------+   +--------------+
| muni-pal.io      |   | Free Tools     |   | Skool Community |   | Paid Tier    |
| SEO, referrals,  |-->| MIR            |-->| BFMS playbooks  |-->| Engagement   |
| Bond Strategist  |   | Readiness Scan |   | Peer discussion |   | letter       |
| content, Skool   |   | Credit Spreads |   | Weekly digests  |   | Onboarding   |
+------------------+   +----------------+   +-----------------+   +--------------+
                        |                    |                     |
                        Lead capture         Nurture + educate    Close + activate
                        (email required)     (demonstrate value)  (feature toggles)
```

### 3.2 Free Tool Lead Generation

Each free tool serves a specific funnel purpose:

**Market Intelligence Report (MIR)**
- Trigger: User enters sector + geography on muni-pal.io/tools
- Output: Automated sector snapshot from 866+ deal corpus
- Lead capture: Email required for report delivery
- Qualification signal: Sector, deal size mentioned, repeat visits
- Content hook: "866 healthcare transactions analyzed. See where your next deal benchmarks."
- MA compliance: Counsel must clear as non-advisory (§2.1 Gate L5)

**Readiness Assessment (167-item)**
- Trigger: User self-serves on muni-pal.io/tools/readiness
- Output: Gap score + comparison to sector benchmarks
- Lead capture: Email + organization name required to see results
- Qualification signal: Completion rate (>80% = serious), gap severity, sub-sector
- Content hook: "Where does your organization stand against 167 bond readiness factors?"
- MA compliance: Same as MIR — descriptive framework, not prescriptive advice

**Credit Spread Monitor**
- Trigger: User visits muni-pal.io/tools/credit-spreads
- Output: Live yield curves, all-in TIC grid, EMMA comparable trades
- Lead capture: Email for detailed issuer comparison export
- Qualification signal: Rating tier entered, par amount entered, issuer comparison requested
- Content hook: "See what money actually costs for [sector] borrowers at your rating."

### 3.3 Content Strategy

Content that feeds the funnel and positions Launch Shop as the evidence-first authority:

| Content Type | Frequency | Channel | Funnel Stage | Owner |
|-------------|-----------|---------|--------------|-------|
| BFMS explainer guides ("What is WP3 Extraction?") | 2/month | Skool + website blog | Awareness | CBO + Bond Strategist |
| Weekly credit spread digest | Weekly | Skool + email | Engagement | Bond Strategist (automated after setup) |
| COI benchmarking snapshots (anonymized, sector-level) | Monthly | Skool + website | Engagement | Bond Strategist |
| "What Good Looks Like" guides per sub-sector | 1/quarter | Skool + PDF download | Qualification | Bond Strategist |
| Case studies (post-pilot, per protocol §6-7 rules) | Per pilot | Website + Skool | Conversion | CEO |
| Healthcare CFO landing page updates | As needed | muni-pal.io/healthcare | Awareness | CBO |

> **Internal note:** Case studies require GREEN or AMBER pilot status AND written consent from borrower per pilot-engagement-letter.md §5. Never publish a WITHDRAWN pilot externally.

### 3.4 Lead Scoring

Simple point-based system to prioritize outreach:

| Signal | Points | Source |
|--------|--------|--------|
| MIR request | +10 | Website |
| Readiness Assessment started | +15 | Website |
| Readiness Assessment completed (>80% items) | +25 | Website |
| Credit Spread Monitor: entered real rating + par | +15 | Website |
| Skool community joined | +20 | Skool |
| Skool: 3+ post engagements (comments, likes) | +15 | Skool |
| Repeat MIR request (different deal or timeframe) | +20 | Website |
| Downloaded "What Good Looks Like" guide | +10 | Website |
| Direct inquiry via email or form | +30 | Website/email |
| Referred by existing client | +40 | Direct |
| Baseline interview accepted | +50 | Direct |

**Thresholds:**
- Score > 30: Add to CRM, begin light nurture (Skool invite, weekly digest)
- Score > 60: Direct outreach from CEO or Bond Strategist
- Score > 80: Schedule discovery call / baseline interview

---

## 4. Onboarding Flow

### 4.1 Client Classification

When a lead converts to a client, classify them first:

```
Step 1: Client Type
├── Operator (borrower) → Full BFMS pathway (WP1-WP6)
│   ├── Healthcare → Assign healthcare playbook
│   │   ├── Hospital/health system
│   │   ├── Senior living / CCRC
│   │   ├── FQHC (bond track)
│   │   ├── FQHC (CDFI/NMTC track)
│   │   └── Behavioral health
│   └── Waste/Environmental → Assign waste playbook
│       ├── Solid waste authority
│       ├── Resource recovery
│       └── Environmental services
└── Agency (conduit/issuer) → Facility-level tools
    ├── ED/IDA agency
    └── Health Facilities Authority

Step 2: Tier Assignment (from baseline interview pricing signal + deal complexity)
├── Subscription only ($20K/yr) → Platform access, no per-deal engagement
├── Tier 1: Diagnostic (+$15-25K) → Credit memo + gap analysis
├── Tier 2: Standard ($40-50K) → Active deal coordination
├── Tier 3: Accelerator ($75K+) → Full pre-issuance support
└── Partner (custom) → Infrastructure install + operations

Step 3: MA Status Check
├── Has registered MA on this deal? → Proceed (§15B(e)(4)(C) path)
└── No MA? → STOP. Cannot engage without registered MA per legal framework.
    Recommend MA engagement first, offer to resume when MA is in place.
```

### 4.2 Client-Launch-Protocol Integration

The `client-launch-protocol` skill (located in `EDRS/client-launch-protocol-skill/`) generates a branded onboarding package as a ZIP file. This is the first tangible deliverable the client receives.

**Package contents by client type:**

For **Operator** (borrower):
```
{CLIENT_NAME}_BFMS_Package/
├── 00_WELCOME/
│   ├── 00_FOLDER-GUIDE.pdf          (branded config memo)
│   └── Welcome_Letter.pdf            (from BRAND-GUIDELINES.md voice)
├── 01_PROJECT-OVERVIEW/
│   ├── 00_FOLDER-GUIDE.pdf
│   └── Document_Request_Checklist.pdf (tailored to playbook: healthcare vs waste)
├── 02_FINANCING-STRUCTURE/
│   ├── 00_FOLDER-GUIDE.pdf
│   └── Comparable_Deals_Summary.pdf   (from MIR data for their sector)
├── 03_DUE-DILIGENCE/
│   ├── 00_FOLDER-GUIDE.pdf
│   └── Readiness_Gap_Summary.pdf      (from Readiness Assessment if completed)
├── 04_CLOSING-DOCUMENTS/
│   └── 00_FOLDER-GUIDE.pdf
├── 05_POST-ISSUANCE-COMPLIANCE/
│   └── 00_FOLDER-GUIDE.pdf
├── 06_REPORTING/
│   └── 00_FOLDER-GUIDE.pdf
└── 07_RESOURCE-LIBRARY/
    ├── 00_FOLDER-GUIDE.pdf
    └── BFMS_Quick_Reference.pdf
```

For **Agency** (conduit/issuer):
```
{CLIENT_NAME}_Facility_Package/
├── 00_WELCOME/
├── 01_PIPELINE-MANAGEMENT/
├── 02_DEAL-EXECUTION/
├── 03_BOARD-GOVERNANCE/
├── 04_COMPLIANCE-AND-REGULATORY/
├── 05_FINANCIAL-OPERATIONS/
├── 06_REPORTING/
├── 07_PROGRAMS-AND-INITIATIVES/
└── 08_RESOURCE-LIBRARY/
```

**Invocation steps:**

1. CTO/CEO prepares client config JSON with: `client_name`, `client_type` (operator/agency), `deal_archetype`, `engagement_tier`, `sector`, `active_deals`, `champion_name`, `champion_email`
2. Config can be sourced from:
   - Direct configuration (manual from baseline interview data)
   - Muni-Pal Sensing Engine (from readiness scan + lead form data)
   - EDRS Assessment Engine (if client came through EDRS funnel)
3. Run: `python build_launch_package.py --config config.json --output {client_name}.zip --source {direct|sensing|edrs} --tier {free|retained}`
4. Bond Strategist reviews generated package for domain accuracy (15 min)
5. Package delivered to client alongside engagement letter
6. Client workspace created in platform with matching folder structure

### 4.3 Feature Activation Checklist

Run this checklist when onboarding a new client. Check only the items for the assigned tier.

**All Tiers (Subscription and above):**
- [ ] Project created in platform (`/api/v1/projects/`)
- [ ] Playbook assigned (healthcare sub-sector or waste sub-sector)
- [ ] Client user account created with appropriate role
- [ ] MIR generated for client's sector + geography
- [ ] Readiness Assessment configured for client's sub-sector
- [ ] COI Benchmarking access enabled
- [ ] Risk Reporting (basic) enabled
- [ ] Revenue Diversification view enabled
- [ ] Report Export enabled (1/month for subscription, unlimited for higher tiers)
- [ ] Onboarding package (ZIP) delivered

**Tier 1: Diagnostic (add to above):**
- [ ] Artifact vault opened for unlimited document upload
- [ ] AI Extraction pipeline armed (triggers on document upload)
- [ ] Human Fact Review workflow activated
- [ ] Full Gap Analysis (detailed) enabled
- [ ] Financial Models (read-only) enabled
- [ ] Credit Memo scope agreed with client (document request list sent)
- [ ] Delivery timeline communicated (typically 3 weeks from document receipt)

**Tier 2: Standard (add to above):**
- [ ] Deal coordination workspace activated
- [ ] Milestone tracking configured with comparable deal timeline
- [ ] Information Request routing enabled
- [ ] Advisory Package workflows enabled
- [ ] Advisor Agent (Claude chat) enabled
- [ ] Dedicated point of contact assigned (CEO initially; Bond Strategist for domain questions)
- [ ] Weekly status cadence established with client

**Tier 3: Accelerator (add to above):**
- [ ] Gap remediation support workspace created
- [ ] UW benchmarking data access enabled (self-serve: top-10 UW performance data)
- [ ] Timeline optimization alerts configured
- [ ] Extended post-deal analysis scope confirmed
- [ ] Document Management + VDR enabled (if ready — GATED)
- [ ] E-Signature integration configured (if ready — GATED)
- [ ] Disclosure Tracking enabled
- [ ] Legal Templates access enabled

**Partner (add to above):**
- [ ] Infrastructure requirements scoped (on-prem vs cloud, integrations)
- [ ] Custom integration specification written
- [ ] SLA and support agreement drafted
- [ ] Dedicated implementation schedule created

---

## 5. End-to-End Testing Protocol

### 5.1 Purpose

Before ANY live pilot, validate the full BFMS pipeline using the 000_Oakport synthetic test entity. This is not a unit test — it is a user-journey smoke test that exercises every WP stage with realistic data. If this test fails, the pilot does not launch.

### 5.2 Test Entities

| Entity | Sector | Bond Target | Location |
|--------|--------|-------------|----------|
| 000_Oakport_Regional_Medical_Center | Healthcare (hospital) | $50,000,000 | `Bond Facility Development/000_Oakport_Regional_Medical_Center/` |
| 000_Oakport_Solid_Waste_Authority | Waste/Environmental | $108,177,500 | `Bond Facility Development/000_Oakport_Solid_Waste_Authority/` |

**Known entity details (from `_docx_manifest.json`):**
- Oakport Regional MC: EIN 15-1234567, NY, hospital_anchor_system archetype
- DSCR 1.503 (2025), unmodified audit opinion, no going concern
- Licensed beds: 425, occupancy 72.9%, case mix 1.52
- Bond counsel engaged: Kuhn Loeb Inc, Resolution RES-2026-501

### 5.3 WP-by-WP Test Checklist

**WP1 — Foundation & Data Contracts:**
- [ ] Create project "000_Oakport_Regional_Medical_Center" in platform
- [ ] Assign `healthcare > hospital` playbook
- [ ] Verify schema paths loaded (68 healthcare paths expected)
- [ ] Confirm schema validation passes for all 13 data primitives
- [ ] Verify role-based access (analyst can edit, viewer cannot)
- [ ] **Expected:** Project entity created with sector=healthcare, archetype=hospital_anchor_system

**WP2 — Artifact Vault & Ingestion:**
- [ ] Upload all 19 Oakport documents (financial statements, legal auth, project description, demographics, KPIs, budget projections, revenue docs, insurance, regulatory, management/governance)
- [ ] Verify each artifact gets SHA-256 hash
- [ ] Verify chunking produces correct page/table units for each document type
- [ ] Confirm immutability (re-upload same file → same hash, no duplicate)
- [ ] Check no waste-sector schema items appear (no `feedstock_supply`, no `tipping_fee`)
- [ ] **Expected:** 19 artifacts, each with chunks, all hashes unique

**WP3 — Controlled Intelligence (Extraction):**
- [ ] Trigger AI extraction pipeline across all 19 artifacts
- [ ] Verify proposed facts are schema-bound (all `schema_path` values in healthcare allowlist)
- [ ] Spot-check 10 proposed facts against source documents for accuracy:
  - [ ] `financials.audit_opinion` = "unmodified" (from audited financial statements)
  - [ ] `financials.by_year.2025.dscr` = 1.503 (from financial data)
  - [ ] `financials.by_year.2025.gross_revenues` ≈ $16.66M
  - [ ] `project.entity_name` = "Oakport Regional Medical Center"
  - [ ] `project.target_bond_amount` = $50,000,000
  - [ ] `operational.licensed_beds` = 425
  - [ ] `operational.occupancy_rate` = 72.9%
  - [ ] `legal.bond_counsel` = "Kuhn Loeb Inc"
  - [ ] `demographic.population` = 425,000
  - [ ] `revenue.payer_mix.medicare` = 42%
- [ ] Bond Strategist reviews full extraction output for domain accuracy
- [ ] Accept majority of facts; reject at least 2 to test rejection workflow
- [ ] Verify provenance chain: each fact → artifact_id → chunk_id → page
- [ ] Verify confidence tiers: CRITICAL facts (DSCR, bond amount) ≥ 0.90, MATERIAL ≥ 0.70
- [ ] **Expected:** ~100-120 extracted facts with full provenance

**WP4 — Deterministic Judgment (Readiness):**
- [ ] Run 19-item deal flow checklist against accepted facts
- [ ] Verify checklist status reflects known completeness of Oakport documents
- [ ] Run 8-dimension readiness scoring:
  - [ ] Financial Strength (2.5x weight): DSCR 1.503 should score well
  - [ ] Revenue Stability (2.0x): Multiple sources documented
  - [ ] Legal & Governance (1.5x): Board resolution exists, bond counsel engaged
  - [ ] Project Readiness (1.5x): $50M expansion, architect + GC selected
- [ ] Verify gap analysis identifies known gaps (permits partially obtained, etc.)
- [ ] Verify gap severity rankings (critical vs important vs supplementary)
- [ ] Confirm no waste-sector readiness items appear
- [ ] **Expected:** Overall readiness score 7.0–8.0 (Selective Engagement range)

**WP5 — Financial & Performance Models:**
- [ ] Run Revenue Projection model against 2021-2025 historical data
  - [ ] Verify 5-year forward projections (2026-2030) using 2.8% revenue growth
  - [ ] Confirm expense escalation at 3.2%
- [ ] Run DSCR Analysis model
  - [ ] Verify historical DSCR trend (should show improvement from 2021 to 2025)
  - [ ] Confirm covenant compliance check against 1.2x minimum
- [ ] Run Sensitivity Analysis (3 scenarios)
  - [ ] Base case: 0% revenue adjustment
  - [ ] Moderate stress: -10% revenue, +5% expenses
  - [ ] Severe stress: -20% revenue, +10% expenses
- [ ] Verify assumption register is populated with source, confidence, sensitivity_impact
- [ ] Confirm determinism: run twice, get identical outputs
- [ ] **Expected:** 3 financial models, all rebuildable, assumption register complete

**WP6 — Warm Handoff Pack Assembly:**
- [ ] Generate Handoff Pack from WP4 + WP5 outputs
- [ ] Verify all 7 sections present:
  1. [ ] Deal Overview (project name, sector, location, EIN, bond amount, readiness score)
  2. [ ] Readiness Report (dimension scores, gaps, severity)
  3. [ ] Checklist Summary (P1-P7 phase status)
  4. [ ] Checklist Items (19 items with evidence counts)
  5. [ ] Financial Tables (5yr historical + 5yr projected + sensitivity)
  6. [ ] Assumptions Log (all assumptions with source and confidence)
  7. [ ] Disclosure Outline (legal doc template placeholders)
- [ ] Export as PDF, DOCX, and Markdown
- [ ] Bond Strategist reviews for:
  - [ ] Domain accuracy (no incorrect sector terminology)
  - [ ] Liability compliance (no recommendations, no deal advice, no approvals)
  - [ ] Professional quality (advisor-ready presentation)
- [ ] Verify legal disclaimers are present in output
- [ ] **Expected:** Complete 7-section deliverable, export-ready

### 5.4 Sensing Tools Validation

Run alongside WP testing to confirm the full tool suite:

- [ ] Generate MIR for healthcare sector, New York geography
- [ ] Verify MIR contains: deal count, median DSCR, par distribution, sub-sector breakdown
- [ ] Run Readiness Assessment with Oakport's profile (use `_sensing_input.json`)
- [ ] Verify readiness score from sensing tool aligns with WP4 readiness score (±0.5)
- [ ] Pull COI Benchmarking for: healthcare, $50M, A+ rating, 25yr maturity
- [ ] Verify Credit Spread Monitor loads current AAA curve + EMMA trades
- [ ] Run batch test with `sensing_test_batch.json` (12 entities)
- [ ] **Expected:** All sensing tools return correct, non-empty results

### 5.5 Cross-Platform Consistency Check

The user noted that "some platform features diverge between website and the muni-pal platform." Verify alignment:

- [ ] Readiness score from muni-pal.io/tools/readiness matches backend `/api/v1/readiness/` output for same inputs
- [ ] COI benchmarking data on website matches backend `/api/v1/sensing/` output
- [ ] Credit Spread Monitor data on website matches backend data (including AAA curve source)
- [ ] MIR data on website matches backend corpus query results
- [ ] Brand voice and terminology consistent between website and platform UI

### 5.6 Pass/Fail

| Criterion | Threshold |
|-----------|-----------|
| WP1-WP6 all complete without errors | Required |
| Bond Strategist domain accuracy review | Approved |
| Sensing tools return correct results | Required |
| Cross-platform consistency | No divergence found |
| Financial models deterministic | Same inputs → same outputs (2 runs) |
| Handoff Pack advisor-ready quality | Bond Strategist approved |

**If ANY criterion fails: FIX and RE-RUN. Do not proceed to live pilot with a failed test.**

---

## 6. Service Delivery Playbook

Each service component gets a standardized operational checklist: trigger, responsible party, inputs, process steps, outputs, quality gate, and handoff.

### 6.1 MIR Delivery (Free Tier)

| Field | Detail |
|-------|--------|
| **Trigger** | Lead enters email + sector + geography on website |
| **Responsible** | Automated (platform) |
| **Inputs** | Sector, geography, optional: deal size range, sub-sector |
| **Steps** | 1. Query EMMA corpus for sector matches → 2. Calculate sector statistics (median DSCR, par distribution, deal count) → 3. Format into MIR template (per BRAND-GUIDELINES.md) → 4. Deliver via email → 5. Log lead in funnel |
| **Output** | PDF/HTML Market Intelligence Report |
| **Quality Gate** | Template-based (automated); quarterly manual review of template accuracy |
| **Handoff** | Lead entered into scoring system; Skool invite sent |
| **Estimated Cost** | $0.50 AI compute + $5 infrastructure = ~$6 per MIR |
| **MA Compliance** | Data vendor activity; historical data only, no interpretation |

### 6.2 Readiness Assessment Delivery (Free Tier)

| Field | Detail |
|-------|--------|
| **Trigger** | Lead self-serves on muni-pal.io/tools/readiness |
| **Responsible** | Automated (platform) |
| **Inputs** | Sub-sector selection, 167 yes/no/partial responses, optional financial metrics |
| **Steps** | 1. User completes assessment → 2. Score against sector framework → 3. Generate gap summary → 4. Show comparison to sector benchmarks → 5. Offer full report (email capture) |
| **Output** | Readiness score + gap summary + benchmark comparison |
| **Quality Gate** | Automated (deterministic scoring) |
| **Handoff** | Lead scored; if score > 60, direct outreach triggered |
| **Estimated Cost** | $0.25 AI compute = ~$0.25 per assessment |
| **MA Compliance** | Descriptive framework from historical OS data, not prescriptive |

### 6.3 Credit Memo + Gap Analysis (Tier 1: Diagnostic)

| Field | Detail |
|-------|--------|
| **Trigger** | Tier 1 engagement signed, documents received |
| **Responsible** | Bond Strategist (primary), CTO (platform support) |
| **Inputs** | Client documents (uploaded to artifact vault), playbook selection, client profile |
| **Steps** | 1. Onboarding package delivered (§4.2) → 2. Document request checklist sent → 3. Client uploads documents to vault (WP2) → 4. AI extraction runs (WP3) → 5. Bond Strategist reviews proposed facts (accept/reject/flag) → 6. Readiness scoring runs (WP4) → 7. Gap analysis generated → 8. Bond Strategist writes credit memo narrative → 9. Comparable deal structures queried from corpus → 10. Timeline estimate generated from benchmarks → 11. Full report assembled and reviewed → 12. Report delivered to client |
| **Output** | Credit memo (30-50 pages): readiness assessment, DSCR analysis, debt capacity estimate, peer comparison, gap analysis, comparable structures, actionable timeline |
| **Quality Gate** | Bond Strategist sign-off on report. CEO reviews before first 3 deliveries. |
| **Handoff** | Report delivered to client; post-delivery debrief scheduled (30 min) |
| **Delivery Timeline** | 3 weeks from document receipt |
| **Estimated Cost** | 15-25 hours Bond Strategist ($2,250-3,750) + $15-25 AI compute + $10 infra = $2,300-3,800 |
| **MA Compliance** | Observations and historical data, not recommendations. "Here is what comparables had" not "here is what you need." |

### 6.4 Active Deal Coordination (Tier 2: Standard)

| Field | Detail |
|-------|--------|
| **Trigger** | Tier 2 engagement signed, deal team assembled |
| **Responsible** | CEO (point of contact), Bond Strategist (domain), CTO (platform) |
| **Inputs** | Everything from Tier 1 + deal team contacts (UW, counsel, MA), deal timeline |
| **Steps** | 1. All Tier 1 steps completed → 2. Deal coordination workspace activated → 3. Milestone tracking configured from comparable deal timeline → 4. Information request routing configured (borrower ↔ UW/counsel/MA) → 5. Weekly status updates to client → 6. Platform alerts when milestones lag benchmarks → 7. COI benchmarking run (statistical ranges, not deal-specific) → 8. Post-deal report generated (timeline comparison, COI comparison) |
| **Output** | Ongoing coordination + milestone tracking + post-deal report |
| **Quality Gate** | Weekly check-in with client; Bond Strategist reviews all outgoing materials |
| **Handoff** | Post-deal report delivered within 30 days of close |
| **Delivery Timeline** | Duration of deal (typically 12-20 weeks) |
| **Estimated Cost** | 40-80 hours labor ($6,000-12,000) + $5-10 AI compute + $20/mo infra |
| **MA Compliance** | Document routing and project management only. NEVER draft/edit borrower responses. NEVER advise on structure, terms, timing, sale method. If borrower asks timing question: "That's a question for your MA." |

### 6.5 Gap Remediation Support (Tier 3: Accelerator)

| Field | Detail |
|-------|--------|
| **Trigger** | Tier 3 engagement signed, gap analysis completed |
| **Responsible** | Bond Strategist (primary), CEO (relationship) |
| **Inputs** | Gap analysis from WP4, client's organizational context |
| **Steps** | 1. All Tier 2 steps active → 2. Gap remediation roadmap created from gap analysis → 3. Work with client to close documentation gaps (organizational/coordination tasks) → 4. UW benchmarking data access activated (historical UW performance: spread, volume, specialization as self-serve dataset) → 5. Timeline optimization alerts enabled → 6. Extended post-deal analysis: full COI line-item analysis, timeline milestone comparison, next-deal recommendations |
| **Output** | Remediation roadmap + ongoing support + extended post-deal analysis |
| **Quality Gate** | Bond Strategist reviews all remediation work; CEO reviews any materials that could cross advisory boundary |
| **Delivery Timeline** | Duration of deal (typically 16-24 weeks) |
| **Estimated Cost** | 60-100 hours labor ($9,000-15,000) + $10-15 AI compute + $25/mo infra |
| **MA Compliance** | HIGHEST RISK TIER. Remediation must be narrowly scoped to organizational/coordination tasks. Never strategic advice. Gap impact framed as "historical cost ranges in comparables" not "what this will cost you." UW data is raw self-serve dataset; Launch Shop does NOT interpret. |

### 6.6 Partner Infrastructure Services

| Field | Detail |
|-------|--------|
| **Trigger** | Custom agreement signed |
| **Responsible** | CTO (implementation), CEO (relationship), Implementation Architect |
| **Inputs** | Client's infrastructure requirements, integration specifications |
| **Steps** | 1. Requirements scoping → 2. Architecture design for client's environment → 3. Infrastructure deployment (BFMS instance) → 4. Integration with client's existing systems (ERP, treasury, board reporting) → 5. Data migration if applicable → 6. Training and documentation → 7. Ongoing operation and monitoring → 8. Quarterly business reviews |
| **Output** | Running BFMS instance in client's environment + integrations + ongoing support |
| **Quality Gate** | Acceptance testing with client; SLA compliance |
| **Delivery Timeline** | 2-4 months for deployment; ongoing for operation |
| **Estimated Cost** | 200-400 hours implementation ($25,000-50,000) + ongoing ops ($5K-15K/month) |
| **MA Compliance** | Technology vendor relationship. Platform provides tools; client's MA provides advice. Written vendor agreement, not engagement letter. |

---

## 7. Monitoring & Measurement

### 7.1 Pilot Measurement Integration

This section does NOT duplicate the measurement protocol — it specifies operational integration points.

**Task Log (Protocol §4.1):**
- Location: `pilot/{client}/task-log.md` (or database if infrastructure is built)
- Every platform-performed task logged with: timestamp, task type, WP stage, time spent
- Counterfactual annotation: "Would otherwise be done by [MA/counsel/CFO/staff]"
- Annotation ownership: Bond Strategist does initial annotation, CEO does weekly QC
- Weekly QC cadence: Monday morning, 30 minutes

**Hours Diary (Protocol §4.2):**
- Template: 5-minute weekly form sent to client Friday afternoon
- Compliance risk: Degrades after week 4; plan for missing weeks
- Reminder: Automated via Executive Assistant agent (weekly Friday 2pm)
- If 2 consecutive weeks missed: CEO direct follow-up

**Milestone Timestamps (Protocol §4.3):**
- Every deal milestone (engagement → POS → rating → roadshow → pricing → close)
- Logged as platform events when they occur
- Compared against baseline deal milestones from interview

**COI Line Items (Protocol §4.4):**
- Captured line-by-line from closing memo after close
- Compared against frozen prediction from Track 2 COI model
- This is the first true out-of-sample v2 test — do NOT fold into training set until post-mortem

### 7.2 KPI Dashboard

| KPI | Source | Target (6 months) | Cadence |
|-----|--------|--------------------|---------|
| Free tool leads (MIR + Readiness + Credit Spreads) | Website analytics | 50/month by M3 | Weekly |
| Skool community members | Skool dashboard | 200 by M6 | Weekly |
| Qualified leads (score > 60) | Lead scoring | 10/month by M3 | Weekly |
| Paid conversions (any tier) | CRM / payment system | 3 by M6 | Monthly |
| Subscription revenue (ARR) | Payment system | $60K ARR by M6 (3 × $20K) | Monthly |
| Pilot completion rate | Internal tracking | 100% | Per pilot |
| Pilot outcome (GREEN/AMBER/WITHDRAWN) | Measurement protocol | GREEN for pilot #1 | Post-pilot |
| Platform uptime | Infrastructure monitoring | 99.5% | Daily |
| Extraction accuracy (WP3 accept rate) | Platform metrics | >90% | Weekly during pilot |
| Client satisfaction (NPS proxy) | Post-delivery survey | >8/10 | Per engagement |
| COI model accuracy (Track 2) | Model validation | <$2.10/1000 MAE on investment-grade hospital | Post-Track 2 |

### 7.3 Demand Signals (per Amendment #1)

The pilot's primary purpose is demand discovery, not productivity measurement. Track these signals explicitly:

| Signal | Measurement | GREEN | AMBER | WITHDRAWN |
|--------|-------------|-------|-------|-----------|
| Repeat engagement | Adventist signs deal #2 before deal #1 closes | YES | — | — |
| Reference provided | Written reference for peer outreach | YES | — | — |
| Peer introduction | Adventist introduces another health system | YES | — | — |
| Satisfaction expressed | Verbal or written satisfaction, no repeat commitment | — | YES | — |
| Disengagement | Client pulls out or completes without endorsement | — | — | YES |

**Decision rules (from measurement protocol Amendment #1):**
- GREEN: Any one of the three GREEN signals → pilot validates demand
- AMBER: Deal completes, satisfaction expressed, no repeat signal → informational
- WITHDRAWN: Disengagement at any stage → do NOT publish externally

> **Internal note:** Productivity data (task log, hours diary, milestones) is still collected but downgraded to informational-only for pilot #1. It becomes decision-rule-bearing starting with pilot #2.

---

## 8. Pricing & Tier Management

### 8.1 Pricing Model Reconciliation

Two pricing models now coexist and are **complementary, not conflicting:**

| Model | What it is | When it applies | Price |
|-------|-----------|-----------------|-------|
| **Subscription** | Ongoing platform access (sensing tools, readiness, COI benchmarks, basic risk reporting, advisor agent access, report exports) | Between deals; ongoing value even when not in an active engagement | $20,000/year or $2,000/month |
| **Per-Engagement** | Service delivery for a specific bond deal (diagnostic, coordination, or acceleration) | When a client has an active deal they want to run through the BFMS | Tiered: $15K-25K / $40K-50K / $75K+ |

**Annual vs Monthly:**
- Monthly: $2,000/month = $24,000/year
- Annual: $20,000/year = 17% discount vs monthly
- Annual discount incentivizes commitment and improves cash flow predictability

**How they combine:**
- A client can be subscription-only (no active deal, using platform tools)
- A client on Tier 1+ engagement includes subscription in the engagement price
- A client who completes a Tier 2 engagement can downgrade to subscription-only between deals
- Subscription is the "floor" — every paying client has at least this

### 8.2 Full Price Card

| Tier | Access | Price | Billing | Includes Subscription? |
|------|--------|-------|---------|----------------------|
| Free | MIR, Readiness Scan, Credit Spread Monitor (read-only) | $0 | — | No |
| Subscription | Platform access per toggle matrix §1.2 | $20,000/yr or $2,000/mo | Annual or monthly | Yes (is subscription) |
| Tier 1: Diagnostic | Subscription + credit memo + gap analysis + comparable structures | $15,000–$25,000 one-time | On engagement | Yes |
| Tier 2: Standard | Subscription + Tier 1 + active deal coordination + COI benchmarking + milestone tracking | $40,000–$50,000 per deal | On engagement | Yes |
| Tier 3: Accelerator | Subscription + Tier 2 + gap remediation + UW benchmarking + timeline optimization + extended post-deal | $75,000+ per deal | On engagement | Yes |
| Partner | Everything + infrastructure install + ongoing operation + custom integrations | Custom ($100K+) | Project + retainer | Yes |

**Per-engagement price drivers (from existing docs/three-tier-pricing-structure.md):**
- Tier 1: WTP-based by par size (sub-$25M: $15K / $25-75M: $20K / $75M+: $25K)
- Tier 2: Deal complexity (single-series refunding: $40K / new money moderate: $45K / multi-series complex: $50K)
- Tier 3: Par size ($50-100M: $75K / $100-200M: $100K / $200M+: $125K+)

### 8.3 Pilot Pricing

**Decision required before pilot kickoff (Gate C1):**

| Option | Pros | Cons | Engagement Letter Impact |
|--------|------|------|-------------------------|
| Free (original plan) | Lowest friction; measurement-rights-as-consideration framing intact | No revenue signal; may attract non-serious participants | Current §2 works as-is |
| Discounted (30-50% off) | Revenue signal; tests willingness to pay; some cash flow | May create price anchoring below target | §2 must be rewritten with actual fee |
| Full price ($20K subscription) | True market test; validates pricing; no discount to unwind later | Higher friction; Adventist may balk; engagement letter §2 rewrite required | §2 completely rewritten |

> **CEO's stated preference:** Charge pilot participants. "If we can solve Muni-Pal's bugs ahead of time, we don't have to work for free."
>
> **Consideration:** If charging, the measurement-rights-as-consideration framing in the engagement letter (§2 "Launch Shop absorbs costs for chance to work on real deal") must be replaced with a standard commercial framing. The measurement instrumentation becomes a service improvement mechanism, not the consideration for free work.

### 8.4 Feature Augmentation Path

How tiers escalate during an active client relationship:

```
Subscription ($20K/yr)
    │
    ├── Client requests credit analysis for upcoming deal
    │   └── Upgrade to Tier 1: Diagnostic (+$15-25K)
    │       ├── Scope addendum to engagement letter
    │       ├── Feature toggles updated per §1.2
    │       └── Document request list sent
    │
    ├── Client wants active deal coordination
    │   └── Upgrade to Tier 2: Standard ($40-50K total, includes Tier 1 deliverables)
    │       ├── New engagement letter or scope amendment
    │       ├── Dedicated point of contact assigned
    │       ├── Feature toggles updated
    │       └── Weekly status cadence begins
    │
    ├── Client needs gap remediation support
    │   └── Upgrade to Tier 3: Accelerator ($75K+ total, includes Tier 1+2 deliverables)
    │       ├── Expanded engagement letter with remediation scope
    │       ├── Feature toggles updated
    │       └── Extended timeline confirmed
    │
    └── Deal closes → Client returns to Subscription tier
        ├── Per-engagement features deactivated
        ├── Subscription features retained
        └── Post-deal report delivered (if Tier 2+)
```

**Downgrade process:**
1. Engagement complete (deal closed or terminated per §6)
2. Post-deal deliverables completed (if applicable)
3. CTO deactivates engagement-tier features in toggle system
4. Client retains subscription-tier access
5. Next annual/monthly renewal continues at subscription rate

---

## 9. Skool Community Integration

### 9.1 Purpose

Skool.com serves as the middle-of-funnel nurture environment. It sits between "used a free tool" and "signed an engagement." It is where operators learn what the BFMS can do, see evidence of its value, and build confidence to commit.

### 9.2 Community Setup

| Setting | Value |
|---------|-------|
| Community name | Bond Finance Management System (BFMS) |
| URL | skool.com/bfms (or skool.com/muni-pal) |
| Access | Free to join (captures email + organization affiliation) |
| Moderation | CEO + CBO; weekly review of all posts |
| Brand voice | Per BRAND-GUIDELINES.md: professional, evidence-based, no jargon without explanation |

### 9.3 Content Pillars

| Pillar | Description | Example Content | Frequency |
|--------|-------------|-----------------|-----------|
| **BFMS Education** | What the 6 WP stages do, explained for operators who've never seen this | "What Happens When You Upload Documents to BFMS" (WP2→WP3 explainer) | 2/month |
| **Market Intelligence** | Weekly credit spread digests, sector outlooks, notable deals | "Healthcare Bond Market This Week: What AAA Spreads Tell You" | Weekly |
| **Deal Prep Playbooks** | How to prepare for your next issuance, organized by sub-sector | "Hospital Bond Readiness: The 10 Documents That Matter Most" | 1/month |
| **COI Transparency** | Anonymized benchmarking data, "what good looks like" | "What Did Healthcare Borrowers Actually Pay in 2025? (866 Deals Analyzed)" | Monthly |
| **Peer Discussion** | Operator-to-operator Q&A, moderated | Open threads: "What surprised you about your last issuance?" | Ongoing |

### 9.4 Funnel Integration

```
Website free tools ──> Email capture ──> Automated Skool invite
                                              │
Skool engagement ──> Lead scoring (+20 join, +15 engagement)
                                              │
Score > 60 ──> Direct outreach (CEO or Bond Strategist)
                                              │
Discovery call ──> Baseline interview ──> Engagement letter ──> Onboarding
```

**Specific automation steps:**
1. When lead captures email via any free tool → send Skool community invite (automated)
2. When Skool member engages with 3+ posts → add +15 to lead score
3. When Skool member asks deal-specific question → flag for CEO review (may indicate readiness for direct outreach)
4. When lead score > 60 → CRM alert to CEO for personalized outreach
5. Skool members get early access to new sensing tool features (beta testers)

### 9.5 Content Calendar Template (First Month)

| Week | Content | Pillar | CTA |
|------|---------|--------|-----|
| 1 | "What is a Bond Facility Management System?" explainer | BFMS Education | Try the free Readiness Assessment |
| 1 | Welcome post: community guidelines, what to expect | Community | Introduce yourself |
| 2 | Weekly credit spread digest #1 | Market Intel | Visit the Credit Spread Monitor |
| 2 | "5 Documentation Gaps That Delay Healthcare Deals" | Deal Prep | Download the checklist |
| 3 | Healthcare COI benchmarking snapshot (anonymized) | COI Transparency | Run your own COI benchmark |
| 3 | AMA thread: "Ask a Bond Strategist" (Bond Strategist answers) | Peer Discussion | Post your question |
| 4 | "How BFMS Extraction Works: From PDF to Evidence" (WP3 explainer) | BFMS Education | See a demo |
| 4 | Weekly credit spread digest #2 | Market Intel | Compare your issuer's cost structure |

### 9.6 Compliance & Moderation

- **No specific deal advice in the community.** All content is educational, historical, or descriptive. If a member asks "should we issue now?" the answer is always: "That's a question for your municipal advisor. Here's what the historical data shows..."
- **No identification of specific borrowers or deals** unless publicly available (EMMA data)
- **All content reviewed against engagement letter §1 scope boundaries** before posting
- **Community guidelines posted on join:** This is an educational community, not an advisory service. Launch Shop is not a registered municipal advisor.
- **Bond Strategist review:** All data-containing posts reviewed by Bond Strategist for domain accuracy before publication
- **CBO review:** All marketing-adjacent content reviewed for brand consistency

---

## 10. Sequencing & Dependencies

### 10.1 Critical Path to Pilot Launch

Based on Bond Strategist's cross-document analysis (docs/bond-strategist-pilot-review.md §6), here is the sequenced critical path. Items that can run in parallel are marked.

```
WEEK 1-2: LEGAL
├── [L1] Send counsel briefing ──────────────────────────────────────> [L2] Receive opinion
│                                                                       │
│   PARALLEL TRACK A: PLATFORM                                         │
│   ├── [P1] Run 000_Oakport end-to-end test (§5)                     │
│   ├── Fix any failures from test                                     │
│   └── [P3] Bond Strategist validates synthetic outputs               │
│                                                                       │
│   PARALLEL TRACK B: SKOOL + CONTENT                                  │
│   ├── Set up Skool community                                         │
│   ├── Create first month of content                                  │
│   └── Configure lead scoring system                                  │
│                                                                       │
│   PARALLEL TRACK C: COI MODEL (Track 2)                              │
│   ├── Feature extraction (Days 1-3)                                  │
│   ├── Model refit + walk-forward CV (Day 4)                          │
│   └── Model card + marketing language (Days 5-6)                     │
│                                                                       │
WEEK 2-3: ENGAGEMENT                                                    │
├── [L3-L5] Counsel opinion received ──> Finalize engagement letter    │
├── [E2] Confirm Adventist's MA on this deal                           │
├── [E3-E4] Notify MA + UW of Launch Shop's role                      │
├── [E5] Obtain MA written acknowledgment                              │
│   (14-day window per engagement letter §7)                           │
├── [E6] Sign engagement letter                                        │
│                                                                       │
WEEK 3-4: BASELINE                                                      │
├── [M2] Conduct baseline interview                                    │
│   (after engagement letter signed)                                   │
├── [M3] File baseline data                                            │
├── [M4] File frozen predictions (COI from Track 2, timeline, hours)   │
├── [M5-M7] Activate measurement infrastructure                        │
│                                                                       │
WEEK 4: PRICING + ONBOARDING                                           │
├── [C1-C5] Pricing decision finalized                                 │
├── [§4.2] Generate onboarding package via client-launch-protocol      │
├── [§4.3] Run feature activation checklist for assigned tier          │
│                                                                       │
WEEK 4-5: LAUNCH                                                        │
├── ALL §2 gates verified GREEN                                        │
├── Pilot kickoff                                                       │
└── Week 1 hours diary reminder sent                                   │
```

### 10.2 Parallel Work Streams (Do Not Gate on Pilot)

These are valuable regardless of pilot timing:

| Work Stream | Owner | Timeline | Dependencies |
|-------------|-------|----------|--------------|
| Skool community setup + content | CBO + Bond Strategist | 2 weeks | None |
| Pricing page implementation (LAU-324) | CTO | 1 week | Pricing decision from CEO |
| COI model upgrade (Track 2) | Bond Strategist | 5-8 working days | None |
| Lead notification + email sequence (LAU-322) | CTO | 1 week | None |
| Feature toggle system build | CTO | 2 weeks | Toggle matrix from §1.2 |
| Outreach templates launch (LAU-76) | CBO | Pending Board approval | Board decision |

### 10.3 Post-Pilot Sequence

After pilot completes:

1. **Day 1-3:** Collect final data (closing COI line items, final milestone timestamps)
2. **Day 3-7:** Post-deal interview with Adventist (30 min per engagement letter §4)
3. **Day 7-14:** Internal post-mortem memo (CEO + Bond Strategist)
   - Compare outcomes to frozen predictions
   - Assess demand signals (GREEN/AMBER/WITHDRAWN)
   - Document actual labor, AI compute, and infra costs (per Internal Cost Memo template)
4. **Day 14:** Decision: publish external case study? (Only if GREEN/AMBER AND Adventist written consent)
5. **Day 14-30:** Calibrate pricing based on actual cost data
6. **Day 14-30:** Calibrate feature toggle matrix based on what client actually used
7. **Day 30:** Begin pilot #2 recruitment from Skool community + lead pipeline

---

## Appendix A: Quick-Reference Checklists

### A.1 New Client Onboarding (Condensed)

- [ ] Classify: operator or agency (§4.1)
- [ ] Assign tier based on deal complexity and baseline interview signal (§4.1)
- [ ] Confirm registered MA exists on deal (§4.1 Step 3)
- [ ] Generate onboarding package via client-launch-protocol (§4.2)
- [ ] Bond Strategist reviews package (15 min)
- [ ] Deliver package + engagement letter
- [ ] Create project in platform
- [ ] Run feature activation checklist for tier (§4.3)
- [ ] Send document request checklist
- [ ] Schedule kick-off call
- [ ] Add to KPI tracking (§7.2)

### A.2 Weekly Pilot Operations

- [ ] Review task log entries from past week (Bond Strategist)
- [ ] QC counterfactual annotations (CEO — 30 min Monday)
- [ ] Check hours diary compliance (did client submit?)
- [ ] Log any deal milestones that occurred
- [ ] Review platform for domain errors in outputs
- [ ] Update lead scoring for any new leads
- [ ] Post weekly Skool content (per content calendar)
- [ ] Send credit spread digest to Skool (if week's content)

### A.3 Monthly Business Review

- [ ] Review KPI dashboard (§7.2)
- [ ] Review lead funnel: total leads, qualified leads, conversions
- [ ] Review Skool engagement metrics
- [ ] Review platform uptime and error rates
- [ ] Review AI compute costs vs budget
- [ ] Review extraction accuracy rate
- [ ] Update platform readiness status (§1.3)
- [ ] Plan next month's Skool content
