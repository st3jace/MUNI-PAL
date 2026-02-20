/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskActionRequestSyncItem } from './RiskActionRequestSyncItem';
/**
 * Sync summary for risk actions mapped into information requests.
 */
export type RiskActionSyncResponse = {
    created_count?: number;
    project_id: string;
    skipped_count?: number;
    synced_at: string;
    synced_requests?: Array<RiskActionRequestSyncItem>;
    total_actions?: number;
    updated_count?: number;
};

