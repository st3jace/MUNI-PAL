/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskBenchmarkPosition } from './RiskBenchmarkPosition';
/**
 * Overall project posture versus benchmark corpus.
 */
export type RiskOverallPosture = {
    benchmark_position: RiskBenchmarkPosition;
    explanation: string;
    posture_score: number;
};

