# Muni-Pal Internal Cost & Automation Memo

**Status:** Draft v1.0
**Date:** 2026-04-09
**Owner:** CEO + CTO
**Classification:** INTERNAL ONLY — do not share with clients, prospects, or external partners
**Purpose:** Identify cost drivers across labor, AI compute, and infrastructure for every Muni-Pal service component. Recommend where to automate, where to focus labor, and how to configure flat-fee services based on actual cost structure.

---

## 1. Cost Model Framework

### 1.1 Three Cost Dimensions

Every service component is costed across three dimensions:

| Dimension | What It Includes | How Measured | Key Driver |
|-----------|-----------------|--------------|------------|
| **Labor** | Bond Strategist time, CEO time, CTO/Engineer time, Implementation Architect time | Hours × blended rate | Human expertise that cannot be automated without degrading quality or creating regulatory risk |
| **AI Compute** | Claude API calls for extraction, chat, analysis, report generation | Input/output tokens × API pricing | Volume of documents processed and complexity of analysis |
| **Infrastructure** | Hosting (FastAPI, React, PostgreSQL, Redis, Celery), storage (S3/local), scraping infra (EMMA crawler), monitoring | Monthly fixed costs + per-unit variable | Scales with number of clients and data volume |

### 1.2 Blended Rate Assumptions

| Role | Estimated Hourly Cost (Fully Loaded) | Notes |
|------|--------------------------------------|-------|
| CEO | $200/hr | Opportunity cost; this is what CEO time is worth, not what we pay |
| Bond Strategist | $150/hr | Domain expertise; the scarcest and most valuable labor |
| CTO / Engineer | $125/hr | Platform development and maintenance |
| Implementation Architect | $125/hr | System design and integration |
| CBO | $100/hr | Brand, content, community management |
| Executive Assistant (AI) | $0/hr | Paperclip agent; compute cost only |

### 1.3 AI Compute Pricing Reference

Current model: Claude Sonnet 4 (claude-sonnet-4-20250514)

| Operation | Input Cost | Output Cost |
|-----------|-----------|-------------|
| Standard API call | $3.00 / 1M input tokens | $15.00 / 1M output tokens |
| Extended thinking | Same input | Same output (thinking tokens billable) |

If extraction quality requires upgrade to Claude Opus: costs increase approximately 5x. Current architecture uses Sonnet for all extraction and advisory operations.

---

## 2. Per-Component Cost Analysis

### 2.1 Component Cost Matrix

Estimated costs per single client engagement at each component. These are estimates based on platform architecture and expected usage; the Adventist pilot will provide actual data to calibrate.

| # | Component | Labor (hrs) | Labor Cost | AI Compute | Infra (per engagement) | Total Cost | Automation Potential |
|---|-----------|-------------|------------|------------|----------------------|------------|---------------------|
| 1 | **MIR Generation** | 0.5 (QC) | $75 | $0.50 | $5 | **$81** | **HIGH** |
| 2 | **Readiness Scan (self-serve)** | 0 | $0 | $0.25 | $2 | **$2** | **ALREADY AUTOMATED** |
| 3 | **Credit Spread Monitor** | 2/month (data QC) | $250/mo | $0 (deterministic) | $20/mo | **$270/mo** | **HIGH** |
| 4 | **COI Benchmarking** | 1 (review) | $150 | $1 | $5 | **$156** | **MEDIUM** |
| 5 | **Full Readiness Assessment** | 0.5 (review) | $75 | $0.50 | $5 | **$81** | **HIGH** |
| 6 | **Credit Memo + Gap Analysis (T1)** | 15–25 | $2,250–3,750 | $15–25 | $10 | **$2,275–3,785** | **LOW** |
| 7 | **AI Extraction Pipeline (WP3)** | 8–15 (review) | $1,200–2,250 | $10–40 | $10 | **$1,220–2,300** | **MEDIUM** |
| 8 | **Financial Models (WP5)** | 5–10 | $750–1,500 | $5–10 | $5 | **$760–1,515** | **MEDIUM** |
| 9 | **Handoff Pack Assembly (WP6)** | 3–5 | $450–750 | $5 | $5 | **$460–760** | **HIGH** |
| 10 | **Active Deal Coordination (T2)** | 40–80 | $6,000–12,000 | $5–10 | $60 (3 months) | **$6,065–12,070** | **LOW** |
| 11 | **Advisory Packages** | 10–20 | $1,500–3,000 | $3–5 | $10 | **$1,513–3,015** | **MEDIUM** |
| 12 | **Advisor Agent (Claude chat)** | 2 (monitoring) | $300 | $5–20 | $10 | **$315–330** | **HIGH** |
| 13 | **Document Mgmt + VDR** | 5–10 (setup) | $625–1,250 | $0 | $30 | **$655–1,280** | **HIGH** |
| 14 | **Info Request Routing** | 10–30 | $1,500–4,500 | $2–5 | $10 | **$1,512–4,515** | **MEDIUM** |
| 15 | **Gap Remediation Support (T3)** | 60–100 | $9,000–15,000 | $10–15 | $75 (4 months) | **$9,085–15,090** | **LOW** |
| 16 | **Disclosure Tracking** | 2 (setup) | $300 | $0 | $10 | **$310** | **HIGH** |
| 17 | **Risk Reporting** | 1 (review) | $150 | $2 | $5 | **$157** | **HIGH** |
| 18 | **Report Export (PDF/Excel)** | 0.5 | $75 | $1 | $2 | **$78** | **HIGH** |
| 19 | **Legal Templates** | 2 (customize) | $300 | $3 | $2 | **$305** | **MEDIUM** |
| 20 | **Revenue Diversification Analysis** | 0.5 | $75 | $1 | $2 | **$78** | **HIGH** |

### 2.2 AI Compute Cost Detail

| Operation | Est. Tokens (Input + Output) | Cost Per Run | Frequency Per Engagement | Notes |
|-----------|------------------------------|-------------|--------------------------|-------|
| Document extraction (WP3) — per artifact | 50K–200K | $0.50–$2.00 | 10–30 artifacts per project | Largest AI cost; scales linearly with document volume |
| Readiness scoring | 10K–30K | $0.10–$0.30 | 1 per assessment | Light compute |
| Advisor Agent — per conversation turn | 5K–50K | $0.05–$0.50 | 10–50 turns per engagement | Variable; depends on client usage |
| MIR generation | 20K–40K | $0.20–$0.40 | 1 per report | Template-heavy, low compute |
| Handoff Pack narrative sections | 30K–60K | $0.30–$0.60 | 1 per pack | Could be deterministic with templates |
| Financial model assumptions extraction | 15K–30K | $0.15–$0.30 | 1 per model run | Moderate |
| Gap analysis narrative | 10K–25K | $0.10–$0.25 | 1 per analysis | Light |

**Total estimated AI compute cost per full engagement (Tier 2):** $30–$80

This is a negligible cost relative to the $40K–$50K engagement price. AI compute is NOT a scaling constraint.

### 2.3 Infrastructure Cost Baseline

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| PostgreSQL (managed) | $50–100 | Scales with data volume; current usage is light |
| Redis (managed) | $15–30 | Celery broker + caching |
| FastAPI hosting (1 instance) | $25–50 | Uvicorn workers; may need scaling at 20+ concurrent clients |
| React frontend (Vercel) | $0–20 | Free tier sufficient initially; Pro at $20/mo for custom domains |
| Celery worker (1 instance) | $25–50 | Async extraction, deliverable generation, notifications |
| S3/storage | $5–20 | Per GB; grows with document volume |
| EMMA scraping infra | $10–20 | Playwright browser automation; runs weekly |
| Domain + SSL | $15/mo | muni-pal.io |
| Monitoring/logging | $0–25 | Structured logging; Vercel Analytics |
| **Total baseline** | **$145–$330/mo** | Before any client-specific costs |

**Per-client incremental infrastructure:** ~$10–$30/month (storage, compute, database rows)

**Bottom line:** At $20K/year subscription pricing, infrastructure cost per client is approximately $150–$360/year — less than 2% of revenue. Infrastructure is NOT a scaling constraint.

---

## 3. What Costs the Most (Ranked)

### 3.1 Most Expensive Components by Total Cost

Ranking by total estimated cost per engagement:

| Rank | Component | Total Cost Range | Primary Driver | Tier |
|------|-----------|-----------------|----------------|------|
| 1 | **Gap Remediation Support** | $9,085–$15,090 | Bond Strategist labor (60–100 hrs) | Tier 3 |
| 2 | **Active Deal Coordination** | $6,065–$12,070 | CEO + Bond Strategist labor (40–80 hrs) | Tier 2 |
| 3 | **Credit Memo + Gap Analysis** | $2,275–$3,785 | Bond Strategist labor (15–25 hrs) | Tier 1 |
| 4 | **Info Request Routing** | $1,512–$4,515 | Labor coordination (10–30 hrs) | Tier 2 |
| 5 | **AI Extraction Pipeline** | $1,220–$2,300 | Bond Strategist review (8–15 hrs) + AI compute | Tier 1+ |
| 6 | **Advisory Packages** | $1,513–$3,015 | Deal coordination labor (10–20 hrs) | Tier 2 |
| 7 | **Financial Models** | $760–$1,515 | Domain expertise (5–10 hrs) | Tier 1+ |
| 8 | **Document Mgmt + VDR** | $655–$1,280 | Setup labor (5–10 hrs) | Tier 2+ |

**The pattern is clear:** Labor is the dominant cost in every expensive component. AI compute and infrastructure are negligible by comparison.

### 3.2 Most Expensive by Cost Driver

**Labor-intensive (>10 hours per engagement):**
- Gap Remediation Support: 60–100 hrs → Bond Strategist is the bottleneck
- Active Deal Coordination: 40–80 hrs → CEO + Bond Strategist
- Credit Memo: 15–25 hrs → Bond Strategist
- Info Request Routing: 10–30 hrs → coordination labor
- AI Extraction Review: 8–15 hrs → Bond Strategist reviewing proposed facts

**AI compute-intensive:**
- AI Extraction Pipeline: $10–$40 per engagement (10–30 docs × $0.50–$2.00 each)
- Advisor Agent: $5–$20 per engagement (depends on client usage)
- Everything else: <$5 per run

**Infrastructure-intensive:**
- Credit Spread Monitor: $20/mo (scraping + data pipeline)
- Document Mgmt + VDR: $30/mo (storage, versioning, access control)
- Everything else shares baseline infrastructure

### 3.3 The Bond Strategist Bottleneck

The Bond Strategist is involved in the highest-cost activities at every tier:

| Activity | Bond Strategist Hours | Tier |
|----------|----------------------|------|
| WP3 extraction fact review | 8–15 | Tier 1+ |
| Credit memo writing | 10–15 | Tier 1 |
| Domain accuracy QA | 3–5/week | All |
| Deal coordination oversight | 5–10/week | Tier 2 |
| Gap remediation work | 20–40 | Tier 3 |
| Task log annotation (pilot) | 3–5/week | Pilot |
| Content creation (Skool/blog) | 2–4/week | All |

**Total Bond Strategist capacity needed per active engagement:**
- Tier 1: ~20–30 hours over 3 weeks
- Tier 2: ~10–15 hours/week for 12–20 weeks
- Tier 3: ~15–20 hours/week for 16–24 weeks

**At current staffing (1 Bond Strategist):**
- Can support: 2–3 Tier 1 diagnostics simultaneously, OR 1 Tier 2 + 1 Tier 1, OR 1 Tier 3 alone
- Cannot support: 2+ Tier 2 engagements simultaneously without hiring

This is the binding constraint for scaling beyond 3–5 paying clients.

---

## 4. Automation & Self-Service Recommendations

### 4.1 Automate to Zero Labor (Target: No Human Touch Per Engagement)

These components should run without any human involvement per client interaction:

| Component | Current State | Target State | Investment Needed | Expected Savings |
|-----------|--------------|--------------|-------------------|-----------------|
| MIR Generation | Mostly automated, manual QC | Fully automated with template validation suite | Build template QA test suite (1 week CTO) | Eliminate 0.5 hr/report |
| Readiness Scan | Already self-serve | Maintain | None | Already $0 labor |
| Credit Spread Monitor | Manual weekly data QC | Automated scraping + anomaly detection alerts | Scraping reliability work + alert rules (2 weeks CTO) | Reduce from 2 hrs/week to 0.5 hrs/week (exception-only) |
| Advisor Agent | Working but unmonitored | Self-serve with guardrail prompts + weekly audit | Guardrail prompt engineering + audit dashboard (2 weeks CTO) | Enable self-serve; reduce monitoring to 30 min/week |
| Handoff Pack Assembly | Semi-automated from pipeline | Fully automated: WP4+WP5 outputs → Pack with zero manual steps | Rendering pipeline hardening + template finalization (1 week CTO) | Eliminate 3–5 hrs/pack |
| Onboarding Package | client-launch-protocol skill (manual trigger) | Automated trigger on engagement signing (webhook → skill → ZIP → email) | Webhook integration (2 days CTO) | Eliminate 1 hr/client onboarding |
| Report Export | Manual trigger, some formatting issues | One-click export with guaranteed formatting | PDF/Excel template fixes (3 days CTO) | Eliminate 0.5 hr/export |
| Disclosure Tracking | Manual setup per client | Auto-configured from project creation | Integration work (1 week CTO) | Eliminate 2 hrs/client |
| Risk Reporting | Manual trigger + review | Auto-generated, flagged only if anomalous | Anomaly detection rules (3 days CTO) | Eliminate 1 hr/client |
| Revenue Diversification | Manual trigger | Auto-generated from financial data upload | Pipeline integration (2 days CTO) | Eliminate 0.5 hr/client |

**Total automation investment:** ~8–10 weeks of CTO/Engineer time
**Total labor savings:** ~10–15 hours per Tier 1 engagement, ~15–25 hours per Tier 2 engagement

### 4.2 Partially Automate (Reduce Labor But Retain Human Quality Gate)

These components have automatable portions but require human judgment for quality or regulatory reasons:

| Component | Automatable Portion | Human-Required Portion | Why Human Required |
|-----------|--------------------|-----------------------|-------------------|
| AI Extraction (WP3) | Extraction itself (14 extractors run automatically) | Fact review: accept/reject/flag | System invariant: "AI proposes, never decides." Extracted facts become the evidence base for all downstream outputs. Wrong facts = wrong readiness scores, wrong financial models, wrong handoff packs. |
| Financial Models (WP5) | Model computation is deterministic | Assumption review, domain accuracy check | Assumptions drive projections. A wrong growth rate or covenant threshold produces misleading DSCR forecasts. Bond professionals will catch errors instantly. |
| COI Benchmarking | Model runs automatically | Interpretation context for client | Raw prediction is automatable; context about comparables, slice-specific accuracy requires domain knowledge. But can mitigate with self-serve interpretation guide. |
| Info Request Routing | Routing rules, reminders, status tracking | Judgment on what's responsive to UW/counsel requests | Routing = project management (automate). Assessing whether a response is complete = domain judgment (human). |
| Legal Templates | Template rendering from project data | Customization for deal-specific terms | Templates are standard; deal-specific modifications need lawyer/Bond Strategist input. |
| Advisory Packages | Workflow automation, milestone tracking | Scope decisions, escalation judgment | When to escalate, what to flag, how to frame — requires domain expertise. |

**Key insight:** The human-required portions are almost always the Bond Strategist reviewing or annotating AI-generated output. The single highest-leverage automation investment is **improving extraction accuracy** so that the Bond Strategist spends less time per review cycle.

### 4.3 Where Labor Should Focus

With automation handling the commodity work, human time should concentrate on:

| Focus Area | Why It's High-Value | Who | Target Hours/Week |
|-----------|--------------------|----|-------------------|
| **WP3 Extraction Review** | Facts are the evidence base for everything. Wrong facts cascade into wrong outputs. This is the quality gate that makes or breaks credibility. | Bond Strategist | 5–10 hrs (per active Tier 1+ engagement) |
| **Domain Accuracy QA** | Platform outputs shown to deal professionals (UW, counsel, MA). A single domain error destroys credibility instantly. | Bond Strategist | 3–5 hrs |
| **Security & Access Control** | Healthcare clients expect vendor security. SOC 2 readiness, encryption, access controls. Breach = company-ending. | CTO | 3–5 hrs |
| **Legal Boundary Monitoring** | Every output must not cross into advisory territory. This requires ongoing vigilance, not one-time setup. | CEO | 2–3 hrs |
| **Client Relationship (Tier 2+)** | Dedicated point of contact for active engagements. Builds trust, enables demand signals. | CEO (initially) | 5–10 hrs |
| **Pilot Instrumentation** | Task log annotation, counterfactual coding, weekly QC. The measurement data that validates the business. | Bond Strategist + CEO | 3–5 hrs (during pilot) |
| **Content & Community** | Skool content, credit spread digests, educational materials. Feeds the funnel. | Bond Strategist + CBO | 3–5 hrs |

**Total human capacity needed per week (steady-state, 1 active Tier 2 engagement + subscription base):**
- Bond Strategist: 20–35 hrs/week
- CEO: 10–18 hrs/week
- CTO: 10–15 hrs/week
- CBO: 5–10 hrs/week

### 4.4 High-Cost Consulting Tier (Partner)

Services that are inherently labor-intensive and should be priced as premium consulting:

| Service | Why It Cannot Be Automated | Pricing Approach | Estimated Cost to Deliver |
|---------|--------------------------|------------------|--------------------------|
| Infrastructure installation | Client needs BFMS running in their environment — requires custom architecture, integration, deployment | Fixed project fee ($50K–$100K+) | 200–400 hrs ($25K–$50K) |
| Ongoing infrastructure operation | System administration, monitoring, updates, incident response in client's environment | Monthly retainer ($5K–$15K/mo) | 20–40 hrs/month ($2.5K–$5K) |
| Custom integrations | Client ERP, treasury, board reporting — every org is different | Scoped project fee ($15K–$75K) | 80–200 hrs ($10K–$25K) |
| White-glove gap remediation | Domain expertise applied to specific borrower situations; requires understanding of their organizational dynamics | Included in Tier 3 or separate SOW | 60–100 hrs ($9K–$15K) |
| Deal team meeting participation | Presence with deal professionals (with MA risk constraints); real-time domain expertise | Included in Tier 3 | 10–20 hrs ($1.5K–$3K) |

> **CEO's philosophy:** "I only expect our high cost, labor-intensive consulting-esque services to be for implementing our systems into the client's internal business, which I'll consider installing and perhaps even operating infrastructure for them. These would be true partners."
>
> **Translation:** Partner tier = strategic relationships, not transactional. Offer only when the client commits to long-term engagement (annual contract + reference rights + co-development potential). The economics work at $100K+ annual value because the labor is justified by the relationship depth.

---

## 5. Flat-Fee Service Configuration

### 5.1 Margin Analysis by Tier

| Tier | Revenue | Estimated Cost Per Engagement | Gross Margin | Margin % | Scalability |
|------|---------|-------------------------------|-------------|----------|-------------|
| **Subscription** ($20K/yr) | $20,000 | $2,000–$4,000 (platform + light support) | $16,000–$18,000 | **80–90%** | **HIGH** — mostly automated; marginal cost per client is infrastructure + light QA |
| **Tier 1: Diagnostic** (+$15–25K) | $15,000–$25,000 | $2,500–$4,000 (Bond Strategist 15–25 hrs + AI + infra) | $11,000–$21,000 | **73–84%** | **MEDIUM** — Bond Strategist is bottleneck; 2–3 concurrent max |
| **Tier 2: Standard** ($40–50K) | $40,000–$50,000 | $8,000–$15,000 (40–80 hrs labor + AI + infra) | $25,000–$42,000 | **60–84%** | **LOW** — significant labor per deal; 1 concurrent max with current team |
| **Tier 3: Accelerator** ($75K+) | $75,000+ | $12,000–$20,000 (60–100 hrs + AI + infra) | $55,000+ | **73%+** | **LOW** — consulting-grade labor; 1 at a time |
| **Partner** (Custom $100K+) | $100,000+ | $30,000–$60,000 (implementation + ongoing ops) | $40,000–$70,000 | **40–70%** | **VERY LOW** — bespoke; each client is a project |

### 5.2 Break-Even Analysis (Subscription Tier)

At $20K annual subscription:

| Cost Category | Annual Per Client |
|---------------|------------------|
| Infrastructure (proportional) | $150–$360 |
| AI compute (moderate usage) | $300–$600 |
| Labor (onboarding + light support) | $500–$1,500 |
| **Total marginal cost per client** | **$950–$2,460** |
| **Contribution margin per client** | **$17,540–$19,050** |

**Fixed overhead (must be covered by total contribution):**

| Fixed Cost | Annual |
|-----------|--------|
| Bond Strategist (full-time equivalent) | $150,000–$200,000 |
| CTO/Engineer (full-time equivalent) | $125,000–$175,000 |
| CEO allocation (50% to Muni-Pal) | $100,000–$150,000 |
| CBO allocation (25% to Muni-Pal) | $25,000–$50,000 |
| Infrastructure baseline | $2,000–$4,000 |
| **Total fixed overhead** | **$402,000–$579,000** |

**Break-even at subscription tier only:**
- At $17,540 contribution margin per client: **23–33 subscription clients** to cover fixed overhead
- This is too many clients for Year 1. Subscription alone does not cover overhead.

**Break-even with blended tiers:**
- 3 subscription clients ($20K × 3 = $60K) + 2 Tier 1 ($20K × 2 = $40K) + 1 Tier 2 ($45K) + Skool content (nurture) = $145K revenue
- This covers ~25–35% of fixed overhead in Year 1, which is realistic for a pre-revenue startup
- True break-even requires 10–15 clients across tiers, or 1–2 Partner engagements

### 5.3 Scaling Constraints

| Constraint | At 5 Clients | At 20 Clients | At 50 Clients |
|-----------|-------------|--------------|--------------|
| **Bond Strategist capacity** | Comfortable (1 Tier 2 + 2 Tier 1 + subscriptions) | Stretched; Tier 2+ only (need hiring or automation lift) | Requires 2–3 Bond Strategists |
| **CEO time** | Heavy (relationship management for all) | Unsustainable for all; delegate Tier 1/subscription | Tier 3 + Partner only |
| **Claude API costs** | ~$200/month | ~$800/month | ~$2,000/month |
| **Infrastructure** | Current hosting sufficient | May need PostgreSQL scaling, additional workers | Dedicated instances, CDN, possibly multi-region |
| **Feature toggle complexity** | Manual config per client | Need automated toggle system | Need self-serve admin panel |
| **Onboarding capacity** | Manual is fine | Semi-automated needed | Fully automated required |

---

## 6. Recommendations

### 6.1 Immediate (Before Adventist Pilot)

**Priority 1: Harden the automated pipeline**
- MIR, Readiness Scan, Credit Spread Monitor must require zero labor per lead
- These are the top-of-funnel tools that generate leads at no marginal cost
- Investment: 1–2 weeks CTO time
- Return: Every lead generated after this costs ~$0 in labor

**Priority 2: Build the feature toggle system**
- Currently only `auth_enforcement_v2` exists as a feature flag in `config.py`
- Need per-tier component toggles matching the matrix in pilot-navigation-system.md §1.2
- This is the mechanism that enables tier escalation/de-escalation during pilots
- Investment: 2 weeks CTO time
- Return: Enables the entire SaaS-style tier management model

**Priority 3: Establish cost tracking during the pilot**
- Use the Pilot Cost Tracking Template (Appendix A) alongside the task log
- Every task logged in the measurement protocol gets a cost annotation
- This gives us real data to calibrate the estimates in §2.1 above
- Investment: 30 min/week during pilot (Bond Strategist annotates costs alongside counterfactuals)
- Return: Actual cost data for pricing decisions

### 6.2 Post-Pilot (Informed by Adventist Data)

**Priority 4: Calibrate cost estimates with actual data**
- Compare estimated costs in §2.1 against actual pilot costs
- Identify where estimates were wrong (likely: extraction review hours, coordination labor)
- Adjust pricing if margins are significantly different than projected

**Priority 5: Determine subscription scope**
- Does the $20K subscription include an annual readiness refresh? Or platform access only?
- Pilot data will show which features clients actually use vs. which they ignore
- Configure subscription scope based on observed usage patterns

**Priority 6: Automate Tier 2 coordination**
- Routing rules, milestone alerts, status updates can be automated
- Information request routing is the biggest labor sink in Tier 2 (10–30 hrs)
- Even partial automation (automated reminders, status dashboards) could save 10–15 hrs/engagement
- Investment: 3–4 weeks CTO time
- Return: Improve Tier 2 margins from 60–84% to 75–90%

### 6.3 Long-Term (6–12 Months)

**Priority 7: Improve extraction accuracy**
- WP3 extraction review is the single largest labor cost in the pipeline
- Every 10% improvement in extraction accuracy reduces Bond Strategist review time by ~15–20%
- Approaches: fine-tune extractors on accepted facts, add sector-specific few-shot examples, pre-validate against schema before human review
- Investment: Ongoing engineering (2–4 weeks/quarter)
- Return: Unlock Bond Strategist capacity for more concurrent engagements

**Priority 8: Build self-serve onboarding**
- Tier 1 and subscription clients should be able to self-onboard
- Automated account creation → playbook selection → onboarding package → document upload
- Investment: 4–6 weeks CTO time
- Return: Remove CEO/CTO from onboarding loop; enable scale

**Priority 9: Reserve Bond Strategist for Tier 2+ only**
- As extraction accuracy improves and self-serve tools mature, Bond Strategist time should shift entirely to:
  - Active deal coordination (Tier 2)
  - Gap remediation (Tier 3)
  - Content creation (Skool, playbooks)
  - New domain expansion (new sectors, new playbooks)
- Tier 1 diagnostics should eventually run with minimal Bond Strategist review (spot-check only)

**Priority 10: Partner tier as strategic play**
- Offer Partner tier only to organizations that are genuine strategic partners
- Criteria: annual contract ($100K+), reference rights, co-development willingness, long-term commitment
- These partners provide: revenue, case studies, product feedback, peer introductions
- Do NOT offer Partner tier as an upsell from Tier 3; it's a separate relationship

---

## 7. Feature Configuration Strategy

### 7.1 How to Use Pilot Data for Feature Configuration

The user's stated approach: "Whatever flat-fee services we provide, we're going to configure based on which features turn on-off as we conduct pilots and see what clients actually use and ask for."

**Implementation:**

During each pilot:
1. Enable all features for the assigned tier
2. Track feature usage per client (which API endpoints are called, which pages are visited, which outputs are downloaded)
3. After pilot, analyze:
   - Which features were used frequently? → Core to the tier
   - Which features were used once or never? → Candidate for tier downgrade or removal
   - Which features were requested but not available? → Candidate for tier upgrade
4. Adjust the Feature Toggle Matrix (pilot-navigation-system.md §1.2) based on observed patterns
5. After 3–5 pilots, the toggle matrix should stabilize and become the production configuration

### 7.2 Pricing Configuration From Pilot Data

1. **Subscription tier**: Include features used by 80%+ of clients. Exclude features used by <20%.
2. **Tier 1 add-on**: Include features that are deal-specific and used by clients who have active deals.
3. **Tier 2/3 boundary**: Draw the line at "labor-intensive coordination" vs "automated analysis." If coordination can be automated, it moves down a tier.
4. **Price points**: Calibrate based on actual cost data (§2.1 calibrated) + desired margin targets (§5.1).

---

## Appendix A: Pilot Cost Tracking Template

Use this template alongside the task log in the measurement protocol. Every task gets a cost annotation.

| Date | Task Description | WP Stage | Who | Hours | AI Cost ($) | Infra Cost ($) | Total Cost ($) | Counterfactual (who would have done this?) | Notes |
|------|-----------------|----------|-----|-------|-------------|----------------|----------------|---------------------------------------------|-------|
| | | | | | | | | | |

**Instructions:**
- Fill in one row per task (matching the task log from measurement protocol §4.1)
- "Who" = which team member performed the task
- "Hours" = actual hours spent (15-min increments)
- "AI Cost" = Claude API cost for that task (check API dashboard)
- "Infra Cost" = proportional infrastructure cost (use $0.50/task as default; adjust quarterly)
- "Counterfactual" = who would have done this if Muni-Pal didn't exist? (MA, counsel, CFO, staff, nobody)

**Aggregation (weekly):**
- Sum hours by role
- Sum AI costs
- Calculate running total per engagement
- Compare against estimates in §2.1

## Appendix B: AI Compute Cost Monitoring

Track monthly AI compute costs to detect unexpected growth:

| Month | Extraction Calls | Advisor Turns | Other Calls | Total Tokens (M) | Total Cost ($) | Cost Per Client ($) |
|-------|-----------------|---------------|-------------|-------------------|----------------|---------------------|
| | | | | | | |

**Alert thresholds:**
- If cost per client exceeds $100/month: investigate (likely extraction re-runs or excessive advisor usage)
- If total monthly cost exceeds $500: review whether model upgrade is needed or if calls can be optimized
- If extraction cost per document exceeds $3: check for chunking issues (oversized chunks = wasted tokens)

## Appendix C: Scaling Decision Points

| Milestone | Trigger | Decision |
|-----------|---------|----------|
| 3 paying clients | Revenue validation | Invest in automation (§4.1 priorities) |
| 5 paying clients | Bond Strategist at capacity | Hire second Bond Strategist OR improve extraction accuracy to reduce review load |
| 10 paying clients | CEO at capacity for relationships | Hire account manager for Tier 1/subscription; CEO focuses on Tier 2+ |
| 20 paying clients | Infrastructure scaling needed | Migrate to managed infrastructure; implement auto-scaling |
| 1 Partner client | Custom infrastructure work | Hire or contract Implementation Architect for dedicated deployment |
| $500K ARR | Business viability proven | Consider: raise capital, expand to new sectors, build self-serve Tier 1 |
