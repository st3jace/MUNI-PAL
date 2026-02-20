/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChecklistPhase } from './ChecklistPhase';
import type { CriticalityTier } from './CriticalityTier';
/**
 * Definition of a checklist item from playbook.
 *
 * This is the template; actual status is computed per-project.
 */
export type ChecklistItemDefinition = {
    blocked_explanation?: (string | null);
    /**
     * If True, phase cannot complete until this item is ready
     */
    blocks_phase_completion?: boolean;
    criticality?: CriticalityTier;
    description: string;
    in_progress_explanation?: (string | null);
    /**
     * Unique code (e.g., 'P1.1', 'P2.3')
     */
    item_code: string;
    /**
     * Schema paths that contribute but aren't required
     */
    optional_schema_paths?: Array<string>;
    phase: ChecklistPhase;
    ready_explanation?: (string | null);
    /**
     * Schema paths that must have approved facts for this item to be 'ready'
     */
    required_schema_paths: Array<string>;
    title: string;
};

