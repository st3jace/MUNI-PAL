import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  ArrowLeft,
  ChevronDown,
  ChevronRight,
  Loader2,
  Download,
  BarChart3,
  Shield,
  DollarSign,
  AlertTriangle,
  TrendingUp,
  Activity,
  FileText,
  Briefcase,
  Scale,
  ArrowRight,
  BookOpen,
} from 'lucide-react'
import { sensingApi } from '../../services/sensingApi'
import { useSensing } from '../../contexts/SensingContext'
import {
  InformationGap,
  ParetoAnalysis,
  RiskProfileNarrative,
  BondStructureNorms,
  RegulatoryFramework,
  PricingGrid,
  EngagementPath,
} from './HealthcareMIRContent'

/* ------------------------------------------------------------------ */
/*  Brand constants                                                    */
/* ------------------------------------------------------------------ */
const BRAND = {
  navy: '#1B3A5C',
  teal: '#2DAEAC',
  orange: '#E8913A',
}

/* ------------------------------------------------------------------ */
/*  Section metadata for navigation & numbering                        */
/* ------------------------------------------------------------------ */
const SECTION_META: Record<
  string,
  { icon: typeof BarChart3; label: string }
> = {
  'executive-summary': { icon: BookOpen, label: 'Executive Summary' },
  'information-gap': { icon: AlertTriangle, label: 'Information Gap' },
  'deal-structure': { icon: Briefcase, label: 'Deal Structure Profile' },
  'rating-distribution': { icon: Shield, label: 'Rating Distribution' },
  'financial-benchmarks': { icon: DollarSign, label: 'Financial Benchmarks' },
  'pareto-analysis': { icon: BarChart3, label: 'Pareto Analysis' },
  'risk-factor': { icon: AlertTriangle, label: 'Risk Factor Analysis' },
  'risk-narrative': { icon: FileText, label: 'Risk Profile & Cybersecurity' },
  'security-covenant': { icon: Scale, label: 'Security & Covenant Profile' },
  'credit-spread': { icon: TrendingUp, label: 'Credit Spread & Pricing' },
  'bond-structure-norms': { icon: Briefcase, label: 'Bond Structure Norms' },
  'pricing-grid': { icon: DollarSign, label: 'Full Pricing Grid' },
  'regulatory-framework': { icon: Scale, label: 'Regulatory Framework' },
  'market-activity': { icon: Activity, label: 'Secondary Market Activity' },
  'rating-agency': { icon: Shield, label: 'Rating Agency Perspective' },
  'engagement-path': { icon: ArrowRight, label: 'Engagement Path' },
}

/* ------------------------------------------------------------------ */
/*  StatBox variants                                                   */
/* ------------------------------------------------------------------ */
type StatVariant = 'financial' | 'count' | 'rating' | 'default'

function StatBox({
  label,
  value,
  variant = 'default',
}: {
  label: string
  value: string | number
  variant?: StatVariant
}) {
  const styles: Record<StatVariant, string> = {
    financial: `bg-[${BRAND.navy}] text-white`,
    count: 'bg-white border-l-4 border-muni-teal text-muni-navy',
    rating: 'bg-white border-l-4 border-amber-400 text-muni-navy',
    default: 'bg-white border border-gray-200 text-muni-navy',
  }
  // PDF-safe: use inline fallbacks for gradient backgrounds
  return (
    <div
      className={`rounded-lg px-4 py-3 ${styles[variant]}`}
      style={variant === 'financial' ? { backgroundColor: BRAND.navy, color: '#fff' } : undefined}
    >
      <div
        className={`text-xs uppercase tracking-wider mb-1 ${
          variant === 'financial' ? 'text-gray-300' : 'text-gray-500'
        }`}
      >
        {label}
      </div>
      <div
        className={`text-lg font-semibold ${
          variant === 'financial' ? 'text-white' : ''
        }`}
      >
        {String(value)}
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  SectionCard — defaults open, numbered, teal top border, icon       */
/* ------------------------------------------------------------------ */
function SectionCard({
  id,
  sectionNumber,
  totalSections,
  title,
  icon: Icon,
  children,
  defaultOpen = true,
}: {
  id: string
  sectionNumber: number
  totalSections: number
  title: string
  icon?: typeof BarChart3
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <div
      id={id}
      className="bg-white rounded-lg border border-gray-200 shadow-sm scroll-mt-20 overflow-hidden"
      style={{ borderTop: `3px solid ${BRAND.teal}` }}
    >
      <button
        className="flex items-center justify-between w-full text-left px-5 py-4"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-3">
          {Icon && (
            <div
              className="h-8 w-8 rounded-lg flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: `${BRAND.navy}10` }}
            >
              <Icon className="h-4 w-4" style={{ color: BRAND.teal }} />
            </div>
          )}
          <div>
            <span className="text-[10px] uppercase tracking-widest text-gray-400 font-medium">
              Section {sectionNumber} of {totalSections}
            </span>
            <h3 className="font-semibold text-gray-900 text-base">{title}</h3>
          </div>
        </div>
        {open ? (
          <ChevronDown className="h-5 w-5 text-gray-400 flex-shrink-0" />
        ) : (
          <ChevronRight className="h-5 w-5 text-gray-400 flex-shrink-0" />
        )}
      </button>
      {open && <div className="px-5 pb-5 pt-1">{children}</div>}
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  DataTable — branded row striping                                   */
/* ------------------------------------------------------------------ */
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
          <tr className="border-b-2" style={{ borderColor: BRAND.teal }}>
            {headers.map((h) => (
              <th
                key={h}
                className="text-left py-2.5 px-3 font-medium"
                style={{ color: BRAND.navy }}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className="border-b border-gray-100"
              style={i % 2 === 1 ? { backgroundColor: `${BRAND.navy}08` } : undefined}
            >
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

/* ------------------------------------------------------------------ */
/*  Formatters                                                         */
/* ------------------------------------------------------------------ */
function fmt$(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(1)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(1)}M`
  return `$${n.toLocaleString()}`
}

function pctDecimal(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  return `${(n * 100).toFixed(1)}%`
}

function pctDirect(n: number | null | undefined): string {
  if (n == null) return 'N/A'
  return `${n.toFixed(1)}%`
}

/* ------------------------------------------------------------------ */
/*  MuniPal Logo Mark (inline SVG)                                     */
/* ------------------------------------------------------------------ */
function MuniPalLogo({ size = 40 }: { size?: number }) {
  return (
    <img
      src="/muni-pal-emblem.png"
      alt="Muni-Pal"
      width={size}
      height={size}
      className="flex-shrink-0 rounded-xl"
      style={{
        filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.3))',
      }}
    />
  )
}

/* ------------------------------------------------------------------ */
/*  Section Navigation Bar                                             */
/* ------------------------------------------------------------------ */
function SectionNav({ sectionIds }: { sectionIds: string[] }) {
  const [activeSection, setActiveSection] = useState('')
  const navRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id)
          }
        }
      },
      { rootMargin: '-80px 0px -70% 0px', threshold: 0 }
    )
    for (const id of sectionIds) {
      const el = document.getElementById(id)
      if (el) observer.observe(el)
    }
    return () => observer.disconnect()
  }, [sectionIds])

  return (
    <div
      ref={navRef}
      className="sticky top-0 z-30 bg-white/95 backdrop-blur border-b border-gray-200 -mx-4 px-4 py-2 mb-6 overflow-x-auto"
    >
      <div className="flex gap-1 min-w-max">
        {sectionIds.map((id) => {
          const meta = SECTION_META[id]
          if (!meta) return null
          const isActive = activeSection === id
          return (
            <a
              key={id}
              href={`#${id}`}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                isActive
                  ? 'text-white'
                  : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100'
              }`}
              style={isActive ? { backgroundColor: BRAND.navy } : undefined}
              onClick={(e) => {
                e.preventDefault()
                document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
              }}
            >
              {meta.label}
            </a>
          )
        })}
      </div>
    </div>
  )
}

/* ================================================================== */
/*  Main Component                                                     */
/* ================================================================== */
export default function MarketIntelligence() {
  const sensing = useSensing()
  const [sector, setSector] = useState(sensing.sector || 'healthcare')

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

  useEffect(() => {
    if (report) {
      sensing.setMarketIntel(report)
      sensing.setSector(sector)
    }
  }, [report, sector]) // eslint-disable-line react-hooks/exhaustive-deps

  /* Build visible section list for navigation */
  const visibleSections: string[] = []
  if (report) {
    visibleSections.push('executive-summary')
    if (sector === 'healthcare') visibleSections.push('information-gap')
    if (report.deal_structure) visibleSections.push('deal-structure')
    if (report.rating_distribution) visibleSections.push('rating-distribution')
    if (report.financial_benchmarks) visibleSections.push('financial-benchmarks')
    if (sector === 'healthcare') visibleSections.push('pareto-analysis')
    if (report.risk_profile) visibleSections.push('risk-factor')
    if (sector === 'healthcare') visibleSections.push('risk-narrative')
    if (report.security_profile) visibleSections.push('security-covenant')
    if (report.spread_curve?.rating_to_spread_bps) visibleSections.push('credit-spread')
    if (sector === 'healthcare') visibleSections.push('bond-structure-norms')
    if (sector === 'healthcare') visibleSections.push('pricing-grid')
    if (sector === 'healthcare') visibleSections.push('regulatory-framework')
    if (report.market_activity) visibleSections.push('market-activity')
    if (report.rating_agency_perspective) visibleSections.push('rating-agency')
    if (sector === 'healthcare') visibleSections.push('engagement-path')
  }

  /* Section counter helper (skip executive-summary and healthcare narrative sections from count) */
  let sectionCounter = 0
  const totalDataSections = visibleSections.filter(
    (id) => id !== 'executive-summary'
  ).length
  function nextSection() {
    sectionCounter++
    return sectionCounter
  }

  const sectorLabel = sector
    .replace('_', ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())

  return (
    <div className="max-w-5xl mx-auto px-4">
      {/* ============================================================ */}
      {/*  BRANDED REPORT HEADER                                        */}
      {/* ============================================================ */}
      <div
        className="rounded-2xl p-8 md:p-10 text-white mb-8 print:bg-muni-navy"
        style={{
          background: `linear-gradient(135deg, ${BRAND.navy} 0%, #1B3A5C 40%, #312e81 100%)`,
        }}
      >
        <div className="flex items-start justify-between gap-4 mb-6">
          <Link
            to="/tools"
            className="mt-1 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div className="flex flex-col items-end gap-2">
            <label className="text-xs text-gray-400 font-medium">Sector</label>
            <select
              className="bg-white/10 border border-white/20 text-white text-sm rounded-lg px-3 py-1.5 focus:outline-none focus:border-white/40"
              value={sector}
              onChange={(e) => setSector(e.target.value)}
            >
              {(sectorsQuery.data || []).map((s) => (
                <option key={s.id} value={s.id} className="text-gray-900">
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-4 mb-4">
          <MuniPalLogo size={56} />
          <div>
            <h1 className="text-2xl md:text-3xl font-bold leading-tight">
              {sectorLabel} Municipal Bond Market Intelligence
            </h1>
            <p className="text-sm text-gray-300 mt-1">Q1 2026</p>
          </div>
        </div>

        <p className="text-sm text-gray-300 leading-relaxed max-w-3xl">
          Sector benchmark from the EMMA municipal bond corpus — deal structures,
          financial benchmarks, risk profiles, credit spreads, and rating agency
          perspectives.
        </p>
      </div>

      {/* Loading / Error */}
      {reportQuery.isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin" style={{ color: BRAND.teal }} />
          <span className="ml-3 text-gray-500">
            Generating report for {sectorLabel}...
          </span>
        </div>
      )}

      {reportQuery.error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
          Failed to load report: {String(reportQuery.error)}
        </div>
      )}

      {report && (
        <>
          {/* Section Navigation */}
          <SectionNav sectionIds={visibleSections} />

          <div className="space-y-5">
            {/* ====================================================== */}
            {/*  EXECUTIVE SUMMARY                                      */}
            {/* ====================================================== */}
            <div
              id="executive-summary"
              className="rounded-lg p-6 text-white scroll-mt-20 print:bg-muni-navy"
              style={{ backgroundColor: BRAND.navy }}
            >
              <div className="flex items-start justify-between mb-4">
                <h2 className="text-lg font-semibold">Executive Summary</h2>
                {es?.data_freshness && (
                  <span className="text-xs bg-white/10 rounded-full px-3 py-1 text-gray-300">
                    Data as of {es.data_freshness}
                  </span>
                )}
              </div>

              <p className="text-sm text-gray-200 mb-3 leading-relaxed">
                This is a data-driven market intelligence report for the{' '}
                <strong className="text-white">
                  {es?.sector_title || sectorLabel}
                </strong>{' '}
                municipal bond sector, built from analysis of real EMMA filings,
                rating agency actions, and secondary market trading data.
              </p>

              {es?.audience_intro && (
                <p className="text-sm text-gray-300 mb-4 leading-relaxed italic">
                  {es.audience_intro}
                </p>
              )}

              {es?.report_completeness && (
                <div className="flex gap-6 text-sm mb-4">
                  <span>
                    <span style={{ color: BRAND.teal }} className="font-semibold">
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

              {es?.report_guide && es.report_guide.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2" style={{ color: BRAND.teal }}>
                    What You'll Find in This Report
                  </h3>
                  <ul className="space-y-1.5 text-sm text-gray-300">
                    {es.report_guide.map((item: string, i: number) => (
                      <li key={i} className="flex gap-2">
                        <span style={{ color: BRAND.teal }} className="flex-shrink-0 mt-0.5">&#x2022;</span>
                        <span
                          dangerouslySetInnerHTML={{
                            __html: item.replace(
                              /\*\*(.*?)\*\*/g,
                              '<strong class="text-white">$1</strong>'
                            ),
                          }}
                        />
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {es?.why_it_matters && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2" style={{ color: BRAND.teal }}>
                    Why This Matters
                  </h3>
                  <p className="text-sm text-gray-300 leading-relaxed">
                    {es.why_it_matters}
                  </p>
                </div>
              )}

              {es?.takeaways && es.takeaways.length > 0 && (
                <div className="mb-4">
                  <h3 className="text-sm font-semibold mb-2" style={{ color: BRAND.teal }}>
                    What You Should Take Away
                  </h3>
                  <ul className="space-y-1.5 text-sm text-gray-300">
                    {es.takeaways.map((t: string, i: number) => (
                      <li key={i} className="flex gap-2">
                        <span style={{ color: BRAND.teal }} className="flex-shrink-0">&#x2713;</span>
                        <span>{t}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {es?.key_findings && es.key_findings.length > 0 && (
                <div className="pt-3 border-t border-white/10">
                  <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                    Data at a Glance
                  </h3>
                  <ul className="space-y-1.5 text-sm text-gray-300">
                    {es.key_findings.map((f: string, i: number) => (
                      <li key={i} className="flex gap-2">
                        <span style={{ color: BRAND.teal }} className="flex-shrink-0">-</span>
                        <span>{f}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Healthcare: Information Gap */}
            {sector === 'healthcare' && (
              <div id="information-gap" className="scroll-mt-20">
                <InformationGap />
              </div>
            )}

            {/* Deal Structure */}
            {report.deal_structure && (
              <SectionCard
                id="deal-structure"
                sectionNumber={nextSection()}
                totalSections={totalDataSections}
                title="Deal Structure Profile"
                icon={SECTION_META['deal-structure']?.icon}
              >
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <StatBox
                    label="Total Deals"
                    value={report.deal_structure.n_deals ?? 0}
                    variant="count"
                  />
                  <StatBox
                    label="Total Par"
                    value={fmt$(report.deal_structure.par_amount_total_usd)}
                    variant="financial"
                  />
                  <StatBox
                    label="Median Par"
                    value={fmt$(report.deal_structure.par_amount_median_usd)}
                    variant="financial"
                  />
                  <StatBox
                    label="States"
                    value={
                      Object.keys(
                        report.deal_structure.state_distribution || {}
                      ).length
                    }
                    variant="count"
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
                            className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium"
                            style={{ backgroundColor: `${BRAND.navy}10`, color: BRAND.navy }}
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
              <SectionCard
                id="rating-distribution"
                sectionNumber={nextSection()}
                totalSections={totalDataSections}
                title="Rating Distribution"
                icon={SECTION_META['rating-distribution']?.icon}
              >
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <StatBox
                    label="Total Rated"
                    value={report.rating_distribution.total_rated ?? 0}
                    variant="count"
                  />
                  <StatBox
                    label="Investment Grade"
                    value={pctDirect(report.rating_distribution.investment_grade_pct)}
                    variant="rating"
                  />
                  <StatBox
                    label="Modal Rating"
                    value={report.rating_distribution.modal_rating || 'N/A'}
                    variant="rating"
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
                                className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium"
                                style={{ backgroundColor: `${BRAND.navy}10`, color: BRAND.navy }}
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
            {report.financial_benchmarks && (() => {
              const fb = report.financial_benchmarks
              const dscrMedian = fb.dscr?.median ?? fb.dscr_median
              const dscrP25 = fb.dscr?.p25
              const dscrP75 = fb.dscr?.p75
              const dscrWarning = fb.dscr?.sample_warning
              return (
                <SectionCard
                  id="financial-benchmarks"
                  sectionNumber={nextSection()}
                  totalSections={totalDataSections}
                  title="Financial Benchmarks"
                  icon={SECTION_META['financial-benchmarks']?.icon}
                >
                  {dscrWarning && (
                    <div className="mb-3 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
                      <span className="font-semibold">Note:</span> {dscrWarning}
                    </div>
                  )}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {dscrMedian != null && (
                      <StatBox
                        label="DSCR Median"
                        value={`${dscrMedian.toFixed(2)}x`}
                        variant="financial"
                      />
                    )}
                    {fb.operating_margin_median != null && (
                      <StatBox
                        label="Op. Margin"
                        value={pctDecimal(fb.operating_margin_median)}
                        variant="financial"
                      />
                    )}
                    {fb.net_margin_median != null && (
                      <StatBox
                        label="Net Margin"
                        value={pctDecimal(fb.net_margin_median)}
                        variant="financial"
                      />
                    )}
                    {fb.days_cash_on_hand_median != null && (
                      <StatBox
                        label="Days Cash"
                        value={`${fb.days_cash_on_hand_median.toFixed(0)} days`}
                        variant="count"
                      />
                    )}
                    {fb.leverage_median != null && (
                      <StatBox
                        label="Leverage"
                        value={`${fb.leverage_median.toFixed(2)}x`}
                        variant="financial"
                      />
                    )}
                    <StatBox
                      label="Reports"
                      value={fb.n_reports ?? 0}
                      variant="count"
                    />
                  </div>
                  {dscrP25 != null && dscrP75 != null && (
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-gray-600 mb-2">
                        DSCR Quartile Range (Pareto)
                      </h4>
                      <div className="flex items-center gap-2">
                        <div
                          className="flex-1 rounded-lg p-3"
                          style={{ backgroundColor: `${BRAND.navy}08` }}
                        >
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-amber-600 font-medium">
                              Bottom 25%: &lt; {dscrP25.toFixed(2)}x
                            </span>
                            <span className="text-gray-400 px-4">|</span>
                            <span className="text-gray-600 font-medium">
                              Median: {dscrMedian?.toFixed(2)}x
                            </span>
                            <span className="text-gray-400 px-4">|</span>
                            <span className="text-green-600 font-medium">
                              Top 25%: &gt; {dscrP75.toFixed(2)}x
                            </span>
                          </div>
                          <div className="mt-2 h-2 bg-gray-200 rounded-full relative">
                            <div
                              className="absolute h-2 rounded-full"
                              style={{
                                left: '0%',
                                right: '0%',
                                background: `linear-gradient(to right, #f59e0b, ${BRAND.teal}, #22c55e)`,
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </SectionCard>
              )
            })()}

            {/* Healthcare: Pareto Analysis */}
            {sector === 'healthcare' && (
              <div id="pareto-analysis" className="scroll-mt-20">
                <ParetoAnalysis />
              </div>
            )}

            {/* Risk Profile */}
            {report.risk_profile && (
              <SectionCard
                id="risk-factor"
                sectionNumber={nextSection()}
                totalSections={totalDataSections}
                title="Risk Factor Analysis"
                icon={SECTION_META['risk-factor']?.icon}
              >
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <StatBox
                    label="Total Factors"
                    value={report.risk_profile.n_risk_factors ?? 0}
                    variant="count"
                  />
                  <StatBox
                    label="Categories"
                    value={
                      Object.keys(
                        report.risk_profile.category_distribution || {}
                      ).length
                    }
                    variant="count"
                  />
                  <StatBox
                    label="Mitigation Rate"
                    value={pctDecimal(report.risk_profile.overall_mitigation_rate)}
                    variant="rating"
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
                            cat.category
                              .replace(/_/g, ' ')
                              .replace(/\b\w/g, (c: string) => c.toUpperCase()),
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

            {/* Healthcare: Risk Profile Narrative & Cybersecurity */}
            {sector === 'healthcare' && (
              <div id="risk-narrative" className="scroll-mt-20">
                <RiskProfileNarrative />
              </div>
            )}

            {/* Security Profile */}
            {report.security_profile && (
              <SectionCard
                id="security-covenant"
                sectionNumber={nextSection()}
                totalSections={totalDataSections}
                title="Security & Covenant Profile"
                icon={SECTION_META['security-covenant']?.icon}
              >
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <StatBox
                    label="Packages"
                    value={report.security_profile.n_packages ?? 0}
                    variant="count"
                  />
                  {report.security_profile.coverage_ratio?.median != null && (
                    <StatBox
                      label="Coverage Median"
                      value={`${report.security_profile.coverage_ratio.median.toFixed(2)}x`}
                      variant="financial"
                    />
                  )}
                  {report.security_profile.additional_bonds_test_median != null && (
                    <StatBox
                      label="ABT Median"
                      value={`${report.security_profile.additional_bonds_test_median.toFixed(2)}x`}
                      variant="financial"
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
                            className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium"
                            style={{ backgroundColor: `${BRAND.navy}10`, color: BRAND.navy }}
                          >
                            {type}: {count}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                {report.security_profile.lien_position_distribution &&
                  Object.keys(report.security_profile.lien_position_distribution).length > 0 && (
                    <div className="mt-4">
                      <h4 className="text-sm font-medium text-gray-600 mb-2">
                        Lien Position
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(
                          report.security_profile.lien_position_distribution as Record<string, number>
                        ).map(([type, count]) => (
                          <span
                            key={type}
                            className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium"
                            style={{ backgroundColor: `${BRAND.teal}15`, color: BRAND.navy }}
                          >
                            {type.replace(/_/g, ' ')}: {count}
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
                            className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium"
                            style={{ backgroundColor: `${BRAND.navy}10`, color: BRAND.navy }}
                          >
                            {type}: {count}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
              </SectionCard>
            )}

            {/* Spread Curve & Pricing Grid */}
            {report.spread_curve && report.spread_curve.rating_to_spread_bps && (
              <SectionCard
                id="credit-spread"
                sectionNumber={nextSection()}
                totalSections={totalDataSections}
                title="Credit Spread & Pricing Reference"
                icon={SECTION_META['credit-spread']?.icon}
              >
                <DataTable
                  headers={['Rating', 'Spread (bps)', 'Over AAA MMD']}
                  rows={Object.entries(
                    report.spread_curve.rating_to_spread_bps as Record<
                      string,
                      number
                    >
                  )
                    .filter(([r]) =>
                      ['AA+', 'AA', 'AA-', 'A+', 'A', 'A-', 'BBB+', 'BBB', 'BBB-'].includes(r)
                    )
                    .map(([rating, bps]) => [rating, bps, `+${bps}`])}
                />
                {report.spread_curve.sector_typical_range && (
                  <p className="mt-3 text-sm text-gray-500">
                    Typical range: {report.spread_curve.sector_typical_range}
                  </p>
                )}
                {report.spread_curve.investment_grade_range_bps && (
                  <div
                    className="mt-4 rounded-lg p-3"
                    style={{ backgroundColor: `${BRAND.teal}10` }}
                  >
                    <h4 className="text-sm font-medium mb-1" style={{ color: BRAND.navy }}>
                      Estimated Cost-of-Capital Reference (25-Year Maturity)
                    </h4>
                    <p className="text-xs mb-2" style={{ color: `${BRAND.navy}99` }}>
                      Based on AAA MMD curve + sector spreads. For detailed pricing, see
                      Credit Spread Monitor.
                    </p>
                    <div className="grid grid-cols-3 gap-3">
                      {(['AA', 'A', 'BBB'] as const).map((rating) => {
                        const spread = (
                          report.spread_curve.rating_to_spread_bps as Record<string, number>
                        )[rating]
                        if (spread == null) return null
                        const estYield = (4.42 + spread / 100).toFixed(2)
                        return (
                          <div
                            key={rating}
                            className="bg-white rounded-lg px-3 py-2 text-center border"
                            style={{ borderColor: `${BRAND.teal}40` }}
                          >
                            <div className="text-xs text-gray-500 uppercase">
                              {rating}-Rated
                            </div>
                            <div
                              className="text-lg font-semibold"
                              style={{ color: BRAND.navy }}
                            >
                              {estYield}%
                            </div>
                            <div className="text-xs text-gray-400">+{spread} bps</div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </SectionCard>
            )}

            {/* Healthcare: Bond Structure Norms */}
            {sector === 'healthcare' && (
              <div id="bond-structure-norms" className="scroll-mt-20">
                <BondStructureNorms />
              </div>
            )}

            {/* Healthcare: Full Pricing Grid */}
            {sector === 'healthcare' && (
              <div id="pricing-grid" className="scroll-mt-20">
                <PricingGrid />
              </div>
            )}

            {/* Healthcare: Regulatory Framework */}
            {sector === 'healthcare' && (
              <div id="regulatory-framework" className="scroll-mt-20">
                <RegulatoryFramework />
              </div>
            )}

            {/* Market Activity */}
            {report.market_activity && (
              <SectionCard
                id="market-activity"
                sectionNumber={nextSection()}
                totalSections={totalDataSections}
                title="Secondary Market Activity"
                icon={SECTION_META['market-activity']?.icon}
              >
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <StatBox
                    label="Total Trades"
                    value={
                      report.market_activity.n_secondary_trades?.toLocaleString() ?? 0
                    }
                    variant="count"
                  />
                  <StatBox
                    label="CUSIPs Tracked"
                    value={report.market_activity.n_cusips_tracked ?? 0}
                    variant="count"
                  />
                  {report.market_activity.avg_trades_per_bond != null && (
                    <StatBox
                      label="Avg Trades/Bond"
                      value={report.market_activity.avg_trades_per_bond.toFixed(1)}
                      variant="default"
                    />
                  )}
                  {report.market_activity.trade_size_median_usd != null && (
                    <StatBox
                      label="Median Trade Size"
                      value={fmt$(report.market_activity.trade_size_median_usd)}
                      variant="financial"
                    />
                  )}
                </div>
                {report.market_activity.yield_range && (
                  <p className="mt-3 text-sm text-gray-500">
                    Yield range:{' '}
                    {report.market_activity.yield_range[0]?.toFixed(2)}% &ndash;{' '}
                    {report.market_activity.yield_range[1]?.toFixed(2)}% | Price range:{' '}
                    {report.market_activity.price_range?.[0]?.toFixed(2)} &ndash;{' '}
                    {report.market_activity.price_range?.[1]?.toFixed(2)}
                  </p>
                )}
              </SectionCard>
            )}

            {/* Rating Agency Perspective */}
            {report.rating_agency_perspective && (
              <SectionCard
                id="rating-agency"
                sectionNumber={nextSection()}
                totalSections={totalDataSections}
                title="Rating Agency Perspective"
                icon={SECTION_META['rating-agency']?.icon}
              >
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <StatBox
                    label="Rating Actions"
                    value={report.rating_agency_perspective.n_rating_actions ?? 0}
                    variant="count"
                  />
                  <StatBox
                    label="Rating Factors"
                    value={report.rating_agency_perspective.n_rating_factors ?? 0}
                    variant="count"
                  />
                  {report.rating_agency_perspective.action_distribution && (
                    <>
                      <StatBox
                        label="Upgrades"
                        value={
                          report.rating_agency_perspective.action_distribution
                            .upgrades ?? 0
                        }
                        variant="rating"
                      />
                      <StatBox
                        label="Downgrades"
                        value={
                          report.rating_agency_perspective.action_distribution
                            .downgrades ?? 0
                        }
                        variant="rating"
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
                            className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium"
                            style={{ backgroundColor: `${BRAND.navy}10`, color: BRAND.navy }}
                          >
                            {agency}: {count}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
              </SectionCard>
            )}

            {/* Healthcare: Engagement Path */}
            {sector === 'healthcare' && (
              <div id="engagement-path" className="scroll-mt-20">
                <EngagementPath />
              </div>
            )}

            {/* ====================================================== */}
            {/*  BOTTOM CTA                                             */}
            {/* ====================================================== */}
            <div
              className="rounded-xl p-8 text-white text-center print:bg-muni-navy"
              style={{
                background: `linear-gradient(135deg, ${BRAND.navy} 0%, #1B3A5C 50%, #312e81 100%)`,
              }}
            >
              <h2 className="text-xl font-bold mb-2">
                Ready to see where you stand?
              </h2>
              <p className="text-sm text-gray-300 mb-6 max-w-lg mx-auto">
                Take the free Readiness Scan — an automated pre-screen that shows
                your sector fit, deal size positioning, and top 3 gaps to close
                before approaching the market.
              </p>
              <Link
                to="/tools/readiness"
                className="inline-flex items-center gap-2 font-semibold px-8 py-3 rounded-lg transition-colors"
                style={{
                  backgroundColor: BRAND.orange,
                  color: '#fff',
                }}
              >
                Take the Free Readiness Scan
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            {/* Footer bar */}
            <div className="flex items-center justify-between pt-4 pb-8">
              <Link
                to="/tools/export"
                className="flex items-center gap-2 text-sm font-medium hover:opacity-80 transition-opacity"
                style={{ color: BRAND.navy }}
              >
                <Download className="h-4 w-4" />
                Export Combined Report
                {sensing.completedCount > 0 && (
                  <span
                    className="rounded-full px-2 py-0.5 text-xs"
                    style={{ backgroundColor: `${BRAND.teal}20`, color: BRAND.navy }}
                  >
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
        </>
      )}
    </div>
  )
}
