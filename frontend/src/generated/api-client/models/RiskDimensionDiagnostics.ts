/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskBenchmarkPosition } from './RiskBenchmarkPosition';
import type { RiskBenchmarkStats } from './RiskBenchmarkStats';
import type { RiskConfidence } from './RiskConfidence';
import type { RiskGapSeverity } from './RiskGapSeverity';
import type { RiskProjectStatus } from './RiskProjectStatus';
/**
 * Canonical risk diagnostics payload per dimension.
 */
export type RiskDimensionDiagnostics = {
    advanced_analytics_applied?: boolean;
    advanced_analytics_note?: (string | null);
    advanced_metrics?: Record<string, number>;
    benchmark_position: RiskBenchmarkPosition;
    benchmark_stats: RiskBenchmarkStats;
    confidence: RiskConfidence;
    conflict_count?: number;
    dimension_id: string;
    evidence_count?: number;
    gap_severity: RiskGapSeverity;
    posture_explainer: string;
    posture_score: number;
    project_status: RiskProjectStatus;
};

