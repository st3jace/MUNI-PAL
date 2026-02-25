/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskAdvisoryStatement } from './RiskAdvisoryStatement';
import type { RiskBenchmarkCohort } from './RiskBenchmarkCohort';
import type { RiskBenchmarkPosition } from './RiskBenchmarkPosition';
import type { RiskExternalActionBrief } from './RiskExternalActionBrief';
import type { RiskExternalComplianceCheck } from './RiskExternalComplianceCheck';
import type { RiskIntegrationMode } from './RiskIntegrationMode';
/**
 * Versioned BFMS integration contract with graceful fallback metadata.
 *
 * This contract is intentionally compact so BFMS can consume a stable payload
 * without coupling to internal diagnostics internals.
 */
export type RiskBfmsIntegrationResponse = {
    advisory_next_steps?: Array<RiskExternalActionBrief>;
    cohort: RiskBenchmarkCohort;
    compliance_checks?: Array<RiskExternalComplianceCheck>;
    consumer_interpretation_guide?: Array<string>;
    contract_version?: string;
    critical_risk_flags?: Array<string>;
    directional_guidance_only?: boolean;
    external_brief_contract_version?: string;
    fallback_reasons?: Array<string>;
    generated_at: string;
    governance_policy_version?: string;
    integration_mode: RiskIntegrationMode;
    internal_report_contract_version?: string;
    interpretation_guide_version?: string;
    key_assumptions?: Array<string>;
    material_risk_statements?: Array<RiskAdvisoryStatement>;
    overall_benchmark_position: RiskBenchmarkPosition;
    overall_posture_score: number;
    project_id: string;
    reliability_low_dimensions?: number;
    scoring_profile_checksum?: string;
    scoring_profile_version?: string;
};

