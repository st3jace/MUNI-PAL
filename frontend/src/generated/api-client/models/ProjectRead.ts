/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for reading a project.
 */
export type ProjectRead = {
    approved_fact_count?: number;
    archetype_id?: (string | null);
    archetype_version?: (string | null);
    artifact_count?: number;
    created_at: string;
    description?: (string | null);
    fact_count?: number;
    id: string;
    issuer_name?: (string | null);
    name: string;
    overall_readiness_score?: (number | null);
    owner_id: string;
    playbook_id: string;
    project_location?: (string | null);
    sector?: (string | null);
    subsector?: (string | null);
    /**
     * Target bond amount in USD
     */
    target_bond_amount?: (number | null);
    tenant_id: string;
    updated_at: string;
};

