/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Body_publish_delivery_api_v1_register_deals__deal_id__deliveries_post } from '../models/Body_publish_delivery_api_v1_register_deals__deal_id__deliveries_post';
import type { Body_upload_api_v1_register_deals__deal_id__documents_post } from '../models/Body_upload_api_v1_register_deals__deal_id__documents_post';
import type { DealCreate } from '../models/DealCreate';
import type { FolderCreate } from '../models/FolderCreate';
import type { FolderUpdate } from '../models/FolderUpdate';
import type { Quote } from '../models/Quote';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class RegisterPortalService {
    /**
     * Account
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static accountApiV1RegisterAccountGet(
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/register/account',
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Deals
     * @param offset
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static listDealsApiV1RegisterDealsGet(
        offset?: number,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/register/deals',
            headers: {
                'authorization': authorization,
            },
            query: {
                'offset': offset,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Deal
     * @param requestBody
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static createDealApiV1RegisterDealsPost(
        requestBody: DealCreate,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/register/deals',
            headers: {
                'authorization': authorization,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Detail
     * @param dealId
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static detailApiV1RegisterDealsDealIdGet(
        dealId: string,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/register/deals/{deal_id}',
            path: {
                'deal_id': dealId,
            },
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Build
     * @param dealId
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static buildApiV1RegisterDealsDealIdBuildPost(
        dealId: string,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/register/deals/{deal_id}/build',
            path: {
                'deal_id': dealId,
            },
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Checkout
     * @param dealId
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static checkoutApiV1RegisterDealsDealIdCheckoutPost(
        dealId: string,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/register/deals/{deal_id}/checkout',
            path: {
                'deal_id': dealId,
            },
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Publish Delivery
     * Operators publish reviewed engine outputs, including approved registers.
     * @param dealId
     * @param formData
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static publishDeliveryApiV1RegisterDealsDealIdDeliveriesPost(
        dealId: string,
        formData: Body_publish_delivery_api_v1_register_deals__deal_id__deliveries_post,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/register/deals/{deal_id}/deliveries',
            path: {
                'deal_id': dealId,
            },
            headers: {
                'authorization': authorization,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Upload
     * @param dealId
     * @param formData
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static uploadApiV1RegisterDealsDealIdDocumentsPost(
        dealId: string,
        formData: Body_upload_api_v1_register_deals__deal_id__documents_post,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/register/deals/{deal_id}/documents',
            path: {
                'deal_id': dealId,
            },
            headers: {
                'authorization': authorization,
            },
            formData: formData,
            mediaType: 'multipart/form-data',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Download Document
     * @param dealId
     * @param documentId
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static downloadDocumentApiV1RegisterDealsDealIdDocumentsDocumentIdGet(
        dealId: string,
        documentId: string,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/register/deals/{deal_id}/documents/{document_id}',
            path: {
                'deal_id': dealId,
                'document_id': documentId,
            },
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Attach Folder
     * @param dealId
     * @param requestBody
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static attachFolderApiV1RegisterDealsDealIdFoldersPost(
        dealId: string,
        requestBody: FolderCreate,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/register/deals/{deal_id}/folders',
            path: {
                'deal_id': dealId,
            },
            headers: {
                'authorization': authorization,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Update Folder
     * @param dealId
     * @param folderId
     * @param requestBody
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static updateFolderApiV1RegisterDealsDealIdFoldersFolderIdPatch(
        dealId: string,
        folderId: string,
        requestBody: FolderUpdate,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PATCH',
            url: '/api/v1/register/deals/{deal_id}/folders/{folder_id}',
            path: {
                'deal_id': dealId,
                'folder_id': folderId,
            },
            headers: {
                'authorization': authorization,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Quote
     * @param dealId
     * @param requestBody
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static quoteApiV1RegisterDealsDealIdQuotePut(
        dealId: string,
        requestBody: Quote,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/api/v1/register/deals/{deal_id}/quote',
            path: {
                'deal_id': dealId,
            },
            headers: {
                'authorization': authorization,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Download Report
     * @param dealId
     * @param reportId
     * @param authorization
     * @returns any Successful Response
     * @throws ApiError
     */
    public static downloadReportApiV1RegisterDealsDealIdReportsReportIdGet(
        dealId: string,
        reportId: string,
        authorization?: (string | null),
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/register/deals/{deal_id}/reports/{report_id}',
            path: {
                'deal_id': dealId,
                'report_id': reportId,
            },
            headers: {
                'authorization': authorization,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
