import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ClipboardList,
  RefreshCw,
  AlertCircle,
  Clock,
  CheckCircle,
  XCircle,
  User,
  Calendar,
  AlertTriangle,
} from 'lucide-react'
import { api } from '../services/api'
import { ApiError } from '../services/generatedApi'
import type {
  InformationRequest,
  RequestStatus,
  RequestPriority,
} from '../types'

const statusColors: Record<RequestStatus, string> = {
  open: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  submitted: 'bg-purple-100 text-purple-800',
  resolved: 'bg-green-100 text-green-800',
  deferred: 'bg-gray-100 text-gray-800',
}

const priorityColors: Record<RequestPriority, string> = {
  low: 'bg-gray-100 text-gray-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
}

const statusIcons: Record<RequestStatus, React.ReactNode> = {
  open: <AlertCircle className="h-4 w-4" />,
  in_progress: <Clock className="h-4 w-4" />,
  submitted: <ClipboardList className="h-4 w-4" />,
  resolved: <CheckCircle className="h-4 w-4" />,
  deferred: <XCircle className="h-4 w-4" />,
}

const getErrorMessage = (error: unknown): string => {
  if (error instanceof ApiError) {
    const bodyDetail =
      error.body &&
      typeof error.body === 'object' &&
      'detail' in error.body &&
      typeof error.body.detail === 'string'
        ? error.body.detail
        : null
    if (bodyDetail && bodyDetail.trim()) {
      return bodyDetail
    }
    return `Request failed (${error.status}).`
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return 'Request failed. Check API connectivity and auth token configuration.'
}

export default function InformationRequests() {
  const { projectId } = useParams<{ projectId: string }>()
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<RequestStatus | ''>('')
  const [priorityFilter, setPriorityFilter] = useState<RequestPriority | ''>('')
  const [selectedRequest, setSelectedRequest] = useState<InformationRequest | null>(null)
  const [statusBanner, setStatusBanner] = useState<{
    tone: 'success' | 'error'
    message: string
  } | null>(null)

  const { data: report, isLoading: isReportLoading, error: reportError } = useQuery({
    queryKey: ['information-requests-report', projectId],
    queryFn: () => api.getInformationRequestReport(projectId!),
    enabled: !!projectId,
  })

  const {
    data: requestsList,
    isLoading: isRequestsLoading,
    error: requestsError,
  } = useQuery({
    queryKey: ['information-requests', projectId, statusFilter, priorityFilter],
    queryFn: () =>
      api.listInformationRequests({
        project_id: projectId!,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
        limit: 100,
      }),
    enabled: !!projectId,
  })

  const {
    data: overdueRequests,
    isLoading: isOverdueLoading,
    error: overdueError,
  } = useQuery({
    queryKey: ['overdue-requests', projectId],
    queryFn: () => api.getOverdueRequests(projectId!),
    enabled: !!projectId,
  })

  const generateMutation = useMutation({
    mutationFn: () => api.generateInformationRequests(projectId!, false),
    onMutate: () => {
      setStatusBanner(null)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['information-requests-report', projectId] })
      queryClient.invalidateQueries({ queryKey: ['information-requests', projectId] })
      queryClient.invalidateQueries({ queryKey: ['overdue-requests', projectId] })
      setStatusBanner({
        tone: 'success',
        message:
          result.requests_created > 0
            ? `Generated ${result.requests_created} request(s).`
            : 'No new requests generated. Existing requests may already cover current gaps.',
      })
    },
  })

  const acknowledgeMutation = useMutation({
    mutationFn: (requestId: string) => api.acknowledgeInformationRequest(requestId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['information-requests', projectId] })
      queryClient.invalidateQueries({ queryKey: ['information-requests-report', projectId] })
    },
  })

  const fetchRequestDetail = async (requestId: string) => {
    try {
      const request = await api.getInformationRequest(requestId)
      setSelectedRequest(request)
    } catch (error) {
      setStatusBanner({
        tone: 'error',
        message: getErrorMessage(error),
      })
    }
  }

  const pageError = reportError ?? requestsError ?? overdueError
  const isLoading = isReportLoading || isRequestsLoading || isOverdueLoading

  if (!projectId) {
    return (
      <div className="card p-6 border border-red-200 bg-red-50 text-red-700">
        Missing project context. Open this page from a project workspace.
      </div>
    )
  }

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading requests...</div>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Information Requests</h1>
          <p className="mt-1 text-sm text-gray-500">
            WP8 - Actionable requests for missing evidence
          </p>
        </div>
        <button
          className="btn btn-primary flex items-center gap-2"
          onClick={() => generateMutation.mutate()}
          disabled={!projectId || generateMutation.isPending}
        >
          <RefreshCw className={`h-4 w-4 ${generateMutation.isPending ? 'animate-spin' : ''}`} />
          {generateMutation.isPending ? 'Generating...' : 'Generate Requests'}
        </button>
      </div>

      {pageError ? (
        <div className="card p-4 border border-red-200 bg-red-50 text-red-700">
          {getErrorMessage(pageError)}
        </div>
      ) : null}

      {generateMutation.error ? (
        <div className="card p-4 border border-red-200 bg-red-50 text-red-700">
          {getErrorMessage(generateMutation.error)}
        </div>
      ) : null}

      {acknowledgeMutation.error ? (
        <div className="card p-4 border border-red-200 bg-red-50 text-red-700">
          {getErrorMessage(acknowledgeMutation.error)}
        </div>
      ) : null}

      {statusBanner ? (
        <div
          className={`card p-4 ${
            statusBanner.tone === 'success'
              ? 'border border-blue-200 bg-blue-50 text-blue-800'
              : 'border border-red-200 bg-red-50 text-red-700'
          }`}
        >
          {statusBanner.message}
        </div>
      ) : null}

      {/* Status Overview */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="card p-5">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-2xl font-bold">{report?.by_status?.open ?? 0}</p>
              <p className="text-sm text-gray-500">Open</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3">
            <Clock className="h-8 w-8 text-yellow-500" />
            <div>
              <p className="text-2xl font-bold">{report?.by_status?.in_progress ?? 0}</p>
              <p className="text-sm text-gray-500">In Progress</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3">
            <ClipboardList className="h-8 w-8 text-purple-500" />
            <div>
              <p className="text-2xl font-bold">{report?.by_status?.submitted ?? 0}</p>
              <p className="text-sm text-gray-500">Submitted</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3">
            <CheckCircle className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-2xl font-bold">{report?.by_status?.resolved ?? 0}</p>
              <p className="text-sm text-gray-500">Resolved</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <div>
              <p className="text-2xl font-bold">{report?.overdue_count ?? 0}</p>
              <p className="text-sm text-gray-500">Overdue</p>
            </div>
          </div>
        </div>
      </div>

      {/* Priority Breakdown */}
      <div className="card p-5">
        <h3 className="text-sm font-medium text-gray-700 mb-3">By Priority</h3>
        <div className="flex gap-4">
          {(['critical', 'high', 'medium', 'low'] as RequestPriority[]).map((priority) => (
            <div key={priority} className="flex items-center gap-2">
              <span className={`badge ${priorityColors[priority]}`}>
                {priority.toUpperCase()}
              </span>
              <span className="font-medium">{report?.by_priority?.[priority] ?? 0}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Overdue Requests Alert */}
      {overdueRequests && overdueRequests.length > 0 && (
        <div className="card border-red-200 bg-red-50">
          <div className="px-5 py-4">
            <h2 className="text-lg font-medium text-red-800 flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Overdue Requests ({overdueRequests.length})
            </h2>
          </div>
          <ul className="divide-y divide-red-200">
            {overdueRequests.slice(0, 5).map((req) => (
              <li
                key={req.id}
                className="px-5 py-3 flex items-center justify-between cursor-pointer hover:bg-red-100"
                onClick={() => fetchRequestDetail(req.id)}
              >
                <div>
                  <span className="font-medium text-red-900">{req.request_code}</span>
                  <span className="ml-2 text-red-700">{req.title}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-red-600">
                    {req.days_overdue} days overdue
                  </span>
                  <span className={`badge ${priorityColors[req.priority]}`}>
                    {req.priority}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-4">
        <select
          className="input"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as RequestStatus | '')}
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="submitted">Submitted</option>
          <option value="resolved">Resolved</option>
          <option value="deferred">Deferred</option>
        </select>
        <select
          className="input"
          value={priorityFilter}
          onChange={(e) => setPriorityFilter(e.target.value as RequestPriority | '')}
        >
          <option value="">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Requests List */}
      <div className="card">
        <div className="border-b border-gray-200 px-5 py-4">
          <h2 className="text-lg font-medium text-gray-900">
            All Requests ({requestsList?.total ?? 0})
          </h2>
        </div>
        {requestsList?.requests && requestsList.requests.length > 0 ? (
          <ul className="divide-y divide-gray-200">
            {requestsList.requests.map((req) => (
              <li
                key={req.id}
                className="px-5 py-4 cursor-pointer hover:bg-gray-50"
                onClick={() => fetchRequestDetail(req.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`badge ${statusColors[req.status]}`}>
                      {statusIcons[req.status]}
                      <span className="ml-1">{req.status.replace('_', ' ')}</span>
                    </span>
                    <span className={`badge ${priorityColors[req.priority]}`}>
                      {req.priority}
                    </span>
                    <span className="font-mono text-sm text-gray-600">
                      {req.request_code}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    {req.suggested_owner && (
                      <span className="flex items-center gap-1">
                        <User className="h-4 w-4" />
                        {req.suggested_owner}
                      </span>
                    )}
                    {req.target_date && (
                      <span className="flex items-center gap-1">
                        <Calendar className="h-4 w-4" />
                        {new Date(req.target_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                </div>
                <p className="mt-2 text-gray-900">{req.title}</p>
                {req.is_overdue && (
                  <p className="mt-1 text-sm text-red-600">
                    {req.days_overdue} days overdue
                  </p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <div className="p-12 text-center">
            <ClipboardList className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">
              No Information Requests
            </h3>
            <p className="mt-2 text-sm text-gray-500">
              Generate requests to create actionable items for missing evidence.
            </p>
          </div>
        )}
      </div>

      {/* Request Detail Modal */}
      {selectedRequest && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div
            className="fixed inset-0 bg-gray-500 bg-opacity-75"
            onClick={() => setSelectedRequest(null)}
          />
          <div className="relative min-h-screen flex items-center justify-center p-4">
            <div className="relative bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-mono text-sm text-gray-500">
                      {selectedRequest.request_code}
                    </span>
                    <h2 className="text-xl font-bold text-gray-900 mt-1">
                      {selectedRequest.title}
                    </h2>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`badge ${statusColors[selectedRequest.status]}`}>
                      {selectedRequest.status.replace('_', ' ')}
                    </span>
                    <span className={`badge ${priorityColors[selectedRequest.priority]}`}>
                      {selectedRequest.priority}
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-6 space-y-6">
                {/* Why It Matters */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Why This Matters
                  </h3>
                  <p className="text-gray-900">{selectedRequest.why_it_matters}</p>
                  <div className="mt-2 p-3 bg-yellow-50 rounded-lg">
                    <p className="text-sm text-yellow-800">
                      <strong>Consequences:</strong> {selectedRequest.consequences}
                    </p>
                  </div>
                </div>

                {/* Who Needs It */}
                {selectedRequest.who_needs_it.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">
                      Who Needs This Information
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedRequest.who_needs_it.map((who) => (
                        <span key={who} className="badge bg-blue-100 text-blue-800">
                          {who}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Guidance */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    How to Fill This Request
                  </h3>
                  <p className="text-gray-900">{selectedRequest.guidance_overview}</p>
                  {selectedRequest.specific_questions.length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm font-medium text-gray-600 mb-2">
                        Specific Questions to Answer:
                      </p>
                      <ul className="list-disc list-inside space-y-1 text-gray-700">
                        {selectedRequest.specific_questions.map((q, i) => (
                          <li key={i}>{q}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Acceptable Sources */}
                {selectedRequest.acceptable_sources.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-2">
                      Acceptable Sources
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {selectedRequest.acceptable_sources.map((source, i) => (
                        <span key={i} className="badge bg-gray-100 text-gray-800">
                          {source}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Missing Fact Paths */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">
                    Missing Data Points
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedRequest.missing_fact_paths.map((path) => (
                      <code key={path} className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {path}
                      </code>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t">
                  <button
                    className="btn btn-secondary"
                    onClick={() => setSelectedRequest(null)}
                  >
                    Close
                  </button>
                  {selectedRequest.status === 'open' && (
                    <button
                      className="btn btn-primary"
                      onClick={() => {
                        acknowledgeMutation.mutate(selectedRequest.id)
                        setSelectedRequest(null)
                      }}
                    >
                      Acknowledge & Start
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
