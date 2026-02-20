/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { InformationRequestSummary } from './InformationRequestSummary';
/**
 * Information requests grouped by owner.
 */
export type RequestsByOwner = {
    in_progress_count?: number;
    open_count?: number;
    overdue_count?: number;
    owner: string;
    requests?: Array<InformationRequestSummary>;
};

