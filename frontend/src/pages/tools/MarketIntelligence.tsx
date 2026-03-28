import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { ArrowLeft, ChevronDown, ChevronRight, Loader2, Download } from 'lucide-react'
import { sensingApi } from '../../services/sensingApi'
import { useSensing } from '../../contexts/SensingContext'

function SectionCard({
  title,
  children,
  defaultOpen = false,
}: {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <button
        className="flex items-center justify-between w-full text-left px-5 py-4"
        onClick={() => setOpen(!open)}
      >
        <h3 className="font-semibold text-gray-900 text-base">{title}</h3>
        {open ? (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-400" />
        )}
      </button>
      {open && <div className="px-5 pb-5 pt-1">{children}</div>}
    </div>
  )
}

function StatBox({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-50 rounded-lg px-4 py-3">
      <div className="text-xs text-gray-500 uppercase tracking-wider mb-1">
        {label}
      </div>
      <div className="text-lg font-semibold text-gray-900">{String(value)}</div>
    </div>
  )
}

function DataTable({
  headers,
  rows,
}: {
  headers: string[]
  rows: (string | number)[][]
}) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            {headers.map((h) => (
              <th
                key={h}
                className="text-left py-2.5 px-3 font-medium text-gray-600"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-gray-100">
              {row.map((cell, j) => (
                <td key={j} className="py-2.5 px-3 text-gray-800">
                  {String(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function fmt$(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  return `$${n.toLocaleString()}`
}

/** Format a decimal ratio (0.165) as a percentage string ("16.5%"). */
function pctDecimal(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  return `${(n * 100).toFixed(1)}%`
}

/** Format an already-percentage value (72.4) as "72.4%". */
function pctDirect(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  return `${n.toFixed(1)}%`
}

export default function MarketIntelligence() {
  const sensing = useSensing()
  const [sector, setSector] = useState(sensing.sector || 'waste')

  const sectorsQuery = useQuery({
    queryKey: ['sensing-sectors'],
    queryFn: sensingApi.listSectors,
  })

  const reportQuery = useQuery({
    queryKey: ['market-intelligence', sector],
    queryFn: () => sensingApi.getMarketIntelligence(sector),
    enabled: !!sector,
  })

  const report = reportQuery.data
  const es = report?.executive_summary

  // Store results in shared context for PDF export
  useEffect(() => {
    if (report) {
      sensing.setMarketIntel(report)
      sensing.setSector(sector)
    }
  }, [report, sector]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Link
            to="/tools"
            className="mt-1 text-gray-400 hover:text-gray-600"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Market Intelligence Report
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Sector benchmark from the EMMA municipal bond corpus
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <label className="text-xs text-gray-500 font-medium">Sector</label>
          <select
            className="input w-48"
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

      {reportQuery.isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          <span className="ml-3 text-gray-500">
            Generating report for{' '}
            {sector.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            ...
          </span>
        </div>
      )}

      {reportQuery.error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
          Failed to load report: {String(reportQuery.error)}
        </div>
      )}

      {report && (
        <div className="space-y-5">
          {/* Executive Summary */}
          <div className="bg-muni-navy rounded-lg p-6 text-white">
            <h2 className="text-lg font-semibold mb-4">Executive Summary</h2>
            {es?.report_completeness && (
              <div className="flex gap-6 text-sm mb-4">
                <span>
                  <span className="text-muni-teal font-semibold">
                    {es.report_completeness.available_sections}
                  </span>{' '}
                  available
                </span>
                <span>
                  <span className="text-yellow-400 font-semibold">
                    {es.report_completeness.partial_sections}
                  </span>{' '}
                  partial
                </span>
                <span>
                  <span className="text-gray-400 font-semibold">
                    {es.report_completeness.pending_sections}
                  </span>{' '}
                  pending
                </span>
              </div>
            )}
            {es?.key_findings && (
              <ul className="space-y-1.5 text-sm text-gray-300">
                {es.key_findings.map((f: string, i: number) => (
                  <li key={i} className="flex gap-2">
                    <span className="text-muni-teal flex-shrink-0">-</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Deal Structure */}
          {report.deal_structure && (
            <SectionCard title="Deal Structure Profile" defaultOpen>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <StatBox
                  label="Total Deals"
                  value={report.deal_structure.n_deals ?? 0}
                />
                <StatBox
                  label="Total Par"
                  value={fmt$(report.deal_structure.par_amount_total_usd)}
                />
                <StatBox
                  label="Median Par"
                  value={fmt$(report.deal_structure.par_amount_median_usd)}
                />
                <StatBox
                  label="States"
                  value={
                    Object.keys(
                      report.deal_structure.state_distribution || {}
                    ).length
                  }
                />
              </div>
              {report.deal_structure.top_issuers &&
                report.deal_structure.top_issuers.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">
                      Top Issuers
                    </h4>
                    <DataTable
                      headers={['Issuer', 'Deals']}
                      rows={report.deal_structure.top_issuers.map(
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        (iss: any) => [iss.name || 'Unknown', iss.deal_count ?? 0]
                      )}
                    />
                  </div>
                )}
              {report.deal_structure.bond_type_distribution &&
                Object.keys(report.deal_structure.bond_type_distribution).length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">
                      Bond Types
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(
                        report.deal_structure.bond_type_distribution as Record<string, number>
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
            </SectionCard>
          )}

          {/* Ratings */}
          {report.rating_distribution && (
            <SectionCard title="Rating Distribution" defaultOpen>
              <div className="grid grid-cols-3 gap-3 mb-4">
                <StatBox
                  label="Total Rated"
                  value={report.rating_distribution.total_rated ?? 0}
                />
                <StatBox
                  label="Investment Grade"
                  value={pctDirect(report.rating_distribution.investment_grade_pct)}
                />
                <StatBox
                  label="Modal Rating"
                  value={report.rating_distribution.modal_rating || 'N/A'}
                />
              </div>
              {report.rating_distribution.by_agency &&
                Object.entries(report.rating_distribution.by_agency).map(
                  ([agency, ratings]) => (
                    <div key={agency} className="mt-4">
                      <h4 className="text-sm font-medium text-gray-600 mb-2">
                        {agency}
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(
                          ratings as Record<string, number>
                        )
                          .sort(([, a], [, b]) => b - a)
                          .map(([rating, count]) => (
                            <span
                              key={rating}
                              className="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
                            >
                              {rating}: {count}
                            </span>
                          ))}
                      </div>
                    </div>
                  )
                )}
            </SectionCard>
          )}

          {/* Financial Benchmarks */}
          {report.financial_benchmarks && (
            <SectionCard title="Financial Benchmarks" defaultOpen>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {report.financial_benchmarks.dscr_median != null && (
                  <StatBox
                    label="DSCR Median"
                    value={`${report.financial_benchmarks.dscr_median.toFixed(2)}x`}
                  />
                )}
                {report.financial_benchmarks.operating_margin_median != null && (
                  <StatBox
                    label="Op. Margin"
                    value={pctDecimal(
                      report.financial_benchmarks.operating_margin_median
                    )}
                  />
                )}
                {report.financial_benchmarks.leverage_median != null && (
                  <StatBox
                    label="Leverage"
                    value={`${report.financial_benchmarks.leverage_median.toFixed(2)}x`}
                  />
                )}
                <StatBox
                  label="Reports"
                  value={report.financial_benchmarks.n_reports ?? 0}
                />
              </div>
            </SectionCard>
          )}

          {/* Risk Profile */}
          {report.risk_profile && (
            <SectionCard title="Risk Factor Analysis">
              <div className="grid grid-cols-3 gap-3 mb-4">
                <StatBox
                  label="Total Factors"
                  value={report.risk_profile.n_risk_factors ?? 0}
                />
                <StatBox
                  label="Categories"
                  value={
                    Object.keys(
                      report.risk_profile.category_distribution || {}
                    ).length
                  }
                />
                <StatBox
                  label="Mitigation Rate"
                  value={pctDecimal(report.risk_profile.overall_mitigation_rate)}
                />
              </div>
              {report.risk_profile.top_categories &&
                report.risk_profile.top_categories.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">
                      Top Categories
                    </h4>
                    <DataTable
                      headers={['Category', 'Count', '% of Total', 'Mitigation']}
                      rows={report.risk_profile.top_categories.map(
                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                        (cat: any) => [
                          cat.category,
                          cat.count,
                          `${cat.pct_of_total}%`,
                          `${cat.mitigation_rate}%`,
                        ]
                      )}
                    />
                  </div>
                )}
              {report.risk_profile.severity_distribution &&
                Object.keys(report.risk_profile.severity_distribution).length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">
                      Severity Distribution
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(
                        report.risk_profile.severity_distribution as Record<
                          string,
                          number
                        >
                      ).map(([severity, count]) => (
                        <span
                          key={severity}
                          className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${
                            severity === 'critical'
                              ? 'bg-red-100 text-red-700'
                              : severity === 'significant'
                                ? 'bg-orange-100 text-orange-700'
                                : severity === 'material'
                                  ? 'bg-amber-100 text-amber-700'
                                  : 'bg-gray-100 text-gray-700'
                          }`}
                        >
                          {severity}: {count}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
            </SectionCard>
          )}

          {/* Security Profile */}
          {report.security_profile && (
            <SectionCard title="Security & Covenant Profile">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <StatBox
                  label="Packages"
                  value={report.security_profile.n_packages ?? 0}
                />
                {report.security_profile.coverage_ratio?.median != null && (
                  <StatBox
                    label="Coverage Median"
                    value={`${report.security_profile.coverage_ratio.median.toFixed(2)}x`}
                  />
                )}
                {report.security_profile.additional_bonds_test_median != null && (
                  <StatBox
                    label="ABT Median"
                    value={`${report.security_profile.additional_bonds_test_median.toFixed(2)}x`}
                  />
                )}
              </div>
              {report.security_profile.pledge_type_distribution &&
                Object.keys(report.security_profile.pledge_type_distribution).length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">
                      Pledge Types
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(
                        report.security_profile.pledge_type_distribution as Record<string, number>
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
              {report.security_profile.dsrf_type_distribution &&
                Object.keys(report.security_profile.dsrf_type_distribution).length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">
                      DSRF Types
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(
                        report.security_profile.dsrf_type_distribution as Record<string, number>
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
            </SectionCard>
          )}

          {/* Spread Curve */}
          {report.spread_curve && report.spread_curve.rating_to_spread_bps && (
            <SectionCard title="Credit Spread Reference Curve">
              <DataTable
                headers={['Rating', 'Spread (bps)', 'Over AAA MMD']}
                rows={Object.entries(
                  report.spread_curve.rating_to_spread_bps as Record<
                    string,
                    number
                  >
                ).map(([rating, bps]) => [rating, bps, `+${bps}`])}
              />
              {report.spread_curve.sector_typical_range && (
                <p className="mt-3 text-sm text-gray-500">
                  Typical range: {report.spread_curve.sector_typical_range}
                </p>
              )}
            </SectionCard>
          )}

          {/* Market Activity */}
          {report.market_activity && (
            <SectionCard title="Secondary Market Activity">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatBox
                  label="Total Trades"
                  value={
                    report.market_activity.n_secondary_trades?.toLocaleString() ??
                    0
                  }
                />
                <StatBox
                  label="CUSIPs Tracked"
                  value={report.market_activity.n_cusips_tracked ?? 0}
                />
                {report.market_activity.avg_trades_per_bond != null && (
                  <StatBox
                    label="Avg Trades/Bond"
                    value={report.market_activity.avg_trades_per_bond.toFixed(1)}
                  />
                )}
                {report.market_activity.trade_size_median_usd != null && (
                  <StatBox
                    label="Median Trade Size"
                    value={fmt$(report.market_activity.trade_size_median_usd)}
                  />
                )}
              </div>
              {report.market_activity.yield_range && (
                <p className="mt-3 text-sm text-gray-500">
                  Yield range: {report.market_activity.yield_range[0]?.toFixed(2)}%
                  {' '}&ndash;{' '}
                  {report.market_activity.yield_range[1]?.toFixed(2)}% | Price
                  range:{' '}
                  {report.market_activity.price_range?.[0]?.toFixed(2)} &ndash;{' '}
                  {report.market_activity.price_range?.[1]?.toFixed(2)}
                </p>
              )}
            </SectionCard>
          )}

          {/* Rating Agency Perspective */}
          {report.rating_agency_perspective && (
            <SectionCard title="Rating Agency Perspective">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <StatBox
                  label="Rating Actions"
                  value={report.rating_agency_perspective.n_rating_actions ?? 0}
                />
                <StatBox
                  label="Rating Factors"
                  value={report.rating_agency_perspective.n_rating_factors ?? 0}
                />
                {report.rating_agency_perspective.action_distribution && (
                  <>
                    <StatBox
                      label="Upgrades"
                      value={
                        report.rating_agency_perspective.action_distribution
                          .upgrades ?? 0
                      }
                    />
                    <StatBox
                      label="Downgrades"
                      value={
                        report.rating_agency_perspective.action_distribution
                          .downgrades ?? 0
                      }
                    />
                  </>
                )}
              </div>
              {report.rating_agency_perspective.top_strengths &&
                report.rating_agency_perspective.top_strengths.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">
                      Top Strengths
                    </h4>
                    <ul className="space-y-1.5">
                      {report.rating_agency_perspective.top_strengths.map(
                        (s: string, i: number) => (
                          <li
                            key={i}
                            className="text-sm text-gray-700 flex items-start gap-2"
                          >
                            <span className="text-green-500 mt-0.5 flex-shrink-0">
                              +
                            </span>
                            <span>{s}</span>
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              {report.rating_agency_perspective.top_challenges &&
                report.rating_agency_perspective.top_challenges.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">
                      Top Challenges
                    </h4>
                    <ul className="space-y-1.5">
                      {report.rating_agency_perspective.top_challenges.map(
                        (s: string, i: number) => (
                          <li
                            key={i}
                            className="text-sm text-gray-700 flex items-start gap-2"
                          >
                            <span className="text-amber-500 mt-0.5 flex-shrink-0">
                              -
                            </span>
                            <span>{s}</span>
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              {report.rating_agency_perspective.agency_distribution &&
                Object.keys(report.rating_agency_perspective.agency_distribution)
                  .length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-600 mb-2">
                      By Agency
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(
                        report.rating_agency_perspective
                          .agency_distribution as Record<string, number>
                      ).map(([agency, count]) => (
                        <span
                          key={agency}
                          className="inline-flex items-center rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
                        >
                          {agency}: {count}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
            </SectionCard>
          )}

          <div className="flex items-center justify-between pt-4">
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
            <div className="text-xs text-gray-400">
              Generated: {report.generated_at?.slice(0, 10)} | Version:{' '}
              {report.report_version}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
