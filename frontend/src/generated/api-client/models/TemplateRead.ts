/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DealDocumentTypeRead } from './DealDocumentTypeRead';
/**
 * Full template read schema.
 */
export type TemplateRead = {
    created_at: string;
    document_type?: (DealDocumentTypeRead | null);
    document_type_id: string;
    id: string;
    is_active: boolean;
    is_system: boolean;
    jurisdiction: (string | null);
    name: string;
    template_body: string;
    tenant_id: string;
    updated_at: string;
    variable_schema: (Record<string, any> | null);
    version: number;
};

