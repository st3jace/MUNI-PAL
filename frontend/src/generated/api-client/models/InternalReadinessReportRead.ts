/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AssumptionRegisterSection } from './AssumptionRegisterSection';
import type { ChecklistStatusSection } from './ChecklistStatusSection';
import type { EvidenceIndexSection } from './EvidenceIndexSection';
import type { ExecutiveSummary } from './ExecutiveSummary';
import type { GapAnalysisSection } from './GapAnalysisSection';
import type { InformationRequestsSection } from './InformationRequestsSection';
import type { ReadinessDashboard } from './ReadinessDashboard';
/**
 * Schema for reading an internal readiness report.
 */
export type InternalReadinessReportRead = {
    assumption_register?: (AssumptionRegisterSection | Record<string, any>);
    bfms_version?: (string | null);
    checklist_status?: (ChecklistStatusSection | Record<string, any>);
    created_at: string;
    critical_gap_count?: number;
    dimension_scores?: Array<Record<string, any>>;
    evidence_index?: (EvidenceIndexSection | Record<string, any>);
    executive_summary?: (ExecutiveSummary | Record<string, any>);
    facts_count?: number;
    gap_analysis?: (GapAnalysisSection | Record<string, any>);
    generation_completed_at?: (string | null);
    generation_started_at?: (string | null);
    high_gap_count?: number;
    id: string;
    information_requests_section?: (InformationRequestsSection | Record<string, any>);
    is_complete?: boolean;
    md_storage_path?: (string | null);
    open_request_count?: number;
    overall_score?: (number | null);
    overdue_request_count?: number;
    pdf_storage_path?: (string | null);
    playbook_version?: (string | null);
    project_id: string;
    readiness_dashboard?: (ReadinessDashboard | Record<string, any>);
    updated_at: string;
    version?: number;
};

