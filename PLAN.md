# Muni-Pal Document Management System — Architecture Plan

## Overview

A deal documentation platform built on top of Muni-Pal's existing FastAPI + React stack. Handles document creation, collaborative editing, e-signatures, and controlled external sharing via Virtual Data Rooms. Starts with municipal finance, expands to PE/RE/project finance.

**User Decisions:**
- Priority: Municipal Finance first
- E-Signature: Dropbox Sign API ($15/user/mo)
- Editing: In-browser rich text editor (TipTap)
- VDR: Full Virtual Data Room with analytics, watermarking, granular permissions

---

## Document Universe — Municipal Finance

### Templated / Semi-Templated (template library candidates)
- NDA / Confidentiality Agreement
- Continuing Disclosure Agreement (SEC Rule 15c2-12)
- Board resolutions / Authorizing ordinances
- Tax compliance certificates (IRS Form 8038)
- Closing certificates and checklists
- Due diligence request lists
- Capital call / Distribution notices (private placements)

### Heavily Negotiated (need rich editor + clause library)
- Official Statement / Preliminary Official Statement
- Trust Indenture / Bond Resolution
- Credit enhancement docs (LOC, bond insurance, SBPA)
- Remarketing Agreement
- ISDA Master Agreement + Schedule
- Loan Agreement (direct placements)
- Rate Covenant provisions

### Professional Reports (uploaded via existing Artifact vault)
- Feasibility studies, Engineering reports
- Environmental assessments (Phase I/II)
- Appraisals, Legal opinions

### Regulatory Filings (generated + filed to EMMA/EDGAR)
- Official Statement (MSRB G-32: filed within 1 biz day of closing)
- Material event notices (16 listed events per Rule 15c2-12)
- Annual financial/operating data filings

---

## Part 1: Database Schema (11 new tables)

All tables use existing patterns: UUID PKs, `TimestampMixin`, `UUIDType` for FK/PK, `tenant_id` on root entities, PostgreSQL `JSON` columns.

### New Models — `src/munipal/core/models/deal_document.py`

| Table | Purpose |
|-------|---------|
| `deal_document_types` | Extensible registry: code, category (templated/negotiated/report/regulatory), deal_vertical (muni/pe/re), retention_policy, requires_signature |
| `deal_documents` | Core doc instance: title, type FK, **status state machine** (draft→under_review→approved→execution→signed→filed→archived), content_json (TipTap), signature tracking, filing tracking, legal_hold, artifact FK, project FK |
| `deal_document_versions` | Immutable version history: version_number, content_json, content_hash (SHA-256), snapshot_reason, storage_path |
| `document_templates` | Jinja2 templates in DB: document_type FK, jurisdiction, version, template_body, variable_schema JSON, tenant_id |
| `template_clauses` | Reusable clause library: name, category (rate_covenant, default_events, etc.), content_json (TipTap nodes), jurisdiction |
| `document_reviews` | Parallel review workflow: reviewer FK, status (pending/approved/rejected/changes_requested), review_version |
| `document_signers` | E-sig signer tracking: name, email, role (issuer/underwriter/bond_counsel/trustee), signing_order, dropbox_sign_signer_id, signed_at, IP |
| `document_audit_log` | Immutable append-only: actor, action (created/edited/signed/viewed/filed/etc.), details JSON, IP, user_agent, timestamp |
| `virtual_data_rooms` | VDR per project: require_nda, nda_template FK, watermark_enabled, settings JSON |
| `vdr_participants` | External party access: email, org, role (viewer/downloader/uploader/admin), access_token, nda_accepted, expires_at |
| `vdr_document_permissions` | Per-document granular: can_view, can_download, can_print per participant |
| `vdr_activity_log` | Page-level analytics: page_number, duration_seconds, action (viewed/downloaded/printed) |

### Modifications to Existing Tables
- **Project**: Add `deal_documents` and `virtual_data_room` relationships
- **User**: Add `role` column (analyst/admin/viewer)

### Single Alembic Migration
One migration file creates all 11 tables + seeds `deal_document_types` with 25+ muni finance document types.

---

## Part 2: Backend Services & API

### New Config (added to `src/munipal/config.py`)
```
# Document Management
document_storage_path, max_document_size_mb

# Dropbox Sign
dropbox_sign_api_key, dropbox_sign_client_id, dropbox_sign_webhook_secret, dropbox_sign_test_mode

# VDR
vdr_base_url, vdr_watermark_font_size

# Feature Flags
document_management_v1, esignature_v1, vdr_v1
```

### New Services

**`deal_document_service.py`** — CRUD + workflow state machine + version snapshots + export
- State machine enforces: draft→under_review (content not empty), under_review→approved (all reviews done), approved→execution (admin only), execution→signed (all signers done via webhook), signed→filed (filing ref), filed→archived
- Legal hold prevents transition to archived or deletion
- Auto-version-snapshot on content save

**`template_service.py`** — Template CRUD + Jinja2 rendering to TipTap JSON + clause library

**`esignature_service.py`** — Dropbox Sign integration
- Creates signature requests from document PDFs
- Webhook handler processes: sent, viewed, signed, all_signed, declined, expired
- On all_signed: auto-downloads signed PDF → stores as Artifact → transitions to "signed"
- Webhook security via HMAC-SHA256 verification (not JWT)

**`vdr_service.py`** — Virtual Data Room management
- Room CRUD, participant invite/revoke, NDA acceptance
- Per-document permission matrix
- Page-level view analytics + duration tracking
- Server-side watermarked PDF generation (participant name + timestamp on every page)
- Bulk ZIP download via Celery task

**`storage_backend.py`** — Abstract storage interface
- `LocalStorageBackend` (wraps current behavior)
- `S3StorageBackend` (uses boto3 + existing AWS settings)
- Auto-selects based on `s3_bucket_name` in config

**`document_renderer.py`** — TipTap JSON → HTML → PDF/DOCX
- HTML→PDF via WeasyPrint (pure Python, no browser binary)
- DOCX via python-docx (already installed)
- Watermarking via pypdf (already installed)

**`document_audit_service.py`** — Immutable audit logging for all doc operations

### API Routes

**`/api/v1/deal-documents/`** (12 endpoints)
- CRUD, content update, status transition, versions, compare, legal hold, export, audit log

**`/api/v1/templates/`** (8 endpoints)
- Template CRUD, render with variables, document types, clause CRUD

**`/api/v1/esignature/`** (5 endpoints)
- Create request, check status, cancel, webhook callback, download signed

**`/api/v1/vdr/`** (12+ endpoints)
- Room CRUD, participants, document permissions, analytics, bulk download
- External token-based access (no JWT): validate, NDA, list docs, view watermarked PDF

**`/api/v1/deal-checklist/`** (2 endpoints)
- Auto-generated closing checklist from document type registry

### Celery Worker Tasks — `workers/tasks/document_tasks.py`
- `export_document_pdf` / `export_document_docx`
- `generate_watermarked_pdf`
- `bulk_zip_download`

---

## Part 3: Frontend Architecture

### New Pages
| Page | Purpose |
|------|---------|
| `DealRoom.tsx` | Main deal document dashboard — document list with status badges, filters, "New Document" wizard |
| `DocumentEditor.tsx` | TipTap rich text editor with toolbar, clause inserter, auto-save |
| `DocumentViewer.tsx` | Read-only view with version history timeline |
| `TemplateLibrary.tsx` | Browse/manage templates and clauses |
| `DataRoom.tsx` | VDR management for project owners |
| `DataRoomViewer.tsx` | External VDR viewer (token-based, separate route) |
| `SignatureStatus.tsx` | E-signature tracking dashboard |
| `ClosingChecklist.tsx` | Auto-generated closing checklist |

### Key Components
- **Editor**: TipTapEditor, EditorToolbar, ClauseInserter, VariableHighlighter, CommentSidebar, TrackChangesToggle, AutoSaveIndicator
- **Documents**: DocumentList, DocumentStatusBadge, StatusTransitionModal, VersionHistory, VersionDiffViewer
- **Signature**: SignerList, SignatureRequestForm, SignatureTimeline
- **VDR**: VdrDashboard, ParticipantManager, DocumentPermissionGrid, ActivityFeed, AnalyticsCharts, NdaGate, WatermarkedViewer (react-pdf + dynamic overlay)

### New Routes
```
/projects/:projectId/deal-room              → DealRoom
/projects/:projectId/deal-room/:docId       → DocumentViewer
/projects/:projectId/deal-room/:docId/edit  → DocumentEditor
/projects/:projectId/deal-room/templates    → TemplateLibrary
/projects/:projectId/data-room              → DataRoom
/projects/:projectId/closing-checklist      → ClosingChecklist
/projects/:projectId/signatures             → SignatureStatus
/vdr/:accessToken                           → DataRoomViewer (external)
/vdr/:accessToken/documents/:docId          → WatermarkedViewer (external)
```

---

## Part 4: Integration Architecture

### Dropbox Sign Flow
1. User clicks "Request Signatures" on approved document
2. Backend exports to PDF → uploads to Dropbox Sign with signer definitions
3. Stores `signature_request_id`, creates `DocumentSigner` rows, transitions to `execution`
4. Dropbox Sign emails signers
5. Webhook callbacks update signer statuses
6. On `all_signed`: download signed PDF → store as Artifact → transition to `signed`

### S3 Key Structure
```
documents/{tenant_id}/{project_id}/{document_id}/
  content/v{version}.json
  exports/v{version}.pdf
  exports/v{version}.docx
  signed/{signature_request_id}.pdf
  watermarked/{participant_id}.pdf
```

### PDF Pipeline
TipTap JSON → HTML (ProseMirror schema) → PDF (WeasyPrint) → Watermark (pypdf)

---

## Part 5: Compliance & Retention

| Rule | Requirement | Implementation |
|------|-------------|----------------|
| MSRB G-9 | 6-year minimum for transaction records | `standard_6yr` retention policy |
| SEC 15c2-12 | EMMA filings indefinite | `indefinite` retention policy |
| IRS | Tax compliance: life of bonds + 3 years | `bond_life_plus_3yr` retention policy |
| ESIGN Act / UETA | E-signatures legally binding | Dropbox Sign compliance |
| Legal Hold | Prevent deletion during litigation | `legal_hold` flag blocks archive/delete |
| Audit Trail | All operations logged | `document_audit_log` append-only table |

---

## Part 6: Implementation Phases

### Phase 1: Foundation (Week 1-2)
- All 11 database tables + Alembic migration + seed data
- StorageBackend abstraction (local + S3)
- Config additions + feature flags
- DealDocumentService (CRUD + state machine + versions)
- DocumentAuditService
- API routes: deal-documents (12 endpoints)
- Frontend: DealRoom.tsx scaffold with document list

### Phase 2: Template Engine (Week 2-3)
- TemplateService with Jinja2 rendering to TipTap JSON
- API routes: templates (8 endpoints)
- 5-8 starter muni templates (NDA, CDA, Board Resolution, etc.)
- Frontend: TemplateLibrary.tsx, TemplateRenderForm.tsx
- "New Document" wizard: type → template → fill variables → create

### Phase 3: Rich Text Editor (Week 3-5) — Largest phase
- TipTap integration: editor, toolbar, table editing
- Extensions: comments, track changes, variable highlighting
- Clause insertion sidebar connected to clause library API
- Auto-save (2s debounce) with version snapshots
- DocumentRenderer: PDF (WeasyPrint) + DOCX (python-docx) export
- Celery tasks for async PDF/DOCX generation
- Frontend: DocumentEditor.tsx, DocumentViewer.tsx

### Phase 4: E-Signature (Week 5-6)
- `dropbox-sign` SDK integration
- ESignatureService + webhook handler
- Signed PDF auto-storage as Artifacts
- Frontend: SignatureRequestForm, SignerList, SignatureStatus page

### Phase 5: Virtual Data Room (Week 6-8)
- VdrService: rooms, participants, permissions, analytics
- Server-side watermarked PDF generation
- NDA gate for external access
- Page-level view tracking
- Bulk ZIP download via Celery
- Frontend: DataRoom, DataRoomViewer, analytics dashboard
- External routes: token-based access (no JWT required)

### Phase 6: Closing Checklist & Compliance (Week 8-9)
- Auto-generated checklist from document type registry
- Retention policy enforcement (Celery beat)
- Legal hold UI
- MSRB G-9 / SEC 15c2-12 filing metadata tracking

### Phase 7: Polish & Integration (Week 9-10)
- Email notifications on status transitions
- Version diff viewer
- Parallel review workflow refinement
- Performance: pagination, lazy loading, PDF caching
- Integration tests for complete workflows

---

## Part 7: New Dependencies

### Python (`pyproject.toml`)
```
weasyprint>=62.0       # HTML→PDF (pure Python)
jinja2>=3.1.3          # Template engine
boto3>=1.34.0          # S3 storage
dropbox-sign>=1.6.0    # E-signature SDK
python-magic>=0.4.27   # MIME type detection
Pillow>=10.2.0         # Image processing for watermarks
```

### npm (`frontend/package.json`)
```
@tiptap/react, @tiptap/starter-kit, @tiptap/pm
@tiptap/extension-table, -table-row, -table-cell, -table-header
@tiptap/extension-highlight, -placeholder, -underline, -text-align, -color, -text-style
@tiptap/extension-collaboration, -collaboration-cursor, -mention
react-pdf, pdfjs-dist
react-dropzone, zustand
```

---

## Key Design Decisions

1. **Project = Deal**: Extend existing `Project` model rather than creating separate `Deal`. `deal_document_types.deal_vertical` provides extensibility for PE/RE.

2. **TipTap JSON in PostgreSQL**: Preserves full ProseMirror doc structure. `content_plaintext` column enables full-text search without JSON parsing.

3. **Server-side watermarking**: pypdf overlay on actual PDF bytes (not just frontend CSS). More secure — downloaded files contain the watermark.

4. **WeasyPrint over Puppeteer/wkhtmltopdf**: Pure Python, no browser binary dependency. Simpler deployment.

5. **Feature flags**: `document_management_v1`, `esignature_v1`, `vdr_v1` — independent toggles for incremental rollout.

6. **Webhook auth separation**: Dropbox Sign webhook uses HMAC-SHA256 verification, not JWT. Separate dependency injector for that route.
