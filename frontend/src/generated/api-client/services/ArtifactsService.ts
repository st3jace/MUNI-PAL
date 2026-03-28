/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ArtifactRead } from '../models/ArtifactRead';
import type { Body_upload_artifact_api_v1_artifacts_upload_post } from '../models/Body_upload_artifact_api_v1_artifacts_upload_post';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ArtifactsService {
    /**
     * List Artifacts
     * List all artifacts for a project.
     * @param projectId
     * @param skip
     * @param limit
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listArtifactsApiV1ArtifactsGet(
        projectId: string,
        skip?: number,
        limit: number = 50,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/artifacts/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'skip': skip,
                'limit': limit,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Upload Artifact
     * Upload an artifact to a project.
     *
     * Accepts PDFs, Word docs, Excel files, CSVs, and images.
     * Returns immediately with artifact ID; chunking happens async via Celery.
     *
     * Per spec: "Artifacts land in the vault; chunks are created async."
     *
     * Supported file types:
     * - PDF (.pdf)
     * - Word documents (.docx)
     * - Excel files (.xlsx, .xls)
     * - CSV (.csv)
     * - Plain text (.txt)
     * - Images (.png, .jpeg)
     * @param formData
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns ArtifactRead Successful Response
     * @throws ApiError
     */
    public static uploadArtifactApiV1ArtifactsUploadPost(
        formData: Body_upload_artifact_api_v1_artifacts_upload_post,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ArtifactRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/artifacts/upload',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
                'x-user-role': xUserRole,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Artifact
     * Delete an artifact.
     *
     * Per spec: Deleting an artifact orphans any ExtractedFacts that cite it,
     * but does not delete those facts (they become unverifiable).
     * @param artifactId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns void
     * @throws ApiError
     */
    public static deleteArtifactApiV1ArtifactsArtifactIdDelete(
        artifactId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/artifacts/{artifact_id}',
            path: {
                'artifact_id': artifactId,
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
     * Get Artifact
     * Get artifact metadata and processing status.
     * @param artifactId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns ArtifactRead Successful Response
     * @throws ApiError
     */
    public static getArtifactApiV1ArtifactsArtifactIdGet(
        artifactId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ArtifactRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/artifacts/{artifact_id}',
            path: {
                'artifact_id': artifactId,
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
     * List Artifact Chunks
     * List all chunks for an artifact.
     *
     * Per spec: Chunks are immutable evidence units (page-based for PDFs,
     * sheet-based for Excel).
     * @param artifactId
     * @param skip
     * @param limit
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listArtifactChunksApiV1ArtifactsArtifactIdChunksGet(
        artifactId: string,
        skip?: number,
        limit: number = 100,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/artifacts/{artifact_id}/chunks',
            path: {
                'artifact_id': artifactId,
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
     * Trigger Processing
     * Process an artifact: extract text and create chunks.
     *
     * This extracts text from PDFs, Excel files, Word documents, etc.
     * and creates searchable chunks for fact extraction.
     * @param artifactId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static triggerProcessingApiV1ArtifactsArtifactIdProcessPost(
        artifactId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/artifacts/{artifact_id}/process',
            path: {
                'artifact_id': artifactId,
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
     * Reset Extraction Status
     * Reset the extraction status of an artifact.
     *
     * This marks the artifact as not extracted, allowing it to be
     * re-processed for fact extraction. Existing facts from this
     * artifact are NOT deleted - they remain in the system.
     * @param artifactId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static resetExtractionStatusApiV1ArtifactsArtifactIdResetExtractionPost(
        artifactId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/artifacts/{artifact_id}/reset-extraction',
            path: {
                'artifact_id': artifactId,
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
}
