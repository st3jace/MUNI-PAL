/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Request to generate a disclosure document.
 */
export type GenerateDisclosureRequest = {
    /**
     * Regenerate even if document exists
     */
    force_regenerate?: boolean;
    project_id: string;
    /**
     * Specific sections to generate (None = all)
     */
    sections?: (Array<string> | null);
};

