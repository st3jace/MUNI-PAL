import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowLeft, Calculator, Loader2, Download } from 'lucide-react'
import { sensingApi } from '../../services/sensingApi'
import { useSensing } from '../../contexts/SensingContext'

const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
  'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
  'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
  'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC',
]

const RATINGS = [
  'AAA','AA+','AA','AA-','A+','A','A-',
  'BBB+','BBB','BBB-','BB+','BB','BB-',
  'B+','B','B-',
]

function fmt$(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
  return `$${n.toLocaleString()}`
}

function StatBox({
  label,
  value,
  color,
}: {
  label: string
  value: string
  color?: string
}) {
  return (
    <div className="bg-gray-50 rounded-lg px-4 py-3">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
        {label}
      </div>
      <div
        className={`text-lg font-semibold ${color || 'text-gray-900'}`}
      >
        {value}
      </div>
    </div>
  )
}

function CoiEstimateSection({
  dealSize,
  sector,
}: {
  dealSize: number
  sector: string
}) {
  // Only show for healthcare sectors
  const isHealthcare =
    sector === 'healthcare' || sector.startsWith('healthcare_')
  const subSector = sector.startsWith('healthcare_')
    ? sector.replace('healthcare_', '')
    : 'hospital'

  const coiQuery = useQuery({
    queryKey: ['coi-deal-benchmarks', subSector],
    queryFn: () => sensingApi.getCoiDealBenchmarks(subSector),
    enabled: isHealthcare && dealSize > 0,
  })

  if (!isHealthcare || !coiQuery.data) return null

  const ssData = coiQuery.data.sub_sectors?.[subSector]
  if (!ssData) return null

  const coi = ssData.total_coi_per_1000 || ssData.coi_per_1000
  if (!coi) return null

  const parIn1000 = dealSize / 1000
  const medianCoi = (coi.median || coi.value) * parIn1000
  const lowCoi = (coi.p25 ?? coi.median ?? coi.value) * parIn1000
  const highCoi = (coi.p75 ?? coi.median ?? coi.value) * parIn1000

  // Find matching size bucket
  const bySize = ssData.by_deal_size
  let sizeLabel = ''
  let sizeBucketMedian: number | null = null
  if (bySize) {
    const dealMM = dealSize / 1e6
    const bucket =
      dealMM < 100
        ? bySize.small_under_100m
        : dealMM <= 500
          ? bySize.mid_100_500m
          : bySize.large_over_500m
    if (bucket) {
      sizeLabel = bucket.label
      sizeBucketMedian = (bucket.median_coi_per_1000 ?? bucket.median) * parIn1000
    }
  }

  // Recent period data
  const byPeriod = ssData.by_period
  const recentMedian = byPeriod?.recent_2022_2025?.median_coi_per_1000 ??
    byPeriod?.recent_2022_plus?.median

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
      <h3 className="font-semibold text-gray-900 mb-1">
        Cost-of-Issuance (COI) Estimate
      </h3>
      <p className="text-xs text-gray-500 mb-4">
        Based on {ssData.sample_size} actual {subSector.replace('_', ' ')} deals
        {ssData.year_range
          ? ` (${ssData.year_range[0]}–${ssData.year_range[1]})`
          : ''}
      </p>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <StatBox
          label="Expected COI (median)"
          value={fmt$(Math.round(medianCoi))}
        />
        <StatBox
          label="COI Range (P25–P75)"
          value={`${fmt$(Math.round(lowCoi))} – ${fmt$(Math.round(highCoi))}`}
        />
        {sizeBucketMedian != null && (
          <StatBox
            label={`Size Bucket (${sizeLabel})`}
            value={fmt$(Math.round(sizeBucketMedian))}
          />
        )}
        {recentMedian != null && (
          <StatBox
            label="Recent Deals (2022+)"
            value={`$${recentMedian.toFixed(2)}/1000`}
          />
        )}
      </div>
      {ssData.repeat_issuer_savings && (
        <p className="mt-3 text-sm text-gray-500">
          Repeat issuers pay about ${ssData.repeat_issuer_savings.median_raw_decline_per_1000 ?? ssData.repeat_issuer_insight?.median_coi_decline_per_1000} less per $1,000 borrowed, on average.
        </p>
      )}
    </div>
  )
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function ResultsView({ data }: { data: any }) {
  const spread = data.spread_estimate
  const peers = data.peer_comparison
  const structure = data.structural_norms
  const risk = data.risk_profile
  const financials = data.financial_benchmarks
  const pfa = data.pfa_comparison
  const market = data.market_context

  return (
    <div className="space-y-5">
      {/* Spread Estimate */}
      {spread && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Spread Estimate</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatBox
              label="Expected Spread"
              value={
                spread.expected_spread_bps != null
                  ? `${spread.expected_spread_bps} bps`
                  : 'N/A'
              }
            />
            <StatBox
              label="Sector Median"
              value={
                spread.sector_median_spread_bps != null
                  ? `${spread.sector_median_spread_bps} bps`
                  : 'N/A'
              }
            />
            <StatBox
              label="vs. Sector"
              value={spread.spread_vs_sector || 'N/A'}
              color={
                spread.spread_vs_sector === 'tighter'
                  ? 'text-green-600'
                  : spread.spread_vs_sector === 'wider'
                    ? 'text-red-600'
                    : undefined
              }
            />
            <StatBox
              label="Rating"
              value={spread.rating_normalized || 'N/A'}
            />
          </div>
          {spread.note && (
            <p className="mt-3 text-sm text-gray-500">{spread.note}</p>
          )}
        </div>
      )}

      {/* Peer Comparison */}
      {peers && peers.n_peers > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-4">
            Peer Comparison ({peers.n_peers} peers)
          </h3>
          {peers.top_peers && peers.top_peers.length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2.5 px-3 font-medium text-gray-600">
                      Issuer
                    </th>
                    <th className="text-left py-2.5 px-3 font-medium text-gray-600">
                      Par Amount
                    </th>
                    <th className="text-left py-2.5 px-3 font-medium text-gray-600">
                      State
                    </th>
                    <th className="text-left py-2.5 px-3 font-medium text-gray-600">
                      Similarity
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {peers.top_peers.map((p: any, i: number) => (
                    <tr key={i} className="border-b border-gray-100">
                      <td className="py-2.5 px-3 text-gray-800">
                        {p.issuer_name || p.cusip_9}
                      </td>
                      <td className="py-2.5 px-3 text-gray-800">
                        {fmt$(p.par_amount)}
                      </td>
                      <td className="py-2.5 px-3 text-gray-800">{p.state}</td>
                      <td className="py-2.5 px-3 text-gray-800">
                        {p.similarity_score != null
                          ? `${(p.similarity_score * 100).toFixed(0)}%`
                          : 'N/A'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Structural Norms */}
      {structure && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Structural Norms</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {structure.pledge_type_distribution && (
              <div>
                <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                  Pledge Types
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(
                    structure.pledge_type_distribution as Record<string, number>
                  ).map(([type, count]) => (
                    <span
                      key={type}
                      className="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
                    >
                      {type}: {count}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {structure.coverage_median != null && (
              <StatBox
                label="Coverage Median"
                value={`${structure.coverage_median.toFixed(2)}x`}
              />
            )}
            {structure.abt_rate != null && (
              <StatBox
                label="ABT Rate"
                value={`${(structure.abt_rate * 100).toFixed(0)}%`}
              />
            )}
          </div>
        </div>
      )}

      {/* Risk Profile */}
      {risk && risk.total_factors > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Risk Profile</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3">
            <StatBox label="Total Factors" value={String(risk.total_factors)} />
            <StatBox
              label="Mitigation Rate"
              value={
                risk.mitigation_rate != null
                  ? `${(risk.mitigation_rate * 100).toFixed(0)}%`
                  : 'N/A'
              }
            />
            <StatBox
              label="Categories"
              value={String(risk.n_categories ?? 0)}
            />
          </div>
          {risk.prospect_flags && risk.prospect_flags.length > 0 && (
            <div className="mt-3">
              <h4 className="text-xs font-medium text-gray-600 uppercase tracking-wider mb-2">
                Risk Flags
              </h4>
              <ul className="space-y-1.5">
                {risk.prospect_flags.map((flag: string, i: number) => (
                  <li
                    key={i}
                    className="text-sm text-amber-700 bg-amber-50 rounded-lg px-3 py-2"
                  >
                    {flag}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Financial Benchmarks */}
      {financials && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-4">
            Financial Benchmarks
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {financials.dscr_median != null && (
              <StatBox
                label="DSCR Median"
                value={`${financials.dscr_median.toFixed(2)}x`}
              />
            )}
            {financials.operating_margin_median != null && (
              <StatBox
                label="Op. Margin"
                value={`${(financials.operating_margin_median * 100).toFixed(1)}%`}
              />
            )}
            {financials.revenue_median != null && (
              <StatBox
                label="Revenue Median"
                value={fmt$(financials.revenue_median)}
              />
            )}
            <StatBox
              label="Reports"
              value={String(financials.n_reports ?? 0)}
            />
          </div>
        </div>
      )}

      {/* PFA Comparison */}
      {pfa && pfa.n_pfa_deals > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-1">
            Public Finance Authority Comparison
          </h3>
          <p className="text-xs text-gray-500 mb-4">
            How deals issued through multi-state conduit issuers (authorities
            that issue on your behalf) compare.
          </p>
          <div className="grid grid-cols-2 gap-3">
            <StatBox label="PFA Deals" value={String(pfa.n_pfa_deals)} />
            <StatBox
              label="PFA Share"
              value={
                pfa.pfa_share != null
                  ? `${(pfa.pfa_share * 100).toFixed(0)}%`
                  : 'N/A'
              }
            />
          </div>
          {pfa.pfa_note && (
            <p className="mt-3 text-sm text-gray-500">{pfa.pfa_note}</p>
          )}
        </div>
      )}

      {/* Market Context */}
      {market && (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Market Context</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {market.total_trades != null && (
              <StatBox
                label="Trades"
                value={market.total_trades.toLocaleString()}
              />
            )}
            {market.median_yield != null && (
              <StatBox
                label="Median Yield"
                value={`${market.median_yield.toFixed(2)}%`}
              />
            )}
            {market.n_cusips != null && (
              <StatBox label="CUSIPs" value={String(market.n_cusips)} />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default function BenchmarkCalculator() {
  const sensing = useSensing()
  const [sector, setSector] = useState(sensing.sector || 'healthcare')
  const [dealSize, setDealSize] = useState('')
  const [state, setState] = useState('')
  const [rating, setRating] = useState('A')
  const [maturity, setMaturity] = useState('30')

  const sectorsQuery = useQuery({
    queryKey: ['sensing-sectors'],
    queryFn: sensingApi.listSectors,
  })

  const benchmarkMutation = useMutation({
    mutationFn: sensingApi.runBenchmark,
  })

  // Store results in shared context for PDF export
  useEffect(() => {
    if (benchmarkMutation.data) {
      sensing.setBenchmark(benchmarkMutation.data)
      sensing.setBenchmarkInputs({
        deal_size: parseFloat(dealSize.replace(/[,$]/g, '')) || 0,
        state,
        rating,
        maturity: parseFloat(maturity) || 30,
      })
      sensing.setSector(sector)
    }
  }, [benchmarkMutation.data]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const size = parseFloat(dealSize.replace(/[,$]/g, ''))
    if (isNaN(size) || !state || !rating) return
    benchmarkMutation.mutate({
      sector,
      deal_size: size,
      state,
      rating,
      maturity: parseFloat(maturity) || 30,
    })
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8 flex items-start gap-4">
        <Link to="/tools" className="mt-1 text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Deal Benchmarks
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            See what deals like yours actually cost — compared against real
            municipal bond transactions
          </p>
        </div>
      </div>

      {/* Input Form */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-6"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Deal Size (USD)
            </label>
            <input
              type="text"
              className="input w-full"
              placeholder="50,000,000"
              value={dealSize}
              onChange={(e) => setDealSize(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              State
            </label>
            <select
              className="input w-full"
              value={state}
              onChange={(e) => setState(e.target.value)}
              required
            >
              <option value="">Select...</option>
              {US_STATES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Expected Rating
            </label>
            <select
              className="input w-full"
              value={rating}
              onChange={(e) => setRating(e.target.value)}
            >
              {RATINGS.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Maturity (years)
            </label>
            <input
              type="number"
              className="input w-full"
              value={maturity}
              onChange={(e) => setMaturity(e.target.value)}
              min="1"
              max="40"
            />
          </div>
          <div className="flex items-end">
            <button
              type="submit"
              className="btn btn-primary w-full flex items-center justify-center gap-2"
              disabled={benchmarkMutation.isPending}
            >
              {benchmarkMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Calculator className="h-4 w-4" />
                  Compare my deal
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {benchmarkMutation.error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          Benchmark failed: {String(benchmarkMutation.error)}
        </div>
      )}

      {benchmarkMutation.data && (
        <>
          <ResultsView data={benchmarkMutation.data} />
          <div className="mt-5">
            <CoiEstimateSection
              dealSize={parseFloat(dealSize.replace(/[,$]/g, '')) || 0}
              sector={sector}
            />
          </div>
          <p className="mt-5 text-sm text-gray-600">
            Not sure you're ready to be in this table?{' '}
            <Link
              to="/tools/readiness"
              className="font-medium text-primary-600 hover:text-primary-700 underline"
            >
              Take the free readiness assessment
            </Link>{' '}
            — about 10 minutes.
          </p>
          <div className="mt-4 flex justify-end">
            <Link
              to="/tools/export"
              className="flex items-center gap-2 text-sm font-medium text-primary-600 hover:text-primary-700"
            >
              <Download className="h-4 w-4" />
              Export Combined Report
              {sensing.completedCount > 0 && (
                <span className="bg-primary-100 text-primary-700 rounded-full px-2 py-0.5 text-xs">
                  {sensing.completedCount}/4
                </span>
              )}
            </Link>
          </div>
        </>
      )}
    </div>
  )
}
