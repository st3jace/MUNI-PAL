/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RevenueScenarioSafety } from './RevenueScenarioSafety';
import type { RevenueStreamSlice } from './RevenueStreamSlice';
/**
 * Scenario payload for the diversification comparison chart.
 */
export type RevenueScenarioMix = {
    assumptions?: Array<string>;
    breach_weeks: number;
    breakeven_diesel_price: number;
    covenant_trigger_diesel_price: number;
    dscr_mean: number;
    dscr_minimum: number;
    dscr_parity_diesel_price?: (number | null);
    implied_rating: string;
    label: string;
    revenue_streams?: Array<RevenueStreamSlice>;
    safety_label: string;
    safety_status: RevenueScenarioSafety;
    scenario_id: string;
    total_revenue: number;
};

