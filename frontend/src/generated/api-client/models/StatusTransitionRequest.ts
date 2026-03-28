/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DocumentStatus } from './DocumentStatus';
/**
 * Schema for transitioning document workflow status.
 */
export type StatusTransitionRequest = {
    comment?: (string | null);
    new_status: DocumentStatus;
};

