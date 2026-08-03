import { Link } from 'react-router-dom'
import { BarChart3, Calculator, ClipboardCheck, ArrowRight, Download, TrendingUp, Layers, Route } from 'lucide-react'
import { useSensing } from '../../contexts/SensingContext'

const tools = [
  {
    name: 'Bond Readiness Assessment',
    description:
      'Find out if your facility is bond-ready — free, about 10 minutes. Answer plain-English questions and get a scored action plan: your top gaps, what each one costs you, and what to fix first.',
    href: '/tools/readiness',
    icon: ClipboardCheck,
    color: 'bg-muni-gold',
    cta: 'Check my readiness',
    primary: true,
  },
  {
    name: 'Deal Benchmarks',
    description:
      'See what deals like yours actually cost. Enter your size, state, and expected rating, and compare against real municipal bond transactions — the spread you can expect (the premium over the benchmark rate), typical structures, and your closest peers.',
    href: '/tools/benchmark',
    icon: Calculator,
    color: 'bg-muni-teal',
    cta: 'Compare my deal',
  },
  {
    name: "Today's Borrowing Costs",
    description:
      'What each rating tier pays to borrow right now. Current tax-exempt yield curves and the all-in cost of a deal by credit level — built from the AAA benchmark curve and real observed trades.',
    href: '/tools/credit-spreads',
    icon: TrendingUp,
    color: 'bg-emerald-600',
    cta: "See today's costs",
  },
  {
    name: 'Cost-of-Issuance Benchmarks',
    description:
      "Every fee in a bond deal — and what's normal to pay. Cost of issuance (the fees to get a deal done) benchmarked against real healthcare deals, sized to your deal.",
    href: '/tools/coi-benchmarking',
    icon: Layers,
    color: 'bg-rose-600',
    cta: "See what's normal",
  },
  {
    name: 'Sector Market Report',
    description:
      'What good looks like in your sector — the financial profile, ratings, deal structures, and borrowing costs lenders expect, built from 866 real municipal bond transactions.',
    href: '/tools/market-intelligence',
    icon: BarChart3,
    color: 'bg-blue-500',
    cta: 'Read the report',
  },
  {
    name: 'Work With Us',
    description:
      'Thinking about a deeper engagement? See how a pilot works: what we check first, what you get, and where your registered advisor stays in charge.',
    href: '/tools/pilot-navigation',
    icon: Route,
    color: 'bg-indigo-600',
    cta: 'See how it works',
  },
]

export default function ToolsHub() {
  const sensing = useSensing()

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-10">
        <h1 className="text-2xl font-bold text-gray-900">Free Bond Tools</h1>
        <p className="mt-2 text-gray-600 max-w-2xl">
          Free tools that show you what municipal deals like yours actually
          look like — built from 866 real transactions in public disclosure
          filings. See what your sector pays, compare your deal, and find out
          if you're bond-ready before you sit down with anyone.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {tools.map((tool) => (
          <Link
            key={tool.name}
            to={tool.href}
            className={`group bg-white rounded-lg border shadow-sm p-6 hover:shadow-md transition-all ${
              tool.primary
                ? 'border-2 border-muni-gold hover:border-muni-gold'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-3 mb-4">
              <div
                className={`h-10 w-10 rounded-lg ${tool.color} flex items-center justify-center`}
              >
                <tool.icon className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900 group-hover:text-primary-600 transition-colors">
                {tool.name}
              </h2>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed mb-4">
              {tool.description}
            </p>
            <div className="flex items-center text-sm font-medium text-primary-600 opacity-0 group-hover:opacity-100 transition-opacity">
              {tool.cta} <ArrowRight className="h-4 w-4 ml-1" />
            </div>
          </Link>
        ))}
      </div>

      {/* Export Report CTA */}
      {sensing.completedCount > 0 && (
        <Link
          to="/tools/export"
          className="mt-6 flex items-center justify-between bg-white rounded-lg border-2 border-primary-200 shadow-sm p-5 hover:border-primary-400 transition-colors group"
        >
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-primary-500 flex items-center justify-center">
              <Download className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-gray-900">
                Download Your Combined Report
              </h2>
              <p className="text-sm text-gray-500">
                {sensing.completedCount} of 4 sections ready — get everything as one PDF, free
              </p>
            </div>
          </div>
          <ArrowRight className="h-5 w-5 text-primary-400 group-hover:text-primary-600 transition-colors" />
        </Link>
      )}

      <div className="mt-12 p-8 bg-muni-navy rounded-lg text-white">
        <h3 className="font-semibold text-lg mb-4">How it works</h3>
        <div className="flex flex-col md:flex-row gap-8 text-sm text-gray-300">
          <div className="flex-1">
            <span className="text-muni-teal font-semibold text-base">
              1. Explore
            </span>
            <p className="mt-2 leading-relaxed">
              See what good looks like in your sector — ratings, financials,
              and costs from real deals.
            </p>
          </div>
          <div className="flex-1">
            <span className="text-muni-teal font-semibold text-base">
              2. Compare
            </span>
            <p className="mt-2 leading-relaxed">
              Compare your specific deal against its closest real-world peers.
            </p>
          </div>
          <div className="flex-1">
            <span className="text-muni-teal font-semibold text-base">
              3. Assess
            </span>
            <p className="mt-2 leading-relaxed">
              Take the free readiness assessment and get a scored action plan
              — about 10 minutes.
            </p>
          </div>
          <div className="flex-1">
            <span className="text-muni-teal font-semibold text-base">
              4. Price
            </span>
            <p className="mt-2 leading-relaxed">
              See what borrowing costs today at your credit level — all fees
              included.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
