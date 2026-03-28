/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ClauseCreate } from '../models/ClauseCreate';
import type { ClauseRead } from '../models/ClauseRead';
import type { ClauseRecommendation } from '../models/ClauseRecommendation';
import type { ClauseRecommendationRequest } from '../models/ClauseRecommendationRequest';
import type { ClauseUpdate } from '../models/ClauseUpdate';
import type { TemplateCreate } from '../models/TemplateCreate';
import type { TemplateRead } from '../models/TemplateRead';
import type { TemplateRenderRequest } from '../models/TemplateRenderRequest';
import type { TemplateRenderResult } from '../models/TemplateRenderResult';
import type { TemplateUpdate } from '../models/TemplateUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class TemplatesService {
    /**
     * List Templates
     * List templates with optional filters.
     * @param documentTypeId
     * @param jurisdiction
     * @param activeOnly
     * @param skip
     * @param limit
     * @param authorization Authorization: Bearer <token>
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listTemplatesApiV1TemplatesGet(
        documentTypeId?: (string | null),
        jurisdiction?: (string | null),
        activeOnly: boolean = true,
        skip?: number,
        limit: number = 50,
        authorization?: (string | null),
        xTenantId?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/templates/',
            headers: {
                'authorization': authorization,
                'x-tenant-id': xTenantId,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'document_type_id': documentTypeId,
                'jurisdiction': jurisdiction,
                'active_only': activeOnly,
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Template
     * Create a template in the tenant-scoped library.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns TemplateRead Successful Response
     * @throws ApiError
     */
    public static createTemplateApiV1TemplatesPost(
        requestBody: TemplateCreate,
        authorization?: (string | null),
        xTenantId?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<TemplateRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/templates/',
            headers: {
                'authorization': authorization,
                'x-tenant-id': xTenantId,
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
     * List Clauses
     * List clause library entries.
     * @param templateId
     * @param category
     * @param jurisdiction
     * @param textQuery
     * @param activeOnly
     * @param skip
     * @param limit
     * @param authorization Authorization: Bearer <token>
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listClausesApiV1TemplatesClausesGet(
        templateId?: (string | null),
        category?: (string | null),
        jurisdiction?: (string | null),
        textQuery?: (string | null),
        activeOnly: boolean = true,
        skip?: number,
        limit: number = 100,
        authorization?: (string | null),
        xTenantId?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/templates/clauses',
            headers: {
                'authorization': authorization,
                'x-tenant-id': xTenantId,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'template_id': templateId,
                'category': category,
                'jurisdiction': jurisdiction,
                'text_query': textQuery,
                'active_only': activeOnly,
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Clause
     * Create a clause entry in the reusable clause library.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ClauseRead Successful Response
     * @throws ApiError
     */
    public static createClauseApiV1TemplatesClausesPost(
        requestBody: ClauseCreate,
        authorization?: (string | null),
        xTenantId?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ClauseRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/templates/clauses',
            headers: {
                'authorization': authorization,
                'x-tenant-id': xTenantId,
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
     * Recommend Clauses
     * Recommend clauses based on deal structure and feature signals.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ClauseRecommendation Successful Response
     * @throws ApiError
     */
    public static recommendClausesApiV1TemplatesClausesRecommendationsPost(
        requestBody: ClauseRecommendationRequest,
        authorization?: (string | null),
        xTenantId?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Array<ClauseRecommendation>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/templates/clauses/recommendations',
            headers: {
                'authorization': authorization,
                'x-tenant-id': xTenantId,
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
     * Get Clause
     * Get a clause by ID.
     * @param clauseId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns ClauseRead Successful Response
     * @throws ApiError
     */
    public static getClauseApiV1TemplatesClausesClauseIdGet(
        clauseId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ClauseRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/templates/clauses/{clause_id}',
            path: {
                'clause_id': clauseId,
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
     * Update Clause
     * Update a clause entry.
     * @param clauseId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns ClauseRead Successful Response
     * @throws ApiError
     */
    public static updateClauseApiV1TemplatesClausesClauseIdPatch(
        clauseId: string,
        requestBody: ClauseUpdate,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ClauseRead> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/templates/clauses/{clause_id}',
            path: {
                'clause_id': clauseId,
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
     * Get Template
     * Get a template by ID.
     * @param templateId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns TemplateRead Successful Response
     * @throws ApiError
     */
    public static getTemplateApiV1TemplatesTemplateIdGet(
        templateId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<TemplateRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/templates/{template_id}',
            path: {
                'template_id': templateId,
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
     * Update Template
     * Update a template entry.
     * @param templateId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns TemplateRead Successful Response
     * @throws ApiError
     */
    public static updateTemplateApiV1TemplatesTemplateIdPatch(
        templateId: string,
        requestBody: TemplateUpdate,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<TemplateRead> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/templates/{template_id}',
            path: {
                'template_id': templateId,
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
     * Render Template
     * Render a template to TipTap JSON using input variables.
     * @param templateId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns TemplateRenderResult Successful Response
     * @throws ApiError
     */
    public static renderTemplateApiV1TemplatesTemplateIdRenderPost(
        templateId: string,
        requestBody: TemplateRenderRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<TemplateRenderResult> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/templates/{template_id}/render',
            path: {
                'template_id': templateId,
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
}
