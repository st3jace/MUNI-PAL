/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ReviewStatus } from './ReviewStatus';
/**
 * Schema for submitting a fact review.
 */
export type FactReviewRequest = {
    /**
     * approve, reject, or needs_revision
     */
    action: ReviewStatus;
    /**
     * Corrected value if approving with changes
     */
    corrected_value?: null;
    /**
     * Review note or rejection reason
     */
    note?: (string | null);
};

