/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReadinessAssessment } from '../models/ReadinessAssessment';
import type { ReadinessDimension } from '../models/ReadinessDimension';
import type { ReadinessGapReport } from '../models/ReadinessGapReport';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ReadinessService {
    /**
     * Get Readiness Scores
     * Get complete readiness assessment for all dimensions.
     *
     * Returns dimension-by-dimension scores with weighted contributions
     * to overall score, plus recommendation based on scoring thresholds:
     *
     * - 0.0-3.0: Not Yet Viable - Fundamental evidence gaps
     * - 3.0-5.5: Structurally Viable - Foundation established, gaps remain
     * - 5.5-7.5: Ready for Selective Engagement - Can begin advisor discussions
     * - 7.5-10.0: Ready for Advisor-Led Market Review - Substantially documented
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns ReadinessAssessment Successful Response
     * @throws ApiError
     */
    public static getReadinessScoresApiV1ReadinessGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<ReadinessAssessment> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/readiness/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
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
     * Get Dimension Detail
     * Get detailed scoring breakdown for a specific dimension.
     *
     * Returns:
     * - Score and weighted contribution
     * - Contributing facts with confidence scores
     * - Missing paths with suggested evidence
     * - Improvement suggestions
     *
     * Available dimensions:
     * - issuer_authority: Issuer Authorization & Entity Formation
     * - project_tech: Project & Technology Definition
     * - revenue_feedstock: Revenue Model & Feedstock Supply
     * - cab_financial: CAB Financial Structure & DSCR
     * - risk_security_slb: Risk Assessment & Security Package
     * - slb_verification: SLB KPIs & Verification Plan
     * @param dimension
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getDimensionDetailApiV1ReadinessDimensionDimensionGet(
        dimension: ReadinessDimension,
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/readiness/dimension/{dimension}',
            path: {
                'dimension': dimension,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
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
     * Get Dimension Summary
     * Get quick summary for a dimension without full fact listing.
     * @param dimension
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getDimensionSummaryApiV1ReadinessDimensionDimensionSummaryGet(
        dimension: ReadinessDimension,
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/readiness/dimension/{dimension}/summary',
            path: {
                'dimension': dimension,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
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
     * Get Readiness Explanation
     * Get a narrative explanation of the readiness assessment.
     *
     * Returns human-readable explanations for each dimension
     * and overall recommendation rationale.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getReadinessExplanationApiV1ReadinessExplanationGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/readiness/explanation',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
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
     * Get Readiness Gaps
     * Get a prioritized list of gaps that would improve readiness scores.
     *
     * Per spec: "Gaps are features, not bugs." This endpoint surfaces
     * what evidence is missing to help users understand what to provide.
     *
     * Returns gaps organized by criticality:
     * - critical_gaps: Block deal progression, highest priority
     * - material_gaps: Significantly affect scoring
     * - secondary_gaps: Nice to have, lower priority
     *
     * Also includes priority_actions - top recommended steps.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns ReadinessGapReport Successful Response
     * @throws ApiError
     */
    public static getReadinessGapsApiV1ReadinessGapsGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<ReadinessGapReport> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/readiness/gaps',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            query: {
                'project_id': projectId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
