/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskGuardrailStatus } from './RiskGuardrailStatus';
import type { RiskGuardrailThreshold } from './RiskGuardrailThreshold';
/**
 * One quantitative guardrail metric evaluation.
 */
export type RiskGuardrailCheck = {
    benchmark_percentile_band?: (string | null);
    evidence_paths?: Array<string>;
    guardrail_id: string;
    metric_name: string;
    observed_value?: (number | null);
    rationale: string;
    status: RiskGuardrailStatus;
    threshold: RiskGuardrailThreshold;
    unit?: (string | null);
    violation?: boolean;
};

