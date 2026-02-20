You are an execution-focused software engineer and system builder.

The following markdown file is the authoritative Build Spec for a system called the Bond Facility Management System (BFMS).

Your task is to:

- Implement the system exactly as specified
- Treat all constraints, invariants, and non-goals as binding
- Use a contract-first approach (schemas, data models, API boundaries before UI)
- Avoid inventing features, logic, or intelligence not explicitly described

Important rules:

- This system is NOT a decision engine, pricing engine, or advisory tool
- AI may propose information but may never decide, approve, score, or infer beyond evidence
- Deterministic rules must be used wherever specified
- If information is missing or ambiguous, surface the gap—do not resolve it

If there is any conflict or ambiguity:

1. System invariants override all else
2. Work Package requirements override summaries
3. Default to less automation, more transparency

Proceed section by section. Do not skip steps. Do not generalize beyond the spec.

**Recommended packaging format for code LLMs**

Create **one markdown “working paper”** that contains:

1. **North Star** (what success looks like)
2. **MVP scope** (what’s in/out)
3. **System outline** (modules + responsibilities)
4. **Contracts** (data model + API boundaries)
5. **Workflows** (end-to-end sequences)
6. **AI pipelines** (extract → normalize → map → review)
7. **Deliverables** (Warm Handoff Pack)
8. **Acceptance criteria** (what “done” means)
9. **Implementation plan** (tickets / milestones)

The key is to make your spec **contract-first** so bots don’t invent structures.

---

## Build Spec v1.0

**Status:** Execution-Optimized Master Outline

**Supersedes:** Conceptual outline used prior to WP1–WP6

**Authoritative Detail:** WP1–WP6 (unchanged, appended verbatim)

---

**0. How to Use This Spec (Critical for Code LLMs)**

This document is a **build guide**, not a conceptual discussion.

- **This outline defines structure, flow, and invariants.**
- **WP1–WP6 define exact requirements and contracts.**
- If there is ambiguity:

1. System invariants override all else
2. WP-specific rules override general descriptions
3. The system must default to _less automation, more transparency_

The BFMS is an evidence-first, advisor-grade system.

It must never behave like a decision engine, pricing engine, or approval authority.

---

**1. System Invariants & Liability Boundaries (Non-Negotiable)**

These rules apply globally and must be enforced in every module.

**1.1 Evidence & Truth**

- No statement is “true” unless supported by an **accepted ExtractedFact**
- Every fact must trace to:

- Artifact → Chunk → Page/Sheet → Source file

- Provenance is mandatory and immutable

**1.2 AI Usage**

- AI may **propose**, never decide
- AI outputs are always reviewable, rejectable, and auditable
- No AI inference is allowed where data is absent

**1.3 Determinism**

- All scoring, readiness, and modeling is deterministic
- Same inputs must always produce the same outputs

**1.4 Liability Controls**

The system must never:

- Approve a deal
- Recommend issuance
- Size bonds
- Optimize pricing or yield
- Replace advisor judgment

Every export must reinforce this boundary.

---

**2. End-to-End System Pipeline (Mental Model)**

All system behavior fits into this pipeline:

Domain Context (User Input)

  ↓

Artifacts (Docs, Excel, Images)

  ↓

Chunks (Immutable Evidence Units)

  ↓

Proposed Facts (AI, Schema-Bound)

  ↓

Reviewed Facts (Human Accepted)

  ↓

Deterministic Insight (Rules)

  ↓

Structured Models (Rebuildable)

  ↓

Warm Handoff Pack (Advisor-Ready)

If a feature does not fit cleanly into this pipeline, it likely does not belong in the MVP.

---

**3. Core Data Primitives (System Backbone)**

These objects are the system’s “atoms.”

They must be implemented before features.

- **Project**
- **Playbook** (bond intelligence configuration)
- **Artifact**
- **Chunk**
- **ExtractionJob**
- **ExtractedFact**
- **EvidenceLink**
- **ChecklistItem**
- **ReadinessDimension**
- **Assumption**
- **FinancialModel**
- **HandoffPack**

All downstream behavior emerges from these primitives.

---

**4. Functional Modules (Execution-Grouped)**

This section maps WP1–WP6 into **buildable modules**, grouped by function rather than chronology.

---

**4.1 Foundation & Contracts**

**(WP1)**

**Purpose**

- Establish domain model
- Define schemas, invariants, permissions
- Enforce contract-first development

**Key Outcomes**

- Postgres schema
- Pydantic models
- Canonical schema paths (Bond Evidence Model)
- Role-based access

**Non-Goals**

- No workflows
- No AI
- No scoring

---

**4.2 Artifact Vault & Ingestion**

**(WP2 v1.1)**

**Purpose**

- Safely ingest raw domain context
- Preserve original meaning and layout
- Produce immutable evidence units

**Key Outcomes**

- File upload & validation
- Chunking (page / table based)
- Hashing & versioning
- Zero interpretation

**Non-Goals**

- No extraction
- No summarization
- No OCR inference (unless explicitly enabled later)

---

**4.3 Controlled Intelligence (AI Pipelines)**

**(WP3 v1.1)**

**Purpose**

- Convert evidence into structured _proposals_
- Maintain human authority at all times

**Key Outcomes**

- Classification
- Schema-driven extraction
- Normalization
- Conflict detection (consolidate)
- Evidence mapping
- Review workflows

**Non-Goals**

- No acceptance without human action
- No scoring
- No decision logic

---

**4.4 Deterministic Judgment & Insight**

**(WP4 v1.0)**

**Purpose**

- Turn reviewed facts into readiness insight
- Identify gaps clearly and honestly

**Key Outcomes**

- Checklist states
- Readiness dimension scores (0–5)
- Gap detection & severity
- Plain-language explanations

**Non-Goals**

- No AI
- No recommendations
- No approvals

---

**4.5 Financial & Performance Models**

**(WP5 v1.0)**

**Purpose**

- Produce rebuildable, advisor-usable models
- Maintain strict transparency

**Key Outcomes**

- Revenue / OPEX models
- CAB accretion schedules
- DSCR tables
- Sensitivity scaffolding
- SLB KPI baseline tables
- Assumption Register

**Non-Goals**

- No sizing
- No pricing
- No optimization

---

**4.6 Warm Handoff Pack Assembly**

**(WP6 v1.0)**

**Purpose**

- Package everything into a professional, neutral deliverable

**Key Outcomes**

- Deal Overview Memo
- Readiness & Gap Report
- Checklist Summary
- Evidence Index
- Financial Tables
- SLB KPI Brief
- Disclosure Outline (skeleton)
- Versioned exports (MD / PDF / DOCX)

**Non-Goals**

- No new facts
- No new models
- No legal drafting

---

**5. Data & Control Flow (Implementation Guidance)**

**5.1 Data Flow**

- Artifacts → Chunks → Facts → Models → Packs
- No reverse mutation allowed

**5.2 Control Flow**

- All long-running tasks async
- Idempotency enforced for all jobs
- Human review gates every state transition that matters

---

**6. Execution Guidance for Code LLMs**

- Implement **contracts first**, UI second
- Prefer explicit enums over free text
- Fail loudly when invariants are violated
- Default to “show the gap,” not “hide the problem”
- Never invent domain intelligence

If uncertain: surface uncertainty, do not resolve it.

---

**7. Acceptance & Validation**

**7.1 MVP Acceptance Test**

- One real UCS-style project
- End-to-end run:

- Upload → Extract → Review → Score → Model → Pack

- Outputs must:

- Link every claim to evidence
- Surface gaps clearly
- Export cleanly

**7.2 Definition of “Done”**

- An advisor can review the handoff pack in <15 minutes
- Nothing feels hidden
- Nothing feels promotional
- Everything feels rebuildable

---

**8. Appendices (Authoritative Detail)**

- **Appendix A:** WP1 — Foundation & Core Data Contracts
- **Appendix B:** WP2 v1.1 — Artifact Vault & Ingestion
- **Appendix C:** WP3 v1.1 — AI Pipelines & Review
- **Appendix D:** WP4 v1.0 — Checklist & Readiness
- **Appendix E:** WP5 v1.0 — Financial Models
- **Appendix F:** WP6 v1.0 — Warm Handoff Pack

In case of conflict, appendices govern.

## WP1 — Foundation & Core Data Contracts

**Bond Facility Management System (BFMS)**

**Stack: FastAPI + Postgres + Celery/Redis**

**Status: FINAL (v1.0)**

---

**WP1 Purpose**

WP1 establishes the **irreversible foundations** of the system:

- Canonical domain primitives
- Data contracts and constraints
- API boundaries
- Async job scaffolding
- Auditability guarantees

No business logic, no AI intelligence, no UI polish.

This work package exists to **prevent schema drift, hallucinated structures, and downstream rewrites**.

---

**WP1 Scope (Strict)**

**In scope**

- Database schema (Postgres)
- Pydantic models (contract-first)
- Core CRUD APIs
- Background job scaffolding (Celery)
- Non-negotiable constraints

**Out of scope**

- Actual AI extraction logic
- Financial model math
- UI implementation
- Readiness scoring formulas
- Playbook authoring tools

---

**1. Core Architectural Rules (Non-Negotiable)**

1. **Facts are first-class citizens**

- Nothing “exists” unless represented as an ExtractedFact with provenance.

3. **Evidence beats opinion**

- Checklists, readiness, and deliverables are derived from accepted facts only.

5. **AI is non-authoritative**

- AI proposes; humans approve.

7. **Everything is auditable**

- All fact changes are versioned and attributable.

9. **Async by default**

- Any operation involving documents, parsing, or AI runs via background jobs.

11. **Playbooks define meaning**

- Schema paths, checklist logic, and readiness dimensions come from playbooks—not hardcoded assumptions.

---

**2. Core Domain Primitives**

**2.1 Project**

A workspace representing one bond-eligible project.

**Fields**

- id (UUID, PK)
- name
- description
- playbook_id
- status: draft | active | archived
- created_by
- created_at

---

**2.2 Playbook**

Defines what “bond-ready” means for a project archetype.

**MVP Handling**

- Stored as versioned JSON config
- Materialized into DB tables at startup or migration time

**Fields**

- id
- name
- version
- source (e.g., ucs_cab_slb_v1)
- checksum

---

**2.3 Artifact (Context Artifact)**

Any user-supplied input.

**Fields**

- id
- project_id
- filename
- mime_type
- size
- storage_uri
- hash_sha256
- uploaded_by
- uploaded_at
- user_notes (why this matters)
- doc_type (enum, nullable)
- doc_type_confidence
- doc_type_source: ai | user
- artifact_role:

technology | finance | sustainability | permitting | legal | marketing | unknown

- version_parent_id (nullable)

**Rules**

- SHA-256 is mandatory
- Duplicate hashes require explicit versioning

---

**2.4 Chunk**

Normalized unit of artifact content.

**Fields**

- id
- artifact_id
- chunk_index
- page_start
- page_end
- text
- table_json (nullable)
- embedding_vector_id (future)

---

**2.5 ExtractionJob**

Async job wrapper for AI and parsing work.

**Fields**

- id
- artifact_id
- project_id
- job_type: classify | extract | normalize | map | generate
- status: queued | running | succeeded | failed
- idempotency_key (UNIQUE)
- started_at
- completed_at
- error

**Idempotency Rule**

idempotency_key ="{artifact_sha256}:{job_type}:{extractor_version}"

---

**2.6 ExtractedFact (Core Primitive)**

A structured, reviewable claim about the project.

**Fields**

- id
- project_id
- artifact_id
- schema_path
- value_json
- unit
- confidence (0–1)
- review_status: proposed | accepted | rejected | edited
- provenance_json

(page, span, anchor_text, excerpt_hash)

- extractor_version
- created_at

**Rule**

If it’s not an ExtractedFact, it does not exist.

---

**2.7 FactRevision (Audit Log)**

Immutable history of fact changes.

**Fields**

- id
- extracted_fact_id
- changed_by
- changed_at
- old_value_json
- new_value_json
- old_status
- new_status
- comment

---

**2.8 EvidenceLink**

Maps facts to system meaning.

**Fields**

- id
- extracted_fact_id
- checklist_item_id (nullable)
- readiness_dimension_id (nullable)
- deliverable_section_id (nullable)

---

**2.9 ChecklistItem**

Operational bond diligence requirements.

**Fields**

- id
- playbook_id
- code (e.g., P3.5)
- title
- description
- required_fact_paths (array)
- status_rule (expression or rule reference)

---

**2.10 ReadinessDimension**

High-level maturity scoring buckets.

**Fields**

- id
- playbook_id
- name
- weight
- required_fact_paths
- scoring_rules (JSON)

---

**2.11 DeliverablePack**

A generated advisory-ready output bundle.

**Fields**

- id
- project_id
- version
- generated_at
- generated_by
- status: draft | finalized

---

**2.12 DeliverableSection**

One section of a deliverable pack.

**Fields**

- id
- deliverable_pack_id
- section_key
- content_md
- supporting_fact_ids

---

**2.13 Assumption**

Explicit declaration of uncertainty.

**Fields**

- id
- project_id
- name
- value
- unit
- source_type: artifact | user | inferred
- source_ref
- confidence
- last_updated

---

**3. Canonical Bond Evidence Model (Schema Paths)**

Schema paths **must** match playbook-defined vocabulary.

**Minimum required paths (MVP)**

**Project**

- project.canonical_description
- project.location
- project.outputs.products[]

**Parties**

- parties.issuer.name
- parties.borrower.name
- parties.operator.name

**Revenue / Feedstock**

- revenue.feedstock.type
- revenue.feedstock.volume
- revenue.offtake.products[]
- revenue.pricing.assumptions

**CAB**

- cab.enabled
- cab.accretion_rate
- cab.final_maturity_date
- cab.turbo_redemption.enabled

**Financial Model**

- finmodel.inputs.capex_total
- finmodel.inputs.opex_total
- finmodel.inputs.revenue_ramp
- finmodel.outputs.dscr_base
- finmodel.outputs.debt_service_schedule[]

**SLB**

- slb.enabled
- slb.kpis.long_list[]
- slb.kpis.short_list[]
- slb.baseline.methodology
- slb.verification.plan

**Risk**

- risk.register[]

---

**4. API Surface (MVP)**

All endpoints are async FastAPI routes.

**Core**

- POST /projects
- GET /projects/{id}

**Artifacts**

- POST /projects/{id}/artifacts
- GET /projects/{id}/artifacts

**Jobs**

- POST /artifacts/{id}/jobs/{job_type}

**Facts**

- GET /projects/{id}/facts
- POST /facts/{id}/review

**Readiness / Checklist**

- GET /projects/{id}/checklist
- GET /projects/{id}/readiness

**Deliverables**

- POST /projects/{id}/deliverables/generate

---

**5. Async Execution Model**

- FastAPI → async DB sessions
- Celery workers → **sync SQLAlchemy sessions**
- No async DB usage inside Celery tasks
- All long-running work occurs in workers

---

**6. Authentication & Authorization (MVP)**

- JWT-based auth
- ProjectMembership table:

- user_id
- project_id
- role: admin | sponsor | reviewer

Permissions enforced per project.

---

**7. Definition of Done (WP1)**

WP1 is complete when:

- All tables exist and migrate cleanly
- CRUD works for projects and artifacts
- Artifacts can be uploaded and hashed
- Celery worker runs and accepts stub jobs
- ExtractedFacts can be created, reviewed, and audited
- Checklist and readiness endpoints return computed placeholders
- OpenAPI spec reflects all contracts accurately

---

## WP2 — Artifact Vault, Ingestion & Chunking

**Bond Facility Management System (BFMS)**

**Status: FINAL (v1.1)**

**Depends on:** WP1 — Foundation & Core Data Contracts

**Supersedes:** WP2 v1.0

---

**WP2 Purpose**

WP2 implements the **Artifact Vault** and **Ingestion Pipeline**, enabling the system to:

- Accept messy, domain-native inputs (documents, spreadsheets, images, notes)
- Preserve user intent and context at upload time
- Normalize content into immutable, traceable chunks
- Prepare artifacts for safe, explainable AI extraction in WP3+
- Maintain strict provenance without interpreting meaning

WP2 does not extract facts, interpret content, or assess readiness.

It prepares evidence so that later stages can do so safely.

---

**WP2 Scope (Strict)**

**In scope**

- Artifact upload + storage abstraction
- Metadata capture (doc_type, artifact_role, tags, user intent)
- File hashing and versioning
- Content ingestion and chunking
- Basic table extraction
- Chunk registry + keyword search
- Ingestion job scaffolding
- Preview utilities for debugging and UX validation

**Out of scope**

- NLP / LLM-based extraction
- OCR (opt-in, reviewed, future WP)
- Financial modeling
- Readiness scoring
- Checklist logic
- Embeddings / semantic search (stub only)

---

**1. Artifact Vault (System of Record)**

**1.1 Storage Abstraction**

Implement a storage interface with interchangeable backends.

**Interface**

- store(file) -> storage_uri
- retrieve(storage_uri) -> file
- delete(storage_uri)

**MVP Implementation**

- Local filesystem
- Directory structure:
- /data
-   /projects/{project_id}
-     /artifacts/{artifact_id}
-       original.{ext}
-       metadata.json

**Rules**

- No direct filesystem access outside the storage interface
- storage_uri is the only persisted reference

---

**1.2 Upload Workflow (API-Level)**

**Endpoint**

POST /projects/{project_id}/artifacts

**Required Request Fields**

- file (multipart)
- artifact_role (enum)
- user_notes (optional free text)
- artifact_tags (optional string[])

**Supported MIME Types (MVP Allowlist)**

- application/pdf
- application/vnd.openxmlformats-officedocument.spreadsheetml.sheet (xlsx)
- text/csv
- application/vnd.openxmlformats-officedocument.wordprocessingml.document (docx)
- image/png
- image/jpeg
- image/webp

Reject others with HTTP 400 and a helpful error message.

**Steps**

1. Accept upload
2. Stream to temp storage
3. Compute SHA-256 hash
4. Check for existing artifact with same hash:

- If exists → require explicit version_parent_id

6. Persist Artifact record
7. Store file via storage interface
8. Create ExtractionJob with:

- job_type = ingest

10. Return Artifact metadata

---

**2. Artifact Metadata & Intent Capture**

**2.1 Artifact Role (Intent-Oriented)**

artifact_role expresses **what the user believes the artifact supports**, not what it is.

**Enum**

technology

finance

sustainability

permitting

legal

marketing

unknown

This field guides downstream extraction but is never authoritative.

---

**2.2 Artifact Tags (Flexible, Non-Authoritative)**

Optional freeform tags for additional signal.

Examples:

["ppp","os","kpi","dscr","permit","feedstock","accretion"]

Rules:

- Tags do not replace classification
- Tags are never required
- Tags are not enforced by schema logic

---

**2.3 Doc Type (Preliminary, Revisable)**

Initial doc_type may be set during ingestion using lightweight heuristics.

**Enum (MVP)**

unknown

ppm

indenture

loan_agreement

feasibility_study

technology_specs

financial_model

sustainability_report

presentation

image

other

**Associated Fields**

- doc_type_confidence
- doc_type_source: user | system

LLM-based classification is deferred to WP3.

---

**3. Content Ingestion & Chunking**

**3.1 Ingestion Job (job_type = ingest)**

Triggered automatically after upload.

**Responsibilities**

- Extract raw content
- Create immutable Chunk records
- Preserve layout references (page numbers, sheets)
- Capture parsing diagnostics
- Never interpret meaning

---

**3.2 File-Type Handling**

**PDFs**

- Use pdfplumber or equivalent
- Extract page-level text
- Chunk strategy (MVP):

- **1 chunk per page**

- Preserve:

- page_start, page_end

**Word / DOCX**

- Use python-docx
- Chunk by:

- Headings if available
- Else fixed-length blocks

**Excel / CSV**

- Use pandas
- For each sheet:

- Extract table as table_json
- Include sheet name + dimensions

- Chunk granularity:

- One chunk per sheet (MVP)

**Images**

- Store metadata only
- No OCR in WP2
- Create placeholder chunk with text = null

---

**3.3 Chunk Creation Rules**

Every Chunk **must** include:

- artifact_id
- chunk_index
- chunk_hash_sha256
- One of:

- text
- table_json

Never allow both to be null.

---

**4. Chunk Registry & Retrieval**

**4.1 Chunk Registry**

The Chunk table is the **single source of truth** for parsed content.

**Guarantees**

- Stable chunk IDs
- Immutable content
- Traceable to artifact + location
- Hash-protected against mutation

---

**4.2 Search (MVP)**

Implement basic keyword search:

GET /projects/{id}/chunks?query=...

- SQL ILIKE on text
- No semantic ranking in WP2

---

**5. Provenance Preservation**

Although WP2 does not create facts, it must preserve **future provenance hooks**.

**5.1 Required Metadata for Every Chunk**

- Artifact ID
- Page/sheet reference
- Offset range (if available)
- chunk_hash_sha256

This enables:

- Precise fact provenance in WP3+
- Advisor-grade traceability

---

**6. Diagnostics & Observability**

**6.1 ExtractionJob Enhancements**

Add fields:

- duration_seconds
- error_details_json (JSONB)

**Suggested keys**

{

"parser":"pdfplumber | pandas | python-docx",

"message":"...",

"stack_trace":"...",

"sheet_name":"...",

"page_number":12,

"row_count":350,

"col_count":14

}

---

**7. Preview Utilities (MVP UX / Debug Tool)**

**7.1 Preview Endpoint**

GET /artifacts/{id}/preview?max_chars=500

**Behavior**

- If first chunk has text → return first max_chars
- If first chunk has table → return:

- sheet name
- first 5 rows/columns

- Else → “No preview available”

This endpoint is for **validation**, not analysis.

---

**8. API Surface (WP2)**

**Artifact Vault**

- POST /projects/{id}/artifacts
- GET /projects/{id}/artifacts
- GET /artifacts/{id}

**Chunk Access**

- GET /artifacts/{id}/chunks
- GET /projects/{id}/chunks?query=

**Jobs**

- POST /artifacts/{id}/jobs/ingest

---

**9. Async Execution Model**

- Upload endpoints are non-blocking
- Ingestion runs in Celery workers
- Workers use **sync SQLAlchemy sessions**
- Errors do not invalidate artifacts

If ingestion fails:

- Job marked failed
- Artifact remains accessible
- No partial chunks persisted

---

**10. Explicit Non-Goals (WP2)**

Bots must **not**:

- Infer meaning
- Populate ExtractedFacts
- Normalize values
- Run OCR
- Apply checklists
- Score readiness
- Generate deliverables

Those begin in WP3+.

---

**11. Definition of Done (WP2 v1.1)**

WP2 is complete when:

- Artifacts upload cleanly with validation
- Files are hashed, versioned, and stored
- Ingestion jobs create immutable chunks
- Chunk hashes are stored and stable
- Keyword search works across chunks
- Preview endpoint confirms ingestion success
- System tolerates junk uploads without breaking
- No AI interpretation exists yet

---

**Alignment Check**

WP2 v1.1 is fully aligned with:

- WP1 contracts and primitives
- Domain-expert-first workflows
- Bond-counsel-grade provenance expectations
- Future Muni-Pal architecture

It deliberately prepares _evidence_, not _answers_.

---

## WP3 — AI Pipelines: Classification, Extraction, Normalization & Review

**Bond Facility Management System (BFMS)**

**Status:** FINAL (v1.1)

**Depends on:**

- WP1 — Foundation & Core Data Contracts
- WP2 v1.1 — Artifact Vault, Ingestion & Chunking

**Supersedes:** WP3 v1.0

---

**WP3 Purpose**

WP3 introduces **controlled intelligence** into the system by allowing AI to:

- Propose structured, bond-relevant facts from chunked artifacts
- Normalize values into canonical bond schema paths
- Detect conflicts and ambiguities across sources
- Map evidence to downstream structures
- Present all outputs for **explicit human review**

WP3 enables the system to interpret evidence —

**not** to judge sufficiency, complete checklists, or assess readiness.

---

**WP3 Scope (Strict)**

**In scope**

- AI-assisted document classification
- Schema-driven fact extraction
- Canonical value normalization
- Conflict detection and consolidation
- Evidence mapping (facts → checklist/readiness references)
- Review surfaces for extracted facts
- Confidence scoring and diagnostics (advisory only)

**Out of scope**

- Checklist completion
- Readiness scoring logic
- Financial model computation
- Drafting of legal or disclosure language
- Predictive ML or training
- Autonomous decision-making

---

**1. AI Operating Principles (Non-Negotiable)**

1. **Schema-first extraction**

AI may extract _only_ schema paths defined by the active playbook.

2. **Chunk-local reasoning**

AI operates on selected chunks, never full documents by default.

3. **Propose, never assert**

All AI outputs create ExtractedFact records with review_status = proposed.

4. **Provenance required**

Every fact must reference chunk IDs, page/sheet locations, and content hashes.

5. **Confidence is advisory only**

Confidence informs review priority, not truth.

6. **No hallucination fallback**

If a value is not explicitly present, AI must return null.

---

**2. AI Pipeline Overview**

Each artifact flows through the following **explicit, idempotent pipeline stages**:

Artifact

 → classify_ai

 → extract

 → normalize

 → consolidate

 → map

 → human review

Each stage runs as a **separate Celery job**, versioned and repeatable.

---

**3. AI-Assisted Classification**

**3.1 Classification Job**

**Job Type:** classify_ai

**Inputs**

- Artifact metadata
- Selected chunks (e.g., first 3 pages / first tables)
- User-provided artifact_role and artifact_tags

**Outputs**

- Proposed doc_type
- Updated doc_type_confidence
- Classification rationale (stored in job metadata)

**Rules**

- Classification is always revisable
- User overrides take precedence
- Confidence below threshold → flagged for reviewer attention

---

**4. Extraction Framework (Core Intelligence Layer)**

**4.1 Extractor Definitions (Playbook-Driven)**

Each playbook defines **Extractor Schemas**, stored declaratively.

Each extractor specifies:

- Extractor ID (e.g., CABTermsExtractor)
- Applicable doc_type
- Applicable artifact_role
- Required chunk characteristics (text vs table, page ranges)
- Canonical output schema paths
- Prompt template
- Optional criticality flag

**Prompt templates are stored in the Playbook**, not hardcoded.

---

**4.2 Extraction Job**

**Job Type:** extract

**Inputs**

- Artifact ID
- Extractor ID
- Selected chunk IDs

**Prompt Constraints**

- Extract only listed schema paths
- If value is not present → return null
- Cite exact chunk ID and page/sheet
- No inference, no synthesis

**Outputs**

- One or more ExtractedFact records:

- schema_path
- value_json
- unit (if applicable)
- confidence
- confidence_factors_json (optional)
- provenance_json
- review_status = proposed
- extractor_version

---

**5. Canonical Fact Normalization**

**5.1 Normalization Job**

**Job Type:** normalize

**Purpose**

Convert extracted values into canonical formats.

**Examples**

- Percent strings → floats
- Currency strings → numeric + unit
- Dates → ISO format
- Ranges → structured objects

**Rules**

- No inference permitted
- Ambiguous normalization → flagged
- Provenance remains unchanged

---

**6. Consolidation & Conflict Detection**

**6.1 Consolidation Job**

**Job Type:** consolidate

**Purpose**

Detect conflicts and duplication **without resolving them**.

**Responsibilities**

- Group proposed facts by schema_path
- Detect:

- Multiple values from different artifacts
- Unit mismatches
- Material numeric deltas

- Flag conflicts in job metadata
- Annotate involved facts (read-only flags)

**Rules**

- No merging
- No overwriting
- No acceptance
- Human resolution required

---

**7. Evidence Mapping (Non-Scoring)**

**7.1 Mapping Job**

**Job Type:** map

**Purpose**

Create EvidenceLink records connecting facts to:

- Checklist items
- Readiness dimensions
- Deliverable sections (future use)

**Rules**

- Mapping does not alter checklist status
- Mapping does not score readiness
- One fact may support multiple downstream items

---

**8. Review Surfaces (Human-in-the-Loop)**

**8.1 Fact Review Interface**

Reviewers can:

- View proposed value
- Inspect confidence + confidence factors
- Jump to source chunk + page/sheet
- Accept
- Edit (creates FactRevision)
- Reject (with reason)

---

**8.2 Bulk Review Controls**

- Bulk accept available only via explicit user action
- Threshold configurable per playbook:

- Default (example): 0.85
- Higher thresholds for critical schema paths (e.g., CAB terms)

---

**8.3 Conflict & Criticality Indicators**

UI must visually flag:

- Conflicting facts for same schema_path
- Low-confidence facts on critical schema paths

Low-confidence critical facts set:

critical_low_confidence_flag =true

(No Assumption records created in WP3.)

---

**9. Confidence Scoring (Advisory)**

Each ExtractedFact includes:

- confidence ∈ [0,1]

Optional structured metadata:

confidence_factors_json = {

"text_explicitness": 0.9,

"table_presence": 0.95,

"multiple_mentions": 0.8,

"artifact_role_alignment": 1.0

}

**Rules**

- Confidence never auto-accepts a fact
- Confidence never drives readiness directly

---

**10. Idempotency & Safety**

All jobs enforce:

- Unique (artifact_hash, job_type, extractor_version)
- Safe re-runs on extractor upgrades
- No duplicate fact creation on retries

---

**11. API Surface (WP3)**

**Classification**

- POST /artifacts/{id}/jobs/classify_ai

**Extraction**

- POST /artifacts/{id}/jobs/extract?extractor_id=

**Normalization / Consolidation / Mapping**

- POST /artifacts/{id}/jobs/normalize
- POST /artifacts/{id}/jobs/consolidate
- POST /artifacts/{id}/jobs/map

**Review**

- GET /projects/{id}/facts?review_status=proposed
- POST /facts/{id}/review

**Diagnostics**

- GET /artifacts/{id}/extraction_summary

---

**12. Explicit Non-Goals (WP3)**

Bots must **not**:

- Auto-complete checklists
- Compute readiness scores
- Generate financial models
- Draft legal language
- Merge conflicting facts
- Train ML models
- Decide truth

Those begin in WP4+.

---

**13. Definition of Done (WP3 v1.1)**

WP3 is complete when:

- AI-assisted classification updates doc_type safely
- Extractors generate proposed facts with provenance
- Normalization enforces canonical formats
- Consolidation flags conflicts without resolution
- EvidenceLinks are created correctly
- Review UI supports clean accept/edit/reject flows
- No accepted fact exists without human approval
- System can explain _why every fact exists_

---

**Alignment Check**

WP3 v1.1:

- Preserves WP1’s fact-first, audit-first discipline
- Builds safely on WP2’s chunk integrity and provenance
- Reflects how real municipal advisors evaluate evidence
- Establishes the first trustworthy “Muni-Pal brain”

Intelligence is now present — but still leashed.

---

## WP4 — Checklist Logic, Readiness Scoring & Gap Analysis

Below is **WP4 v1.0 FINAL (bot-ready)**, fully aligned with **WP1–WP3 v1.1** and your domain-expert → bond-pro handoff intent.

---

**Bond Facility Management System (BFMS)**

**Status:** FINAL (v1.0)

**Depends on:**

- WP1 — Foundation & Core Data Contracts
- WP2 v1.1 — Artifact Vault, Ingestion & Chunking
- WP3 v1.1 — AI Pipelines & Review

**Purpose:** Turn _accepted facts_ into _actionable readiness insight_

---

**WP4 Purpose**

WP4 introduces **deterministic judgment logic** (not AI judgment) to:

- Evaluate accepted evidence against playbook requirements
- Compute checklist item states
- Compute readiness dimension scores
- Identify gaps, risks, and next actions
- Explain _why_ a project is or is not bond-ready

WP4 answers: “Where do we stand, and what’s missing?”

It does _not_ answer: “Is this deal approved?”

---

**WP4 Scope (Strict)**

**In scope**

- Checklist item evaluation (rules-based)
- Readiness dimension scoring (rules-based)
- Evidence sufficiency assessment
- Gap detection and prioritization
- Human-readable explanations
- Advisor-grade transparency

**Out of scope**

- Financial model computation (WP5)
- Drafting legal or disclosure language
- SLB KPI optimization
- Approval workflows
- External stakeholder portals

---

**1. Core Principles (Non-Negotiable)**

1. **Facts drive state**

- Only accepted or edited ExtractedFacts are considered.

3. **Rules, not AI**

- All logic is deterministic and auditable.

5. **Explainability first**

- Every checklist state and score must explain itself.

7. **No silent completion**

- Nothing advances without visible evidence.

9. **Gap visibility beats optimism**

- Missing or weak evidence is surfaced, not smoothed over.

---

**2. Checklist Engine**

**2.1 Checklist Item States**

Each ChecklistItem evaluates to one of:

not_started

in_progress

ready

blocked

**2.2 Checklist Evaluation Rules**

Each ChecklistItem defines:

- required_fact_paths (array)
- status_rule (rule reference or expression)

**Default Rule (MVP)**

- ready → all required facts exist and are accepted
- in_progress → some required facts exist
- not_started → no required facts exist
- blocked → conflicting or rejected facts present

**2.3 Evidence Attribution**

For every checklist item, the system must expose:

- Supporting fact IDs
- Missing required fact paths
- Conflicting facts (if any)

---

**3. Readiness Dimension Engine**

**3.1 Readiness Dimensions**

Each ReadinessDimension includes:

- Name (e.g., “Financial Feasibility”)
- Weight
- Required fact paths
- Scoring rules

**3.2 Dimension Scoring (MVP)**

**Score Range**

0.0 – 5.0

**Baseline Logic**

- 0.0 → no required facts
- 2.0 → partial evidence
- 3.0 → minimum viable evidence
- 4.0 → strong evidence
- 5.0 → complete, conflict-free evidence

Exact thresholds are defined per playbook.

**3.3 Weighting**

Overall readiness score is a weighted average of dimension scores.

---

**4. Evidence Sufficiency & Conflict Handling**

**4.1 Sufficiency Checks**

A required fact path is considered:

- **Satisfied** → accepted fact exists
- **Weak** → accepted fact exists but critical_low_confidence_flag = true
- **Missing** → no accepted fact exists

**4.2 Conflict Impact**

If conflicting accepted facts exist:

- Checklist items → blocked
- Readiness dimension → capped at defined maximum (e.g., ≤ 2.0)
- Conflict explanation surfaced prominently

---

**5. Gap Analysis Engine**

**5.1 Gap Types**

Gaps are classified as:

- **Missing Evidence** (no fact)
- **Weak Evidence** (low confidence)
- **Conflicting Evidence**
- **Outdated Evidence** (future WP)

**5.2 Gap Records (Computed, Not Stored)**

Each gap includes:

- Related checklist item(s)
- Related readiness dimension(s)
- Missing or weak schema paths
- Severity:
- low | medium | high | critical

- Recommended next action (text)

---

**6. “What’s Missing & Why” Explanations**

For any checklist item or readiness dimension, the system must generate:

- Plain-language explanation:

- What’s missing
- Why it matters for bond issuance
- What type of artifact would satisfy it

Example:

“Revenue feasibility is incomplete because no accepted revenue ramp assumptions exist. Municipal advisors require a defensible revenue model to assess DSCR and debt sizing.”

---

**7. User Surfaces (Logic Only, No UI Design)**

WP4 must support the following views:

**7.1 Checklist View**

- Checklist grouped by phase (P1–P6 style)
- State per item
- Expand to show evidence + gaps

**7.2 Readiness Dashboard**

- Dimension scores (0–5)
- Weighted overall score
- Visual flags for blocked dimensions

**7.3 Gap Summary**

- Ordered by severity
- Filterable by domain (finance, legal, sustainability)
- Click-through to affected checklist items

---

**8. API Surface (WP4)**

**Checklist**

- GET /projects/{id}/checklist

- returns checklist items + state + evidence

**Readiness**

- GET /projects/{id}/readiness

- returns dimension scores + explanations

**Gaps**

- GET /projects/{id}/gaps

- returns computed gap list

---

**9. Determinism & Safety**

- No randomness
- No AI calls
- No hidden heuristics
- Same inputs → same outputs

This ensures:

- Auditability
- Advisor trust
- Regulatory defensibility

---

**10. Explicit Non-Goals (WP4)**

Bots must **not**:

- Auto-accept facts
- Infer missing facts
- Optimize readiness scores
- Generate documents
- Decide deal viability

WP4 diagnoses; it does not prescribe approval.

---

**11. Definition of Done (WP4 v1.0)**

WP4 is complete when:

- Checklist states compute correctly from accepted facts
- Readiness dimensions score deterministically
- Conflicts visibly block progress
- Gaps are clearly identified and explained
- Outputs are understandable by non-bond experts
- Municipal advisors can immediately see “what’s missing”

---

**Alignment Check**

WP4:

- Uses WP3’s reviewed facts only
- Respects WP2’s provenance integrity
- Reflects real muni advisory reasoning
- Gives your domain team a clear roadmap to bond readiness

At this point, the system can confidently answer:

“Are we structurally ready to engage a municipal advisor—and if not, what exactly needs to be done?”

---

## WP5 — Financial Model Construction & Warm Handoff Inputs

What follows is **WP5 v1.0 FINAL (bot-ready)**, aligned tightly with **WP1–WP4**, and scoped so it delivers real value **without crossing into pricing, approval, or underwriting judgment**.

---

**Bond Facility Management System (BFMS)**

**Status:** FINAL (v1.0)

**Depends on:**

- WP1 — Foundation & Core Data Contracts
- WP2 v1.1 — Artifact Vault, Ingestion & Chunking
- WP3 v1.1 — AI Pipelines & Review
- WP4 v1.0 — Checklist Logic, Readiness & Gaps

---

**WP5 Purpose**

WP5 converts **accepted facts and declared assumptions** into:

1. **Structured financial model outputs** (CAB- and SLB-aware, template-driven)
2. **Advisor-ready inputs** that can be rebuilt, stress-tested, or replaced
3. **Traceable tables and schedules** suitable for inclusion in bond docs
4. **A clean handoff surface**—not a pricing engine, not a decision engine

WP5 answers:

**“Here is a defensible financial and performance picture, with assumptions clearly stated.”**

It does _not_ answer: “Is this deal sized correctly?” or “Should we issue?”

---

**WP5 Scope (Strict)**

**In scope**

- Template-driven financial model construction
- CAB-specific schedules (accretion, maturity profile)
- Revenue, expense, and DSCR computation (deterministic)
- Sensitivity scaffolding (no optimization)
- SLB KPI baseline tables (non-economic)
- Assumption Register population and linkage
- Structured outputs for advisor consumption

**Out of scope**

- Bond sizing
- Pricing/yield optimization
- Underwriter-style cash flow sculpting
- Tax or legal conclusions
- Investment recommendations
- Auto-updating market data

---

**1. Core Principles (Non-Negotiable)**

1. **Accepted facts only**

Models draw exclusively from:

- accepted / edited ExtractedFacts
- Explicit Assumptions

2. **Templates, not free-form models**

All models follow predefined, auditable structures.

3. **No hidden math**

Every output references its inputs and assumptions.

4. **Advisor rebuildability**

Outputs must be easy to replicate in Excel or other tools.

5. **No AI inference**

All calculations are deterministic and transparent.

---

**2. Financial Model Architecture**

**2.1 Model Types (MVP)**

Implement the following **template-based models**:

**A. Revenue Model**

- Annual revenue projections
- Based on:

- revenue.feedstock.*
- revenue.pricing.assumptions
- finmodel.inputs.revenue_ramp

**B. Operating Expense Model**

- Annual OPEX
- Based on:

- finmodel.inputs.opex_total
- O&M structure facts (if present)

**C. Debt Service Model**

- Deterministic schedule
- Inputs:

- Principal
- Accretion rate (if CAB)
- Tenor
- Interest conventions

**D. DSCR Model**

- DSCR by period
- Based on:

- Net revenues
- Debt service

- No sculpting or optimization

---

**2.2 CAB-Specific Logic (Critical)**

If cab.enabled = true, include:

- Accretion schedule
- Accreted value over time
- Final maturity exposure
- Optional turbo redemption flag (display only)

**Explicitly excluded**

- Accretion restructuring
- Stress optimization
- Early amortization logic

---

**3. SLB KPI Tables (Non-Economic)**

**3.1 KPI Baseline Tables**

For each accepted SLB KPI:

- KPI name
- Baseline value
- Measurement method
- Reporting frequency
- Verification concept (if provided)

No penalty math or step-up logic in WP5.

---

**4. Assumption Register Integration**

**4.1 Assumption Sources**

Assumptions may originate from:

- Explicit user input
- Low-confidence accepted facts
- Model-required inputs with no supporting fact

**4.2 Assumption Register Population**

Each model must emit:

- A list of assumptions used
- Linked to:

- Schema paths
- Source artifacts (if any)
- Confidence level

---

**5. Sensitivity Scaffolding (MVP)**

**5.1 What Sensitivity Means Here**

Sensitivity ≠ optimization.

Sensitivity = **parameter toggles** that show directional impact.

Examples:

- ±10% revenue
- ±15% OPEX
- Delayed ramp start

**5.2 Output**

- Sensitivity table placeholders
- No scenario ranking
- No “best case / worst case” labeling

---

**6. Model Outputs & Formats**

**6.1 Internal Representation**

- Structured JSON objects
- Deterministic schemas
- Versioned per model run

**6.2 Export Formats (MVP)**

- CSV (tables)
- XLSX (one model per sheet)
- Markdown tables (for handoff pack)

---

**7. Traceability & Explainability**

For every model output:

- Reference:

- Input facts
- Assumptions

- Include:

- “What this table shows”
- “What it does not claim”

Example disclaimer:

“This DSCR table reflects input assumptions only and is not a sizing or pricing determination.”

---

**8. API Surface (WP5)**

**Model Construction**

- POST /projects/{id}/models/build

- Payload: model_type(s)

**Model Access**

- GET /projects/{id}/models
- GET /models/{model_id}

**Export**

- GET /models/{model_id}/export?format=csv|xlsx|md

---

**9. Determinism & Safety**

- No randomness
- Same inputs → same outputs
- Model versions immutable once generated
- Regeneration requires explicit user action

---

**10. Explicit Non-Goals (WP5)**

Bots must **not**:

- Recommend bond sizes
- Optimize yields
- Compare financing alternatives
- Predict investor appetite
- Replace advisor judgment

WP5 prepares information; it does not decide outcomes.

---

**11. Definition of Done (WP5 v1.0)**

WP5 is complete when:

- Financial models build from accepted facts
- CAB schedules are transparent and traceable
- DSCR tables are reproducible
- SLB KPI tables are structured and clear
- Assumptions are explicit and linked
- Exports are advisor-usable
- No output implies approval or recommendation

---

**Alignment Check**

WP5:

- Activates WP4 insights
- Preserves WP3 evidentiary discipline
- Honors WP2 provenance
- Completes the “warm handoff” foundation

At this point, the system can credibly hand an advisor:

A structured, honest, rebuildable financial and performance picture—without liability.

---

## WP6 — Warm Handoff Pack Assembly & Advisor Interface

Below is **WP6 v1.0 FINAL (bot-ready)**, aligned tightly with **WP1–WP5**, scoped correctly, and written so code LLMs can implement it without inventing new logic or crossing liability boundaries.

---

**Bond Facility Management System (BFMS)**

**Status:** FINAL (v1.0)

**Depends on:**

- WP1 — Foundation & Core Data Contracts
- WP2 v1.1 — Artifact Vault, Ingestion & Chunking
- WP3 v1.1 — AI Pipelines & Review
- WP4 v1.0 — Checklist Logic, Readiness & Gaps
- WP5 v1.0 — Financial Model Construction & Outputs

---

**WP6 Purpose**

WP6 assembles all **validated, deterministic outputs** into a **coherent, advisor-ready Warm Handoff Pack** that:

- Explains the project clearly and honestly
- Shows exactly what evidence exists and where it came from
- Surfaces readiness, gaps, and priorities
- Provides rebuildable financial and SLB tables
- Avoids approval, recommendation, or pricing language

WP6 answers:

**“Here is everything you need to understand this project and engage productively.”**

It does _not_ answer: “Should you do this deal?”

---

**WP6 Scope (Strict)**

**In scope**

- Assembly of a structured Warm Handoff Pack
- Templated narrative generation (from accepted facts only)
- Evidence indexing and traceability
- Inclusion of readiness, gaps, and financial outputs
- Professional export formats (MD / PDF / DOCX)
- Advisor-oriented navigation and summaries

**Out of scope**

- New calculations
- AI inference or judgment
- Legal drafting or final disclosure language
- Approval workflows
- External portal access (future WP)

---

**1. Core Principles (Non-Negotiable)**

1. **Assembly, not intelligence**

WP6 assembles outputs from WP3–5; it does not create new facts or logic.

2. **Evidence-linked everything**

Every statement must trace back to accepted facts or assumptions.

3. **Professional neutrality**

Language must be factual, conditional, and non-promotional.

4. **Rebuildability respected**

Advisors must be able to discard, rebuild, or replace any component.

5. **Clarity over completeness**

Gaps are shown explicitly, not buried.

---

**2. Warm Handoff Pack Structure (MVP)**

The Warm Handoff Pack is a **versioned deliverable bundle** consisting of the following sections.

---

**2.1 Cover & Metadata**

**Contents**

- Project name
- Issuer / Borrower
- Date generated
- Playbook used
- BFMS version
- Disclaimer footer (standardized)

**Disclaimer (mandatory)**

“This package was generated by the Bond Facility Management System (BFMS) on [date]. It is based solely on accepted facts and explicit assumptions as of that date. It does not constitute financial advice, bond sizing, pricing, or a recommendation to proceed. All contents are intended to be rebuilt, validated, or replaced by professional advisors.”

---

**2.2 Deal Overview Memo (Templated Narrative)**

**Purpose**

Provide a fast, bond-literate orientation to the project.

**Inputs**

- Accepted facts only:

- project.canonical_description
- project.location
- Parties & roles
- Technology / operations summary
- Revenue logic
- CAB / SLB flags

**Rules**

- Declarative, not persuasive
- No forward-looking claims
- No market assumptions

**Example Sections**

- Project Summary
- Issuance Intent (CAB / SLB context)
- Parties & Roles
- Use of Proceeds (if available)
- Structural Notes (high-level only)

---

**2.3 Readiness & Gap Report**

**Contents**

- Overall readiness score
- Dimension-level scores (0–5)
- Key blockers
- High-severity gaps
- Prioritized next actions

**Rules**

- Scores and gaps sourced directly from WP4
- No interpretation beyond WP4 explanations
- Language must answer “what’s missing and why”

---

**2.4 Checklist Status Summary**

**Contents**

- Checklist grouped by phase (P1–P6 style)
- Status per item:

- not_started / in_progress / needs_review / ready / blocked

- Expandable evidence links

**Rules**

- Read-only representation
- No ability to modify checklist state here

---

**2.5 Evidence Index (Critical Section)**

**Purpose**

Give advisors confidence that nothing is hidden.

**Structure**

For each accepted fact:

- Schema path
- Value (formatted)
- Source artifact
- Page / sheet reference
- Chunk ID
- Confidence
- Review status

This section is **non-narrative** and audit-oriented.

---

**2.6 Assumption Register**

**Contents**

For each assumption:

- Name
- Value
- Source type
- Confidence
- Impact category
- Linked model outputs

**Rules**

- Explicit separation from facts
- Highlight assumptions impacting CAB or SLB paths

---

**2.7 Financial Model Outputs**

**Included Tables**

- Revenue projections
- OPEX summary
- Debt service schedule
- CAB accretion schedule
- DSCR table
- Cash Flow Waterfall Skeleton (if enabled)
- Sensitivity scaffolding tables

**Rules**

- Imported directly from WP5 outputs
- Include standardized disclaimer footer
- No commentary beyond “what this table shows”

---

**2.8 SLB KPI Brief**

**Contents**

For each KPI:

- KPI name
- Baseline value
- Measurement method
- Reporting frequency
- Verification concept (if available)
- Known gaps

**Rules**

- No penalty mechanics
- No step-up economics
- No claims of ambition or compliance

---

**2.9 Disclosure Outline (Skeleton)**

**Purpose**

Help advisors see how this would map into bond docs.

**Contents**

- High-level section outline:

- Security
- Sources & Uses
- Project Description
- Risk Factors
- SLB Disclosure (if applicable)

**Rules**

- Headings only
- No drafted prose
- Placeholders allowed

---

**3. Pack Versioning & Regeneration**

**3.1 Versioning Rules**

- Every pack has:

- Version (v1, v2, …)
- Timestamp
- Input snapshot (facts + assumptions IDs)

**3.2 Regeneration**

- New version created on:

- Fact acceptance changes
- Assumption changes
- Model regeneration

Old versions remain immutable.

---

**4. Advisor Interface (Internal View)**

WP6 includes a **read-only advisor-oriented interface** (internal users only):

- Section navigation
- Jump-to-evidence links
- Download/export controls
- No edit actions

---

**5. Export Formats (MVP)**

- **Markdown** (source of truth)
- **PDF** (professional handoff)
- **DOCX** (advisor-editable)

All exports must:

- Preserve section order
- Preserve evidence links (as footnotes or references)
- Include standardized disclaimers

---

**6. API Surface (WP6)**

**Pack Generation**

- POST /projects/{id}/handoff-pack/generate

**Pack Access**

- GET /projects/{id}/handoff-pack
- GET /handoff-pack/{pack_id}

**Export**

- GET /handoff-pack/{pack_id}/export?format=md|pdf|docx

---

**7. Explicit Non-Goals (WP6)**

Bots must **not**:

- Add new facts
- Modify models
- Suggest approval
- Generate legal language
- Mask gaps or conflicts
- Replace advisor judgment

---

**8. Definition of Done (WP6 v1.0)**

WP6 is complete when:

- A full Warm Handoff Pack can be generated end-to-end
- All sections trace back to facts, assumptions, or models
- Advisors can orient themselves in <15 minutes
- Gaps and risks are obvious, not hidden
- Outputs feel professional, neutral, and trustworthy
- No content implies approval or recommendation

---

**Alignment Check**

WP6 completes the MVP vision you originally described:

A system where domain experts input context,

the platform **structures and validates evidence**,

and professionals receive a **clean, honest handoff**.

At this point, BFMS can credibly support:

- Internal readiness management
- Early advisor engagement
- Reduced friction and re-work
- Institutional-grade transparency

---