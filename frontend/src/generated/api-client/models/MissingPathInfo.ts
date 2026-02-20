/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CriticalityTier } from './CriticalityTier';
/**
 * Information about a schema path that doesn't have an approved fact yet.
 *
 * Used for displaying outstanding items that need manual entry.
 */
export type MissingPathInfo = {
    /**
     * Importance tier
     */
    criticality: CriticalityTier;
    /**
     * Human-readable name for the path
     */
    display_name: string;
    /**
     * Which checklist item needs this
     */
    item_code: string;
    /**
     * Title of the checklist item
     */
    item_title: string;
    /**
     * Which checklist phase needs this
     */
    phase: string;
    /**
     * The canonical schema path
     */
    schema_path: string;
    /**
     * Expected value type
     */
    value_type?: string;
};

