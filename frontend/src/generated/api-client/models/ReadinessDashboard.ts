/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReportDimensionScore } from './ReportDimensionScore';
/**
 * Readiness dashboard section for internal report.
 */
export type ReadinessDashboard = {
    dimensions?: Array<ReportDimensionScore>;
    overall_score: number;
    score_interpretation_guide?: Record<string, any>;
};

