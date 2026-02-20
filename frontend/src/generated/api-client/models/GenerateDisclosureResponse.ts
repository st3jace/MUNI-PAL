/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Response from disclosure generation.
 */
export type GenerateDisclosureResponse = {
    celery_task_id?: (string | null);
    document_id: string;
    message?: (string | null);
    /**
     * queued, running, completed, failed
     */
    status: string;
};

