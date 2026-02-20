/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Criticality tiers for schema paths.
 *
 * Per playbook:
 * - CRITICAL: Requires 0.90+ confidence, blocks progression if missing
 * - MATERIAL: Significant impact on readiness scoring
 * - SECONDARY: Nice to have, lower confidence thresholds acceptable
 */
export enum CriticalityTier {
    CRITICAL = 'critical',
    MATERIAL = 'material',
    SECONDARY = 'secondary',
}
