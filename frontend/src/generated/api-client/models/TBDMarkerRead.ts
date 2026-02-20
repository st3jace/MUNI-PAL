/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TBDSeverity } from './TBDSeverity';
/**
 * Schema for reading a TBD marker.
 */
export type TBDMarkerRead = {
    created_at: string;
    disclosure_document_id: string;
    id: string;
    is_resolved?: boolean;
    /**
     * Location within the section content
     */
    location: string;
    /**
     * Schema paths that are missing
     */
    missing_fact_paths: Array<string>;
    /**
     * Human-readable reason for the TBD
     */
    reason: string;
    resolved_at?: (string | null);
    resolved_by_fact_id?: (string | null);
    section_id?: (string | null);
    severity?: TBDSeverity;
    updated_at: string;
};

