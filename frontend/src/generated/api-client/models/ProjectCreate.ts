/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for creating a new project.
 */
export type ProjectCreate = {
    /**
     * Stable sector archetype id
     */
    archetype_id?: (string | null);
    /**
     * Sector archetype version
     */
    archetype_version?: (string | null);
    description?: (string | null);
    issuer_name?: (string | null);
    name: string;
    /**
     * Optional playbook to use. Defaults to the canonical Healthcare archetype playbook when configured.
     */
    playbook_id?: (string | null);
    project_location?: (string | null);
    /**
     * Project sector, e.g. healthcare, housing, or waste
     */
    sector?: (string | null);
    /**
     * Project subsector, e.g. healthcare_hospital
     */
    subsector?: (string | null);
    /**
     * Target bond amount in USD
     */
    target_bond_amount?: (number | null);
};

