/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReadinessDimension } from './ReadinessDimension';
/**
 * Dimension score for reports.
 */
export type ReportDimensionScore = {
    current_state_explanation: string;
    dimension: ReadinessDimension;
    dimension_name: string;
    recommended_action?: (string | null);
    related_gaps?: Array<Record<string, any>>;
    score: number;
    status_emoji: string;
    supporting_facts?: Array<Record<string, any>>;
    weight: number;
    what_measured: string;
    why_it_matters: string;
};

