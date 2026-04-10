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
} from 'lucide-react'

/* ------------------------------------------------------------------ */
/*  Brand constants                                                    */
/* ------------------------------------------------------------------ */
const BRAND = {
  navy: '#1B3A5C',
  teal: '#2DAEAC',
  orange: '#E8913A',
  orangeHover: '#d47e2e',
  gold: '#f59e0b',
}

/* ------------------------------------------------------------------ */
/*  Data                                                               */
/* ------------------------------------------------------------------ */
const VALUE_PROPS = [
  {
    icon: BarChart3,
    headline: 'Know what "good" looks like',
    copy: 'See the exact DSCR (gross revenue pledge, healthcare-adjusted), payer mix, days cash on hand, and pledge structures that separate AA-rated healthcare systems from BBB — drawn from real EMMA data, not industry averages.',
  },
  {
    icon: DollarSign,
    headline: 'Know what it costs — right now',
    copy: "Corpus-calibrated TIC estimates by rating tier. Not a vague \"market rate\" answer. Actual spread data so you can pressure-test your advisor's term sheet.",
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
  { step: 4, name: 'Bond Readiness Accelerator', price: '$75K+', description: 'Full pre-issuance support — gap remediation, benchmarking, and timeline optimization' },
]

const TIMELINE_PHASES = [
  { months: 'Month 0–2', label: 'Discovery', color: BRAND.teal, width: '25%', ml: '0%' },
  { months: 'Month 2–3', label: 'Diagnostic', color: BRAND.orange, width: '15%', ml: '15%' },
  { months: 'Month 3–6', label: 'Preparation', color: '#6366f1', width: '30%', ml: '25%' },
  { months: 'Month 6–9+', label: 'Execution', color: BRAND.navy, width: '30%', ml: '55%' },
]

/* ------------------------------------------------------------------ */
/*  Preview Card (hero right side)                                     */
/* ------------------------------------------------------------------ */
function PreviewCard() {
  return (
    <div className="bg-white rounded-xl shadow-2xl overflow-hidden border border-gray-100 max-w-sm">
      <div className="bg-gradient-to-r from-[#1B3A5C] to-[#2a4f7a] px-5 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-400" />
          <span className="text-xs text-gray-300 font-mono">app.muni-pal.io</span>
        </div>
      </div>
      <div className="p-5 space-y-4">
        <div>
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Bond Readiness Score</p>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold text-[#1B3A5C]">72</span>
            <span className="text-sm text-gray-400 mb-1">/100</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2 mt-2">
            <div className="bg-[#2DAEAC] h-2 rounded-full" style={{ width: '72%' }} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'DSCR', value: '1.45x', color: BRAND.teal },
            { label: 'Rating', value: 'A-', color: BRAND.gold },
            { label: 'Coverage', value: '2.1x', color: BRAND.teal },
            { label: 'Risk Score', value: 'Low', color: '#22c55e' },
          ].map((item) => (
            <div key={item.label} className="bg-gray-50 rounded-lg p-2.5">
              <p className="text-[10px] text-gray-400 uppercase">{item.label}</p>
              <p className="text-sm font-bold" style={{ color: item.color }}>{item.value}</p>
            </div>
          ))}
        </div>
        <div className="border-t border-gray-100 pt-3">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <span className="text-xs text-gray-600">3 of 6 dimensions bond-ready</span>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ================================================================== */
/*  Main Component                                                     */
/* ================================================================== */
export default function HealthcareCFOLanding() {
  return (
    <div className="-m-6">
      {/* ============================================================ */}
      {/*  HERO                                                        */}
      {/* ============================================================ */}
      <section className="relative bg-gradient-to-br from-[#1B3A5C] via-[#1B3A5C] to-indigo-900 overflow-hidden">
        {/* Subtle radial glow */}
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background:
              'radial-gradient(ellipse 60% 50% at 30% 40%, rgba(45,174,172,0.4) 0%, transparent 70%)',
          }}
        />
        {/* Subtle grid dots */}
        <div
          className="absolute inset-0 opacity-[0.05]"
          style={{ backgroundImage: 'radial-gradient(#ffffff 0.5px, transparent 0.5px)', backgroundSize: '16px 16px' }}
        />

        <div className="relative max-w-7xl mx-auto px-6 lg:px-8 py-14 md:py-20">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left — copy */}
            <div>
              <p
                className="text-sm font-semibold tracking-wide uppercase mb-4"
                style={{ color: BRAND.teal }}
              >
                Healthcare Bond Intelligence
              </p>
              <h1 className="text-3xl md:text-4xl lg:text-[2.75rem] font-bold leading-tight text-white max-w-xl mb-6">
                You're planning a bond issuance. Here's what your advisors won't
                tell you for free.
              </h1>
              <p className="text-base md:text-lg text-gray-300 max-w-lg mb-10 leading-relaxed">
                Muni-Pal's Healthcare Market Intelligence Report benchmarks your
                deal against{' '}
                <span className="text-white font-semibold">
                  866 actual EMMA transactions
                </span>{' '}
                — so you walk into the room knowing what top-performing credits
                look like, what borrowing actually costs, and where risk
                disclosures go wrong.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/tools/market-intelligence"
                  className="inline-flex items-center justify-center gap-2 text-white font-semibold px-7 py-3.5 rounded-lg transition-colors text-base shadow-lg"
                  style={{ backgroundColor: BRAND.orange, boxShadow: `0 8px 24px ${BRAND.orange}33` }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = BRAND.orangeHover)}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = BRAND.orange)}
                >
                  Get Your Free Market Intelligence Report
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <Link
                  to="#engagement-path"
                  className="inline-flex items-center justify-center gap-2 border border-white/25 hover:border-white/50 text-white font-medium px-7 py-3.5 rounded-lg transition-colors backdrop-blur-sm bg-white/5"
                >
                  See the Bond Readiness Path
                  <ChevronRight className="h-5 w-5" />
                </Link>
              </div>
            </div>

            {/* Right — Preview card */}
            <div className="hidden lg:flex justify-center">
              <PreviewCard />
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  VALUE PROPS — Cards overlapping hero                         */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 -mt-8 relative z-10 mb-14">
        <div className="grid gap-6 md:grid-cols-3">
          {VALUE_PROPS.map((prop) => (
            <div
              key={prop.headline}
              className="bg-white border border-gray-200 shadow-lg rounded-xl p-7 hover:shadow-xl transition-shadow"
            >
              <div className="h-11 w-11 rounded-xl flex items-center justify-center mb-4" style={{ backgroundColor: BRAND.navy }}>
                <prop.icon className="h-5 w-5" style={{ color: BRAND.teal }} />
              </div>
              <h3 className="text-base font-semibold text-gray-900 mb-2">
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
      {/*  SOCIAL PROOF STATS                                           */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-14">
        <div className="bg-gray-50 border border-gray-100 rounded-xl py-8 px-6">
          <div className="flex flex-wrap justify-center gap-10 md:gap-16 text-center">
            {[
              { value: '866', label: 'EMMA transactions analyzed' },
              { value: '3.20x', label: 'Median healthcare DSCR', sub: '(gross revenue pledge basis)' },
              { value: '5', label: 'Risk categories scored' },
              { value: '1,318', label: 'Financial reports in corpus' },
            ].map((stat) => (
              <div key={stat.label}>
                <span className="block text-3xl font-bold" style={{ color: BRAND.navy }}>{stat.value}</span>
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
      {/*  ENGAGEMENT PATH — 4 Steps with pricing                       */}
      {/* ============================================================ */}
      <section id="engagement-path" className="max-w-6xl mx-auto px-6 lg:px-8 mb-14 scroll-mt-24">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          The Bond Readiness Path
        </h2>
        <p className="text-gray-600 mb-8 max-w-2xl">
          From free benchmarks to deal-ready in four steps. Start with the data
          — escalate only when you're confident in the opportunity.
        </p>

        <div className="grid gap-0 md:grid-cols-4 relative">
          <div className="hidden md:block absolute top-10 left-[12.5%] right-[12.5%] h-px bg-gray-200" />
          {ENGAGEMENT_PATH.map((step) => (
            <div key={step.name} className="relative flex flex-col items-center text-center px-4 mb-8 md:mb-0">
              <div
                className={`relative z-10 h-14 w-14 rounded-full flex items-center justify-center text-lg font-bold mb-3 ${
                  step.price === 'Free'
                    ? 'bg-[#2DAEAC] text-white'
                    : 'bg-[#1B3A5C] text-white'
                }`}
              >
                {step.step}
              </div>
              <span
                className={`text-xs font-semibold px-3 py-1 rounded-full mb-3 ${
                  step.price === 'Free'
                    ? 'bg-green-50 text-green-700'
                    : 'bg-[#E8913A]/10 text-[#E8913A]'
                }`}
              >
                {step.price}
              </span>
              <h3 className="text-sm font-semibold text-gray-900 mb-1.5">
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
      {/*  COST OF INACTION                                             */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-14">
        <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-xl border border-red-100 p-7 md:p-8">
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
              <TrendingUp className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                The Cost of Inaction
              </h3>
              <p className="text-sm text-gray-700 leading-relaxed mb-3">
                The difference between an A-rated and BBB-rated issuance costs{' '}
                <span className="font-bold text-red-700">$27M+</span> over 25
                years on a $75M deal. The Accelerator helps you document your way
                to a better rating — for{' '}
                <span className="font-semibold">less than 0.04%</span> of deal
                size.
              </p>
              <p className="text-xs text-gray-500">
                Based on observed AA vs. BBB spread differentials in EMMA
                healthcare revenue bond data (gross revenue pledge basis).
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  WHEN TO ENGAGE — Timeline                                    */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-14">
        <h2 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <Clock className="h-6 w-6" style={{ color: BRAND.teal }} />
          When to Engage
        </h2>
        <p className="text-gray-600 mb-8 max-w-2xl">
          A typical healthcare bond transaction takes 6–9 months. Here's how the
          Bond Readiness Path maps to your deal timeline.
        </p>

        <div className="space-y-3">
          {TIMELINE_PHASES.map((phase) => (
            <div key={phase.months} className="flex items-center gap-4">
              <div className="w-28 text-right flex-shrink-0 hidden md:block">
                <span className="text-xs font-semibold" style={{ color: BRAND.teal }}>
                  {phase.months}
                </span>
              </div>
              <div className="flex-1 relative">
                <div
                  className="rounded-lg py-3 px-4 text-white text-sm font-semibold"
                  style={{
                    width: phase.width,
                    backgroundColor: phase.color,
                    marginLeft: phase.ml,
                  }}
                >
                  {phase.label}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ============================================================ */}
      {/*  AUDIENCE FILTER                                              */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-14">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <h3 className="text-base font-semibold text-gray-800 px-7 pt-7 pb-4 flex items-center gap-3">
            <Shield className="h-5 w-5 text-gray-400" />
            Who this is for — and who it isn't
          </h3>
          <div className="grid md:grid-cols-2 gap-0">
            <div className="bg-white p-7 md:border-r border-gray-200">
              <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: BRAND.teal }}>
                Built for
              </p>
              <ul className="space-y-2.5">
                {[
                  'Healthcare CFOs and finance directors planning a bond issuance',
                  'Hospital systems evaluating capital structure options',
                  'Deals above $10M in total issuance size',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-gray-700">
                    <CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5" style={{ color: BRAND.teal }} />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-gray-50 p-7">
              <p className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">
                Not designed for
              </p>
              <ul className="space-y-2.5">
                {[
                  'Sub-$10M deal sizes',
                  'Non-healthcare municipal issuers',
                  'General financial advice seekers',
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5 text-sm text-gray-400">
                    <XCircle className="h-4 w-4 flex-shrink-0 mt-0.5 text-gray-300" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  SECONDARY TRUST CTAs                                         */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-14 grid gap-5 sm:grid-cols-2">
        <Link
          to="/tools/market-intelligence"
          className="flex items-start gap-4 bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow group"
        >
          <div className="h-11 w-11 rounded-xl bg-[#2DAEAC]/10 flex items-center justify-center flex-shrink-0">
            <FileText className="h-5 w-5 text-[#2DAEAC]" />
          </div>
          <div>
            <p className="font-semibold text-gray-900 group-hover:text-[#2DAEAC] transition-colors">
              View a Sample MIR Report
            </p>
            <p className="text-sm text-gray-500 mt-1">
              See the exact benchmarks, risk scoring, and pricing data a
              healthcare CFO receives — before you request your own.
            </p>
          </div>
        </Link>
        <Link
          to="/tools/market-intelligence"
          className="flex items-start gap-4 bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-shadow group"
        >
          <div className="h-11 w-11 rounded-xl bg-[#1B3A5C]/10 flex items-center justify-center flex-shrink-0">
            <BarChart3 className="h-5 w-5 text-[#1B3A5C]" />
          </div>
          <div>
            <p className="font-semibold text-gray-900 group-hover:text-[#1B3A5C] transition-colors">
              Compare Risk Profiles by Rating Tier
            </p>
            <p className="text-sm text-gray-500 mt-1">
              How does your system's risk profile stack up against AA, A, and
              BBB-rated peers? See the gap analysis framework.
            </p>
          </div>
        </Link>
      </section>

      {/* ============================================================ */}
      {/*  PLATFORM PREVIEW — Monte Carlo                               */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-14">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          See the Platform in Action
        </h2>
        <div className="bg-[#1B3A5C] rounded-xl p-6 md:p-8">
          <h3 className="text-white font-semibold text-lg mb-1">Risk Analysis — Monte Carlo Simulation</h3>
          <p className="text-gray-400 text-sm mb-6">
            1,000 simulations over 25 years with 10.00% revenue volatility and 3.00% expense volatility.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            {[
              { label: 'P(VR BREACH)', value: '4.10%', color: 'text-white' },
              { label: 'NEGATIVE NET INCOME', value: '41.34%', color: 'text-white' },
              { label: 'VaR (5TH)', value: '-45.52%', color: 'text-red-400' },
              { label: 'EXPECTED COVERAGE RATIO', value: '-81.07%', color: 'text-red-400' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <p className={`text-2xl md:text-3xl font-bold ${stat.color}`}>{stat.value}</p>
                <p className="text-[10px] text-gray-400 uppercase mt-1 tracking-wider">{stat.label}</p>
              </div>
            ))}
          </div>
          <div>
            <h4 className="text-white font-semibold text-sm mb-3">Distribution Percentiles</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 text-xs uppercase">
                    <th className="text-left py-2 pr-4">Metric</th>
                    <th className="text-right py-2 px-3">P5 (Downside)</th>
                    <th className="text-right py-2 px-3">P50 (Median)</th>
                    <th className="text-right py-2 px-3">Mean</th>
                    <th className="text-right py-2 px-3">P95 (Upside)</th>
                  </tr>
                </thead>
                <tbody className="text-gray-300">
                  <tr className="border-t border-white/10">
                    <td className="py-2 pr-4 text-white">IRR</td>
                    <td className="text-right px-3">-45.52%</td>
                    <td className="text-right px-3">2.63%</td>
                    <td className="text-right px-3">-2.28%</td>
                    <td className="text-right px-3">15.92%</td>
                  </tr>
                  <tr className="border-t border-white/10">
                    <td className="py-2 pr-4 text-white">Equity Multiple</td>
                    <td className="text-right px-3">0.06x</td>
                    <td className="text-right px-3">1.41x</td>
                    <td className="text-right px-3">1.39x</td>
                    <td className="text-right px-3">5.90x</td>
                  </tr>
                  <tr className="border-t border-white/10">
                    <td className="py-2 pr-4 text-white">Min DSCR</td>
                    <td className="text-right px-3">1.34x</td>
                    <td className="text-right px-3">1.04x</td>
                    <td className="text-right px-3">2.96x</td>
                    <td className="text-right px-3">4.22x</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  BOTTOM CTA                                                   */}
      {/* ============================================================ */}
      <section style={{ backgroundColor: BRAND.navy }} className="py-14 md:py-16">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">
            Get Your Free Market Intelligence Report
          </h2>
          <p className="text-gray-300 mb-8 max-w-lg mx-auto text-sm">
            No login required. No sales call. Just the data your advisors charge
            $25K to compile.
          </p>
          <Link
            to="/tools/market-intelligence"
            className="inline-flex items-center gap-2 text-white font-semibold px-10 py-4 rounded-lg transition-colors text-lg"
            style={{ backgroundColor: BRAND.orange, boxShadow: `0 8px 24px ${BRAND.orange}33` }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = BRAND.orangeHover)}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = BRAND.orange)}
          >
            Start Now — It's Free
            <ArrowRight className="h-5 w-5" />
          </Link>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  FOOTER                                                       */}
      {/* ============================================================ */}
      <footer className="max-w-6xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col items-center gap-3 py-8 border-t border-gray-200">
          <img
            src="/muni-pal-emblem.png"
            alt="Muni-Pal"
            className="h-10 w-10 object-contain opacity-50"
          />
          <p className="text-sm text-gray-400">
            Muni-Pal &mdash; A Launch Shop product. Built by Innovation Factory.
          </p>
          <p className="text-[11px] text-gray-400 max-w-2xl text-center leading-relaxed">
            Bond Readiness Accelerator is an educational and analytical service.
            It does not constitute municipal advisory services as defined under
            Section 15B of the Securities Exchange Act.
          </p>
        </div>
      </footer>
    </div>
  )
}
