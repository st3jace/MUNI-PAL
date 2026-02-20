/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChecklistPhase } from './ChecklistPhase';
/**
 * Summary of checklist completion for a phase.
 */
export type ChecklistPhaseSummary = {
    blocked_count: number;
    /**
     * True if all blocking items are ready
     */
    can_proceed_to_next: boolean;
    completion_percentage: number;
    in_progress_count: number;
    not_started_count: number;
    phase: ChecklistPhase;
    phase_name: string;
    ready_count: number;
    total_items: number;
};

