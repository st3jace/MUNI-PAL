import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  ArrowLeft,
  ClipboardCheck,
  Loader2,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCcw,
  Download,
} from 'lucide-react'
import { sensingApi } from '../../services/sensingApi'
import { useSensing } from '../../contexts/SensingContext'

// Dimensions are now derived dynamically from the questionnaire data
// returned by the API, which is sector-specific.

function tierColor(tier: string): string {
  switch (tier) {
    case 'Bond Ready':
      return 'text-green-700 bg-green-50 border-green-300'
    case 'Nearly Ready':
      return 'text-blue-700 bg-blue-50 border-blue-300'
    case 'Developing':
      return 'text-amber-700 bg-amber-50 border-amber-300'
    default:
      return 'text-red-700 bg-red-50 border-red-300'
  }
}

function scoreColor(score: number): string {
  if (score >= 85) return 'text-green-600'
  if (score >= 65) return 'text-blue-600'
  if (score >= 40) return 'text-amber-600'
  return 'text-red-600'
}

function barColor(score: number): string {
  if (score >= 17) return 'bg-green-500'
  if (score >= 13) return 'bg-blue-500'
  if (score >= 8) return 'bg-amber-500'
  return 'bg-red-500'
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ResultsView({ data }: { data: any }) {
  return (
    <div className="space-y-5">
      {/* Score Banner */}
      <div className={`rounded-lg border-2 p-6 ${tierColor(data.tier)}`}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">{data.project_name}</h2>
            <p className="text-sm opacity-75 mt-1">
              {data.sector
                ?.replace('_', ' ')
                .replace(/\b\w/g, (c: string) => c.toUpperCase())}{' '}
              Sector
            </p>
          </div>
          <div className="text-right">
            <div
              className={`text-4xl font-bold ${scoreColor(data.readiness_score)}`}
            >
              {data.readiness_score}
            </div>
            <div className="text-sm font-medium mt-1">{data.tier}</div>
          </div>
        </div>
        <p className="mt-3 text-sm leading-relaxed">{data.tier_guidance}</p>
      </div>

      {/* Dimension Scores */}
      {data.dimensions && data.dimensions.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-5">Dimension Scores</h3>
          <div className="space-y-4">
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {data.dimensions.map((dim: any) => (
              <div key={dim.dimension} className="flex items-center gap-4">
                <div className="w-48 text-sm font-medium text-gray-700 truncate">
                  {dim.display_name || dim.dimension}
                </div>
                <div className="flex-1">
                  <div className="h-5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${barColor(dim.score)}`}
                      style={{ width: `${(dim.score / 20) * 100}%` }}
                    />
                  </div>
                </div>
                <div
                  className={`w-14 text-right text-sm font-semibold ${scoreColor(dim.score * 5)}`}
                >
                  {dim.score}/{dim.max_score || 20}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Financial Assessment */}
      {data.financial_assessment && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-4">
            Financial Assessment
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            {data.financial_assessment.dscr_assessment && (
              <div className="bg-gray-50 rounded-lg px-4 py-3">
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                  DSCR
                </div>
                <div className="text-sm text-gray-900 leading-relaxed">
                  {data.financial_assessment.dscr_assessment}
                </div>
              </div>
            )}
            {data.financial_assessment.coverage_assessment && (
              <div className="bg-gray-50 rounded-lg px-4 py-3">
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                  Coverage
                </div>
                <div className="text-sm text-gray-900 leading-relaxed">
                  {data.financial_assessment.coverage_assessment}
                </div>
              </div>
            )}
            {data.financial_assessment.revenue_assessment && (
              <div className="bg-gray-50 rounded-lg px-4 py-3">
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                  Revenue
                </div>
                <div className="text-sm text-gray-900 leading-relaxed">
                  {data.financial_assessment.revenue_assessment}
                </div>
              </div>
            )}
            <div className="bg-gray-50 rounded-lg px-4 py-3">
              <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
                Score Adjustment
              </div>
              <div
                className={`text-lg font-semibold ${
                  data.financial_assessment.total_adjustment > 0
                    ? 'text-green-600'
                    : data.financial_assessment.total_adjustment < 0
                      ? 'text-red-600'
                      : 'text-gray-600'
                }`}
              >
                {data.financial_assessment.total_adjustment > 0 ? '+' : ''}
                {data.financial_assessment.total_adjustment ?? 0} pts
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Gap Analysis */}
      {data.gap_analysis && data.gap_analysis.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Gap Analysis</h3>
          <div className="space-y-3">
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {data.gap_analysis.map((gap: any, i: number) => (
              <div
                key={i}
                className={`rounded-lg border p-4 ${
                  gap.severity === 'critical'
                    ? 'border-red-200 bg-red-50'
                    : gap.severity === 'material'
                      ? 'border-amber-200 bg-amber-50'
                      : 'border-green-200 bg-green-50'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {gap.severity === 'critical' ? (
                    <XCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
                  ) : gap.severity === 'material' ? (
                    <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0" />
                  ) : (
                    <CheckCircle2 className="h-4 w-4 text-green-500 flex-shrink-0" />
                  )}
                  <span className="text-sm font-semibold">
                    {gap.dimension_name || gap.dimension}
                  </span>
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      gap.severity === 'critical'
                        ? 'bg-red-100 text-red-700'
                        : gap.severity === 'material'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-green-100 text-green-700'
                    }`}
                  >
                    {gap.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-600 ml-6 leading-relaxed">
                  {gap.narrative}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Priority Actions */}
      {data.priority_actions && data.priority_actions.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Priority Actions</h3>
          <ol className="space-y-2.5">
            {data.priority_actions.map((action: string, i: number) => (
              <li key={i} className="flex gap-3 text-sm text-gray-700">
                <span className="font-semibold text-gray-400 flex-shrink-0 w-6 text-right">
                  {i + 1}.
                </span>
                <span className="leading-relaxed">{action}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      <div className="text-xs text-gray-400 text-right pt-2">
        Generated: {data.generated_at?.slice(0, 10)} | Evidence:{' '}
        {data.evidence_present ?? 0}/{data.evidence_possible ?? 25}
      </div>
    </div>
  )
}

export default function ReadinessAssess() {
  const sensing = useSensing()
  const [sector, setSector] = useState(sensing.sector || 'healthcare')
  const [projectName, setProjectName] = useState('')
  const [responses, setResponses] = useState<Record<string, boolean>>({})
  const [evidenceIds, setEvidenceIds] = useState<Set<string>>(new Set())
  const [dscr, setDscr] = useState('')
  const [revenue, setRevenue] = useState('')
  const [coverageRatio, setCoverageRatio] = useState('')

  const sectorsQuery = useQuery({
    queryKey: ['sensing-sectors'],
    queryFn: sensingApi.listSectors,
  })

  const questionnaireQuery = useQuery({
    queryKey: ['sensing-questionnaire', sector],
    queryFn: () => sensingApi.getQuestionnaire(sector),
  })

  const assessMutation = useMutation({
    mutationFn: sensingApi.runReadinessAssessment,
  })

  // Store results in shared context for PDF export
  useEffect(() => {
    if (assessMutation.data) {
      sensing.setReadiness(assessMutation.data)
      sensing.setSector(sector)
    }
  }, [assessMutation.data]) // eslint-disable-line react-hooks/exhaustive-deps

  // Reset form state when sector changes (different dimensions/questions)
  useEffect(() => {
    setResponses({})
    setEvidenceIds(new Set())
    assessMutation.reset()
  }, [sector]) // eslint-disable-line react-hooks/exhaustive-deps

  const toggleResponse = (key: string) => {
    setResponses((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const toggleEvidence = (id: string) => {
    setEvidenceIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    assessMutation.mutate({
      sector,
      project_name: projectName || 'Project',
      responses,
      evidence_ids: Array.from(evidenceIds),
      dscr: dscr ? parseFloat(dscr) : undefined,
      revenue: revenue ? parseFloat(revenue.replace(/[,$]/g, '')) : undefined,
      coverage_ratio: coverageRatio ? parseFloat(coverageRatio) : undefined,
    })
  }

  // Group questionnaire items by dimension
  const grouped = (questionnaireQuery.data || []).reduce(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (acc: Record<string, any[]>, item: any) => {
      acc[item.dimension] = acc[item.dimension] || []
      acc[item.dimension].push(item)
      return acc
    },
    {} as Record<string, unknown[]>
  )

  // Derive dimensions dynamically from the questionnaire data (preserves order)
  const dimensions: { key: string; label: string }[] = []
  const seenDims = new Set<string>()
  for (const item of questionnaireQuery.data || []) {
    if (!seenDims.has(item.dimension)) {
      seenDims.add(item.dimension)
      dimensions.push({
        key: item.dimension,
        label: item.dimension_label || item.dimension,
      })
    }
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8 flex items-start gap-4">
        <Link to="/tools" className="mt-1 text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Bond Readiness Assessment
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Evaluate your project across {dimensions.length || 5} risk dimensions
          </p>
        </div>
      </div>

      {/* Show results if available */}
      {assessMutation.data ? (
        <div>
          <div className="flex items-center justify-between mb-6">
            <button
              className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 rounded-lg px-4 py-2 transition-colors"
              onClick={() => assessMutation.reset()}
            >
              <RotateCcw className="h-4 w-4" />
              Start New Assessment
            </button>
            <Link
              to="/tools/export"
              className="flex items-center gap-2 text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              <Download className="h-4 w-4" />
              Export Combined Report
              {sensing.completedCount > 0 && (
                <span className="bg-primary-100 text-primary-700 rounded-full px-2 py-0.5 text-xs">
                  {sensing.completedCount}/3
                </span>
              )}
            </Link>
          </div>
          <ResultsView data={assessMutation.data} />
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          {/* Project Info */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-5">
            <h3 className="font-semibold text-gray-900 mb-4">
              Project Information
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Project Name
                </label>
                <input
                  type="text"
                  className="input w-full"
                  placeholder="e.g., Regional Waste Authority"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Sector
                </label>
                <select
                  className="input w-full"
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                >
                  {(sectorsQuery.data || []).map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Financial Metrics */}
          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-5">
            <h3 className="font-semibold text-gray-900 mb-4">
              Financial Metrics
              <span className="text-sm font-normal text-gray-500 ml-2">
                (optional)
              </span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  DSCR
                </label>
                <input
                  type="number"
                  step="0.01"
                  className="input w-full"
                  placeholder="e.g., 1.35"
                  value={dscr}
                  onChange={(e) => setDscr(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Annual Revenue (USD)
                </label>
                <input
                  type="text"
                  className="input w-full"
                  placeholder="e.g., 10,000,000"
                  value={revenue}
                  onChange={(e) => setRevenue(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Coverage Ratio
                </label>
                <input
                  type="number"
                  step="0.01"
                  className="input w-full"
                  placeholder="e.g., 1.50"
                  value={coverageRatio}
                  onChange={(e) => setCoverageRatio(e.target.value)}
                />
              </div>
            </div>
          </div>

          {/* Risk Dimensions */}
          {questionnaireQuery.isLoading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">
                Loading questionnaire...
              </span>
            </div>
          ) : (
            dimensions.map((dim) => {
              const items = grouped[dim.key] || []
              const descItems = items.filter(
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (i: any) => i.category === 'description'
              )
              const mitItems = items.filter(
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (i: any) => i.category === 'mitigants'
              )
              const evidItems = items.filter(
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                (i: any) => i.category === 'evidence'
              )
              return (
                <div
                  key={dim.key}
                  className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-5"
                >
                  <h3 className="font-semibold text-gray-900 text-base mb-5">
                    {dim.label}
                  </h3>

                  {/* Description & Mitigants toggles */}
                  <div className="space-y-4 mb-5">
                    {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                    {[...descItems, ...mitItems].map((item: any) => (
                      <label
                        key={item.item_id}
                        className="flex items-start gap-3 cursor-pointer group"
                      >
                        <input
                          type="checkbox"
                          className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary-600"
                          checked={responses[item.item_id] || false}
                          onChange={() => toggleResponse(item.item_id)}
                        />
                        <div>
                          <div className="text-sm font-medium text-gray-800 leading-relaxed">
                            {item.question}
                            <span className="ml-1.5 text-xs text-gray-400">
                              (+{item.points} pts)
                            </span>
                          </div>
                          {item.help_text && (
                            <div className="text-xs text-gray-500 mt-1 leading-relaxed">
                              {item.help_text}
                            </div>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>

                  {/* Evidence items */}
                  {evidItems.length > 0 && (
                    <div className="border-t border-gray-100 pt-4">
                      <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                        Evidence Items (+2 pts each)
                      </h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                        {evidItems.map((item: any) => (
                          <label
                            key={item.item_id}
                            className="flex items-center gap-2.5 cursor-pointer text-sm"
                          >
                            <input
                              type="checkbox"
                              className="h-3.5 w-3.5 rounded border-gray-300 text-primary-600"
                              checked={evidenceIds.has(item.item_id)}
                              onChange={() => toggleEvidence(item.item_id)}
                            />
                            <span className="text-gray-700 leading-relaxed">
                              {item.question}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )
            })
          )}

          {/* Submit */}
          <div className="flex justify-end gap-3 mt-6 mb-8">
            <button
              type="submit"
              className="btn btn-primary flex items-center gap-2 px-6 py-2.5"
              disabled={assessMutation.isPending}
            >
              {assessMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Scoring...
                </>
              ) : (
                <>
                  <ClipboardCheck className="h-4 w-4" />
                  Score Assessment
                </>
              )}
            </button>
          </div>

          {assessMutation.error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mt-4">
              Assessment failed: {String(assessMutation.error)}
            </div>
          )}
        </form>
      )}
    </div>
  )
}
