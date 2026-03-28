/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { SnapshotReason } from './SnapshotReason';
/**
 * Version snapshot read schema.
 */
export type DealDocumentVersionRead = {
    change_summary: (string | null);
    content_hash: string;
    created_at: string;
    created_by_id: string;
    document_id: string;
    id: string;
    snapshot_reason: SnapshotReason;
    storage_path: (string | null);
    updated_at: string;
    version_number: number;
};

