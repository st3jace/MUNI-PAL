import { useState, useEffect, useMemo } from 'react'
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
  Clock,
  DollarSign,
  TrendingUp,
  Building2,
  HeartPulse,
  Home,
  Stethoscope,
} from 'lucide-react'
import { sensingApi, SectorInfo } from '../../services/sensingApi'
import { useSensing } from '../../contexts/SensingContext'

const SUB_SECTOR_META: Record<
  string,
  { icon: typeof Building2; label: string; description: string }
> = {
  healthcare_hospital: {
    icon: Building2,
    label: 'Hospital',
    description: 'Acute care hospitals & health systems',
  },
  healthcare_senior_living: {
    icon: Home,
    label: 'Senior Living / CCRC',
    description: 'Continuing care retirement communities',
  },
  healthcare_fqhc_bond: {
    icon: HeartPulse,
    label: 'FQHC Revenue Bonds',
    description: 'Federally qualified health centers \u2014 bond track',
  },
  healthcare_fqhc_cdfi: {
    icon: Stethoscope,
    label: 'FQHC CDFI/NMTC',
    description: 'Federally qualified health centers \u2014 CDFI/NMTC track',
  },
}

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

function formatCurrency(value: number): string {
  if (value >= 1000) return `$${(value / 1000).toFixed(0)}K`
  return `$${value.toLocaleString()}`
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ResultsView({ data }: { data: any }) {
  const hasCoi = data.coi_estimate != null
  const hasTimeline =
    data.timeline_baseline_weeks != null &&
    data.timeline_compressed_weeks != null

  return (
    <div className="space-y-5">
      {/* Score Banner */}
      <div className={`rounded-lg border-2 p-6 ${tierColor(data.tier)}`}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold">{data.project_name}</h2>
            <p className="text-sm opacity-75 mt-1">
              {data.sector
                ?.replace(/_/g, ' ')
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

      {/* COI Gap Estimate Banner */}
      {hasCoi && (
        <div className="rounded-lg border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-5">
          <div className="flex items-start gap-3">
            <DollarSign className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-amber-900">
                Cost of Issuance Impact
              </h3>
              <p className="text-sm text-amber-800 mt-1">
                Incomplete readiness may add{' '}
                <span className="font-bold">
                  {typeof data.coi_estimate === 'object'
                    ? `${formatCurrency(data.coi_estimate.low)}-${formatCurrency(data.coi_estimate.high)}`
                    : formatCurrency(data.coi_estimate)}
                </span>{' '}
                in additional issuance costs from advisory fees, expanded
                feasibility scope, and extended deal timelines.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Timeline Comparison + Agent Displacement */}
      {(hasTimeline || data.agent_displacement_value) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {hasTimeline && (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
              <div className="flex items-center gap-2 mb-4">
                <Clock className="h-4 w-4 text-gray-500" />
                <h3 className="font-semibold text-gray-900 text-sm">
                  Timeline to Market
                </h3>
              </div>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Baseline</span>
                    <span>
                      {Array.isArray(data.timeline_baseline_weeks)
                        ? `${data.timeline_baseline_weeks[0]}-${data.timeline_baseline_weeks[1]} weeks`
                        : `${data.timeline_baseline_weeks} weeks`}
                    </span>
                  </div>
                  <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gray-400 rounded-full"
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                    <span>Agent-Assisted</span>
                    <span>
                      {Array.isArray(data.timeline_compressed_weeks)
                        ? `${data.timeline_compressed_weeks[0]}-${data.timeline_compressed_weeks[1]} weeks`
                        : `${data.timeline_compressed_weeks} weeks`}
                    </span>
                  </div>
                  <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-500 rounded-full"
                      style={{
                        width: `${
                          Array.isArray(data.timeline_compressed_weeks)
                            ? (data.timeline_compressed_weeks[1] /
                                (Array.isArray(data.timeline_baseline_weeks)
                                  ? data.timeline_baseline_weeks[1]
                                  : data.timeline_baseline_weeks)) *
                              100
                            : (data.timeline_compressed_weeks /
                                data.timeline_baseline_weeks) *
                              100
                        }%`,
                      }}
                    />
                  </div>
                </div>
                {data.timeline_compression_pct != null && (
                  <p className="text-xs text-gray-500 mt-1">
                    {Math.round(data.timeline_compression_pct)}% faster
                    with agent-assisted preparation
                  </p>
                )}
              </div>
            </div>
          )}

          {data.agent_displacement_value && (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="h-4 w-4 text-gray-500" />
                <h3 className="font-semibold text-gray-900 text-sm">
                  Agent Displacement Value
                </h3>
              </div>
              <div className="text-3xl font-bold text-primary-600">
                {typeof data.agent_displacement_value === 'object'
                  ? `${formatCurrency(data.agent_displacement_value.low)}-${formatCurrency(data.agent_displacement_value.high)}`
                  : formatCurrency(data.agent_displacement_value)}
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Estimated savings per deal through agent-assisted preparation.
              </p>
            </div>
          )}
        </div>
      )}

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
                      style={{
                        width: `${(dim.score / (dim.max_score || 20)) * 100}%`,
                      }}
                    />
                  </div>
                </div>
                <div
                  className={`w-14 text-right text-sm font-semibold ${scoreColor((dim.score / (dim.max_score || 20)) * 100)}`}
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

function SubSectorPicker({
  children,
  selected,
  onSelect,
}: {
  children: SectorInfo[]
  selected: string | null
  onSelect: (id: string) => void
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-5">
      <h3 className="font-semibold text-gray-900 mb-2">
        Healthcare Sub-Sector
      </h3>
      <p className="text-sm text-gray-500 mb-4">
        Select the type of healthcare facility for a tailored readiness
        assessment.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {children.map((child) => {
          const meta = SUB_SECTOR_META[child.id]
          const Icon = meta?.icon || Building2
          const isSelected = selected === child.id
          return (
            <button
              key={child.id}
              type="button"
              onClick={() => onSelect(child.id)}
              className={`flex items-start gap-3 rounded-lg border-2 p-4 text-left transition-all ${
                isSelected
                  ? 'border-primary-500 bg-primary-50 ring-1 ring-primary-200'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              <Icon
                className={`h-5 w-5 mt-0.5 flex-shrink-0 ${isSelected ? 'text-primary-600' : 'text-gray-400'}`}
              />
              <div>
                <div
                  className={`text-sm font-semibold ${isSelected ? 'text-primary-900' : 'text-gray-900'}`}
                >
                  {meta?.label || child.name}
                </div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {meta?.description || child.name}
                </div>
              </div>
            </button>
          )
        })}
      </div>
    </div>
  )
}

const CATEGORY_ORDER = ['required', 'recommended', 'optional'] as const
const CATEGORY_STYLE: Record<
  string,
  { bg: string; badge: string; label: string }
> = {
  required: {
    bg: 'border-red-100',
    badge: 'bg-red-100 text-red-700',
    label: 'Required',
  },
  recommended: {
    bg: 'border-amber-100',
    badge: 'bg-amber-100 text-amber-700',
    label: 'Recommended',
  },
  optional: {
    bg: 'border-gray-100',
    badge: 'bg-gray-100 text-gray-600',
    label: 'Optional',
  },
}

function isHealthcareSector(s: string): boolean {
  return s.startsWith('healthcare')
}

export default function ReadinessAssess() {
  const sensing = useSensing()
  const [sector, setSector] = useState(sensing.sector || 'healthcare')
  const [subSector, setSubSector] = useState<string | null>(null)
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

  const assessMutation = useMutation({
    mutationFn: sensingApi.runReadinessAssessment,
  })

  // Find healthcare sector children
  const healthcareSector = (sectorsQuery.data || []).find(
    (s) => s.id === 'healthcare'
  )
  const hasSubSectors =
    healthcareSector?.children && healthcareSector.children.length > 0

  // The effective sector sent to the API
  const effectiveSector =
    isHealthcareSector(sector) && subSector ? subSector : sector

  const questionnaireQuery = useQuery({
    queryKey: ['sensing-questionnaire', effectiveSector],
    queryFn: () => sensingApi.getQuestionnaire(effectiveSector),
    enabled: !(isHealthcareSector(sector) && hasSubSectors && !subSector),
  })

  // Store results in shared context for PDF export
  useEffect(() => {
    if (assessMutation.data) {
      sensing.setReadiness(assessMutation.data)
      sensing.setSector(effectiveSector)
    }
  }, [assessMutation.data]) // eslint-disable-line react-hooks/exhaustive-deps

  // Reset form state when sector or sub-sector changes
  useEffect(() => {
    setResponses({})
    setEvidenceIds(new Set())
    assessMutation.reset()
  }, [sector, subSector]) // eslint-disable-line react-hooks/exhaustive-deps

  // Reset sub-sector when switching away from healthcare
  useEffect(() => {
    if (!isHealthcareSector(sector)) {
      setSubSector(null)
    }
  }, [sector])

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
      sector: effectiveSector,
      project_name: projectName || 'Project',
      responses,
      evidence_ids: Array.from(evidenceIds),
      dscr: dscr ? parseFloat(dscr) : undefined,
      revenue: revenue ? parseFloat(revenue.replace(/[,$]/g, '')) : undefined,
      coverage_ratio: coverageRatio ? parseFloat(coverageRatio) : undefined,
    })
  }

  // Determine if the questionnaire uses healthcare-style categories
  const isHealthcareQuestionnaire = useMemo(() => {
    const items = questionnaireQuery.data || []
    return items.some(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (i: any) =>
        i.category === 'required' ||
        i.category === 'recommended' ||
        i.category === 'optional'
    )
  }, [questionnaireQuery.data])

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

  // Derive dimensions dynamically from the questionnaire data
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
            Evaluate your project across {dimensions.length || 5}{' '}
            {isHealthcareQuestionnaire
              ? 'readiness categories'
              : 'risk dimensions'}
          </p>
        </div>
      </div>

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
                  placeholder="e.g., Regional Medical Center"
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

          {/* Healthcare Sub-Sector Picker */}
          {isHealthcareSector(sector) &&
            hasSubSectors &&
            healthcareSector?.children && (
              <SubSectorPicker
                children={healthcareSector.children}
                selected={subSector}
                onSelect={setSubSector}
              />
            )}

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

          {/* Questionnaire */}
          {questionnaireQuery.isLoading ? (
            <div className="flex items-center justify-center py-10">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">
                Loading questionnaire...
              </span>
            </div>
          ) : isHealthcareSector(sector) && hasSubSectors && !subSector ? (
            <div className="flex items-center justify-center py-10 text-gray-500 text-sm">
              Select a healthcare sub-sector above to load the readiness
              questionnaire.
            </div>
          ) : isHealthcareQuestionnaire ? (
            dimensions.map((dim) => {
              const items = grouped[dim.key] || []
              return (
                <div
                  key={dim.key}
                  className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-5"
                >
                  <h3 className="font-semibold text-gray-900 text-base mb-5">
                    {dim.label}
                  </h3>
                  {CATEGORY_ORDER.map((cat) => {
                    const catItems = items.filter(
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      (i: any) => i.category === cat
                    )
                    if (catItems.length === 0) return null
                    const style = CATEGORY_STYLE[cat]
                    return (
                      <div key={cat} className="mb-5 last:mb-0">
                        <div className="flex items-center gap-2 mb-3">
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${style.badge}`}
                          >
                            {style.label}
                          </span>
                          <span className="text-xs text-gray-400">
                            {catItems.length} item
                            {catItems.length !== 1 ? 's' : ''}
                          </span>
                        </div>
                        <div
                          className={`space-y-3 pl-1 border-l-2 ${style.bg}`}
                        >
                          {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                          {catItems.map((item: any) => (
                            <label
                              key={item.item_id}
                              className="flex items-start gap-3 cursor-pointer group pl-3"
                            >
                              <input
                                type="checkbox"
                                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-primary-600"
                                checked={responses[item.item_id] || false}
                                onChange={() => toggleResponse(item.item_id)}
                              />
                              <div className="flex-1 min-w-0">
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
                                <div className="flex flex-wrap items-center gap-3 mt-1.5">
                                  {item.lead_time && (
                                    <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                                      <Clock className="h-3 w-3" />
                                      {item.lead_time}
                                    </span>
                                  )}
                                  {item.agent_assistable &&
                                    item.agent_assistable !== 'no' && (
                                      <span className="inline-flex items-center gap-1 text-xs text-primary-500">
                                        <TrendingUp className="h-3 w-3" />
                                        {item.agent_assistable === 'yes'
                                          ? 'Agent-assistable'
                                          : 'Partially assistable'}
                                      </span>
                                    )}
                                  {item.coi_impact &&
                                    (item.coi_impact === 'high' ||
                                      item.coi_impact === 'very_high') && (
                                      <span className="inline-flex items-center gap-1 text-xs text-amber-500">
                                        <DollarSign className="h-3 w-3" />
                                        {item.coi_impact === 'very_high'
                                          ? 'Very high COI impact'
                                          : 'High COI impact'}
                                      </span>
                                    )}
                                </div>
                              </div>
                            </label>
                          ))}
                        </div>
                      </div>
                    )
                  })}
                </div>
              )
            })
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
              disabled={
                assessMutation.isPending ||
                (isHealthcareSector(sector) && hasSubSectors && !subSector)
              }
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
