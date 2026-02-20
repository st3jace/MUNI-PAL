import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Gauge,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  Info,
} from 'lucide-react'
import { api } from '../services/api'
import { ReadinessDimension } from '../types'

const dimensionNames: Record<ReadinessDimension, string> = {
  [ReadinessDimension.ISSUER_AUTHORITY]: 'Issuer Authority',
  [ReadinessDimension.PROJECT_TECH]: 'Project & Technology',
  [ReadinessDimension.REVENUE_FEEDSTOCK]: 'Revenue & Feedstock',
  [ReadinessDimension.CAB_FINANCIAL]: 'CAB Financial Structure',
  [ReadinessDimension.RISK_SECURITY_SLB]: 'Risk, Security & SLB',
  [ReadinessDimension.SLB_VERIFICATION]: 'SLB Verification',
}

const recommendationColors: Record<string, string> = {
  'Not Yet Viable': 'bg-red-100 text-red-800 border-red-200',
  'Structurally Viable': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  'Ready for Selective Engagement': 'bg-blue-100 text-blue-800 border-blue-200',
  'Ready for Broad Market': 'bg-green-100 text-green-800 border-green-200',
}

export default function Readiness() {
  const { projectId } = useParams<{ projectId: string }>()

  const { data: assessment, isLoading } = useQuery({
    queryKey: ['readiness', projectId],
    queryFn: () => api.getReadinessAssessment(projectId!),
    enabled: !!projectId,
  })

  const { data: gaps } = useQuery({
    queryKey: ['readiness-gaps', projectId],
    queryFn: () => api.getReadinessGaps(projectId!),
    enabled: !!projectId,
  })

  const { data: riskIntegration } = useQuery({
    queryKey: ['risk-bfms-integration', projectId],
    queryFn: () => api.getRiskBfmsIntegration(projectId!),
    enabled: !!projectId,
  })

  if (isLoading) {
    return <div className="text-center py-12 text-gray-500">Loading readiness...</div>
  }

  const scoreColor =
    (assessment?.overall_score ?? 0) >= 7.5
      ? 'text-green-600'
      : (assessment?.overall_score ?? 0) >= 5.5
      ? 'text-blue-600'
      : (assessment?.overall_score ?? 0) >= 3.0
      ? 'text-yellow-600'
      : 'text-red-600'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Readiness Assessment</h1>
        <p className="mt-1 text-sm text-gray-500">
          Bond issuance readiness scoring across 6 dimensions
        </p>
      </div>

      {riskIntegration && (
        <div
          className={`card p-5 border ${
            riskIntegration.integration_mode === 'fallback'
              ? 'border-yellow-200 bg-yellow-50'
              : 'border-green-200 bg-green-50'
          }`}
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              {riskIntegration.integration_mode === 'fallback' ? (
                <AlertTriangle className="mt-0.5 h-6 w-6 text-yellow-600" />
              ) : (
                <CheckCircle className="mt-0.5 h-6 w-6 text-green-600" />
              )}
              <div>
                <h2 className="text-base font-semibold text-gray-900">
                  BFMS Risk Integration: {riskIntegration.integration_mode === 'fallback' ? 'Fallback Mode' : 'Full Mode'}
                </h2>
                <p className="text-sm text-gray-600">
                  Contract `{riskIntegration.contract_version}` | Posture score{' '}
                  {riskIntegration.overall_posture_score.toFixed(3)}
                </p>
              </div>
            </div>
            <span
              className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${
                riskIntegration.directional_guidance_only
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-green-100 text-green-800'
              }`}
            >
              {riskIntegration.directional_guidance_only ? 'Directional Guidance' : 'Execution Grade'}
            </span>
          </div>

          {riskIntegration.integration_mode === 'fallback' &&
            (riskIntegration.fallback_reasons ?? []).length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-yellow-900">Fallback Reasons</p>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-yellow-800">
                  {(riskIntegration.fallback_reasons ?? []).map((reason: string, idx: number) => (
                    <li key={`fallback-reason-${idx}`}>{reason}</li>
                  ))}
                </ul>
              </div>
            )}

          {(riskIntegration.advisory_next_steps ?? []).length > 0 && (
            <div className="mt-4">
              <p className="text-sm font-medium text-gray-900">Top Risk Next Steps</p>
              <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-gray-700">
                {(riskIntegration.advisory_next_steps ?? []).slice(0, 3).map((step: {
                  action_id: string
                  priority: string
                  title: string
                  owner: string
                  target_date_hint: string
                }) => (
                  <li key={step.action_id}>
                    [{step.priority}] {step.title} ({step.owner}, target {step.target_date_hint})
                  </li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      {/* Overall Score */}
      <div className="card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Overall Score</h2>
            <p className="mt-1 text-sm text-gray-500">
              Weighted average across all dimensions
            </p>
          </div>
          <div className="text-right">
            <div className={`text-5xl font-bold ${scoreColor}`}>
              {assessment?.overall_score?.toFixed(1) ?? '—'}
              <span className="text-2xl text-gray-400">/10</span>
            </div>
          </div>
        </div>

        {assessment?.recommendation && (
          <div
            className={`mt-4 p-4 rounded-lg border ${
              recommendationColors[assessment.recommendation] ?? 'bg-gray-100'
            }`}
          >
            <div className="flex items-center gap-2">
              <Gauge className="h-5 w-5" />
              <span className="font-medium">{assessment.recommendation}</span>
            </div>
            {assessment.recommendation_rationale && (
              <p className="mt-2 text-sm opacity-80">
                {assessment.recommendation_rationale}
              </p>
            )}
          </div>
        )}
      </div>

      {/* Dimension Scores */}
      <div className="card">
        <div className="border-b border-gray-200 px-5 py-4">
          <h2 className="text-lg font-medium text-gray-900">Dimension Scores</h2>
        </div>
        <div className="p-5 space-y-6">
          {assessment?.dimensions &&
            Object.entries(assessment.dimensions).map(([dim, score]) => {
              const percentage = (score.score / score.max_score) * 100
              const barColor =
                percentage >= 80
                  ? 'bg-green-500'
                  : percentage >= 60
                  ? 'bg-blue-500'
                  : percentage >= 40
                  ? 'bg-yellow-500'
                  : 'bg-red-500'

              return (
                <div key={dim}>
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <span className="font-medium text-gray-900">
                        {dimensionNames[dim as ReadinessDimension] ?? dim}
                      </span>
                      <span className="ml-2 text-sm text-gray-500">
                        ({(score.weight * 100).toFixed(0)}% weight)
                      </span>
                    </div>
                    <span className="font-medium">
                      {score.score.toFixed(1)}/{score.max_score}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className={`${barColor} h-3 rounded-full transition-all`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  {score.explanation && (
                    <p className="mt-2 text-sm text-gray-500">{score.explanation}</p>
                  )}
                  {score.improvement_suggestions &&
                    score.improvement_suggestions.length > 0 && (
                      <div className="mt-2 text-sm">
                        <span className="text-gray-500">Suggestions: </span>
                        {score.improvement_suggestions.join('; ')}
                      </div>
                    )}
                </div>
              )
            })}
        </div>
      </div>

      {/* Evidence Summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-5">
          <div className="flex items-center gap-3">
            <CheckCircle className="h-8 w-8 text-green-500" />
            <div>
              <p className="text-2xl font-bold">
                {assessment?.total_facts_approved ?? 0}
              </p>
              <p className="text-sm text-gray-500">Approved Facts</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3">
            <Info className="h-8 w-8 text-yellow-500" />
            <div>
              <p className="text-2xl font-bold">
                {assessment?.total_facts_pending ?? 0}
              </p>
              <p className="text-sm text-gray-500">Pending Review</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-8 w-8 text-red-500" />
            <div>
              <p className="text-2xl font-bold">
                {assessment?.critical_gaps_count ?? 0}
              </p>
              <p className="text-sm text-gray-500">Critical Gaps</p>
            </div>
          </div>
        </div>
        <div className="card p-5">
          <div className="flex items-center gap-3">
            <TrendingUp className="h-8 w-8 text-blue-500" />
            <div>
              <p className="text-2xl font-bold">
                {assessment?.material_gaps_count ?? 0}
              </p>
              <p className="text-sm text-gray-500">Material Gaps</p>
            </div>
          </div>
        </div>
      </div>

      {/* Priority Actions */}
      {gaps?.priority_actions && gaps.priority_actions.length > 0 && (
        <div className="card p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Priority Actions
          </h2>
          <ol className="list-decimal list-inside space-y-2">
            {gaps.priority_actions.map((action, index) => (
              <li key={index} className="text-gray-700">
                {action}
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Critical Gaps */}
      {gaps?.critical_gaps && gaps.critical_gaps.length > 0 && (
        <div className="card">
          <div className="border-b border-gray-200 px-5 py-4 bg-red-50">
            <h2 className="text-lg font-medium text-red-800">Critical Gaps</h2>
            <p className="text-sm text-red-600">
              These gaps must be addressed before proceeding
            </p>
          </div>
          <ul className="divide-y divide-gray-200">
            {gaps.critical_gaps.map((gap, index) => (
              <li key={index} className="px-5 py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{gap.description}</p>
                    {gap.short_description && (
                      <p className="mt-1 text-sm text-gray-600">{gap.short_description}</p>
                    )}
                  </div>
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded ml-3 whitespace-nowrap text-gray-500">
                    {gap.schema_path}
                  </code>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Material Gaps */}
      {gaps?.material_gaps && gaps.material_gaps.length > 0 && (
        <div className="card">
          <div className="border-b border-gray-200 px-5 py-4 bg-yellow-50">
            <h2 className="text-lg font-medium text-yellow-800">Material Gaps</h2>
            <p className="text-sm text-yellow-600">
              These gaps significantly affect scoring
            </p>
          </div>
          <ul className="divide-y divide-gray-200">
            {gaps.material_gaps.slice(0, 10).map((gap, index) => (
              <li key={index} className="px-5 py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">{gap.description}</p>
                    {gap.short_description && (
                      <p className="mt-1 text-sm text-gray-600">{gap.short_description}</p>
                    )}
                  </div>
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded ml-3 whitespace-nowrap text-gray-500">
                    {gap.schema_path}
                  </code>
                </div>
              </li>
            ))}
            {gaps.material_gaps.length > 10 && (
              <li className="px-5 py-4 text-sm text-gray-500">
                ...and {gaps.material_gaps.length - 10} more
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}
