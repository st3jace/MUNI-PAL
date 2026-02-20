/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskReliabilityBand } from './RiskReliabilityBand';
/**
 * Confidence and reliability metadata for one risk dimension.
 */
export type RiskConfidence = {
    reliability_band: RiskReliabilityBand;
    score: number;
    uncertainty_note?: (string | null);
};

