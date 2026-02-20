/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskActionItem } from './RiskActionItem';
import type { RiskBenchmarkCohort } from './RiskBenchmarkCohort';
import type { RiskDimensionDiagnostics } from './RiskDimensionDiagnostics';
import type { RiskGuardrailCheck } from './RiskGuardrailCheck';
import type { RiskOverallPosture } from './RiskOverallPosture';
/**
 * Internal diagnostics response for risk reporting foundation.
 */
export type RiskDiagnosticsResponse = {
    actions: Array<RiskActionItem>;
    cohort: RiskBenchmarkCohort;
    dimensions: Array<RiskDimensionDiagnostics>;
    guardrails: Array<RiskGuardrailCheck>;
    overall_posture: RiskOverallPosture;
    project_id: string;
};

