/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RevenueRiskProofMetric } from './RevenueRiskProofMetric';
/**
 * Packet-level proof that diversification changes the risk profile.
 */
export type RevenueDiversificationRiskProof = {
    baseline_label: string;
    diversified_label: string;
    metrics?: Array<RevenueRiskProofMetric>;
    takeaway: string;
    title: string;
};

