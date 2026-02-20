/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CriticalityTier } from './CriticalityTier';
import type { FactDuplicateClassification } from './FactDuplicateClassification';
import type { FactLifecycleState } from './FactLifecycleState';
import type { ReviewStatus } from './ReviewStatus';
import type { SourceType } from './SourceType';
/**
 * Minimal fact summary for listings.
 */
export type ExtractedFactSummary = {
    confidence_score: number;
    criticality: CriticalityTier;
    duplicate_classification?: FactDuplicateClassification;
    id: string;
    is_canonical?: boolean;
    lifecycle_state?: FactLifecycleState;
    review_status: ReviewStatus;
    schema_path: string;
    source_type?: SourceType;
    value: any;
};

