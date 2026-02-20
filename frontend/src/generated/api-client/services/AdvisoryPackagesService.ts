/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DistributionValidation } from '../models/DistributionValidation';
import type { ExternalAdvisoryPackageRead } from '../models/ExternalAdvisoryPackageRead';
import type { GenerateExternalPackageRequest } from '../models/GenerateExternalPackageRequest';
import type { GenerateExternalPackageResponse } from '../models/GenerateExternalPackageResponse';
import type { GenerateInternalReportRequest } from '../models/GenerateInternalReportRequest';
import type { GenerateInternalReportResponse } from '../models/GenerateInternalReportResponse';
import type { InternalReadinessReportRead } from '../models/InternalReadinessReportRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AdvisoryPackagesService {
    /**
     * List External Packages
     * List external packages for a project.
     * @param projectId
     * @param limit
     * @param offset
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listExternalPackagesApiV1AdvisoryPackagesExternalGet(
        projectId: string,
        limit: number = 10,
        offset?: number,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/advisory-packages/external/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
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
     * Generate External Package
     * Generate an external advisory package for a project.
     *
     * Per spec: Professional deliverable for municipal advisors.
     * Does NOT reveal internal gaps, conflicts, or operational status.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns GenerateExternalPackageResponse Successful Response
     * @throws ApiError
     */
    public static generateExternalPackageApiV1AdvisoryPackagesExternalGeneratePost(
        requestBody: GenerateExternalPackageRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<GenerateExternalPackageResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/advisory-packages/external/generate',
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
     * Get Latest External Package
     * Get the latest external package for a project.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getLatestExternalPackageApiV1AdvisoryPackagesExternalProjectProjectIdLatestGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<(ExternalAdvisoryPackageRead | null)> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/advisory-packages/external/project/{project_id}/latest',
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
     * Get External Package
     * Get an external advisory package by ID.
     * @param packageId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns ExternalAdvisoryPackageRead Successful Response
     * @throws ApiError
     */
    public static getExternalPackageApiV1AdvisoryPackagesExternalPackageIdGet(
        packageId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<ExternalAdvisoryPackageRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/advisory-packages/external/{package_id}',
            path: {
                'package_id': packageId,
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
     * Export External Package
     * Export an external advisory package in the specified format.
     *
     * Supported formats: pdf (primary), docx, md (Markdown)
     * @param packageId
     * @param format
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static exportExternalPackageApiV1AdvisoryPackagesExternalPackageIdExportGet(
        packageId: string,
        format: string = 'pdf',
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/advisory-packages/external/{package_id}/export',
            path: {
                'package_id': packageId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            query: {
                'format': format,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Validate External Package
     * Validate an external package for distribution readiness.
     *
     * Per spec: Package must pass quality gates before external distribution.
     * @param packageId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns DistributionValidation Successful Response
     * @throws ApiError
     */
    public static validateExternalPackageApiV1AdvisoryPackagesExternalPackageIdValidateGet(
        packageId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<DistributionValidation> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/advisory-packages/external/{package_id}/validate',
            path: {
                'package_id': packageId,
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
     * List Internal Reports
     * List internal reports for a project.
     * @param projectId
     * @param limit
     * @param offset
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listInternalReportsApiV1AdvisoryPackagesInternalGet(
        projectId: string,
        limit: number = 10,
        offset?: number,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/advisory-packages/internal/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
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
     * Generate Internal Report
     * Generate an internal readiness report for a project.
     *
     * Per spec: Provides complete visibility into readiness state, gaps,
     * information requests, evidence, and checklist progress.
     * NOT for external consumption.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns GenerateInternalReportResponse Successful Response
     * @throws ApiError
     */
    public static generateInternalReportApiV1AdvisoryPackagesInternalGeneratePost(
        requestBody: GenerateInternalReportRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<GenerateInternalReportResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/advisory-packages/internal/generate',
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
     * Get Latest Internal Report
     * Get the latest internal report for a project.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getLatestInternalReportApiV1AdvisoryPackagesInternalProjectProjectIdLatestGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<(InternalReadinessReportRead | null)> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/advisory-packages/internal/project/{project_id}/latest',
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
     * Get Internal Report
     * Get an internal readiness report by ID.
     * @param reportId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns InternalReadinessReportRead Successful Response
     * @throws ApiError
     */
    public static getInternalReportApiV1AdvisoryPackagesInternalReportIdGet(
        reportId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<InternalReadinessReportRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/advisory-packages/internal/{report_id}',
            path: {
                'report_id': reportId,
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
     * Export Internal Report
     * Export an internal report in the specified format.
     *
     * Supported formats: md (Markdown), pdf, html
     * @param reportId
     * @param format
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static exportInternalReportApiV1AdvisoryPackagesInternalReportIdExportGet(
        reportId: string,
        format: string = 'md',
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/advisory-packages/internal/{report_id}/export',
            path: {
                'report_id': reportId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            query: {
                'format': format,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
