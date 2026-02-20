/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DeliverableSection } from './DeliverableSection';
/**
 * Schema for reading a deliverable pack.
 */
export type DeliverablePackRead = {
    created_at: string;
    /**
     * Mandatory standardized disclaimer per playbook
     */
    disclaimer?: string;
    facts_included_count?: number;
    /**
     * Intended recipient (e.g., 'Bond Counsel Review')
     */
    generated_for: string;
    generation_completed_at?: (string | null);
    generation_started_at?: (string | null);
    id: string;
    is_complete?: boolean;
    project_id: string;
    readiness_score_at_generation?: (number | null);
    sections?: Array<DeliverableSection>;
    title: string;
    updated_at: string;
    warnings?: Array<string>;
};

