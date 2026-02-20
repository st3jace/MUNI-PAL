import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Filter,
  ChevronDown,
  Edit3,
  Info,
  HelpCircle,
  BookOpen,
  Users,
} from 'lucide-react'
import { api } from '../services/api'
import { ReviewStatus, type ExtractedFact } from '../types'

const statusConfig = {
  [ReviewStatus.PENDING]: {
    label: 'Pending',
    icon: Clock,
    badge: 'badge-pending',
  },
  [ReviewStatus.APPROVED]: {
    label: 'Approved',
    icon: CheckCircle,
    badge: 'badge-approved',
  },
  [ReviewStatus.REJECTED]: {
    label: 'Rejected',
    icon: XCircle,
    badge: 'badge-rejected',
  },
  [ReviewStatus.NEEDS_REVISION]: {
    label: 'Needs Revision',
    icon: AlertTriangle,
    badge: 'badge-needs-revision',
  },
}

export default function FactsReview() {
  const { projectId } = useParams<{ projectId: string }>()
  const [statusFilter, setStatusFilter] = useState<ReviewStatus | ''>('')
  const [selectedFact, setSelectedFact] = useState<ExtractedFact | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editedValue, setEditedValue] = useState('')
  const [reviewNote, setReviewNote] = useState('')
  const [showGuidance, setShowGuidance] = useState(false)
  const queryClient = useQueryClient()

  // Fetch schema path metadata when a fact is selected
  const { data: metadata } = useQuery({
    queryKey: ['schema-path-metadata', selectedFact?.schema_path],
    queryFn: () => api.getSchemaPathMetadata(selectedFact!.schema_path),
    enabled: !!selectedFact,
    staleTime: 1000 * 60 * 10, // Cache for 10 minutes
  })

  // Reset edit state when selecting a new fact
  useEffect(() => {
    if (selectedFact) {
      setEditedValue(String(selectedFact.value))
      setReviewNote(selectedFact.review_note || '')
      // Auto-enable editing for needs_revision facts
      setIsEditing(selectedFact.review_status === ReviewStatus.NEEDS_REVISION)
    } else {
      setIsEditing(false)
      setEditedValue('')
      setReviewNote('')
    }
  }, [selectedFact])

  const { data, isLoading } = useQuery({
    queryKey: ['facts', projectId, statusFilter],
    queryFn: () =>
      api.listFacts({
        project_id: projectId!,
        status: statusFilter || undefined,
      }),
    enabled: !!projectId,
  })

  const reviewMutation = useMutation({
    mutationFn: ({
      factId,
      action,
      note,
      correctedValue,
    }: {
      factId: string
      action: ReviewStatus
      note?: string
      correctedValue?: unknown
    }) =>
      api.reviewFact(factId, {
        action,
        note,
        corrected_value: correctedValue,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['facts', projectId] })
      setSelectedFact(null)
    },
  })

  const handleReview = (action: ReviewStatus) => {
    if (!selectedFact) return

    // Check if value was edited
    const originalValue = String(selectedFact.value)
    const valueChanged = editedValue !== originalValue

    reviewMutation.mutate({
      factId: selectedFact.id,
      action,
      note: reviewNote || undefined,
      correctedValue: valueChanged ? editedValue : undefined,
    })
  }

  const closeModal = () => {
    setSelectedFact(null)
    setIsEditing(false)
    setEditedValue('')
    setReviewNote('')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Facts Review</h1>
          <p className="mt-1 text-sm text-gray-500">
            Review and approve extracted facts
          </p>
        </div>

        {/* Filter */}
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ReviewStatus | '')}
            className="input py-1.5 pl-3 pr-8"
          >
            <option value="">All Status</option>
            <option value={ReviewStatus.PENDING}>Pending</option>
            <option value={ReviewStatus.APPROVED}>Approved</option>
            <option value={ReviewStatus.REJECTED}>Rejected</option>
            <option value={ReviewStatus.NEEDS_REVISION}>Needs Revision</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {Object.entries(statusConfig).map(([status, config]) => {
          const count =
            data?.facts.filter((f) => f.review_status === status).length ?? 0
          return (
            <button
              key={status}
              onClick={() =>
                setStatusFilter(statusFilter === status ? '' : (status as ReviewStatus))
              }
              className={`card p-4 text-left transition-colors ${
                statusFilter === status ? 'ring-2 ring-primary-500' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <config.icon className="h-5 w-5 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-500">{config.label}</p>
                  <p className="text-xl font-semibold">{count}</p>
                </div>
              </div>
            </button>
          )
        })}
      </div>

      {/* Facts Table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading facts...</div>
        ) : data?.facts.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No facts found matching the filter.
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Schema Path
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Criticality
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-6 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {data?.facts.map((fact) => {
                const config = statusConfig[fact.review_status as ReviewStatus]
                return (
                  <tr
                    key={fact.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => setSelectedFact(fact)}
                  >
                    <td className="px-6 py-4">
                      <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                        {fact.schema_path}
                      </code>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                      {String(fact.value)}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              fact.confidence_score >= 0.9
                                ? 'bg-green-500'
                                : fact.confidence_score >= 0.7
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                            style={{ width: `${fact.confidence_score * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-600">
                          {(fact.confidence_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`badge badge-${fact.criticality}`}>
                        {fact.criticality}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={config.badge}>{config.label}</span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <ChevronDown className="h-4 w-4 text-gray-400" />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Review Modal */}
      {selectedFact && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex min-h-screen items-center justify-center p-4">
            <div
              className="fixed inset-0 bg-gray-500 bg-opacity-75"
              onClick={closeModal}
            />
            <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-medium text-gray-900">
                  {selectedFact.review_status === ReviewStatus.NEEDS_REVISION
                    ? 'Edit & Re-review Fact'
                    : 'Review Fact'}
                </h2>
                {selectedFact.review_status === ReviewStatus.NEEDS_REVISION && (
                  <span className="badge bg-orange-100 text-orange-800">Needs Revision</span>
                )}
              </div>

              <dl className="space-y-4">
                <div>
                  <div className="flex items-center justify-between">
                    <dt className="text-sm text-gray-500">Schema Path</dt>
                    <button
                      type="button"
                      onClick={() => setShowGuidance(!showGuidance)}
                      className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                    >
                      <HelpCircle className="h-4 w-4" />
                      {showGuidance ? 'Hide' : 'What is this?'}
                    </button>
                  </div>
                  <dd className="mt-1">
                    <code className="bg-gray-100 px-2 py-1 rounded">
                      {selectedFact.schema_path}
                    </code>
                  </dd>
                </div>

                {/* Guidance Panel */}
                {showGuidance && metadata && (
                  <div className="rounded-md border border-blue-200 bg-blue-50 p-4 space-y-3">
                    <div className="flex items-start gap-2">
                      <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-blue-900">What is this field?</h4>
                        <p className="text-sm text-blue-800 mt-1">{metadata.description}</p>
                      </div>
                    </div>

                    <div className="flex items-start gap-2">
                      <BookOpen className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="font-medium text-blue-900">What to look for</h4>
                        <p className="text-sm text-blue-800 mt-1">{metadata.guidance}</p>
                      </div>
                    </div>

                    {metadata.example && (
                      <div className="bg-white rounded p-3 border border-blue-200">
                        <span className="text-xs font-medium text-blue-700 uppercase tracking-wide">Example</span>
                        <p className="text-sm text-gray-900 mt-1 font-mono">
                          {typeof metadata.example === 'object'
                            ? JSON.stringify(metadata.example, null, 2)
                            : String(metadata.example)}
                        </p>
                      </div>
                    )}

                    {metadata.who_needs_it && metadata.who_needs_it.length > 0 && (
                      <div className="flex items-start gap-2">
                        <Users className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <h4 className="font-medium text-blue-900">Who needs this</h4>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {metadata.who_needs_it.map((who) => (
                              <span key={who} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                                {who}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div>
                  <div className="flex items-center justify-between">
                    <dt className="text-sm text-gray-500">Value</dt>
                    {!isEditing && selectedFact.review_status !== ReviewStatus.APPROVED && (
                      <button
                        onClick={() => setIsEditing(true)}
                        className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                      >
                        <Edit3 className="h-3 w-3" />
                        Edit
                      </button>
                    )}
                  </div>
                  {isEditing ? (
                    <div className="mt-1">
                      <input
                        type="text"
                        value={editedValue}
                        onChange={(e) => setEditedValue(e.target.value)}
                        className="input w-full"
                      />
                      {selectedFact.unit && (
                        <span className="text-sm text-gray-500 mt-1 block">
                          Unit: {selectedFact.unit}
                        </span>
                      )}
                      {editedValue !== String(selectedFact.value) && (
                        <p className="text-sm text-blue-600 mt-1">
                          Original: {String(selectedFact.value)}
                        </p>
                      )}
                    </div>
                  ) : (
                    <dd className="mt-1 font-medium text-gray-900">
                      {String(selectedFact.value)}
                      {selectedFact.unit && (
                        <span className="text-gray-500 ml-1">({selectedFact.unit})</span>
                      )}
                      {selectedFact.original_value !== undefined && selectedFact.original_value !== null && (
                        <p className="text-sm text-gray-500 mt-1">
                          Original AI extraction: {String(selectedFact.original_value)}
                        </p>
                      )}
                    </dd>
                  )}
                </div>

                <div>
                  <dt className="text-sm text-gray-500">Confidence</dt>
                  <dd className="mt-1">
                    {(selectedFact.confidence_score * 100).toFixed(0)}%
                    {selectedFact.confidence_rationale && (
                      <p className="text-sm text-gray-500 mt-1">
                        {selectedFact.confidence_rationale}
                      </p>
                    )}
                  </dd>
                </div>

                {selectedFact.review_note && selectedFact.review_status === ReviewStatus.NEEDS_REVISION && (
                  <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                    <dt className="text-sm font-medium text-orange-800">Previous Review Note</dt>
                    <dd className="mt-1 text-sm text-orange-700">
                      {selectedFact.review_note}
                    </dd>
                  </div>
                )}

                <div>
                  <dt className="text-sm text-gray-500">
                    {selectedFact.review_status === ReviewStatus.NEEDS_REVISION
                      ? 'Update Note'
                      : 'Review Note (optional)'}
                  </dt>
                  <textarea
                    value={reviewNote}
                    onChange={(e) => setReviewNote(e.target.value)}
                    rows={3}
                    className="mt-1 input w-full"
                    placeholder={
                      selectedFact.review_status === ReviewStatus.NEEDS_REVISION
                        ? 'Describe the changes made...'
                        : 'Add a note about this review...'
                    }
                  />
                </div>
              </dl>

              <div className="mt-6 flex justify-end gap-3">
                <button onClick={closeModal} className="btn-secondary">
                  Cancel
                </button>
                {selectedFact.review_status !== ReviewStatus.REJECTED && (
                  <button
                    onClick={() => handleReview(ReviewStatus.REJECTED)}
                    disabled={reviewMutation.isPending}
                    className="btn-danger"
                  >
                    Reject
                  </button>
                )}
                {selectedFact.review_status !== ReviewStatus.NEEDS_REVISION && (
                  <button
                    onClick={() => handleReview(ReviewStatus.NEEDS_REVISION)}
                    disabled={reviewMutation.isPending}
                    className="btn bg-orange-600 text-white hover:bg-orange-700"
                  >
                    Needs Revision
                  </button>
                )}
                <button
                  onClick={() => handleReview(ReviewStatus.APPROVED)}
                  disabled={reviewMutation.isPending}
                  className="btn-success"
                >
                  {editedValue !== String(selectedFact.value)
                    ? 'Approve with Changes'
                    : 'Approve'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
