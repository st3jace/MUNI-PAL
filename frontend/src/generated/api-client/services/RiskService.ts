/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskActionAcceptanceRequest } from '../models/RiskActionAcceptanceRequest';
import type { RiskActionAcceptanceResponse } from '../models/RiskActionAcceptanceResponse';
import type { RiskActionSyncResponse } from '../models/RiskActionSyncResponse';
import type { RiskBfmsIntegrationResponse } from '../models/RiskBfmsIntegrationResponse';
import type { RiskDiagnosticsResponse } from '../models/RiskDiagnosticsResponse';
import type { RiskExternalBriefResponse } from '../models/RiskExternalBriefResponse';
import type { RiskInternalReportResponse } from '../models/RiskInternalReportResponse';
import type { RiskOverrideDecisionRequest } from '../models/RiskOverrideDecisionRequest';
import type { RiskOverrideDecisionResponse } from '../models/RiskOverrideDecisionResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class RiskService {
    /**
     * Accept Risk Action
     * Record acceptance of a synthesized risk action for execution.
     * @param actionId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns RiskActionAcceptanceResponse Successful Response
     * @throws ApiError
     */
    public static acceptRiskActionApiV1RiskActionsActionIdAcceptPost(
        actionId: string,
        requestBody: RiskActionAcceptanceRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<RiskActionAcceptanceResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/risk/actions/{action_id}/accept',
            path: {
                'action_id': actionId,
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
    /**
     * Get Risk Bfms Integration Payload
     * Versioned BFMS integration payload with graceful fallback semantics.
     * @param projectId
     * @param sector
     * @param issuerSizeBand
     * @param dealType
     * @param recencyWindow
     * @param sampleSize
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns RiskBfmsIntegrationResponse Successful Response
     * @throws ApiError
     */
    public static getRiskBfmsIntegrationPayloadApiV1RiskBfmsIntegrationGet(
        projectId: string,
        sector: string,
        issuerSizeBand: string,
        dealType: string,
        recencyWindow: string,
        sampleSize: number,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<RiskBfmsIntegrationResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/risk/bfms-integration',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'sector': sector,
                'issuer_size_band': issuerSizeBand,
                'deal_type': dealType,
                'recency_window': recencyWindow,
                'sample_size': sampleSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Risk Diagnostics
     * Internal-only diagnostics endpoint for risk foundation outputs.
     * @param projectId
     * @param sector
     * @param issuerSizeBand
     * @param dealType
     * @param recencyWindow
     * @param sampleSize
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns RiskDiagnosticsResponse Successful Response
     * @throws ApiError
     */
    public static getRiskDiagnosticsApiV1RiskDiagnosticsGet(
        projectId: string,
        sector: string,
        issuerSizeBand: string,
        dealType: string,
        recencyWindow: string,
        sampleSize: number,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<RiskDiagnosticsResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/risk/diagnostics',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'sector': sector,
                'issuer_size_band': issuerSizeBand,
                'deal_type': dealType,
                'recency_window': recencyWindow,
                'sample_size': sampleSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Risk External Brief
     * External-safe advisory risk brief contract.
     * @param projectId
     * @param sector
     * @param issuerSizeBand
     * @param dealType
     * @param recencyWindow
     * @param sampleSize
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns RiskExternalBriefResponse Successful Response
     * @throws ApiError
     */
    public static getRiskExternalBriefApiV1RiskExternalBriefGet(
        projectId: string,
        sector: string,
        issuerSizeBand: string,
        dealType: string,
        recencyWindow: string,
        sampleSize: number,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<RiskExternalBriefResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/risk/external-brief',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'sector': sector,
                'issuer_size_band': issuerSizeBand,
                'deal_type': dealType,
                'recency_window': recencyWindow,
                'sample_size': sampleSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Risk Internal Report
     * Internal risk report contract for readiness and advisory service consumption.
     * @param projectId
     * @param sector
     * @param issuerSizeBand
     * @param dealType
     * @param recencyWindow
     * @param sampleSize
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns RiskInternalReportResponse Successful Response
     * @throws ApiError
     */
    public static getRiskInternalReportApiV1RiskInternalReportGet(
        projectId: string,
        sector: string,
        issuerSizeBand: string,
        dealType: string,
        recencyWindow: string,
        sampleSize: number,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<RiskInternalReportResponse> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/risk/internal-report',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'sector': sector,
                'issuer_size_band': issuerSizeBand,
                'deal_type': dealType,
                'recency_window': recencyWindow,
                'sample_size': sampleSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Record Risk Override Decision
     * Record governed override decisions for risk scores/guardrail outcomes.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns RiskOverrideDecisionResponse Successful Response
     * @throws ApiError
     */
    public static recordRiskOverrideDecisionApiV1RiskOverridesPost(
        requestBody: RiskOverrideDecisionRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<RiskOverrideDecisionResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/risk/overrides',
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
     * Sync Risk Information Requests
     * Auto-create/refresh risk-related information requests from synthesized actions.
     * @param projectId
     * @param sector
     * @param issuerSizeBand
     * @param dealType
     * @param recencyWindow
     * @param sampleSize
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xUserRole User role for development auth
     * @returns RiskActionSyncResponse Successful Response
     * @throws ApiError
     */
    public static syncRiskInformationRequestsApiV1RiskSyncInformationRequestsPost(
        projectId: string,
        sector: string,
        issuerSizeBand: string,
        dealType: string,
        recencyWindow: string,
        sampleSize: number,
        authorization?: (string | null),
        xUserId?: (string | null),
        xUserRole?: (string | null),
    ): CancelablePromise<RiskActionSyncResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/risk/sync-information-requests',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-user-role': xUserRole,
            },
            query: {
                'project_id': projectId,
                'sector': sector,
                'issuer_size_band': issuerSizeBand,
                'deal_type': dealType,
                'recency_window': recencyWindow,
                'sample_size': sampleSize,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
