/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskAdvisoryStatement } from './RiskAdvisoryStatement';
/**
 * Ready-to-consume risk block for advisory package generation.
 */
export type RiskAdvisoryInput = {
    action_briefs?: Array<string>;
    material_risk_statements?: Array<RiskAdvisoryStatement>;
    mitigant_highlights?: Array<string>;
};

