/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Dedup classification assigned during canonicalization.
 */
export enum FactDuplicateClassification {
    UNIQUE = 'unique',
    DUPLICATE_EXACT = 'duplicate_exact',
    DUPLICATE_SEMANTIC = 'duplicate_semantic',
    CANDIDATE_CONFLICT = 'candidate_conflict',
}
