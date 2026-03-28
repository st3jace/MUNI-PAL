/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Result of comparing two document versions.
 */
export type VersionDiff = {
    content_a: (Record<string, any> | null);
    content_b: (Record<string, any> | null);
    document_id: string;
    version_a: number;
    version_b: number;
};

