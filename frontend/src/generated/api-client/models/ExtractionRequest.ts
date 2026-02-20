/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to create an extraction job.
 */
export type ExtractionRequest = {
    artifact_ids: Array<string>;
    project_id: string;
    /**
     * Optional: specific schema paths to extract. If None, extracts all.
     */
    target_schema_paths?: (Array<string> | null);
};

