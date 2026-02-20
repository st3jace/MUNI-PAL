/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskBenchmarkPosition } from './RiskBenchmarkPosition';
/**
 * High-level executive summary for internal risk report consumption.
 */
export type RiskInternalExecutiveSummary = {
    guardrail_breaches?: number;
    guardrail_watches?: number;
    high_priority_actions?: number;
    overall_benchmark_position: RiskBenchmarkPosition;
    overall_posture_score: number;
    reliability_low_dimensions?: number;
    top_findings?: Array<string>;
};

