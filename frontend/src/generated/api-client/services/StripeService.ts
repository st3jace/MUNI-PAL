/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CheckoutRequest } from '../models/CheckoutRequest';
import type { CheckoutResponse } from '../models/CheckoutResponse';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class StripeService {
    /**
     * Create Checkout Session
     * Create a Stripe Checkout Session for an authenticated user.
     * @param requestBody
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns CheckoutResponse Successful Response
     * @throws ApiError
     */
    public static createCheckoutSessionApiV1StripeCreateCheckoutSessionPost(
        requestBody: CheckoutRequest,
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<CheckoutResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/stripe/create-checkout-session',
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
     * Stripe Webhook
     * Handle Stripe webhook events.
     * @returns any Successful Response
     * @throws ApiError
     */
    public static stripeWebhookApiV1StripeWebhookPost(): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/stripe/webhook',
        });
    }
}
