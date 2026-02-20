/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExtractionRequest } from '../models/ExtractionRequest';
import type { ExtractionResponse } from '../models/ExtractionResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ExtractionService {
    /**
     * List Extraction Jobs
     * List extraction jobs for a project.
     * @param projectId
     * @param statusFilter Filter by status
     * @param skip
     * @param limit
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listExtractionJobsApiV1ExtractionGet(
        projectId: string,
        statusFilter?: (string | null),
        skip?: number,
        limit: number = 50,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/extraction/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'status_filter': statusFilter,
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Extraction Job
     * Create and queue an extraction job.
     *
     * The job will process the specified artifacts and extract facts
     * using the project's playbook extractors.
     *
     * Returns immediately - use GET /extraction/{job_id} to check status.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractionResponse Successful Response
     * @throws ApiError
     */
    public static createExtractionJobApiV1ExtractionPost(
        requestBody: ExtractionRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ExtractionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/extraction/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Extraction Job
     * Get the status and details of an extraction job.
     * @param jobId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getExtractionJobApiV1ExtractionJobIdGet(
        jobId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/extraction/{job_id}',
            path: {
                'job_id': jobId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Retry Extraction Job
     * Retry a failed extraction job.
     * @param jobId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractionResponse Successful Response
     * @throws ApiError
     */
    public static retryExtractionJobApiV1ExtractionJobIdRetryPost(
        jobId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ExtractionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/extraction/{job_id}/retry',
            path: {
                'job_id': jobId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Run Extraction Job
     * Run an extraction job synchronously.
     *
     * This endpoint is for development mode - in production, extraction
     * runs asynchronously via Celery workers.
     *
     * Processes all artifacts in the job, extracts facts using Claude,
     * and saves them to the database.
     * @param jobId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static runExtractionJobApiV1ExtractionJobIdRunPost(
        jobId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/extraction/{job_id}/run',
            path: {
                'job_id': jobId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
