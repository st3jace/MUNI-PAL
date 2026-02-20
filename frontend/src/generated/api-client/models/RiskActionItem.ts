/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RiskActionPriority } from './RiskActionPriority';
/**
 * Action synthesized from risk gaps and/or guardrail outcomes.
 */
export type RiskActionItem = {
    action_id: string;
    evidence_required?: Array<string>;
    expected_impact: string;
    owner: string;
    priority: RiskActionPriority;
    rationale: string;
    source_refs?: Array<string>;
    target_date_hint: string;
    title: string;
};

