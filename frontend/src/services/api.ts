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
  Playbook,
  ChecklistItemStatus,
  ChecklistPhaseSummary,
  ReadinessAssessment,
  ReviewStatus,
  ChecklistPhase,
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
    review: FactReviewRequest
  ): Promise<ExtractedFact> {
    const { data } = await this.client.post(`/facts/${factId}/review`, review);
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
    const { data } = await this.client.get(`/readiness/${projectId}`);
    return data;
  }

  async getReadinessGaps(projectId: UUID): Promise<{
    critical_gaps: Array<{ schema_path: string; description: string }>;
    material_gaps: Array<{ schema_path: string; description: string }>;
    priority_actions: string[];
  }> {
    const { data } = await this.client.get(`/readiness/${projectId}/gaps`);
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
