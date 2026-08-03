import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronLeft,
  Calculator,
  DollarSign,
  Sparkles,
  Building2,
  FileText,
  Shield,
  Users,
  BarChart3,
  Layers,
  TrendingUp,
} from 'lucide-react'

/* ------------------------------------------------------------------ */
/*  Tier definitions                                                   */
/* ------------------------------------------------------------------ */

interface TierFeature {
  name: string
  free: boolean | string
  subscription: boolean | string
  perProject: boolean | string
}

const FEATURES: TierFeature[] = [
  { name: 'Bond Readiness Assessment', free: true, subscription: true, perProject: true },
  { name: 'Market Intelligence Report', free: true, subscription: true, perProject: true },
  { name: 'COI Benchmarking Tool', free: true, subscription: true, perProject: true },
  { name: 'Credit Spread Monitor', free: true, subscription: true, perProject: true },
  { name: 'Project Dashboard', free: false, subscription: true, perProject: true },
  { name: 'Advanced Readiness Scoring (0-10)', free: false, subscription: true, perProject: true },
  { name: 'Full COI Benchmark Reports', free: false, subscription: true, perProject: true },
  { name: 'Bond Structuring Checklist', free: false, subscription: true, perProject: true },
  { name: 'Evidence Extraction (AI)', free: false, subscription: false, perProject: true },
  { name: 'Disclosure Management', free: false, subscription: false, perProject: true },
  { name: 'Information Request Workflows', free: false, subscription: false, perProject: true },
  { name: 'Deliverable Packs for Advisors', free: false, subscription: false, perProject: true },
  { name: 'Revenue Diversification Analysis', free: false, subscription: false, perProject: true },
  { name: 'Dedicated Support', free: false, subscription: false, perProject: true },
]

/* ------------------------------------------------------------------ */
/*  Per-project estimator config                                       */
/* ------------------------------------------------------------------ */

interface EstimatorFeature {
  id: string
  name: string
  description: string
  baseCost: number
  icon: typeof FileText
}

const ESTIMATOR_FEATURES: EstimatorFeature[] = [
  {
    id: 'diagnostic',
    name: 'Bond Readiness Diagnostic',
    description: 'Full readiness score, gap analysis, and critical path to close',
    baseCost: 15000,
    icon: BarChart3,
  },
  {
    id: 'coi-benchmark',
    name: 'COI Benchmarking & Negotiation Pack',
    description: 'Peer-compared cost-of-issuance analysis with negotiation data points',
    baseCost: 8000,
    icon: DollarSign,
  },
  {
    id: 'evidence',
    name: 'Evidence Extraction',
    description: 'AI-powered document parsing — financials, audits, board minutes',
    baseCost: 12000,
    icon: FileText,
  },
  {
    id: 'disclosure',
    name: 'Disclosure Management',
    description: 'Track and manage all continuing disclosure requirements',
    baseCost: 10000,
    icon: Shield,
  },
  {
    id: 'deal-coord',
    name: 'Deal Coordination',
    description: 'Active deal milestone tracking and advisor coordination',
    baseCost: 18000,
    icon: Users,
  },
  {
    id: 'deliverables',
    name: 'Deliverable Packs',
    description: 'Generate handoff deliverables for advisors and underwriters',
    baseCost: 8000,
    icon: Layers,
  },
  {
    id: 'revenue',
    name: 'Revenue Diversification Analysis',
    description: 'Revenue stream analysis and visualization for credit story',
    baseCost: 6000,
    icon: TrendingUp,
  },
]

type BondSize = '$5M–$15M' | '$15M–$35M' | '$35M–$75M' | '$75M–$100M'
type Complexity = 'standard' | 'moderate' | 'complex'

const BOND_SIZE_MULTIPLIER: Record<BondSize, number> = {
  '$5M–$15M': 0.85,
  '$15M–$35M': 1.0,
  '$35M–$75M': 1.15,
  '$75M–$100M': 1.3,
}

const COMPLEXITY_MULTIPLIER: Record<Complexity, number> = {
  standard: 1.0,
  moderate: 1.2,
  complex: 1.45,
}

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

/* Stripe price IDs — monthly and annual for the Subscription tier */
const STRIPE_PRICES = {
  monthly: import.meta.env.VITE_STRIPE_PRICE_MONTHLY ?? '',
  annual: import.meta.env.VITE_STRIPE_PRICE_ANNUAL ?? '',
} as const

const API_URL = ''  // Relative paths — Vercel/vite proxy rewrites to backend

async function startCheckout(priceId: string, accessToken: string | null) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (accessToken) headers['Authorization'] = `Bearer ${accessToken}`

  const res = await fetch(`${API_URL}/api/v1/stripe/create-checkout-session`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ price_id: priceId }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail ?? 'Failed to start checkout')
  }
  const { url } = await res.json()
  window.location.href = url
}

export default function PricingPage() {
  const [searchParams] = useSearchParams()
  const checkoutStatus = searchParams.get('checkout') // 'success' | 'cancel' | null
  const navigate = useNavigate()
  const { user, getAccessToken, isSubscribed } = useAuth()

  const [selectedFeatures, setSelectedFeatures] = useState<Set<string>>(new Set())
  const [bondSize, setBondSize] = useState<BondSize>('$15M–$35M')
  const [complexity, setComplexity] = useState<Complexity>('standard')
  const [checkoutLoading, setCheckoutLoading] = useState(false)
  const [checkoutError, setCheckoutError] = useState<string | null>(null)

  const handleSubscribe = async (priceId: string) => {
    if (!user) {
      navigate('/auth?mode=register&returnTo=/pricing')
      return
    }
    if (!priceId) return
    setCheckoutLoading(true)
    setCheckoutError(null)
    try {
      await startCheckout(priceId, getAccessToken())
    } catch (err: unknown) {
      setCheckoutError(err instanceof Error ? err.message : 'Checkout failed')
      setCheckoutLoading(false)
    }
  }

  const toggleFeature = (id: string) => {
    setSelectedFeatures((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAll = () => {
    setSelectedFeatures(new Set(ESTIMATOR_FEATURES.map((f) => f.id)))
  }

  const clearAll = () => setSelectedFeatures(new Set())

  const rawEstimate = ESTIMATOR_FEATURES.filter((f) => selectedFeatures.has(f.id)).reduce(
    (sum, f) => sum + f.baseCost,
    0,
  )
  const adjusted = Math.round(
    rawEstimate * BOND_SIZE_MULTIPLIER[bondSize] * COMPLEXITY_MULTIPLIER[complexity],
  )
  const estimateLow = Math.round(adjusted * 0.9)
  const estimateHigh = Math.round(adjusted * 1.1)

  const fmt = (n: number) =>
    n >= 1000 ? `$${Math.round(n / 1000)}K` : `$${n.toLocaleString()}`

  return (
    <div className="max-w-5xl mx-auto">
      {/* Back link */}
      <Link
        to="/"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-muni-navy mb-6 transition-colors"
      >
        <ChevronLeft className="h-4 w-4" />
        Back to Home
      </Link>

      {/* Header */}
      <section className="mb-10">
        <div className="flex items-center gap-3 mb-4">
          <img
            src="/muni-pal-emblem.png"
            alt="Muni-Pal"
            className="h-10 w-10 rounded-xl object-contain"
          />
          <p className="text-xs font-semibold tracking-wide text-muni-teal uppercase">
            Pricing &amp; Plans
          </p>
        </div>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">
          Choose the right level for your bond journey
        </h1>
        <p className="text-sm text-gray-600 max-w-2xl">
          Start free with sensing tools. Subscribe for ongoing readiness workspace access.
          Or scope a registered-advisor-review support engagement for pre-issuance preparation.
        </p>
      </section>

      {/* Checkout result banner */}
      {checkoutStatus === 'success' && (
        <div className="mb-6 rounded-lg border border-green-200 bg-green-50 px-5 py-3 text-sm text-green-800">
          <strong>Payment successful!</strong> Your subscription is now active. We&rsquo;ll send a confirmation email shortly.
        </div>
      )}
      {checkoutStatus === 'cancel' && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-5 py-3 text-sm text-amber-800">
          Checkout was cancelled. No charge was made. You can try again anytime.
        </div>
      )}
      {checkoutError && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-5 py-3 text-sm text-red-800">
          {checkoutError}
        </div>
      )}

      {/* ---------------------------------------------------------------- */}
      {/*  Tier cards                                                       */}
      {/* ---------------------------------------------------------------- */}
      <section className="mb-14">
        <div className="grid gap-6 md:grid-cols-3">
          {/* Free Tier */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 flex flex-col">
            <div className="h-10 w-10 rounded-lg bg-gray-100 flex items-center justify-center mb-4">
              <BarChart3 className="h-5 w-5 text-gray-500" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-1">Free</h3>
            <p className="text-2xl font-bold text-gray-900 mb-1">
              $0<span className="text-sm font-normal text-gray-400">/forever</span>
            </p>
            <p className="text-xs text-gray-500 mb-5">
              Sensing tools &mdash; no login required
            </p>
            <ul className="space-y-2 text-sm text-gray-600 mb-6 flex-1">
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" /> Bond Readiness Assessment</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" /> Market Intelligence Report</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" /> COI Benchmarking Tool</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" /> Credit Spread Monitor</li>
            </ul>
            <Link
              to="/tools"
              className="w-full text-center inline-flex items-center justify-center gap-2 border border-gray-300 hover:border-muni-navy text-gray-700 font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm"
            >
              Explore Free Tools
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          {/* Subscription Tier */}
          <div className="bg-white rounded-xl border-2 border-muni-teal shadow-md p-6 flex flex-col relative">
            <span className="absolute -top-3 left-6 bg-muni-teal text-white text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full">
              Most Popular
            </span>
            <div className="h-10 w-10 rounded-lg bg-muni-teal/10 flex items-center justify-center mb-4">
              <Sparkles className="h-5 w-5 text-muni-teal" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-1">Subscription</h3>
            <p className="text-2xl font-bold text-gray-900 mb-1">
              $499<span className="text-sm font-normal text-gray-400">/mo</span>
            </p>
            <p className="text-xs text-gray-500 mb-1">
              or $4,990/year (save 17%)
            </p>
            <p className="text-xs text-gray-400 mb-5">
              For organizations exploring bond issuance
            </p>
            <ul className="space-y-2 text-sm text-gray-600 mb-6 flex-1">
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-teal mt-0.5 flex-shrink-0" /> Everything in Free</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-teal mt-0.5 flex-shrink-0" /> Project Dashboard</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-teal mt-0.5 flex-shrink-0" /> Advanced Readiness Scoring</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-teal mt-0.5 flex-shrink-0" /> Full COI Benchmark Reports</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-teal mt-0.5 flex-shrink-0" /> Bond Structuring Checklist</li>
            </ul>
            {isSubscribed ? (
              <div className="w-full text-center inline-flex items-center justify-center gap-2 bg-green-100 text-green-700 font-semibold px-4 py-2.5 rounded-lg text-sm">
                <CheckCircle2 className="h-4 w-4" /> Active
              </div>
            ) : (
              <button
                onClick={() => handleSubscribe(STRIPE_PRICES.monthly)}
                disabled={checkoutLoading || !STRIPE_PRICES.monthly}
                className="w-full text-center inline-flex items-center justify-center gap-2 bg-muni-teal hover:bg-[#259e9c] text-white font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {checkoutLoading ? 'Redirecting...' : user ? 'Subscribe — $499/mo' : 'Create Account to Subscribe'}
                {!checkoutLoading && <ArrowRight className="h-4 w-4" />}
              </button>
            )}
          </div>

          {/* Per-Project Tier */}
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 flex flex-col">
            <div className="h-10 w-10 rounded-lg bg-muni-orange/10 flex items-center justify-center mb-4">
              <Building2 className="h-5 w-5 text-muni-orange" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-1">Per-Project</h3>
            <p className="text-2xl font-bold text-gray-900 mb-1">
              Custom<span className="text-sm font-normal text-gray-400"> quote</span>
            </p>
            <p className="text-xs text-gray-500 mb-5">
              Scoped to your deal &mdash; pay for what you need
            </p>
            <ul className="space-y-2 text-sm text-gray-600 mb-6 flex-1">
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-orange mt-0.5 flex-shrink-0" /> Everything in Subscription</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-orange mt-0.5 flex-shrink-0" /> Evidence Extraction (AI)</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-orange mt-0.5 flex-shrink-0" /> Disclosure Management</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-orange mt-0.5 flex-shrink-0" /> Deliverable Packs</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-orange mt-0.5 flex-shrink-0" /> Revenue Diversification</li>
              <li className="flex gap-2"><CheckCircle2 className="h-4 w-4 text-muni-orange mt-0.5 flex-shrink-0" /> Dedicated Support</li>
            </ul>
            <a
              href="#estimator"
              className="w-full text-center inline-flex items-center justify-center gap-2 bg-muni-orange hover:bg-[#d47e2e] text-white font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm"
            >
              Get Your Estimate
              <ArrowRight className="h-4 w-4" />
            </a>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- */}
      {/*  Feature comparison table                                        */}
      {/* ---------------------------------------------------------------- */}
      <section className="mb-14">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Full Feature Comparison</h2>
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700 w-1/2">Feature</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Free</th>
                  <th className="text-center py-3 px-4 font-semibold text-muni-teal">Subscription</th>
                  <th className="text-center py-3 px-4 font-semibold text-muni-orange">Per-Project</th>
                </tr>
              </thead>
              <tbody>
                {FEATURES.map((f, i) => (
                  <tr key={f.name} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                    <td className="py-2.5 px-4 text-gray-700">{f.name}</td>
                    {(['free', 'subscription', 'perProject'] as const).map((tier) => (
                      <td key={tier} className="py-2.5 px-4 text-center">
                        {f[tier] === true ? (
                          <Check className="h-4 w-4 text-green-500 mx-auto" />
                        ) : f[tier] === false ? (
                          <span className="text-gray-300">&mdash;</span>
                        ) : (
                          <span className="text-xs text-gray-600">{f[tier]}</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- */}
      {/*  Per-project estimator                                           */}
      {/* ---------------------------------------------------------------- */}
      <section id="estimator" className="mb-14 scroll-mt-8">
        <div className="flex items-center gap-3 mb-2">
          <Calculator className="h-6 w-6 text-muni-orange" />
          <h2 className="text-xl font-bold text-gray-900">Per-Project Estimator</h2>
        </div>
        <p className="text-sm text-gray-600 mb-6 max-w-2xl">
          Select the features you need, set your bond size and complexity, and
          get an indicative quote. Final pricing is confirmed after a scoping
          conversation.
        </p>

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Feature selection */}
          <div className="lg:col-span-2 bg-white rounded-xl border border-gray-200 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-700">Select Features</h3>
              <div className="flex gap-3 text-xs">
                <button onClick={selectAll} className="text-muni-teal hover:underline">Select all</button>
                <button onClick={clearAll} className="text-gray-400 hover:underline">Clear</button>
              </div>
            </div>
            <div className="space-y-3">
              {ESTIMATOR_FEATURES.map((feat) => {
                const selected = selectedFeatures.has(feat.id)
                return (
                  <button
                    key={feat.id}
                    onClick={() => toggleFeature(feat.id)}
                    className={`w-full text-left flex items-start gap-3 p-3 rounded-lg border transition-all ${
                      selected
                        ? 'border-muni-orange bg-muni-orange/5 shadow-sm'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div
                      className={`h-5 w-5 rounded border flex items-center justify-center flex-shrink-0 mt-0.5 transition-colors ${
                        selected
                          ? 'bg-muni-orange border-muni-orange'
                          : 'border-gray-300'
                      }`}
                    >
                      {selected && <Check className="h-3 w-3 text-white" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-gray-900">{feat.name}</span>
                        <span className="text-xs text-gray-400 flex-shrink-0">from {fmt(feat.baseCost)}</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-0.5">{feat.description}</p>
                    </div>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Quote panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 sticky top-8">
              <h3 className="text-sm font-semibold text-gray-700 mb-4">Your Estimate</h3>

              {/* Bond size */}
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Bond Size</label>
              <select
                value={bondSize}
                onChange={(e) => setBondSize(e.target.value as BondSize)}
                className="w-full mb-4 text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-muni-teal"
              >
                {(Object.keys(BOND_SIZE_MULTIPLIER) as BondSize[]).map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>

              {/* Complexity */}
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Deal Complexity</label>
              <select
                value={complexity}
                onChange={(e) => setComplexity(e.target.value as Complexity)}
                className="w-full mb-6 text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-muni-teal"
              >
                <option value="standard">Standard &mdash; straightforward revenue bond</option>
                <option value="moderate">Moderate &mdash; multi-series or refunding</option>
                <option value="complex">Complex &mdash; new-money + refunding, unusual structure</option>
              </select>

              {/* Estimate display */}
              <div className="border-t border-gray-100 pt-4 mb-4">
                <p className="text-xs text-gray-500 mb-1">
                  {selectedFeatures.size} feature{selectedFeatures.size !== 1 ? 's' : ''} selected
                </p>
                {selectedFeatures.size === 0 ? (
                  <p className="text-lg font-bold text-gray-300">Select features above</p>
                ) : (
                  <>
                    <p className="text-2xl font-bold text-muni-navy">
                      {fmt(estimateLow)} &ndash; {fmt(estimateHigh)}
                    </p>
                    <p className="text-[10px] text-gray-400 mt-1">
                      Indicative range. Final pricing confirmed after scoping call.
                    </p>
                  </>
                )}
              </div>

              {/* CTA */}
              <Link
                to="/tools/readiness"
                className="w-full text-center inline-flex items-center justify-center gap-2 bg-muni-navy hover:bg-[#15304d] text-white font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm"
              >
                Start with Free Assessment
                <ArrowRight className="h-4 w-4" />
              </Link>
              <p className="text-[10px] text-gray-400 mt-2 text-center">
                We'll reach out to discuss your project scope
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ROI context */}
      <section className="mb-12 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border border-green-100 p-6 md:p-8">
        <h3 className="text-base font-bold text-gray-900 mb-2 flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-green-600" />
          Why This Pays for Itself
        </h3>
        <p className="text-sm text-gray-700 leading-relaxed mb-3">
          Repeat issuers who benchmark costs save <span className="font-semibold text-green-700">$150K&ndash;$500K</span> on
          a $100M deal through better underwriter negotiation alone. A one-tier
          rating improvement saves <span className="font-semibold text-green-700">$27M+</span> over 25 years. The
          Per-Project engagement typically costs less than <span className="font-semibold">0.1%</span> of deal size.
        </p>
        <p className="text-xs text-gray-500">
          Based on observed cost-of-issuance and spread differentials in public healthcare revenue bond disclosures.
        </p>
      </section>

      {/* FAQ */}
      <section className="mb-12">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Frequently Asked Questions</h2>
        <div className="space-y-4">
          {[
            {
              q: 'Can I start free and upgrade later?',
              a: 'Yes. Start with the free sensing tools today. When you\'re ready for deeper analysis, subscribe or request a per-project quote — your readiness data carries over.',
            },
            {
              q: 'What\'s included in the subscription vs. per-project?',
              a: 'The subscription gives you ongoing access to advisory dashboards, advanced scoring, and benchmark reports. Per-project adds hands-on deal support: evidence extraction, disclosure management, deliverable packs, and dedicated support scoped to your specific issuance.',
            },
            {
              q: 'How is per-project pricing determined?',
              a: 'The estimator above gives an indicative range. Final pricing is based on bond size, deal complexity, number of features selected, and level of advisory involvement. We\'ll confirm pricing after a brief scoping call.',
            },
            {
              q: 'Is this a replacement for a financial advisor?',
              a: 'No. Muni-Pal is independent due diligence — benchmarks, risk analysis, and preparation tools. Your financial advisor executes the deal. We help you walk in better prepared.',
            },
            {
              q: 'What deal sizes do you support?',
              a: 'We\'re built for healthcare bond issuances in the $5M–$100M range. This covers the vast majority of FQHC, community hospital, and senior living facility bond transactions.',
            },
          ].map((item) => (
            <details key={item.q} className="bg-white rounded-lg border border-gray-200 group">
              <summary className="cursor-pointer px-5 py-3 text-sm font-semibold text-gray-900 flex items-center justify-between">
                {item.q}
                <ChevronLeft className="h-4 w-4 text-gray-400 -rotate-90 group-open:rotate-90 transition-transform" />
              </summary>
              <p className="px-5 pb-4 text-sm text-gray-600 leading-relaxed">{item.a}</p>
            </details>
          ))}
        </div>
      </section>

      {/* Disclaimer */}
      <p className="text-[11px] text-gray-400 mb-8 max-w-3xl">
        Pricing shown is indicative and subject to final scoping. Muni-Pal provides benchmarking,
        preparation, and analytical tools — not investment advice, not municipal advisory advice,
        and not a pricing, sizing, issuance, or deal-execution recommendation. Registered advisors,
        counsel, underwriters, issuers, and borrowers retain their professional roles.
      </p>

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
