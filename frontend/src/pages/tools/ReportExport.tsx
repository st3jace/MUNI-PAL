/**
 * Combined Sensing Report — Lead capture + PDF export.
 *
 * Collects all 3 tool results (market intelligence, benchmark, readiness)
 * and generates a combined PDF report after the user fills out a lead
 * capture form. The backend records the lead and links all prior
 * session events.
 */
import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useSensing } from '../../contexts/SensingContext'
import {
  ArrowLeft,
  Download,
  Loader2,
  CheckCircle2,
  FileText,
  BarChart3,
  Calculator,
  ClipboardCheck,
  TrendingUp,
} from 'lucide-react'
import { sensingApi, getSensingSessionId } from '../../services/sensingApi'

// Dynamically import html2pdf (it's a CJS module)
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let html2pdf: any = null

const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA',
  'HI','ID','IL','IN','IA','KS','KY','LA','ME','MD',
  'MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ',
  'NM','NY','NC','ND','OH','OK','OR','PA','RI','SC',
  'SD','TN','TX','UT','VT','VA','WA','WV','WI','WY','DC',
]

const REFERRAL_SOURCES = [
  'Search Engine',
  'Industry Conference',
  'Municipal Advisor Referral',
  'Bond Counsel Referral',
  'Trade Publication',
  'Professional Network',
  'Other',
]

function fmt$(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  if (Math.abs(n) >= 1e3) return `$${(n / 1e3).toFixed(0)}K`
  return `$${n.toLocaleString()}`
}

export default function ReportExport() {
  const sensing = useSensing()

  const [showForm, setShowForm] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [leadCaptured, setLeadCaptured] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Lead form fields
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [organization, setOrganization] = useState('')
  const [privacyConsent, setPrivacyConsent] = useState(false)
  const [title, setTitle] = useState('')
  const [phone, setPhone] = useState('')
  const [dealSize, setDealSize] = useState('')
  const [state, setState] = useState('')
  const [rating, setRating] = useState('')
  const [referralSource, setReferralSource] = useState('')

  const reportRef = useRef<HTMLDivElement>(null)

  // Pre-fill from benchmark inputs if available
  useEffect(() => {
    if (sensing.benchmarkInputs) {
      const bi = sensing.benchmarkInputs
      if (bi.deal_size) setDealSize(String(bi.deal_size))
      if (bi.state) setState(bi.state)
      if (bi.rating) setRating(bi.rating)
    }
  }, [sensing.benchmarkInputs])

  // Track page view
  useEffect(() => {
    sensingApi.trackEvent({
      session_id: getSensingSessionId(),
      event_type: 'report_export_viewed',
      sector: sensing.sector,
    })
  }, [sensing.sector])

  const hasData = sensing.marketIntel || sensing.benchmark || sensing.readiness || sensing.creditSpreads
  const componentCount = sensing.completedCount

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setGenerating(true)

    try {
      // 1. Capture lead in backend
      await sensingApi.captureLead({
        email,
        name,
        organization,
        title: title || undefined,
        phone: phone || undefined,
        sector: sensing.sector || 'healthcare',
        deal_size_estimate: dealSize ? parseFloat(dealSize.replace(/[,$]/g, '')) : undefined,
        state: state || undefined,
        expected_rating: rating || undefined,
        referral_source: referralSource || undefined,
        session_id: getSensingSessionId(),
        privacy_consent: privacyConsent,
        consent_version: 'sensing-lead-v1',
        market_intel_json: sensing.marketIntel
          ? JSON.stringify(sensing.marketIntel)
          : undefined,
        benchmark_json: sensing.benchmark
          ? JSON.stringify(sensing.benchmark)
          : undefined,
        readiness_json: sensing.readiness
          ? JSON.stringify(sensing.readiness)
          : undefined,
      })

      setLeadCaptured(true)

      // 2. Generate PDF
      if (!html2pdf) {
        const mod = await import('html2pdf.js')
        html2pdf = mod.default || mod
      }

      if (reportRef.current) {
        const sectorName = (sensing.sector || 'sector')
          .replace('_', ' ')
          .replace(/\b\w/g, (c: string) => c.toUpperCase())

        await html2pdf()
          .set({
            margin: [12, 12, 12, 12],
            filename: `Muni-Pal_Readiness_Benchmark_Report_${sectorName}_${new Date().toISOString().slice(0, 10)}.pdf`,
            image: { type: 'jpeg', quality: 0.95 },
            html2canvas: { scale: 2, useCORS: true, logging: false },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
            pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
          })
          .from(reportRef.current)
          .save()

        // Track download
        await sensingApi.trackEvent({
          session_id: getSensingSessionId(),
          event_type: 'report_downloaded',
          sector: sensing.sector,
        })
      }
    } catch (err) {
      setError(String(err))
    } finally {
      setGenerating(false)
    }
  }

  const mi = sensing.marketIntel
  const bm = sensing.benchmark
  const ra = sensing.readiness
  const cs = sensing.creditSpreads

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-start gap-4">
        <Link to="/tools" className="mt-1 text-gray-400 hover:text-gray-600">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">
            Export Combined Report
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Download everything you've generated here as one free PDF
          </p>
        </div>
      </div>

      {!hasData ? (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-8 text-center">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Nothing to export yet
          </h2>
          <p className="text-sm text-gray-500 mb-6 max-w-md mx-auto">
            Run any of the free tools first — your results collect here
            automatically, ready to download as one PDF.
          </p>
          <div className="flex justify-center gap-3">
            <Link
              to="/tools/market-intelligence"
              className="btn btn-secondary text-sm"
            >
              Market Intelligence
            </Link>
            <Link to="/tools/benchmark" className="btn btn-secondary text-sm">
              Benchmarking
            </Link>
            <Link to="/tools/readiness" className="btn btn-secondary text-sm">
              Readiness
            </Link>
          </div>
        </div>
      ) : (
        <>
          {/* Report Status Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div
              className={`rounded-lg border p-4 ${mi ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <BarChart3
                  className={`h-4 w-4 ${mi ? 'text-green-600' : 'text-gray-400'}`}
                />
                <span className="text-sm font-medium text-gray-800">
                  Market Intelligence
                </span>
              </div>
              <p className="text-xs text-gray-500">
                {mi ? 'Included in report' : 'Not generated'}
              </p>
            </div>
            <div
              className={`rounded-lg border p-4 ${bm ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Calculator
                  className={`h-4 w-4 ${bm ? 'text-green-600' : 'text-gray-400'}`}
                />
                <span className="text-sm font-medium text-gray-800">
                  Benchmark Results
                </span>
              </div>
              <p className="text-xs text-gray-500">
                {bm ? 'Included in report' : 'Not generated'}
              </p>
            </div>
            <div
              className={`rounded-lg border p-4 ${ra ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <ClipboardCheck
                  className={`h-4 w-4 ${ra ? 'text-green-600' : 'text-gray-400'}`}
                />
                <span className="text-sm font-medium text-gray-800">
                  Readiness Assessment
                </span>
              </div>
              <p className="text-xs text-gray-500">
                {ra ? 'Included in report' : 'Not generated'}
              </p>
            </div>
            <div
              className={`rounded-lg border p-4 ${cs ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp
                  className={`h-4 w-4 ${cs ? 'text-green-600' : 'text-gray-400'}`}
                />
                <span className="text-sm font-medium text-gray-800">
                  Credit Spreads
                </span>
              </div>
              <p className="text-xs text-gray-500">
                {cs ? 'Included in report' : 'Not generated'}
              </p>
            </div>
          </div>

          {/* Action area */}
          {!showForm && !leadCaptured && (
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 text-center mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                Ready to export {componentCount} report
                {componentCount !== 1 ? ' sections' : ' section'}
              </h2>
              <p className="text-sm text-gray-500 mb-4">
                Tell us who to prepare it for and the PDF downloads immediately
                — free.
              </p>
              <button
                className="btn btn-primary flex items-center gap-2 mx-auto"
                onClick={() => setShowForm(true)}
              >
                <Download className="h-4 w-4" />
                Get Your Report
              </button>
            </div>
          )}

          {/* Lead Capture Form */}
          {showForm && !leadCaptured && (
            <form
              onSubmit={handleSubmit}
              className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mb-6"
            >
              <h2 className="text-lg font-semibold text-gray-900 mb-1">
                Get Your Report
              </h2>
              <p className="text-sm text-gray-500 mb-5">
                We'll prepare your customized PDF with the analysis results.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    className="input w-full"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Jane Smith"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Email *
                  </label>
                  <input
                    type="email"
                    className="input w-full"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="jane@municipality.gov"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Organization *
                  </label>
                  <input
                    type="text"
                    className="input w-full"
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    placeholder="City of Springfield"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Title / Role
                  </label>
                  <input
                    type="text"
                    className="input w-full"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Finance Director"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Phone
                  </label>
                  <input
                    type="tel"
                    className="input w-full"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="(555) 123-4567"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1.5">
                    Estimated Deal Size
                  </label>
                  <input
                    type="text"
                    className="input w-full"
                    value={dealSize}
                    onChange={(e) => setDealSize(e.target.value)}
                    placeholder="50,000,000"
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
                    How did you hear about us?
                  </label>
                  <select
                    className="input w-full"
                    value={referralSource}
                    onChange={(e) => setReferralSource(e.target.value)}
                  >
                    <option value="">Select...</option>
                    {REFERRAL_SOURCES.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <label className="flex items-start gap-3 text-sm text-gray-600 mb-4">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={privacyConsent}
                  onChange={(e) => setPrivacyConsent(e.target.checked)}
                  required
                />
                <span>
                  I consent to Muni-Pal collecting my contact details, organization context,
                  sector/deal context, session events, and selected report snapshots to prepare
                  this report and evaluate pilot fit. Outputs are screening artifacts, not legal
                  advice, municipal advisory advice, deal approval, pricing, sizing, or issuance instructions.
                </span>
              </label>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 text-sm mb-4">
                  {error}
                </div>
              )}

              <div className="flex items-center justify-between">
                <button
                  type="button"
                  className="text-sm text-gray-500 hover:text-gray-700"
                  onClick={() => setShowForm(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary flex items-center gap-2"
                  disabled={generating}
                >
                  {generating ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Generating PDF...
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4" />
                      Download Report
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* Success state */}
          {leadCaptured && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center mb-6">
              <CheckCircle2 className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <h2 className="text-lg font-semibold text-green-800 mb-1">
                Report Downloaded
              </h2>
              <p className="text-sm text-green-600 mb-4">
                Your PDF has been generated. Check your downloads folder.
              </p>
              <button
                className="btn btn-primary flex items-center gap-2 mx-auto"
                onClick={async () => {
                  setGenerating(true)
                  try {
                    if (!html2pdf) {
                      const mod = await import('html2pdf.js')
                      html2pdf = mod.default || mod
                    }
                    if (reportRef.current) {
                      const sectorName = (sensing.sector || 'sector')
                        .replace('_', ' ')
                        .replace(/\b\w/g, (c: string) => c.toUpperCase())
                      await html2pdf()
                        .set({
                          margin: [12, 12, 12, 12],
                          filename: `Muni-Pal_Readiness_Benchmark_Report_${sectorName}_${new Date().toISOString().slice(0, 10)}.pdf`,
                          image: { type: 'jpeg', quality: 0.95 },
                          html2canvas: { scale: 2, useCORS: true, logging: false },
                          jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
                          pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
                        })
                        .from(reportRef.current)
                        .save()
                    }
                  } finally {
                    setGenerating(false)
                  }
                }}
                disabled={generating}
              >
                {generating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Download className="h-4 w-4" />
                )}
                Download Again
              </button>
            </div>
          )}

          {/* Hidden PDF content (rendered offscreen for html2pdf) */}
          <div
            ref={reportRef}
            className="bg-white"
            style={{
              position: leadCaptured ? 'relative' : 'absolute',
              left: leadCaptured ? 'auto' : '-9999px',
              width: '210mm',
              padding: '20mm',
              fontFamily: 'system-ui, -apple-system, sans-serif',
              fontSize: '11px',
              lineHeight: '1.5',
              color: '#1f2937',
            }}
          >
            {/* Cover */}
            <div style={{ textAlign: 'center', marginBottom: '30px' }}>
              <h1
                style={{
                  fontSize: '24px',
                  fontWeight: 700,
                  color: '#0f172a',
                  marginBottom: '6px',
                }}
              >
                Municipal Bond Readiness &amp; Benchmark Report
              </h1>
              <p style={{ fontSize: '14px', color: '#64748b' }}>
                {sensing.sector
                  ?.replace('_', ' ')
                  .replace(/\b\w/g, (c: string) => c.toUpperCase())}{' '}
                Sector
              </p>
              <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                Generated {new Date().toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}{' '}
                | Powered by Muni-Pal
              </p>
              <hr
                style={{
                  border: 'none',
                  borderTop: '2px solid #0f172a',
                  marginTop: '20px',
                }}
              />
            </div>

            {/* Section 1: Market Intelligence */}
            {mi && (
              <div style={{ marginBottom: '24px' }} className="pdf-section">
                <h2
                  style={{
                    fontSize: '16px',
                    fontWeight: 700,
                    color: '#0f172a',
                    borderBottom: '1px solid #e2e8f0',
                    paddingBottom: '6px',
                    marginBottom: '12px',
                  }}
                >
                  1. Sector Market Intelligence
                </h2>

                {mi.executive_summary?.key_findings && (
                  <div style={{ marginBottom: '12px' }}>
                    <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                      Key Findings
                    </h3>
                    <ul style={{ paddingLeft: '16px', margin: 0 }}>
                      {mi.executive_summary.key_findings.map(
                        (f: string, i: number) => (
                          <li key={i} style={{ marginBottom: '3px' }}>
                            {f}
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr 1fr',
                    gap: '8px',
                    marginBottom: '12px',
                  }}
                >
                  {mi.deal_structure && (
                    <PdfStat
                      label="Deals Analyzed"
                      value={String(mi.deal_structure.n_deals ?? 0)}
                    />
                  )}
                  {mi.deal_structure && (
                    <PdfStat
                      label="Total Par"
                      value={fmt$(mi.deal_structure.par_amount_total_usd)}
                    />
                  )}
                  {mi.rating_distribution && (
                    <PdfStat
                      label="Modal Rating"
                      value={mi.rating_distribution.modal_rating || 'N/A'}
                    />
                  )}
                  {mi.financial_benchmarks?.dscr_median != null && (
                    <PdfStat
                      label="DSCR Median"
                      value={`${mi.financial_benchmarks.dscr_median.toFixed(2)}x`}
                    />
                  )}
                  {mi.rating_distribution && (
                    <PdfStat
                      label="IG %"
                      value={`${mi.rating_distribution.investment_grade_pct?.toFixed(1)}%`}
                    />
                  )}
                  {mi.market_activity && (
                    <PdfStat
                      label="Secondary Trades"
                      value={mi.market_activity.n_secondary_trades?.toLocaleString() ?? '0'}
                    />
                  )}
                </div>
              </div>
            )}

            {/* Section 2: Benchmark */}
            {bm && (
              <div style={{ marginBottom: '24px' }} className="pdf-section">
                <h2
                  style={{
                    fontSize: '16px',
                    fontWeight: 700,
                    color: '#0f172a',
                    borderBottom: '1px solid #e2e8f0',
                    paddingBottom: '6px',
                    marginBottom: '12px',
                  }}
                >
                  2. Issuance Benchmark
                </h2>

                {bm.spread_estimate && (
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr 1fr 1fr',
                      gap: '8px',
                      marginBottom: '12px',
                    }}
                  >
                    <PdfStat
                      label="Expected Spread"
                      value={
                        bm.spread_estimate.expected_spread_bps != null
                          ? `${bm.spread_estimate.expected_spread_bps} bps`
                          : 'N/A'
                      }
                    />
                    <PdfStat
                      label="Sector Median"
                      value={
                        bm.spread_estimate.sector_median_spread_bps != null
                          ? `${bm.spread_estimate.sector_median_spread_bps} bps`
                          : 'N/A'
                      }
                    />
                    <PdfStat
                      label="vs. Sector"
                      value={bm.spread_estimate.spread_vs_sector || 'N/A'}
                    />
                    <PdfStat
                      label="Rating"
                      value={bm.spread_estimate.rating_normalized || 'N/A'}
                    />
                  </div>
                )}

                {bm.peer_comparison?.top_peers?.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                      Peer Comparison ({bm.peer_comparison.n_peers} peers)
                    </h3>
                    <table
                      style={{
                        width: '100%',
                        borderCollapse: 'collapse',
                        fontSize: '10px',
                      }}
                    >
                      <thead>
                        <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>
                            Issuer
                          </th>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>
                            Par
                          </th>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>
                            State
                          </th>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>
                            Similarity
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                        {bm.peer_comparison.top_peers.slice(0, 8).map((p: any, i: number) => (
                          <tr
                            key={i}
                            style={{ borderBottom: '1px solid #f1f5f9' }}
                          >
                            <td style={{ padding: '3px 6px' }}>
                              {p.issuer_name || p.cusip_9}
                            </td>
                            <td style={{ padding: '3px 6px' }}>
                              {fmt$(p.par_amount)}
                            </td>
                            <td style={{ padding: '3px 6px' }}>{p.state}</td>
                            <td style={{ padding: '3px 6px' }}>
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

            {/* Section 3: Readiness Assessment */}
            {ra && (
              <div style={{ marginBottom: '24px' }} className="pdf-section">
                <h2
                  style={{
                    fontSize: '16px',
                    fontWeight: 700,
                    color: '#0f172a',
                    borderBottom: '1px solid #e2e8f0',
                    paddingBottom: '6px',
                    marginBottom: '12px',
                  }}
                >
                  3. Bond Readiness Assessment
                </h2>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr 1fr',
                    gap: '8px',
                    marginBottom: '12px',
                  }}
                >
                  <PdfStat
                    label="Readiness Score"
                    value={`${ra.readiness_score}/100`}
                  />
                  <PdfStat label="Tier" value={ra.tier || 'N/A'} />
                  <PdfStat
                    label="Evidence"
                    value={`${ra.evidence_present ?? 0}/${ra.evidence_possible ?? 25}`}
                  />
                </div>

                {ra.dimensions && ra.dimensions.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                      Dimension Scores
                    </h3>
                    {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                    {ra.dimensions.map((dim: any) => (
                      <div
                        key={dim.dimension}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '8px',
                          marginBottom: '4px',
                        }}
                      >
                        <span
                          style={{
                            width: '140px',
                            fontSize: '10px',
                            fontWeight: 500,
                          }}
                        >
                          {dim.display_name || dim.dimension}
                        </span>
                        <div
                          style={{
                            flex: 1,
                            height: '8px',
                            background: '#f1f5f9',
                            borderRadius: '4px',
                            overflow: 'hidden',
                          }}
                        >
                          <div
                            style={{
                              height: '100%',
                              width: `${(dim.score / 20) * 100}%`,
                              background:
                                dim.score >= 17
                                  ? '#22c55e'
                                  : dim.score >= 13
                                    ? '#3b82f6'
                                    : dim.score >= 8
                                      ? 'var(--brand-gold)'
                                      : '#ef4444',
                              borderRadius: '4px',
                            }}
                          />
                        </div>
                        <span
                          style={{
                            width: '40px',
                            textAlign: 'right',
                            fontSize: '10px',
                            fontWeight: 600,
                          }}
                        >
                          {dim.score}/{dim.max_score || 20}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {ra.gap_analysis && ra.gap_analysis.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                      Gap Analysis
                    </h3>
                    {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                    {ra.gap_analysis.map((gap: any, i: number) => (
                      <div
                        key={i}
                        style={{
                          padding: '6px 8px',
                          marginBottom: '4px',
                          background:
                            gap.severity === 'critical' ? '#fef2f2' : '#fffbeb',
                          borderRadius: '4px',
                          border: `1px solid ${gap.severity === 'critical' ? '#fecaca' : '#fde68a'}`,
                        }}
                      >
                        <strong style={{ fontSize: '11px' }}>
                          {gap.dimension_name || gap.dimension}
                        </strong>{' '}
                        <span
                          style={{
                            fontSize: '9px',
                            padding: '1px 4px',
                            borderRadius: '3px',
                            background:
                              gap.severity === 'critical' ? '#fecaca' : '#fde68a',
                          }}
                        >
                          {gap.severity}
                        </span>
                        <p style={{ fontSize: '10px', margin: '3px 0 0 0', color: '#4b5563' }}>
                          {gap.narrative}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {ra.priority_actions && ra.priority_actions.length > 0 && (
                  <div>
                    <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                      Priority Actions
                    </h3>
                    <ol style={{ paddingLeft: '16px', margin: 0, fontSize: '10px' }}>
                      {ra.priority_actions
                        .slice(0, 10)
                        .map((action: string, i: number) => (
                          <li key={i} style={{ marginBottom: '3px' }}>
                            {action}
                          </li>
                        ))}
                    </ol>
                  </div>
                )}
              </div>
            )}

            {/* Section 4: Credit Spreads */}
            {cs && (
              <div style={{ marginBottom: '24px' }} className="pdf-section">
                <h2
                  style={{
                    fontSize: '16px',
                    fontWeight: 700,
                    color: '#0f172a',
                    borderBottom: '1px solid #e2e8f0',
                    paddingBottom: '6px',
                    marginBottom: '12px',
                  }}
                >
                  4. Borrowing Costs
                </h2>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr 1fr',
                    gap: '8px',
                    marginBottom: '12px',
                  }}
                >
                  <PdfStat
                    label="AAA Curve Source"
                    value={cs.aaa_curve_source || 'N/A'}
                  />
                  <PdfStat
                    label="Curve Date"
                    value={cs.aaa_curve_date || 'N/A'}
                  />
                  <PdfStat
                    label="Comparable Trades"
                    value={String(cs.recent_comps?.length ?? 0)}
                  />
                </div>

                {cs.cost_grid && cs.cost_grid.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                      Cost Grid (Selected Maturities)
                    </h3>
                    <table
                      style={{
                        width: '100%',
                        borderCollapse: 'collapse',
                        fontSize: '10px',
                      }}
                    >
                      <thead>
                        <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>Rating</th>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>Maturity</th>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>Spread (bps)</th>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>Yield</th>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>TIC Est.</th>
                        </tr>
                      </thead>
                      <tbody>
                        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                        {cs.cost_grid.slice(0, 10).map((row: any, i: number) => (
                          <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '3px 6px' }}>{row.rating}</td>
                            <td style={{ padding: '3px 6px' }}>{row.maturity}yr</td>
                            <td style={{ padding: '3px 6px' }}>
                              {row.spread_bps != null ? `${row.spread_bps.toFixed(1)}` : 'N/A'}
                            </td>
                            <td style={{ padding: '3px 6px' }}>
                              {row.yield_pct != null ? `${row.yield_pct.toFixed(2)}%` : 'N/A'}
                            </td>
                            <td style={{ padding: '3px 6px' }}>
                              {row.tic_estimate_pct != null ? `${row.tic_estimate_pct.toFixed(2)}%` : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {cs.issuer_comparisons && cs.issuer_comparisons.length > 0 && (
                  <div style={{ marginBottom: '12px' }}>
                    <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                      Issuer Comparisons ({cs.issuer_comparisons.length})
                    </h3>
                    <table
                      style={{
                        width: '100%',
                        borderCollapse: 'collapse',
                        fontSize: '10px',
                      }}
                    >
                      <thead>
                        <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>Issuer</th>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>Rating</th>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>Par</th>
                          <th style={{ textAlign: 'left', padding: '4px 6px' }}>Spread</th>
                        </tr>
                      </thead>
                      <tbody>
                        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                        {cs.issuer_comparisons.slice(0, 8).map((comp: any, i: number) => (
                          <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                            <td style={{ padding: '3px 6px' }}>{comp.issuer_name || comp.cusip_9}</td>
                            <td style={{ padding: '3px 6px' }}>{comp.rating || 'N/A'}</td>
                            <td style={{ padding: '3px 6px' }}>{fmt$(comp.par_amount)}</td>
                            <td style={{ padding: '3px 6px' }}>
                              {comp.spread_bps != null ? `${comp.spread_bps.toFixed(1)} bps` : 'N/A'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* Footer */}
            <div
              style={{
                borderTop: '1px solid #e2e8f0',
                paddingTop: '12px',
                marginTop: '20px',
                fontSize: '9px',
                color: '#94a3b8',
                textAlign: 'center',
              }}
            >
              This report was generated by Muni-Pal's free tools using data
              from public municipal securities disclosures and our own deal
              analysis. It is an educational snapshot, not investment or
              municipal advisory advice. Questions? info@muni-pal.io.
            </div>
          </div>
        </>
      )}
    </div>
  )
}

/** Small stat box for PDF rendering (inline styles for html2pdf). */
function PdfStat({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        background: '#f8fafc',
        borderRadius: '4px',
        padding: '6px 8px',
      }}
    >
      <div
        style={{
          fontSize: '9px',
          color: '#64748b',
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: '13px', fontWeight: 600, color: '#0f172a' }}>
        {value}
      </div>
    </div>
  )
}
