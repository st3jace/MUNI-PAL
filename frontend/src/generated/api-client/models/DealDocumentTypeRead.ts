/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DealVertical } from './DealVertical';
import type { DocumentCategory } from './DocumentCategory';
import type { RetentionPolicy } from './RetentionPolicy';
/**
 * Read schema for document type registry entries.
 */
export type DealDocumentTypeRead = {
    category: DocumentCategory;
    code: string;
    created_at: string;
    deal_vertical: DealVertical;
    default_workflow: string;
    description?: (string | null);
    display_name: string;
    id: string;
    is_active: boolean;
    requires_signature: boolean;
    retention_policy: RetentionPolicy;
    sort_order: number;
    updated_at: string;
};

