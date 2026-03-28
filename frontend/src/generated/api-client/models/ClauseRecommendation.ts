/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Recommended clause candidate with scoring details.
 */
export type ClauseRecommendation = {
    category: string;
    clause_id?: (string | null);
    clause_name: string;
    reason: string;
    sample_documents?: Array<string>;
    score: number;
    source: string;
};

