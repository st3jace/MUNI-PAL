/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Preview of a disclosure section before full generation.
 */
export type DisclosureSectionPreview = {
    /**
     * Schema paths that have approved facts
     */
    available_facts: Array<string>;
    /**
     * Whether there's enough evidence to generate this section
     */
    can_generate: boolean;
    /**
     * Estimated section confidence
     */
    estimated_confidence?: number;
    /**
     * Schema paths without approved facts
     */
    missing_facts: Array<string>;
    /**
     * Schema paths required for this section
     */
    required_facts: Array<string>;
    section_id: string;
    title: string;
};

