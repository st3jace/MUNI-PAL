/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskActionPriority } from './RiskActionPriority';
/**
 * External-safe action summary without internal diagnostics metadata.
 */
export type RiskExternalActionBrief = {
    action_id: string;
    expected_impact: string;
    owner: string;
    priority: RiskActionPriority;
    target_date_hint: string;
    title: string;
};

