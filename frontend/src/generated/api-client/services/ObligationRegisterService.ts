/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ObligationRegisterIntake } from '../models/ObligationRegisterIntake';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ObligationRegisterService {
    /**
     * Submit Intake
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static submitIntakeApiV1SensingObligationRegisterIntakePost(
        requestBody: ObligationRegisterIntake,
    ): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/sensing/obligation-register/intake',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Intake Privacy Contract
     * @returns any Successful Response
     * @throws ApiError
     */
    public static intakePrivacyContractApiV1SensingObligationRegisterPrivacyGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/sensing/obligation-register/privacy',
        });
    }
}
