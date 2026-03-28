/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Template rendering result with structured output and diagnostics.
 */
export type TemplateRenderResult = {
    content_json?: (Record<string, any> | null);
    missing_variables?: Array<string>;
    rendered_text: string;
    template_id: string;
    used_variables?: Array<string>;
    warnings?: Array<string>;
};

