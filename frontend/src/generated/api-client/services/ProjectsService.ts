/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ProjectCreate } from '../models/ProjectCreate';
import type { ProjectRead } from '../models/ProjectRead';
import type { ProjectUpdate } from '../models/ProjectUpdate';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ProjectsService {
    /**
     * List Projects
     * List all projects accessible to the current user.
     *
     * Returns paginated list with summary information.
     * @param skip
     * @param limit
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listProjectsApiV1ProjectsGet(
        skip?: number,
        limit: number = 50,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/projects/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
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
     * Create Project
     * Create a new project.
     *
     * A project is the workspace for one bond-eligible project.
     * If no playbook_id is provided, the default UCS CAB+SLB playbook is used.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static createProjectApiV1ProjectsPost(
        requestBody: ProjectCreate,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ProjectRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/projects/',
            headers: {
                'authorization': authorization,
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
     * Delete Project
     * Delete a project.
     *
     * WARNING: This will delete all associated artifacts, facts, and deliverables.
     * This action cannot be undone.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns void
     * @throws ApiError
     */
    public static deleteProjectApiV1ProjectsProjectIdDelete(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/projects/{project_id}',
            path: {
                'project_id': projectId,
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
     * Get Project
     * Get a specific project by ID with computed metrics.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static getProjectApiV1ProjectsProjectIdGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ProjectRead> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/projects/{project_id}',
            path: {
                'project_id': projectId,
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
     * Update Project
     * Update a project's metadata.
     * @param projectId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns ProjectRead Successful Response
     * @throws ApiError
     */
    public static updateProjectApiV1ProjectsProjectIdPatch(
        projectId: string,
        requestBody: ProjectUpdate,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<ProjectRead> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/projects/{project_id}',
            path: {
                'project_id': projectId,
            },
            headers: {
                'authorization': authorization,
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
}
