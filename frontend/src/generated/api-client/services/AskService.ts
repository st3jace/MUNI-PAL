/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AskCitation } from '../models/AskCitation';
import type { AskConversationRead } from '../models/AskConversationRead';
import type { AskCreate } from '../models/AskCreate';
import type { AskHistory } from '../models/AskHistory';
import type { AskQuestion } from '../models/AskQuestion';
import type { AskScope } from '../models/AskScope';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class AskService {
    /**
     * List Conversations
     * @param offset
     * @param authorization
     * @returns AskConversationRead Successful Response
     * @throws ApiError
     */
    public static listConversationsApiV1AskConversationsGet(
        offset?: number,
        authorization?: (string | null),
    ): CancelablePromise<Array<AskConversationRead>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/ask/conversations',
            headers: {
                'authorization': authorization,
            },
            query: {
                'offset': offset,
            },
            errors: {
                401: `Valid access token required`,
                403: `Inactive account or subscription_required; upgrade_url: /pricing`,
                404: `Not found or inaccessible`,
                413: `Request body exceeds 16 KiB`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Create Conversation
     * @param requestBody
     * @param authorization
     * @returns AskConversationRead Successful Response
     * @throws ApiError
     */
    public static createConversationApiV1AskConversationsPost(
        requestBody: AskCreate,
        authorization?: (string | null),
    ): CancelablePromise<AskConversationRead> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ask/conversations',
            headers: {
                'authorization': authorization,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                401: `Valid access token required`,
                403: `Inactive account or subscription_required; upgrade_url: /pricing`,
                404: `Not found or inaccessible`,
                413: `Request body exceeds 16 KiB`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Delete Conversation
     * @param conversationId
     * @param authorization
     * @returns void
     * @throws ApiError
     */
    public static deleteConversationApiV1AskConversationsConversationIdDelete(
        conversationId: string,
        authorization?: (string | null),
    ): CancelablePromise<void> {
        return __request(OpenAPI, {
            method: 'DELETE',
            url: '/api/v1/ask/conversations/{conversation_id}',
            path: {
                'conversation_id': conversationId,
            },
            headers: {
                'authorization': authorization,
            },
            errors: {
                401: `Valid access token required`,
                403: `Inactive account or subscription_required; upgrade_url: /pricing`,
                404: `Not found or inaccessible`,
                413: `Request body exceeds 16 KiB`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Read Conversation
     * @param conversationId
     * @param authorization
     * @returns AskHistory Successful Response
     * @throws ApiError
     */
    public static readConversationApiV1AskConversationsConversationIdGet(
        conversationId: string,
        authorization?: (string | null),
    ): CancelablePromise<AskHistory> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/ask/conversations/{conversation_id}',
            path: {
                'conversation_id': conversationId,
            },
            headers: {
                'authorization': authorization,
            },
            errors: {
                401: `Valid access token required`,
                403: `Inactive account or subscription_required; upgrade_url: /pricing`,
                404: `Not found or inaccessible`,
                413: `Request body exceeds 16 KiB`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Send Message
     * @param conversationId
     * @param requestBody
     * @param authorization
     * @returns AskHistory Successful Response
     * @throws ApiError
     */
    public static sendMessageApiV1AskConversationsConversationIdMessagesPost(
        conversationId: string,
        requestBody: AskQuestion,
        authorization?: (string | null),
    ): CancelablePromise<AskHistory> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/api/v1/ask/conversations/{conversation_id}/messages',
            path: {
                'conversation_id': conversationId,
            },
            headers: {
                'authorization': authorization,
            },
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                401: `Valid access token required`,
                403: `Inactive account or subscription_required; upgrade_url: /pricing`,
                404: `Not found or inaccessible`,
                413: `Request body exceeds 16 KiB`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * List Scopes
     * @param authorization
     * @returns AskScope Successful Response
     * @throws ApiError
     */
    public static listScopesApiV1AskScopesGet(
        authorization?: (string | null),
    ): CancelablePromise<Array<AskScope>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/ask/scopes',
            headers: {
                'authorization': authorization,
            },
            errors: {
                401: `Valid access token required`,
                403: `Inactive account or subscription_required; upgrade_url: /pricing`,
                404: `Not found or inaccessible`,
                413: `Request body exceeds 16 KiB`,
                422: `Validation Error`,
            },
        });
    }
    /**
     * Read Source
     * @param chunkId
     * @param authorization
     * @returns AskCitation Successful Response
     * @throws ApiError
     */
    public static readSourceApiV1AskSourcesChunkIdGet(
        chunkId: string,
        authorization?: (string | null),
    ): CancelablePromise<AskCitation> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/ask/sources/{chunk_id}',
            path: {
                'chunk_id': chunkId,
            },
            headers: {
                'authorization': authorization,
            },
            errors: {
                401: `Valid access token required`,
                403: `Inactive account or subscription_required; upgrade_url: /pricing`,
                404: `Not found or inaccessible`,
                413: `Request body exceeds 16 KiB`,
                422: `Validation Error`,
            },
        });
    }
}
