/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Definition of an AI extractor from playbook.
 *
 * Per playbook: 8 concrete extractors with prompt templates.
 */
export type ExtractorDefinition = {
    description: string;
    /**
     * User prompt template with {content} placeholder
     */
    extraction_prompt_template: string;
    /**
     * Unique extractor identifier
     */
    extractor_id: string;
    /**
     * If True, re-running produces identical results
     */
    idempotent?: boolean;
    name: string;
    /**
     * If True, needs full artifact; if False, works per-chunk
     */
    requires_full_document?: boolean;
    /**
     * System prompt for the LLM
     */
    system_prompt: string;
    /**
     * Schema paths this extractor targets
     */
    target_schema_paths: Array<string>;
};

