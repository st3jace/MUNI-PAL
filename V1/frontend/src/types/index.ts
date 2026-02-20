/**
 * TypeScript types for Muni-Pal BFMS frontend.
 * Mirrors backend Pydantic schemas.
 */

// -----------------------------------------------------------------------------
// Common Types
// -----------------------------------------------------------------------------

export type UUID = string;

export enum ReviewStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  NEEDS_REVISION = 'needs_revision',
}

export enum ChecklistStatus {
  NOT_STARTED = 'not_started',
  IN_PROGRESS = 'in_progress',
  BLOCKED = 'blocked',
  READY = 'ready',
}

export enum ChecklistPhase {
  P1 = 'P1',
  P2 = 'P2',
  P3 = 'P3',
  P4 = 'P4',
  P5 = 'P5',
  P6 = 'P6',
}

export enum CriticalityTier {
  CRITICAL = 'critical',
  MATERIAL = 'material',
  SECONDARY = 'secondary',
}

export enum SourceType {
  EXTRACTED = 'extracted',
  MANUAL = 'manual',
}

export enum ReadinessDimension {
  ISSUER_AUTHORITY = 'issuer_authority',
  PROJECT_TECH = 'project_tech',
  REVENUE_FEEDSTOCK = 'revenue_feedstock',
  CAB_FINANCIAL = 'cab_financial',
  RISK_SECURITY_SLB = 'risk_security_slb',
  SLB_VERIFICATION = 'slb_verification',
}

// -----------------------------------------------------------------------------
// Project Types
// -----------------------------------------------------------------------------

export interface Project {
  id: UUID;
  name: string;
  description?: string;
  issuer_name: string;
  project_location?: string;
  target_bond_amount?: number;
  playbook_id: UUID;
  owner_id: UUID;
  artifact_count: number;
  fact_count: number;
  approved_fact_count: number;
  overall_readiness_score?: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectSummary {
  id: UUID;
  name: string;
  issuer_name: string;
  artifact_count: number;
  overall_readiness_score?: number;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  issuer_name: string;
  project_location?: string;
  target_bond_amount?: number;
  playbook_id?: UUID;
}

// -----------------------------------------------------------------------------
// Fact Types
// -----------------------------------------------------------------------------

export interface ExtractedFact {
  id: UUID;
  schema_path: string;
  criticality: CriticalityTier;
  source_type: SourceType;
  value: unknown;
  value_type: string;
  unit?: string;
  confidence_score: number;
  confidence_rationale?: string;
  project_id: UUID;
  extraction_job_id?: UUID; // Optional for manual facts
  review_status: ReviewStatus;
  reviewed_by?: UUID;
  reviewed_at?: string;
  review_note?: string;
  original_value?: unknown;
  created_at: string;
  updated_at: string;
}

export interface FactReviewRequest {
  action: ReviewStatus;
  corrected_value?: unknown;
  note?: string;
}

export interface ManualFactCreate {
  project_id: UUID;
  schema_path: string;
  value: unknown;
  value_type?: string;
  unit?: string;
  note?: string;
}

export interface MissingPathInfo {
  schema_path: string;
  display_name: string;
  criticality: CriticalityTier;
  value_type: string;
  phase: string;
  item_code: string;
  item_title: string;
}

// -----------------------------------------------------------------------------
// Playbook Types
// -----------------------------------------------------------------------------

export interface Playbook {
  id: UUID;
  name: string;
  version: string;
  description?: string;
  bond_archetype: string;
  is_default: boolean;
  is_active: boolean;
  schema_paths: Record<string, SchemaPathConfig>;
  checklist_items: ChecklistItemDefinition[];
}

export interface SchemaPathConfig {
  criticality: CriticalityTier;
  description: string;
  dimension?: ReadinessDimension;
}

export interface ChecklistItemDefinition {
  code: string;
  phase: ChecklistPhase;
  name: string;
  description?: string;
  required_paths: string[];
  optional_paths?: string[];
  is_blocking?: boolean;
}

// -----------------------------------------------------------------------------
// Checklist Types
// -----------------------------------------------------------------------------

export interface ChecklistItemStatus {
  item_code: string;
  phase: ChecklistPhase;
  title: string;
  status: ChecklistStatus;
  status_reason: string;
  required_paths_count: number;
  covered_paths_count: number;
  coverage_percentage: number;
  linked_fact_ids: UUID[];
  missing_paths: string[];
  low_confidence_paths: string[];
}

export interface ChecklistPhaseSummary {
  phase: ChecklistPhase;
  phase_name: string;
  total_items: number;
  ready_count: number;
  in_progress_count: number;
  blocked_count: number;
  not_started_count: number;
  completion_percentage: number;
  can_proceed_to_next: boolean;
}

// -----------------------------------------------------------------------------
// Readiness Types
// -----------------------------------------------------------------------------

export interface DimensionScore {
  dimension: ReadinessDimension;
  dimension_name: string;
  score: number;
  max_score: number;
  weight: number;
  weighted_contribution: number;
  critical_paths_covered: number;
  critical_paths_total: number;
  explanation: string;
  improvement_suggestions: string[];
}

export interface ReadinessAssessment {
  project_id: UUID;
  dimensions: Record<ReadinessDimension, DimensionScore>;
  overall_score: number;
  recommendation: string;
  recommendation_rationale: string;
  total_facts_approved: number;
  total_facts_pending: number;
  critical_gaps_count: number;
  material_gaps_count: number;
}

export interface ReadinessGap {
  schema_path: string;
  dimension: ReadinessDimension;
  criticality: CriticalityTier;
  description: string;
  impact: string;
  suggested_evidence: string;
}

// -----------------------------------------------------------------------------
// API Response Types
// -----------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
}

export interface ProjectListResponse {
  projects: ProjectSummary[];
  total: number;
}

export interface FactListResponse {
  facts: ExtractedFact[];
  total: number;
}

// -----------------------------------------------------------------------------
// Deliverable Pack Types
// -----------------------------------------------------------------------------

export interface DeliverableSection {
  section_number: number;
  section_name: string;
  content: string;
  is_complete: boolean;
  warnings: string[];
}

export interface DeliverablePackCreate {
  project_id: UUID;
  title: string;
  generated_for: string;
  include_sections?: number[];
  include_appendices?: boolean;
}

export interface DeliverablePack {
  id: UUID;
  project_id: UUID;
  title: string;
  generated_for: string;
  is_complete: boolean;
  generation_started_at?: string;
  generation_completed_at?: string;
  sections: DeliverableSection[];
  facts_included_count: number;
  readiness_score_at_generation?: number;
  warnings: string[];
  disclaimer: string;
  created_at: string;
  updated_at: string;
}

export interface DeliverablePackSummary {
  id: UUID;
  title: string;
  generated_for: string;
  is_complete: boolean;
  created_at: string;
  readiness_score_at_generation?: number;
}
