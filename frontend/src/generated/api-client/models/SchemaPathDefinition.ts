/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CriticalityTier } from './CriticalityTier';
/**
 * Definition of a canonical schema path.
 *
 * Per playbook: Strict allowlist of valid extraction targets.
 */
export type SchemaPathDefinition = {
    /**
     * Optional enumeration of valid values
     */
    allowed_values?: (Array<string> | null);
    criticality: CriticalityTier;
    description: string;
    display_name: string;
    /**
     * Keywords or patterns to look for when extracting
     */
    extraction_hints?: Array<string>;
    /**
     * Minimum confidence required for auto-approval consideration
     */
    min_confidence?: number;
    /**
     * Dot-notation path (e.g., 'cab.accretionrate')
     */
    path: string;
    /**
     * Expected unit if applicable
     */
    unit?: (string | null);
    /**
     * Optional regex for value validation
     */
    validation_regex?: (string | null);
    /**
     * Expected type: string, number, date, boolean, currency, percentage
     */
    value_type: string;
};

