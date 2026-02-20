/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for creating a manually-entered fact.
 *
 * Unlike ExtractedFactCreate, this doesn't require an extraction job
 * or source chunks since the user is the source.
 */
export type ManualFactCreate = {
    /**
     * Optional note explaining the source or context of this fact
     */
    note?: (string | null);
    project_id: string;
    /**
     * Canonical path from playbook (e.g., 'project.name')
     */
    schema_path: string;
    /**
     * Unit if applicable (USD, MW, tpd, etc.)
     */
    unit?: (string | null);
    /**
     * The fact value
     */
    value: any;
    /**
     * Type hint for value (string, number, date, boolean, currency, percentage)
     */
    value_type?: string;
};

