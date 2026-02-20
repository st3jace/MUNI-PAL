/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InformationRequestCreate } from '../models/InformationRequestCreate';
import type { InformationRequestRead } from '../models/InformationRequestRead';
import type { InformationRequestReport } from '../models/InformationRequestReport';
import type { InformationRequestSummary } from '../models/InformationRequestSummary';
import type { InformationRequestUpdate } from '../models/InformationRequestUpdate';
import type { LinkEvidenceRequest } from '../models/LinkEvidenceRequest';
import type { RequestPriority } from '../models/RequestPriority';
import type { RequestStatus } from '../models/RequestStatus';
import type { ResolveRequestInput } from '../models/ResolveRequestInput';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class InformationRequestsService {
    /**
     * List Information Requests
     * List information requests for a project.
     *
     * Supports filtering by status, priority, and owner.
     * @param projectId
     * @param statusFilter
     * @param priority
     * @param owner
     * @param limit
     * @param offset
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listInformationRequestsApiV1InformationRequestsGet(
        projectId: string,
        statusFilter?: (RequestStatus | null),
        priority?: (RequestPriority | null),
        owner?: (string | null),
        limit: number = 100,
        offset?: number,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/information-requests/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            query: {
                'project_id': projectId,
                'status_filter': statusFilter,
                'priority': priority,
                'owner': owner,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Information Request
     * Create a new information request manually.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns InformationRequestRead Successful Response
     * @throws ApiError
     */
    public static createInformationRequestApiV1InformationRequestsPost(
        requestBody: InformationRequestCreate,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<InformationRequestRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/information-requests/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Generate Information Requests
     * Generate information requests from gap analysis.
     *
     * Per WP8 spec: Each gap type maps to a request template.
     * Requests include bond-domain context, guidance, and examples.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static generateInformationRequestsApiV1InformationRequestsGeneratePost(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/information-requests/generate',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            query: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Overdue Requests
     * Get overdue information requests for a project.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns InformationRequestSummary Successful Response
     * @throws ApiError
     */
    public static getOverdueRequestsApiV1InformationRequestsOverdueProjectIdGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Array<InformationRequestSummary>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/information-requests/overdue/{project_id}',
            path: {
                'project_id': projectId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Request Report
     * Get a summary report of information requests for a project.
     *
     * Includes counts by status/priority, overdue requests, and grouping by owner.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns InformationRequestReport Successful Response
     * @throws ApiError
     */
    public static getRequestReportApiV1InformationRequestsReportProjectIdGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<InformationRequestReport> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/information-requests/report/{project_id}',
            path: {
                'project_id': projectId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Information Request
     * Get an information request by ID.
     * @param requestId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns InformationRequestRead Successful Response
     * @throws ApiError
     */
    public static getInformationRequestApiV1InformationRequestsRequestIdGet(
        requestId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<InformationRequestRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/information-requests/{request_id}',
            path: {
                'request_id': requestId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Information Request
     * Update an information request.
     *
     * Use to change status, assign owner, or set target date.
     * @param requestId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns InformationRequestRead Successful Response
     * @throws ApiError
     */
    public static updateInformationRequestApiV1InformationRequestsRequestIdPatch(
        requestId: string,
        requestBody: InformationRequestUpdate,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<InformationRequestRead> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/information-requests/{request_id}',
            path: {
                'request_id': requestId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Acknowledge Request
     * Acknowledge a request (mark as in_progress).
     *
     * Per WP8 spec: OPEN -> IN_PROGRESS when owner acknowledges.
     * @param requestId
     * @param userId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns InformationRequestRead Successful Response
     * @throws ApiError
     */
    public static acknowledgeRequestApiV1InformationRequestsRequestIdAcknowledgePost(
        requestId: string,
        userId?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<InformationRequestRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/information-requests/{request_id}/acknowledge',
            path: {
                'request_id': requestId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            query: {
                'user_id': userId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Defer Request
     * Defer a request with explanation.
     *
     * Per WP8 spec: Any status -> DEFERRED with recorded reason.
     * @param requestId
     * @param reason
     * @param reviewDate
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns InformationRequestRead Successful Response
     * @throws ApiError
     */
    public static deferRequestApiV1InformationRequestsRequestIdDeferPost(
        requestId: string,
        reason: string,
        reviewDate?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<InformationRequestRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/information-requests/{request_id}/defer',
            path: {
                'request_id': requestId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            query: {
                'reason': reason,
                'review_date': reviewDate,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Link Evidence To Request
     * Link an artifact as evidence for a request.
     *
     * Per WP8 spec: IN_PROGRESS -> SUBMITTED when evidence is uploaded.
     * @param requestId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns InformationRequestRead Successful Response
     * @throws ApiError
     */
    public static linkEvidenceToRequestApiV1InformationRequestsRequestIdEvidencePost(
        requestId: string,
        requestBody: LinkEvidenceRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<InformationRequestRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/information-requests/{request_id}/evidence',
            path: {
                'request_id': requestId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Resolve Request
     * Resolve a request with accepted facts.
     *
     * Per WP8 spec: SUBMITTED -> RESOLVED when facts are accepted via WP3.
     * @param requestId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns InformationRequestRead Successful Response
     * @throws ApiError
     */
    public static resolveRequestApiV1InformationRequestsRequestIdResolvePost(
        requestId: string,
        requestBody: ResolveRequestInput,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<InformationRequestRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/information-requests/{request_id}/resolve',
            path: {
                'request_id': requestId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
