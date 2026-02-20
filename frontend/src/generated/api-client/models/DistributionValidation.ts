/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Validation result for package distribution readiness.
 */
export type DistributionValidation = {
    issues?: Array<string>;
    ready_for_distribution: boolean;
    recommendations?: Array<string>;
    warnings?: Array<string>;
};

