/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DimensionScore } from './DimensionScore';
/**
 * Complete readiness assessment for a project.
 *
 * Per spec scoring ranges:
 * - 0.0-3.0: Not Yet Viable
 * - 3.0-5.5: Structurally Viable
 * - 5.6-7.5: Ready for Selective Engagement
 * - 7.6-10.0: Ready for Advisor-Led Market Review
 */
export type ReadinessAssessment = {
    critical_gaps_count?: number;
    dimensions: Record<string, DimensionScore>;
    material_gaps_count?: number;
    /**
     * Weighted average on 0-10 scale
     */
    overall_score: number;
    project_id: string;
    /**
     * One of: Not Yet Viable, Structurally Viable, Ready for Selective Engagement, Ready for Advisor-Led Market Review
     */
    recommendation: string;
    /**
     * Explanation of the recommendation
     */
    recommendation_rationale: string;
    total_facts_approved?: number;
    total_facts_pending?: number;
};

