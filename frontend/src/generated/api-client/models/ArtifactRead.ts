/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ArtifactType } from './ArtifactType';
/**
 * Schema for reading an artifact.
 */
export type ArtifactRead = {
    artifact_type: ArtifactType;
    chunk_count?: number;
    created_at: string;
    display_name?: (string | null);
    file_size_bytes: number;
    filename: string;
    id: string;
    is_extracted?: boolean;
    is_processed?: boolean;
    last_extraction_job_id?: (string | null);
    mime_type: string;
    processing_error?: (string | null);
    project_id: string;
    storage_path: string;
    updated_at: string;
};

