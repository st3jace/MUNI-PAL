/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { LoginRequest } from '../models/LoginRequest';
import type { RefreshRequest } from '../models/RefreshRequest';
import type { RegisterRequest } from '../models/RegisterRequest';
import type { TokenResponse } from '../models/TokenResponse';
import type { UserProfile } from '../models/UserProfile';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AuthService {
    /**
     * Login
     * Authenticate with email and password.
     * @param requestBody
     * @returns TokenResponse Successful Response
     * @throws ApiError
     */
    public static loginApiV1AuthLoginPost(
        requestBody: LoginRequest,
    ): CancelablePromise<TokenResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/login',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Profile
     * Get the current user's profile.
     * @param authorization Authorization: Bearer <token>
     * @param xUserId User ID for development auth
     * @returns UserProfile Successful Response
     * @throws ApiError
     */
    public static getProfileApiV1AuthMeGet(
        authorization?: (string | null),
        xUserId?: (string | null),
    ): CancelablePromise<UserProfile> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/auth/me',
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
     * Refresh Token
     * Exchange a refresh token for new access + refresh tokens.
     * @param requestBody
     * @returns TokenResponse Successful Response
     * @throws ApiError
     */
    public static refreshTokenApiV1AuthRefreshPost(
        requestBody: RefreshRequest,
    ): CancelablePromise<TokenResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/refresh',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Register
     * Create a new user account and return tokens.
     * @param requestBody
     * @returns TokenResponse Successful Response
     * @throws ApiError
     */
    public static registerApiV1AuthRegisterPost(
        requestBody: RegisterRequest,
    ): CancelablePromise<TokenResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/auth/register',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
