/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChecklistPhase } from './ChecklistPhase';
import type { ChecklistStatus } from './ChecklistStatus';
/**
 * Computed status for a checklist item in a specific project.
 *
 * Per spec: Status is deterministic (rules-based, not learned).
 */
export type ChecklistItemStatus = {
    coverage_percentage: number;
    covered_paths_count: number;
    item_code: string;
    linked_fact_ids?: Array<string>;
    /**
     * Paths with facts below confidence threshold
     */
    low_confidence_paths?: Array<string>;
    /**
     * Required paths without approved facts
     */
    missing_paths?: Array<string>;
    phase: ChecklistPhase;
    required_paths_count: number;
    status: ChecklistStatus;
    /**
     * Human-readable explanation of why this status
     */
    status_reason: string;
    title: string;
};

