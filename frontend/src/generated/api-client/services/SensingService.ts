/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BenchmarkRequest } from '../models/BenchmarkRequest';
import type { EventRequest } from '../models/EventRequest';
import type { LeadCaptureRequest } from '../models/LeadCaptureRequest';
import type { ReadinessRequest } from '../models/ReadinessRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class SensingService {
    /**
     * Benchmark Issuance
     * Benchmark a prospective issuance against the EMMA corpus.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static benchmarkIssuanceApiV1SensingBenchmarkPost(
        requestBody: BenchmarkRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sensing/benchmark',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Track Event
     * Track a funnel interaction event.
     *
     * Events are linked to a session_id and optionally to a lead_id
     * once the prospect completes the lead capture form.
     * @param requestBody
     * @returns string Successful Response
     * @throws ApiError
     */
    public static trackEventApiV1SensingEventPost(
        requestBody: EventRequest,
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sensing/event',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Capture Lead
     * Capture prospect lead when they request the combined report PDF.
     *
     * Stores contact info, deal context, and a snapshot of all report data
     * for follow-up. Links anonymous session events to this lead.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static captureLeadApiV1SensingLeadPost(
        requestBody: LeadCaptureRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sensing/lead',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Leads
     * List captured sensing leads (admin view).
     * @param limit
     * @param offset
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listLeadsApiV1SensingLeadsGet(
        limit: number = 50,
        offset?: number,
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/leads',
            query: {
                'limit': limit,
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Market Intelligence
     * Generate Sector Market Intelligence Report.
     * @param sector Sector (waste, healthcare)
     * @returns any Successful Response
     * @throws ApiError
     */
    public static marketIntelligenceApiV1SensingMarketIntelligenceGet(
        sector: string,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/market-intelligence',
            query: {
                'sector': sector,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Questionnaire
     * Get the readiness self-assessment questionnaire.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getQuestionnaireApiV1SensingQuestionnaireGet(): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/questionnaire',
        });
    }
    /**
     * Readiness Assessment
     * Score a Bond Readiness Self-Assessment.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static readinessAssessmentApiV1SensingReadinessPost(
        requestBody: ReadinessRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sensing/readiness',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Sectors
     * List available sectors with corpus data.
     * @returns string Successful Response
     * @throws ApiError
     */
    public static listSectorsApiV1SensingSectorsGet(): CancelablePromise<Array<Record<string, string>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/sectors',
        });
    }
}
