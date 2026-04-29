/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RevenueDiversificationRiskProof } from './RevenueDiversificationRiskProof';
import type { RevenueScenarioMix } from './RevenueScenarioMix';
import type { RevenueStreamDefinition } from './RevenueStreamDefinition';
/**
 * Versioned visualization contract for revenue diversification rendering.
 */
export type RevenueDiversificationVisualizationResponse = {
    contract_version?: string;
    covenant_trigger_dscr: number;
    data_quality_notes?: Array<string>;
    debt_service_annual: number;
    generated_at: string;
    non_diesel_combined_coverage_dscr?: (number | null);
    non_diesel_senior_coverage_dscr?: (number | null);
    project_id: string;
    project_name: string;
    revenue_scenarios?: Array<RevenueScenarioMix>;
    risk_proof?: (RevenueDiversificationRiskProof | null);
    stream_definitions?: Array<RevenueStreamDefinition>;
};

