import { Link } from 'react-router-dom'
import {
  BarChart3,
  DollarSign,
  AlertTriangle,
  ArrowRight,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  Shield,
  Users,
} from 'lucide-react'

/* ------------------------------------------------------------------ */
/*  Brand constants                                                    */
/* ------------------------------------------------------------------ */
const BRAND = {
  navy: 'var(--brand-primary)',
  teal: 'var(--brand-accent)',
  orange: 'var(--brand-cta)',
  orangeHover: 'var(--brand-cta-hover)',
  gold: 'var(--brand-gold)',
}

/* ------------------------------------------------------------------ */
/*  Browser Mockup Frame                                               */
/* ------------------------------------------------------------------ */
function BrowserFrame({ src, alt, className = '' }: { src: string; alt: string; className?: string }) {
  return (
    <div className={`rounded-lg overflow-hidden shadow-2xl ${className}`} style={{ backgroundColor: '#1e293b' }}>
      <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-800 border-b border-gray-700">
        <div className="flex gap-1.5">
          <div className="h-2.5 w-2.5 rounded-full bg-red-400" />
          <div className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
          <div className="h-2.5 w-2.5 rounded-full bg-green-400" />
        </div>
        <div className="flex-1 mx-3">
          <div className="bg-gray-700 rounded-md px-3 py-1 text-xs text-gray-400 font-mono truncate">
            app.muni-pal.io/tools/readiness
          </div>
        </div>
      </div>
      <img src={src} alt={alt} className="w-full block" />
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Top Navigation Bar                                                 */
/* ------------------------------------------------------------------ */
function TopNav() {
  return (
    <nav
      className="sticky top-6 z-40 flex items-center gap-8 px-6 py-3 border-b border-white/10"
      style={{ backgroundColor: BRAND.navy }}
    >
      <Link to="/healthcare" className="flex items-center gap-3 flex-shrink-0">
        <img src="/muni-pal-logo-transparent.png" alt="Muni-Pal" className="h-24 w-24 object-contain" />
        <span className="text-white font-bold text-lg tracking-tight">Muni-Pal</span>
      </Link>
      <div className="hidden md:flex items-center gap-1 ml-auto">
        <Link
          to="/healthcare"
          className="px-4 py-2 text-sm font-medium text-white bg-white/10 rounded-md"
        >
          Healthcare
        </Link>
        <Link
          to="/tools"
          className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white hover:bg-white/5 rounded-md transition-colors"
        >
          Tools
        </Link>
        <Link
          to="/tools/market-intelligence"
          className="px-4 py-2 text-sm font-medium text-gray-300 hover:text-white hover:bg-white/5 rounded-md transition-colors"
        >
          Market Intelligence
        </Link>
      </div>
    </nav>
  )
}

/* ------------------------------------------------------------------ */
/*  Data constants                                                     */
/* ------------------------------------------------------------------ */
const VALUE_PROPS = [
  {
    icon: BarChart3,
    color: BRAND.teal,
    headline: 'Know what "good" looks like',
    copy: 'See the exact DSCR (gross revenue pledge, healthcare-adjusted), payer mix, days cash on hand, and pledge structures that separate AA-rated healthcare systems from BBB — drawn from real public-disclosure data, not industry averages.',
  },
  {
    icon: DollarSign,
    color: BRAND.orange,
    headline: 'Understand cost context — right now',
    copy: "Corpus-calibrated cost-of-capital context by rating tier. Not a vague \"market rate\" answer. Actual spread data so you can prepare better questions for your registered advisor and deal team.",
  },
  {
    icon: AlertTriangle,
    color: BRAND.gold,
    headline: 'Know where deals fall apart',
    copy: 'The 5 risk categories healthcare issuers consistently under-mitigate — and the specific actions upgraded credits took to close the gap.',
  },
]

const ENGAGEMENT_PATH = [
  { step: 1, name: 'Market Intelligence Report', price: 'Free', description: 'Sector benchmarks — DSCR, pricing, risk profile, Pareto framework' },
  { step: 2, name: 'Readiness Scan', price: 'Free', description: 'Automated pre-screen — sector fit, deal size, top 3 gaps' },
  { step: 3, name: 'Bond Readiness Diagnostic', price: '$15K\u2013$25K', description: 'Full score + gap analysis + critical path to close' },
  { step: 4, name: 'Standard Engagement', price: '$40K\u2013$50K', description: 'Diagnostic + readiness workplan + registered-advisor review support' },
  { step: 5, name: 'Bond Readiness Accelerator', price: '$75K+', description: 'Full pre-issuance support \u2014 gap remediation, benchmarking, and timeline optimization' },
]

const TIMELINE_PHASES = [
  { months: 'Month 1\u20132', label: 'Discovery', step: 'Market Intelligence Report + Readiness Scan', detail: 'Benchmark your system against peers. Identify top gaps before engaging advisors.', width: '25%' },
  { months: 'Month 2\u20133', label: 'Diagnostic', step: 'Bond Readiness Diagnostic', detail: 'Full scoring, gap analysis, and critical path. Know exactly what underwriters will scrutinize.', width: '12%' },
  { months: 'Month 3\u20135', label: 'Coordination', step: 'Standard Engagement', detail: 'Readiness workplan, cost-context benchmarking, and milestone tracking for advisor/deal-team review.', width: '22%' },
  { months: 'Month 4\u20137', label: 'Acceleration', step: 'Bond Readiness Accelerator', detail: 'Full pre-issuance support \u2014 gap remediation, benchmarking, and deal timeline optimization.', width: '22%' },
  { months: 'Month 6\u20139', label: 'Execution', step: 'Market entry', detail: 'Go to market with a complete, defensible credit story. Advisors execute \u2014 you negotiate from strength.', width: '22%' },
]

/* ================================================================== */
/*  Main Component                                                     */
/* ================================================================== */
export default function HealthcareCFOLanding() {
  return (
    <div className="min-h-screen bg-gray-50">
      <TopNav />

      {/* ============================================================ */}
      {/*  HERO                                                         */}
      {/* ============================================================ */}
      <section
        className="relative overflow-hidden"
        style={{ background: `linear-gradient(135deg, ${BRAND.navy} 0%, #142d4a 50%, #1e3a5f 100%)` }}
      >
        {/* Subtle grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{ backgroundImage: 'radial-gradient(#ffffff 0.5px, transparent 0.5px)', backgroundSize: '16px 16px' }}
        />
        <div className="relative max-w-7xl mx-auto px-6 py-16 md:py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <p
                className="text-sm font-semibold tracking-wide uppercase mb-4"
                style={{ color: BRAND.teal }}
              >
                Healthcare Bond Intelligence
              </p>
              <h1 className="text-3xl md:text-4xl lg:text-5xl font-extrabold text-white leading-tight mb-6">
                You're planning a bond issuance. Bring better evidence into the advisor-led process.
              </h1>
              <p className="text-lg text-gray-300 mb-8 max-w-xl leading-relaxed">
                Muni-Pal's Healthcare Market Intelligence Report benchmarks your deal
                against <span className="text-white font-semibold">866 actual municipal bond transactions</span> — so
                you walk into the room knowing what top-performing credits look like, what
                borrowing actually costs, and where risk disclosures go wrong.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/tools/market-intelligence"
                  className="inline-flex items-center justify-center gap-2 font-bold px-7 py-3.5 rounded-lg transition-colors text-white"
                  style={{ backgroundColor: BRAND.orange }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = BRAND.orangeHover)}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = BRAND.orange)}
                >
                  Get Your Free Market Intelligence Report
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link
                  to="/tools"
                  className="inline-flex items-center justify-center gap-2 border border-white/30 hover:border-white/60 text-white font-medium px-7 py-3.5 rounded-lg transition-colors"
                >
                  See the Bond Readiness Path
                  <ChevronRight className="h-4 w-4" />
                </Link>
              </div>
            </div>
            <div className="hidden lg:block">
              <BrowserFrame src="/screenshots/readiness-checklist.png" alt="Muni-Pal Readiness Checklist" />
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  STATS DASHBOARD — KPI Grid                                   */}
      {/* ============================================================ */}
      <section className="py-12 md:py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { value: '866', label: 'municipal bond transactions analyzed' },
              { value: '3.20x', label: 'Median healthcare DSCR', sub: '(gross revenue pledge basis)' },
              { value: '5', label: 'Risk categories scored' },
              { value: '1,318', label: 'Financial reports in corpus' },
            ].map((stat) => (
              <div
                key={stat.label}
                className="bg-white shadow-sm rounded-lg p-5 border-l-4 hover:shadow-md transition-shadow"
                style={{ borderLeftColor: BRAND.teal }}
              >
                <div className="text-3xl font-extrabold" style={{ color: BRAND.navy }}>
                  {stat.value}
                </div>
                <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
                {stat.sub && <div className="text-[10px] text-gray-400">{stat.sub}</div>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  VALUE PROPS — Cards with left color bar                      */}
      {/* ============================================================ */}
      <section className="py-12 md:py-16 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-2xl font-extrabold mb-8" style={{ color: BRAND.navy }}>
            What You Get
          </h2>
          <div className="grid gap-6 md:grid-cols-3">
            {VALUE_PROPS.map((prop) => (
              <div
                key={prop.headline}
                className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 hover:shadow-lg hover:-translate-y-0.5 transition-all duration-200 border-l-4"
                style={{ borderLeftColor: prop.color }}
              >
                <div
                  className="h-11 w-11 rounded-lg flex items-center justify-center mb-4"
                  style={{ backgroundColor: BRAND.navy }}
                >
                  <prop.icon className="h-5 w-5" style={{ color: prop.color }} />
                </div>
                <h3 className="text-base font-bold mb-2" style={{ color: BRAND.navy }}>
                  {prop.headline}
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed">{prop.copy}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  ENGAGEMENT PATH — Vertical Timeline                          */}
      {/* ============================================================ */}
      <section className="py-12 md:py-16">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-2xl font-extrabold mb-2" style={{ color: BRAND.navy }}>
            The Bond Readiness Path
          </h2>
          <p className="text-sm text-gray-600 mb-8 max-w-2xl">
            From free benchmarks to deal-ready in five steps. Start with the data — escalate
            only when you're confident in the opportunity.
          </p>
          <div className="relative">
            {/* Dotted connecting line */}
            <div
              className="absolute left-5 top-0 bottom-0 w-px hidden md:block"
              style={{ borderLeft: `2px dotted color-mix(in srgb, ${BRAND.teal} 25%, transparent)` }}
            />
            <div className="space-y-6">
              {ENGAGEMENT_PATH.map((step) => (
                <div key={step.name} className="flex items-start gap-6 md:pl-2 relative">
                  <div
                    className="hidden md:flex items-center justify-center h-8 w-8 rounded-full text-white text-xs font-bold flex-shrink-0 z-10"
                    style={{ backgroundColor: BRAND.teal }}
                  >
                    {step.step}
                  </div>
                  <div className="flex-1 bg-white rounded-lg border border-gray-200 shadow-sm p-5 hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="md:hidden inline-flex items-center justify-center h-6 w-6 rounded-full text-white text-xs font-bold" style={{ backgroundColor: BRAND.teal }}>
                        {step.step}
                      </span>
                      <h3 className="text-sm font-bold" style={{ color: BRAND.navy }}>
                        {step.name}
                      </h3>
                      <span
                        className={`text-xs font-semibold px-2.5 py-0.5 rounded-full ${
                          step.price === 'Free'
                            ? 'bg-green-100 text-green-700'
                            : 'text-white'
                        }`}
                        style={step.price !== 'Free' ? { backgroundColor: BRAND.orange } : undefined}
                      >
                        {step.price}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 leading-relaxed">{step.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  COST OF INACTION                                              */}
      {/* ============================================================ */}
      <section className="py-12 md:py-16 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div
            className="rounded-xl p-8 md:p-10 text-white"
            style={{ backgroundColor: BRAND.navy }}
          >
            <div className="flex items-start gap-4">
              <div className="h-12 w-12 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-red-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white mb-3">The Cost of Inaction</h3>
                <p className="text-base text-gray-300 leading-relaxed mb-3">
                  The difference between an A-rated and BBB-rated issuance costs{' '}
                  <span className="text-4xl font-extrabold" style={{ color: BRAND.orange }}>$27M+</span>{' '}
                  over 25 years on a $75M deal. The Accelerator helps you document your way
                  for registered-advisor review — for less than{' '}
                  <span className="font-bold" style={{ color: BRAND.teal }}>0.04%</span>{' '}
                  of deal size.
                </p>
                <p className="text-xs text-gray-400">
                  Based on observed AA vs. BBB spread differentials in public healthcare revenue
                  bond disclosures (gross revenue pledge basis).
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  TIMELINE — Horizontal Gantt-style                            */}
      {/* ============================================================ */}
      <section className="py-12 md:py-16">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-2xl font-extrabold mb-2 flex items-center gap-3" style={{ color: BRAND.navy }}>
            <Clock className="h-6 w-6" style={{ color: BRAND.teal }} />
            When to Engage
          </h2>
          <p className="text-sm text-gray-600 mb-8 max-w-2xl">
            A typical healthcare bond transaction takes 5-8 months. Here's how the Bond
            Readiness Path maps to your deal timeline.
          </p>
          {/* Month labels */}
          <div className="hidden md:flex items-center mb-2 text-xs text-gray-400 font-mono">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((m) => (
              <div key={m} className="flex-1 text-center">M{m}</div>
            ))}
          </div>
          <div className="space-y-3">
            {TIMELINE_PHASES.map((phase, i) => {
              const colors = [BRAND.teal, BRAND.navy, BRAND.orange, '#6366f1']
              return (
                <div key={phase.months} className="relative group">
                  <div className="flex items-center gap-4">
                    <div className="w-28 text-right flex-shrink-0 hidden md:block">
                      <span className="text-xs font-semibold" style={{ color: BRAND.teal }}>
                        {phase.months}
                      </span>
                    </div>
                    <div className="flex-1 relative">
                      <div
                        className="rounded-lg py-3 px-4 text-white text-sm font-semibold transition-all hover:shadow-lg cursor-default"
                        style={{
                          width: phase.width,
                          backgroundColor: colors[i],
                          marginLeft: i === 0 ? '0%' : i === 1 ? '15%' : i === 2 ? '25%' : '55%',
                        }}
                      >
                        {phase.label}
                      </div>
                    </div>
                  </div>
                  {/* Tooltip on hover */}
                  <div className="hidden group-hover:block absolute z-20 left-32 mt-1 bg-white border border-gray-200 shadow-lg rounded-lg p-3 max-w-sm">
                    <p className="text-xs font-semibold text-gray-900">{phase.step}</p>
                    <p className="text-xs text-gray-500 mt-1">{phase.detail}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  WORKS WITH YOUR ADVISORS                                     */}
      {/* ============================================================ */}
      <section className="py-12 md:py-16 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="rounded-xl border border-gray-200 shadow-sm p-6 md:p-8 bg-gray-50/50">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2" style={{ color: BRAND.navy }}>
              <Users className="h-5 w-5" style={{ color: BRAND.teal }} />
              Works With Your Advisors, Not Against Them
            </h2>
            <p className="text-sm text-gray-700 leading-relaxed mb-3 max-w-3xl">
              Muni-Pal is independent due diligence — not a replacement for your
              financial advisor. We give you the benchmarks, risk analysis, and
              market context so you walk into advisor meetings asking better
              questions and validating recommendations with data.
            </p>
            <p className="text-sm text-gray-700 leading-relaxed max-w-3xl">
              Your advisor brings deal execution. Muni-Pal brings evidence.
              Together, you get a stronger credit story and better terms.
            </p>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  AUDIENCE FILTER — Dashboard Comparison                       */}
      {/* ============================================================ */}
      <section className="py-12 md:py-16 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <h3 className="text-lg font-bold mb-6 flex items-center gap-2" style={{ color: BRAND.navy }}>
            <Shield className="h-5 w-5 text-gray-400" />
            Who this is for — and who it isn't
          </h3>
          <div className="grid md:grid-cols-2 gap-0 rounded-xl overflow-hidden border border-gray-200 shadow-sm">
            {/* Built for */}
            <div className="bg-white p-6 border-r border-gray-200">
              <p className="text-xs font-bold uppercase tracking-wide mb-4" style={{ color: BRAND.teal }}>
                Built for
              </p>
              <ul className="space-y-3">
                {[
                  'Healthcare CFOs and finance directors planning a bond issuance',
                  'Hospital systems evaluating capital structure options',
                  'Deals above $10M in total issuance size',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-gray-700">
                    <CheckCircle2 className="h-5 w-5 flex-shrink-0 mt-0.5" style={{ color: BRAND.teal }} />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            {/* Not for */}
            <div className="bg-gray-50 p-6">
              <p className="text-xs font-bold uppercase tracking-wide text-gray-400 mb-4">
                Not designed for
              </p>
              <ul className="space-y-3">
                {[
                  'Sub-$10M deal sizes',
                  'Non-healthcare municipal issuers',
                  'General financial advice seekers',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm text-gray-400">
                    <XCircle className="h-5 w-5 flex-shrink-0 mt-0.5 text-gray-300" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  PLATFORM PREVIEW — Full-width browser mockup                  */}
      {/* ============================================================ */}
      <section className="py-12 md:py-16">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-2xl font-extrabold mb-6 text-center" style={{ color: BRAND.navy }}>
            See the Platform in Action
          </h2>
          <BrowserFrame src="/screenshots/monte-carlo.png" alt="Muni-Pal Monte Carlo Analysis" />
        </div>
      </section>

      {/* ============================================================ */}
      {/*  BOTTOM CTA                                                    */}
      {/* ============================================================ */}
      <section
        className="py-16"
        style={{ backgroundColor: BRAND.navy }}
      >
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-extrabold text-white mb-3">
            Get Your Free Market Intelligence Report
          </h2>
          <p className="text-sm text-gray-300 mb-8 max-w-lg mx-auto">
            No login required. No sales call. Just the data your advisors charge $25K to compile.
          </p>
          <Link
            to="/tools/market-intelligence"
            className="inline-flex items-center gap-2 font-bold px-8 py-3.5 rounded-lg transition-colors text-white"
            style={{ backgroundColor: BRAND.orange }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = BRAND.orangeHover)}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = BRAND.orange)}
          >
            Start Now — It's Free
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  FOOTER                                                        */}
      {/* ============================================================ */}
      <footer className="bg-white border-t border-gray-200 py-6">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-center gap-3 text-sm text-gray-400">
            <img
              src="/muni-pal-logo-transparent.png"
              alt="Muni-Pal"
              className="h-8 w-8 object-contain opacity-60"
            />
            <p>Muni-Pal &mdash; A Launch Shop product. Built by Innovation Factory.</p>
          </div>
          <p className="text-[11px] text-gray-400 mt-4 max-w-3xl mx-auto text-center">
            Bond Readiness Accelerator is an educational and analytical service. It does not
            constitute municipal advisory services as defined under Section 15B of the Securities
            Exchange Act. Muni-Pal provides educational and analytical services and is not a
            registered municipal advisor.
          </p>
        </div>
      </footer>
    </div>
  )
}
