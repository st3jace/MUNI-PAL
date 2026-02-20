/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for requesting pack generation.
 */
export type DeliverablePackCreate = {
    /**
     * Intended recipient (e.g., 'Bond Counsel Review')
     */
    generated_for: string;
    include_appendices?: boolean;
    /**
     * Section numbers to include (1-9)
     */
    include_sections?: Array<number>;
    project_id: string;
    title: string;
};

