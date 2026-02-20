/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DisclosureDocumentRead } from '../models/DisclosureDocumentRead';
import type { DisclosureSectionPreview } from '../models/DisclosureSectionPreview';
import type { GenerateDisclosureRequest } from '../models/GenerateDisclosureRequest';
import type { GenerateDisclosureResponse } from '../models/GenerateDisclosureResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class DisclosureService {
    /**
     * List Disclosure Documents
     * List disclosure documents for a project.
     * @param projectId
     * @param limit
     * @param offset
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listDisclosureDocumentsApiV1DisclosureGet(
        projectId: string,
        limit: number = 10,
        offset?: number,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/disclosure/',
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
     * Generate Disclosure Document
     * Generate a disclosure document for a project.
     *
     * Per WP7 spec: Synthesizes content from extracted facts using templates.
     * Every sentence traces to fact(s) or is a templated qualifier.
     * TBD markers are inserted for insufficient evidence.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns GenerateDisclosureResponse Successful Response
     * @throws ApiError
     */
    public static generateDisclosureDocumentApiV1DisclosureGeneratePost(
        requestBody: GenerateDisclosureRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<GenerateDisclosureResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/disclosure/generate',
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
     * Preview Disclosure Section
     * Preview what a disclosure section would contain.
     *
     * Returns information about required facts, available facts,
     * and estimated confidence without generating the full document.
     * @param sectionId
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static previewDisclosureSectionApiV1DisclosurePreviewSectionSectionIdGet(
        sectionId: string,
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<(DisclosureSectionPreview | null)> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/disclosure/preview/section/{section_id}',
            path: {
                'section_id': sectionId,
            },
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
     * Get Latest Disclosure Document
     * Get the latest disclosure document for a project.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getLatestDisclosureDocumentApiV1DisclosureProjectProjectIdLatestGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<(DisclosureDocumentRead | null)> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/disclosure/project/{project_id}/latest',
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
     * Get Disclosure Document
     * Get a disclosure document by ID.
     * @param documentId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns DisclosureDocumentRead Successful Response
     * @throws ApiError
     */
    public static getDisclosureDocumentApiV1DisclosureDocumentIdGet(
        documentId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<DisclosureDocumentRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/disclosure/{document_id}',
            path: {
                'document_id': documentId,
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
     * Export Disclosure Document
     * Export a disclosure document in the specified format.
     *
     * Supported formats: md (Markdown), pdf, docx
     * @param documentId
     * @param format
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static exportDisclosureDocumentApiV1DisclosureDocumentIdExportGet(
        documentId: string,
        format: string = 'md',
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/disclosure/{document_id}/export',
            path: {
                'document_id': documentId,
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
