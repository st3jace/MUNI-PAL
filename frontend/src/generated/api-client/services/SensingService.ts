/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BenchmarkRequest } from '../models/BenchmarkRequest';
import type { CreditSpreadRequest } from '../models/CreditSpreadRequest';
import type { EventRequest } from '../models/EventRequest';
import type { LeadCaptureRequest } from '../models/LeadCaptureRequest';
import type { LeadConvertRequest } from '../models/LeadConvertRequest';
import type { LeadFunnelUpdate } from '../models/LeadFunnelUpdate';
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
     * Coi Benchmarks
     * COI line-item benchmarking data for healthcare sub-sectors.
     *
     * Returns questionnaire items grouped by dimension with COI impact
     * ratings, lead times, and agent-assistable flags, plus aggregate
     * benchmarks (COI gap range, timeline compression, displacement value).
     * @param subSector Healthcare sub-sector (healthcare_hospital, healthcare_senior_living, etc.). Omit for all.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static coiBenchmarksApiV1SensingCoiBenchmarksGet(
        subSector?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/coi-benchmarks',
            query: {
                'sub_sector': subSector,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Coi Deal Benchmarks
     * Deal-level COI benchmark statistics from EMMA/CDIAC/DASNY research.
     *
     * Returns actual deal-level COI statistics (median, p25/p75, by size
     * bucket, by period) for healthcare sub-sectors. Use alongside the
     * existing /coi-benchmarks endpoint which provides line-item checklist
     * data.
     * @param subSector Sub-sector key (hospital, senior_living, fqhc). Omit for all.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static coiDealBenchmarksApiV1SensingCoiDealBenchmarksGet(
        subSector?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/coi-deal-benchmarks',
            query: {
                'sub_sector': subSector,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Credit Spread Monitor
     * Generate Credit Spread Monitor & All-In Cost of Capital report.
     *
     * Returns yield curves, cost-of-capital grid, issuer fee comparisons,
     * corpus-derived spread observations, and recent comparable deals.
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static creditSpreadMonitorApiV1SensingCreditSpreadsPost(
        requestBody: CreditSpreadRequest,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sensing/credit-spreads',
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
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listLeadsApiV1SensingLeadsGet(
        limit: number = 50,
        offset?: number,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/leads',
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
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
     * Get Lead
     * Get a single sensing lead with full detail including report snapshots.
     * @param leadId
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getLeadApiV1SensingLeadsLeadIdGet(
        leadId: string,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/leads/{lead_id}',
            path: {
                'lead_id': leadId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Convert Lead To Project
     * Convert a sensing lead into a BFMS project.
     *
     * This is the critical handoff from top-of-funnel sensing to the advisory
     * engagement workflow. It:
     * 1. Creates a new Project pre-populated from lead data
     * 2. Advances the lead funnel stage to 'engaged'
     * 3. Records a conversion event
     * 4. Returns the new project ID for immediate use
     *
     * The project is created with:
     * - name: derived from organization + sector
     * - issuer_name: from lead organization
     * - target_bond_amount: from lead deal_size_estimate
     * - project_location: from lead state
     * @param leadId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static convertLeadToProjectApiV1SensingLeadsLeadIdConvertToProjectPost(
        leadId: string,
        requestBody: LeadConvertRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sensing/leads/{lead_id}/convert-to-project',
            path: {
                'lead_id': leadId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Lead Funnel
     * Advance a lead through the funnel stages.
     *
     * Stages: report_requested > report_downloaded > contacted > qualified > engaged
     * @param leadId
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @param xTenantId Tenant ID for tenant isolation
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateLeadFunnelApiV1SensingLeadsLeadIdFunnelPatch(
        leadId: string,
        requestBody: LeadFunnelUpdate,
        authorization?: (string | null),
        xUserId?: (string | null),
        xTenantId?: (string | null),
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/sensing/leads/{lead_id}/funnel',
            path: {
                'lead_id': leadId,
            },
            headers: {
                'authorization': authorization,
                'x-user-id': xUserId,
                'x-tenant-id': xTenantId,
            },
            body: requestBody,
            mediaType: 'application/json',
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
     * Get the readiness self-assessment questionnaire for a sector.
     * @param sector Sector (waste, healthcare)
     * @returns any Successful Response
     * @throws ApiError
     */
    public static getQuestionnaireApiV1SensingQuestionnaireGet(
        sector: string = 'waste',
    ): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/questionnaire',
            query: {
                'sector': sector,
            },
            errors: {
                422: `Validation Error`,
            },
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
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listSectorsApiV1SensingSectorsGet(): CancelablePromise<Array<Record<string, any>>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/sectors',
        });
    }
    /**
     * Unsubscribe
     * One-click unsubscribe from the email drip sequence.
     *
     * CAN-SPAM compliant: no login required, immediate effect.
     * @param token Unsubscribe token
     * @returns string Successful Response
     * @throws ApiError
     */
    public static unsubscribeApiV1SensingUnsubscribeGet(
        token: string,
    ): CancelablePromise<Record<string, string>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/unsubscribe',
            query: {
                'token': token,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
