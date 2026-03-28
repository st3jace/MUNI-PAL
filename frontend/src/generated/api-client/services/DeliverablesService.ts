/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DeliverablePackCreate } from '../models/DeliverablePackCreate';
import type { DeliverablePackRead } from '../models/DeliverablePackRead';
import type { DeliverablePackSummary } from '../models/DeliverablePackSummary';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DeliverablesService {
    /**
     * List Packs
     * List deliverable packs for a project.
     *
     * Returns pack summaries ordered by creation date (newest first).
     * @param projectId
     * @param limit
     * @param offset
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns DeliverablePackSummary Successful Response
     * @throws ApiError
     */
    public static listPacksApiV1DeliverablesGet(
        projectId: string,
        limit: number = 20,
        offset?: number,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Array<DeliverablePackSummary>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deliverables/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            query: {
                'project_id': projectId,
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Pack
     * Create and generate a new deliverable pack.
     *
     * By default, the pack will be generated asynchronously via Celery.
     * Use sync=true to generate synchronously (useful for testing without Celery).
     * Poll GET /{pack_id} to check generation status.
     *
     * Per playbook, the pack has 9 sections:
     * 1. Cover
     * 2. Deal Overview Memo
     * 3. Readiness & Gap Report
     * 4. Checklist Status
     * 5. Evidence Index
     * 6. Assumption Register
     * 7. Financial Model Outputs
     * 8. SLB KPI Brief
     * 9. Disclosure Outline
     * @param requestBody
     * @param sync Generate synchronously (for testing without Celery)
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createPackApiV1DeliverablesPost(
        requestBody: DeliverablePackCreate,
        sync: boolean = false,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/deliverables/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            query: {
                'sync': sync,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Pack
     * Get a deliverable pack by ID.
     *
     * Returns full pack content if generation is complete,
     * or status information if still in progress.
     * @param packId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns DeliverablePackRead Successful Response
     * @throws ApiError
     */
    public static getPackApiV1DeliverablesPackIdGet(
        packId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<DeliverablePackRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deliverables/{pack_id}',
            path: {
                'pack_id': packId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Export Markdown
     * Export pack content as combined markdown.
     *
     * Returns all sections concatenated into a single markdown document.
     * @param packId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static exportMarkdownApiV1DeliverablesPackIdExportMarkdownGet(
        packId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deliverables/{pack_id}/export/markdown',
            path: {
                'pack_id': packId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Export Pdf
     * Export a deliverable pack to PDF format.
     *
     * Pack must be fully generated before export.
     * @param packId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static exportPdfApiV1DeliverablesPackIdExportPdfPost(
        packId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/deliverables/{pack_id}/export/pdf',
            path: {
                'pack_id': packId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Regenerate Pack
     * Regenerate a deliverable pack.
     *
     * Useful after new facts have been approved or reviewed.
     * Use sync=true for synchronous regeneration.
     * @param packId
     * @param sync Regenerate synchronously
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static regeneratePackApiV1DeliverablesPackIdRegeneratePost(
        packId: string,
        sync: boolean = false,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/deliverables/{pack_id}/regenerate',
            path: {
                'pack_id': packId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            query: {
                'sync': sync,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Section
     * Get a specific section from a deliverable pack.
     * @param packId
     * @param sectionNumber
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getSectionApiV1DeliverablesPackIdSectionsSectionNumberGet(
        packId: string,
        sectionNumber: number,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deliverables/{pack_id}/sections/{section_number}',
            path: {
                'pack_id': packId,
                'section_number': sectionNumber,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Pack Status
     * Get generation status for a pack.
     *
     * Lightweight endpoint for polling during async generation.
     * @param packId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getPackStatusApiV1DeliverablesPackIdStatusGet(
        packId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/deliverables/{pack_id}/status',
            path: {
                'pack_id': packId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
