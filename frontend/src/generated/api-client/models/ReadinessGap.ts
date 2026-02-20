/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReadinessDimension } from './ReadinessDimension';
/**
 * A specific gap in readiness evidence.
 */
export type ReadinessGap = {
    criticality: string;
    description: string;
    dimension: ReadinessDimension;
    /**
     * How this gap affects the assessment
     */
    impact: string;
    schema_path: string;
    /**
     * Brief one-sentence explanation of what this data point is
     */
    short_description?: string;
    /**
     * What type of document or data would fill this gap
     */
    suggested_evidence: string;
};

