/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReadinessDimension } from './ReadinessDimension';
/**
 * Score for a single readiness dimension.
 */
export type DimensionScore = {
    critical_paths_covered?: number;
    critical_paths_total?: number;
    dimension: ReadinessDimension;
    dimension_name: string;
    /**
     * Why-it-matters narrative from playbook
     */
    explanation: string;
    /**
     * Specific actions to improve this dimension
     */
    improvement_suggestions?: Array<string>;
    material_paths_covered?: number;
    material_paths_total?: number;
    max_score?: number;
    /**
     * Score on 0-5 scale
     */
    score: number;
    weight: number;
    /**
     * This dimension's contribution to overall score
     */
    weighted_contribution: number;
};

