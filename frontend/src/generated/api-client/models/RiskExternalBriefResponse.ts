/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskAdvisoryStatement } from './RiskAdvisoryStatement';
import type { RiskBenchmarkCohort } from './RiskBenchmarkCohort';
import type { RiskBenchmarkPosition } from './RiskBenchmarkPosition';
import type { RiskExternalActionBrief } from './RiskExternalActionBrief';
import type { RiskExternalComplianceCheck } from './RiskExternalComplianceCheck';
/**
 * Versioned external advisory risk brief contract (JSON + Markdown).
 */
export type RiskExternalBriefResponse = {
    advisory_next_steps?: Array<RiskExternalActionBrief>;
    cohort: RiskBenchmarkCohort;
    compliance_checks?: Array<RiskExternalComplianceCheck>;
    contract_version?: string;
    generated_at: string;
    key_assumptions?: Array<string>;
    markdown_brief: string;
    material_risk_statements?: Array<RiskAdvisoryStatement>;
    mitigant_summary?: Array<string>;
    overall_benchmark_position: RiskBenchmarkPosition;
    overall_posture_score: number;
    project_id: string;
};

