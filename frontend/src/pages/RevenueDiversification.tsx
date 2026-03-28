import { useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import {
  Download,
  ShieldAlert,
  TrendingUp,
  LineChart,
  Fuel,
  DollarSign,
  Columns3,
} from 'lucide-react'
import RevenueDiversificationChart from '../components/RevenueDiversificationChart'
import { api } from '../services/api'
import type {
  RevenueDiversificationVisualizationResponse,
  RevenueScenarioMix,
} from '../types'

type VisualizationMode = 'packet' | 'native' | 'compare'

function formatCurrency(value: number, maximumFractionDigits = 0): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits,
  }).format(value)
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

function getDieselShare(scenario?: RevenueScenarioMix): number {
  if (!scenario) {
    return 0
  }

  const diesel = scenario.revenue_streams.find((slice) => slice.stream_id === 'diesel')
  return diesel?.pct_of_total ?? 0
}

function getSafetyChipClasses(status: RevenueScenarioMix['safety_status']): string {
  if (status === 'fragile') {
    return 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-200'
  }
  if (status === 'fortress') {
    return 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200'
  }
  return 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-200'
}

function getScenarioNotes(
  visualization?: RevenueDiversificationVisualizationResponse
): RevenueScenarioMix[] {
  return visualization?.revenue_scenarios.filter((scenario) => scenario.assumptions.length > 0) ?? []
}

function ModeButton({
  label,
  active,
  onClick,
}: {
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition-colors ${
        active
          ? 'bg-slate-900 text-white shadow-sm'
          : 'bg-white text-slate-600 ring-1 ring-inset ring-slate-200 hover:bg-slate-50'
      }`}
    >
      {label}
    </button>
  )
}

function MetricCards({
  visualization,
}: {
  visualization: RevenueDiversificationVisualizationResponse
}) {
  const currentScenario = visualization.revenue_scenarios[0]
  const fullScenario =
    visualization.revenue_scenarios[visualization.revenue_scenarios.length - 1]
  const revenueLift = fullScenario.total_revenue - currentScenario.total_revenue
  const dscrLift = fullScenario.dscr_mean - currentScenario.dscr_mean

  return (
    <div className="mt-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-white p-2 text-slate-700 shadow-sm ring-1 ring-slate-200">
            <TrendingUp className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Revenue Lift
            </p>
            <p className="mt-1 text-lg font-semibold text-slate-950">
              {formatCurrency(revenueLift)}
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-white p-2 text-slate-700 shadow-sm ring-1 ring-slate-200">
            <LineChart className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              {visualization.non_diesel_combined_coverage_dscr
                ? 'Non-Diesel Coverage'
                : 'DSCR Expansion'}
            </p>
            <p className="mt-1 text-lg font-semibold text-slate-950">
              {visualization.non_diesel_combined_coverage_dscr
                ? `${visualization.non_diesel_combined_coverage_dscr.toFixed(2)}x combined`
                : `+${dscrLift.toFixed(2)}x`}
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-white p-2 text-slate-700 shadow-sm ring-1 ring-slate-200">
            <Fuel className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Diesel Share
            </p>
            <p className="mt-1 text-lg font-semibold text-slate-950">
              {formatPercent(getDieselShare(currentScenario))} to{' '}
              {formatPercent(getDieselShare(fullScenario))}
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-white p-2 text-slate-700 shadow-sm ring-1 ring-slate-200">
            <DollarSign className="h-4 w-4" />
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
              Annual Debt Service
            </p>
            <p className="mt-1 text-lg font-semibold text-slate-950">
              {formatCurrency(visualization.debt_service_annual)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

function DataQualityPanel({
  visualization,
  title = 'Data Quality Notes',
}: {
  visualization: RevenueDiversificationVisualizationResponse
  title?: string
}) {
  if (visualization.data_quality_notes.length === 0) {
    return null
  }

  return (
    <div className="rounded-[28px] border border-amber-200 bg-amber-50/70 p-6 shadow-[0_18px_48px_-38px_rgba(120,53,15,0.22)]">
      <div className="flex items-start gap-3">
        <div className="rounded-xl bg-white p-2 text-amber-700 ring-1 ring-amber-200">
          <ShieldAlert className="h-5 w-5" />
        </div>
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-amber-900">
            {title}
          </h2>
          <p className="mt-2 text-sm leading-6 text-amber-900/80">
            These notes explain where the visualization still depends on modeled scenario logic instead of fully evidenced future-state revenue streams.
          </p>
          <ul className="mt-3 space-y-2 text-sm leading-6 text-amber-950">
            {visualization.data_quality_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

function ScenarioNotesSection({
  visualization,
}: {
  visualization: RevenueDiversificationVisualizationResponse
}) {
  const scenarioNotes = getScenarioNotes(visualization)
  if (scenarioNotes.length === 0) {
    return null
  }

  return (
    <div className="rounded-[26px] border border-slate-200 bg-white p-6 shadow-[0_18px_50px_-38px_rgba(15,23,42,0.22)]">
      <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
        Scenario Notes
      </p>
      <h2 className="mt-2 text-xl font-semibold text-slate-950">
        Modeling Assumptions and Safety Posture
      </h2>

      <div className="mt-5 grid gap-4 xl:grid-cols-3">
        {scenarioNotes.map((scenario) => (
          <div
            key={scenario.scenario_id}
            className="rounded-[22px] border border-slate-200 bg-slate-50 p-5"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-slate-950">{scenario.label}</h3>
                <p className="mt-1 text-sm text-slate-600">
                  {scenario.implied_rating} implied rating
                </p>
              </div>
              <span
                className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] ${getSafetyChipClasses(
                  scenario.safety_status
                )}`}
              >
                {scenario.safety_label}
              </span>
            </div>

            <ul className="mt-4 space-y-2 text-sm leading-6 text-slate-600">
              {scenario.assumptions.map((assumption) => (
                <li key={assumption}>{assumption}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  )
}

function ComparisonSummary({
  packet,
  native,
}: {
  packet: RevenueDiversificationVisualizationResponse
  native: RevenueDiversificationVisualizationResponse
}) {
  const packetCurrent = packet.revenue_scenarios[0]
  const packetFull = packet.revenue_scenarios[packet.revenue_scenarios.length - 1]
  const nativeCurrent = native.revenue_scenarios[0]
  const nativeFull = native.revenue_scenarios[native.revenue_scenarios.length - 1]

  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-2">
        <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_-38px_rgba(15,23,42,0.22)]">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            Packet Overlay
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-950">
            Forced to Caldor packet design assumptions
          </h2>
          <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-2xl bg-slate-50 p-4">
              <dt className="text-slate-500">Debt Service</dt>
              <dd className="mt-1 text-lg font-semibold text-slate-950">
                {formatCurrency(packet.debt_service_annual)}
              </dd>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <dt className="text-slate-500">Non-Diesel Coverage</dt>
              <dd className="mt-1 text-lg font-semibold text-slate-950">
                {packet.non_diesel_combined_coverage_dscr?.toFixed(2)}x
              </dd>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <dt className="text-slate-500">Current State</dt>
              <dd className="mt-1 font-semibold text-slate-950">{packetCurrent.label}</dd>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <dt className="text-slate-500">Diversified DSCR</dt>
              <dd className="mt-1 font-semibold text-slate-950">
                {packetFull.dscr_mean.toFixed(2)}x
              </dd>
            </div>
          </dl>
        </div>

        <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_-38px_rgba(15,23,42,0.22)]">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
            Native Extracted
          </p>
          <h2 className="mt-2 text-xl font-semibold text-slate-950">
            Derived only from currently approved facts
          </h2>
          <dl className="mt-5 grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-2xl bg-slate-50 p-4">
              <dt className="text-slate-500">Debt Service</dt>
              <dd className="mt-1 text-lg font-semibold text-slate-950">
                {formatCurrency(native.debt_service_annual)}
              </dd>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <dt className="text-slate-500">Current Diesel Share</dt>
              <dd className="mt-1 text-lg font-semibold text-slate-950">
                {formatPercent(getDieselShare(nativeCurrent))}
              </dd>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <dt className="text-slate-500">Current State</dt>
              <dd className="mt-1 font-semibold text-slate-950">{nativeCurrent.label}</dd>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4">
              <dt className="text-slate-500">Diversified DSCR</dt>
              <dd className="mt-1 font-semibold text-slate-950">
                {nativeFull.dscr_mean.toFixed(2)}x
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_18px_50px_-38px_rgba(15,23,42,0.22)]">
        <div className="flex items-center gap-2">
          <Columns3 className="h-4 w-4 text-slate-500" />
          <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            Overlay Comparison
          </h3>
        </div>

        <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
          <table className="w-full border-collapse text-sm">
            <thead className="bg-slate-50 text-left">
              <tr>
                <th className="px-4 py-3 font-semibold text-slate-500">Metric</th>
                <th className="px-4 py-3 font-semibold text-slate-900">Packet Overlay</th>
                <th className="px-4 py-3 font-semibold text-slate-900">Native Extracted</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-t border-slate-200">
                <td className="px-4 py-3 text-slate-500">Diversified Revenue</td>
                <td className="px-4 py-3 text-slate-700">
                  {formatCurrency(packetFull.total_revenue)}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {formatCurrency(nativeFull.total_revenue)}
                </td>
              </tr>
              <tr className="border-t border-slate-200">
                <td className="px-4 py-3 text-slate-500">Mean DSCR</td>
                <td className="px-4 py-3 text-slate-700">{packetFull.dscr_mean.toFixed(2)}x</td>
                <td className="px-4 py-3 text-slate-700">{nativeFull.dscr_mean.toFixed(2)}x</td>
              </tr>
              <tr className="border-t border-slate-200">
                <td className="px-4 py-3 text-slate-500">Breach Weeks</td>
                <td className="px-4 py-3 text-slate-700">{packetFull.breach_weeks}</td>
                <td className="px-4 py-3 text-slate-700">{nativeFull.breach_weeks}</td>
              </tr>
              <tr className="border-t border-slate-200">
                <td className="px-4 py-3 text-slate-500">DSCR 1.35x Breakeven</td>
                <td className="px-4 py-3 text-slate-700">
                  {formatCurrency(packetFull.covenant_trigger_diesel_price, 2)}/gal
                </td>
                <td className="px-4 py-3 text-slate-700">
                  {formatCurrency(nativeFull.covenant_trigger_diesel_price, 2)}/gal
                </td>
              </tr>
              <tr className="border-t border-slate-200">
                <td className="px-4 py-3 text-slate-500">Risk Story</td>
                <td className="px-4 py-3 text-slate-700">
                  {packet.risk_proof?.takeaway ?? 'Packet proof not available'}
                </td>
                <td className="px-4 py-3 text-slate-700">
                  Native view reflects only the currently approved fact set and inferred uplifts.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default function RevenueDiversification() {
  const { projectId } = useParams<{ projectId: string }>()
  const [mode, setMode] = useState<VisualizationMode>('compare')
  const packetChartRef = useRef<SVGSVGElement | null>(null)
  const nativeChartRef = useRef<SVGSVGElement | null>(null)

  const packetQuery = useQuery({
    queryKey: ['revenue-diversification', projectId, 'packet'],
    queryFn: () => api.getRevenueDiversificationVisualization(projectId!, 'packet'),
    enabled: !!projectId && (mode === 'packet' || mode === 'compare'),
  })

  const nativeQuery = useQuery({
    queryKey: ['revenue-diversification', projectId, 'native'],
    queryFn: () => api.getRevenueDiversificationVisualization(projectId!, 'native'),
    enabled: !!projectId && (mode === 'native' || mode === 'compare'),
  })

  const activeVisualization =
    mode === 'native' ? nativeQuery.data : packetQuery.data ?? nativeQuery.data

  const activeChartRef = mode === 'native' ? nativeChartRef : packetChartRef
  const isLoading =
    mode === 'compare'
      ? packetQuery.isLoading || nativeQuery.isLoading
      : mode === 'native'
      ? nativeQuery.isLoading
      : packetQuery.isLoading

  const handleDownloadSvg = () => {
    if (!activeChartRef.current || !projectId) {
      return
    }

    const serializer = new XMLSerializer()
    const source = serializer.serializeToString(activeChartRef.current)
    const blob = new Blob([source], {
      type: 'image/svg+xml;charset=utf-8',
    })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${projectId}-revenue-diversification-${mode === 'native' ? 'native' : 'packet'}.svg`
    link.click()
    URL.revokeObjectURL(url)
  }

  if (isLoading) {
    return <div className="py-12 text-center text-gray-500">Loading revenue visualization...</div>
  }

  if (mode === 'compare' && (!packetQuery.data || !nativeQuery.data)) {
    return (
      <div className="py-12 text-center text-gray-500">
        Revenue diversification comparison is not available for this project yet.
      </div>
    )
  }

  if (!activeVisualization && mode !== 'compare') {
    return (
      <div className="py-12 text-center text-gray-500">
        Revenue diversification data is not available for this project yet.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_20px_60px_-34px_rgba(15,23,42,0.22)]">
        <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Scenario Analytics
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
              Revenue Diversification
            </h1>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              Switch between packet-forced assumptions and native extracted facts, or compare both so we can judge how close Muni-Pal gets from ingestion alone.
            </p>
          </div>

          <div className="flex flex-col items-start gap-3">
            <button
              type="button"
              onClick={handleDownloadSvg}
              className="btn-secondary rounded-xl px-4 py-2.5"
            >
              <Download className="mr-2 h-4 w-4" />
              {mode === 'native' ? 'Download Native SVG' : 'Download Packet SVG'}
            </button>
            <div className="flex flex-wrap gap-2">
              <ModeButton
                label="Packet Overlay"
                active={mode === 'packet'}
                onClick={() => setMode('packet')}
              />
              <ModeButton
                label="Native Extracted"
                active={mode === 'native'}
                onClick={() => setMode('native')}
              />
              <ModeButton
                label="Compare Both"
                active={mode === 'compare'}
                onClick={() => setMode('compare')}
              />
            </div>
          </div>
        </div>

        {mode !== 'compare' && activeVisualization ? (
          <MetricCards visualization={activeVisualization} />
        ) : null}
      </div>

      {mode === 'compare' && packetQuery.data && nativeQuery.data ? (
        <>
          <ComparisonSummary packet={packetQuery.data} native={nativeQuery.data} />

          <div className="space-y-6">
            <section className="space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Packet Overlay
                </p>
                <h2 className="mt-1 text-xl font-semibold text-slate-950">
                  Visualization forced to the Caldor packet narrative
                </h2>
              </div>
              <RevenueDiversificationChart
                ref={packetChartRef}
                visualization={packetQuery.data}
              />
              <DataQualityPanel
                visualization={packetQuery.data}
                title="Packet Overlay Notes"
              />
              <ScenarioNotesSection visualization={packetQuery.data} />
            </section>

            <section className="space-y-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">
                  Native Extracted
                </p>
                <h2 className="mt-1 text-xl font-semibold text-slate-950">
                  Visualization built only from approved facts currently in Muni-Pal
                </h2>
              </div>
              <RevenueDiversificationChart
                ref={nativeChartRef}
                visualization={nativeQuery.data}
              />
              <DataQualityPanel
                visualization={nativeQuery.data}
                title="Native Extraction Notes"
              />
              <ScenarioNotesSection visualization={nativeQuery.data} />
            </section>
          </div>
        </>
      ) : null}

      {mode === 'packet' && packetQuery.data ? (
        <>
          <DataQualityPanel visualization={packetQuery.data} />
          <RevenueDiversificationChart ref={packetChartRef} visualization={packetQuery.data} />
          <ScenarioNotesSection visualization={packetQuery.data} />
        </>
      ) : null}

      {mode === 'native' && nativeQuery.data ? (
        <>
          <DataQualityPanel visualization={nativeQuery.data} />
          <RevenueDiversificationChart ref={nativeChartRef} visualization={nativeQuery.data} />
          <ScenarioNotesSection visualization={nativeQuery.data} />
        </>
      ) : null}
    </div>
  )
}
