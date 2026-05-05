import { Link } from 'react-router-dom'
import { BarChart3, Calculator, ClipboardCheck, ArrowRight, Download, TrendingUp, Layers, Route } from 'lucide-react'
import { useSensing } from '../../contexts/SensingContext'

const tools = [
  {
    name: 'Market Intelligence',
    description:
      'Comprehensive sector benchmark report covering deal structures, ratings, financial metrics, risk factors, and secondary market activity.',
    href: '/tools/market-intelligence',
    icon: BarChart3,
    color: 'bg-blue-500',
  },
  {
    name: 'Benchmarking Calculator',
    description:
      'Compare your prospective issuance against sector peers. Get spread estimates, structural norms, and risk context.',
    href: '/tools/benchmark',
    icon: Calculator,
    color: 'bg-muni-teal',
  },
  {
    name: 'Readiness Assessment',
    description:
      'Healthcare sub-sector scoring (Hospital, Senior Living, FQHC) with 177-item assessment, COI gap estimates, and timeline compression analysis.',
    href: '/tools/readiness',
    icon: ClipboardCheck,
    color: 'bg-muni-gold',
  },
  {
    name: 'COI Benchmarking',
    description:
      'Line-item cost-of-issuance comparison across healthcare sub-sectors. See COI impact, lead times, and agent displacement value per item.',
    href: '/tools/coi-benchmarking',
    icon: Layers,
    color: 'bg-rose-600',
  },
  {
    name: 'Credit Spread Monitor',
    description:
      'Live yield curves, all-in cost of capital grid, and issuer channel comparison. Powered by AAA MMD base curve and EMMA corpus spreads.',
    href: '/tools/credit-spreads',
    icon: TrendingUp,
    color: 'bg-emerald-600',
  },
  {
    name: 'Pilot Navigation',
    description:
      'Lead capture to pilot qualification path, BFMS project creation gate, pre-pilot checks, and advisor-safe handoff boundaries.',
    href: '/tools/pilot-navigation',
    icon: Route,
    color: 'bg-indigo-600',
  },
]

export default function ToolsHub() {
  const sensing = useSensing()

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-10">
        <h1 className="text-2xl font-bold text-gray-900">Sensing Tools</h1>
        <p className="mt-2 text-gray-600 max-w-2xl">
          Data-driven tools powered by the EMMA municipal bond corpus. Analyze
          sector benchmarks, compare your issuance, and assess your bond
          readiness.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {tools.map((tool) => (
          <Link
            key={tool.name}
            to={tool.href}
            className="group bg-white rounded-lg border border-gray-200 shadow-sm p-6 hover:shadow-md hover:border-gray-300 transition-all"
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
              Open tool <ArrowRight className="h-4 w-4 ml-1" />
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
                Export Combined Report
              </h2>
              <p className="text-sm text-gray-500">
                {sensing.completedCount} of 4 sections ready — download as PDF
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
              Review sector benchmarks from the Market Intelligence report.
            </p>
          </div>
          <div className="flex-1">
            <span className="text-muni-teal font-semibold text-base">
              2. Compare
            </span>
            <p className="mt-2 leading-relaxed">
              Benchmark your specific issuance against corpus peers.
            </p>
          </div>
          <div className="flex-1">
            <span className="text-muni-teal font-semibold text-base">
              3. Assess
            </span>
            <p className="mt-2 leading-relaxed">
              Complete the readiness assessment for a scored action plan.
            </p>
          </div>
          <div className="flex-1">
            <span className="text-muni-teal font-semibold text-base">
              4. Price
            </span>
            <p className="mt-2 leading-relaxed">
              View live credit spreads and all-in cost of capital by issuer channel.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
