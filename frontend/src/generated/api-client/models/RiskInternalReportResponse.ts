/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskAdvisoryInput } from './RiskAdvisoryInput';
import type { RiskBenchmarkCohort } from './RiskBenchmarkCohort';
import type { RiskDiagnosticsResponse } from './RiskDiagnosticsResponse';
import type { RiskInternalExecutiveSummary } from './RiskInternalExecutiveSummary';
import type { RiskReadinessInput } from './RiskReadinessInput';
/**
 * Versioned internal risk report contract (JSON + Markdown).
 */
export type RiskInternalReportResponse = {
    advisory_input: RiskAdvisoryInput;
    cohort: RiskBenchmarkCohort;
    contract_version?: string;
    diagnostics: RiskDiagnosticsResponse;
    executive_summary: RiskInternalExecutiveSummary;
    generated_at: string;
    markdown_report: string;
    project_id: string;
    readiness_input: RiskReadinessInput;
};

