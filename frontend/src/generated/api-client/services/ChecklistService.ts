/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChecklistItemDefinition } from '../models/ChecklistItemDefinition';
import type { ChecklistItemStatus } from '../models/ChecklistItemStatus';
import type { ChecklistPhase } from '../models/ChecklistPhase';
import type { ChecklistPhaseSummary } from '../models/ChecklistPhaseSummary';
import type { ChecklistStatus } from '../models/ChecklistStatus';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ChecklistService {
    /**
     * List Checklist Items
     * List checklist items for a project with computed status.
     *
     * Per spec: Checklist phases are:
     * - P1: Issuer Authority & Deal Formation
     * - P2: Project & Technology Definition
     * - P3: Financial Structure & Revenue Model
     * - P4: Risk, Security & Disclosure
     * - P5: SLB Architecture & Final Modeling
     * - P6: Advisor Engagement & Execution
     *
     * Status is computed from linked facts:
     * - not_started: No approved facts for required paths
     * - in_progress: Some required paths covered
     * - blocked: Critical path missing or low confidence
     * - ready: All required paths have approved facts
     * @param projectId
     * @param phase
     * @param statusFilter
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listChecklistItemsApiV1ChecklistGet(
        projectId: string,
        phase?: (ChecklistPhase | null),
        statusFilter?: (ChecklistStatus | null),
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/checklist/',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            query: {
                'project_id': projectId,
                'phase': phase,
                'status_filter': statusFilter,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Definitions
     * List checklist item definitions from playbook.
     *
     * Returns the template definitions without project-specific status.
     * Useful for understanding what evidence is needed.
     * @param phase
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns ChecklistItemDefinition Successful Response
     * @throws ApiError
     */
    public static listDefinitionsApiV1ChecklistDefinitionsGet(
        phase?: (ChecklistPhase | null),
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Array<ChecklistItemDefinition>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/checklist/definitions',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            query: {
                'phase': phase,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Project Gaps
     * Get comprehensive gap analysis for entire project.
     *
     * Returns all missing evidence organized by phase and criticality.
     * Useful for understanding what documents to upload next.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getProjectGapsApiV1ChecklistGapsGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/checklist/gaps',
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
     * Get Phase Summary
     * Get detailed summary for a specific phase.
     *
     * Includes completion percentage and whether all blocking
     * items are ready to proceed to next phase.
     * @param phase
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns ChecklistPhaseSummary Successful Response
     * @throws ApiError
     */
    public static getPhaseSummaryApiV1ChecklistPhasePhaseGet(
        phase: ChecklistPhase,
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<ChecklistPhaseSummary> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/checklist/phase/{phase}',
            path: {
                'phase': phase,
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
     * List Phase Items
     * List all checklist items in a phase with computed status.
     * @param phase
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns ChecklistItemStatus Successful Response
     * @throws ApiError
     */
    public static listPhaseItemsApiV1ChecklistPhasePhaseItemsGet(
        phase: ChecklistPhase,
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Array<ChecklistItemStatus>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/checklist/phase/{phase}/items',
            path: {
                'phase': phase,
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
     * Get Checklist Summary
     * Get a summary of checklist completion by phase.
     *
     * Returns counts and percentages for each P1-P6 phase,
     * including whether each phase can proceed to the next.
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns ChecklistPhaseSummary Successful Response
     * @throws ApiError
     */
    public static getChecklistSummaryApiV1ChecklistSummaryGet(
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, ChecklistPhaseSummary>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/checklist/summary',
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
     * Get Checklist Item
     * Get a specific checklist item with its computed status.
     *
     * Returns the item definition, required fact paths, current status,
     * and any blocking issues.
     * @param itemCode
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns ChecklistItemStatus Successful Response
     * @throws ApiError
     */
    public static getChecklistItemApiV1ChecklistItemCodeGet(
        itemCode: string,
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<ChecklistItemStatus> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/checklist/{item_code}',
            path: {
                'item_code': itemCode,
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
     * Get Item Definition
     * Get the playbook definition for a checklist item.
     *
     * Returns the template without project-specific status.
     * @param itemCode
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns ChecklistItemDefinition Successful Response
     * @throws ApiError
     */
    public static getItemDefinitionApiV1ChecklistItemCodeDefinitionGet(
        itemCode: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<ChecklistItemDefinition> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/checklist/{item_code}/definition',
            path: {
                'item_code': itemCode,
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
     * Get Item Facts
     * Get all facts relevant to a checklist item.
     *
     * Returns facts whose schema paths match the item's required
     * and optional paths.
     * @param itemCode
     * @param projectId
     * @param approvedOnly Only return approved facts
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getItemFactsApiV1ChecklistItemCodeFactsGet(
        itemCode: string,
        projectId: string,
        approvedOnly: boolean = true,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/checklist/{item_code}/facts',
            path: {
                'item_code': itemCode,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
            },
            query: {
                'project_id': projectId,
                'approved_only': approvedOnly,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Checklist Gaps
     * Get missing evidence for a checklist item.
     *
     * Returns the specific schema paths that lack approved facts,
     * enabling targeted document upload or fact entry.
     *
     * Also provides recommendations for closing gaps.
     * @param itemCode
     * @param projectId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getChecklistGapsApiV1ChecklistItemCodeGapsGet(
        itemCode: string,
        projectId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/checklist/{item_code}/gaps',
            path: {
                'item_code': itemCode,
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
}
