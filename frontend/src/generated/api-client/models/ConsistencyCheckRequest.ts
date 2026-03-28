/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ConsistencyDomain } from './ConsistencyDomain';
/**
 * Request payload for model-to-document consistency checks.
 */
export type ConsistencyCheckRequest = {
    domain: ConsistencyDomain;
    legal_terms?: (Record<string, any> | null);
    model_terms?: Record<string, any>;
    strict?: boolean;
    tolerance_ratio?: number;
};

