/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { EvidenceExample } from './EvidenceExample';
import type { EvidenceState } from './EvidenceState';
import type { RequestPriority } from './RequestPriority';
/**
 * Schema for creating an information request.
 */
export type InformationRequestCreate = {
    acceptable_sources?: Array<string>;
    affected_checklist_items?: Array<string>;
    affected_dimensions?: Array<string>;
    common_pitfalls?: Array<string>;
    consequences: string;
    current_evidence_state?: EvidenceState;
    data_points_needed?: Array<string>;
    examples?: Array<EvidenceExample>;
    expected_format?: (string | null);
    /**
     * Link to gap record if tracked separately
     */
    gap_id?: (string | null);
    guidance_overview: string;
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
    specific_questions?: Array<string>;
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
    when_needed?: (string | null);
    who_needs_it?: Array<string>;
    why_it_matters: string;
};

