import { Link } from 'react-router-dom'
import {
  BarChart3,
  Shield,
  DollarSign,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
} from 'lucide-react'

const VALUE_PROPS = [
  {
    icon: BarChart3,
    headline: 'Know what "good" looks like',
    copy: 'See the exact DSCR, payer mix, days cash on hand, and pledge structures that separate AA-rated healthcare systems from BBB — drawn from real EMMA data, not industry averages.',
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
    price: '$15K–$25K',
    description:
      'Full score + gap analysis + critical path to close',
  },
  {
    step: 4,
    name: 'Bond Readiness Accelerator',
    price: '$45K–$75K',
    description:
      'Evidence assembly, disclosure prep, underwriter coordination',
  },
]

export default function HealthcareCFOLanding() {
  return (
    <div className="max-w-5xl mx-auto">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-muni-navy via-[#1B3A5C] to-indigo-900 rounded-2xl p-8 md:p-12 text-white mb-10">
        <p className="text-sm font-semibold tracking-wide text-[#2DAEAC] uppercase mb-4">
          Healthcare Bond Intelligence
        </p>
        <h1 className="text-2xl md:text-3xl lg:text-4xl font-bold leading-tight max-w-3xl mb-4">
          You're planning a bond issuance. Here's what your advisors won't tell
          you for free.
        </h1>
        <p className="text-base md:text-lg text-gray-300 max-w-2xl mb-8">
          Muni-Pal's Healthcare Market Intelligence Report benchmarks your deal
          against 866 actual EMMA transactions — so you walk into the room
          knowing what top-performing credits look like, what borrowing actually
          costs, and where risk disclosures go wrong.
        </p>
        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            to="/tools/market-intelligence"
            className="inline-flex items-center justify-center gap-2 bg-[#E8913A] hover:bg-[#d47e2e] text-white font-semibold px-6 py-3 rounded-lg transition-colors"
          >
            Get Your Free Market Intelligence Report
            <ArrowRight className="h-4 w-4" />
          </Link>
          <a
            href="#engagement-path"
            className="inline-flex items-center justify-center gap-2 border border-white/30 hover:border-white/60 text-white font-medium px-6 py-3 rounded-lg transition-colors"
          >
            See the Bond Readiness Path
            <ChevronRight className="h-4 w-4" />
          </a>
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
          </div>
          <div>
            <span className="block text-2xl font-bold text-muni-navy">5</span>
            Risk categories scored
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

      {/* Primary CTA Block */}
      <section className="mb-12 bg-muni-navy rounded-lg p-8 text-white text-center">
        <h2 className="text-xl font-bold mb-2">
          Get Your Free Market Intelligence Report
        </h2>
        <p className="text-sm text-gray-300 mb-6 max-w-lg mx-auto">
          No login required. No sales call. Just the data your advisors charge
          $25K to compile.
        </p>
        <Link
          to="/tools/market-intelligence"
          className="inline-flex items-center gap-2 bg-[#E8913A] hover:bg-[#d47e2e] text-white font-semibold px-8 py-3 rounded-lg transition-colors"
        >
          Start Now — It's Free
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
      <footer className="text-center text-xs text-gray-400 py-6 border-t border-gray-100">
        <p>Muni-Pal &mdash; A Launch Shop product. Built by Innovation Factory.</p>
      </footer>
    </div>
  )
}
