import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  ArrowLeft,
  TrendingUp,
  Loader2,
  Download,
  Building2,
  BarChart3,
  Scale,
  FileText,
} from 'lucide-react'
import { sensingApi, type CreditSpreadParams } from '../../services/sensingApi'
import { useSensing } from '../../contexts/SensingContext'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmt$(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
  return `$${n.toLocaleString()}`
}

function fmtPct(n: number | null | undefined, decimals = 2): string {
  if (n == null) return 'N/A'
  return `${n.toFixed(decimals)}%`
}

function fmtBps(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  return `${n.toFixed(1)} bps`
}

// Rating color helper
function ratingColor(rating: string): string {
  if (rating.startsWith('AAA')) return 'text-emerald-700 bg-emerald-50'
  if (rating.startsWith('AA')) return 'text-green-700 bg-green-50'
  if (rating.startsWith('A')) return 'text-blue-700 bg-blue-50'
  if (rating.startsWith('BBB')) return 'text-amber-700 bg-amber-50'
  if (rating.startsWith('BB')) return 'text-orange-700 bg-orange-50'
  return 'text-red-700 bg-red-50'
}

// ---------------------------------------------------------------------------
// Yield Curve Visualization (simple text-based)
// ---------------------------------------------------------------------------

function YieldCurveTable({
  curves,
}: {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  curves: Record<string, Record<string, number>>
}) {
  const ratings = ['AAA', 'AA', 'A', 'BBB', 'BB']
  const tenors = ['5', '10', '15', '20', '25', '30']

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2.5 px-3 font-medium text-gray-600">
              Rating
            </th>
            {tenors.map((t) => (
              <th
                key={t}
                className="text-right py-2.5 px-3 font-medium text-gray-600"
              >
                {t}yr
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {ratings
            .filter((r) => curves[r])
            .map((rating) => (
              <tr
                key={rating}
                className="border-b border-gray-100 hover:bg-gray-50"
              >
                <td className="py-2.5 px-3">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${ratingColor(rating)}`}
                  >
                    {rating}
                  </span>
                </td>
                {tenors.map((t) => (
                  <td
                    key={t}
                    className="text-right py-2.5 px-3 text-gray-800 font-mono"
                  >
                    {curves[rating]?.[t] != null
                      ? fmtPct(curves[rating][t])
                      : '-'}
                  </td>
                ))}
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Cost of Capital Grid
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CostGrid({ rows }: { rows: any[] }) {
  // Group by rating
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const byRating: Record<string, any[]> = {}
  for (const row of rows) {
    if (!byRating[row.rating]) byRating[row.rating] = []
    byRating[row.rating].push(row)
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b-2 border-gray-300">
            <th className="text-left py-3 px-3 font-semibold text-gray-700">
              Rating
            </th>
            <th className="text-center py-3 px-3 font-semibold text-gray-700">
              Tenor
            </th>
            <th className="text-right py-3 px-3 font-semibold text-gray-700">
              AAA Base
            </th>
            <th className="text-right py-3 px-3 font-semibold text-gray-700">
              Sector Spread
            </th>
            <th className="text-right py-3 px-3 font-semibold text-gray-700">
              Est. Yield
            </th>
            <th className="text-right py-3 px-3 font-semibold text-gray-700">
              Issuer + Costs
            </th>
            <th className="text-right py-3 px-3 font-semibold text-muni-navy">
              All-In TIC
            </th>
            <th className="text-right py-3 px-3 font-semibold text-gray-500">
              Corpus Obs.
            </th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(byRating).map(([rating, ratingRows]) =>
            ratingRows.map((row, i) => (
              <tr
                key={`${rating}-${row.tenor}`}
                className={`border-b border-gray-100 hover:bg-gray-50 ${i === 0 ? 'border-t border-gray-200' : ''}`}
              >
                <td className="py-2.5 px-3">
                  {i === 0 && (
                    <span
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${ratingColor(rating)}`}
                    >
                      {rating}
                    </span>
                  )}
                </td>
                <td className="text-center py-2.5 px-3 text-gray-700">
                  {row.tenor}yr
                </td>
                <td className="text-right py-2.5 px-3 text-gray-600 font-mono">
                  {fmtPct(row.base_aaa_yield)}
                </td>
                <td className="text-right py-2.5 px-3 text-gray-600 font-mono">
                  +{fmtBps(row.sector_spread_bps)}
                </td>
                <td className="text-right py-2.5 px-3 text-gray-800 font-mono font-medium">
                  {fmtPct(row.estimated_yield)}
                </td>
                <td className="text-right py-2.5 px-3 text-gray-600 font-mono">
                  +{fmtBps(row.issuer_fee_bps + row.structural_cost_bps)}
                </td>
                <td className="text-right py-2.5 px-3 text-muni-navy font-mono font-bold">
                  {fmtPct(row.all_in_tic)}
                </td>
                <td className="text-right py-2.5 px-3 text-gray-400 font-mono text-xs">
                  {row.corpus_observed_yield != null ? (
                    <span title={`${row.n_corpus_obs} observations`}>
                      {fmtPct(row.corpus_observed_yield)} ({row.n_corpus_obs})
                    </span>
                  ) : (
                    '-'
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Issuer Comparison
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function IssuerComparisonPanel({ comparisons }: { comparisons: any[] }) {
  if (!comparisons || comparisons.length === 0) return null

  return (
    <div className="space-y-4">
      {comparisons.map((comp) => (
        <div
          key={`${comp.rating}-${comp.tenor}`}
          className="border border-gray-200 rounded-lg p-4"
        >
          <div className="flex items-center gap-2 mb-3">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${ratingColor(comp.rating)}`}
            >
              {comp.rating}
            </span>
            <span className="text-sm text-gray-600">{comp.tenor}-year</span>
            <span className="text-sm text-gray-400">|</span>
            <span className="text-sm text-gray-600">
              Base yield: {fmtPct(comp.base_yield)}
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 px-3 font-medium text-gray-600">
                    Issuer
                  </th>
                  <th className="text-right py-2 px-3 font-medium text-gray-600">
                    Issuer Fee
                  </th>
                  <th className="text-right py-2 px-3 font-medium text-gray-600">
                    Total Costs
                  </th>
                  <th className="text-right py-2 px-3 font-medium text-gray-600">
                    Annual on $50M
                  </th>
                  <th className="text-right py-2 px-3 font-semibold text-muni-navy">
                    All-In TIC
                  </th>
                </tr>
              </thead>
              <tbody>
                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                {comp.comparisons.map((c: any) => {
                  const isBest =
                    c.all_in_tic ===
                    Math.min(
                      // eslint-disable-next-line @typescript-eslint/no-explicit-any
                      ...comp.comparisons.map((x: any) => x.all_in_tic)
                    )
                  return (
                    <tr
                      key={c.issuer_key}
                      className={`border-b border-gray-100 ${isBest ? 'bg-emerald-50' : 'hover:bg-gray-50'}`}
                    >
                      <td className="py-2.5 px-3 text-gray-800 font-medium">
                        {c.issuer}
                        {isBest && (
                          <span className="ml-2 text-xs text-emerald-600 font-normal">
                            lowest
                          </span>
                        )}
                      </td>
                      <td className="text-right py-2.5 px-3 font-mono text-gray-600">
                        {fmtBps(c.issuer_fee_bps)}
                      </td>
                      <td className="text-right py-2.5 px-3 font-mono text-gray-600">
                        {fmtBps(c.total_cost_bps)}
                      </td>
                      <td className="text-right py-2.5 px-3 font-mono text-gray-600">
                        {fmt$(c.annual_fee_on_par)}
                      </td>
                      <td className="text-right py-2.5 px-3 font-mono font-bold text-muni-navy">
                        {fmtPct(c.all_in_tic)}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Recent Comps Table
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function RecentCompsTable({ comps }: { comps: any[] }) {
  if (!comps || comps.length === 0) return null

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2.5 px-3 font-medium text-gray-600">
              Issuer
            </th>
            <th className="text-center py-2.5 px-3 font-medium text-gray-600">
              Rating
            </th>
            <th className="text-right py-2.5 px-3 font-medium text-gray-600">
              Yield
            </th>
            <th className="text-right py-2.5 px-3 font-medium text-gray-600">
              Par Amount
            </th>
            <th className="text-center py-2.5 px-3 font-medium text-gray-600">
              Maturity
            </th>
            <th className="text-center py-2.5 px-3 font-medium text-gray-600">
              Trade Date
            </th>
            <th className="text-center py-2.5 px-3 font-medium text-gray-600">
              CUSIP
            </th>
          </tr>
        </thead>
        <tbody>
          {comps.map((c, i) => (
            <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
              <td
                className="py-2.5 px-3 text-gray-800 max-w-[250px] truncate"
                title={c.issuer}
              >
                {c.issuer}
              </td>
              <td className="text-center py-2.5 px-3">
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold ${ratingColor(c.rating_bucket)}`}
                >
                  {c.rating_bucket}
                </span>
              </td>
              <td className="text-right py-2.5 px-3 font-mono text-gray-800">
                {fmtPct(c.yield)}
              </td>
              <td className="text-right py-2.5 px-3 text-gray-600">
                {fmt$(c.par_amount)}
              </td>
              <td className="text-center py-2.5 px-3 text-gray-600">
                {c.maturity_date || '-'}
              </td>
              <td className="text-center py-2.5 px-3 text-gray-600">
                {c.trade_date || '-'}
              </td>
              <td className="text-center py-2.5 px-3 font-mono text-gray-400 text-xs">
                {c.cusip || '-'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Fee Schedule Display
// ---------------------------------------------------------------------------

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function FeeScheduleCards({ fees }: { fees: any[] }) {
  if (!fees || fees.length === 0) return null

  return (
    <div className="grid gap-4 md:grid-cols-3">
      {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
      {fees.map((f: any) => (
        <div
          key={f.key}
          className="border border-gray-200 rounded-lg p-4 bg-white"
        >
          <h4 className="font-semibold text-gray-900 text-sm mb-3">
            {f.display_name}
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-500">Annual Fee</span>
              <span className="font-mono font-medium">
                {f.annual_fee_bps} bps
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Minimum</span>
              <span className="font-mono">{fmt$(f.annual_fee_min_usd)}/yr</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Upfront</span>
              <span className="font-mono">
                {f.upfront_fee_bps > 0
                  ? `${f.upfront_fee_bps} bps + ${fmt$(f.upfront_fee_flat_usd)}`
                  : 'Negotiable'}
              </span>
            </div>
            {f.out_of_state_surcharge_bps > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500">Out-of-State</span>
                <span className="font-mono">
                  +{f.out_of_state_surcharge_bps} bps
                </span>
              </div>
            )}
            <div className="border-t border-gray-100 pt-2 mt-2 flex justify-between">
              <span className="text-gray-500">Example: $50M issue</span>
              <span className="font-mono font-medium text-muni-navy">
                {fmt$(f.example_annual_on_50m)}/yr
              </span>
            </div>
          </div>
          {f.notes && f.notes.length > 0 && (
            <ul className="mt-3 space-y-1">
              {f.notes.slice(0, 3).map((n: string, i: number) => (
                <li key={i} className="text-xs text-gray-400 leading-relaxed">
                  {n}
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Corpus Spread Summary
// ---------------------------------------------------------------------------

function CorpusSpreadSummary({
  spreads,
}: {
  spreads: Record<string, { n_observations: number; median_yield: number; min_yield: number; max_yield: number; spread_over_aaa_bps: number | null }>
}) {
  const ratings = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B']
  const available = ratings.filter((r) => spreads[r])

  if (available.length === 0) return null

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200">
            <th className="text-left py-2.5 px-3 font-medium text-gray-600">
              Rating
            </th>
            <th className="text-right py-2.5 px-3 font-medium text-gray-600">
              Observations
            </th>
            <th className="text-right py-2.5 px-3 font-medium text-gray-600">
              Median Yield
            </th>
            <th className="text-right py-2.5 px-3 font-medium text-gray-600">
              Range
            </th>
            <th className="text-right py-2.5 px-3 font-medium text-gray-600">
              Spread vs AAA
            </th>
          </tr>
        </thead>
        <tbody>
          {available.map((r) => {
            const s = spreads[r]
            return (
              <tr key={r} className="border-b border-gray-100">
                <td className="py-2.5 px-3">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${ratingColor(r)}`}
                  >
                    {r}
                  </span>
                </td>
                <td className="text-right py-2.5 px-3 text-gray-600">
                  {s.n_observations}
                </td>
                <td className="text-right py-2.5 px-3 font-mono text-gray-800">
                  {fmtPct(s.median_yield)}
                </td>
                <td className="text-right py-2.5 px-3 font-mono text-gray-500 text-xs">
                  {fmtPct(s.min_yield)} - {fmtPct(s.max_yield)}
                </td>
                <td className="text-right py-2.5 px-3 font-mono text-gray-800">
                  {s.spread_over_aaa_bps != null
                    ? `+${s.spread_over_aaa_bps.toFixed(0)} bps`
                    : 'base'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Section wrapper
// ---------------------------------------------------------------------------

function Section({
  title,
  icon: Icon,
  children,
  defaultOpen = true,
}: {
  title: string
  icon: React.ComponentType<{ className?: string }>
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
        <div className="flex items-center gap-2.5">
          <Icon className="h-5 w-5 text-muni-teal" />
          <h3 className="font-semibold text-gray-900 text-base">{title}</h3>
        </div>
        <svg
          className={`h-5 w-5 text-gray-400 transition-transform ${open ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {open && <div className="px-5 pb-5 pt-1">{children}</div>}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function CreditSpreadMonitor() {
  const sensing = useSensing()
  const [sector, setSector] = useState(sensing.sector || 'healthcare')
  const [parAmount, setParAmount] = useState('50000000')
  const [outOfState, setOutOfState] = useState(false)

  const sectorsQuery = useQuery({
    queryKey: ['sensing-sectors'],
    queryFn: sensingApi.listSectors,
  })

  const spreadMutation = useMutation({
    mutationFn: sensingApi.getCreditSpreads,
  })

  // Auto-load on mount with defaults
  useEffect(() => {
    spreadMutation.mutate({ sector, par_amount: 50_000_000, out_of_state: false })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Store results in shared context
  useEffect(() => {
    if (spreadMutation.data) {
      sensing.setCreditSpreads(spreadMutation.data)
      sensing.setSector(sector)
    }
  }, [spreadMutation.data]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const par = parseFloat(parAmount.replace(/[,$]/g, ''))
    if (isNaN(par) || par <= 0) return
    const params: CreditSpreadParams = {
      sector,
      par_amount: par,
      out_of_state: outOfState,
    }
    spreadMutation.mutate(params)
  }

  const data = spreadMutation.data

  return (
    <div className="max-w-6xl mx-auto">
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
              Credit Spread Monitor
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              All-in cost of capital comparison powered by our municipal bond corpus &amp;
              live AAA MMD curve
            </p>
          </div>
        </div>
      </div>

      {/* Parameters Bar */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg border border-gray-200 shadow-sm p-5 mb-6"
      >
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
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
              Representative Par ($)
            </label>
            <input
              type="text"
              className="input w-full"
              placeholder="50,000,000"
              value={parAmount}
              onChange={(e) => setParAmount(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2 pt-6">
            <input
              id="oos"
              type="checkbox"
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              checked={outOfState}
              onChange={(e) => setOutOfState(e.target.checked)}
            />
            <label htmlFor="oos" className="text-sm text-gray-700">
              Out-of-state borrower
            </label>
          </div>
          <div className="md:col-span-2 flex justify-end">
            <button
              type="submit"
              className="btn btn-primary flex items-center gap-2"
              disabled={spreadMutation.isPending}
            >
              {spreadMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <TrendingUp className="h-4 w-4" />
                  Update Analysis
                </>
              )}
            </button>
          </div>
        </div>
      </form>

      {spreadMutation.error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
          Failed to load: {String(spreadMutation.error)}
        </div>
      )}

      {spreadMutation.isPending && !data && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          <span className="ml-3 text-gray-500">
            Loading credit spread data...
          </span>
        </div>
      )}

      {data && (
        <div className="space-y-5">
          {/* Summary Banner */}
          <div className="bg-muni-navy rounded-lg p-6 text-white">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">
                {sector.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}{' '}
                Sector &mdash; Cost of Capital Overview
              </h2>
              <div className="text-sm text-gray-300">
                AAA curve:{' '}
                <span className="text-muni-teal font-medium">
                  {data.aaa_curve_source}
                </span>{' '}
                | As of {data.aaa_curve_date}
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider">
                  AAA 10yr
                </div>
                <div className="text-xl font-semibold text-muni-teal">
                  {data.yield_curves?.AAA?.['10']
                    ? fmtPct(data.yield_curves.AAA['10'])
                    : '-'}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider">
                  AAA 30yr
                </div>
                <div className="text-xl font-semibold text-muni-teal">
                  {data.yield_curves?.AAA?.['30']
                    ? fmtPct(data.yield_curves.AAA['30'])
                    : '-'}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider">
                  A-rated 30yr TIC
                </div>
                <div className="text-xl font-semibold text-white">
                  {data.cost_grid?.find(
                    // eslint-disable-next-line @typescript-eslint/no-explicit-any
                    (r: any) => r.rating === 'A' && r.tenor === 30
                  )
                    ? fmtPct(
                        data.cost_grid.find(
                          // eslint-disable-next-line @typescript-eslint/no-explicit-any
                          (r: any) => r.rating === 'A' && r.tenor === 30
                        ).all_in_tic
                      )
                    : '-'}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider">
                  Corpus Trades
                </div>
                <div className="text-xl font-semibold text-white">
                  {data.recent_comps?.length || 0}
                </div>
              </div>
            </div>
          </div>

          {/* Yield Curves */}
          {data.yield_curves && (
            <Section title="Municipal Yield Curves by Rating" icon={TrendingUp}>
              <p className="text-sm text-gray-500 mb-4">
                Current estimated tax-exempt yields by rating tier and tenor.
                AAA base from {data.aaa_curve_source}; spreads from reference
                table blended with corpus observations.
              </p>
              <YieldCurveTable curves={data.yield_curves} />
            </Section>
          )}

          {/* Cost of Capital Grid */}
          {data.cost_grid && data.cost_grid.length > 0 && (
            <Section
              title="All-In Cost of Capital Grid"
              icon={BarChart3}
            >
              <p className="text-sm text-gray-500 mb-4">
                Estimated all-in True Interest Cost (TIC) by rating and tenor,
                including base yield, sector credit spread, issuer fees, and
                structural costs (underwriter, counsel, trustee, rating agency,
                DSRF).
              </p>
              <CostGrid rows={data.cost_grid} />
            </Section>
          )}

          {/* Issuer Comparison */}
          {data.issuer_comparisons && data.issuer_comparisons.length > 0 && (
            <Section title="Issuer Channel Comparison" icon={Building2}>
              <p className="text-sm text-gray-500 mb-4">
                Side-by-side cost comparison across issuance channels. Shows how
                issuer fee structures affect all-in TIC for representative
                rating/tenor combinations.
              </p>
              <IssuerComparisonPanel comparisons={data.issuer_comparisons} />
            </Section>
          )}

          {/* Corpus-Derived Spreads */}
          <Section
            title="Observed Spreads"
            icon={Scale}
            defaultOpen={false}
          >
            <p className="text-sm text-gray-500 mb-4">
              Credit spreads derived from actual secondary market trades in
              our corpus for this sector. These observations inform the
              blended spread estimates in the cost grid above.
            </p>
            {data.corpus_spreads &&
            Object.keys(data.corpus_spreads).length > 0 ? (
              <CorpusSpreadSummary spreads={data.corpus_spreads} />
            ) : (
              <div className="text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-200">
                <Scale className="h-8 w-8 text-gray-300 mx-auto mb-3" />
                <p className="text-sm font-medium text-gray-500">
                  No corpus trade observations yet for this sector
                </p>
                <p className="text-xs text-gray-400 mt-1 max-w-md mx-auto">
                  Observed data for this sector is coming soon.
                </p>
              </div>
            )}
          </Section>

          {/* Recent Comps */}
          <Section
            title="Recent Comparable Deals"
            icon={FileText}
            defaultOpen={false}
          >
            <p className="text-sm text-gray-500 mb-4">
              Most recent observed trades from our corpus in this sector, sorted by
              trade date. Use these as conversation-ready comps for borrower
              discussions.
            </p>
            {data.recent_comps && data.recent_comps.length > 0 ? (
              <RecentCompsTable comps={data.recent_comps} />
            ) : (
              <div className="text-center py-8 bg-gray-50 rounded-lg border border-dashed border-gray-200">
                <FileText className="h-8 w-8 text-gray-300 mx-auto mb-3" />
                <p className="text-sm font-medium text-gray-500">
                  No comparable deals in the corpus yet
                </p>
                <p className="text-xs text-gray-400 mt-1 max-w-md mx-auto">
                  As sector data is added, trades will appear here.
                </p>
              </div>
            )}
          </Section>

          {/* Fee Schedules */}
          {data.fee_schedules && data.fee_schedules.length > 0 && (
            <Section
              title="Issuer Fee Schedules"
              icon={Building2}
              defaultOpen={false}
            >
              <p className="text-sm text-gray-500 mb-4">
                Detailed fee structures for each issuance channel. Actual fees
                are subject to negotiation between borrower&apos;s counsel and
                issuer&apos;s counsel.
              </p>
              <FeeScheduleCards fees={data.fee_schedules} />
            </Section>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-4">
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
            <div className="text-xs text-gray-400">
              Generated: {data.generated_at?.slice(0, 10)} | Sector:{' '}
              {data.sector}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
