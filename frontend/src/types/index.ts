/**
 * TypeScript types for Muni-Pal BFMS frontend.
 * Mirrors backend Pydantic schemas.
 */

import type {
  components as OpenApiComponents,
  paths as OpenApiPaths,
} from './openapi.generated';

export type { OpenApiComponents, OpenApiPaths };

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
  sector?: string;
  subsector?: string;
  archetype_id?: string;
  archetype_version?: string;
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
  sector?: string;
  subsector?: string;
  archetype_id?: string;
  archetype_version?: string;
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
  sector?: string;
  subsector?: string;
  archetype_id?: string;
  archetype_version?: string;
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
// Schema Path Metadata Types
// -----------------------------------------------------------------------------

export interface SchemaPathMetadata {
  path: string;
  display_name: string;
  value_type: string;
  criticality: CriticalityTier;
  min_confidence: number;
  unit?: string;
  allowed_values?: string[];
  // Rich metadata for guidance
  description: string;
  short_description: string;
  guidance: string;
  example: string | number | boolean | string[] | Record<string, unknown>;
  who_needs_it: string[];
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
  short_description: string;
  impact: string;
  suggested_evidence: string;
}

// -----------------------------------------------------------------------------
// Phase 7 - BFMS Risk Integration Types
// -----------------------------------------------------------------------------

export interface RiskBfmsCohortParams {
  sector: string;
  issuer_size_band: string;
  deal_type: string;
  recency_window: string;
  sample_size: number;
}

export type RiskIntegrationMode = OpenApiComponents['schemas']['RiskIntegrationMode'];
export type RiskBfmsIntegrationResponse =
  OpenApiComponents['schemas']['RiskBfmsIntegrationResponse'];

// -----------------------------------------------------------------------------
// Revenue Visualization Types
// -----------------------------------------------------------------------------

export type RevenueStabilityClass = 'stable' | 'balanced' | 'volatile';
export type RevenueScenarioSafety = 'fragile' | 'safe' | 'fortress';

export interface RevenueStreamDefinition {
  stream_id: string;
  label: string;
  color: string;
  stability_class: RevenueStabilityClass;
  description: string;
}

export interface RevenueStreamSlice {
  stream_id: string;
  label: string;
  amount: number;
  pct_of_total: number;
  color: string;
  stability_class: RevenueStabilityClass;
  is_inferred: boolean;
  source_path?: string | null;
}

export interface RevenueScenarioMix {
  scenario_id: string;
  label: string;
  total_revenue: number;
  revenue_streams: RevenueStreamSlice[];
  dscr_mean: number;
  dscr_minimum: number;
  breach_weeks: number;
  implied_rating: string;
  breakeven_diesel_price: number;
  dscr_parity_diesel_price?: number | null;
  covenant_trigger_diesel_price: number;
  safety_status: RevenueScenarioSafety;
  safety_label: string;
  assumptions: string[];
}

export interface RevenueRiskProofMetric {
  metric_id: string;
  label: string;
  baseline_value: string;
  diversified_value: string;
  delta_label: string;
}

export interface RevenueDiversificationRiskProof {
  title: string;
  baseline_label: string;
  diversified_label: string;
  takeaway: string;
  metrics: RevenueRiskProofMetric[];
}

export interface RevenueDiversificationVisualizationResponse {
  contract_version: string;
  generated_at: string;
  project_id: UUID;
  project_name: string;
  debt_service_annual: number;
  covenant_trigger_dscr: number;
  non_diesel_combined_coverage_dscr?: number | null;
  non_diesel_senior_coverage_dscr?: number | null;
  stream_definitions: RevenueStreamDefinition[];
  revenue_scenarios: RevenueScenarioMix[];
  risk_proof?: RevenueDiversificationRiskProof | null;
  data_quality_notes: string[];
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
  generation_completed_at?: string;
  readiness_score_at_generation?: number;
}

// -----------------------------------------------------------------------------
// v2 - WP7 Disclosure Synthesis Types
// -----------------------------------------------------------------------------

export enum TBDSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export interface TBDMarker {
  id: UUID;
  location: string;
  missing_fact_paths: string[];
  reason: string;
  severity: TBDSeverity;
  is_resolved: boolean;
  resolved_at?: string;
  section_id?: UUID;
}

export interface DisclosureSection {
  id: UUID;
  section_id: string;
  section_order: number;
  title: string;
  content_md: string;
  confidence: number;
  required_fact_count: number;
  present_fact_count: number;
  tbd_count: number;
  supporting_fact_ids: UUID[];
  is_rendered: boolean;
  subsections?: DisclosureSection[];
  tbd_markers?: TBDMarker[];
}

export interface DisclosureDocument {
  id: UUID;
  project_id: UUID;
  version: number;
  completeness_score: number;
  is_complete: boolean;
  generation_started_at?: string;
  generation_completed_at?: string;
  playbook_version?: string;
  sections: DisclosureSection[];
  tbd_items: TBDMarker[];
  created_at: string;
  updated_at: string;
}

export interface DisclosureDocumentSummary {
  id: UUID;
  project_id: UUID;
  version: number;
  completeness_score: number;
  is_complete: boolean;
  section_count: number;
  tbd_count: number;
  created_at: string;
}

export interface GenerateDisclosureRequest {
  project_id: UUID;
  section_ids?: string[];
  force_regenerate?: boolean;
}

// -----------------------------------------------------------------------------
// v2 - WP8 Information Request Types
// -----------------------------------------------------------------------------

export enum EvidenceState {
  NONE = 'none',
  PARTIAL = 'partial',
  CONFLICTING = 'conflicting',
  WEAK = 'weak',
}

export enum RequestPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export enum RequestStatus {
  OPEN = 'open',
  IN_PROGRESS = 'in_progress',
  SUBMITTED = 'submitted',
  RESOLVED = 'resolved',
  DEFERRED = 'deferred',
}

export interface BondDomainContext {
  why_it_matters: string;
  who_needs_it: string[];
  when_needed?: string;
  consequences: string;
  related_requirements: string[];
  regulatory_reference?: string;
}

export interface RequestGuidance {
  overview: string;
  specific_questions: string[];
  data_points_needed: string[];
  suggested_approach?: string;
  common_pitfalls: string[];
  time_estimate?: string;
}

export interface EvidenceExample {
  document_type: string;
  content_preview: string;
  quality_notes: string;
}

export interface InformationRequest {
  id: UUID;
  request_code: string;
  title: string;
  project_id: UUID;
  // What's missing
  missing_fact_paths: string[];
  current_evidence_state: EvidenceState;
  gap_id?: string;
  // Bond domain context
  why_it_matters: string;
  who_needs_it: string[];
  when_needed?: string;
  consequences: string;
  related_requirements: string[];
  regulatory_reference?: string;
  // Affected items
  affected_checklist_items: string[];
  affected_dimensions: string[];
  // Guidance
  guidance_overview: string;
  specific_questions: string[];
  data_points_needed: string[];
  suggested_approach?: string;
  common_pitfalls: string[];
  time_estimate?: string;
  examples: EvidenceExample[];
  acceptable_sources: string[];
  // Quality requirements
  minimum_confidence: number;
  expected_format?: string;
  // Assignment
  priority: RequestPriority;
  suggested_owner?: string;
  target_date?: string;
  // Lifecycle
  status: RequestStatus;
  acknowledged_at?: string;
  submitted_at?: string;
  resolved_at?: string;
  deferred_at?: string;
  deferred_reason?: string;
  // Resolution
  resolution_notes?: string;
  resolved_by_fact_ids: UUID[];
  linked_artifact_id?: UUID;
  // Escalation
  escalation_level: number;
  last_escalated_at?: string;
  created_at: string;
  updated_at: string;
}

export interface InformationRequestSummary {
  id: UUID;
  request_code: string;
  title: string;
  priority: RequestPriority;
  status: RequestStatus;
  suggested_owner?: string;
  target_date?: string;
  is_overdue: boolean;
  days_overdue?: number;
  created_at: string;
}

export interface InformationRequestNote {
  id: UUID;
  request_id: UUID;
  content: string;
  note_type: string;
  created_by_id: UUID;
  created_at: string;
}

export interface InformationRequestReport {
  project_id: UUID;
  total_requests: number;
  by_status: Record<RequestStatus, number>;
  by_priority: Record<RequestPriority, number>;
  overdue_count: number;
  requests: InformationRequestSummary[];
}

// -----------------------------------------------------------------------------
// v2 - Bifurcated Deliverable Types (Internal/External)
// -----------------------------------------------------------------------------

// Internal Readiness Report Types
export interface ExecutiveSummary {
  overall_score: number;
  score_interpretation: string;
  score_trajectory?: { date: string; score: number }[];
  key_achievements: { description: string; date: string }[];
  critical_blockers: { title: string; summary: string; consequences: string; suggested_owner?: string }[];
}

export interface DimensionDetail {
  name: string;
  score: number;
  weight: number;
  status_emoji: string;
  what_measured: string;
  current_state_explanation: string;
  why_it_matters: string;
  supporting_facts: { schema_path: string; value: string; confidence: number }[];
  related_gaps: { title: string; severity: string }[];
  recommended_action?: string;
}

export interface ReadinessDashboardSection {
  overall_score: number;
  dimensions: DimensionDetail[];
  score_interpretation_guide: { score_range: string; meaning: string; recommended_action: string }[];
}

export interface GapDetail {
  title: string;
  severity: string;
  missing_fact_paths: string[];
  current_evidence_state: string;
  why_it_matters: string;
  consequences: string;
  affected_checklist_items: string[];
  affected_dimensions: string[];
  suggested_owner?: string;
  suggested_deadline?: string;
}

export interface GapAnalysisSection {
  summary: { priority: string; count: number; impact: string }[];
  critical_gaps: GapDetail[];
  high_gaps: GapDetail[];
  medium_gaps: GapDetail[];
  low_gaps: GapDetail[];
}

export interface InternalReadinessReport {
  id: UUID;
  project_id: UUID;
  version: number;
  is_complete: boolean;
  generation_started_at?: string;
  generation_completed_at?: string;
  // Content sections
  executive_summary: ExecutiveSummary;
  readiness_dashboard: ReadinessDashboardSection;
  gap_analysis: GapAnalysisSection;
  information_requests_section: Record<string, unknown>;
  checklist_status: Record<string, unknown>;
  evidence_index: Record<string, unknown>;
  assumption_register: Record<string, unknown>;
  // Metrics
  overall_score?: number;
  dimension_scores: { dimension: string; score: number }[];
  critical_gap_count: number;
  high_gap_count: number;
  open_request_count: number;
  overdue_request_count: number;
  facts_count: number;
  // Metadata
  playbook_version?: string;
  bfms_version?: string;
  created_at: string;
  updated_at: string;
}

export interface InternalReportSummary {
  id: UUID;
  project_id: UUID;
  version: number;
  is_complete: boolean;
  overall_score?: number;
  critical_gap_count: number;
  open_request_count: number;
  created_at: string;
}

// External Advisory Package Types
export interface CoverPage {
  project_name: string;
  issuer_name: string;
  prepared_for: string;
  prepared_by: string;
  date: string;
  version: string;
  confidentiality_notice: string;
}

export interface DealOverviewMemo {
  transaction_summary: string;
  key_terms: { term: string; value: string }[];
  use_of_proceeds: string;
  security_structure: string;
  timeline: { milestone: string; date: string }[];
}

export interface FinancialTable {
  table_name: string;
  headers: string[];
  rows: (string | number)[][];
  footnotes?: string[];
}

export interface SLBBrief {
  kpi_summary: { kpi_name: string; baseline: string; target: string; verification_method: string }[];
  sustainability_narrative: string;
  third_party_verification: string;
}

export interface ExternalAdvisoryPackage {
  id: UUID;
  project_id: UUID;
  version: number;
  title: string;
  generated_for: string;
  is_complete: boolean;
  generation_started_at?: string;
  generation_completed_at?: string;
  // Content sections
  cover_page: CoverPage;
  executive_summary: Record<string, unknown>;
  deal_overview: DealOverviewMemo;
  financial_tables: Record<string, FinancialTable[]>;
  slb_brief: SLBBrief;
  key_assumptions: { name: string; value: string; source: string; confidence: number }[];
  disclaimer: string;
  // Quality metrics
  disclosure_completeness_score?: number;
  critical_tbd_count: number;
  high_tbd_count: number;
  readiness_score_at_generation?: number;
  ready_for_distribution: boolean;
  distribution_issues: string[];
  // Metadata
  playbook_version?: string;
  bfms_version?: string;
  disclosure_document_id?: UUID;
  created_at: string;
  updated_at: string;
}

export interface ExternalPackageSummary {
  id: UUID;
  project_id: UUID;
  version: number;
  title: string;
  generated_for: string;
  is_complete: boolean;
  ready_for_distribution: boolean;
  readiness_score_at_generation?: number;
  created_at: string;
}

export interface DistributionValidation {
  ready_for_distribution: boolean;
  issues: string[];
  warnings: string[];
  recommendations: string[];
}
