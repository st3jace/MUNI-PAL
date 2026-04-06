import { Link } from 'react-router-dom'
import {
  BarChart3,
  Shield,
  DollarSign,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  Clock,
  FileText,
  TrendingUp,
  Users,
} from 'lucide-react'

const VALUE_PROPS = [
  {
    icon: BarChart3,
    headline: 'Know what "good" looks like',
    copy: 'See the exact DSCR (gross revenue pledge, healthcare-adjusted), payer mix, days cash on hand, and pledge structures that separate AA-rated healthcare systems from BBB — drawn from real EMMA data, not industry averages.',
  },
  {
    icon: DollarSign,
    headline: 'Know what it costs — right now',
    copy: 'Corpus-calibrated TIC estimates by rating tier. Not a vague "market rate" answer. Actual spread data so you can pressure-test your advisor\'s term sheet.',
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
    name: 'Bond Readiness Assessment',
    price: 'Free',
    description:
      'Score your facility across 6 dimensions — gaps, priorities, timeline',
  },
  {
    step: 2,
    name: 'Market Intelligence Report',
    price: 'Free',
    description:
      'Sector benchmarks — DSCR, pricing, risk profile, Pareto framework',
  },
  {
    step: 3,
    name: 'Bond Readiness Diagnostic',
    price: '$15K–$25K',
    description:
      'Full score + gap analysis + critical path to close',
  },
  {
    step: 4,
    name: 'Bond Readiness Accelerator',
    price: '$45K–$75K',
    description:
      'Evidence assembly, disclosure prep, underwriter coordination *',
  },
]

export default function HealthcareCFOLanding() {
  return (
    <div className="max-w-5xl mx-auto">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-muni-navy via-[#1B3A5C] to-indigo-900 rounded-2xl p-8 md:p-12 text-white mb-10">
        <div className="flex items-center gap-4 mb-5">
          <img
            src="/muni-pal-emblem.png"
            alt="Muni-Pal"
            className="h-14 w-14 rounded-xl object-contain"
            style={{ filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.3))' }}
          />
          <p className="text-sm font-semibold tracking-wide text-[#2DAEAC] uppercase">
            Healthcare Bond Intelligence
          </p>
        </div>
        <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold leading-tight max-w-3xl mb-4">
          You're planning a bond issuance. Here's what your advisors won't tell
          you for free.
        </h1>
        <p className="text-base md:text-lg text-gray-300 max-w-2xl mb-8">
          Muni-Pal's free Bond Readiness Assessment scores your facility across
          6 dimensions that drive bond outcomes — backed by benchmarks from 866
          actual EMMA transactions. Know where you stand, what it costs, and
          what to fix first.
        </p>
        <div className="flex flex-col sm:flex-row flex-wrap gap-4">
          <Link
            to="/tools/readiness"
            className="inline-flex items-center justify-center gap-2 bg-[#E8913A] hover:bg-[#d47e2e] text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            Take the Free Bond Readiness Assessment
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            to="/tools/market-intelligence"
            className="inline-flex items-center justify-center gap-2 bg-[#2DAEAC] hover:bg-[#259e9c] text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            Get Your Free Market Intelligence Report
            <ArrowRight className="h-4 w-4" />
          </Link>
          <Link
            to="/tools"
            className="inline-flex items-center justify-center gap-2 border border-white/30 hover:border-white/60 text-white font-medium px-6 py-3 rounded-lg transition-colors"
          >
            See the Bond Readiness Path
            <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      {/* 3-Point Value Proposition */}
      <section className="mb-12">
        <div className="grid gap-6 md:grid-cols-3">
          {VALUE_PROPS.map((prop) => (
            <div
              key={prop.headline}
              className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 hover:shadow-md transition-shadow"
            >
              <div className="h-10 w-10 rounded-lg bg-muni-navy flex items-center justify-center mb-4">
                <prop.icon className="h-5 w-5 text-[#2DAEAC]" />
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

      {/* Social Proof / Data Line */}
      <section className="mb-12 bg-gray-50 rounded-lg p-6 border border-gray-100">
        <div className="flex flex-wrap justify-center gap-8 text-center text-sm text-gray-600">
          <div>
            <span className="block text-2xl font-bold text-muni-navy">866</span>
            EMMA transactions analyzed
          </div>
          <div>
            <span className="block text-2xl font-bold text-muni-navy">
              3.20x
            </span>
            Median healthcare DSCR
            <span className="block text-[10px] text-gray-400">(gross revenue pledge basis)</span>
          </div>
          <div>
            <span className="block text-2xl font-bold text-muni-navy">10</span>
            Risk categories tracked
          </div>
          <div>
            <span className="block text-2xl font-bold text-muni-navy">
              1,318
            </span>
            Financial reports in corpus
          </div>
        </div>
      </section>

      {/* Bond Readiness Engagement Path */}
      <section id="engagement-path" className="mb-12 scroll-mt-8">
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          The Bond Readiness Path
        </h2>
        <p className="text-sm text-gray-600 mb-6 max-w-2xl">
          From free benchmarks to deal-ready in four steps. Start with the data
          — escalate only when you're confident in the opportunity.
        </p>
        <div className="grid gap-4 md:grid-cols-4">
          {ENGAGEMENT_PATH.map((step, i) => (
            <div
              key={step.name}
              className="relative bg-white rounded-lg border border-gray-200 shadow-sm p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center gap-2 mb-3">
                <span className="inline-flex items-center justify-center h-7 w-7 rounded-full bg-[#2DAEAC] text-white text-xs font-bold">
                  {step.step}
                </span>
                <span
                  className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    step.price === 'Free'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-[#E8913A]/10 text-[#E8913A]'
                  }`}
                >
                  {step.price}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-gray-900 mb-1">
                {step.name}
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                {step.description}
              </p>
              {i < ENGAGEMENT_PATH.length - 1 && (
                <ChevronRight className="hidden md:block absolute -right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-300 z-10" />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* MSRB G-42 Disclaimer */}
      <p className="text-[11px] text-gray-400 mt-3 max-w-3xl">
        * Bond Readiness Accelerator is an educational and analytical service. It does not constitute municipal advisory services as defined under Section 15B of the Securities Exchange Act.
      </p>

      {/* Cost of Inaction — ROI Callout */}
      <section className="mb-12 bg-gradient-to-r from-red-50 to-orange-50 rounded-lg border border-red-100 p-6 md:p-8">
        <div className="flex items-start gap-4">
          <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
            <TrendingUp className="h-5 w-5 text-red-600" />
          </div>
          <div>
            <h3 className="text-base font-bold text-gray-900 mb-2">
              The Cost of Inaction
            </h3>
            <p className="text-sm text-gray-700 leading-relaxed mb-3">
              The difference between an A-rated and BBB-rated issuance costs{' '}
              <span className="font-semibold text-red-700">$27M+</span> over 25
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
      </section>

      {/* When to Engage — Timeline */}
      <section className="mb-12">
        <h2 className="text-xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <Clock className="h-5 w-5 text-[#2DAEAC]" />
          When to Engage
        </h2>
        <p className="text-sm text-gray-600 mb-6 max-w-2xl">
          A typical healthcare bond transaction takes 5–8 months. Here's how the
          Bond Readiness Path maps to your deal timeline.
        </p>
        <div className="relative">
          <div className="absolute left-4 top-2 bottom-2 w-px bg-gray-200 hidden md:block" />
          <div className="space-y-4">
            {[
              {
                months: 'Month 1–2',
                label: 'Discovery',
                step: 'Bond Readiness Assessment + Market Intelligence Report',
                detail:
                  'Score your facility and benchmark against peers. Identify top gaps before engaging advisors.',
              },
              {
                months: 'Month 2–3',
                label: 'Diagnostic',
                step: 'Bond Readiness Diagnostic',
                detail:
                  'Full scoring, gap analysis, and critical path. Know exactly what underwriters will scrutinize.',
              },
              {
                months: 'Month 3–5',
                label: 'Preparation',
                step: 'Bond Readiness Accelerator',
                detail:
                  'Evidence assembly, disclosure prep, and underwriter coordination. Close documentation gaps.',
              },
              {
                months: 'Month 5–8',
                label: 'Execution',
                step: 'Market entry',
                detail:
                  'Go to market with a complete, defensible credit story. Advisors execute — you negotiate from strength.',
              },
            ].map((phase) => (
              <div
                key={phase.months}
                className="flex items-start gap-4 md:pl-10 relative"
              >
                <div className="absolute left-2.5 top-1.5 h-3 w-3 rounded-full bg-[#2DAEAC] border-2 border-white shadow hidden md:block" />
                <div className="min-w-[80px]">
                  <span className="text-xs font-semibold text-[#2DAEAC] uppercase">
                    {phase.months}
                  </span>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    {phase.label}{' '}
                    <span className="font-normal text-gray-500">
                      — {phase.step}
                    </span>
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {phase.detail}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Works With Your Advisors */}
      <section className="mb-12">
        <div className="bg-white rounded-lg border border-gray-200 p-6 md:p-8">
          <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-3">
            <Users className="h-6 w-6 text-[#2DAEAC]" />
            Works With Your Advisors, Not Against Them
          </h2>
          <p className="text-sm text-gray-700 leading-relaxed mb-3">
            Muni-Pal is independent due diligence — not a replacement for your
            financial advisor. We give you the benchmarks, risk analysis, and
            market context so you walk into advisor meetings asking better
            questions and validating recommendations with data.
          </p>
          <p className="text-sm text-gray-700 leading-relaxed">
            Your advisor brings deal execution. Muni-Pal brings evidence.
            Together, you get a stronger credit story and better terms.
          </p>
        </div>
      </section>

      {/* Secondary Trust-Building CTAs */}
      <section className="mb-12 grid gap-4 sm:grid-cols-2">
        <Link
          to="/tools/market-intelligence"
          className="flex items-start gap-4 bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow group"
        >
          <div className="h-10 w-10 rounded-lg bg-[#2DAEAC]/10 flex items-center justify-center flex-shrink-0">
            <FileText className="h-5 w-5 text-[#2DAEAC]" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900 group-hover:text-[#2DAEAC] transition-colors">
              View a Sample MIR Report
            </p>
            <p className="text-xs text-gray-500 mt-1">
              See the exact benchmarks, risk scoring, and pricing data a
              healthcare CFO receives — before you request your own.
            </p>
          </div>
        </Link>
        <Link
          to="/tools"
          className="flex items-start gap-4 bg-white rounded-lg border border-gray-200 p-5 hover:shadow-md transition-shadow group"
        >
          <div className="h-10 w-10 rounded-lg bg-muni-navy/10 flex items-center justify-center flex-shrink-0">
            <BarChart3 className="h-5 w-5 text-muni-navy" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900 group-hover:text-muni-navy transition-colors">
              Compare Risk Profiles by Rating Tier
            </p>
            <p className="text-xs text-gray-500 mt-1">
              How does your system's risk profile stack up against AA, A, and
              BBB-rated peers? See the gap analysis framework.
            </p>
          </div>
        </Link>
      </section>

      {/* Primary CTA Block */}
      <section className="mb-12 bg-muni-navy rounded-lg p-8 text-white text-center">
        <h2 className="text-xl font-bold mb-2">
          How Bond-Ready Is Your Facility?
        </h2>
        <p className="text-sm text-gray-300 mb-6 max-w-lg mx-auto">
          No login required. No sales call. Score your facility across 6
          dimensions in about 10 minutes — and see exactly what to fix first.
        </p>
        <Link
          to="/tools/readiness"
          className="inline-flex items-center gap-2 bg-[#E8913A] hover:bg-[#d47e2e] text-white font-semibold px-8 py-3 rounded-lg transition-colors"
        >
          Take the Free Readiness Assessment
          <ArrowRight className="h-4 w-4" />
        </Link>
      </section>

      {/* Audience Filter */}
      <section className="mb-10 bg-gray-50 rounded-lg border border-gray-100 p-6">
        <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Shield className="h-4 w-4 text-gray-400" />
          Who this is for — and who it isn't
        </h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs font-semibold text-green-700 mb-2 uppercase tracking-wide">
              Built for
            </p>
            <ul className="space-y-1.5 text-sm text-gray-600">
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                Healthcare CFOs and finance directors planning a bond issuance
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                Hospital systems evaluating capital structure options
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                Deals above $10M in total issuance size
              </li>
            </ul>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wide">
              Not designed for
            </p>
            <ul className="space-y-1.5 text-sm text-gray-400">
              <li className="flex items-start gap-2">
                <span className="mt-0.5 flex-shrink-0">—</span>
                Sub-$10M deal sizes
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 flex-shrink-0">—</span>
                Non-healthcare municipal issuers
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 flex-shrink-0">—</span>
                General financial advice seekers
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="flex items-center justify-center gap-2 text-xs text-gray-400 py-6 border-t border-gray-100">
        <img
          src="/muni-pal-emblem.png"
          alt="Muni-Pal"
          className="h-6 w-6 rounded object-contain opacity-60"
        />
        <p>Muni-Pal &mdash; A Launch Shop product. Built by Innovation Factory.</p>
      </footer>
    </div>
  )
}
