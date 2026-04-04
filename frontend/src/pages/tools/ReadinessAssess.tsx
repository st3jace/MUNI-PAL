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
  Building2,
  Home,
  Heart,
  Landmark,
  Clock,
  DollarSign,
  TrendingDown,
  Bot,
} from 'lucide-react'
import { sensingApi } from '../../services/sensingApi'
import { useSensing } from '../../contexts/SensingContext'

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

function barColorPct(pct: number): string {
  if (pct >= 75) return 'bg-green-500'
  if (pct >= 50) return 'bg-blue-500'
  if (pct >= 25) return 'bg-amber-500'
  return 'bg-red-500'
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`
  return `$${value.toLocaleString()}`
}

const SUB_SECTOR_ICONS: Record<string, typeof Building2> = {
  healthcare_hospital: Building2,
  healthcare_senior_living: Home,
  healthcare_fqhc_bond: Heart,
  healthcare_fqhc_cdfi: Landmark,
}

const SUB_SECTOR_DESCRIPTIONS: Record<string, string> = {
  healthcare_hospital: 'Acute care hospitals & health systems',
  healthcare_senior_living: 'CCRCs & senior living facilities',
  healthcare_fqhc_bond: 'Revenue bond issuance (large FQHCs)',
  healthcare_fqhc_cdfi: 'CDFI/NMTC financing (most FQHCs)',
}

const CATEGORY_STYLES: Record<string, { label: string; bg: string; text: string; border: string }> = {
  required: { label: 'Required', bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200' },
  recommended: { label: 'Recommended', bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
  optional: { label: 'Optional', bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200' },
}

/** Detect whether the questionnaire uses the new category format. */
function isNewFormat(items: { category: string }[]): boolean {
  return items.some((it) => it.category === 'required' || it.category === 'recommended')
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function COIBanner({ data }: { data: any }) {
  if (!data.coi_estimate) return null
  const { min, max, required_items_gap, required_items_total } = data.coi_estimate
  if (min === 0 && max === 0) return null

  return (
    <div className="rounded-lg border-2 border-amber-300 bg-amber-50 p-5">
      <div className="flex items-start gap-3">
        <DollarSign className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
        <div>
          <h3 className="font-semibold text-amber-800">Estimated Cost of Incomplete Readiness</h3>
          <p className="text-2xl font-bold text-amber-900 mt-1">
            {formatCurrency(min)} &ndash; {formatCurrency(max)}
          </p>
          <p className="text-sm text-amber-700 mt-1">
            Based on {required_items_gap} of {required_items_total} required items still outstanding.
            Completing these items before approaching the market can significantly reduce advisory fees,
            feasibility study costs, and deal timeline.
          </p>
        </div>
      </div>
    </div>
  )
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function TimelineComparison({ data }: { data: any }) {
  if (!data.timeline_baseline_weeks || !data.timeline_compressed_weeks) return null

  const baseline = data.timeline_baseline_weeks
  const compressed = data.timeline_compressed_weeks
  const compressionPct = data.timeline_compression_pct || 0
  const maxWeeks = baseline.max

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
      <div className="flex items-center gap-2 mb-4">
        <Clock className="h-4 w-4 text-gray-500" />
        <h3 className="font-semibold text-gray-900">Timeline to Market</h3>
        {compressionPct > 0 && (
          <span className="inline-flex items-center gap-1 rounded-full bg-green-100 text-green-700 px-2.5 py-0.5 text-xs font-medium">
            <TrendingDown className="h-3 w-3" />
            {compressionPct}% faster with agent assistance
          </span>
        )}
      </div>
      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-600">Traditional preparation</span>
            <span className="font-medium text-gray-900">{baseline.min}&ndash;{baseline.max} weeks</span>
          </div>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gray-400 rounded-full"
              style={{ width: `${(baseline.max / maxWeeks) * 100}%` }}
            />
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-gray-600 flex items-center gap-1">
              <Bot className="h-3.5 w-3.5" /> Agent-assisted
            </span>
            <span className="font-medium text-green-700">{compressed.min}&ndash;{compressed.max} weeks</span>
          </div>
          <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-green-500 rounded-full"
              style={{ width: `${(compressed.max / maxWeeks) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function AgentDisplacementCard({ data }: { data: any }) {
  if (!data.agent_displacement_value) return null

  return (
    <div className="bg-gradient-to-br from-primary-50 to-blue-50 rounded-lg border border-primary-200 p-5">
      <div className="flex items-center gap-2 mb-2">
        <Bot className="h-4 w-4 text-primary-600" />
        <h3 className="font-semibold text-primary-900">Agent Displacement Value</h3>
      </div>
      <p className="text-3xl font-bold text-primary-700">
        {formatCurrency(data.agent_displacement_value)}
      </p>
      <p className="text-sm text-primary-600 mt-1">
        Estimated cost savings per deal through agent-assisted preparation —
        reduced advisory hours, faster data compilation, and improved rating outcomes.
      </p>
    </div>
  )
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

      {/* COI Estimate Banner */}
      <COIBanner data={data} />

      {/* Timeline + Agent Displacement side by side */}
      {(data.timeline_baseline_weeks || data.agent_displacement_value) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <TimelineComparison data={data} />
          <AgentDisplacementCard data={data} />
        </div>
      )}

      {/* Dimension Scores */}
      {data.dimensions && data.dimensions.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-5">Dimension Scores</h3>
          <div className="space-y-4">
            {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
            {data.dimensions.map((dim: any) => {
              const pct = dim.pct ?? (dim.max_score ? (dim.score / dim.max_score) * 100 : 0)
              return (
                <div key={dim.dimension} className="flex items-center gap-4">
                  <div className="w-48 text-sm font-medium text-gray-700 truncate">
                    {dim.display_name || dim.dimension}
                  </div>
                  <div className="flex-1">
                    <div className="h-5 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${barColorPct(pct)}`}
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div
                    className={`w-20 text-right text-sm font-semibold ${scoreColor(pct)}`}
                  >
                    {dim.score}/{dim.max_score}
                  </div>
                </div>
              )
            })}
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
                  {gap.high_coi_impact_items > 0 && (
                    <span className="inline-flex items-center rounded-full bg-red-100 text-red-700 px-2 py-0.5 text-xs font-medium">
                      {gap.high_coi_impact_items} high-COI items
                    </span>
                  )}
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

/**
 * Renders questionnaire items grouped by category (required/recommended/optional)
 * for the new healthcare sub-sector format.
 */
function CategoryGroupedItems({
  items,
  responses,
  toggleResponse,
}: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  items: any[]
  responses: Record<string, boolean>
  toggleResponse: (key: string) => void
}) {
  const byCategory: Record<string, typeof items> = {}
  for (const item of items) {
    const cat = item.category || 'optional'
    byCategory[cat] = byCategory[cat] || []
    byCategory[cat].push(item)
  }

  const order = ['required', 'recommended', 'optional']

  return (
    <div className="space-y-5">
      {order.map((cat) => {
        const catItems = byCategory[cat]
        if (!catItems || catItems.length === 0) return null
        const style = CATEGORY_STYLES[cat] || CATEGORY_STYLES.optional

        return (
          <div key={cat}>
            <div className="flex items-center gap-2 mb-3">
              <span
                className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${style.bg} ${style.text}`}
              >
                {style.label}
              </span>
              <span className="text-xs text-gray-400">
                {catItems.length} item{catItems.length !== 1 ? 's' : ''}
              </span>
            </div>
            <div className="space-y-3">
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {catItems.map((item: any) => (
                <label
                  key={item.item_id}
                  className={`flex items-start gap-3 cursor-pointer group rounded-lg border p-3 transition-colors ${
                    responses[item.item_id]
                      ? 'border-green-200 bg-green-50/50'
                      : `${style.border} hover:bg-gray-50`
                  }`}
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
                    </div>
                    {item.help_text && (
                      <div className="text-xs text-gray-500 mt-1 leading-relaxed">
                        {item.help_text}
                      </div>
                    )}
                    <div className="flex flex-wrap items-center gap-2 mt-1.5">
                      {item.lead_time && (
                        <span className="inline-flex items-center gap-1 text-xs text-gray-400">
                          <Clock className="h-3 w-3" /> {item.lead_time}
                        </span>
                      )}
                      {item.agent_assistable && (
                        <span className="inline-flex items-center gap-1 text-xs text-primary-500">
                          <Bot className="h-3 w-3" /> Agent-assistable
                        </span>
                      )}
                      {item.coi_impact && ['HIGH', 'VERY HIGH'].includes(item.coi_impact.toUpperCase()) && (
                        <span className="inline-flex items-center gap-1 text-xs text-red-500 font-medium">
                          <DollarSign className="h-3 w-3" /> {item.coi_impact} COI impact
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
}

/**
 * Renders questionnaire items in the legacy format (description/mitigants/evidence).
 */
function LegacyItems({
  items,
  responses,
  evidenceIds,
  toggleResponse,
  toggleEvidence,
}: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  items: any[]
  responses: Record<string, boolean>
  evidenceIds: Set<string>
  toggleResponse: (key: string) => void
  toggleEvidence: (id: string) => void
}) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const descItems = items.filter((i: any) => i.category === 'description')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const mitItems = items.filter((i: any) => i.category === 'mitigants')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const evidItems = items.filter((i: any) => i.category === 'evidence')

  return (
    <>
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
    </>
  )
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

  // Resolve the effective sector for API calls
  const effectiveSector = subSector || sector

  const questionnaireQuery = useQuery({
    queryKey: ['sensing-questionnaire', effectiveSector],
    queryFn: () => sensingApi.getQuestionnaire(effectiveSector),
  })

  const assessMutation = useMutation({
    mutationFn: sensingApi.runReadinessAssessment,
  })

  // Store results in shared context for PDF export
  useEffect(() => {
    if (assessMutation.data) {
      sensing.setReadiness(assessMutation.data)
      sensing.setSector(effectiveSector)
    }
  }, [assessMutation.data]) // eslint-disable-line react-hooks/exhaustive-deps

  // Reset form state when sector changes
  useEffect(() => {
    setResponses({})
    setEvidenceIds(new Set())
    assessMutation.reset()
  }, [effectiveSector]) // eslint-disable-line react-hooks/exhaustive-deps

  // Reset sub-sector when parent sector changes
  useEffect(() => {
    setSubSector(null)
  }, [sector])

  // Find children for the current sector (healthcare sub-sectors)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const currentSectorData = (sectorsQuery.data || []).find((s: any) => s.id === sector)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const children: { id: string; name: string }[] = (currentSectorData as any)?.children || []

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

  // Group questionnaire items by dimension
  const allItems = questionnaireQuery.data || []
  const grouped = allItems.reduce(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (acc: Record<string, any[]>, item: any) => {
      acc[item.dimension] = acc[item.dimension] || []
      acc[item.dimension].push(item)
      return acc
    },
    {} as Record<string, unknown[]>
  )

  // Derive dimensions dynamically (preserves order)
  const dimensions: { key: string; label: string }[] = []
  const seenDims = new Set<string>()
  for (const item of allItems) {
    if (!seenDims.has(item.dimension)) {
      seenDims.add(item.dimension)
      dimensions.push({
        key: item.dimension,
        label: item.dimension_label || item.dimension,
      })
    }
  }

  const useNewFormat = allItems.length > 0 && isNewFormat(allItems)

  // Count completion for progress indicator
  const totalItems = allItems.length
  const completedItems = allItems.filter(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (it: any) => responses[it.item_id] || evidenceIds.has(it.item_id)
  ).length

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
            Evaluate your project across {dimensions.length || 5} readiness dimensions
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
          {children.length > 0 && (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-5">
              <h3 className="font-semibold text-gray-900 mb-2">
                Healthcare Sub-Sector
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                Select your facility type for a tailored readiness assessment
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {children.map((child) => {
                  const Icon = SUB_SECTOR_ICONS[child.id] || Building2
                  const isActive = subSector === child.id
                  return (
                    <button
                      key={child.id}
                      type="button"
                      onClick={() => setSubSector(isActive ? null : child.id)}
                      className={`flex flex-col items-center text-center gap-2 rounded-lg border-2 p-4 transition-all ${
                        isActive
                          ? 'border-primary-500 bg-primary-50 shadow-sm'
                          : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      <Icon
                        className={`h-6 w-6 ${isActive ? 'text-primary-600' : 'text-gray-400'}`}
                      />
                      <div>
                        <div
                          className={`text-sm font-semibold ${isActive ? 'text-primary-900' : 'text-gray-700'}`}
                        >
                          {child.name}
                        </div>
                        {SUB_SECTOR_DESCRIPTIONS[child.id] && (
                          <div className="text-xs text-gray-500 mt-0.5">
                            {SUB_SECTOR_DESCRIPTIONS[child.id]}
                          </div>
                        )}
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>
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

          {/* Progress indicator */}
          {totalItems > 0 && (
            <div className="flex items-center justify-between bg-white rounded-lg border border-gray-200 shadow-sm px-6 py-3 mb-5">
              <span className="text-sm text-gray-600">
                Readiness Checklist Progress
              </span>
              <div className="flex items-center gap-3">
                <div className="w-32 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full transition-all"
                    style={{ width: `${(completedItems / totalItems) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-700">
                  {completedItems}/{totalItems}
                </span>
              </div>
            </div>
          )}

          {/* Questionnaire Dimensions */}
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
              return (
                <div
                  key={dim.key}
                  className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-5"
                >
                  <h3 className="font-semibold text-gray-900 text-base mb-5">
                    {dim.label}
                    <span className="text-xs font-normal text-gray-400 ml-2">
                      {items.length} items
                    </span>
                  </h3>

                  {useNewFormat ? (
                    <CategoryGroupedItems
                      items={items}
                      responses={responses}
                      toggleResponse={toggleResponse}
                    />
                  ) : (
                    <LegacyItems
                      items={items}
                      responses={responses}
                      evidenceIds={evidenceIds}
                      toggleResponse={toggleResponse}
                      toggleEvidence={toggleEvidence}
                    />
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
