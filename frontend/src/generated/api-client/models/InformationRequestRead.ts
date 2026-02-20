/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EvidenceExample } from './EvidenceExample';
import type { EvidenceState } from './EvidenceState';
import type { RequestPriority } from './RequestPriority';
import type { RequestStatus } from './RequestStatus';
/**
 * Schema for reading an information request.
 */
export type InformationRequestRead = {
    acceptable_sources?: Array<string>;
    acknowledged_at?: (string | null);
    acknowledged_by?: (string | null);
    affected_checklist_items?: Array<string>;
    affected_dimensions?: Array<string>;
    common_pitfalls?: Array<string>;
    consequences: string;
    created_at: string;
    current_evidence_state?: EvidenceState;
    data_points_needed?: Array<string>;
    days_overdue?: number;
    deferred_at?: (string | null);
    deferred_reason?: (string | null);
    deferred_review_date?: (string | null);
    escalation_level?: number;
    examples?: Array<EvidenceExample>;
    expected_format?: (string | null);
    /**
     * Link to gap record if tracked separately
     */
    gap_id?: (string | null);
    guidance_overview: string;
    id: string;
    is_overdue?: boolean;
    last_escalated_at?: (string | null);
    linked_artifact_id?: (string | null);
    minimum_confidence?: number;
    /**
     * Schema paths that are missing
     */
    missing_fact_paths: Array<string>;
    priority?: RequestPriority;
    project_id: string;
    regulatory_reference?: (string | null);
    related_requirements?: Array<string>;
    /**
     * Unique code (e.g., 'IR-P2.3-001')
     */
    request_code: string;
    resolution_notes?: (string | null);
    resolved_at?: (string | null);
    resolved_by_fact_ids?: Array<string>;
    specific_questions?: Array<string>;
    status?: RequestStatus;
    submitted_at?: (string | null);
    suggested_approach?: (string | null);
    /**
     * Suggested responsible party
     */
    suggested_owner?: (string | null);
    /**
     * Target completion date
     */
    target_date?: (string | null);
    time_estimate?: (string | null);
    /**
     * Human-readable title
     */
    title: string;
    updated_at: string;
    when_needed?: (string | null);
    who_needs_it?: Array<string>;
    why_it_matters: string;
};

