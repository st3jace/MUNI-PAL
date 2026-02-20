/**
 * API client for Muni-Pal BFMS backend.
 */

import axios, { AxiosInstance } from 'axios';
import type {
  Project,
  ProjectCreate,
  ProjectListResponse,
  ExtractedFact,
  FactListResponse,
  FactReviewRequest,
  ManualFactCreate,
  MissingPathInfo,
  Playbook,
  ChecklistItemStatus,
  ChecklistPhaseSummary,
  ReadinessAssessment,
  ReviewStatus,
  ChecklistPhase,
  CriticalityTier,
  DeliverablePack,
  DeliverablePackCreate,
  DeliverablePackSummary,
  UUID,
} from '../types';

const API_BASE_URL = '/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // ---------------------------------------------------------------------------
  // Projects
  // ---------------------------------------------------------------------------

  async listProjects(params?: {
    skip?: number;
    limit?: number;
  }): Promise<ProjectListResponse> {
    const { data } = await this.client.get('/projects/', { params });
    return data;
  }

  async getProject(projectId: UUID): Promise<Project> {
    const { data } = await this.client.get(`/projects/${projectId}`);
    return data;
  }

  async createProject(project: ProjectCreate): Promise<Project> {
    const { data } = await this.client.post('/projects/', project);
    return data;
  }

  async updateProject(
    projectId: UUID,
    updates: Partial<ProjectCreate>
  ): Promise<Project> {
    const { data } = await this.client.patch(`/projects/${projectId}`, updates);
    return data;
  }

  async deleteProject(projectId: UUID): Promise<void> {
    await this.client.delete(`/projects/${projectId}`);
  }

  // ---------------------------------------------------------------------------
  // Facts
  // ---------------------------------------------------------------------------

  async listFacts(params: {
    project_id: UUID;
    status?: ReviewStatus;
    schema_path_prefix?: string;
    min_confidence?: number;
    limit?: number;
    offset?: number;
  }): Promise<FactListResponse> {
    const { data } = await this.client.get('/facts/', { params });
    return data;
  }

  async getFact(factId: UUID): Promise<ExtractedFact> {
    const { data } = await this.client.get(`/facts/${factId}`);
    return data;
  }

  async reviewFact(
    factId: UUID,
    review: FactReviewRequest,
    reviewerId: UUID = '00000000-0000-0000-0000-000000000001' // Dev user
  ): Promise<ExtractedFact> {
    const { data } = await this.client.post(
      `/facts/${factId}/review`,
      review,
      { params: { reviewer_id: reviewerId } }
    );
    return data;
  }

  async getFactStatusCounts(
    projectId: UUID
  ): Promise<Record<ReviewStatus, number>> {
    const { data } = await this.client.get('/facts/status-counts', {
      params: { project_id: projectId },
    });
    return data;
  }

  async getFactConflicts(projectId: UUID): Promise<{
    conflicts: Array<{
      schema_path: string;
      fact_count: number;
      facts: ExtractedFact[];
    }>;
  }> {
    const { data } = await this.client.get('/facts/conflicts/', {
      params: { project_id: projectId },
    });
    return data;
  }

  async getMissingPaths(
    projectId: UUID,
    phase?: ChecklistPhase,
    criticality?: CriticalityTier
  ): Promise<MissingPathInfo[]> {
    const { data } = await this.client.get('/facts/missing-paths', {
      params: {
        project_id: projectId,
        phase: phase,
        criticality: criticality,
      },
    });
    return data;
  }

  async createManualFact(
    fact: ManualFactCreate,
    createdBy: UUID = '00000000-0000-0000-0000-000000000001', // Dev user
    autoApprove: boolean = false
  ): Promise<ExtractedFact> {
    const { data } = await this.client.post('/facts/manual', fact, {
      params: {
        created_by: createdBy,
        auto_approve: autoApprove,
      },
    });
    return data;
  }

  // ---------------------------------------------------------------------------
  // Playbooks
  // ---------------------------------------------------------------------------

  async listPlaybooks(includeInactive = false): Promise<{ playbooks: Playbook[] }> {
    const { data } = await this.client.get('/playbooks/', {
      params: { include_inactive: includeInactive },
    });
    return data;
  }

  async getPlaybook(playbookId: UUID): Promise<Playbook> {
    const { data } = await this.client.get(`/playbooks/${playbookId}`);
    return data;
  }

  async getDefaultPlaybook(): Promise<Playbook> {
    const { data } = await this.client.get('/playbooks/default');
    return data;
  }

  // ---------------------------------------------------------------------------
  // Checklist
  // ---------------------------------------------------------------------------

  async listChecklistItems(params: {
    project_id: UUID;
    phase?: ChecklistPhase;
    status_filter?: string;
  }): Promise<{ checklist_items: ChecklistItemStatus[]; total: number }> {
    const { data } = await this.client.get('/checklist/', { params });
    return data;
  }

  async getChecklistSummary(
    projectId: UUID
  ): Promise<Record<ChecklistPhase, ChecklistPhaseSummary>> {
    const { data } = await this.client.get('/checklist/summary', {
      params: { project_id: projectId },
    });
    return data;
  }

  async getChecklistItem(
    projectId: UUID,
    itemCode: string
  ): Promise<ChecklistItemStatus> {
    const { data } = await this.client.get(`/checklist/${itemCode}`, {
      params: { project_id: projectId },
    });
    return data;
  }

  async getChecklistGaps(projectId: UUID): Promise<{
    gaps: Array<{ schema_path: string; criticality: string }>;
    total_gaps: number;
  }> {
    const { data } = await this.client.get('/checklist/gaps', {
      params: { project_id: projectId },
    });
    return data;
  }

  // ---------------------------------------------------------------------------
  // Readiness
  // ---------------------------------------------------------------------------

  async getReadinessAssessment(projectId: UUID): Promise<ReadinessAssessment> {
    const { data } = await this.client.get('/readiness/', {
      params: { project_id: projectId },
    });
    return data;
  }

  async getReadinessGaps(projectId: UUID): Promise<{
    critical_gaps: Array<{ schema_path: string; description: string }>;
    material_gaps: Array<{ schema_path: string; description: string }>;
    priority_actions: string[];
  }> {
    const { data } = await this.client.get('/readiness/gaps', {
      params: { project_id: projectId },
    });
    return data;
  }

  // ---------------------------------------------------------------------------
  // Artifacts
  // ---------------------------------------------------------------------------

  async uploadArtifact(
    projectId: UUID,
    file: File,
    displayName?: string
  ): Promise<{ id: string; filename: string; status: string }> {
    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('file', file);
    if (displayName) {
      formData.append('display_name', displayName);
    }

    const { data } = await this.client.post('/artifacts/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return data;
  }

  async listArtifacts(
    projectId: UUID,
    params?: { skip?: number; limit?: number }
  ): Promise<{
    artifacts: Array<{
      id: string;
      filename: string;
      display_name: string;
      artifact_type: string;
      is_processed: boolean;
      is_extracted: boolean;
      chunk_count: number;
      created_at: string;
    }>;
    total: number;
  }> {
    const { data } = await this.client.get('/artifacts/', {
      params: { project_id: projectId, ...params },
    });
    return data;
  }

  async processArtifact(artifactId: string): Promise<{ artifact_id: string; status: string }> {
    const { data } = await this.client.post(`/artifacts/${artifactId}/process`);
    return data;
  }

  async deleteArtifact(artifactId: string): Promise<void> {
    await this.client.delete(`/artifacts/${artifactId}`);
  }

  async resetArtifactExtraction(artifactId: string): Promise<{ artifact_id: string; status: string; message: string }> {
    const { data } = await this.client.post(`/artifacts/${artifactId}/reset-extraction`);
    return data;
  }

  async triggerExtraction(
    projectId: UUID,
    artifactIds: string[]
  ): Promise<{ job_id: string; status: string }> {
    const { data } = await this.client.post('/extraction/', {
      project_id: projectId,
      artifact_ids: artifactIds,
    });
    return data;
  }

  async runExtraction(jobId: string): Promise<{
    job_id: string;
    status: string;
    message: string;
    facts_extracted: number;
    total_chunks?: number;
  }> {
    const { data } = await this.client.post(`/extraction/${jobId}/run`);
    return data;
  }

  // ---------------------------------------------------------------------------
  // Extraction Jobs
  // ---------------------------------------------------------------------------

  async getExtractionJob(jobId: string): Promise<{
    id: string;
    project_id: string;
    status: string;
    facts_extracted: number;
    total_chunks: number;
    processed_chunks: number;
  }> {
    const { data } = await this.client.get(`/extraction/${jobId}`);
    return data;
  }

  async listExtractionJobs(
    projectId: UUID,
    params?: { status_filter?: string; skip?: number; limit?: number }
  ): Promise<{
    jobs: Array<{
      id: string;
      job_type: string;
      status: string;
      facts_extracted: number;
      created_at: string;
      completed_at: string | null;
    }>;
    total: number;
  }> {
    const { data } = await this.client.get('/extraction/', {
      params: { project_id: projectId, ...params },
    });
    return data;
  }

  // ---------------------------------------------------------------------------
  // Readiness (correct endpoints)
  // ---------------------------------------------------------------------------

  async getReadiness(projectId: UUID): Promise<ReadinessAssessment> {
    const { data } = await this.client.get('/readiness/', {
      params: { project_id: projectId },
    });
    return data;
  }

  async getReadinessExplanation(projectId: UUID): Promise<{
    summary: string;
    overall_score: number;
    recommendation: string;
    next_steps: string[];
    metrics: {
      total_facts_approved: number;
      total_facts_pending: number;
      critical_gaps: number;
      material_gaps: number;
    };
  }> {
    const { data } = await this.client.get('/readiness/explanation', {
      params: { project_id: projectId },
    });
    return data;
  }

  // ---------------------------------------------------------------------------
  // Deliverable Packs
  // ---------------------------------------------------------------------------

  async createDeliverablePack(
    pack: DeliverablePackCreate,
    sync: boolean = true // Default to sync for testing without Celery
  ): Promise<{ pack_id: string; status: string }> {
    const { data } = await this.client.post('/deliverables/', pack, {
      params: { sync },
    });
    return data;
  }

  async listDeliverablePacks(
    projectId: UUID
  ): Promise<{ packs: DeliverablePackSummary[]; total: number }> {
    const { data } = await this.client.get('/deliverables/', {
      params: { project_id: projectId },
    });
    // Backend returns array directly, wrap it
    const packs = Array.isArray(data) ? data : [];
    return { packs, total: packs.length };
  }

  async getDeliverablePack(packId: UUID): Promise<DeliverablePack> {
    const { data } = await this.client.get(`/deliverables/${packId}`);
    return data;
  }

  async getDeliverablePackStatus(
    packId: UUID
  ): Promise<{ pack_id: string; is_complete: boolean; sections_generated: number }> {
    const { data } = await this.client.get(`/deliverables/${packId}/status`);
    return data;
  }

  async regenerateDeliverablePack(
    packId: UUID,
    sync: boolean = true // Default to sync for testing without Celery
  ): Promise<{ pack_id: string; status: string }> {
    const { data } = await this.client.post(`/deliverables/${packId}/regenerate`, null, {
      params: { sync },
    });
    return data;
  }

  async exportDeliverableMarkdown(packId: UUID): Promise<string> {
    const { data } = await this.client.get(`/deliverables/${packId}/export/markdown`);
    // API returns { pack_id, title, format, content }
    return data.content;
  }

  async exportDeliverablePdf(
    packId: UUID
  ): Promise<{ pack_id: string; status: string; task_id: string }> {
    const { data } = await this.client.post(`/deliverables/${packId}/export/pdf`);
    return data;
  }

  // ---------------------------------------------------------------------------
  // Health
  // ---------------------------------------------------------------------------

  async healthCheck(): Promise<{ status: string; version: string }> {
    const { data } = await this.client.get('/health');
    return data;
  }
}

export const api = new ApiClient();
