/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReadinessGap } from './ReadinessGap';
/**
 * Prioritized report of all readiness gaps.
 */
export type ReadinessGapReport = {
    /**
     * Gaps that block deal progression
     */
    critical_gaps?: Array<ReadinessGap>;
    /**
     * Gaps that significantly affect scoring
     */
    material_gaps?: Array<ReadinessGap>;
    overall_score: number;
    /**
     * Top 3-5 actions to improve readiness
     */
    priority_actions?: Array<string>;
    project_id: string;
    /**
     * Nice-to-have evidence
     */
    secondary_gaps?: Array<ReadinessGap>;
};

