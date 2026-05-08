import { useState, useEffect, useMemo } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Heart,
  Stethoscope,
  Clock,
  TrendingUp,
  BarChart3,
  Zap,
  ChevronRight,
  Mail,
  Lock,
  Loader2,
} from 'lucide-react'
import {
  type SubSector,
  type DealType,
  type FqhcTrack,
  type ReadinessItem,
  type AssessedItem,
  type AssessmentResult,
  type ItemStatus,
  filterItems,
  computeAssessment,
  responseToStatus,
} from '../../lib/readinessScoring'
import { sensingApi, getSensingSessionId } from '../../services/sensingApi'

// ── Types ──

type Step = 'facility' | 'fqhc_track' | 'deal_type' | 'assessment' | 'lead_gate' | 'results'
type Response = 'yes' | 'no' | 'partial' | 'na'

interface FrameworkData {
  items: ReadinessItem[]
}

// ── Facility options ──

const FACILITY_TYPES: { id: SubSector; label: string; description: string; icon: typeof Building2 }[] = [
  {
    id: 'hospital',
    label: 'Hospital / Health System',
    description: 'Acute care hospitals, health systems, and academic medical centers',
    icon: Building2,
  },
  {
    id: 'ccrc',
    label: 'Senior Living / CCRC',
    description: 'Continuing Care Retirement Communities and senior living facilities',
    icon: Heart,
  },
  {
    id: 'fqhc',
    label: 'FQHC / Community Health Center',
    description: 'Federally Qualified Health Centers and FQHC Look-Alikes',
    icon: Stethoscope,
  },
]

const DEAL_TYPES: { id: DealType; label: string; description: string }[] = [
  { id: 'new_money', label: 'New Construction / Expansion', description: 'New money bond for capital project' },
  { id: 'refunding', label: 'Refinancing Existing Debt', description: 'Refunding outstanding bonds' },
  { id: 'combined', label: 'Both New Money & Refunding', description: 'Combined new money and refunding' },
]

const FQHC_TRACKS: { id: FqhcTrack; label: string; description: string }[] = [
  { id: 'bond', label: 'Revenue Bonds / Bank Placement', description: 'For larger FQHCs ($50M+ revenue) considering conduit revenue bonds or private placement' },
  { id: 'cdfi_nmtc', label: 'CDFI / NMTC / Grant', description: 'For most FQHCs using non-bond capital sources — CDFI loans, NMTC, HRSA grants' },
]

// ── Component ──

export default function HealthcareReadiness() {
  const [step, setStep] = useState<Step>('facility')
  const [subSector, setSubSector] = useState<SubSector | null>(null)
  const [dealType, setDealType] = useState<DealType | null>(null)
  const [fqhcTrack, setFqhcTrack] = useState<FqhcTrack | undefined>()
  const [responses, setResponses] = useState<Record<string, Response>>({})
  const [numericValues, setNumericValues] = useState<Record<string, number>>({})
  const [framework, setFramework] = useState<FrameworkData | null>(null)
  const [result, setResult] = useState<AssessmentResult | null>(null)

  // Track page view
  useEffect(() => {
    sensingApi.trackEvent({
      session_id: getSensingSessionId(),
      event_type: 'page_view',
      event_data: JSON.stringify({ page: 'healthcare_readiness' }),
    })
  }, [])

  // Load framework data
  useEffect(() => {
    fetch('/data/healthcare_readiness_framework.json')
      .then((r) => r.json())
      .then((data) => setFramework(data))
      .catch(() => {
        // Fallback: framework will be null, show error
      })
  }, [])

  // Filter items based on selections
  const applicableItems = useMemo(() => {
    if (!framework || !subSector || !dealType) return []
    return filterItems(framework.items, subSector, dealType, fqhcTrack)
  }, [framework, subSector, dealType, fqhcTrack])

  // Get Required + Critical items for the quick assessment
  const assessmentItems = useMemo(() => {
    return applicableItems.filter(
      (item) => item.requirement === 'required' && ['critical', 'very_high', 'high'].includes(item.coiImpact),
    )
  }, [applicableItems])

  function handleFacilitySelect(fs: SubSector) {
    setSubSector(fs)
    setResponses({})
    setNumericValues({})
    setResult(null)
    if (fs === 'fqhc') {
      setStep('fqhc_track')
    } else {
      setStep('deal_type')
    }
  }

  function handleFqhcTrackSelect(track: FqhcTrack) {
    setFqhcTrack(track)
    setStep('deal_type')
  }

  function handleDealTypeSelect(dt: DealType) {
    setDealType(dt)
    setStep('assessment')
  }

  function handleResponse(itemId: string, value: Response) {
    setResponses((prev) => ({ ...prev, [itemId]: value }))
  }

  function handleNumericValue(itemId: string, value: string) {
    const num = parseFloat(value)
    if (!isNaN(num)) {
      setNumericValues((prev) => ({ ...prev, [itemId]: num }))
      // Auto-classify based on thresholds
      const item = assessmentItems.find((i) => i.id === itemId)
      if (item?.thresholds && subSector) {
        const t = item.thresholds[subSector]
        if (t) {
          if (num >= t.strong) handleResponse(itemId, 'yes')
          else if (num >= t.adequate) handleResponse(itemId, 'partial')
          else handleResponse(itemId, 'no')
        }
      }
    }
  }

  function computeResults() {
    if (!subSector || !dealType) return

    const assessed: AssessedItem[] = applicableItems.map((item) => {
      const resp = responses[item.id]
      const status: ItemStatus = resp ? responseToStatus(resp) : 'missing'
      return { item, status, numericValue: numericValues[item.id] }
    })

    const assessmentResult = computeAssessment(assessed)
    setResult(assessmentResult)

    // Track scoring event
    sensingApi.trackEvent({
      session_id: getSensingSessionId(),
      event_type: 'readiness_scored',
      sector: subSector,
      event_data: JSON.stringify({
        score: assessmentResult.overallScore,
        tier: assessmentResult.tier.label,
        subSector,
        dealType,
      }),
    })

    setStep('lead_gate')
  }

  function reset() {
    setStep('facility')
    setSubSector(null)
    setDealType(null)
    setFqhcTrack(undefined)
    setResponses({})
    setNumericValues({})
    setResult(null)
  }

  const answeredCount = Object.keys(responses).length
  const totalQuestions = assessmentItems.length
  const progress = totalQuestions > 0 ? Math.round((answeredCount / totalQuestions) * 100) : 0

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link to="/healthcare" className="text-gray-400 hover:text-gray-600 transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-gray-900">Healthcare Bond Readiness Assessment</h1>
          <p className="text-sm text-gray-500">
            Score your facility across critical readiness dimensions in about 10 minutes
          </p>
        </div>
      </div>

      {/* Step indicator */}
      {step !== 'results' && (
        <div className="flex items-center gap-2 mb-8">
          {(['facility', 'deal_type', 'assessment'] as Step[]).map((s, i) => {
            const labels = ['Facility Type', 'Deal Type', 'Quick Assessment']
            const stepOrder = ['facility', 'fqhc_track', 'deal_type', 'assessment']
            const stepIndex = stepOrder.indexOf(step)
            const thresholds = [0, 2, 3]
            const isActive = stepIndex >= thresholds[i]
            return (
              <div key={s} className="flex items-center gap-2">
                {i > 0 && <div className={`w-8 h-px ${isActive ? 'bg-[#2DAEAC]' : 'bg-gray-200'}`} />}
                <div
                  className={`flex items-center gap-1.5 text-xs font-medium ${
                    isActive ? 'text-[#2DAEAC]' : 'text-gray-400'
                  }`}
                >
                  <span
                    className={`inline-flex items-center justify-center h-5 w-5 rounded-full text-[10px] font-bold ${
                      isActive ? 'bg-[#2DAEAC] text-white' : 'bg-gray-200 text-gray-400'
                    }`}
                  >
                    {i + 1}
                  </span>
                  <span className="hidden sm:inline">{labels[i]}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Step 1: Facility Type */}
      {step === 'facility' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">What type of healthcare organization are you?</h2>
          <p className="text-sm text-gray-500 mb-6">
            This determines which readiness framework and scoring criteria apply to your facility.
          </p>
          <div className="grid gap-4 sm:grid-cols-3">
            {FACILITY_TYPES.map((ft) => (
              <button
                key={ft.id}
                onClick={() => handleFacilitySelect(ft.id)}
                className="text-left bg-white rounded-lg border-2 border-gray-200 p-5 hover:border-[#2DAEAC] hover:shadow-md transition-all group"
              >
                <div className="h-10 w-10 rounded-lg bg-muni-navy flex items-center justify-center mb-3">
                  <ft.icon className="h-5 w-5 text-[#2DAEAC]" />
                </div>
                <h3 className="text-sm font-semibold text-gray-900 group-hover:text-[#2DAEAC] transition-colors mb-1">
                  {ft.label}
                </h3>
                <p className="text-xs text-gray-500">{ft.description}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 1b: FQHC Track */}
      {step === 'fqhc_track' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Which financing track are you considering?</h2>
          <p className="text-sm text-gray-500 mb-6">
            FQHCs have two primary capital access pathways with different readiness criteria.
          </p>
          <div className="grid gap-4 sm:grid-cols-2">
            {FQHC_TRACKS.map((track) => (
              <button
                key={track.id}
                onClick={() => handleFqhcTrackSelect(track.id)}
                className="text-left bg-white rounded-lg border-2 border-gray-200 p-5 hover:border-[#2DAEAC] hover:shadow-md transition-all group"
              >
                <h3 className="text-sm font-semibold text-gray-900 group-hover:text-[#2DAEAC] transition-colors mb-1">
                  {track.label}
                </h3>
                <p className="text-xs text-gray-500">{track.description}</p>
              </button>
            ))}
          </div>
          <button onClick={() => setStep('facility')} className="mt-4 text-xs text-gray-400 hover:text-gray-600">
            &larr; Back to facility selection
          </button>
        </div>
      )}

      {/* Step 2: Deal Type */}
      {step === 'deal_type' && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">What is your primary financing objective?</h2>
          <p className="text-sm text-gray-500 mb-6">
            This determines which capital project items are included in your assessment.
          </p>
          <div className="grid gap-4 sm:grid-cols-3">
            {DEAL_TYPES.map((dt) => (
              <button
                key={dt.id}
                onClick={() => handleDealTypeSelect(dt.id)}
                className="text-left bg-white rounded-lg border-2 border-gray-200 p-5 hover:border-[#2DAEAC] hover:shadow-md transition-all group"
              >
                <h3 className="text-sm font-semibold text-gray-900 group-hover:text-[#2DAEAC] transition-colors mb-1">
                  {dt.label}
                </h3>
                <p className="text-xs text-gray-500">{dt.description}</p>
              </button>
            ))}
          </div>
          <button
            onClick={() => setStep(subSector === 'fqhc' ? 'fqhc_track' : 'facility')}
            className="mt-4 text-xs text-gray-400 hover:text-gray-600"
          >
            &larr; Back
          </button>
        </div>
      )}

      {/* Step 3: Quick Assessment */}
      {step === 'assessment' && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Quick Assessment</h2>
              <p className="text-sm text-gray-500">
                Answer these {totalQuestions} critical-path questions about your facility's readiness.
              </p>
            </div>
            <div className="text-right">
              <span className="text-2xl font-bold text-[#2DAEAC]">{answeredCount}</span>
              <span className="text-sm text-gray-400">/{totalQuestions}</span>
              <div className="w-24 h-1.5 bg-gray-200 rounded-full mt-1">
                <div
                  className="h-full bg-[#2DAEAC] rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>

          {/* Group by category */}
          {(() => {
            const grouped = new Map<string, ReadinessItem[]>()
            for (const item of assessmentItems) {
              if (!grouped.has(item.category)) grouped.set(item.category, [])
              grouped.get(item.category)!.push(item)
            }
            return Array.from(grouped.entries()).map(([catId, items]) => (
              <div key={catId} className="mb-8">
                <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide flex items-center gap-2">
                  <div className="h-1.5 w-1.5 rounded-full bg-[#2DAEAC]" />
                  {items[0]?.category && getCategoryLabel(items[0].category)}
                </h3>
                <div className="space-y-3">
                  {items.map((item) => (
                    <QuestionCard
                      key={item.id}
                      item={item}
                      response={responses[item.id]}
                      numericValue={numericValues[item.id]}
                      subSector={subSector!}
                      onResponse={(v) => handleResponse(item.id, v)}
                      onNumericChange={(v) => handleNumericValue(item.id, v)}
                    />
                  ))}
                </div>
              </div>
            ))
          })()}

          <div className="flex items-center justify-between pt-6 border-t border-gray-100">
            <button onClick={() => setStep('deal_type')} className="text-sm text-gray-400 hover:text-gray-600">
              &larr; Back
            </button>
            <button
              onClick={computeResults}
              disabled={answeredCount < 3}
              className="inline-flex items-center gap-2 bg-[#E8913A] hover:bg-[#d47e2e] disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-semibold px-6 py-3 rounded-lg transition-colors"
            >
              See Your Readiness Score
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>

          {answeredCount < 3 && (
            <p className="text-xs text-gray-400 text-right mt-2">Answer at least 3 questions to see results</p>
          )}
        </div>
      )}

      {/* Step 4: Lead Capture Gate */}
      {step === 'lead_gate' && result && (
        <LeadCaptureGate
          result={result}
          subSector={subSector!}
          dealType={dealType!}
          onUnlock={() => {
            sensingApi.trackEvent({
              session_id: getSensingSessionId(),
              event_type: 'readiness_results_unlocked',
              sector: subSector!,
            })
            setStep('results')
          }}
          onSkip={() => setStep('results')}
        />
      )}

      {/* Step 5: Results */}
      {step === 'results' && result && (
        <ResultsView result={result} subSector={subSector!} onReset={reset} />
      )}
    </div>
  )
}

// ── Sub-components ──

function getCategoryLabel(catId: string): string {
  const labels: Record<string, string> = {
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
  return labels[catId] || catId
}

function QuestionCard({
  item,
  response,
  numericValue,
  subSector,
  onResponse,
  onNumericChange,
}: {
  item: ReadinessItem
  response?: Response
  numericValue?: number
  subSector: SubSector
  onResponse: (v: Response) => void
  onNumericChange: (v: string) => void
}) {
  const impactColors: Record<string, string> = {
    critical: 'bg-red-100 text-red-700',
    very_high: 'bg-orange-100 text-orange-700',
    high: 'bg-amber-100 text-amber-700',
    medium: 'bg-gray-100 text-gray-600',
    low: 'bg-gray-50 text-gray-500',
  }

  return (
    <div
      className={`bg-white rounded-lg border p-4 transition-all ${
        response ? 'border-gray-200' : 'border-gray-100'
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1.5">
            <span
              className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${impactColors[item.coiImpact]}`}
            >
              {item.coiImpact === 'very_high' ? 'VERY HIGH' : item.coiImpact.toUpperCase()} COI IMPACT
            </span>
            {item.leadTimeWeeks > 0 && (
              <span className="text-[10px] text-gray-400 flex items-center gap-0.5">
                <Clock className="h-3 w-3" />
                {item.leadTimeWeeks}w lead time
              </span>
            )}
            {item.agentAssistable !== 'no' && (
              <span className="text-[10px] text-[#2DAEAC] flex items-center gap-0.5">
                <Zap className="h-3 w-3" />
                Agent-assistable
              </span>
            )}
          </div>
          <p className="text-sm text-gray-800">{item.question}</p>

          {/* Numeric input for DCOH/DSCR */}
          {item.inputType === 'number' && (
            <div className="mt-2">
              <input
                type="number"
                placeholder={item.id.includes('DCOH') ? 'e.g., 150' : 'e.g., 1.75'}
                value={numericValue ?? ''}
                onChange={(e) => onNumericChange(e.target.value)}
                className="input w-32 text-sm"
                step={item.id.includes('DSCR') ? '0.01' : '1'}
              />
              {numericValue !== undefined && item.thresholds?.[subSector] && (
                <span
                  className={`ml-2 text-xs font-medium ${
                    numericValue >= item.thresholds[subSector].strong
                      ? 'text-green-600'
                      : numericValue >= item.thresholds[subSector].adequate
                        ? 'text-amber-600'
                        : 'text-red-600'
                  }`}
                >
                  {numericValue >= item.thresholds[subSector].strong
                    ? 'Strong'
                    : numericValue >= item.thresholds[subSector].adequate
                      ? 'Adequate'
                      : 'Below threshold'}
                </span>
              )}
            </div>
          )}
        </div>

        {/* Response buttons */}
        <div className="flex gap-1.5 flex-shrink-0">
          {(['yes', 'partial', 'no'] as Response[]).map((r) => {
            const labels = { yes: 'Yes', partial: 'Partial', no: 'No', na: 'N/A' }
            const colors = {
              yes: response === r ? 'bg-green-500 text-white border-green-500' : 'bg-white text-green-700 border-green-200 hover:border-green-400',
              partial: response === r ? 'bg-amber-500 text-white border-amber-500' : 'bg-white text-amber-700 border-amber-200 hover:border-amber-400',
              no: response === r ? 'bg-red-500 text-white border-red-500' : 'bg-white text-red-700 border-red-200 hover:border-red-400',
              na: response === r ? 'bg-gray-500 text-white border-gray-500' : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400',
            }
            return (
              <button
                key={r}
                onClick={() => onResponse(r)}
                className={`text-xs font-medium px-2.5 py-1.5 rounded border transition-all ${colors[r]}`}
              >
                {labels[r]}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function LeadCaptureGate({
  result,
  subSector,
  dealType,
  onUnlock,
  onSkip,
}: {
  result: AssessmentResult
  subSector: SubSector
  dealType: DealType
  onUnlock: () => void
  onSkip: () => void
}) {
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [organization, setOrganization] = useState('')
  const [title, setTitle] = useState('')
  const [privacyConsent, setPrivacyConsent] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const sectorLabel = { hospital: 'Hospital', ccrc: 'Senior Living / CCRC', fqhc: 'FQHC' }[subSector]

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      await sensingApi.captureLead({
        email,
        name,
        organization,
        title: title || undefined,
        sector: `healthcare_${subSector}`,
        session_id: getSensingSessionId(),
        privacy_consent: privacyConsent,
        consent_version: 'sensing-lead-v1',
        readiness_json: JSON.stringify({
          overallScore: result.overallScore,
          tier: result.tier.label,
          subSector,
          dealType,
          categoryScores: result.categoryScores,
          criticalPathWeeks: result.criticalPathWeeks,
          gapCount: result.gaps.length,
        }),
      })

      sensingApi.trackEvent({
        session_id: getSensingSessionId(),
        event_type: 'readiness_lead_captured',
        sector: subSector,
        event_data: JSON.stringify({ email_domain: email.split('@')[1] }),
      })

      onUnlock()
    } catch {
      setError('Something went wrong. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div>
      {/* Score teaser */}
      <div
        className="rounded-2xl p-8 text-white mb-8"
        style={{ background: `linear-gradient(135deg, #1B3A5C 0%, ${result.tier.color}33 100%)` }}
      >
        <p className="text-sm font-medium text-gray-300 mb-1">{sectorLabel} Bond Readiness Score</p>
        <div className="flex items-end gap-4 mb-4">
          <span className="text-5xl font-bold">{result.overallScore}%</span>
          <span
            className="text-sm font-bold px-3 py-1 rounded-full mb-1"
            style={{ backgroundColor: result.tier.color }}
          >
            {result.tier.label}
          </span>
        </div>
        <div className="relative w-full h-3 bg-white/20 rounded-full overflow-hidden mb-4">
          <div
            className="absolute inset-y-0 left-0 rounded-full transition-all duration-1000"
            style={{ width: `${result.overallScore}%`, backgroundColor: result.tier.color }}
          />
          {[50, 75, 90].map((mark) => (
            <div
              key={mark}
              className="absolute top-0 bottom-0 w-px bg-white/40"
              style={{ left: `${mark}%` }}
            />
          ))}
        </div>
        <p className="text-sm text-gray-300">
          Your assessment identified <span className="font-semibold text-white">{result.gaps.length} readiness gaps</span> across {result.categoryScores.length} categories.
        </p>
      </div>

      {/* Email gate */}
      <div className="bg-white rounded-xl border-2 border-[#2DAEAC]/30 p-6 md:p-8 mb-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="h-12 w-12 rounded-xl bg-[#2DAEAC] flex items-center justify-center flex-shrink-0">
            <Mail className="h-6 w-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900 mb-1">
              Get Your Full Readiness Report
            </h2>
            <p className="text-sm text-gray-600">
              See your category-by-category breakdown, top gaps ranked by COI impact,
              critical path timeline, and actionable next steps.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="lead-name" className="block text-xs font-medium text-gray-700 mb-1">Name *</label>
              <input
                id="lead-name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Jane Smith"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#2DAEAC] focus:border-[#2DAEAC] outline-none"
              />
            </div>
            <div>
              <label htmlFor="lead-email" className="block text-xs font-medium text-gray-700 mb-1">Work Email *</label>
              <input
                id="lead-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jane@hospital.org"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#2DAEAC] focus:border-[#2DAEAC] outline-none"
              />
            </div>
            <div>
              <label htmlFor="lead-org" className="block text-xs font-medium text-gray-700 mb-1">Organization *</label>
              <input
                id="lead-org"
                type="text"
                required
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                placeholder="Community Health System"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#2DAEAC] focus:border-[#2DAEAC] outline-none"
              />
            </div>
            <div>
              <label htmlFor="lead-title" className="block text-xs font-medium text-gray-700 mb-1">Title</label>
              <input
                id="lead-title"
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="CFO"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-[#2DAEAC] focus:border-[#2DAEAC] outline-none"
              />
            </div>
          </div>

          <label className="flex items-start gap-3 text-xs text-gray-600">
            <input
              type="checkbox"
              className="mt-0.5"
              checked={privacyConsent}
              onChange={(e) => setPrivacyConsent(e.target.checked)}
              required
            />
            <span>
              I consent to Muni-Pal collecting my contact details, organization context,
              readiness snapshot, and session context to prepare this report and evaluate pilot fit.
              Outputs are screening artifacts, not legal advice, municipal advisory advice, deal approval,
              pricing, sizing, or issuance instructions.
            </span>
          </label>

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <div className="flex items-center justify-between pt-2">
            <p className="text-[11px] text-gray-400 flex items-center gap-1">
              <Lock className="h-3 w-3" />
              We never share your information. Used only for your readiness report.
            </p>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 bg-[#E8913A] hover:bg-[#d47e2e] disabled:bg-gray-300 text-white font-semibold px-6 py-3 rounded-lg transition-colors"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  Unlock Full Report
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      <button
        onClick={onSkip}
        className="w-full text-center text-xs text-gray-400 hover:text-gray-600 transition-colors py-2"
      >
        Skip for now &mdash; view summary results
      </button>
    </div>
  )
}

function ResultsView({
  result,
  subSector,
  onReset,
}: {
  result: AssessmentResult
  subSector: SubSector
  onReset: () => void
}) {
  const sectorLabel = { hospital: 'Hospital', ccrc: 'Senior Living / CCRC', fqhc: 'FQHC' }[subSector]

  return (
    <div>
      {/* Score Hero */}
      <div
        className="rounded-2xl p-8 text-white mb-8"
        style={{ background: `linear-gradient(135deg, #1B3A5C 0%, ${result.tier.color}33 100%)` }}
      >
        <p className="text-sm font-medium text-gray-300 mb-1">{sectorLabel} Bond Readiness Score</p>
        <div className="flex items-end gap-4 mb-4">
          <span className="text-5xl font-bold">{result.overallScore}%</span>
          <span
            className="text-sm font-bold px-3 py-1 rounded-full mb-1"
            style={{ backgroundColor: result.tier.color }}
          >
            {result.tier.label}
          </span>
        </div>

        {/* Score gauge */}
        <div className="relative w-full h-3 bg-white/20 rounded-full overflow-hidden mb-4">
          <div
            className="absolute inset-y-0 left-0 rounded-full transition-all duration-1000"
            style={{ width: `${result.overallScore}%`, backgroundColor: result.tier.color }}
          />
          {/* Tier markers */}
          {[50, 75, 90].map((mark) => (
            <div
              key={mark}
              className="absolute top-0 bottom-0 w-px bg-white/40"
              style={{ left: `${mark}%` }}
            />
          ))}
        </div>
        <div className="flex justify-between text-[10px] text-gray-400">
          <span>Pre-Preparation</span>
          <span>Preparation</span>
          <span>Near-Ready</span>
          <span>Advisor Review</span>
        </div>
      </div>

      {/* Key metrics */}
      <div className="grid gap-4 sm:grid-cols-3 mb-8">
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
            <Clock className="h-3.5 w-3.5" />
            Critical Path
          </div>
          <p className="text-lg font-bold text-gray-900">
            {result.criticalPathWeeks > 0 ? `${result.criticalPathWeeks} weeks` : 'No critical gaps'}
          </p>
          {result.agentAssistedWeeks > 0 && (
            <p className="text-xs text-[#2DAEAC] flex items-center gap-1 mt-0.5">
              <Zap className="h-3 w-3" />
              ~{result.agentAssistedWeeks} weeks with agent assistance
            </p>
          )}
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
            <BarChart3 className="h-3.5 w-3.5" />
            Items Assessed
          </div>
          <p className="text-lg font-bold text-gray-900">{result.totalApplicableItems}</p>
          <p className="text-xs text-gray-400">across {result.categoryScores.length} categories</p>
        </div>
        <div className="bg-white rounded-lg border border-gray-200 p-4">
          <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
            <TrendingUp className="h-3.5 w-3.5" />
            Timeline Estimate
          </div>
          <p className="text-lg font-bold text-gray-900">{result.tier.agentWeeks} weeks</p>
          <p className="text-xs text-gray-400">to advisor-review-ready (agent-assisted)</p>
        </div>
      </div>

      {/* Category breakdown */}
      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Category Breakdown</h3>
        <div className="space-y-3">
          {result.categoryScores.map((cat) => {
            const pct = Math.round(cat.percentage)
            const barColor = pct >= 90 ? '#22c55e' : pct >= 75 ? '#eab308' : pct >= 50 ? '#f97316' : '#ef4444'
            return (
              <div key={cat.categoryId}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-gray-700 font-medium">{cat.label}</span>
                  <span className="font-semibold" style={{ color: barColor }}>
                    {pct}%
                  </span>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-700"
                    style={{ width: `${pct}%`, backgroundColor: barColor }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Top gaps */}
      {result.gaps.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <h3 className="text-sm font-semibold text-gray-900 mb-1">Top Readiness Gaps</h3>
          <p className="text-xs text-gray-500 mb-4">
            Ranked by readiness impact weight — addressing these first should strengthen the evidence package for advisor and deal-team review.
          </p>
          <div className="space-y-2">
            {result.gaps.slice(0, 5).map((gap, i) => {
              const statusLabels: Record<string, string> = { missing: 'Missing', partial: 'Partial', in_progress: 'In Progress', complete: 'Complete', na: 'N/A' }
              const statusColors: Record<string, string> = { missing: 'text-red-600 bg-red-50', partial: 'text-amber-600 bg-amber-50', in_progress: 'text-blue-600 bg-blue-50', complete: 'text-green-600 bg-green-50', na: 'text-gray-600 bg-gray-50' }
              const statusLabel = statusLabels[gap.status] || gap.status
              const statusColor = statusColors[gap.status] || 'text-gray-600 bg-gray-50'
              return (
                <div key={gap.item.id} className="flex items-start gap-3 p-3 rounded-lg bg-gray-50">
                  <span className="flex-shrink-0 inline-flex items-center justify-center h-5 w-5 rounded-full bg-red-100 text-red-600 text-[10px] font-bold">
                    {i + 1}
                  </span>
                  <div className="flex-1">
                    <p className="text-sm text-gray-800 font-medium">{gap.item.name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${statusColor}`}>
                        {statusLabel}
                      </span>
                      {gap.item.leadTimeWeeks > 0 && (
                        <span className="text-[10px] text-gray-400">
                          {gap.item.leadTimeWeeks}w to resolve
                        </span>
                      )}
                      {gap.item.agentAssistable !== 'no' && (
                        <span className="text-[10px] text-[#2DAEAC] flex items-center gap-0.5">
                          <Zap className="h-2.5 w-2.5" /> Accelerable
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className="text-xs font-semibold text-red-600">
                      {gap.effectiveWeight.toFixed(1)} pts
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* CTA */}
      <div className="bg-muni-navy rounded-lg p-8 text-white text-center mb-8">
        <h3 className="text-lg font-bold mb-2">Ready to Organize Your Gaps for Review?</h3>
        <p className="text-sm text-gray-300 mb-6 max-w-lg mx-auto">
          Our Bond Readiness Accelerator helps organize document preparation, gap analysis, and registered advisor coordination; it does not replace professional judgment or transaction advice.
        </p>
        <div className="flex flex-col sm:flex-row justify-center gap-3">
          <a
            href="mailto:hello@muni-pal.io?subject=Bond%20Readiness%20Assessment%20Follow-Up"
            className="inline-flex items-center justify-center gap-2 bg-[#E8913A] hover:bg-[#d47e2e] text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            Talk to a Readiness Specialist
            <ChevronRight className="h-4 w-4" />
          </a>
          <button
            onClick={onReset}
            className="inline-flex items-center justify-center gap-2 border border-white/30 hover:border-white/60 text-white font-medium px-6 py-3 rounded-lg transition-colors"
          >
            Start New Assessment
          </button>
        </div>
      </div>

      {/* Disclaimer */}
      <p className="text-[11px] text-gray-400 text-center mb-6">
        This assessment is for educational and analytical purposes only. It does not constitute municipal
        advisory services as defined under Section 15B of the Securities Exchange Act. Scores are based on
        self-reported data and may differ from a comprehensive professional evaluation.
      </p>
    </div>
  )
}
