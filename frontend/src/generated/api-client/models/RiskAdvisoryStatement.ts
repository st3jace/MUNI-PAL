/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskBenchmarkPosition } from './RiskBenchmarkPosition';
import type { RiskGapSeverity } from './RiskGapSeverity';
import type { RiskReliabilityBand } from './RiskReliabilityBand';
/**
 * Advisory-oriented statement derived from internal diagnostics.
 */
export type RiskAdvisoryStatement = {
    benchmark_position: RiskBenchmarkPosition;
    dimension_id: string;
    gap_severity: RiskGapSeverity;
    reliability_band: RiskReliabilityBand;
    statement: string;
};

