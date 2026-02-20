/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Reference to a specific chunk for provenance tracking.
 *
 * Per spec: Every fact must trace back to source evidence.
 */
export type ChunkReference = {
    artifact_id: string;
    chunk_id: string;
    /**
     * Relevant text excerpt
     */
    excerpt?: (string | null);
    page_number?: (number | null);
    sheet_name?: (string | null);
};

