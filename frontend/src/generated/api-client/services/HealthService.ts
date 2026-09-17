/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class HealthService {
    /**
     * Health Check
     * Basic health check endpoint.
     *
     * Returns service status without checking dependencies.
     * Use this for liveness probes.
     *
     * This is a public surface. It carries no internal filesystem paths and no
     * corpus/provenance details (DEC-008: zero external references to the
     * retired data source; the former ``corpus`` block was removed 2026-09-10).
     * @returns any Successful Response
     * @throws ApiError
     */
    public static healthCheckHealthGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/health',
        });
    }
    /**
     * Readiness Check
     * Readiness check endpoint.
     *
     * Verifies database connectivity. Use this for readiness probes.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static readinessCheckHealthReadyGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/health/ready',
        });
    }
}
