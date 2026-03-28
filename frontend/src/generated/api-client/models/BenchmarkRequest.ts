/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type BenchmarkRequest = {
    /**
     * Deal size in USD
     */
    deal_size: number;
    /**
     * Years to final maturity
     */
    maturity?: number;
    /**
     * Expected credit rating (e.g., A, BBB+, Aa2)
     */
    rating: string;
    /**
     * Sector (waste, healthcare)
     */
    sector: string;
    /**
     * State abbreviation
     */
    state: string;
};

