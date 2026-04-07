/**
 * Healthcare Bond Readiness Scoring Engine
 *
 * Implements the scoring algorithm from the Readiness Researcher Phase 1 deliverables.
 * Computes item-level, category-level, and overall readiness scores with tier classification.
 */

// ── Types ──

export type SubSector = 'hospital' | 'ccrc' | 'fqhc'
export type DealType = 'new_money' | 'refunding' | 'combined'
export type FqhcTrack = 'bond' | 'cdfi_nmtc'
export type RequirementLevel = 'required' | 'recommended' | 'optional'
export type CoiImpact = 'critical' | 'very_high' | 'high' | 'medium' | 'low'
export type ItemStatus = 'complete' | 'partial' | 'in_progress' | 'missing' | 'na'

export interface ReadinessItem {
  id: string
  name: string
  category: string
  requirement: RequirementLevel
  coiImpact: CoiImpact
  leadTimeWeeks: number
  agentAssistable: 'yes' | 'partial' | 'no'
  subSectors: SubSector[]
  question: string
  inputType?: 'number'
  thresholds?: Record<string, { strong: number; adequate: number; concern: number }>
  conditional?: Record<string, unknown>
}

export interface AssessedItem {
  item: ReadinessItem
  status: ItemStatus
  numericValue?: number
}

export interface CategoryScore {
  categoryId: string
  label: string
  earned: number
  possible: number
  percentage: number
  itemCount: number
}

export interface TierInfo {
  id: string
  label: string
  minScore: number
  color: string
  baselineWeeks: string
  agentWeeks: string
  compression: string
}

export interface GapItem {
  item: ReadinessItem
  effectiveWeight: number
  potentialGain: number
  status: ItemStatus
}

export interface AssessmentResult {
  overallScore: number
  tier: TierInfo
  categoryScores: CategoryScore[]
  gaps: GapItem[]
  criticalPathWeeks: number
  agentAssistedWeeks: number
  totalApplicableItems: number
  totalAssessedItems: number
}

// ── Constants ──

const BASE_WEIGHTS: Record<RequirementLevel, number> = {
  required: 3,
  recommended: 1,
  optional: 0.5,
}

const COI_MULTIPLIERS: Record<CoiImpact, number> = {
  critical: 2.0,
  very_high: 1.5,
  high: 1.25,
  medium: 1.0,
  low: 1.0,
}

const STATUS_FACTORS: Record<ItemStatus, number> = {
  complete: 1.0,
  partial: 0.5,
  in_progress: 0.25,
  missing: 0.0,
  na: 0, // excluded from scoring
}

const TIERS: TierInfo[] = [
  { id: 'bond_ready', label: 'Bond-Ready', minScore: 90, color: '#22c55e', baselineWeeks: '0-2', agentWeeks: '0-1', compression: '50%' },
  { id: 'near_ready', label: 'Near-Ready', minScore: 75, color: '#eab308', baselineWeeks: '4-12', agentWeeks: '3-8', compression: '30-40%' },
  { id: 'preparation', label: 'Preparation Phase', minScore: 50, color: '#f97316', baselineWeeks: '12-24', agentWeeks: '8-16', compression: '30-35%' },
  { id: 'pre_preparation', label: 'Pre-Preparation', minScore: 0, color: '#ef4444', baselineWeeks: '24-52', agentWeeks: '16-36', compression: '30-35%' },
]

// ── Category labels ──

const CATEGORY_LABELS: Record<string, string> = {
  organizational_legal: 'Organizational & Legal',
  regulatory_licensing: 'Regulatory & Licensing',
  financial: 'Financial',
  operational: 'Clinical & Operational',
  capital_project: 'Capital Project',
  tax_compliance: 'Tax & Compliance',
  rating_market: 'Rating & Market Readiness',
  occupancy_demographic: 'Occupancy, Waitlist & Demographics',
  federal_compliance: 'Federal Compliance & HRSA',
  compliance_reporting: 'Compliance & Reporting',
  bond_specific: 'Revenue Bond Specific',
  cdfi_nmtc: 'CDFI/NMTC/Grant Specific',
}

// ── Core functions ──

export function effectiveWeight(item: ReadinessItem): number {
  return BASE_WEIGHTS[item.requirement] * COI_MULTIPLIERS[item.coiImpact]
}

export function itemScore(item: ReadinessItem, status: ItemStatus): number {
  if (status === 'na') return 0
  return effectiveWeight(item) * STATUS_FACTORS[status]
}

export function filterItems(
  items: ReadinessItem[],
  subSector: SubSector,
  dealType: DealType,
  fqhcTrack?: FqhcTrack,
): ReadinessItem[] {
  return items.filter((item) => {
    // Must match sub-sector
    if (!item.subSectors.includes(subSector)) return false

    // Skip capital project items for pure refunding
    if (dealType === 'refunding' && item.conditional?.deal_type === 'new_money') return false

    // FQHC track filtering
    if (subSector === 'fqhc' && fqhcTrack) {
      if (fqhcTrack === 'cdfi_nmtc' && item.conditional?.track === 'bond') return false
      if (fqhcTrack === 'bond' && item.conditional?.track === 'cdfi_nmtc') return false
    }

    return true
  })
}

export function classifyTier(score: number): TierInfo {
  for (const tier of TIERS) {
    if (score >= tier.minScore) return tier
  }
  return TIERS[TIERS.length - 1]
}

export function computeAssessment(assessedItems: AssessedItem[]): AssessmentResult {
  const applicable = assessedItems.filter((ai) => ai.status !== 'na')

  // Overall score
  const totalEarned = applicable.reduce((sum, ai) => sum + itemScore(ai.item, ai.status), 0)
  const totalPossible = applicable.reduce((sum, ai) => sum + effectiveWeight(ai.item), 0)
  const overallScore = totalPossible > 0 ? (totalEarned / totalPossible) * 100 : 0

  // Category scores
  const byCategory = new Map<string, AssessedItem[]>()
  for (const ai of applicable) {
    const cat = ai.item.category
    if (!byCategory.has(cat)) byCategory.set(cat, [])
    byCategory.get(cat)!.push(ai)
  }

  const categoryScores: CategoryScore[] = []
  for (const [catId, catItems] of byCategory) {
    const earned = catItems.reduce((s, ai) => s + itemScore(ai.item, ai.status), 0)
    const possible = catItems.reduce((s, ai) => s + effectiveWeight(ai.item), 0)
    categoryScores.push({
      categoryId: catId,
      label: CATEGORY_LABELS[catId] || catId,
      earned,
      possible,
      percentage: possible > 0 ? (earned / possible) * 100 : 0,
      itemCount: catItems.length,
    })
  }
  categoryScores.sort((a, b) => a.percentage - b.percentage) // worst first

  // Gaps: items that are missing or partial, sorted by COI impact weight
  const gaps: GapItem[] = applicable
    .filter((ai) => ai.status === 'missing' || ai.status === 'partial' || ai.status === 'in_progress')
    .map((ai) => ({
      item: ai.item,
      effectiveWeight: effectiveWeight(ai.item),
      potentialGain: effectiveWeight(ai.item) - itemScore(ai.item, ai.status),
      status: ai.status,
    }))
    .sort((a, b) => b.effectiveWeight - a.effectiveWeight)

  // Critical path: longest-lead Required item that is Missing or In Progress
  const criticalPathItems = applicable.filter(
    (ai) =>
      ai.item.requirement === 'required' &&
      (ai.status === 'missing' || ai.status === 'in_progress'),
  )
  const criticalPathWeeks =
    criticalPathItems.length > 0
      ? Math.max(...criticalPathItems.map((ai) => ai.item.leadTimeWeeks))
      : 0

  // Agent-assisted timeline: roughly 30-40% compression
  const agentAssistedWeeks = Math.ceil(criticalPathWeeks * 0.65)

  const tier = classifyTier(overallScore)

  return {
    overallScore: Math.round(overallScore * 10) / 10,
    tier,
    categoryScores,
    gaps: gaps.slice(0, 10), // top 10 gaps
    criticalPathWeeks,
    agentAssistedWeeks,
    totalApplicableItems: applicable.length,
    totalAssessedItems: assessedItems.length,
  }
}

/**
 * Convert user responses (yes/no/partial) into AssessedItem statuses.
 * For the quick assessment, "yes" = complete, "no" = missing, "partial" = partial.
 */
export function responseToStatus(response: 'yes' | 'no' | 'partial' | 'na'): ItemStatus {
  switch (response) {
    case 'yes': return 'complete'
    case 'no': return 'missing'
    case 'partial': return 'partial'
    case 'na': return 'na'
  }
}
