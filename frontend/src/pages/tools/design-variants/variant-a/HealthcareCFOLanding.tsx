import { Link } from 'react-router-dom'
import {
  BarChart3,
  Shield,
  DollarSign,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Clock,
  FileText,
  TrendingUp,
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
/*  Browser Mockup Frame (from C)                                      */
/* ------------------------------------------------------------------ */
function BrowserFrame({ src, alt, url = 'app.muni-pal.io/tools/readiness' }: { src: string; alt: string; url?: string }) {
  return (
    <div className="rounded-lg overflow-hidden shadow-2xl" style={{ backgroundColor: '#1e293b' }}>
      <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-800 border-b border-gray-700">
        <div className="flex gap-1.5">
          <div className="h-2.5 w-2.5 rounded-full bg-red-400" />
          <div className="h-2.5 w-2.5 rounded-full bg-yellow-400" />
          <div className="h-2.5 w-2.5 rounded-full bg-green-400" />
        </div>
        <div className="flex-1 mx-3">
          <div className="bg-gray-700 rounded-md px-3 py-1 text-xs text-gray-400 font-mono truncate">
            {url}
          </div>
        </div>
      </div>
      <img src={src} alt={alt} className="w-full block" />
    </div>
  )
}

/* ------------------------------------------------------------------ */
/*  Data                                                               */
/* ------------------------------------------------------------------ */
const VALUE_PROPS = [
  {
    icon: BarChart3,
    headline: 'Know what "good" looks like',
    copy: 'See the exact DSCR (gross revenue pledge, healthcare-adjusted), payer mix, days cash on hand, and pledge structures that separate AA-rated healthcare systems from BBB — drawn from real public-disclosure data, not industry averages.',
  },
  {
    icon: DollarSign,
    headline: 'Understand cost context — right now',
    copy: "Corpus-calibrated cost-of-capital context by rating tier. Not a vague \"market rate\" answer. Actual spread data so you can prepare better questions for your registered advisor and deal team.",
  },
  {
    icon: AlertTriangle,
    headline: 'Know where deals fall apart',
    copy: 'The 5 risk categories healthcare issuers consistently under-mitigate — and the specific actions upgraded credits took to close the gap.',
  },
]

const ENGAGEMENT_PATH = [
  { step: 1, name: 'Market Intelligence Report', price: 'Free', description: 'Sector benchmarks — DSCR, pricing, risk profile, Pareto framework' },
  { step: 2, name: 'Readiness Scan', price: 'Free', description: 'Automated pre-screen — sector fit, deal size, top 3 gaps' },
  { step: 3, name: 'Bond Readiness Diagnostic', price: '$15K–$25K', description: 'Full score + gap analysis + critical path to close' },
  { step: 4, name: 'Standard Engagement', price: '$40K–$50K', description: 'Diagnostic + readiness workplan + registered-advisor review support' },
  { step: 5, name: 'Bond Readiness Accelerator', price: '$75K+', description: 'Readiness support — gap remediation, benchmarking, and preparation workflow' },
]

const TIMELINE_PHASES = [
  { months: 'Month 1–2', label: 'Discovery', step: 'Market Intelligence Report + Readiness Scan', detail: 'Benchmark your system against peers. Identify top gaps before engaging advisors.', width: '25%' },
  { months: 'Month 2–3', label: 'Diagnostic', step: 'Bond Readiness Diagnostic', detail: 'Full scoring, gap analysis, and critical path. Know exactly what underwriters will scrutinize.', width: '12%' },
  { months: 'Month 3–5', label: 'Coordination', step: 'Standard Engagement', detail: 'Readiness workplan, cost-context benchmarking, and milestone tracking for advisor/deal-team review.', width: '22%' },
  { months: 'Month 4–7', label: 'Acceleration', step: 'Bond Readiness Accelerator', detail: 'Readiness support — gap remediation, benchmarking, and preparation workflow discipline.', width: '22%' },
  { months: 'Month 6–9', label: 'Advisor-led execution', step: 'Market entry', detail: 'Bring a better-organized evidence record to your registered advisor and deal team for their execution process.', width: '22%' },
]

/* ================================================================== */
/*  Main Component                                                     */
/* ================================================================== */
export default function HealthcareCFOLanding() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* ============================================================ */}
      {/*  HERO — A's gradient + C's side-by-side text/image layout    */}
      {/* ============================================================ */}
      <section className="relative bg-gradient-to-br from-muni-navy via-muni-navy to-indigo-900 overflow-hidden">
        {/* Subtle radial glow (from A) */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background:
              'radial-gradient(ellipse 60% 50% at 30% 40%, rgba(45,174,172,0.4) 0%, transparent 70%)',
          }}
        />
        {/* Subtle grid dots (from C) */}
        <div
          className="absolute inset-0 opacity-[0.05]"
          style={{ backgroundImage: 'radial-gradient(#ffffff 0.5px, transparent 0.5px)', backgroundSize: '16px 16px' }}
        />

        <div className="relative max-w-7xl mx-auto px-6 lg:px-8 py-16 md:py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left — copy (C's layout: label above, no logo next to label) */}
            <div>
              <p
                className="text-sm font-semibold tracking-wide uppercase mb-4"
                style={{ color: BRAND.teal }}
              >
                Healthcare Bond Intelligence
              </p>
              <h1 className="font-serif text-3xl md:text-4xl lg:text-5xl font-bold leading-tight text-white max-w-xl mb-6">
                You're planning a bond issuance. Bring better evidence into the
                advisor-led process.
              </h1>
              <p className="text-lg text-gray-300 max-w-lg mb-10 leading-relaxed">
                Muni-Pal's Healthcare Market Intelligence Report benchmarks your
                deal against{' '}
                <span className="text-white font-semibold">
                  866 actual municipal bond transactions
                </span>{' '}
                — so your team can compare readiness signals, understand market context,
                and prepare better questions for registered-advisor review.

              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/tools/market-intelligence"
                  className="inline-flex items-center justify-center gap-2 bg-muni-orange hover:bg-[var(--brand-cta-hover)] text-white font-semibold px-8 py-4 rounded-lg transition-colors text-base shadow-lg shadow-muni-orange/20"
                >
                  Get Your Free Market Intelligence Report
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link
                  to="/tools"
                  className="inline-flex items-center justify-center gap-2 border border-white/25 hover:border-white/50 text-white font-medium px-8 py-4 rounded-lg transition-colors backdrop-blur-sm bg-white/5"
                >
                  See the Bond Readiness Path
                  <ChevronRight className="h-5 w-5" />
                </Link>
              </div>
            </div>

            {/* Right — Browser mockup (C's BrowserFrame) */}
            <div className="hidden lg:block">
              <BrowserFrame
                src="/screenshots/readiness-checklist.png"
                alt="Muni-Pal Bond Readiness Checklist"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  VALUE PROPS — Glass Cards (from A)                           */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 -mt-10 relative z-10 mb-16">
        <div className="grid gap-6 md:grid-cols-3">
          {VALUE_PROPS.map((prop) => (
            <div
              key={prop.headline}
              className="bg-white/80 backdrop-blur-sm border border-white/20 shadow-lg rounded-xl p-8 hover:shadow-xl transition-shadow"
            >
              <div className="h-12 w-12 rounded-xl bg-muni-navy flex items-center justify-center mb-5">
                <prop.icon className="h-6 w-6 text-muni-teal" />
              </div>
              <h3 className="font-serif text-lg font-semibold text-gray-900 mb-3">
                {prop.headline}
              </h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                {prop.copy}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ============================================================ */}
      {/*  SOCIAL PROOF STATS — Glass Bar (from A)                      */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-16">
        <div className="bg-white/80 backdrop-blur-sm border border-white/20 shadow-lg rounded-xl py-8 px-6">
          <div className="flex flex-wrap justify-center gap-12 text-center">
            {[
              { value: '866', label: 'municipal bond transactions analyzed' },
              { value: '3.20x', label: 'Median healthcare DSCR', sub: '(gross revenue pledge basis)' },
              { value: '5', label: 'Risk categories scored' },
              { value: '1,318', label: 'Financial reports in corpus' },
            ].map((stat) => (
              <div key={stat.label}>
                <span className="block text-3xl font-bold text-muni-navy font-serif">{stat.value}</span>
                <span className="text-sm text-gray-500 mt-1 block">{stat.label}</span>
                {stat.sub && (
                  <span className="block text-[10px] text-gray-400">{stat.sub}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  ENGAGEMENT PATH — Elegant Steps with Gold Accents (from A)   */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-16">
        <div className="w-16 h-px bg-muni-gold mb-8" />
        <h2 className="font-serif text-2xl md:text-3xl font-bold text-gray-900 mb-2">
          The Bond Readiness Path
        </h2>
        <p className="text-gray-600 mb-10 max-w-2xl">
          From free benchmarks to deal-ready in five steps. Start with the data
          — escalate only when you're confident in the opportunity.
        </p>

        <div className="grid gap-0 md:grid-cols-5 relative">
          <div className="hidden md:block absolute top-8 left-[12.5%] right-[12.5%] h-px bg-gray-200" />
          {ENGAGEMENT_PATH.map((step) => (
            <div key={step.name} className="relative flex flex-col items-center text-center px-4 mb-8 md:mb-0">
              <div
                className={`relative z-10 h-16 w-16 rounded-full flex items-center justify-center text-lg font-bold mb-4 ${
                  step.price === 'Free'
                    ? 'bg-muni-gold text-white shadow-lg shadow-muni-gold/20'
                    : 'bg-muni-navy text-white'
                }`}
              >
                {step.step}
              </div>
              <span
                className={`text-xs font-semibold px-3 py-1 rounded-full mb-3 ${
                  step.price === 'Free'
                    ? 'bg-muni-gold/10 text-muni-gold'
                    : 'bg-muni-orange/10 text-muni-orange'
                }`}
              >
                {step.price}
              </span>
              <h3 className="text-sm font-semibold text-gray-900 mb-2">
                {step.name}
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ============================================================ */}
      {/*  COST OF INACTION (from A)                                    */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-16">
        <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-xl border border-red-100 p-8 md:p-10">
          <div className="flex items-start gap-5">
            <div className="h-14 w-14 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
              <TrendingUp className="h-7 w-7 text-red-600" />
            </div>
            <div>
              <h3 className="font-serif text-xl font-bold text-gray-900 mb-3">
                The Cost of Inaction
              </h3>
              <p className="text-base text-gray-700 leading-relaxed mb-4">
                Spread differentials can materially affect long-term borrowing costs.
                <span className="font-bold text-red-700">$27M+</span> over 25
                years on a $75M deal. The Accelerator helps you document your way
                advisor-review questions before your registered professionals
                <span className="font-semibold">less than 0.04%</span> of deal
                make pricing, sizing, issuance, or execution recommendations.
              </p>
              <p className="text-sm text-gray-500">
                Based on observed AA vs. BBB spread differentials in public
                healthcare revenue bond disclosures (gross revenue pledge basis).
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  WHEN TO ENGAGE — Gantt chart from C                          */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-16">
        <div className="w-16 h-px bg-muni-gold mb-8" />
        <h2 className="font-serif text-2xl md:text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <Clock className="h-7 w-7 text-muni-teal" />
          When to Engage
        </h2>
        <p className="text-gray-600 mb-10 max-w-2xl">
          A typical healthcare bond transaction takes 5–8 months. Here's how the
          Bond Readiness Path maps to your deal timeline.
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
      </section>

      {/* ============================================================ */}
      {/*  WORKS WITH YOUR ADVISORS                                     */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-16">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 md:p-10">
          <div className="flex items-center gap-3 mb-6">
            <div className="h-10 w-10 rounded-lg flex items-center justify-center" style={{ backgroundColor: `color-mix(in srgb, ${BRAND.teal} 8%, transparent)` }}>
              <Users className="h-5 w-5" style={{ color: BRAND.teal }} />
            </div>
            <h2 className="font-serif text-xl md:text-2xl font-bold text-gray-900">
              Works With Your Advisors, Not Against Them
            </h2>
          </div>
          <p className="text-base text-gray-700 leading-relaxed mb-4">
            Muni-Pal is independent due diligence — not a replacement for your
            financial advisor. We give you the benchmarks, risk analysis, and
            market context so you walk into advisor meetings asking better
            questions and validating recommendations with data.
          </p>
          <p className="text-base text-gray-700 leading-relaxed">
            Your advisor brings deal execution. Muni-Pal brings evidence.
            Together, you get a stronger credit story and better terms.
          </p>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  AUDIENCE FILTER — Dashboard Comparison (from C)              */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-16">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <h3 className="font-serif text-lg font-semibold text-gray-800 px-8 pt-8 pb-5 flex items-center gap-3">
            <Shield className="h-5 w-5 text-gray-400" />
            Who this is for — and who it isn't
          </h3>
          <div className="grid md:grid-cols-2 gap-0">
            <div className="bg-white p-8 border-r border-gray-200">
              <p className="text-xs font-bold uppercase tracking-widest mb-4" style={{ color: BRAND.teal }}>
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
            <div className="bg-gray-50 p-8">
              <p className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4">
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
      {/*  SECONDARY TRUST CTAs (from A)                                */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-16 grid gap-6 sm:grid-cols-2">
        <Link
          to="/tools/market-intelligence"
          className="flex items-start gap-5 bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow group"
        >
          <div className="h-12 w-12 rounded-xl bg-muni-teal/10 flex items-center justify-center flex-shrink-0">
            <FileText className="h-6 w-6 text-muni-teal" />
          </div>
          <div>
            <p className="font-semibold text-gray-900 group-hover:text-muni-teal transition-colors">
              View a Sample MIR Report
            </p>
            <p className="text-sm text-gray-500 mt-1.5">
              See the exact benchmarks, risk scoring, and pricing data a
              healthcare CFO receives — before you request your own.
            </p>
          </div>
        </Link>
        <Link
          to="/tools/market-intelligence"
          className="flex items-start gap-5 bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow group"
        >
          <div className="h-12 w-12 rounded-xl bg-muni-navy/10 flex items-center justify-center flex-shrink-0">
            <BarChart3 className="h-6 w-6 text-muni-navy" />
          </div>
          <div>
            <p className="font-semibold text-gray-900 group-hover:text-muni-navy transition-colors">
              Compare Risk Profiles by Rating Tier
            </p>
            <p className="text-sm text-gray-500 mt-1.5">
              How does your system's risk profile stack up against AA, A, and
              BBB-rated peers? See the gap analysis framework.
            </p>
          </div>
        </Link>
      </section>

      {/* ============================================================ */}
      {/*  PLATFORM PREVIEW — Full-width browser mockup (from C)        */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-16">
        <h2 className="font-serif text-2xl font-bold text-gray-900 mb-6 text-center">
          See the Platform in Action
        </h2>
        <BrowserFrame
          src="/screenshots/monte-carlo.png"
          alt="Muni-Pal Monte Carlo Risk Analysis"
          url="app.muni-pal.io/tools/risk-analysis"
        />
      </section>

      {/* ============================================================ */}
      {/*  BOTTOM CTA (from A)                                          */}
      {/* ============================================================ */}
      <section className="bg-muni-navy py-16 md:py-20">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="font-serif text-2xl md:text-3xl font-bold text-white mb-4">
            Get Your Free Market Intelligence Report
          </h2>
          <p className="text-gray-300 mb-8 max-w-lg mx-auto">
            No login required. No sales call. Just the data your advisors charge
            $25K to compile.
          </p>
          <Link
            to="/tools/market-intelligence"
            className="inline-flex items-center gap-2 bg-muni-orange hover:bg-[var(--brand-cta-hover)] text-white font-semibold px-10 py-4 rounded-lg transition-colors text-lg shadow-lg shadow-muni-orange/20"
          >
            Start Now — It's Free
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  FOOTER (from A)                                              */}
      {/* ============================================================ */}
      <footer className="max-w-6xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col items-center gap-3 py-10 border-t border-gray-200">
          <img
            src="/muni-pal-logo-transparent.png"
            alt="Muni-Pal"
            className="h-10 w-10 object-contain opacity-50"
            style={{ filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.15))' }}
          />
          <p className="text-sm text-gray-400">
            Muni-Pal &mdash; A Launch Shop product. Built by Innovation Factory.
          </p>
          <p className="text-[11px] text-gray-400 max-w-2xl text-center leading-relaxed">
            Bond Readiness Accelerator is an educational and analytical service.
            It is not municipal advisory advice and does not replace registered
            advisors, counsel, underwriters, issuers, or borrowers.
          </p>
        </div>
      </footer>
    </div>
  )
}
