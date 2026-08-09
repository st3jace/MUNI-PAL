import { Link } from 'react-router-dom'
import {
  BarChart3,
  DollarSign,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  Clock,
  Shield,
  TrendingUp,
  Users,
} from 'lucide-react'

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
  {
    step: 1,
    name: 'Market Intelligence Report',
    price: 'Free',
    description:
      'Sector benchmarks — DSCR, pricing, risk profile, Pareto framework',
  },
  {
    step: 2,
    name: 'Readiness Scan',
    price: 'Free',
    description:
      'Automated pre-screen — sector fit, deal size, top 3 gaps',
  },
  {
    step: 3,
    name: 'Bond Readiness Diagnostic',
    price: '$15K\u2013$25K',
    description:
      'Full score + gap analysis + critical path to close',
  },
  {
    step: 4,
    name: 'Standard Engagement',
    price: '$40K\u2013$50K',
    description:
      'Diagnostic + readiness workplan + registered-advisor review support',
  },
  {
    step: 5,
    name: 'Bond Readiness Accelerator',
    price: '$75K+',
    description:
      'Readiness support — gap remediation, benchmarking, and preparation workflow',
  },
]

const TIMELINE = [
  {
    months: 'Month 1\u20132',
    label: 'Discovery',
    step: 'Market Intelligence Report + Readiness Scan',
    detail:
      'Benchmark your system against peers. Identify top gaps before engaging advisors.',
  },
  {
    months: 'Month 2\u20133',
    label: 'Diagnostic',
    step: 'Bond Readiness Diagnostic',
    detail:
      'Full scoring, gap analysis, and critical path. Know exactly what underwriters will scrutinize.',
  },
  {
    months: 'Month 3\u20135',
    label: 'Coordination',
    step: 'Standard Engagement',
    detail:
      'Readiness workplan, cost-context benchmarking, and milestone tracking for advisor/deal-team review.',
  },
  {
    months: 'Month 4\u20137',
    label: 'Acceleration',
    step: 'Bond Readiness Accelerator',
    detail:
      'Full pre-issuance support \u2014 gap remediation, benchmarking, and deal timeline optimization.',
  },
  {
    months: 'Month 6\u20139',
    label: 'Execution',
    step: 'Market entry',
    detail:
      'Go to market with a complete, defensible credit story. Advisors execute \u2014 you negotiate from strength.',
  },
]

export default function HealthcareCFOLanding() {
  return (
    <div className="min-h-screen bg-white">
      {/* ============================================================ */}
      {/*  HERO                                                         */}
      {/* ============================================================ */}
      <section className="relative overflow-hidden">
        {/* Subtle mesh gradient background */}
        <div
          className="absolute inset-0"
          style={{
            background:
              'radial-gradient(ellipse 80% 60% at 20% 20%, rgba(45,174,172,0.07) 0%, transparent 60%), radial-gradient(ellipse 60% 50% at 80% 80%, rgba(27,58,92,0.05) 0%, transparent 60%)',
          }}
        />

        <div className="relative max-w-6xl mx-auto px-6 py-16 md:py-24">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Copy */}
            <div>
              <div className="mb-8">
                <img
                  src="/muni-pal-logo-transparent.png"
                  alt="Muni-Pal"
                  className="h-24 w-24 object-contain"
                />
              </div>

              <p className="text-xs font-semibold tracking-widest uppercase text-muni-teal mb-4">
                Healthcare Bond Intelligence
              </p>

              <h1 className="text-3xl md:text-4xl lg:text-5xl font-light text-muni-navy leading-tight mb-6">
                You're planning a bond issuance.{' '}
                <span className="font-semibold">
                  Bring better evidence into the advisor-led process.
                </span>
              </h1>

              <p className="text-lg text-gray-500 leading-relaxed mb-10 max-w-lg">
                Muni-Pal benchmarks your deal against 866 actual municipal
                bond transactions — so you walk into the room knowing what
                top-performing credits look like, market context for advisor review,
                and where risk disclosures go wrong.
              </p>

              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/tools/market-intelligence"
                  className="inline-flex items-center justify-center gap-2 rounded-full px-8 py-3 bg-muni-orange hover:bg-[var(--brand-cta-hover)] text-white font-medium transition-colors"
                >
                  Get Your Free Market Intelligence Report
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link
                  to="/tools"
                  className="inline-flex items-center justify-center gap-2 rounded-full px-8 py-3 border border-muni-navy/20 text-muni-navy font-medium hover:border-muni-navy/40 transition-colors"
                >
                  See the Bond Readiness Path
                  <ChevronRight className="h-4 w-4" />
                </Link>
              </div>
            </div>

            {/* Right: Floating screenshots */}
            <div className="relative hidden lg:block h-[420px]">
              <div className="absolute top-0 right-0 w-[320px] shadow-2xl rounded-xl overflow-hidden transform rotate-[1deg]">
                <img
                  src="/screenshots/readiness-checklist.png"
                  alt="Readiness Checklist"
                  className="w-full"
                />
              </div>
              <div className="absolute bottom-0 left-0 w-[280px] shadow-2xl rounded-xl overflow-hidden transform rotate-[-2deg]">
                <img
                  src="/screenshots/monte-carlo.png"
                  alt="Monte Carlo Analysis"
                  className="w-full"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  VALUE PROPS                                                  */}
      {/* ============================================================ */}
      <section className="py-16 md:py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid gap-6 md:grid-cols-3">
            {VALUE_PROPS.map((prop) => (
              <div
                key={prop.headline}
                className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 hover:shadow-md transition-all duration-300 hover:scale-[1.02]"
              >
                <div className="h-12 w-12 rounded-2xl bg-gray-50 flex items-center justify-center mb-6">
                  <prop.icon className="h-6 w-6 text-muni-teal" />
                </div>
                <h3 className="text-lg font-semibold text-muni-navy mb-3">
                  {prop.headline}
                </h3>
                <p className="text-sm text-gray-500 leading-relaxed">
                  {prop.copy}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  STATS ROW                                                    */}
      {/* ============================================================ */}
      <section className="py-16 md:py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex flex-wrap justify-center gap-16 md:gap-24 text-center">
            {[
              { value: '866', label: 'municipal bond transactions analyzed' },
              { value: '3.20x', label: 'Median healthcare DSCR' },
              { value: '5', label: 'Risk categories scored' },
              { value: '1,318', label: 'Financial reports in corpus' },
            ].map((stat) => (
              <div key={stat.label}>
                <div className="text-4xl md:text-5xl font-bold text-muni-navy">
                  {stat.value}
                </div>
                <div className="text-xs text-gray-400 mt-2 uppercase tracking-wider">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  ENGAGEMENT PATH                                              */}
      {/* ============================================================ */}
      <section className="py-16 md:py-20">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-2xl font-light text-muni-navy mb-2">
            The Bond Readiness Path
          </h2>
          <p className="text-sm text-gray-500 mb-12 max-w-xl">
            From free benchmarks to deal-ready in five steps. Start with the
            data — escalate only when you're confident in the opportunity.
          </p>

          <div className="relative">
            {/* Connecting line */}
            <div className="hidden md:block absolute top-6 left-[10%] right-[10%] h-px bg-gray-200" />

            <div className="grid gap-6 md:grid-cols-5">
              {ENGAGEMENT_PATH.map((step) => (
                <div key={step.name} className="relative text-center">
                  {/* Numbered circle */}
                  <div className="inline-flex items-center justify-center h-12 w-12 rounded-full bg-muni-teal text-white text-sm font-bold mb-4 relative z-10">
                    {step.step}
                  </div>
                  <div className="mb-2">
                    <span
                      className={`inline-block text-xs font-semibold px-3 py-1 rounded-full ${
                        step.price === 'Free'
                          ? 'bg-green-50 text-green-600'
                          : 'bg-muni-orange/10 text-muni-orange'
                      }`}
                    >
                      {step.price}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-muni-navy mb-2">
                    {step.name}
                  </h3>
                  <p className="text-xs text-gray-400 leading-relaxed">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  COST OF INACTION                                             */}
      {/* ============================================================ */}
      <section className="py-16 md:py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div
            className="rounded-2xl p-8 md:p-12"
            style={{
              background:
                'linear-gradient(135deg, rgba(45,174,172,0.06) 0%, rgba(232,145,58,0.06) 100%)',
            }}
          >
            <div className="flex items-start gap-6">
              <div className="h-14 w-14 rounded-2xl bg-white flex items-center justify-center flex-shrink-0 shadow-sm">
                <TrendingUp className="h-7 w-7 text-muni-orange" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-muni-navy mb-3">
                  The Cost of Inaction
                </h3>
                <p className="text-sm text-gray-600 leading-relaxed mb-4">
                  The difference between an A-rated and BBB-rated issuance costs{' '}
                  <span className="text-3xl font-bold text-muni-navy">
                    $27M+
                  </span>{' '}
                  over 25 years on a $75M deal. The Accelerator helps you
                  organize evidence for registered-advisor review — for{' '}
                  <span className="font-semibold text-muni-navy">
                    less than 0.04%
                  </span>{' '}
                  of deal size.
                </p>
                <p className="text-xs text-gray-400">
                  Based on observed AA vs. BBB spread differentials in public
                  healthcare revenue bond disclosures (gross revenue pledge basis).
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  TIMELINE                                                     */}
      {/* ============================================================ */}
      <section className="py-16 md:py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center gap-3 mb-2">
            <Clock className="h-5 w-5 text-muni-teal" />
            <h2 className="text-2xl font-light text-muni-navy">
              When to Engage
            </h2>
          </div>
          <p className="text-sm text-gray-500 mb-12 max-w-xl">
            A typical healthcare bond transaction takes 5-8 months. Here's how
            the Bond Readiness Path maps to your deal timeline.
          </p>

          {/* Horizontal timeline */}
          <div className="relative">
            <div className="hidden md:block absolute top-3 left-0 right-0 h-px bg-muni-teal/20" />
            <div className="grid gap-8 md:grid-cols-5">
              {TIMELINE.map((phase) => (
                <div key={phase.months} className="relative">
                  {/* Teal dot */}
                  <div className="h-6 w-6 rounded-full bg-muni-teal border-4 border-white shadow-sm mb-4 relative z-10" />
                  <span className="text-xs font-semibold text-muni-teal uppercase tracking-wider">
                    {phase.months}
                  </span>
                  <p className="text-sm font-semibold text-muni-navy mt-2">
                    {phase.label}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">{phase.step}</p>
                  <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                    {phase.detail}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  WORKS WITH YOUR ADVISORS                                     */}
      {/* ============================================================ */}
      <section className="py-16 md:py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="bg-white border border-gray-100 rounded-2xl p-8 md:p-10">
            <div className="flex items-center gap-3 mb-6">
              <Users className="h-6 w-6 text-muni-teal" />
              <h2 className="text-xl font-bold text-muni-navy">
                Works With Your Advisors, Not Against Them
              </h2>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed mb-4 max-w-2xl">
              Muni-Pal is independent due diligence — not a replacement for your
              financial advisor. We give you the benchmarks, risk analysis, and
              market context so you walk into advisor meetings asking better
              questions and validating recommendations with data.
            </p>
            <p className="text-sm text-gray-600 leading-relaxed max-w-2xl">
              Your advisor brings deal execution. Muni-Pal brings evidence.
              Together, you get a stronger credit story and better terms.
            </p>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  AUDIENCE FILTER                                              */}
      {/* ============================================================ */}
      <section className="py-16 md:py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center gap-3 mb-8">
            <Shield className="h-5 w-5 text-gray-400" />
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
              Who this is for — and who it isn't
            </h3>
          </div>
          <div className="grid gap-12 md:grid-cols-2">
            <div>
              <p className="text-xs font-semibold text-green-600 mb-4 uppercase tracking-widest">
                Built for
              </p>
              <ul className="space-y-4">
                {[
                  'Healthcare CFOs and finance directors planning a bond issuance',
                  'Hospital systems evaluating capital structure options',
                  'Deals above $10M in total issuance size',
                ].map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-3 text-sm text-gray-600"
                  >
                    <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-400 mb-4 uppercase tracking-widest">
                Not designed for
              </p>
              <ul className="space-y-4">
                {[
                  'Sub-$10M deal sizes',
                  'Non-healthcare municipal issuers',
                  'General financial advice seekers',
                ].map((item) => (
                  <li
                    key={item}
                    className="flex items-start gap-3 text-sm text-gray-400"
                  >
                    <span className="mt-0.5 flex-shrink-0">&mdash;</span>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  BOTTOM CTA                                                   */}
      {/* ============================================================ */}
      <section className="py-16 md:py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="bg-muni-navy rounded-2xl p-10 md:p-14 text-center">
            <h2 className="text-2xl font-light text-white mb-3">
              Get Your Free Market Intelligence Report
            </h2>
            <p className="text-sm text-gray-400 mb-8 max-w-md mx-auto">
              No login required. No sales call. Just the data your advisors
              charge $25K to compile.
            </p>
            <Link
              to="/tools/market-intelligence"
              className="inline-flex items-center gap-2 rounded-full px-10 py-4 bg-muni-orange hover:bg-[var(--brand-cta-hover)] text-white font-medium transition-colors"
            >
              Start Now — It's Free
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  FOOTER                                                       */}
      {/* ============================================================ */}
      <footer className="py-10">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-center gap-3 mb-4">
            <img
              src="/muni-pal-logo-transparent.png"
              alt="Muni-Pal"
              className="h-8 w-8 object-contain opacity-50"
            />
            <p className="text-xs text-gray-400">
              Muni-Pal &mdash; A Launch Shop product. Built by Innovation
              Factory.
            </p>
          </div>
          <p className="text-[11px] text-gray-300 text-center max-w-3xl mx-auto leading-relaxed">
            Bond Readiness Accelerator is an educational and analytical
            service. It does not constitute municipal advisory services as
            defined under Section 15B of the Securities Exchange Act. Muni-Pal
            provides educational and analytical services and is not a
            registered municipal advisor.
          </p>
        </div>
      </footer>
    </div>
  )
}
