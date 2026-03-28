/**
 * API client for Muni-Pal BFMS backend.
 *
 * This adapter keeps the existing page-facing method signatures while routing
 * runtime calls through the generated OpenAPI client services.
 */

import axios from 'axios'
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
  DisclosureDocument,
  DisclosureDocumentSummary,
  GenerateDisclosureRequest,
  DisclosureSection,
  InformationRequest,
  InformationRequestSummary,
  InformationRequestReport,
  RequestStatus,
  RequestPriority,
  InternalReadinessReport,
  InternalReportSummary,
  ExternalAdvisoryPackage,
  ExternalPackageSummary,
  DistributionValidation,
  SchemaPathMetadata,
  RiskBfmsCohortParams,
  RiskBfmsIntegrationResponse,
  RevenueDiversificationVisualizationResponse,
} from '../types'
import {
  ApiError,
  AdvisoryPackagesService,
  ArtifactsService,
  ChecklistService,
  DeliverablesService,
  DisclosureService,
  ExtractionService,
  FactsService,
  HealthService,
  InformationRequestsService,
  OpenAPI,
  PlaybooksService,
  ProjectsService,
  ReadinessService,
  RiskService,
} from './generatedApi'

const DEV_USER_ID = '00000000-0000-0000-0000-000000000001'
const DEFAULT_RISK_BFMS_COHORT: RiskBfmsCohortParams = {
  sector: 'waste_to_energy',
  issuer_size_band: 'mid',
  deal_type: 'revenue',
  recency_window: '5y',
  sample_size: 50,
}
type OpenApiSetting<T> = T | ((options?: unknown) => T | Promise<T>)

const isNotFoundError = (error: unknown): boolean =>
  error instanceof ApiError && error.status === 404

const resolveOpenApiSetting = async <T,>(
  value: OpenApiSetting<T> | undefined
): Promise<T | undefined> => {
  if (typeof value === 'function') {
    const resolver = value as (options?: unknown) => T | Promise<T>
    return await resolver()
  }
  return value
}

class ApiClient {
  // ---------------------------------------------------------------------------
  // Projects
  // ---------------------------------------------------------------------------

  async listProjects(params?: {
    skip?: number
    limit?: number
  }): Promise<ProjectListResponse> {
    const data = await ProjectsService.listProjectsApiV1ProjectsGet(
      params?.skip,
      params?.limit ?? 50
    )
    return data as unknown as ProjectListResponse
  }

  async getProject(projectId: UUID): Promise<Project> {
    const data = await ProjectsService.getProjectApiV1ProjectsProjectIdGet(projectId)
    return data as unknown as Project
  }

  async createProject(project: ProjectCreate): Promise<Project> {
    const data = await ProjectsService.createProjectApiV1ProjectsPost(
      project as any
    )
    return data as unknown as Project
  }

  async updateProject(
    projectId: UUID,
    updates: Partial<ProjectCreate>
  ): Promise<Project> {
    const data = await ProjectsService.updateProjectApiV1ProjectsProjectIdPatch(
      projectId,
      updates as unknown as Record<string, unknown>
    )
    return data as unknown as Project
  }

  async deleteProject(projectId: UUID): Promise<void> {
    await ProjectsService.deleteProjectApiV1ProjectsProjectIdDelete(projectId)
  }

  // ---------------------------------------------------------------------------
  // Facts
  // ---------------------------------------------------------------------------

  async listFacts(params: {
    project_id: UUID
    status?: ReviewStatus
    schema_path_prefix?: string
    min_confidence?: number
    limit?: number
    offset?: number
  }): Promise<FactListResponse> {
    const data = await FactsService.listFactsApiV1FactsGet(
      params.project_id,
      undefined,
      params.status as unknown as never,
      undefined,
      params.schema_path_prefix,
      params.min_confidence,
      undefined,
      false,
      params.limit ?? 100,
      params.offset ?? 0
    )
    return data as unknown as FactListResponse
  }

  async getFact(factId: UUID): Promise<ExtractedFact> {
    const data = await FactsService.getFactApiV1FactsFactIdGet(factId)
    return data as unknown as ExtractedFact
  }

  async reviewFact(
    factId: UUID,
    review: FactReviewRequest,
    reviewerId: UUID = DEV_USER_ID
  ): Promise<ExtractedFact> {
    const data = await FactsService.reviewFactApiV1FactsFactIdReviewPost(
      factId,
      review as any,
      reviewerId
    )
    return data as unknown as ExtractedFact
  }

  async getFactStatusCounts(
    projectId: UUID
  ): Promise<Record<ReviewStatus, number>> {
    const data = await FactsService.getReviewCountsApiV1FactsCountsGet(projectId)
    return data as unknown as Record<ReviewStatus, number>
  }

  async getFactConflicts(projectId: UUID): Promise<{
    conflicts: Array<{
      schema_path: string
      fact_count: number
      facts: ExtractedFact[]
    }>
  }> {
    const data = await FactsService.findConflictsApiV1FactsConflictsGet(projectId)
    return data as unknown as {
      conflicts: Array<{
        schema_path: string
        fact_count: number
        facts: ExtractedFact[]
      }>
    }
  }

  async getMissingPaths(
    projectId: UUID,
    phase?: ChecklistPhase,
    criticality?: CriticalityTier
  ): Promise<MissingPathInfo[]> {
    const data = await FactsService.getMissingPathsApiV1FactsMissingPathsGet(
      projectId,
      phase,
      criticality
    )
    return data as unknown as MissingPathInfo[]
  }

  async createManualFact(
    fact: ManualFactCreate,
    createdBy: UUID = DEV_USER_ID,
    autoApprove = false
  ): Promise<ExtractedFact> {
    const data = await FactsService.createManualFactApiV1FactsManualPost(
      createdBy,
      fact as any,
      autoApprove
    )
    return data as unknown as ExtractedFact
  }

  // ---------------------------------------------------------------------------
  // Playbooks
  // ---------------------------------------------------------------------------

  async listPlaybooks(includeInactive = false): Promise<{ playbooks: Playbook[] }> {
    const data = await PlaybooksService.listPlaybooksApiV1PlaybooksGet(includeInactive)
    return data as unknown as { playbooks: Playbook[] }
  }

  async getPlaybook(playbookId: UUID): Promise<Playbook> {
    const data = await PlaybooksService.getPlaybookApiV1PlaybooksPlaybookIdGet(playbookId)
    return data as unknown as Playbook
  }

  async getDefaultPlaybook(): Promise<Playbook> {
    const data = await PlaybooksService.getDefaultPlaybookApiV1PlaybooksDefaultGet()
    return data as unknown as Playbook
  }

  async listSchemaPathsMetadata(): Promise<SchemaPathMetadata[]> {
    const data = await PlaybooksService.listSchemaPathsApiV1PlaybooksSchemaPathsGet()
    return data as unknown as SchemaPathMetadata[]
  }

  async getSchemaPathMetadata(schemaPath: string): Promise<SchemaPathMetadata> {
    const data = await PlaybooksService.getSchemaPathDetailApiV1PlaybooksSchemaPathsSchemaPathGet(
      schemaPath
    )
    return data as unknown as SchemaPathMetadata
  }

  async getSchemaPathsMetadataBatch(paths: string[]): Promise<Record<string, SchemaPathMetadata>> {
    const data = await PlaybooksService.getSchemaPathsBatchApiV1PlaybooksSchemaPathsBatchGet(paths)
    return data as unknown as Record<string, SchemaPathMetadata>
  }

  // ---------------------------------------------------------------------------
  // Checklist
  // ---------------------------------------------------------------------------

  async listChecklistItems(params: {
    project_id: UUID
    phase?: ChecklistPhase
    status_filter?: string
  }): Promise<{ checklist_items: ChecklistItemStatus[]; total: number }> {
    const data = await ChecklistService.listChecklistItemsApiV1ChecklistGet(
      params.project_id,
      params.phase,
      params.status_filter as unknown as never
    )
    return data as unknown as { checklist_items: ChecklistItemStatus[]; total: number }
  }

  async getChecklistSummary(
    projectId: UUID
  ): Promise<Record<ChecklistPhase, ChecklistPhaseSummary>> {
    const data = await ChecklistService.getChecklistSummaryApiV1ChecklistSummaryGet(projectId)
    return data as unknown as Record<ChecklistPhase, ChecklistPhaseSummary>
  }

  async getChecklistItem(
    projectId: UUID,
    itemCode: string
  ): Promise<ChecklistItemStatus> {
    const data = await ChecklistService.getChecklistItemApiV1ChecklistItemCodeGet(
      itemCode,
      projectId
    )
    return data as unknown as ChecklistItemStatus
  }

  async getChecklistGaps(projectId: UUID): Promise<{
    gaps: Array<{ schema_path: string; criticality: string }>
    total_gaps: number
  }> {
    const data = await ChecklistService.getProjectGapsApiV1ChecklistGapsGet(projectId)
    return data as unknown as {
      gaps: Array<{ schema_path: string; criticality: string }>
      total_gaps: number
    }
  }

  // ---------------------------------------------------------------------------
  // Readiness
  // ---------------------------------------------------------------------------

  async getReadinessAssessment(projectId: UUID): Promise<ReadinessAssessment> {
    const data = await ReadinessService.getReadinessScoresApiV1ReadinessGet(projectId)
    return data as unknown as ReadinessAssessment
  }

  async getReadinessGaps(projectId: UUID): Promise<{
    critical_gaps: Array<{ schema_path: string; description: string; short_description: string }>
    material_gaps: Array<{ schema_path: string; description: string; short_description: string }>
    priority_actions: string[]
  }> {
    const data = await ReadinessService.getReadinessGapsApiV1ReadinessGapsGet(projectId)
    return data as unknown as {
      critical_gaps: Array<{ schema_path: string; description: string; short_description: string }>
      material_gaps: Array<{ schema_path: string; description: string; short_description: string }>
      priority_actions: string[]
    }
  }

  async getReadiness(projectId: UUID): Promise<ReadinessAssessment> {
    return this.getReadinessAssessment(projectId)
  }

  async getRiskBfmsIntegration(
    projectId: UUID,
    cohortOverrides: Partial<RiskBfmsCohortParams> = {}
  ): Promise<RiskBfmsIntegrationResponse | null> {
    const cohort = {
      ...DEFAULT_RISK_BFMS_COHORT,
      ...cohortOverrides,
    }
    try {
      const data = await RiskService.getRiskBfmsIntegrationPayloadApiV1RiskBfmsIntegrationGet(
        projectId,
        cohort.sector,
        cohort.issuer_size_band,
        cohort.deal_type,
        cohort.recency_window,
        cohort.sample_size
      )
      return data as unknown as RiskBfmsIntegrationResponse
    } catch (error: unknown) {
      if (isNotFoundError(error)) {
        return null
      }
      throw error
    }
  }

  async getRevenueDiversificationVisualization(
    projectId: UUID,
    mode: 'auto' | 'native' | 'packet' = 'auto'
  ): Promise<RevenueDiversificationVisualizationResponse> {
    const token = await resolveOpenApiSetting<string>(
      OpenAPI.TOKEN as OpenApiSetting<string> | undefined
    )
    const base = OpenAPI.BASE ? `${OpenAPI.BASE}/api/v1/risk/revenue-diversification` : '/api/v1/risk/revenue-diversification'
    const resolvedHeaders = await resolveOpenApiSetting<Record<string, string>>(
      OpenAPI.HEADERS as OpenApiSetting<Record<string, string>> | undefined
    )
    const headers = {
      ...(resolvedHeaders ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    }
    const { data } = await axios.get(base, {
      params: { project_id: projectId, mode },
      headers,
    })
    return data as RevenueDiversificationVisualizationResponse
  }

  async getReadinessExplanation(projectId: UUID): Promise<{
    summary: string
    overall_score: number
    recommendation: string
    next_steps: string[]
    metrics: {
      total_facts_approved: number
      total_facts_pending: number
      critical_gaps: number
      material_gaps: number
    }
  }> {
    const data = await ReadinessService.getReadinessExplanationApiV1ReadinessExplanationGet(
      projectId
    )
    return data as unknown as {
      summary: string
      overall_score: number
      recommendation: string
      next_steps: string[]
      metrics: {
        total_facts_approved: number
        total_facts_pending: number
        critical_gaps: number
        material_gaps: number
      }
    }
  }

  // ---------------------------------------------------------------------------
  // Artifacts
  // ---------------------------------------------------------------------------

  async uploadArtifact(
    projectId: UUID,
    file: File,
    displayName?: string
  ): Promise<{ id: string; filename: string; status: string }> {
    const artifact = await ArtifactsService.uploadArtifactApiV1ArtifactsUploadPost({
      project_id: projectId,
      file: file as unknown as string,
      display_name: displayName,
    })
    return {
      id: artifact.id,
      filename: artifact.filename,
      status: artifact.is_extracted ? 'extracted' : artifact.is_processed ? 'processed' : 'uploaded',
    }
  }

  async listArtifacts(
    projectId: UUID,
    params?: { skip?: number; limit?: number }
  ): Promise<{
    artifacts: Array<{
      id: string
      filename: string
      display_name: string
      artifact_type: string
      is_processed: boolean
      is_extracted: boolean
      chunk_count: number
      created_at: string
    }>
    total: number
  }> {
    const data = await ArtifactsService.listArtifactsApiV1ArtifactsGet(
      projectId,
      params?.skip,
      params?.limit ?? 50
    )
    return data as unknown as {
      artifacts: Array<{
        id: string
        filename: string
        display_name: string
        artifact_type: string
        is_processed: boolean
        is_extracted: boolean
        chunk_count: number
        created_at: string
      }>
      total: number
    }
  }

  async processArtifact(artifactId: string): Promise<{ artifact_id: string; status: string }> {
    const data = await ArtifactsService.triggerProcessingApiV1ArtifactsArtifactIdProcessPost(
      artifactId
    )
    return data as unknown as { artifact_id: string; status: string }
  }

  async deleteArtifact(artifactId: string): Promise<void> {
    await ArtifactsService.deleteArtifactApiV1ArtifactsArtifactIdDelete(artifactId)
  }

  async resetArtifactExtraction(artifactId: string): Promise<{ artifact_id: string; status: string; message: string }> {
    const data =
      await ArtifactsService.resetExtractionStatusApiV1ArtifactsArtifactIdResetExtractionPost(
        artifactId
      )
    return data as unknown as { artifact_id: string; status: string; message: string }
  }

  async triggerExtraction(
    projectId: UUID,
    artifactIds: string[]
  ): Promise<{ job_id: string; status: string }> {
    const data = await ExtractionService.createExtractionJobApiV1ExtractionPost({
      project_id: projectId,
      artifact_ids: artifactIds,
    })
    return {
      job_id: data.job_id,
      status: data.status,
    }
  }

  async runExtraction(jobId: string): Promise<{
    job_id: string
    status: string
    message: string
    facts_extracted: number
    total_chunks?: number
  }> {
    const data = await ExtractionService.runExtractionJobApiV1ExtractionJobIdRunPost(jobId)
    return data as unknown as {
      job_id: string
      status: string
      message: string
      facts_extracted: number
      total_chunks?: number
    }
  }

  // ---------------------------------------------------------------------------
  // Extraction Jobs
  // ---------------------------------------------------------------------------

  async getExtractionJob(jobId: string): Promise<{
    id: string
    project_id: string
    status: string
    facts_extracted: number
    total_chunks: number
    processed_chunks: number
  }> {
    const data = await ExtractionService.getExtractionJobApiV1ExtractionJobIdGet(jobId)
    return data as unknown as {
      id: string
      project_id: string
      status: string
      facts_extracted: number
      total_chunks: number
      processed_chunks: number
    }
  }

  async listExtractionJobs(
    projectId: UUID,
    params?: { status_filter?: string; skip?: number; limit?: number }
  ): Promise<{
    jobs: Array<{
      id: string
      job_type: string
      status: string
      facts_extracted: number
      created_at: string
      completed_at: string | null
    }>
    total: number
  }> {
    const data = await ExtractionService.listExtractionJobsApiV1ExtractionGet(
      projectId,
      params?.status_filter,
      params?.skip,
      params?.limit ?? 50
    )
    return data as unknown as {
      jobs: Array<{
        id: string
        job_type: string
        status: string
        facts_extracted: number
        created_at: string
        completed_at: string | null
      }>
      total: number
    }
  }

  // ---------------------------------------------------------------------------
  // Deliverable Packs
  // ---------------------------------------------------------------------------

  async createDeliverablePack(
    pack: DeliverablePackCreate,
    sync = true
  ): Promise<{ pack_id: string; status: string }> {
    const data = await DeliverablesService.createPackApiV1DeliverablesPost(
      pack as any,
      sync
    )
    return data as unknown as { pack_id: string; status: string }
  }

  async listDeliverablePacks(
    projectId: UUID
  ): Promise<{ packs: DeliverablePackSummary[]; total: number }> {
    const packs = await DeliverablesService.listPacksApiV1DeliverablesGet(projectId)
    return {
      packs: packs as unknown as DeliverablePackSummary[],
      total: packs.length,
    }
  }

  async getDeliverablePack(packId: UUID): Promise<DeliverablePack> {
    const data = await DeliverablesService.getPackApiV1DeliverablesPackIdGet(packId)
    return data as unknown as DeliverablePack
  }

  async getDeliverablePackStatus(
    packId: UUID
  ): Promise<{ pack_id: string; is_complete: boolean; sections_generated: number }> {
    const data = await DeliverablesService.getPackStatusApiV1DeliverablesPackIdStatusGet(packId)
    return data as unknown as { pack_id: string; is_complete: boolean; sections_generated: number }
  }

  async regenerateDeliverablePack(
    packId: UUID,
    sync = true
  ): Promise<{ pack_id: string; status: string }> {
    const data = await DeliverablesService.regeneratePackApiV1DeliverablesPackIdRegeneratePost(
      packId,
      sync
    )
    return data as unknown as { pack_id: string; status: string }
  }

  async exportDeliverableMarkdown(packId: UUID): Promise<string> {
    const data = await DeliverablesService.exportMarkdownApiV1DeliverablesPackIdExportMarkdownGet(
      packId
    )
    return (data as { content?: string }).content ?? ''
  }

  async exportDeliverablePdf(
    packId: UUID
  ): Promise<{ pack_id: string; status: string; task_id: string }> {
    const data = await DeliverablesService.exportPdfApiV1DeliverablesPackIdExportPdfPost(packId)
    return data as unknown as { pack_id: string; status: string; task_id: string }
  }

  // ---------------------------------------------------------------------------
  // v2 - WP7: Disclosure Synthesis Engine
  // ---------------------------------------------------------------------------

  async generateDisclosure(
    request: GenerateDisclosureRequest
  ): Promise<{ document_id: string; status: string; completeness_score: number }> {
    const data = await DisclosureService.generateDisclosureDocumentApiV1DisclosureGeneratePost(
      request as any
    )
    return {
      document_id: data.document_id,
      status: data.status,
      completeness_score: 0,
    }
  }

  async getDisclosureDocument(documentId: UUID): Promise<DisclosureDocument> {
    const data = await DisclosureService.getDisclosureDocumentApiV1DisclosureDocumentIdGet(documentId)
    return data as unknown as DisclosureDocument
  }

  async listDisclosureDocuments(
    projectId: UUID
  ): Promise<{ documents: DisclosureDocumentSummary[]; total: number }> {
    const data = await DisclosureService.listDisclosureDocumentsApiV1DisclosureGet(projectId)
    return data as unknown as { documents: DisclosureDocumentSummary[]; total: number }
  }

  async getLatestDisclosure(projectId: UUID): Promise<DisclosureDocument | null> {
    try {
      const data =
        await DisclosureService.getLatestDisclosureDocumentApiV1DisclosureProjectProjectIdLatestGet(
          projectId
        )
      return (data as unknown as DisclosureDocument) ?? null
    } catch (error: unknown) {
      if (isNotFoundError(error)) {
        return null
      }
      throw error
    }
  }

  async previewDisclosureSection(
    sectionId: UUID,
    projectId?: UUID
  ): Promise<DisclosureSection> {
    if (!projectId) {
      throw new Error('projectId is required to preview a disclosure section')
    }
    const data =
      await DisclosureService.previewDisclosureSectionApiV1DisclosurePreviewSectionSectionIdGet(
        sectionId,
        projectId
      )
    if (!data) {
      throw new Error(`Section ${sectionId} not found`)
    }
    return data as unknown as DisclosureSection
  }

  async exportDisclosure(
    documentId: UUID,
    format: 'md' | 'pdf' | 'docx' = 'md'
  ): Promise<{ format: string; filename: string; content?: string }> {
    const data = await DisclosureService.exportDisclosureDocumentApiV1DisclosureDocumentIdExportGet(
      documentId,
      format
    )
    return data as unknown as { format: string; filename: string; content?: string }
  }

  // ---------------------------------------------------------------------------
  // v2 - WP8: Information Request System
  // ---------------------------------------------------------------------------

  async generateInformationRequests(
    projectId: UUID,
    _regenerate = false
  ): Promise<{ project_id: string; requests_created: number; request_ids: string[] }> {
    const data =
      await InformationRequestsService.generateInformationRequestsApiV1InformationRequestsGeneratePost(
        projectId
      )
    const summaries = Array.isArray((data as { requests?: unknown[] }).requests)
      ? ((data as { requests?: Array<{ id?: string }> }).requests ?? [])
      : []
    return {
      project_id: projectId,
      requests_created: (data as { generated_count?: number }).generated_count ?? summaries.length,
      request_ids: summaries.map((item) => item.id ?? '').filter((id) => id.length > 0),
    }
  }

  async listInformationRequests(params: {
    project_id: UUID
    status?: RequestStatus
    priority?: RequestPriority
    owner?: string
    limit?: number
    offset?: number
  }): Promise<{ requests: InformationRequestSummary[]; total: number }> {
    const data = await InformationRequestsService.listInformationRequestsApiV1InformationRequestsGet(
      params.project_id,
      params.status as unknown as never,
      params.priority as unknown as never,
      params.owner,
      params.limit ?? 100,
      params.offset ?? 0
    )
    return data as unknown as { requests: InformationRequestSummary[]; total: number }
  }

  async getInformationRequest(requestId: UUID): Promise<InformationRequest> {
    const data = await InformationRequestsService.getInformationRequestApiV1InformationRequestsRequestIdGet(
      requestId
    )
    return data as unknown as InformationRequest
  }

  async updateInformationRequest(
    requestId: UUID,
    updates: Partial<{
      status: RequestStatus
      suggested_owner: string
      target_date: string
      resolution_notes: string
    }>
  ): Promise<InformationRequest> {
    const data = await InformationRequestsService.updateInformationRequestApiV1InformationRequestsRequestIdPatch(
      requestId,
      updates as unknown as Record<string, unknown>
    )
    return data as unknown as InformationRequest
  }

  async acknowledgeInformationRequest(
    requestId: UUID,
    userId?: UUID
  ): Promise<InformationRequest> {
    const data =
      await InformationRequestsService.acknowledgeRequestApiV1InformationRequestsRequestIdAcknowledgePost(
        requestId,
        userId
      )
    return data as unknown as InformationRequest
  }

  async submitInformationRequest(
    requestId: UUID,
    artifactId?: UUID
  ): Promise<InformationRequest> {
    if (!artifactId) {
      throw new Error('artifactId is required to submit an information request')
    }
    const data =
      await InformationRequestsService.linkEvidenceToRequestApiV1InformationRequestsRequestIdEvidencePost(
        requestId,
        {
          artifact_id: artifactId,
          notes: null,
        }
      )
    return data as unknown as InformationRequest
  }

  async resolveInformationRequest(
    requestId: UUID,
    factIds: UUID[],
    notes?: string
  ): Promise<InformationRequest> {
    const data = await InformationRequestsService.resolveRequestApiV1InformationRequestsRequestIdResolvePost(
      requestId,
      {
        fact_ids: factIds,
        resolution_notes: notes,
      }
    )
    return data as unknown as InformationRequest
  }

  async deferInformationRequest(
    requestId: UUID,
    reason: string,
    reviewDate?: string
  ): Promise<InformationRequest> {
    const data = await InformationRequestsService.deferRequestApiV1InformationRequestsRequestIdDeferPost(
      requestId,
      reason,
      reviewDate
    )
    return data as unknown as InformationRequest
  }

  async getInformationRequestReport(projectId: UUID): Promise<InformationRequestReport> {
    const data = await InformationRequestsService.getRequestReportApiV1InformationRequestsReportProjectIdGet(
      projectId
    )
    return data as unknown as InformationRequestReport
  }

  async getOverdueRequests(projectId: UUID): Promise<InformationRequestSummary[]> {
    const data = await InformationRequestsService.getOverdueRequestsApiV1InformationRequestsOverdueProjectIdGet(
      projectId
    )
    return data as unknown as InformationRequestSummary[]
  }

  // ---------------------------------------------------------------------------
  // v2 - Bifurcated Deliverables: Internal Readiness Reports
  // ---------------------------------------------------------------------------

  async generateInternalReport(
    projectId: UUID
  ): Promise<{ report_id: string; status: string }> {
    const data = await AdvisoryPackagesService.generateInternalReportApiV1AdvisoryPackagesInternalGeneratePost(
      {
        project_id: projectId,
      }
    )
    return {
      report_id: data.report_id,
      status: data.status,
    }
  }

  async getInternalReport(reportId: UUID): Promise<InternalReadinessReport> {
    const data = await AdvisoryPackagesService.getInternalReportApiV1AdvisoryPackagesInternalReportIdGet(
      reportId
    )
    return data as unknown as InternalReadinessReport
  }

  async listInternalReports(
    projectId: UUID
  ): Promise<{ reports: InternalReportSummary[]; total: number }> {
    const data = await AdvisoryPackagesService.listInternalReportsApiV1AdvisoryPackagesInternalGet(
      projectId
    )
    return data as unknown as { reports: InternalReportSummary[]; total: number }
  }

  async getLatestInternalReport(projectId: UUID): Promise<InternalReadinessReport | null> {
    try {
      const data =
        await AdvisoryPackagesService.getLatestInternalReportApiV1AdvisoryPackagesInternalProjectProjectIdLatestGet(
          projectId
        )
      return (data as unknown as InternalReadinessReport) ?? null
    } catch (error: unknown) {
      if (isNotFoundError(error)) {
        return null
      }
      throw error
    }
  }

  async exportInternalReport(
    reportId: UUID,
    format: 'md' | 'pdf' | 'html' = 'md'
  ): Promise<{ format: string; filename: string; content?: string }> {
    const data = await AdvisoryPackagesService.exportInternalReportApiV1AdvisoryPackagesInternalReportIdExportGet(
      reportId,
      format
    )
    return data as unknown as { format: string; filename: string; content?: string }
  }

  // ---------------------------------------------------------------------------
  // v2 - Bifurcated Deliverables: External Advisory Packages
  // ---------------------------------------------------------------------------

  async generateExternalPackage(
    projectId: UUID,
    title: string,
    generatedFor: string,
    disclosureDocumentId?: UUID
  ): Promise<{ package_id: string; status: string }> {
    const data =
      await AdvisoryPackagesService.generateExternalPackageApiV1AdvisoryPackagesExternalGeneratePost(
        {
          project_id: projectId,
          title,
          generated_for: generatedFor,
          include_disclosure: !!disclosureDocumentId,
        }
      )
    return {
      package_id: data.package_id,
      status: data.status,
    }
  }

  async getExternalPackage(packageId: UUID): Promise<ExternalAdvisoryPackage> {
    const data = await AdvisoryPackagesService.getExternalPackageApiV1AdvisoryPackagesExternalPackageIdGet(
      packageId
    )
    return data as unknown as ExternalAdvisoryPackage
  }

  async listExternalPackages(
    projectId: UUID
  ): Promise<{ packages: ExternalPackageSummary[]; total: number }> {
    const data = await AdvisoryPackagesService.listExternalPackagesApiV1AdvisoryPackagesExternalGet(
      projectId
    )
    return data as unknown as { packages: ExternalPackageSummary[]; total: number }
  }

  async getLatestExternalPackage(projectId: UUID): Promise<ExternalAdvisoryPackage | null> {
    try {
      const data =
        await AdvisoryPackagesService.getLatestExternalPackageApiV1AdvisoryPackagesExternalProjectProjectIdLatestGet(
          projectId
        )
      return (data as unknown as ExternalAdvisoryPackage) ?? null
    } catch (error: unknown) {
      if (isNotFoundError(error)) {
        return null
      }
      throw error
    }
  }

  async validateExternalPackage(packageId: UUID): Promise<DistributionValidation> {
    const data =
      await AdvisoryPackagesService.validateExternalPackageApiV1AdvisoryPackagesExternalPackageIdValidateGet(
        packageId
      )
    return data as unknown as DistributionValidation
  }

  async exportExternalPackage(
    packageId: UUID,
    format: 'pdf' | 'md' | 'docx' = 'pdf'
  ): Promise<{ format: string; filename: string; content?: string }> {
    const data = await AdvisoryPackagesService.exportExternalPackageApiV1AdvisoryPackagesExternalPackageIdExportGet(
      packageId,
      format
    )
    return data as unknown as { format: string; filename: string; content?: string }
  }

  // ---------------------------------------------------------------------------
  // Health
  // ---------------------------------------------------------------------------

  async healthCheck(): Promise<{ status: string; version: string }> {
    const data = await HealthService.healthCheckHealthGet()
    return data as unknown as { status: string; version: string }
  }
}

export const api = new ApiClient()
