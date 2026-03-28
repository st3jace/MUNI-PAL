/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ConsistencySeverity } from './ConsistencySeverity';
/**
 * A single mismatch or warning from a consistency check.
 */
export type ConsistencyIssue = {
    delta?: (number | null);
    field: string;
    legal_value?: (string | number | boolean | null);
    message: string;
    model_value?: (string | number | boolean | null);
    severity: ConsistencySeverity;
};

