/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CoverPage } from './CoverPage';
import type { DealOverviewMemo } from './DealOverviewMemo';
import type { ExternalExecutiveSummary } from './ExternalExecutiveSummary';
import type { FinancialTables } from './FinancialTables';
import type { KeyAssumption } from './KeyAssumption';
import type { SLBKPIBrief } from './SLBKPIBrief';
/**
 * Schema for reading an external advisory package.
 */
export type ExternalAdvisoryPackageRead = {
    bfms_version?: (string | null);
    cover_page?: (CoverPage | Record<string, any>);
    created_at: string;
    critical_tbd_count?: number;
    deal_overview?: (DealOverviewMemo | Record<string, any>);
    disclaimer?: string;
    disclosure_completeness_score?: (number | null);
    disclosure_document_id?: (string | null);
    distribution_issues?: Array<string>;
    docx_storage_path?: (string | null);
    executive_summary?: (ExternalExecutiveSummary | Record<string, any>);
    financial_tables?: (FinancialTables | Record<string, any>);
    generated_for: string;
    generation_completed_at?: (string | null);
    generation_started_at?: (string | null);
    high_tbd_count?: number;
    id: string;
    is_complete?: boolean;
    key_assumptions?: Array<(KeyAssumption | Record<string, any>)>;
    md_storage_path?: (string | null);
    pdf_storage_path?: (string | null);
    playbook_version?: (string | null);
    project_id: string;
    readiness_score_at_generation?: (number | null);
    ready_for_distribution?: boolean;
    slb_brief?: (SLBKPIBrief | Record<string, any>);
    title: string;
    updated_at: string;
    version?: number;
};

