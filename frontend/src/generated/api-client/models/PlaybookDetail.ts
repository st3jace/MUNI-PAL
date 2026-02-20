/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChecklistItemDefinition } from './ChecklistItemDefinition';
import type { ExtractorDefinition } from './ExtractorDefinition';
import type { SchemaPathDefinition } from './SchemaPathDefinition';
/**
 * Full playbook with all definitions.
 */
export type PlaybookDetail = {
    /**
     * e.g., 'UCS CAB+SLB Waste-to-Energy Revenue Bond'
     */
    bond_archetype: string;
    checklist_item_count?: number;
    checklist_items: Array<ChecklistItemDefinition>;
    created_at: string;
    description: string;
    extractor_count?: number;
    extractors: Array<ExtractorDefinition>;
    id: string;
    is_active?: boolean;
    is_default?: boolean;
    name: string;
    schema_path_count?: number;
    schema_paths: Array<SchemaPathDefinition>;
    updated_at: string;
    /**
     * Semantic version (e.g., '0.2.0')
     */
    version: string;
};

