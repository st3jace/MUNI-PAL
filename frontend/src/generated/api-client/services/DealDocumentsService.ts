/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChecklistItemRead } from '../models/ChecklistItemRead';
import type { ConsistencyCheckRequest } from '../models/ConsistencyCheckRequest';
import type { ConsistencyCheckResult } from '../models/ConsistencyCheckResult';
import type { ContentUpdateRequest } from '../models/ContentUpdateRequest';
import type { DealDocumentCreate } from '../models/DealDocumentCreate';
import type { DealDocumentRead } from '../models/DealDocumentRead';
import type { DealDocumentUpdate } from '../models/DealDocumentUpdate';
import type { DealDocumentVersionRead } from '../models/DealDocumentVersionRead';
import type { StatusTransitionRequest } from '../models/StatusTransitionRequest';
import type { VersionDiff } from '../models/VersionDiff';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DealDocumentsService {
    /**
     * List Deal Documents
     * List deal documents for a project with optional filters.
     * @param projectId Filter by project
     * @param status
     * @param type
     * @param skip
     * @param limit
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listDealDocumentsApiV1DealDocumentsGet(
        projectId: string,
        status?: (string | null),
        type?: (string | null),
        skip?: number,
        limit: number = 50,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deal-documents/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'status': status,
                'type': type,
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Deal Document
     * Create a new deal document, optionally from a template.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns DealDocumentRead Successful Response
     * @throws ApiError
     */
    public static createDealDocumentApiV1DealDocumentsPost(
        requestBody: DealDocumentCreate,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<DealDocumentRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/deal-documents/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
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
     * Get Closing Checklist
     * Auto-generate a closing checklist from the document type registry.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns ChecklistItemRead Successful Response
     * @throws ApiError
     */
    public static getClosingChecklistApiV1DealDocumentsChecklistProjectIdGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Array<ChecklistItemRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deal-documents/checklist/{project_id}',
            path: {
                'project_id': projectId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Document Types
     * List available document types.
     * @param dealVertical
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listDocumentTypesApiV1DealDocumentsTypesGet(
        dealVertical?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Array<any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deal-documents/types',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            query: {
                'deal_vertical': dealVertical,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Deal Document
     * Delete a document. Blocked if under legal hold.
     * @param documentId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns void
     * @throws ApiError
     */
    public static deleteDealDocumentApiV1DealDocumentsDocumentIdDelete(
        documentId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/deal-documents/{document_id}',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Deal Document
     * Get a specific deal document by ID.
     * @param documentId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns DealDocumentRead Successful Response
     * @throws ApiError
     */
    public static getDealDocumentApiV1DealDocumentsDocumentIdGet(
        documentId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<DealDocumentRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deal-documents/{document_id}',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Deal Document
     * Update document metadata (title, assignment).
     * @param documentId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns DealDocumentRead Successful Response
     * @throws ApiError
     */
    public static updateDealDocumentApiV1DealDocumentsDocumentIdPatch(
        documentId: string,
        requestBody: DealDocumentUpdate,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<DealDocumentRead> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/deal-documents/{document_id}',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
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
     * Get Document Audit Log
     * Get the audit trail for a document.
     * @param documentId
     * @param skip
     * @param limit
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getDocumentAuditLogApiV1DealDocumentsDocumentIdAuditLogGet(
        documentId: string,
        skip?: number,
        limit: number = 100,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deal-documents/{document_id}/audit-log',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            query: {
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Compare Versions
     * Compare two version snapshots of a document.
     * @param documentId
     * @param v1
     * @param v2
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns VersionDiff Successful Response
     * @throws ApiError
     */
    public static compareVersionsApiV1DealDocumentsDocumentIdCompareGet(
        documentId: string,
        v1: number,
        v2: number,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<VersionDiff> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deal-documents/{document_id}/compare',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            query: {
                'v1': v1,
                'v2': v2,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Check Document Consistency
     * Validate legal terms in a document against model parameters.
     *
     * This enforces model-to-document parity for covenant and waterfall terms.
     * @param documentId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns ConsistencyCheckResult Successful Response
     * @throws ApiError
     */
    public static checkDocumentConsistencyApiV1DealDocumentsDocumentIdConsistencyCheckPost(
        documentId: string,
        requestBody: ConsistencyCheckRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ConsistencyCheckResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/deal-documents/{document_id}/consistency-check',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
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
     * Update Document Content
     * Update document content (editor auto-save).
     *
     * Optionally creates a version snapshot when auto_snapshot is true.
     * Only allowed when document is in draft or under_review status.
     * @param documentId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns DealDocumentRead Successful Response
     * @throws ApiError
     */
    public static updateDocumentContentApiV1DealDocumentsDocumentIdContentPut(
        documentId: string,
        requestBody: ContentUpdateRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<DealDocumentRead> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/deal-documents/{document_id}/content',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
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
     * Set Legal Hold
     * Set or release legal hold on a document. Admin only.
     * @param documentId
     * @param hold
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns DealDocumentRead Successful Response
     * @throws ApiError
     */
    public static setLegalHoldApiV1DealDocumentsDocumentIdLegalHoldPost(
        documentId: string,
        hold: boolean = true,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<DealDocumentRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/deal-documents/{document_id}/legal-hold',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            query: {
                'hold': hold,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Transition Document Status
     * Transition document to a new workflow status.
     *
     * State machine: draft → under_review → approved → execution →
     * signed → filed → archived.
     * @param documentId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns DealDocumentRead Successful Response
     * @throws ApiError
     */
    public static transitionDocumentStatusApiV1DealDocumentsDocumentIdStatusPost(
        documentId: string,
        requestBody: StatusTransitionRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<DealDocumentRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/deal-documents/{document_id}/status',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
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
     * List Document Versions
     * List all version snapshots for a document.
     * @param documentId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns DealDocumentVersionRead Successful Response
     * @throws ApiError
     */
    public static listDocumentVersionsApiV1DealDocumentsDocumentIdVersionsGet(
        documentId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Array<DealDocumentVersionRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deal-documents/{document_id}/versions',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Version Snapshot
     * Create a manual version snapshot.
     * @param documentId
     * @param reason
     * @param changeSummary
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns DealDocumentVersionRead Successful Response
     * @throws ApiError
     */
    public static createVersionSnapshotApiV1DealDocumentsDocumentIdVersionsPost(
        documentId: string,
        reason: string = 'manual_save',
        changeSummary?: (string | null),
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<DealDocumentVersionRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/deal-documents/{document_id}/versions',
            path: {
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            query: {
                'reason': reason,
                'change_summary': changeSummary,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
