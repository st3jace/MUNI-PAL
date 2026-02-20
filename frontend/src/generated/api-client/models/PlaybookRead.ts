/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for reading a playbook.
 */
export type PlaybookRead = {
    /**
     * e.g., 'UCS CAB+SLB Waste-to-Energy Revenue Bond'
     */
    bond_archetype: string;
    checklist_item_count?: number;
    created_at: string;
    description: string;
    extractor_count?: number;
    id: string;
    is_active?: boolean;
    is_default?: boolean;
    name: string;
    schema_path_count?: number;
    updated_at: string;
    /**
     * Semantic version (e.g., '0.2.0')
     */
    version: string;
};

