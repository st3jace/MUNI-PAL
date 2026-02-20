/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Benchmark summary statistics for one risk dimension.
 */
export type RiskBenchmarkStats = {
    mitigation_rate: number;
    n_disclosures: number;
    n_issuances: number;
    severity_distribution?: Record<string, number>;
};

