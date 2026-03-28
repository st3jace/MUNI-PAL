/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DocumentCategory } from './DocumentCategory';
import type { DocumentStatus } from './DocumentStatus';
/**
 * Auto-generated closing checklist item.
 */
export type ChecklistItemRead = {
    category: DocumentCategory;
    document_id?: (string | null);
    document_status?: (DocumentStatus | null);
    document_type_code: string;
    document_type_name: string;
    is_complete?: boolean;
    requires_signature: boolean;
};

