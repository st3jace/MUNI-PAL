import { useParams, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useRef, useState, useCallback } from 'react'
import {
  FileCheck,
  ClipboardList,
  Gauge,
  Upload,
  AlertCircle,
  CheckCircle,
  Clock,
  Loader2,
  FileText,
  Play,
  Trash2,
  Sparkles,
  Zap,
  RotateCcw,
  MoreVertical,
  BarChart3,
} from 'lucide-react'
import { api } from '../services/api'

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [uploadStatus, setUploadStatus] = useState<{ uploading: boolean; message?: string }>({
    uploading: false,
  })
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  })

  const { data: artifactsData } = useQuery({
    queryKey: ['artifacts', projectId],
    queryFn: () => api.listArtifacts(projectId!),
    enabled: !!projectId,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => api.uploadArtifact(projectId!, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['artifacts', projectId] })
      setUploadStatus({ uploading: false, message: 'Upload successful!' })
      setTimeout(() => setUploadStatus({ uploading: false }), 3000)
    },
    onError: (error: Error) => {
      setUploadStatus({ uploading: false, message: `Upload failed: ${error.message}` })
      setTimeout(() => setUploadStatus({ uploading: false }), 5000)
    },
  })

  const processMutation = useMutation({
    mutationFn: (artifactId: string) => api.processArtifact(artifactId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['artifacts', projectId] })
    },
  })

  const extractionMutation = useMutation({
    mutationFn: async (artifactIds: string[]) => {
      // First create the job
      const job = await api.triggerExtraction(projectId!, artifactIds)
      // Then run it synchronously
      const result = await api.runExtraction(job.job_id)
      return result
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['artifacts', projectId] })
      queryClient.invalidateQueries({ queryKey: ['extractionJobs', projectId] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (artifactId: string) => api.deleteArtifact(artifactId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['artifacts', projectId] })
      setOpenMenuId(null)
    },
  })

  const resetExtractionMutation = useMutation({
    mutationFn: (artifactId: string) => api.resetArtifactExtraction(artifactId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['artifacts', projectId] })
      setOpenMenuId(null)
    },
  })

  const { data: extractionJobs } = useQuery({
    queryKey: ['extractionJobs', projectId],
    queryFn: () => api.listExtractionJobs(projectId!),
    enabled: !!projectId,
  })

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files || files.length === 0) return
      setUploadStatus({ uploading: true, message: `Uploading ${files.length} file(s)...` })
      Array.from(files).forEach((file) => {
        uploadMutation.mutate(file)
      })
    },
    [uploadMutation]
  )

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(false)
      handleFiles(e.dataTransfer.files)
    },
    [handleFiles]
  )

  const handleClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      handleFiles(e.target.files)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    },
    [handleFiles]
  )

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading project...</div>
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">Project not found</h3>
      </div>
    )
  }

  const quickActions = [
    {
      name: 'Facts Review',
      description: `${project.approved_fact_count} approved / ${project.fact_count} total`,
      href: `/projects/${projectId}/facts`,
      icon: FileCheck,
      color: 'bg-blue-500',
    },
    {
      name: 'Checklist',
      description: 'Track diligence progress',
      href: `/projects/${projectId}/checklist`,
      icon: ClipboardList,
      color: 'bg-purple-500',
    },
    {
      name: 'Readiness',
      description: project.overall_readiness_score
        ? `Score: ${project.overall_readiness_score.toFixed(1)}/10`
        : 'Not yet scored',
      href: `/projects/${projectId}/readiness`,
      icon: Gauge,
      color: 'bg-green-500',
    },
    ...((project.sector === 'waste' || project.archetype_id === 'ucs_wte_cab_slb') ? [{
      name: 'Revenue Mix',
      description: 'Scenario diversification and DSCR view',
      href: `/projects/${projectId}/revenue-diversification`,
      icon: BarChart3,
      color: 'bg-slate-700',
    }] : []),
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
        <p className="mt-1 text-sm text-gray-500">{project.issuer_name}</p>
      </div>

      {/* Project Info */}
      <div className="card p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Project Details</h2>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-sm text-gray-500">Sector</dt>
            <dd className="mt-1 font-medium text-gray-900">
              {project.sector
                ? <span className="inline-flex items-center gap-1.5">
                    <span className="capitalize">{project.sector}</span>
                    {project.subsector && (
                      <span className="text-gray-500 font-normal">
                        / {project.subsector.replace(`${project.sector}_`, '').replace(/_/g, ' ')}
                      </span>
                    )}
                  </span>
                : '—'}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Location</dt>
            <dd className="mt-1 font-medium text-gray-900">
              {project.project_location || '—'}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Target Bond Amount</dt>
            <dd className="mt-1 font-medium text-gray-900">
              {project.target_bond_amount
                ? `$${project.target_bond_amount.toLocaleString()}`
                : '—'}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Artifacts</dt>
            <dd className="mt-1 font-medium text-gray-900">{project.artifact_count}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Total Facts</dt>
            <dd className="mt-1 font-medium text-gray-900">{project.fact_count}</dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Approved Facts</dt>
            <dd className="mt-1 font-medium text-gray-900">
              {project.approved_fact_count}
            </dd>
          </div>
          <div>
            <dt className="text-sm text-gray-500">Readiness Score</dt>
            <dd className="mt-1 font-medium text-gray-900">
              {project.overall_readiness_score?.toFixed(1) ?? 'Not calculated'}
            </dd>
          </div>
        </dl>
        {project.description && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <dt className="text-sm text-gray-500">Description</dt>
            <dd className="mt-1 text-gray-900">{project.description}</dd>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {quickActions.map((action) => (
            <Link
              key={action.name}
              to={action.href}
              className="card p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-4">
                <div className={`${action.color} rounded-lg p-3`}>
                  <action.icon className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">{action.name}</p>
                  <p className="text-sm text-gray-500">{action.description}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      {/* Upload Section */}
      <div className="card p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Upload Documents</h2>
        <div
          onClick={handleClick}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
            isDragging
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400'
          }`}
        >
          {uploadStatus.uploading ? (
            <Loader2 className="mx-auto h-12 w-12 text-primary-500 animate-spin" />
          ) : (
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
          )}
          <p className="mt-2 text-sm font-medium text-gray-900">
            {uploadStatus.message || (isDragging ? 'Drop files here' : 'Drag and drop files here')}
          </p>
          <p className="mt-1 text-sm text-gray-500">
            or click to browse (PDF, DOCX, XLSX, CSV)
          </p>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.docx,.xlsx,.xls,.csv"
            multiple
            onChange={handleFileChange}
          />
        </div>
      </div>

      {/* Uploaded Artifacts */}
      {artifactsData && artifactsData.artifacts.length > 0 && (
        <div className="card">
          <div className="border-b border-gray-200 px-5 py-4 flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">
              Uploaded Documents ({artifactsData.total})
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => {
                  artifactsData.artifacts
                    .filter((a) => !a.is_processed)
                    .forEach((a) => processMutation.mutate(a.id))
                }}
                disabled={
                  processMutation.isPending ||
                  !artifactsData.artifacts.some((a) => !a.is_processed)
                }
                className="btn-secondary text-sm disabled:opacity-50"
              >
                {processMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Process Pending
                  </>
                )}
              </button>
              <button
                onClick={() => {
                  // Only extract from processed artifacts that haven't been extracted yet
                  const unextractedArtifactIds = artifactsData.artifacts
                    .filter((a) => a.is_processed && !a.is_extracted)
                    .map((a) => a.id)
                  if (unextractedArtifactIds.length > 0) {
                    extractionMutation.mutate(unextractedArtifactIds)
                  }
                }}
                disabled={
                  extractionMutation.isPending ||
                  !artifactsData.artifacts.some((a) => a.is_processed && !a.is_extracted)
                }
                className="btn-primary text-sm disabled:opacity-50"
              >
                {extractionMutation.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Extracting Facts...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Extract New
                  </>
                )}
              </button>
            </div>
          </div>
          <ul className="divide-y divide-gray-200">
            {artifactsData.artifacts.map((artifact) => (
              <li key={artifact.id} className="px-5 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileText className="h-8 w-8 text-gray-400" />
                  <div>
                    <p className="font-medium text-gray-900">{artifact.display_name || artifact.filename}</p>
                    <p className="text-sm text-gray-500">
                      {artifact.artifact_type.toUpperCase()} &middot;{' '}
                      {new Date(artifact.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {artifact.is_extracted ? (
                    <span className="inline-flex items-center gap-1 text-sm text-green-600">
                      <CheckCircle className="h-4 w-4" />
                      Extracted
                    </span>
                  ) : artifact.is_processed ? (
                    <span className="inline-flex items-center gap-1 text-sm text-blue-600">
                      <Clock className="h-4 w-4" />
                      Ready ({artifact.chunk_count} chunks)
                    </span>
                  ) : (
                    <button
                      onClick={() => processMutation.mutate(artifact.id)}
                      disabled={processMutation.isPending}
                      className="btn-secondary text-sm"
                    >
                      <Play className="h-4 w-4 mr-1" />
                      Process
                    </button>
                  )}

                  {/* Artifact Actions Menu */}
                  <div className="relative">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        setOpenMenuId(openMenuId === artifact.id ? null : artifact.id)
                      }}
                      className="p-1 rounded hover:bg-gray-100"
                    >
                      <MoreVertical className="h-5 w-5 text-gray-400" />
                    </button>

                    {openMenuId === artifact.id && (
                      <>
                        {/* Backdrop to capture outside clicks */}
                        <div
                          className="fixed inset-0 z-40"
                          onClick={() => setOpenMenuId(null)}
                        />
                        <div className="absolute right-0 z-50 mt-1 w-48 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
                          <div className="py-1">
                            {artifact.is_extracted && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  resetExtractionMutation.mutate(artifact.id)
                                }}
                                disabled={resetExtractionMutation.isPending}
                                className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer"
                              >
                                <RotateCcw className="h-4 w-4 mr-2" />
                                Reset Extraction
                              </button>
                            )}
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                if (confirm(`Delete "${artifact.display_name}"? This cannot be undone.`)) {
                                  deleteMutation.mutate(artifact.id)
                                }
                              }}
                              disabled={deleteMutation.isPending}
                              className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 cursor-pointer"
                            >
                              <Trash2 className="h-4 w-4 mr-2" />
                              Delete
                            </button>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Extraction Status */}
      {extractionJobs && extractionJobs.jobs.length > 0 && (
        <div className="card">
          <div className="border-b border-gray-200 px-5 py-4">
            <h2 className="text-lg font-medium text-gray-900">
              Extraction Jobs ({extractionJobs.total})
            </h2>
          </div>
          <ul className="divide-y divide-gray-200">
            {extractionJobs.jobs.slice(0, 5).map((job) => (
              <li key={job.id} className="px-5 py-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Zap className={`h-5 w-5 ${job.status === 'completed' ? 'text-green-500' : job.status === 'failed' ? 'text-red-500' : 'text-yellow-500'}`} />
                  <div>
                    <p className="font-medium text-gray-900">
                      {job.status === 'completed' ? `Extracted ${job.facts_extracted} facts` : job.status}
                    </p>
                    <p className="text-sm text-gray-500">
                      {new Date(job.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  job.status === 'completed' ? 'bg-green-100 text-green-800' :
                  job.status === 'failed' ? 'bg-red-100 text-red-800' :
                  job.status === 'running' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {job.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Project Status Summary */}
      <div className="card">
        <div className="border-b border-gray-200 px-5 py-4">
          <h2 className="text-lg font-medium text-gray-900">Project Status</h2>
        </div>
        <div className="p-5 space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Documents uploaded</span>
            <span className="font-medium text-gray-900">{project.artifact_count}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Facts collected</span>
            <span className="font-medium text-gray-900">{project.fact_count}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Facts approved</span>
            <span className="font-medium text-gray-900">
              {project.approved_fact_count}
              {project.fact_count > 0 && (
                <span className="text-gray-400 ml-1">
                  ({Math.round((project.approved_fact_count / project.fact_count) * 100)}%)
                </span>
              )}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Readiness score</span>
            <span className="font-medium text-gray-900">
              {project.overall_readiness_score != null
                ? `${project.overall_readiness_score.toFixed(1)}/10`
                : 'Not calculated'}
            </span>
          </div>
          <div className="pt-2 border-t border-gray-100 flex items-center gap-3 text-xs text-gray-400">
            <Clock className="h-3.5 w-3.5" />
            <span>
              Last updated{' '}
              {new Date(project.updated_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
