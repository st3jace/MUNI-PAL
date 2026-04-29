/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Advisor-facing immutable source reference for an accepted fact.
 *
 * Extends the compact chunk reference with stable file and chunk provenance so
 * API/export consumers can trace an approved claim back to Artifact -> Chunk ->
 * Page/Sheet -> source file without lazy-loading database models.
 */
export type SourceReference = {
    artifact_display_name?: (string | null);
    artifact_filename: string;
    artifact_id: string;
    chunk_id: string;
    chunk_type: string;
    content_hash: string;
    /**
     * Relevant text excerpt
     */
    excerpt?: (string | null);
    page_number?: (number | null);
    section_title?: (string | null);
    sequence_number: number;
    sheet_name?: (string | null);
    storage_path: string;
};

