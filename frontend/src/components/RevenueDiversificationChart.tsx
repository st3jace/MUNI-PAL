import { forwardRef, useState } from 'react'
import type {
  RevenueDiversificationVisualizationResponse,
  RevenueScenarioMix,
  RevenueStreamSlice,
} from '../types'

const WIDTH = 1100
const HEIGHT = 610
const CHART_LEFT = 112
const CHART_RIGHT = WIDTH - 56
const CHART_TOP = 184
const CHART_HEIGHT = 260
const BAR_WIDTH = 120
const GRID_LINES = 4

function formatCompactCurrency(value: number): string {
  const formatter = new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: value >= 1_000_000 ? 1 : 0,
  })
  return `$${formatter.format(value)}`
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 2,
  }).format(value)
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

function getDieselShare(scenario: RevenueScenarioMix): number {
  const diesel = scenario.revenue_streams.find((slice) => slice.stream_id === 'diesel')
  return diesel?.pct_of_total ?? 0
}

function getDeltaLabel(currentRevenue: number, scenarioRevenue: number): string {
  if (currentRevenue <= 0) {
    return 'Baseline'
  }

  const delta = ((scenarioRevenue - currentRevenue) / currentRevenue) * 100
  if (Math.abs(delta) < 0.5) {
    return 'Baseline'
  }

  return `${delta > 0 ? '+' : ''}${Math.round(delta)}% revenue`
}

function toneForSafety(status: RevenueScenarioMix['safety_status']): string {
  if (status === 'fragile') {
    return 'text-red-700'
  }
  if (status === 'fortress') {
    return 'text-emerald-700'
  }
  return 'text-blue-700'
}

type ActiveSlice = {
  scenarioLabel: string
  slice: RevenueStreamSlice
} | null

interface RevenueDiversificationChartProps {
  visualization: RevenueDiversificationVisualizationResponse
}

const RevenueDiversificationChart = forwardRef<SVGSVGElement, RevenueDiversificationChartProps>(
  function RevenueDiversificationChart({ visualization }, ref) {
    const [activeSlice, setActiveSlice] = useState<ActiveSlice>(null)
    const scenarios = visualization.revenue_scenarios
    const baselineRevenue = scenarios[0]?.total_revenue ?? 0
    const showPacketConfigurationMetrics = scenarios.every(
      (scenario) => scenario.dscr_parity_diesel_price != null
    )
    const riskProof = visualization.risk_proof
    const maxRevenue = Math.max(
      ...scenarios.map((scenario) => scenario.total_revenue),
      visualization.debt_service_annual * 1.08,
      1
    )
    const plotWidth = CHART_RIGHT - CHART_LEFT
    const barSpacing = plotWidth / scenarios.length
    const debtServiceY =
      CHART_TOP + CHART_HEIGHT - (visualization.debt_service_annual / maxRevenue) * CHART_HEIGHT
    const hasInferredSlices = scenarios.some((scenario) =>
      scenario.revenue_streams.some((slice) => slice.is_inferred)
    )
    const dieselCompression =
      scenarios.length > 1 ? getDieselShare(scenarios[0]) - getDieselShare(scenarios[scenarios.length - 1]) : 0

    return (
      <div className="space-y-5">
        <div className="overflow-x-auto rounded-[26px] border border-slate-200 bg-white p-5 shadow-[0_18px_48px_-34px_rgba(15,23,42,0.24)]">
          <svg
            ref={ref}
            xmlns="http://www.w3.org/2000/svg"
            viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
            className="w-full min-w-[960px]"
            role="img"
            aria-label="Revenue diversification comparison chart"
          >
            <rect x="0" y="0" width={WIDTH} height={HEIGHT} rx="26" fill="#FFFFFF" />

            <text
              x="36"
              y="44"
              fill="#64748B"
              fontSize="12"
              fontWeight="700"
              letterSpacing="0.18em"
              fontFamily="ui-sans-serif, system-ui, sans-serif"
            >
              SCENARIO COMPARISON
            </text>
            <text
              x="36"
              y="82"
              fill="#0F172A"
              fontSize="30"
              fontWeight="700"
              fontFamily="ui-sans-serif, system-ui, sans-serif"
            >
              Revenue Diversification Impact
            </text>
            <text
              x="36"
              y="108"
              fill="#475569"
              fontSize="14"
              fontFamily="ui-sans-serif, system-ui, sans-serif"
            >
              Compare revenue concentration, covenant headroom, and operating resilience across scenario states.
            </text>

            <rect
              x={WIDTH - 226}
              y="28"
              width="190"
              height="74"
              rx="16"
              fill="#F8FAFC"
              stroke="#D9E2EC"
            />
            <text
              x={WIDTH - 198}
              y="52"
              fill="#64748B"
              fontSize="11"
              fontWeight="700"
              letterSpacing="0.14em"
              fontFamily="ui-sans-serif, system-ui, sans-serif"
            >
              ANNUAL DEBT SERVICE
            </text>
            <text
              x={WIDTH - 198}
              y="84"
              fill="#0F172A"
              fontSize="24"
              fontWeight="700"
              fontFamily="ui-sans-serif, system-ui, sans-serif"
            >
              {formatCompactCurrency(visualization.debt_service_annual)}
            </text>

            {visualization.stream_definitions.map((stream, index) => {
              const x = 36 + index * 148
              return (
                <g key={stream.stream_id} transform={`translate(${x}, 138)`}>
                  <rect width="10" height="10" rx="3" fill={stream.color} />
                  <text
                    x="16"
                    y="9"
                    fill="#334155"
                    fontSize="12"
                    fontFamily="ui-sans-serif, system-ui, sans-serif"
                  >
                    {stream.label}
                  </text>
                </g>
              )
            })}

            {hasInferredSlices ? (
              <text
                x={WIDTH - 310}
                y="147"
                fill="#64748B"
                fontSize="12"
                fontFamily="ui-sans-serif, system-ui, sans-serif"
              >
                Lower-opacity segments indicate modeled or inferred streams.
              </text>
            ) : null}

            {Array.from({ length: GRID_LINES + 1 }).map((_, index) => {
              const ratio = index / GRID_LINES
              const y = CHART_TOP + CHART_HEIGHT - ratio * CHART_HEIGHT
              const tickValue = maxRevenue * ratio
              return (
                <g key={`grid-${index}`}>
                  <line
                    x1={CHART_LEFT}
                    x2={CHART_RIGHT}
                    y1={y}
                    y2={y}
                    stroke={index === 0 ? '#CBD5E1' : '#E2E8F0'}
                    strokeWidth="1"
                  />
                  <text
                    x="36"
                    y={y + 4}
                    fill="#64748B"
                    fontSize="12"
                    fontFamily="ui-sans-serif, system-ui, sans-serif"
                  >
                    {formatCompactCurrency(tickValue)}
                  </text>
                </g>
              )
            })}

            {scenarios.map((scenario, index) => {
              const centerX = CHART_LEFT + barSpacing * index + barSpacing / 2
              const barX = centerX - BAR_WIDTH / 2
              const clipId = `scenario-bar-${index}`
              const deltaLabel = getDeltaLabel(baselineRevenue, scenario.total_revenue)
              const dieselShare = getDieselShare(scenario)
              let currentTop = CHART_TOP + CHART_HEIGHT

              return (
                <g key={scenario.scenario_id}>
                  <clipPath id={clipId}>
                    <rect
                      x={barX}
                      y={CHART_TOP}
                      width={BAR_WIDTH}
                      height={CHART_HEIGHT}
                      rx="14"
                    />
                  </clipPath>

                  <text
                    x={centerX}
                    y="178"
                    textAnchor="middle"
                    fill="#0F172A"
                    fontSize="18"
                    fontWeight="700"
                    fontFamily="ui-sans-serif, system-ui, sans-serif"
                  >
                    {scenario.label}
                  </text>
                  <text
                    x={centerX}
                    y="198"
                    textAnchor="middle"
                    fill={index === 0 ? '#475569' : '#2563EB'}
                    fontSize="11"
                    fontWeight="700"
                    letterSpacing="0.08em"
                    fontFamily="ui-sans-serif, system-ui, sans-serif"
                  >
                    {deltaLabel.toUpperCase()}
                  </text>

                  <rect
                    x={barX}
                    y={CHART_TOP}
                    width={BAR_WIDTH}
                    height={CHART_HEIGHT}
                    rx="14"
                    fill="#F8FAFC"
                    stroke="#D9E2EC"
                  />

                  <g clipPath={`url(#${clipId})`}>
                    {scenario.revenue_streams.map((slice) => {
                      const height = (slice.amount / maxRevenue) * CHART_HEIGHT
                      const y = currentTop - height
                      currentTop = y

                      return (
                        <g
                          key={`${scenario.scenario_id}-${slice.stream_id}`}
                          onMouseEnter={() => setActiveSlice({ scenarioLabel: scenario.label, slice })}
                        >
                          <rect
                            x={barX}
                            y={y}
                            width={BAR_WIDTH}
                            height={height}
                            rx="0"
                            fill={slice.color}
                            opacity={slice.is_inferred ? 0.72 : 0.96}
                            stroke="#FFFFFF"
                            strokeWidth="2"
                          >
                            <title>
                              {scenario.label} - {slice.label}: {formatCurrency(slice.amount)} ({(slice.pct_of_total * 100).toFixed(1)}%)
                              {slice.is_inferred ? ' (inferred)' : ''}
                            </title>
                          </rect>
                          {height > 36 ? (
                            <text
                              x={centerX}
                              y={y + height / 2 + 4}
                              textAnchor="middle"
                              fill={slice.stream_id === 'diesel' ? '#F8FAFC' : '#0F172A'}
                              fontSize="11"
                              fontWeight="700"
                              fontFamily="ui-sans-serif, system-ui, sans-serif"
                            >
                              {slice.label}
                            </text>
                          ) : null}
                        </g>
                      )
                    })}
                  </g>

                  <text
                    x={centerX}
                    y="482"
                    textAnchor="middle"
                    fill="#64748B"
                    fontSize="10"
                    fontWeight="700"
                    letterSpacing="0.16em"
                    fontFamily="ui-sans-serif, system-ui, sans-serif"
                  >
                    TOTAL ANNUAL REVENUE
                  </text>
                  <text
                    x={centerX}
                    y="516"
                    textAnchor="middle"
                    fill="#0F172A"
                    fontSize="28"
                    fontWeight="700"
                    fontFamily="ui-sans-serif, system-ui, sans-serif"
                  >
                    {formatCompactCurrency(scenario.total_revenue)}
                  </text>
                  <text
                    x={centerX}
                    y="538"
                    textAnchor="middle"
                    fill="#475569"
                    fontSize="12"
                    fontFamily="ui-sans-serif, system-ui, sans-serif"
                  >
                    {`Mean DSCR ${scenario.dscr_mean.toFixed(2)}x | Diesel ${formatPercent(dieselShare)}`}
                  </text>
                  <text
                    x={centerX}
                    y="556"
                    textAnchor="middle"
                    fill="#475569"
                    fontSize="12"
                    fontFamily="ui-sans-serif, system-ui, sans-serif"
                  >
                    {`Min DSCR ${scenario.dscr_minimum.toFixed(2)}x | Breach ${scenario.breach_weeks} weeks`}
                  </text>
                </g>
              )
            })}

            <line
              x1={CHART_LEFT}
              x2={CHART_RIGHT}
              y1={debtServiceY}
              y2={debtServiceY}
              stroke="#C2410C"
              strokeWidth="2"
              strokeDasharray="7 7"
            />
            <text
              x={CHART_RIGHT - 38}
              y={debtServiceY - 24}
              textAnchor="middle"
              fill="#9A3412"
              fontSize="10.5"
              fontWeight="700"
              fontFamily="ui-sans-serif, system-ui, sans-serif"
            >
              <tspan x={CHART_RIGHT - 38} dy="0">Debt Service</tspan>
              <tspan x={CHART_RIGHT - 38} dy="12">Threshold</tspan>
            </text>

            <text
              x="36"
              y={HEIGHT - 20}
              fill="#64748B"
              fontSize="12"
              fontFamily="ui-sans-serif, system-ui, sans-serif"
            >
              Diesel concentration declines by {formatPercent(dieselCompression)} from current state to the most diversified case.
            </text>
          </svg>
        </div>

        <div className="grid gap-4 xl:grid-cols-[0.85fr_1.15fr]">
          <div className="rounded-[22px] border border-slate-200 bg-white p-5 shadow-[0_16px_34px_-30px_rgba(15,23,42,0.38)]">
            <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Stream Detail
            </h3>
            {activeSlice ? (
              <div className="mt-4 space-y-3">
                <div>
                  <p className="text-lg font-semibold text-slate-950">
                    {activeSlice.scenarioLabel}: {activeSlice.slice.label}
                  </p>
                  <p className="mt-1 text-sm text-slate-600">
                    {formatCurrency(activeSlice.slice.amount)} and {(activeSlice.slice.pct_of_total * 100).toFixed(1)}% of scenario revenue.
                  </p>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-slate-600">
                  Stability class:{' '}
                  <span className="font-semibold text-slate-900">
                    {activeSlice.slice.stability_class}
                  </span>
                  {activeSlice.slice.is_inferred
                    ? ' | This slice is modeled from scenario uplift assumptions.'
                    : ' | This slice is backed by approved revenue evidence.'}
                  {activeSlice.slice.source_path ? (
                    <div className="mt-2 text-xs text-slate-500">
                      Evidence path: {activeSlice.slice.source_path}
                    </div>
                  ) : null}
                </div>
              </div>
            ) : (
              <p className="mt-4 text-sm leading-6 text-slate-600">
                Hover a revenue segment to inspect its share of the stack and whether it is evidence-backed or scenario-modeled.
              </p>
            )}
          </div>

          <div className="rounded-[22px] border border-slate-200 bg-white p-5 shadow-[0_16px_34px_-30px_rgba(15,23,42,0.38)]">
            <h3 className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Scenario Matrix
            </h3>
            <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
              <table className="w-full border-collapse text-sm">
                <thead className="bg-slate-50 text-left">
                  <tr>
                    <th className="px-4 py-3 font-semibold text-slate-500">Metric</th>
                    {scenarios.map((scenario) => (
                      <th key={scenario.scenario_id} className="px-4 py-3 font-semibold text-slate-900">
                        {scenario.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-slate-200">
                    <td className="px-4 py-3 text-slate-500">Revenue</td>
                    {scenarios.map((scenario) => (
                      <td key={`${scenario.scenario_id}-revenue`} className="px-4 py-3 font-medium text-slate-950">
                        {formatCompactCurrency(scenario.total_revenue)}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-t border-slate-200">
                    <td className="px-4 py-3 text-slate-500">Diesel Share</td>
                    {scenarios.map((scenario) => (
                      <td key={`${scenario.scenario_id}-diesel`} className="px-4 py-3 text-slate-700">
                        {formatPercent(getDieselShare(scenario))}
                      </td>
                    ))}
                  </tr>
                  <tr className="border-t border-slate-200">
                    <td className="px-4 py-3 text-slate-500">Mean DSCR</td>
                    {scenarios.map((scenario) => (
                      <td key={`${scenario.scenario_id}-mean-dscr`} className="px-4 py-3 text-slate-700">
                        {scenario.dscr_mean.toFixed(2)}x
                      </td>
                    ))}
                  </tr>
                  <tr className="border-t border-slate-200">
                    <td className="px-4 py-3 text-slate-500">Min DSCR</td>
                    {scenarios.map((scenario) => (
                      <td key={`${scenario.scenario_id}-min-dscr`} className="px-4 py-3 text-slate-700">
                        {scenario.dscr_minimum.toFixed(2)}x
                      </td>
                    ))}
                  </tr>
                  <tr className="border-t border-slate-200">
                    <td className="px-4 py-3 text-slate-500">Breach Exposure</td>
                    {scenarios.map((scenario) => (
                      <td key={`${scenario.scenario_id}-breach`} className="px-4 py-3 text-slate-700">
                        {scenario.breach_weeks} weeks
                      </td>
                    ))}
                  </tr>
                  {showPacketConfigurationMetrics ? (
                    <>
                      <tr className="border-t border-slate-200">
                        <td className="px-4 py-3 text-slate-500">EBITDA Breakeven</td>
                        {scenarios.map((scenario) => (
                          <td key={`${scenario.scenario_id}-ebitda-breakeven`} className="px-4 py-3 text-slate-700">
                            {formatCurrency(scenario.breakeven_diesel_price)}/gal
                          </td>
                        ))}
                      </tr>
                      <tr className="border-t border-slate-200">
                        <td className="px-4 py-3 text-slate-500">DSCR 1.0x</td>
                        {scenarios.map((scenario) => (
                          <td key={`${scenario.scenario_id}-dscr-parity`} className="px-4 py-3 text-slate-700">
                            {formatCurrency(scenario.dscr_parity_diesel_price ?? 0)}/gal
                          </td>
                        ))}
                      </tr>
                      <tr className="border-t border-slate-200">
                        <td className="px-4 py-3 text-slate-500">DSCR 1.35x</td>
                        {scenarios.map((scenario) => (
                          <td key={`${scenario.scenario_id}-dscr-threshold`} className="px-4 py-3 text-slate-700">
                            {formatCurrency(scenario.covenant_trigger_diesel_price)}/gal
                          </td>
                        ))}
                      </tr>
                    </>
                  ) : (
                    <>
                      <tr className="border-t border-slate-200">
                        <td className="px-4 py-3 text-slate-500">Breakeven</td>
                        {scenarios.map((scenario) => (
                          <td key={`${scenario.scenario_id}-breakeven`} className="px-4 py-3 text-slate-700">
                            {formatCurrency(scenario.breakeven_diesel_price)}/gal
                          </td>
                        ))}
                      </tr>
                    </>
                  )}
                  <tr className="border-t border-slate-200">
                    <td className="px-4 py-3 text-slate-500">Posture</td>
                    {scenarios.map((scenario) => (
                      <td
                        key={`${scenario.scenario_id}-posture`}
                        className={`px-4 py-3 font-semibold ${toneForSafety(scenario.safety_status)}`}
                      >
                        {scenario.safety_label}
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>

            {hasInferredSlices ? (
              <p className="mt-3 text-xs leading-5 text-slate-500">
                Modeled streams are shown with reduced opacity in the chart and called out in hover detail when selected.
              </p>
            ) : null}

            {riskProof ? (
              <div className="mt-5 border-t border-slate-200 pt-5">
                <div className="flex flex-col gap-1">
                  <h4 className="text-sm font-semibold text-slate-950">{riskProof.title}</h4>
                  <p className="text-xs leading-5 text-slate-500">{riskProof.takeaway}</p>
                </div>

                <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200">
                  <table className="w-full border-collapse text-sm">
                    <thead className="bg-slate-50 text-left">
                      <tr>
                        <th className="px-4 py-3 font-semibold text-slate-500">Metric</th>
                        <th className="px-4 py-3 font-semibold text-slate-900">
                          {riskProof.baseline_label}
                        </th>
                        <th className="px-4 py-3 font-semibold text-slate-900">
                          {riskProof.diversified_label}
                        </th>
                        <th className="px-4 py-3 font-semibold text-slate-500">Delta</th>
                      </tr>
                    </thead>
                    <tbody>
                      {riskProof.metrics.map((metric) => (
                        <tr key={metric.metric_id} className="border-t border-slate-200">
                          <td className="px-4 py-3 text-slate-500">{metric.label}</td>
                          <td className="px-4 py-3 text-slate-700">{metric.baseline_value}</td>
                          <td className="px-4 py-3 text-slate-700">{metric.diversified_value}</td>
                          <td className="px-4 py-3 font-medium text-slate-950">{metric.delta_label}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    )
  }
)

export default RevenueDiversificationChart
