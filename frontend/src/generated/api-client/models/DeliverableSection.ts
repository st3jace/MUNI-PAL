/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * A section of the deliverable pack.
 *
 * Per playbook Section 8, the pack has 9 sections:
 * 1. Cover
 * 2. Deal Overview Memo
 * 3. Readiness & Gap Report
 * 4. Checklist Status
 * 5. Evidence Index
 * 6. Assumption Register
 * 7. Financial Model Outputs
 * 8. SLB KPI Brief
 * 9. Disclosure Outline
 */
export type DeliverableSection = {
    /**
     * Markdown content for this section
     */
    content: string;
    is_complete?: boolean;
    section_name: string;
    section_number: number;
    /**
     * Any warnings about this section (e.g., missing data)
     */
    warnings?: Array<string>;
};

