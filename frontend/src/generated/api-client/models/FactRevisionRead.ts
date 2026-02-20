/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReviewStatus } from './ReviewStatus';
/**
 * Schema for reading a fact revision.
 *
 * Per spec: FactRevision is an IMMUTABLE audit log.
 */
export type FactRevisionRead = {
    change_reason?: (string | null);
    changed_by: string;
    created_at: string;
    fact_id: string;
    id: string;
    new_status: ReviewStatus;
    new_value: any;
    previous_status: (ReviewStatus | null);
    previous_value: null;
    revision_number: number;
    updated_at: string;
};

