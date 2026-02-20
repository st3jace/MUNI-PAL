/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RequestStatus } from './RequestStatus';
/**
 * Schema for updating an information request.
 */
export type InformationRequestUpdate = {
    deferred_reason?: (string | null);
    deferred_review_date?: (string | null);
    /**
     * Update notes
     */
    notes?: (string | null);
    status?: (RequestStatus | null);
    suggested_owner?: (string | null);
    target_date?: (string | null);
};

