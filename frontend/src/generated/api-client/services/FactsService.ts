/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CriticalityTier } from '../models/CriticalityTier';
import type { ExtractedFactRead } from '../models/ExtractedFactRead';
import type { ExtractedFactSummary } from '../models/ExtractedFactSummary';
import type { FactArchiveRequest } from '../models/FactArchiveRequest';
import type { FactReviewRequest } from '../models/FactReviewRequest';
import type { FactRevisionRead } from '../models/FactRevisionRead';
import type { FactUnarchiveRequest } from '../models/FactUnarchiveRequest';
import type { ManualFactCreate } from '../models/ManualFactCreate';
import type { MissingPathInfo } from '../models/MissingPathInfo';
import type { ReviewStatus } from '../models/ReviewStatus';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FactsService {
    /**
     * List Facts
     * List extracted facts for a project.
     *
     * Supports filtering by review status, schema path, confidence threshold,
     * and criticality tier. Returns paginated results.
     * @param projectId
     * @param statusFilter
     * @param status Legacy alias for status_filter
     * @param schemaPath Filter by schema path prefix
     * @param schemaPathPrefix Legacy alias for schema_path
     * @param minConfidence
     * @param criticality
     * @param includeArchived Include archived facts
     * @param limit
     * @param offset
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listFactsApiV1FactsGet(
        projectId: string,
        statusFilter?: (ReviewStatus | null),
        status?: (ReviewStatus | null),
        schemaPath?: (string | null),
        schemaPathPrefix?: (string | null),
        minConfidence?: (number | null),
        criticality?: (CriticalityTier | null),
        includeArchived: boolean = false,
        limit: number = 100,
        offset?: number,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/facts/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'status_filter': statusFilter,
                'status': status,
                'schema_path': schemaPath,
                'schema_path_prefix': schemaPathPrefix,
                'min_confidence': minConfidence,
                'criticality': criticality,
                'include_archived': includeArchived,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Facts By Path
     * Get all facts for a specific schema path.
     *
     * Returns facts ordered by confidence score (highest first).
     * @param projectId
     * @param schemaPath Exact schema path to match
     * @param approvedOnly Only return approved facts
     * @param includeArchived Include archived facts
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractedFactSummary Successful Response
     * @throws ApiError
     */
    public static getFactsByPathApiV1FactsByPathGet(
        projectId: string,
        schemaPath: string,
        approvedOnly: boolean = false,
        includeArchived: boolean = false,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Array<ExtractedFactSummary>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/facts/by-path',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'schema_path': schemaPath,
                'approved_only': approvedOnly,
                'include_archived': includeArchived,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Find Conflicts
     * Find conflicting facts in a project.
     *
     * Conflicts occur when multiple extractions produce different values
     * for the same schema path. Returns grouped conflicts with all
     * competing facts listed.
     * @param projectId
     * @param schemaPath Specific path to check
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static findConflictsApiV1FactsConflictsGet(
        projectId: string,
        schemaPath?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, Array<Record<string, any>>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/facts/conflicts/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'schema_path': schemaPath,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Conflict Queue
     * Reviewer queue for unresolved conflicts and stale pending review items.
     * @param projectId
     * @param criticality Filter by criticality
     * @param phase Filter by phase (P1-P6)
     * @param maxAgeDays Only include older pending items
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getConflictQueueApiV1FactsConflictsQueueGet(
        projectId: string,
        criticality?: (string | null),
        phase?: (string | null),
        maxAgeDays?: (number | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, Array<Record<string, any>>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/facts/conflicts/queue',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'criticality': criticality,
                'phase': phase,
                'max_age_days': maxAgeDays,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Resolve Conflicts
     * Automatically resolve fact conflicts using specified strategy.
     *
     * Available strategies:
     * - highest_confidence: Keep the fact with highest confidence score,
     * reject others
     *
     * Returns list of resolution records showing which facts were kept
     * and which were rejected.
     * @param projectId
     * @param strategy Resolution strategy: highest_confidence
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static resolveConflictsApiV1FactsConflictsResolvePost(
        projectId: string,
        strategy: string = 'highest_confidence',
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, Array<Record<string, any>>>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/facts/conflicts/resolve',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'strategy': strategy,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Review Counts
     * Get count of facts by review status for a project.
     *
     * Useful for dashboard displays showing pending review queue.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns number Successful Response
     * @throws ApiError
     */
    public static getReviewCountsApiV1FactsCountsGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, number>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/facts/counts',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
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
     * Create Manual Fact
     * Create a manually-entered fact.
     *
     * Manual facts are entered by users when they have information but
     * don't have documentation to extract from. These facts:
     * - Have source_type='manual'
     * - Have confidence_score=1.0 (user is authoritative)
     * - Don't require source chunks (no extraction job)
     * - Follow the same approval workflow as extracted facts
     *
     * Use auto_approve=true if you trust the input and want to skip review.
     * @param createdBy ID of user creating the fact
     * @param requestBody
     * @param autoApprove If true, fact is immediately approved without review
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractedFactRead Successful Response
     * @throws ApiError
     */
    public static createManualFactApiV1FactsManualPost(
        createdBy: string,
        requestBody: ManualFactCreate,
        autoApprove: boolean = false,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ExtractedFactRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/facts/manual',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'created_by': createdBy,
                'auto_approve': autoApprove,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Missing Paths
     * Get schema paths that don't have approved facts yet.
     *
     * Returns paths that are required by checklist items but don't have
     * approved facts. Useful for identifying what manual facts need to be entered.
     *
     * Sorted by criticality (critical first) then by phase.
     * @param projectId
     * @param phase Filter by checklist phase (P1-P6)
     * @param criticality Filter by criticality tier
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns MissingPathInfo Successful Response
     * @throws ApiError
     */
    public static getMissingPathsApiV1FactsMissingPathsGet(
        projectId: string,
        phase?: (string | null),
        criticality?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Array<MissingPathInfo>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/facts/missing-paths',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'phase': phase,
                'criticality': criticality,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Fact
     * Get a specific fact with full provenance chain.
     *
     * Returns the fact value, confidence score, source chunk references,
     * and review status. Use the /revisions endpoint for revision history.
     * @param factId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractedFactRead Successful Response
     * @throws ApiError
     */
    public static getFactApiV1FactsFactIdGet(
        factId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ExtractedFactRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/facts/{fact_id}',
            path: {
                'fact_id': factId,
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
     * Approve Fact
     * Approve an extracted fact.
     *
     * Per spec: "AI proposes; humans approve." This endpoint allows a human
     * reviewer to approve a fact, optionally with corrections.
     *
     * If corrected_value is provided, the original AI-extracted value is
     * preserved and the corrected value becomes the current value.
     * @param factId
     * @param reviewerId ID of user approving
     * @param correctedValue
     * @param note
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractedFactRead Successful Response
     * @throws ApiError
     */
    public static approveFactApiV1FactsFactIdApprovePost(
        factId: string,
        reviewerId?: (string | null),
        correctedValue?: null,
        note?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ExtractedFactRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/facts/{fact_id}/approve',
            path: {
                'fact_id': factId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'reviewer_id': reviewerId,
                'corrected_value': correctedValue,
                'note': note,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Archive Fact
     * Archive a superseded or redundant fact while preserving provenance/audit trail.
     * @param factId
     * @param requestBody
     * @param reviewerId ID of user archiving
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractedFactRead Successful Response
     * @throws ApiError
     */
    public static archiveFactApiV1FactsFactIdArchivePost(
        factId: string,
        requestBody: FactArchiveRequest,
        reviewerId?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ExtractedFactRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/facts/{fact_id}/archive',
            path: {
                'fact_id': factId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'reviewer_id': reviewerId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Reject Fact
     * Reject an extracted fact.
     *
     * The fact will be marked as rejected and will not contribute to
     * readiness scoring or checklist completion.
     * @param factId
     * @param reviewerId ID of user rejecting
     * @param reason
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractedFactRead Successful Response
     * @throws ApiError
     */
    public static rejectFactApiV1FactsFactIdRejectPost(
        factId: string,
        reviewerId?: (string | null),
        reason?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ExtractedFactRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/facts/{fact_id}/reject',
            path: {
                'fact_id': factId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'reviewer_id': reviewerId,
                'reason': reason,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Review Fact
     * Submit a review for an extracted fact.
     *
     * Per spec: "AI proposes; humans approve." This endpoint allows human
     * reviewers to approve, reject, or flag facts for revision.
     *
     * - approve: Accept the fact (optionally with corrections)
     * - reject: Reject the fact (it won't contribute to readiness)
     * - needs_revision: Flag for further review without rejecting
     * @param factId
     * @param requestBody
     * @param reviewerId ID of user submitting review
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractedFactRead Successful Response
     * @throws ApiError
     */
    public static reviewFactApiV1FactsFactIdReviewPost(
        factId: string,
        requestBody: FactReviewRequest,
        reviewerId?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ExtractedFactRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/facts/{fact_id}/review',
            path: {
                'fact_id': factId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'reviewer_id': reviewerId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Request Revision
     * Request revision of an extracted fact.
     *
     * Flags the fact as needing human attention without fully rejecting it.
     * Use this when the extracted value seems wrong but you want to
     * investigate further rather than outright reject.
     * @param factId
     * @param revisionNote
     * @param reviewerId ID of user requesting revision
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractedFactRead Successful Response
     * @throws ApiError
     */
    public static requestRevisionApiV1FactsFactIdRevisePost(
        factId: string,
        revisionNote: string,
        reviewerId?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ExtractedFactRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/facts/{fact_id}/revise',
            path: {
                'fact_id': factId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'revision_note': revisionNote,
                'reviewer_id': reviewerId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Fact Revisions
     * Get the full revision history for a fact.
     *
     * Per spec: FactRevision is an immutable audit log of all changes.
     * Returns revisions in chronological order (oldest first).
     * @param factId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns FactRevisionRead Successful Response
     * @throws ApiError
     */
    public static listFactRevisionsApiV1FactsFactIdRevisionsGet(
        factId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Array<FactRevisionRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/facts/{fact_id}/revisions',
            path: {
                'fact_id': factId,
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
     * Unarchive Fact
     * Restore an archived fact to active lifecycle state.
     * @param factId
     * @param requestBody
     * @param reviewerId ID of user unarchiving
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ExtractedFactRead Successful Response
     * @throws ApiError
     */
    public static unarchiveFactApiV1FactsFactIdUnarchivePost(
        factId: string,
        requestBody: FactUnarchiveRequest,
        reviewerId?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ExtractedFactRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/facts/{fact_id}/unarchive',
            path: {
                'fact_id': factId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'reviewer_id': reviewerId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
