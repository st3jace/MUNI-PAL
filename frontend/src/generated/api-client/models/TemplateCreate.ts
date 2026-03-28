/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for creating a document template.
 */
export type TemplateCreate = {
    document_type_id: string;
    jurisdiction?: (string | null);
    name: string;
    template_body: string;
    variable_schema?: (Record<string, any> | null);
};

