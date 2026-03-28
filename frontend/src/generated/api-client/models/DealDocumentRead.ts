/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { DealDocumentTypeRead } from './DealDocumentTypeRead';
import type { DocumentStatus } from './DocumentStatus';
import type { RetentionPolicy } from './RetentionPolicy';
import type { UserSummary } from './UserSummary';
/**
 * Full deal document read schema.
 */
export type DealDocumentRead = {
    artifact_id: (string | null);
    assigned_to?: (UserSummary | null);
    content_html?: (string | null);
    content_json: (Record<string, any> | null);
    created_at: string;
    created_by?: (UserSummary | null);
    current_version?: number;
    document_number: (string | null);
    document_type: DealDocumentTypeRead;
    filed_at: (string | null);
    filed_to: (string | null);
    filing_reference: (string | null);
    id: string;
    legal_hold: boolean;
    project_id: string;
    retention_expires_at: (string | null);
    retention_policy: RetentionPolicy;
    signature_request_id?: (string | null);
    signature_status: (string | null);
    status: DocumentStatus;
    template_id: (string | null);
    template_version: (number | null);
    title: string;
    updated_at: string;
    version_count?: number;
};

