/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ConsistencyDomain } from './ConsistencyDomain';
import type { ConsistencyIssue } from './ConsistencyIssue';
/**
 * Result of comparing legal terms against model terms.
 */
export type ConsistencyCheckResult = {
    checked_fields?: number;
    consistency_score?: number;
    document_id: string;
    domain: ConsistencyDomain;
    extracted_legal_terms?: Record<string, any>;
    is_consistent?: boolean;
    issues?: Array<ConsistencyIssue>;
    matched_fields?: number;
    model_terms?: Record<string, any>;
};

