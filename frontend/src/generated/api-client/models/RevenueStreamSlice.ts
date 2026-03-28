/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RevenueStabilityClass } from './RevenueStabilityClass';
/**
 * One revenue stream within a scenario mix.
 */
export type RevenueStreamSlice = {
    amount: number;
    color: string;
    is_inferred?: boolean;
    label: string;
    pct_of_total: number;
    source_path?: (string | null);
    stability_class: RevenueStabilityClass;
    stream_id: string;
};

