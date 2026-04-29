/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Parameters for the credit spread monitor.
 */
export type CreditSpreadRequest = {
    /**
     * Whether borrower is out-of-state (affects IDA fees)
     */
    out_of_state?: boolean;
    /**
     * Representative par amount for fee calculations
     */
    par_amount?: number;
    /**
     * Sector (waste, healthcare, etc.)
     */
    sector: string;
};

