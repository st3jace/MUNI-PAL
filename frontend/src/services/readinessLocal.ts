/**
 * Client-side readiness scoring — fallback when sensing API is unavailable.
 *
 * Loads questionnaire JSON from /data/ and scores locally,
 * mirroring the backend _score_readiness_from_seed() logic.
 */

// Healthcare sub-sector metadata (mirrors backend _HEALTHCARE_SUB_SECTORS)
const HEALTHCARE_SUB_SECTORS: Record<string, { id: string; name: string; coiKey: string }> = {
  healthcare_hospital: { id: 'healthcare_hospital', name: 'Hospital / Health System', coiKey: 'hospital' },
  healthcare_senior_living: { id: 'healthcare_senior_living', name: 'Senior Living / CCRC', coiKey: 'senior_living' },
  healthcare_fqhc_bond: { id: 'healthcare_fqhc_bond', name: 'FQHC Revenue Bond', coiKey: 'fqhc_bond' },
  healthcare_fqhc_cdfi: { id: 'healthcare_fqhc_cdfi', name: 'FQHC CDFI / NMTC', coiKey: 'fqhc_cdfi' },
}

interface QuestionnaireItem {
  item_id: string
  dimension: string
  dimension_label: string
  category: string
  question: string
  help_text: string
  points: number
  lead_time: string
  agent_assistable: boolean
  coi_impact: string
}

interface CoiBenchmark {
  total_items: number
  required_items: number
  agent_assistable_pct: number
  baseline_weeks_min: number
  baseline_weeks_max: number
  compressed_weeks_min: number
  compressed_weeks_max: number
  timeline_compression_pct: number
  coi_gap_cost_min: number
  coi_gap_cost_max: number
  agent_displacement_per_deal: number
  category_weights: Record<string, number>
}

// Cache loaded data
const questionnaireCache = new Map<string, QuestionnaireItem[]>()
let coiBenchmarksCache: Record<string, CoiBenchmark> | null = null

async function loadQuestionnaire(sector: string): Promise<QuestionnaireItem[]> {
  if (questionnaireCache.has(sector)) return questionnaireCache.get(sector)!
  const resp = await fetch(`/data/questionnaire_${sector}.json`)
  if (!resp.ok) {
    // Fallback to generic healthcare
    const fallback = await fetch('/data/questionnaire_healthcare.json')
    if (!fallback.ok) throw new Error('Failed to load questionnaire data')
    const data = await fallback.json()
    questionnaireCache.set(sector, data)
    return data
  }
  const data = await resp.json()
  questionnaireCache.set(sector, data)
  return data
}

async function loadCoiBenchmarks(): Promise<Record<string, CoiBenchmark>> {
  if (coiBenchmarksCache) return coiBenchmarksCache
  const resp = await fetch('/data/coi_benchmarks_healthcare.json')
  if (!resp.ok) return {}
  coiBenchmarksCache = await resp.json()
  return coiBenchmarksCache!
}

/**
 * Static sector list for standalone mode (no backend needed).
 */
export function getLocalSectors() {
  return [
    {
      id: 'healthcare',
      name: 'Healthcare',
      children: Object.values(HEALTHCARE_SUB_SECTORS).map((s) => ({
        id: s.id,
        name: s.name,
      })),
    },
  ]
}

/**
 * Load questionnaire items from static JSON files.
 */
export async function getLocalQuestionnaire(sector: string): Promise<QuestionnaireItem[]> {
  return loadQuestionnaire(sector)
}

/**
 * Score readiness assessment client-side.
 * Mirrors backend _score_readiness_from_seed() logic.
 */
export async function scoreReadinessLocal(params: {
  sector: string
  project_name: string
  responses: Record<string, boolean>
  evidence_ids: string[]
  dscr?: number
  revenue?: number
  coverage_ratio?: number
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
}): Promise<any> {
  const questionnaire = await loadQuestionnaire(params.sector)
  const coiBenchmarks = await loadCoiBenchmarks()
  const subMeta = HEALTHCARE_SUB_SECTORS[params.sector]
  const coiData = subMeta ? coiBenchmarks[subMeta.coiKey] : undefined
  const categoryWeights = coiData?.category_weights

  // Group items by dimension
  const dims = new Map<string, QuestionnaireItem[]>()
  for (const item of questionnaire) {
    if (!dims.has(item.dimension)) dims.set(item.dimension, [])
    dims.get(item.dimension)!.push(item)
  }

  let totalScore = 0
  let totalMax = 0
  let requiredTotal = 0
  let requiredCompleted = 0
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const dimScores: any[] = []
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const gapAnalysis: any[] = []

  for (const [dimKey, items] of dims) {
    let dimMax: number
    let dimEarned: number

    if (categoryWeights) {
      dimMax = items.reduce((s, it) => s + it.points * (categoryWeights[it.category] ?? 1), 0)
      dimEarned = items.reduce(
        (s, it) => s + (params.responses[it.item_id] ? it.points * (categoryWeights[it.category] ?? 1) : 0),
        0,
      )
    } else {
      dimMax = items.reduce((s, it) => s + it.points, 0)
      dimEarned = items.reduce((s, it) => s + (params.responses[it.item_id] ? it.points : 0), 0)
    }

    for (const it of items) {
      if (it.category === 'required') {
        requiredTotal++
        if (params.responses[it.item_id]) requiredCompleted++
      }
    }

    const pct = dimMax > 0 ? (dimEarned / dimMax) * 100 : 0
    totalScore += dimEarned
    totalMax += dimMax

    const evidenceItems = items.filter((it) => it.category === 'evidence')

    dimScores.push({
      dimension: dimKey,
      display_name: items[0]?.dimension_label || dimKey,
      score: Math.round(dimEarned * 10) / 10,
      max_score: dimMax,
      pct: Math.round(pct * 10) / 10,
      description_provided: false,
      mitigants_provided: false,
      evidence_count: evidenceItems.filter((it) => params.responses[it.item_id]).length,
      evidence_total: evidenceItems.length,
    })

    const severity = pct >= 60 ? 'acceptable' : pct >= 30 ? 'material' : 'critical'
    if (severity !== 'acceptable') {
      gapAnalysis.push({
        dimension: dimKey,
        dimension_name: items[0]?.dimension_label || dimKey,
        severity,
        narrative: `Score ${pct.toFixed(0)}% — additional documentation needed.`,
        recommendations: items.filter((it) => !params.responses[it.item_id]).map((it) => it.question),
      })
    }
  }

  const rawPct = totalMax > 0 ? (totalScore / totalMax) * 100 : 0

  // Financial adjustment
  let finAdj = 0
  const finFlags: string[] = []
  if (params.dscr != null) {
    if (params.dscr >= 1.5) finAdj += 5
    else if (params.dscr >= 1.2) finAdj += 2
    else finFlags.push(`DSCR ${params.dscr.toFixed(2)}x below 1.2x threshold`)
  }

  const adjusted = Math.min(rawPct + finAdj, 100)
  const tier =
    adjusted >= 75 ? 'Bond Ready' : adjusted >= 50 ? 'Near Ready' : adjusted >= 25 ? 'Developing' : 'Early Stage'

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const result: any = {
    project_name: params.project_name,
    generated_at: new Date().toISOString(),
    sector: params.sector,
    readiness_score: Math.round(adjusted * 10) / 10,
    raw_score: Math.round(rawPct * 10) / 10,
    tier,
    tier_guidance: `Your project scored ${adjusted.toFixed(0)}% on the bond readiness assessment.`,
    dimensions_addressed: dimScores.filter((d) => d.pct >= 60).length,
    dimensions_partial: dimScores.filter((d) => d.pct > 0 && d.pct < 60).length,
    dimensions_missing: dimScores.filter((d) => d.pct === 0).length,
    evidence_present: dimScores.reduce((s, d) => s + d.evidence_count, 0),
    evidence_possible: dimScores.reduce((s, d) => s + d.evidence_total, 0),
    dimensions: dimScores,
    financial_assessment: {
      dscr_assessment: params.dscr ? `DSCR: ${params.dscr}` : 'Not provided',
      dscr_score: params.dscr ? finAdj : 0,
      coverage_assessment: params.coverage_ratio ? `Coverage ratio: ${params.coverage_ratio}` : 'Not provided',
      coverage_score: 0,
      revenue_assessment: params.revenue ? `Revenue: $${params.revenue.toLocaleString()}` : 'Not provided',
      revenue_score: 0,
      total_adjustment: finAdj,
      flags: finFlags,
    },
    priority_actions: gapAnalysis.slice(0, 3).map((g) => g.narrative),
    gap_analysis: gapAnalysis,
  }

  // Enhanced healthcare metrics
  if (coiData) {
    const requiredGapPct = requiredTotal > 0 ? 1 - requiredCompleted / requiredTotal : 0
    result.coi_estimate = {
      low: Math.round(coiData.coi_gap_cost_min * requiredGapPct),
      high: Math.round(coiData.coi_gap_cost_max * requiredGapPct),
      required_items_total: requiredTotal,
      required_items_completed: requiredCompleted,
      required_items_gap: requiredTotal - requiredCompleted,
    }
    result.timeline_baseline_weeks = [coiData.baseline_weeks_min, coiData.baseline_weeks_max]
    result.timeline_compressed_weeks = [coiData.compressed_weeks_min, coiData.compressed_weeks_max]
    result.timeline_compression_pct = coiData.timeline_compression_pct
    result.agent_displacement_value = coiData.agent_displacement_per_deal
  }

  return result
}
