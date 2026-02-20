/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskActionItem } from './RiskActionItem';
/**
 * Ready-to-consume risk block for readiness services.
 */
export type RiskReadinessInput = {
    critical_risk_flags?: Array<string>;
    directional_guidance_only?: boolean;
    recommended_actions?: Array<RiskActionItem>;
};

