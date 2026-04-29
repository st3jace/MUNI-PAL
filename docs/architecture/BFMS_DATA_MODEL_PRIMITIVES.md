# BFMS Data Model to Platform Primitives Mapping

Purpose: map the implemented BFMS database, schemas, services, migrations, and API surfaces to the reusable platform primitives needed for Muni-Pal beyond the initial UCS/WTE use case.

Scope reviewed for ELA-27:

- src/munipal/core/models/project.py
- src/munipal/core/models/playbook.py
- src/munipal/core/models/artifact.py
- src/munipal/core/models/extraction.py
- src/munipal/core/models/fact.py
- src/munipal/core/models/deliverable.py
- src/munipal/core/models/advisory_package.py
- src/munipal/core/models/disclosure.py
- src/munipal/core/models/information_request.py
- src/munipal/core/models/deal_document.py
- src/munipal/core/schemas/project.py
- src/munipal/core/schemas/playbook.py
- src/munipal/core/schemas/artifact.py
- src/munipal/core/schemas/extraction.py
- src/munipal/core/schemas/fact.py
- src/munipal/core/schemas/deliverable.py
- src/munipal/core/schemas/readiness.py
- src/munipal/services/project_service.py
- src/munipal/services/artifact_service.py
- src/munipal/services/fact_service.py
- src/munipal/services/readiness_service.py
- src/munipal/services/deliverable_service.py
- src/munipal/services/playbook_service.py
- alembic/versions/20260127_0001_a1b2c3d4e5f6_initial_schema.py
- alembic/versions/20260129_0001_d4e5f6a7b8c9_add_manual_fact_support.py
- alembic/versions/20260131_0001_f6a7b8c9d0e1_add_v2_deliverable_models.py
- alembic/versions/20260219_0001_a7b8c9d0e1f2_add_fact_canonicalization_columns.py
- alembic/versions/20260220_0001_b8c9d0e1f2a3_add_project_tenant_id.py
- alembic/versions/20260226_0001_g7h8i9j0k1l2_add_document_management_system.py
- alembic/versions/20260331_1334_ffdbab55c977_add_sensing_lead_and_event_tables.py

## Executive summary

The implemented model already has the core evidence-first spine:

Project -> Artifact -> Chunk -> ExtractionJob -> ExtractedFact -> review/canonicalization -> readiness/deliverables.

The strongest implemented primitives are Artifact, Chunk, ExtractedFact, Playbook, and DeliverablePack. The most important platform gaps are sector metadata on Project/Playbook, stronger tenant propagation beyond Project and document templates, and a clearer split between proposed facts, accepted facts, canonical facts, and exportable facts.

ELA-27 does not change runtime behavior. It records the mapping and the architectural gaps that should drive ELA-28 through ELA-33.

## Primitive mapping

### Project

Implemented model:

- SQLAlchemy: src/munipal/core/models/project.py: Project
- Pydantic: src/munipal/core/schemas/project.py: ProjectBase, ProjectCreate, ProjectRead, ProjectSummary
- APIs/services: src/munipal/api/routes/projects.py, src/munipal/services/project_service.py
- Migrations: alembic/versions/20260127_0001_a1b2c3d4e5f6_initial_schema.py, alembic/versions/20260220_0001_b8c9d0e1f2a3_add_project_tenant_id.py

Current fields:

- id, name, description, issuer_name, project_location, target_bond_amount
- tenant_id, owner_id, playbook_id
- relationships to artifacts, extraction_jobs, extracted_facts, deliverable_packs, disclosure_documents, information_requests, internal_reports, external_packages, deal_documents, virtual_data_room

Assessment:

Project is the primary workspace and tenant boundary for one finance opportunity. It is implemented well as the root container, and project routes enforce tenant/owner authorization through AuthorizationService.

Missing fields:

- sector and subsector are not implemented on Project despite frontend references and the broader sector-wise product direction.
- lifecycle/status is thin; Project does not yet expose pilot/onboarding/readiness phase state as a first-class field.
- external operator/issuer/customer identifiers are not first-class.

Duplicated or overlapping fields:

- SensingLead has sector, but Project does not. This creates a lead-to-project handoff gap.
- Project has issuer_name and project_location while sector-specific onboarding may require richer operator metadata later.

Tenant fields:

- Project has tenant_id and list/get routes can filter by tenant. Many child records rely on project_id for tenant inheritance rather than storing tenant_id directly.

Sector fields:

- No Project sector/subsector fields. SensingLead and SensingEvent do have sector. This is the main migration gap for platform reuse.

### Playbook

Implemented model:

- SQLAlchemy: src/munipal/core/models/playbook.py: Playbook
- Pydantic: src/munipal/core/schemas/playbook.py: PlaybookRead, PlaybookDetail, SchemaPathDefinition, ExtractorDefinition
- Services: src/munipal/services/playbook_service.py and src/munipal/services/playbook_data.py
- Migrations: alembic/versions/20260127_0001_a1b2c3d4e5f6_initial_schema.py and alembic/versions/20260127_0002_b2c3d4e5f6a7_seed_ucs_playbook.py

Current fields:

- id, name, version, description, bond_archetype, is_active, is_default
- schema_paths, extractors, checklist_items, readiness_config

Assessment:

Playbook is implemented as versioned configuration for bond-ready criteria. It carries schema paths, extractor definitions, checklist items, and readiness rules in JSON. This is the correct primitive for making Muni-Pal multi-sector.

Missing fields:

- sector, subsector, product_line, and pilot/production maturity are not explicit columns.
- liability disclaimer, deliverable template policy, and migration policy are not explicit first-class fields; some are implied in services/templates.
- no tenant_id or visibility scope for tenant-specific playbooks.

Duplicated or overlapping fields:

- bond_archetype acts as a rough sector/use-case label, but it is not a stable sector taxonomy.
- readiness_config overlaps with readiness_service and playbook_data constants; source of truth should be made explicit in ELA-30/ELA-33.

Sector fields:

- Existing playbook seed is UCS/WTE-oriented. A reusable sector playbook schema should add sector/subsector metadata rather than overloading bond_archetype.

### Artifact

Implemented model:

- SQLAlchemy: src/munipal/core/models/artifact.py: Artifact
- Pydantic: src/munipal/core/schemas/artifact.py: ArtifactRead, ArtifactSummary
- Services/routes: src/munipal/services/artifact_service.py, src/munipal/api/routes/artifacts.py
- Migrations: alembic/versions/20260127_0001_a1b2c3d4e5f6_initial_schema.py and alembic/versions/20260127_0003_c3d4e5f6a7b8_add_artifact_extraction_status.py

Current fields:

- id, filename, display_name, artifact_type, mime_type, file_size_bytes, storage_path
- is_processed, processing_error, is_extracted, last_extraction_job_id, project_id

Assessment:

Artifact is the user-supplied evidence object. Upload validates supported file types, stores the file, and queues processing. This supports the BFMS invariant that statements must be grounded in source material.

Missing fields:

- explicit content hash or immutable source fingerprint on Artifact itself; Chunk has content_hash but Artifact does not.
- uploaded_by, uploaded_at provenance beyond inherited timestamps.
- tenant_id is inherited through Project rather than stored directly.
- source_system/source_url/source_metadata fields are not first-class.

Provenance fields:

- storage_path, filename, mime_type, file_size_bytes, project_id, and chunk content_hash support provenance, but the source-file fingerprint is incomplete at the Artifact level.

Audit fields:

- delete_artifact emits an audit event, but artifact upload itself is not consistently represented as a durable audit row in the inspected models.

### Chunk

Implemented model:

- SQLAlchemy: src/munipal/core/models/artifact.py: Chunk
- Pydantic: src/munipal/core/schemas/artifact.py: ChunkRead, ChunkSummary
- Services/routes: chunking services and artifact chunk routes
- Migrations: alembic/versions/20260127_0001_a1b2c3d4e5f6_initial_schema.py

Current fields:

- id, chunk_type, sequence_number, page_number, sheet_name, section_title, text_content, content_hash, has_image, artifact_id
- relationship to fact_citations through FactChunkAssociation

Assessment:

Chunk is the immutable evidence unit. It is the correct bridge between source files and extracted facts. Page/sheet/section metadata supports advisor-grade citations.

Missing fields:

- immutable flag or replacement policy is not explicit.
- OCR/extraction method/version and source byte/page offsets are not first-class.
- tenant_id inherited through Artifact -> Project.

Provenance fields:

- artifact_id, page_number, sheet_name, section_title, sequence_number, content_hash, and excerpt on FactChunkAssociation provide the core provenance chain.

### ExtractionJob

Implemented model:

- SQLAlchemy: src/munipal/core/models/extraction.py: ExtractionJob
- Pydantic: src/munipal/core/schemas/extraction.py: ExtractionJobRead, ExtractionProgress
- APIs/routes: src/munipal/api/routes/extraction.py
- Migrations: alembic/versions/20260127_0001_a1b2c3d4e5f6_initial_schema.py

Current fields:

- id, job_type, target_schema_paths, artifact_ids, chunk_ids, status, started_at, completed_at
- total_chunks, processed_chunks, facts_extracted, error_message, retry_count, celery_task_id, project_id

Assessment:

ExtractionJob is implemented as an operational run record. It tracks target artifacts/chunks/schema paths and output counts, but it is not yet a complete reproducibility record.

Missing fields:

- extractor/playbook version snapshot at run time.
- model/provider/version and prompt/template version.
- run policy and deterministic parser version.
- tenant_id inherited through project_id.

Provenance fields:

- artifact_ids, chunk_ids, target_schema_paths, project_id, and status support basic traceability.

Audit fields:

- no explicit actor_id/requested_by field on ExtractionJob.
- asynchronous and synchronous paths should have consistent audit events.

### ExtractedFact

Implemented model:

- SQLAlchemy: src/munipal/core/models/fact.py: ExtractedFact, FactChunkAssociation, FactRevision, EvidenceLink
- Pydantic: src/munipal/core/schemas/fact.py: ExtractedFactRead, ExtractedFactSummary, ManualFactCreate, FactReviewRequest, FactRevisionRead
- Services/routes: src/munipal/services/fact_service.py, src/munipal/api/routes/facts.py
- Migrations: alembic/versions/20260127_0001_a1b2c3d4e5f6_initial_schema.py, alembic/versions/20260129_0001_d4e5f6a7b8c9_add_manual_fact_support.py, alembic/versions/20260219_0001_a7b8c9d0e1f2_add_fact_canonicalization_columns.py

Current fields:

- id, schema_path, criticality, source_type, value, value_type, unit
- confidence_score, confidence_rationale
- review_status, reviewed_by, reviewed_at, review_note
- original_value, fingerprint, duplicate_classification, source_trust_score, canonical_score, is_canonical, lifecycle_state
- archive_reason_code, archive_note, archived_by, archived_at
- project_id, extraction_job_id
- revisions, source_chunks, evidence_links

Assessment:

ExtractedFact is the strongest implemented primitive and is explicitly documented in code as the core primitive. It supports extracted and manual sources, review status, revision history, chunk citations, evidence links, duplicate/canonical classification, and lifecycle/archive state.

Accepted fact:

- Accepted fact is currently represented as ExtractedFact where review_status is approved.
- Canonical/export-preferred fact is represented separately by is_canonical and canonical_score.
- Rejected facts are excluded by review_status and lifecycle_state logic.

Missing fields:

- accepted_by and accepted_at are represented generically as reviewed_by and reviewed_at; this is usable but less explicit for advisor review provenance.
- review policy/version and acceptance rationale category are not first-class.
- manual facts can exist without source chunks; they need stronger provenance semantics before export/readiness use.
- tenant_id inherited through project_id.

Review-state fields:

- review_status, reviewed_by, reviewed_at, review_note, lifecycle_state, archive fields, and FactRevision provide the review state and audit trail.

Provenance fields:

- extraction_job_id, FactChunkAssociation, excerpt, EvidenceLink, source_type, original_value, fingerprint, and revisions support the evidence chain.

Audit fields:

- FactRevision is an immutable change log for fact value/status edits.
- FactService emits audit events for canonical refresh and review/archive behavior in inspected service paths.

### Deliverable

Implemented models:

- SQLAlchemy: src/munipal/core/models/deliverable.py: DeliverablePack
- SQLAlchemy: src/munipal/core/models/disclosure.py: DisclosureDocument, DisclosureSection, TBDMarker
- SQLAlchemy: src/munipal/core/models/advisory_package.py: InternalReadinessReport, ExternalAdvisoryPackage
- Pydantic: src/munipal/core/schemas/deliverable.py
- Services/routes: src/munipal/services/deliverable_service.py, src/munipal/api/routes/deliverables.py
- Migrations: alembic/versions/20260127_0001_a1b2c3d4e5f6_initial_schema.py and alembic/versions/20260131_0001_f6a7b8c9d0e1_add_v2_deliverable_models.py

Current fields:

- DeliverablePack: title, generated_for, is_complete, generation timestamps, include_sections, include_appendices, sections, facts_included_count, readiness_score_at_generation, warnings, pdf_storage_path, celery_task_id, project_id
- DisclosureDocument/Section/TBDMarker: disclosure completeness, sections, supporting_fact_ids, missing_fact_paths, TBD resolution state
- InternalReadinessReport and ExternalAdvisoryPackage: bifurcated internal/external package outputs

Assessment:

Deliverable is implemented in three overlapping forms: original DeliverablePack, disclosure documents/TBD markers, and bifurcated internal/external reports. This reflects product evolution but needs consolidation into a clearer product taxonomy.

Warm Handoff Pack:

- Warm Handoff Pack maps primarily to DeliverablePack and ExternalAdvisoryPackage.
- DeliverableService generates nine advisor-facing sections from approved facts, checklist status, readiness, gaps, and evidence index.

Duplicated or overlapping fields:

- DeliverablePack, InternalReadinessReport, ExternalAdvisoryPackage, and DisclosureDocument all carry generation status, readiness/completeness snapshots, storage paths, and project_id.
- ExternalAdvisoryPackage overlaps with Warm Handoff Pack semantics but has a separate model from DeliverablePack.

Missing fields:

- deliverable_type / package_type as a first-class discriminator.
- provenance appendix version, generated_from_fact_ids, generated_from_playbook_version, and generated_from_readiness_run_id.
- human approval/distribution state for external release.

Provenance fields:

- facts_included_count and readiness_score_at_generation exist, but generated facts/source refs are not recorded as immutable per-deliverable provenance except through embedded sections/content.

## Cross-cutting platform field assessment

### Tenant fields

Implemented:

- Project.tenant_id via alembic/versions/20260220_0001_b8c9d0e1f2a3_add_project_tenant_id.py.
- DocumentTemplate.tenant_id and TemplateClause.tenant_id in the DMS migration.
- CurrentTenantId and AuthorizationService enforce tenant filtering at API/service boundaries.

Gaps:

- Child evidence records do not carry tenant_id directly. Artifact, Chunk, ExtractionJob, ExtractedFact, DeliverablePack, DisclosureDocument, and InformationRequest inherit tenant through project_id.
- This is acceptable for now, but background jobs and exports must consistently join through Project before access or release.

### Sector fields

Implemented:

- SensingLead.sector and SensingEvent.sector via alembic/versions/20260331_1334_ffdbab55c977_add_sensing_lead_and_event_tables.py.
- DealDocumentType.deal_vertical supports cross-vertical document type classification.
- Playbook.bond_archetype can approximate a sector/use-case label.

Gaps:

- Project has no sector/subsector field.
- Playbook has no explicit sector/subsector/product_line field.
- Frontend already references sector/subsector on project types, creating visible API/frontend drift.
- Sector-specific readiness/deliverable policies are currently encoded in playbook JSON/constants rather than a validated reusable schema.

### Provenance fields

Implemented:

- Artifact storage metadata and processing status.
- Chunk artifact_id, page_number, sheet_name, section_title, content_hash.
- FactChunkAssociation fact_id/chunk_id/excerpt.
- ExtractedFact extraction_job_id, source_type, confidence_rationale, original_value, fingerprint.
- EvidenceLink link_type/target_id/contribution_weight.
- DisclosureSection supporting_fact_ids and TBDMarker missing_fact_paths/resolved_by_fact_id.

Gaps:

- Artifact lacks file-level content hash.
- ExtractionJob lacks extractor/model/prompt/playbook version snapshots.
- Deliverables lack immutable generated_from fact/source snapshots.
- Manual facts need a stronger provenance contract before they can safely drive exports.

### Review-state fields

Implemented:

- ExtractedFact review_status, reviewed_by, reviewed_at, review_note.
- FactRevision previous/new value and status with changed_by_id/change_reason.
- lifecycle_state and archive fields on ExtractedFact.
- DocumentReview and signature status for deal documents.
- TBDMarker resolution state.

Gaps:

- accepted fact is an interpretation of review_status=approved, not a separate model or view.
- Human review audit is strong for facts, weaker for deliverable release/distribution.
- Manual fact support needs clearer review semantics and export gating.

### Audit fields

Implemented:

- FactRevision for fact changes.
- DocumentAuditLog for deal documents.
- AuditService emits route/service events for security-sensitive actions.
- DealDocumentVersion has content_hash and version history.

Gaps:

- AuditService event persistence was not found as a first-class database table in the scoped model list.
- Artifact upload, extraction job creation/run, deliverable generation, and external release should have consistent actor/time/policy audit trails.
- Some audit fields are embedded per-domain rather than normalized across platform primitives.

## Migration gaps

1. Add Project sector/subsector/product_line fields, or create a ProjectSectorClassification table, to connect sensing leads to BFMS project execution.
2. Add Playbook sector/subsector/product_line/versioned-schema metadata rather than relying only on bond_archetype and JSON blobs.
3. Add Artifact source_hash/uploaded_by/source_metadata fields for stronger immutable source provenance.
4. Add ExtractionJob run provenance: playbook_version, extractor_version, model_provider, model_name, prompt_version, requested_by.
5. Add deliverable generation provenance: generated_from_fact_ids, generated_from_playbook_version, generated_from_readiness_run_id, and approval/release state.
6. Decide whether tenant_id should remain project-inherited for all child records or be denormalized onto high-risk/exported records for simpler policy enforcement.
7. Convert accepted fact semantics into an explicit documented view or helper that means review_status=approved, lifecycle_state active, not archived, and optionally is_canonical for export/readiness selection.

## Duplicated or overlapping fields

1. DeliverablePack, InternalReadinessReport, ExternalAdvisoryPackage, and DisclosureDocument overlap on generation status, completeness/readiness snapshots, project linkage, and storage paths.
2. Playbook readiness_config and services/playbook_data/readiness_service share responsibility for readiness rules.
3. SensingLead sector captures acquisition context, but Project lacks matching sector fields.
4. Fact review_status and lifecycle_state are both necessary but need documented combinations for proposed, accepted, rejected, archived, and canonical/exportable facts.

## Missing fields by primitive

- Project: sector, subsector, lifecycle/status, operator/customer identity, project-sector handoff source.
- Playbook: sector, subsector, product_line, liability_disclaimer, deliverable_template_set, migration_state, tenant/visibility scope.
- Artifact: file hash, uploaded_by, source_uri/source_system/source_metadata, immutable-source flag.
- Chunk: extraction method/version, byte/page offsets, immutable replacement policy.
- ExtractionJob: actor/requested_by, model/prompt/extractor/playbook version snapshots.
- ExtractedFact: explicit accepted_by/accepted_at aliases or view, review policy version, manual-fact provenance contract.
- Deliverable/Warm Handoff Pack: package_type, generated_from_fact_ids, provenance appendix snapshot, human approval/release state.

## Recommended next engineering implications

- ELA-28 should verify Artifact -> Chunk -> Fact provenance and prevent silent overwrite of source refs after review.
- ELA-29 should codify the proposed fact -> accepted fact lifecycle using explicit status/lifecycle combinations.
- ELA-30 should make readiness selection deterministic over accepted/canonical facts only.
- ELA-33 should add the reusable sector playbook schema and resolve the sector/subsector gap for both Project and Playbook.
