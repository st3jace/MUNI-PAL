import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText,
  Package,
  RefreshCw,
  Download,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  XCircle,
  ExternalLink,
  Building,
  Calendar,
  Shield,
} from 'lucide-react'
import { api } from '../services/api'

type TabType = 'internal' | 'external'

// Helper function to trigger file download from content
const downloadContent = (content: string, filename: string, mimeType: string = 'text/markdown') => {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default function AdvisoryPackages() {
  const { projectId } = useParams<{ projectId: string }>()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<TabType>('internal')
  const [showExternalForm, setShowExternalForm] = useState(false)
  const [externalFormData, setExternalFormData] = useState({
    title: '',
    generated_for: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [exportLoading, setExportLoading] = useState<string | null>(null)

  // Internal Report Queries
  const { data: internalReport, isLoading: loadingInternal } = useQuery({
    queryKey: ['internal-report-latest', projectId],
    queryFn: () => api.getLatestInternalReport(projectId!),
    enabled: !!projectId && activeTab === 'internal',
  })

  const { data: internalReports } = useQuery({
    queryKey: ['internal-reports', projectId],
    queryFn: () => api.listInternalReports(projectId!),
    enabled: !!projectId && activeTab === 'internal',
  })

  // External Package Queries
  const { data: externalPackage, isLoading: loadingExternal } = useQuery({
    queryKey: ['external-package-latest', projectId],
    queryFn: () => api.getLatestExternalPackage(projectId!),
    enabled: !!projectId && activeTab === 'external',
  })

  const { data: externalPackages } = useQuery({
    queryKey: ['external-packages', projectId],
    queryFn: () => api.listExternalPackages(projectId!),
    enabled: !!projectId && activeTab === 'external',
  })

  const {
    data: riskIntegration,
    isLoading: loadingRiskIntegration,
    isError: riskIntegrationError,
  } = useQuery({
    queryKey: ['risk-bfms-integration', projectId],
    queryFn: () => api.getRiskBfmsIntegration(projectId!),
    enabled: !!projectId && activeTab === 'external',
  })

  const { data: validation } = useQuery({
    queryKey: ['external-package-validation', externalPackage?.id],
    queryFn: () => api.validateExternalPackage(externalPackage!.id),
    enabled: !!externalPackage?.id,
  })

  // Mutations
  const generateInternalMutation = useMutation({
    mutationFn: () => api.generateInternalReport(projectId!),
    onSuccess: () => {
      setError(null)
      queryClient.invalidateQueries({ queryKey: ['internal-report-latest', projectId] })
      queryClient.invalidateQueries({ queryKey: ['internal-reports', projectId] })
    },
    onError: (err: unknown) => {
      console.error('Internal report generation failed:', err)
      let errorMessage = 'Failed to generate internal report'
      if (err && typeof err === 'object') {
        const axiosError = err as { response?: { data?: { detail?: string } }; message?: string }
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail
        } else if (axiosError.message) {
          errorMessage = axiosError.message
        }
      }
      setError(errorMessage)
    },
  })

  const generateExternalMutation = useMutation({
    mutationFn: () =>
      api.generateExternalPackage(
        projectId!,
        externalFormData.title || 'Advisory Package',
        externalFormData.generated_for || 'Municipal Advisor'
      ),
    onSuccess: () => {
      setError(null)
      queryClient.invalidateQueries({ queryKey: ['external-package-latest', projectId] })
      queryClient.invalidateQueries({ queryKey: ['external-packages', projectId] })
      setShowExternalForm(false)
      setExternalFormData({ title: '', generated_for: '' })
    },
    onError: (err: unknown) => {
      console.error('External package generation failed:', err)
      let errorMessage = 'Failed to generate external package'
      if (err && typeof err === 'object') {
        const axiosError = err as { response?: { data?: { detail?: string } }; message?: string }
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail
        } else if (axiosError.message) {
          errorMessage = axiosError.message
        }
      }
      setError(errorMessage)
    },
  })

  // Export handlers
  const handleExportInternalReport = async (format: 'md' | 'pdf' | 'html') => {
    if (!internalReport) return
    setExportLoading(`internal-${format}`)
    try {
      const result = await api.exportInternalReport(internalReport.id, format)
      if (result.content) {
        const mimeTypes: Record<string, string> = {
          md: 'text/markdown',
          html: 'text/html',
          pdf: 'application/pdf',
        }
        downloadContent(result.content, result.filename || `internal_report.${format}`, mimeTypes[format])
      } else if (format !== 'md') {
        setError(`Export format '${format}' is not yet implemented on the server`)
      }
    } catch (err: unknown) {
      console.error('Export failed:', err)
      let errorMessage = `Failed to export ${format.toUpperCase()}`
      if (err && typeof err === 'object') {
        const axiosError = err as { response?: { data?: { detail?: string } }; message?: string }
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail
        }
      }
      setError(errorMessage)
    } finally {
      setExportLoading(null)
    }
  }

  const handleExportExternalPackage = async (format: 'md' | 'pdf' | 'docx') => {
    if (!externalPackage) return
    setExportLoading(`external-${format}`)
    try {
      const result = await api.exportExternalPackage(externalPackage.id, format)
      if (result.content) {
        const mimeTypes: Record<string, string> = {
          md: 'text/markdown',
          pdf: 'application/pdf',
          docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        }
        downloadContent(result.content, result.filename || `advisory_package.${format}`, mimeTypes[format])
      } else if (format !== 'md') {
        setError(`Export format '${format}' is not yet implemented on the server`)
      }
    } catch (err: unknown) {
      console.error('Export failed:', err)
      let errorMessage = `Failed to export ${format.toUpperCase()}`
      if (err && typeof err === 'object') {
        const axiosError = err as { response?: { data?: { detail?: string } }; message?: string }
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail
        }
      }
      setError(errorMessage)
    } finally {
      setExportLoading(null)
    }
  }

  const isLoading = activeTab === 'internal' ? loadingInternal : loadingExternal

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Advisory Packages</h1>
          <p className="mt-1 text-sm text-gray-500">
            Bifurcated deliverables for internal and external audiences
          </p>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="card p-4 border-red-200 bg-red-50">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
            <div>
              <p className="font-medium text-red-800">Error</p>
              <p className="text-sm text-red-600">{error}</p>
            </div>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-600"
            >
              &times;
            </button>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'internal'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('internal')}
          >
            <Building className="h-4 w-4 inline mr-2" />
            Internal Readiness Report
          </button>
          <button
            className={`py-4 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'external'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
            onClick={() => setActiveTab('external')}
          >
            <ExternalLink className="h-4 w-4 inline mr-2" />
            External Advisory Package
          </button>
        </nav>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : activeTab === 'internal' ? (
        /* Internal Readiness Report Tab */
        <div className="space-y-6">
          <div className="flex justify-end">
            <button
              className="btn btn-primary flex items-center gap-2"
              onClick={() => generateInternalMutation.mutate()}
              disabled={generateInternalMutation.isPending}
            >
              <RefreshCw
                className={`h-4 w-4 ${generateInternalMutation.isPending ? 'animate-spin' : ''}`}
              />
              {internalReport ? 'Regenerate Report' : 'Generate Report'}
            </button>
          </div>

          {internalReport ? (
            <>
              {/* Score Overview */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="card p-5">
                  <div className="flex items-center gap-3">
                    <div
                      className={`h-12 w-12 rounded-full flex items-center justify-center text-xl font-bold ${
                        (internalReport.overall_score ?? 0) >= 7.5
                          ? 'bg-green-100 text-green-600'
                          : (internalReport.overall_score ?? 0) >= 5.5
                          ? 'bg-blue-100 text-blue-600'
                          : (internalReport.overall_score ?? 0) >= 3.0
                          ? 'bg-yellow-100 text-yellow-600'
                          : 'bg-red-100 text-red-600'
                      }`}
                    >
                      {internalReport.overall_score?.toFixed(1) ?? '—'}
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Overall Score</p>
                      <p className="text-lg font-medium">out of 10</p>
                    </div>
                  </div>
                </div>
                <div className="card p-5">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-8 w-8 text-red-500" />
                    <div>
                      <p className="text-2xl font-bold">{internalReport.critical_gap_count}</p>
                      <p className="text-sm text-gray-500">Critical Gaps</p>
                    </div>
                  </div>
                </div>
                <div className="card p-5">
                  <div className="flex items-center gap-3">
                    <FileText className="h-8 w-8 text-blue-500" />
                    <div>
                      <p className="text-2xl font-bold">{internalReport.open_request_count}</p>
                      <p className="text-sm text-gray-500">Open Requests</p>
                    </div>
                  </div>
                </div>
                <div className="card p-5">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-8 w-8 text-green-500" />
                    <div>
                      <p className="text-2xl font-bold">{internalReport.facts_count}</p>
                      <p className="text-sm text-gray-500">Facts Collected</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Executive Summary */}
              {internalReport.executive_summary && (
                <div className="card">
                  <div className="border-b border-gray-200 px-5 py-4">
                    <h2 className="text-lg font-medium text-gray-900">Executive Summary</h2>
                  </div>
                  <div className="p-5 space-y-4">
                    <div className="flex items-center gap-4">
                      <span className="text-gray-600">Score Interpretation:</span>
                      <span className="font-medium">
                        {internalReport.executive_summary.score_interpretation}
                      </span>
                    </div>
                    {internalReport.executive_summary.critical_blockers?.length > 0 && (
                      <div>
                        <h3 className="text-sm font-medium text-red-700 mb-2">
                          Critical Blockers
                        </h3>
                        <ul className="space-y-2">
                          {internalReport.executive_summary.critical_blockers.map(
                            (blocker, i) => (
                              <li key={i} className="p-3 bg-red-50 rounded-lg">
                                <p className="font-medium text-red-900">{blocker.title}</p>
                                <p className="text-sm text-red-700 mt-1">{blocker.summary}</p>
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Export Options */}
              <div className="card p-5">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Export Report</h3>
                <div className="flex gap-3">
                  <button
                    className="btn btn-secondary flex items-center gap-2"
                    onClick={() => handleExportInternalReport('md')}
                    disabled={exportLoading === 'internal-md'}
                  >
                    <Download className={`h-4 w-4 ${exportLoading === 'internal-md' ? 'animate-pulse' : ''}`} />
                    Markdown
                  </button>
                  <button
                    className="btn btn-secondary flex items-center gap-2"
                    onClick={() => handleExportInternalReport('pdf')}
                    disabled={exportLoading === 'internal-pdf'}
                  >
                    <Download className={`h-4 w-4 ${exportLoading === 'internal-pdf' ? 'animate-pulse' : ''}`} />
                    PDF
                  </button>
                  <button
                    className="btn btn-secondary flex items-center gap-2"
                    onClick={() => handleExportInternalReport('html')}
                    disabled={exportLoading === 'internal-html'}
                  >
                    <Download className={`h-4 w-4 ${exportLoading === 'internal-html' ? 'animate-pulse' : ''}`} />
                    HTML
                  </button>
                </div>
              </div>

              {/* Version History */}
              {internalReports && internalReports.reports.length > 1 && (
                <div className="card">
                  <div className="border-b border-gray-200 px-5 py-4">
                    <h2 className="text-lg font-medium text-gray-900">Report History</h2>
                  </div>
                  <ul className="divide-y divide-gray-200">
                    {internalReports.reports.map((report) => (
                      <li
                        key={report.id}
                        className="px-5 py-4 flex items-center justify-between"
                      >
                        <div>
                          <span className="font-medium">Version {report.version}</span>
                          <span className="ml-2 text-sm text-gray-500">
                            {new Date(report.created_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-sm">
                            Score: {report.overall_score?.toFixed(1) ?? '—'}
                          </span>
                          <span className="text-sm text-gray-500">
                            {report.critical_gap_count} critical gaps
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <div className="card p-12 text-center">
              <Building className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                No Internal Report Yet
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Generate an internal readiness report for your sponsor team.
              </p>
              <button
                className="mt-6 btn btn-primary"
                onClick={() => generateInternalMutation.mutate()}
                disabled={generateInternalMutation.isPending}
              >
                Generate Internal Report
              </button>
            </div>
          )}
        </div>
      ) : (
        /* External Advisory Package Tab */
        <div className="space-y-6">
          <div className="flex justify-end">
            <button
              className="btn btn-primary flex items-center gap-2"
              onClick={() => setShowExternalForm(true)}
            >
              <Package className="h-4 w-4" />
              Create Package
            </button>
          </div>

          {loadingRiskIntegration ? (
            <div className="card border border-gray-200 bg-gray-50 p-5">
              <p className="text-sm text-gray-600">Loading BFMS risk integration status...</p>
            </div>
          ) : riskIntegration ? (
            <div
              className={`card border p-5 ${
                riskIntegration.integration_mode === 'fallback'
                  ? 'border-yellow-200 bg-yellow-50'
                  : 'border-green-200 bg-green-50'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-base font-semibold text-gray-900">
                    BFMS Risk Integration Input:{' '}
                    {riskIntegration.integration_mode === 'fallback'
                      ? 'Fallback Mode'
                      : 'Full Mode'}
                  </h2>
                  <p className="mt-1 text-sm text-gray-600">
                    Contract `{riskIntegration.contract_version}` | Posture score{' '}
                    {riskIntegration.overall_posture_score.toFixed(3)} | Reliability-low dimensions{' '}
                    {riskIntegration.reliability_low_dimensions}
                  </p>
                </div>
                <span
                  className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${
                    riskIntegration.directional_guidance_only
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-green-100 text-green-800'
                  }`}
                >
                  {riskIntegration.directional_guidance_only
                    ? 'Directional Guidance'
                    : 'Execution Grade'}
                </span>
              </div>

              <p
                className={`mt-3 text-sm ${
                  riskIntegration.integration_mode === 'fallback'
                    ? 'text-yellow-800'
                    : 'text-green-800'
                }`}
              >
                {riskIntegration.integration_mode === 'fallback'
                  ? 'Risk outputs are directional for advisory decisioning until reliability improves.'
                  : 'Risk outputs are stable for advisory decisioning and package generation.'}
              </p>

              {(riskIntegration.fallback_reasons ?? []).length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-yellow-900">Fallback Reasons</p>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-yellow-800">
                    {(riskIntegration.fallback_reasons ?? []).map((reason: string, index: number) => (
                      <li key={`risk-fallback-${index}`}>{reason}</li>
                    ))}
                  </ul>
                </div>
              )}

              {(riskIntegration.advisory_next_steps ?? []).length > 0 && (
                <div className="mt-4">
                  <p className="text-sm font-medium text-gray-900">Top Risk Next Steps</p>
                  <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-gray-700">
                    {(riskIntegration.advisory_next_steps ?? []).slice(0, 3).map((step) => (
                      <li key={step.action_id}>
                        [{step.priority}] {step.title} ({step.owner}, target {step.target_date_hint})
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          ) : (
            <div
              className={`card border p-5 ${
                riskIntegrationError
                  ? 'border-red-200 bg-red-50'
                  : 'border-gray-200 bg-gray-50'
              }`}
            >
              <p
                className={`text-sm font-medium ${
                  riskIntegrationError ? 'text-red-800' : 'text-gray-900'
                }`}
              >
                BFMS Risk Integration Input unavailable
              </p>
              <p
                className={`mt-1 text-sm ${
                  riskIntegrationError ? 'text-red-700' : 'text-gray-600'
                }`}
              >
                {riskIntegrationError
                  ? 'Risk integration request failed. External package workflows remain available.'
                  : 'Risk integration contract is not enabled for this environment. External package workflows remain available.'}
              </p>
            </div>
          )}

          {externalPackage ? (
            <>
              {/* Distribution Status */}
              <div
                className={`card p-5 ${
                  externalPackage.ready_for_distribution
                    ? 'border-green-200 bg-green-50'
                    : 'border-yellow-200 bg-yellow-50'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {externalPackage.ready_for_distribution ? (
                      <Shield className="h-8 w-8 text-green-600" />
                    ) : (
                      <AlertTriangle className="h-8 w-8 text-yellow-600" />
                    )}
                    <div>
                      <p
                        className={`font-medium ${
                          externalPackage.ready_for_distribution
                            ? 'text-green-800'
                            : 'text-yellow-800'
                        }`}
                      >
                        {externalPackage.ready_for_distribution
                          ? 'Ready for Distribution'
                          : 'Not Ready for Distribution'}
                      </p>
                      <p
                        className={`text-sm ${
                          externalPackage.ready_for_distribution
                            ? 'text-green-600'
                            : 'text-yellow-600'
                        }`}
                      >
                        {externalPackage.ready_for_distribution
                          ? 'Package meets quality gates for external sharing'
                          : `${externalPackage.distribution_issues?.length ?? 0} issues to resolve`}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Generated for</p>
                    <p className="font-medium">{externalPackage.generated_for}</p>
                  </div>
                </div>
              </div>

              {/* Quality Metrics */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div className="card p-5">
                  <div className="flex items-center gap-3">
                    <CheckCircle className="h-8 w-8 text-blue-500" />
                    <div>
                      <p className="text-2xl font-bold">
                        {((externalPackage.disclosure_completeness_score ?? 0) * 100).toFixed(0)}%
                      </p>
                      <p className="text-sm text-gray-500">Disclosure Complete</p>
                    </div>
                  </div>
                </div>
                <div className="card p-5">
                  <div className="flex items-center gap-3">
                    <XCircle className="h-8 w-8 text-red-500" />
                    <div>
                      <p className="text-2xl font-bold">{externalPackage.critical_tbd_count}</p>
                      <p className="text-sm text-gray-500">Critical TBDs</p>
                    </div>
                  </div>
                </div>
                <div className="card p-5">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-8 w-8 text-yellow-500" />
                    <div>
                      <p className="text-2xl font-bold">{externalPackage.high_tbd_count}</p>
                      <p className="text-sm text-gray-500">High TBDs</p>
                    </div>
                  </div>
                </div>
                <div className="card p-5">
                  <div className="flex items-center gap-3">
                    <Calendar className="h-8 w-8 text-gray-500" />
                    <div>
                      <p className="text-2xl font-bold">v{externalPackage.version}</p>
                      <p className="text-sm text-gray-500">Version</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Validation Issues */}
              {validation && !validation.ready_for_distribution && (
                <div className="card border-red-200">
                  <div className="border-b border-red-200 px-5 py-4 bg-red-50">
                    <h2 className="text-lg font-medium text-red-800">
                      Distribution Issues ({validation.issues.length})
                    </h2>
                  </div>
                  <ul className="divide-y divide-red-200">
                    {validation.issues.map((issue, i) => (
                      <li key={i} className="px-5 py-3 flex items-center gap-3">
                        <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                        <span className="text-red-800">{issue}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Export Options */}
              <div className="card p-5">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Export Package</h3>
                <div className="flex gap-3">
                  <button
                    className="btn btn-primary flex items-center gap-2"
                    onClick={() => handleExportExternalPackage('pdf')}
                    disabled={exportLoading === 'external-pdf'}
                  >
                    <Download className={`h-4 w-4 ${exportLoading === 'external-pdf' ? 'animate-pulse' : ''}`} />
                    PDF (Primary)
                  </button>
                  <button
                    className="btn btn-secondary flex items-center gap-2"
                    onClick={() => handleExportExternalPackage('docx')}
                    disabled={exportLoading === 'external-docx'}
                  >
                    <Download className={`h-4 w-4 ${exportLoading === 'external-docx' ? 'animate-pulse' : ''}`} />
                    Word
                  </button>
                  <button
                    className="btn btn-secondary flex items-center gap-2"
                    onClick={() => handleExportExternalPackage('md')}
                    disabled={exportLoading === 'external-md'}
                  >
                    <Download className={`h-4 w-4 ${exportLoading === 'external-md' ? 'animate-pulse' : ''}`} />
                    Markdown
                  </button>
                </div>
              </div>

              {/* Package History */}
              {externalPackages && externalPackages.packages.length > 1 && (
                <div className="card">
                  <div className="border-b border-gray-200 px-5 py-4">
                    <h2 className="text-lg font-medium text-gray-900">Package History</h2>
                  </div>
                  <ul className="divide-y divide-gray-200">
                    {externalPackages.packages.map((pkg) => (
                      <li
                        key={pkg.id}
                        className="px-5 py-4 flex items-center justify-between"
                      >
                        <div>
                          <span className="font-medium">{pkg.title}</span>
                          <span className="ml-2 text-sm text-gray-500">
                            v{pkg.version} • {new Date(pkg.created_at).toLocaleString()}
                          </span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-sm text-gray-500">
                            For: {pkg.generated_for}
                          </span>
                          {pkg.ready_for_distribution ? (
                            <span className="badge bg-green-100 text-green-800">
                              Ready
                            </span>
                          ) : (
                            <span className="badge bg-yellow-100 text-yellow-800">
                              Not Ready
                            </span>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          ) : (
            <div className="card p-12 text-center">
              <Package className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">
                No External Package Yet
              </h3>
              <p className="mt-2 text-sm text-gray-500">
                Create an external advisory package for municipal advisors and other
                external parties.
              </p>
              <button
                className="mt-6 btn btn-primary"
                onClick={() => setShowExternalForm(true)}
              >
                Create External Package
              </button>
            </div>
          )}
        </div>
      )}

      {/* External Package Form Modal */}
      {showExternalForm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div
            className="fixed inset-0 bg-gray-500 bg-opacity-75"
            onClick={() => setShowExternalForm(false)}
          />
          <div className="relative min-h-screen flex items-center justify-center p-4">
            <div className="relative bg-white rounded-lg shadow-xl max-w-md w-full">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">
                  Create External Advisory Package
                </h2>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Package Title
                  </label>
                  <input
                    type="text"
                    className="input w-full"
                    placeholder="e.g., Bond Advisory Package"
                    value={externalFormData.title}
                    onChange={(e) =>
                      setExternalFormData((prev) => ({ ...prev, title: e.target.value }))
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Generated For
                  </label>
                  <input
                    type="text"
                    className="input w-full"
                    placeholder="e.g., XYZ Municipal Advisors"
                    value={externalFormData.generated_for}
                    onChange={(e) =>
                      setExternalFormData((prev) => ({
                        ...prev,
                        generated_for: e.target.value,
                      }))
                    }
                  />
                </div>
              </div>
              <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowExternalForm(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn btn-primary"
                  onClick={() => generateExternalMutation.mutate()}
                  disabled={generateExternalMutation.isPending}
                >
                  {generateExternalMutation.isPending ? 'Creating...' : 'Create Package'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
