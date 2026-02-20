/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RequestPriority } from './RequestPriority';
import type { RequestStatus } from './RequestStatus';
/**
 * Summary of an information request for listings.
 */
export type InformationRequestSummary = {
    created_at: string;
    days_overdue?: number;
    id: string;
    is_overdue?: boolean;
    priority: RequestPriority;
    request_code: string;
    status: RequestStatus;
    suggested_owner: (string | null);
    target_date: (string | null);
    title: string;
};

