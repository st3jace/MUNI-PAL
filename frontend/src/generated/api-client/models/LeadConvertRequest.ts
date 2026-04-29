/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Convert a sensing lead to a BFMS project.
 */
export type LeadConvertRequest = {
    /**
     * User ID to own the new project
     */
    owner_id: string;
    /**
     * Playbook ID (uses default if omitted)
     */
    playbook_id?: (string | null);
    /**
     * Override project name (defaults to '{org} Bond Advisory')
     */
    project_name?: (string | null);
    /**
     * Tenant ID
     */
    tenant_id?: string;
};

