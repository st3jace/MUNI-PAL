/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for creating a new project.
 */
export type ProjectCreate = {
    description?: (string | null);
    issuer_name?: (string | null);
    name: string;
    /**
     * Optional playbook to use. Defaults to latest UCS CAB+SLB playbook.
     */
    playbook_id?: (string | null);
    project_location?: (string | null);
    /**
     * Target bond amount in USD
     */
    target_bond_amount?: (number | null);
};

