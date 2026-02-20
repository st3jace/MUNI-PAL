/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Override decision input for governed risk score/guardrail adjustments.
 */
export type RiskOverrideDecisionRequest = {
    notes?: (string | null);
    override_value: string;
    previous_value?: (string | null);
    project_id: string;
    reason: string;
    target_ref: string;
};

