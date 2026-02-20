/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { TBDMarkerRead } from './TBDMarkerRead';
/**
 * Schema for reading a disclosure section.
 */
export type DisclosureSectionRead = {
    conditional_on?: (string | null);
    confidence?: number;
    content_md?: string;
    created_at: string;
    disclosure_document_id: string;
    id: string;
    is_rendered?: boolean;
    /**
     * Parent section for nested sections
     */
    parent_section_id?: (string | null);
    present_fact_count?: number;
    required_fact_count?: number;
    /**
     * Section identifier (e.g., 'introduction', 'issuer')
     */
    section_id: string;
    /**
     * Order within document
     */
    section_order?: number;
    subsections?: Array<DisclosureSectionRead>;
    supporting_fact_ids?: Array<string>;
    tbd_count?: number;
    tbd_markers?: Array<TBDMarkerRead>;
    /**
     * Section title
     */
    title: string;
    updated_at: string;
};

