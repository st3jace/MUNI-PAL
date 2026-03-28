/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Schema for creating a new deal document.
 */
export type DealDocumentCreate = {
    assigned_to_id?: (string | null);
    content_json?: (Record<string, any> | null);
    document_type_id: string;
    project_id: string;
    template_id?: (string | null);
    template_variables?: (Record<string, any> | null);
    title: string;
};

