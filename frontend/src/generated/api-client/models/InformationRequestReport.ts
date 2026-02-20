/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InformationRequestSummary } from './InformationRequestSummary';
import type { RequestsByOwner } from './RequestsByOwner';
/**
 * Summary report of information requests for a project.
 */
export type InformationRequestReport = {
    by_owner?: Array<RequestsByOwner>;
    critical_count?: number;
    deferred_count?: number;
    high_count?: number;
    in_progress_count?: number;
    low_count?: number;
    medium_count?: number;
    open_count?: number;
    overdue_count?: number;
    overdue_requests?: Array<InformationRequestSummary>;
    project_id: string;
    resolved_count?: number;
    submitted_count?: number;
};

