/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { PlaybookDetail } from '../models/PlaybookDetail';
import type { PlaybookRead } from '../models/PlaybookRead';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class PlaybooksService {
    /**
     * List Playbooks
     * List playbooks.
     * @param includeInactive Include inactive playbooks
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns PlaybookRead Successful Response
     * @throws ApiError
     */
    public static listPlaybooksApiV1PlaybooksGet(
        includeInactive: boolean = false,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, Array<PlaybookRead>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/playbooks/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            query: {
                'include_inactive': includeInactive,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Default Playbook
     * Get the default active playbook.
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns PlaybookRead Successful Response
     * @throws ApiError
     */
    public static getDefaultPlaybookApiV1PlaybooksDefaultGet(
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<PlaybookRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/playbooks/default',
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
     * List Schema Paths
     * List all schema paths with their metadata.
     *
     * Returns enriched schema path definitions including:
     * - path: The dotted schema path (e.g., 'project.canonicaldescription')
     * - display_name: Human-readable name
     * - value_type: Expected data type (string, number, currency, etc.)
     * - criticality: Importance tier (critical, material, secondary)
     * - description: Full explanation of what this field represents
     * - short_description: Brief one-line summary
     * - guidance: Instructions for what content is expected
     * - example: Sample acceptable value
     * - who_needs_it: List of stakeholders who require this information
     *
     * This endpoint is used by the frontend to provide context and guidance
     * to users entering or reviewing facts.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listSchemaPathsApiV1PlaybooksSchemaPathsGet(): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/playbooks/schema-paths',
        });
    }
    /**
     * Get Schema Paths Batch
     * Get metadata for multiple schema paths in a single request.
     *
     * Useful for efficiently loading metadata for all paths shown on a page.
     * Returns a dictionary keyed by schema path.
     *
     * Paths that don't exist in the metadata registry are omitted from the response.
     * @param paths List of schema paths to retrieve
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getSchemaPathsBatchApiV1PlaybooksSchemaPathsBatchGet(
        paths: Array<string>,
    ): CancelablePromise<Record<string, Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/playbooks/schema-paths-batch',
            query: {
                'paths': paths,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Schema Path Detail
     * Get detailed metadata for a specific schema path.
     *
     * Returns comprehensive information about the schema path including:
     * - description: Full explanation of what this field represents in bond/finance terms
     * - short_description: Brief one-line summary
     * - guidance: Instructions for what content is expected
     * - example: Sample acceptable value
     * - who_needs_it: List of stakeholders who require this information
     *
     * This is useful for providing contextual help when users click on
     * schema paths in the Facts Review, Checklist, or other sections.
     * @param schemaPath
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getSchemaPathDetailApiV1PlaybooksSchemaPathsSchemaPathGet(
        schemaPath: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/playbooks/schema-paths/{schema_path}',
            path: {
                'schema_path': schemaPath,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Seed Playbook
     * Seed the default UCS CAB+SLB playbook.
     *
     * This endpoint initializes the system with the UCS Bond Intelligence
     * Configuration Playbook v0.2. Safe to call multiple times - will return
     * existing playbook if already seeded.
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns PlaybookRead Successful Response
     * @throws ApiError
     */
    public static seedPlaybookApiV1PlaybooksSeedPost(
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<PlaybookRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/playbooks/seed',
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
     * Get Playbook
     * Get a playbook by ID with full configuration details.
     * @param playbookId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns PlaybookDetail Successful Response
     * @throws ApiError
     */
    public static getPlaybookApiV1PlaybooksPlaybookIdGet(
        playbookId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<PlaybookDetail> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/playbooks/{playbook_id}',
            path: {
                'playbook_id': playbookId,
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
}
