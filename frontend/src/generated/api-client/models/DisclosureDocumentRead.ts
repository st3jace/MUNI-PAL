/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DisclosureSectionRead } from './DisclosureSectionRead';
import type { TBDMarkerRead } from './TBDMarkerRead';
/**
 * Schema for reading a disclosure document.
 */
export type DisclosureDocumentRead = {
    completeness_score?: number;
    created_at: string;
    generation_completed_at?: (string | null);
    generation_started_at?: (string | null);
    id: string;
    is_complete?: boolean;
    playbook_version?: (string | null);
    project_id: string;
    sections?: Array<DisclosureSectionRead>;
    tbd_items?: Array<TBDMarkerRead>;
    tbd_summary?: Record<string, number>;
    updated_at: string;
    version?: number;
};

