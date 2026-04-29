/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChunkReference } from './ChunkReference';
import type { CriticalityTier } from './CriticalityTier';
import type { FactDuplicateClassification } from './FactDuplicateClassification';
import type { FactLifecycleState } from './FactLifecycleState';
import type { ReviewStatus } from './ReviewStatus';
import type { SourceReference } from './SourceReference';
import type { SourceType } from './SourceType';
/**
 * Schema for reading a fact (extracted or manual).
 */
export type ExtractedFactRead = {
    archive_note?: (string | null);
    archive_reason_code?: (string | null);
    archived_at?: (string | null);
    archived_by?: (string | null);
    /**
     * True only for active, human-accepted facts eligible for readiness/export outputs.
     */
    can_drive_outputs?: boolean;
    canonical_score?: number;
    /**
     * Why the AI assigned this confidence, or note for manual facts
     */
    confidence_rationale?: (string | null);
    /**
     * AI confidence in extraction (0.0-1.0), or 1.0 for manual facts
     */
    confidence_score: number;
    created_at: string;
    /**
     * Importance tier from playbook
     */
    criticality?: CriticalityTier;
    duplicate_classification?: FactDuplicateClassification;
    extraction_job_id?: (string | null);
    fingerprint?: (string | null);
    id: string;
    is_canonical?: boolean;
    lifecycle_state?: FactLifecycleState;
    /**
     * Original AI-extracted value if human corrected it
     */
    original_value?: null;
    project_id: string;
    /**
     * Deterministic SHA-256 fingerprint of ordered source_refs.
     */
    provenance_fingerprint?: (string | null);
    /**
     * Human-review lifecycle stage: proposed, accepted, rejected, needs_revision, or archived.
     */
    review_lifecycle_stage?: string;
    review_note?: (string | null);
    review_status?: ReviewStatus;
    reviewed_at?: (string | null);
    reviewed_by?: (string | null);
    /**
     * Canonical path from playbook (e.g., 'cab.accretionrate', 'project.name')
     */
    schema_path: string;
    source_chunks?: Array<ChunkReference>;
    /**
     * Advisor-facing stable source references: Artifact -> Chunk -> Page/Sheet -> source file.
     */
    source_refs?: Array<SourceReference>;
    source_trust_score?: number;
    /**
     * Whether fact was AI-extracted or manually entered
     */
    source_type?: SourceType;
    /**
     * Unit if applicable (USD, MW, tpd, etc.)
     */
    unit?: (string | null);
    updated_at: string;
    /**
     * The extracted value (string, number, date, etc.)
     */
    value: any;
    /**
     * Type hint for value (string, number, date, boolean, currency, percentage)
     */
    value_type?: string;
};

