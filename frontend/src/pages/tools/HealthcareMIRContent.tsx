/**
 * Healthcare Market Intelligence Report — narrative content sections.
 *
 * Sourced from the Bond Strategist's MIR document (LAU-31).
 * Renders educational copy alongside the data-driven sections
 * in the Market Intelligence module when sector === 'healthcare'.
 */

/* ---------- Section 1: Information Gap ---------- */

export function InformationGap() {
  return (
    <div className="bg-gradient-to-br from-muni-navy to-indigo-900 rounded-lg p-6 text-white">
      <h2 className="text-lg font-semibold mb-3">
        The Information Gap You're Walking Into
      </h2>
      <p className="text-sm text-gray-300 mb-4">
        Every Healthcare Director and Finance Director planning a bond issuance
        faces the same structural disadvantage: your advisors have closed
        hundreds of deals and know exactly what investors require. You may be
        doing this for the first time, or for the first time in a decade.
      </p>
      <p className="text-sm text-gray-300 mb-3">
        This report closes that gap. Three things it tells you that no advisor
        gives you for free:
      </p>
      <ul className="space-y-2 text-sm text-gray-300">
        <li className="flex gap-2">
          <span className="text-muni-teal flex-shrink-0 font-bold">1.</span>
          <span>
            <strong className="text-white">
              What the best-performing healthcare credits look like
            </strong>{' '}
            — the specific financial profile, pledge structure, and strategic
            characteristics that separate AA-rated systems from BBB-rated ones,
            drawn from 866 actual EMMA deals
          </span>
        </li>
        <li className="flex gap-2">
          <span className="text-muni-teal flex-shrink-0 font-bold">2.</span>
          <span>
            <strong className="text-white">
              What borrowing actually costs right now
            </strong>{' '}
            — corpus-calibrated TIC estimates by rating tier, not a vague
            "market rate" answer
          </span>
        </li>
        <li className="flex gap-2">
          <span className="text-muni-teal flex-shrink-0 font-bold">3.</span>
          <span>
            <strong className="text-white">
              Where the risk disclosures go wrong
            </strong>{' '}
            — the 5 risk categories healthcare issuers consistently fail to
            adequately mitigate, and what the upgraded credits did differently
          </span>
        </li>
      </ul>
      <p className="text-xs text-gray-400 mt-4 border-t border-white/10 pt-3">
        All benchmarks are empirical — sourced from 866 EMMA official
        statements, 1,318 financial reports, and 239 rating agency actions.
      </p>
    </div>
  )
}

/* ---------- Section 3: Pareto Analysis ---------- */

const BEST_PERFORMER_TRAITS = [
  {
    title: 'Strong and diversified market position',
    detail:
      'Defensible competitive position: trauma designation, academic affiliation, subspecialty depth, or system scale across a multi-county region.',
    examples: 'AdventHealth (FL), Texas Children\'s Hospital (TX)',
  },
  {
    title: 'Low Medicaid/Medicare concentration (< 55% combined)',
    detail:
      'Payer mix is the most powerful predictor of credit stability. Best performers show commercial payer mix > 35%.',
    examples: null,
  },
  {
    title: 'Solid health plan/insurance integration',
    detail:
      'Systems that own or operate a health insurance plan show materially more stable cash flow. Premium revenue hedges against volume variability.',
    examples: null,
  },
  {
    title: 'Days Cash on Hand > 200 days',
    detail:
      'Corpus median: 202 days. Best performers above 250 days. Below 150 days = credit concern. Below 100 days = likely requires credit enhancement.',
    examples: null,
  },
  {
    title: 'Strategic capital plan with funded reserves',
    detail:
      'Capital plan funded from operations + bond proceeds, with DCOH remaining above 150 days post-project.',
    examples: null,
  },
  {
    title: 'Experienced, stable management team',
    detail:
      'Explicitly cited in upgrade language. High CFO turnover is a negative signal for rating analysts.',
    examples: null,
  },
  {
    title: 'First-lien gross revenue pledge',
    detail:
      '69% of corpus uses gross revenue pledge. 60% have first lien. Best performers lock in both for broadest security basis.',
    examples: null,
  },
]

const WORST_PERFORMER_SIGNS: [string, string, string][] = [
  [
    'High age of plant (> 16 years) without capital plan',
    'Deferred maintenance, outdated facilities',
    '"Relatively high age of plant" + no funded replacement plan',
  ],
  [
    'Days cash declining over 3 consecutive periods',
    'Operating cash flow negative or thin',
    '"Days cash and cash to debt tempered relative to historic levels"',
  ],
  [
    'Government payer concentration > 65%',
    'Majority of revenue at CMS rate risk',
    'Downgrade trigger when CMS cuts reimbursement',
  ],
  [
    'Highly competitive market + no differentiation',
    'Losing market share to regional/outpatient competitors',
    '"Highly competitive market" + declining inpatient volume',
  ],
  [
    'Staffing crisis exposure',
    'Travel nurse dependency, wage inflation > revenue growth',
    '"Unprecedented staffing shortages" + margin compression',
  ],
  [
    'Capital commitment without liquidity coverage',
    'Bond proceeds spent; operating reserves insufficient',
    'DCOH < 100 days post-project',
  ],
]

export function ParetoAnalysis() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="px-5 py-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900 text-base">
          Pareto Analysis: What Best Performers Look Like
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          The 20% of deal characteristics that explain 80% of the credit outcome
          difference between upgraded and downgraded healthcare bonds.
        </p>
      </div>
      <div className="px-5 pb-5 pt-4">
        {/* Best Performers */}
        <h4 className="text-sm font-semibold text-green-700 mb-3 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-green-500" />
          Best Performer Profile (Top Quartile: DSCR &gt; 7.21x, Ratings
          Aa1–A1)
        </h4>
        <div className="space-y-3 mb-6">
          {BEST_PERFORMER_TRAITS.map((trait, i) => (
            <div
              key={i}
              className="bg-green-50 rounded-lg p-3 border border-green-100"
            >
              <div className="flex items-start gap-2">
                <span className="text-green-600 font-bold text-sm flex-shrink-0">
                  {i + 1}.
                </span>
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {trait.title}
                  </div>
                  <p className="text-xs text-gray-600 mt-1">{trait.detail}</p>
                  {trait.examples && (
                    <p className="text-xs text-gray-500 mt-1 italic">
                      Examples: {trait.examples}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Worst Performers */}
        <h4 className="text-sm font-semibold text-amber-700 mb-3 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          Warning Signs (Bottom Quartile: DSCR &lt; 3.90x, BBB or below)
        </h4>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2.5 px-3 font-medium text-gray-600">
                  Warning Sign
                </th>
                <th className="text-left py-2.5 px-3 font-medium text-gray-600">
                  What It Looks Like
                </th>
                <th className="text-left py-2.5 px-3 font-medium text-gray-600">
                  What Rating Analysts See
                </th>
              </tr>
            </thead>
            <tbody>
              {WORST_PERFORMER_SIGNS.map(([sign, looks, sees], i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="py-2.5 px-3 text-gray-800 font-medium">
                    {sign}
                  </td>
                  <td className="py-2.5 px-3 text-gray-600">{looks}</td>
                  <td className="py-2.5 px-3 text-gray-500 italic">{sees}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="mt-4 bg-gray-50 rounded-lg p-3 border border-gray-200">
          <p className="text-sm text-gray-700">
            <strong>The critical insight:</strong> The difference between best
            and worst performers is not size, geography, or subspecialty. It is{' '}
            <strong>
              whether the organization demonstrates financial resilience while
              executing its capital plan.
            </strong>{' '}
            Rating agencies score a forward-looking capacity question: can this
            system service its debt while continuing to invest in its competitive
            position?
          </p>
        </div>
      </div>
    </div>
  )
}

/* ---------- Section 5: Risk Profile & Cybersecurity ---------- */

const RISK_CATEGORIES: {
  category: string
  factors: number
  pctTotal: string
  mitigationRate: string
  interpretation: string
}[] = [
  { category: 'Financial', factors: 39, pctTotal: '25.0%', mitigationRate: '23%', interpretation: 'Revenue/margin/payer mix risk — partially manageable' },
  { category: 'Regulatory', factors: 31, pctTotal: '19.9%', mitigationRate: '39%', interpretation: 'CMS/CON/state licensing — can be partially documented' },
  { category: 'Supply Chain', factors: 20, pctTotal: '12.8%', mitigationRate: '60%', interpretation: 'Pharmaceutical, medical supply — well-mitigated' },
  { category: 'Construction', factors: 20, pctTotal: '12.8%', mitigationRate: '70%', interpretation: 'Capital projects — well-mitigated via EPC/bonds' },
  { category: 'Market Demand', factors: 13, pctTotal: '8.3%', mitigationRate: '38%', interpretation: 'Patient volume, competition — limited mitigation' },
  { category: 'Cybersecurity', factors: 10, pctTotal: '6.4%', mitigationRate: '50%', interpretation: 'EHR/ransomware risk — sector-specific' },
  { category: 'Technology (Health IT)', factors: 10, pctTotal: '6.4%', mitigationRate: '100%', interpretation: 'EHR implementations — fully mitigated in corpus' },
  { category: 'Management', factors: 8, pctTotal: '5.1%', mitigationRate: '62%', interpretation: 'Leadership stability — partially mitigated' },
]

export function RiskProfileNarrative() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="px-5 py-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900 text-base">
          Healthcare Risk Profile — Where Disclosures Go Wrong
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          Based on 156 risk factors across 11 issuances with risk disclosures.
          Overall mitigation rate: 46% (vs. 23% for WTE).
        </p>
      </div>
      <div className="px-5 pb-5 pt-4 space-y-5">
        {/* Risk Category Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2.5 px-3 font-medium text-gray-600">Category</th>
                <th className="text-right py-2.5 px-3 font-medium text-gray-600"># Factors</th>
                <th className="text-right py-2.5 px-3 font-medium text-gray-600">% Total</th>
                <th className="text-right py-2.5 px-3 font-medium text-gray-600">Mitigation</th>
                <th className="text-left py-2.5 px-3 font-medium text-gray-600">Interpretation</th>
              </tr>
            </thead>
            <tbody>
              {RISK_CATEGORIES.map((r) => (
                <tr key={r.category} className="border-b border-gray-100">
                  <td className="py-2.5 px-3 text-gray-800 font-medium">{r.category}</td>
                  <td className="py-2.5 px-3 text-gray-600 text-right">{r.factors}</td>
                  <td className="py-2.5 px-3 text-gray-600 text-right">{r.pctTotal}</td>
                  <td className="py-2.5 px-3 text-right">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      parseInt(r.mitigationRate) >= 60
                        ? 'bg-green-100 text-green-700'
                        : parseInt(r.mitigationRate) >= 35
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-red-100 text-red-700'
                    }`}>
                      {r.mitigationRate}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-gray-500 text-sm">{r.interpretation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Cybersecurity Callout */}
        <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
          <h4 className="text-sm font-semibold text-amber-900 mb-2 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            Cybersecurity — A Bond Documentation Risk
          </h4>
          <p className="text-sm text-amber-800 mb-3">
            Cybersecurity appears in 10 of 156 risk factors — with 50% mitigation.
            A ransomware event that disrupts billing and cash collections for
            30–90 days can materially reduce DCOH immediately before a rating
            agency review.
          </p>
          <div className="text-sm text-amber-800">
            <p className="font-medium mb-1">Rating agencies expect:</p>
            <ul className="space-y-1 ml-4 text-amber-700">
              <li className="flex gap-2">
                <span className="text-amber-500 flex-shrink-0">-</span>
                Documented cyber insurance coverage ($25M+ for systems &gt; $500M revenue)
              </li>
              <li className="flex gap-2">
                <span className="text-amber-500 flex-shrink-0">-</span>
                Incident response plan
              </li>
              <li className="flex gap-2">
                <span className="text-amber-500 flex-shrink-0">-</span>
                Annual third-party security assessment
              </li>
              <li className="flex gap-2">
                <span className="text-amber-500 flex-shrink-0">-</span>
                Business continuity plan specific to EHR downtime
              </li>
            </ul>
          </div>
          <p className="text-xs text-amber-600 mt-3 italic">
            If your bond transaction is within 12 months, your IR plan and cyber
            insurance documentation should be current and board-approved.
          </p>
        </div>
      </div>
    </div>
  )
}

/* ---------- Section 7: Bond Structure Norms ---------- */

const STRUCTURE_NORMS: { element: string; standard: string; guidance: string }[] = [
  { element: 'Revenue pledge', standard: 'Gross revenue (69% of corpus)', guidance: 'Pledge gross revenues of the obligated group, not net' },
  { element: 'Lien position', standard: 'First lien (60% of corpus)', guidance: 'First lien unless existing senior debt precludes it' },
  { element: 'Coverage covenant', standard: '1.10x (median)', guidance: 'Set at 1.10x in documents; operate above 1.25x' },
  { element: 'DSRF', standard: '31.6% of deals use it', guidance: 'Required for BBB; optional for A+ with strong DCOH' },
  { element: 'Credit enhancement', standard: 'LOC (4 deals), bond insurance (2)', guidance: 'LOC-backed variable rate for sub-100-day DCOH' },
]

const TIMELINE_PHASES: { phase: string; duration: string; milestones: string }[] = [
  { phase: 'Bond readiness preparation', duration: '4–8 weeks', milestones: 'Financial benchmarking, legal authorization, OS framework' },
  { phase: 'Counsel and underwriter engagement', duration: '2–4 weeks', milestones: 'Bond counsel RFP, underwriter selection' },
  { phase: 'Document preparation', duration: '8–12 weeks', milestones: 'POS drafting, financial appendix, ratings preparation' },
  { phase: 'Rating agency process', duration: '4–6 weeks', milestones: 'Submission, call, rating assignment' },
  { phase: 'Marketing and pricing', duration: '1–2 weeks', milestones: 'Roadshow, book-building, pricing day' },
  { phase: 'Closing', duration: '1–2 weeks', milestones: 'Legal opinions, funding' },
]

export function BondStructureNorms() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="px-5 py-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900 text-base">
          Bond Structure Norms — What Market-Standard Healthcare Deals Look Like
        </h3>
      </div>
      <div className="px-5 pb-5 pt-4 space-y-5">
        {/* Security Package */}
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-2">
            Security Package
          </h4>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2.5 px-3 font-medium text-gray-600">Element</th>
                  <th className="text-left py-2.5 px-3 font-medium text-gray-600">Market Standard</th>
                  <th className="text-left py-2.5 px-3 font-medium text-gray-600">Your Deal Should...</th>
                </tr>
              </thead>
              <tbody>
                {STRUCTURE_NORMS.map((n) => (
                  <tr key={n.element} className="border-b border-gray-100">
                    <td className="py-2.5 px-3 text-gray-800 font-medium">{n.element}</td>
                    <td className="py-2.5 px-3 text-gray-600">{n.standard}</td>
                    <td className="py-2.5 px-3 text-gray-700">{n.guidance}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Obligated Group */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">
            Obligated Group Structure
          </h4>
          <p className="text-xs text-gray-600 mb-3">
            The obligated group defines which entities' finances back the bonds.
            This is a negotiated decision with bond counsel that materially affects
            the rating and investor perception.
          </p>
          <div className="space-y-2">
            {[
              { type: 'System obligated group', desc: 'All owned hospitals and affiliates — broadest backing, strongest security' },
              { type: 'Lead obligated group', desc: 'Primary hospital(s) only — acceptable if lead is >75% of system revenue' },
              { type: 'Single-entity', desc: 'Community hospital bond — weakest security base, requires strongest standalone financials' },
            ].map((og) => (
              <div key={og.type} className="flex gap-2 text-sm">
                <span className="text-gray-400 flex-shrink-0">-</span>
                <div>
                  <span className="font-medium text-gray-800">{og.type}:</span>{' '}
                  <span className="text-gray-600">{og.desc}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Transaction Timeline */}
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-2">
            Typical Transaction Timeline (5–8 months total)
          </h4>
          <div className="space-y-2">
            {TIMELINE_PHASES.map((p, i) => (
              <div key={i} className="flex items-center gap-3 bg-blue-50/50 rounded-lg p-2.5 border border-blue-100/50">
                <span className="text-blue-600 font-bold text-xs w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-800">{p.phase}</div>
                  <div className="text-xs text-gray-500">{p.milestones}</div>
                </div>
                <span className="text-xs font-semibold text-blue-700 bg-blue-100 px-2 py-0.5 rounded flex-shrink-0">
                  {p.duration}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

/* ---------- Section 8: Regulatory Framework ---------- */

export function RegulatoryFramework() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="px-5 py-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900 text-base">
          Regulatory Framework — Healthcare-Specific Legal Requirements
        </h3>
      </div>
      <div className="px-5 pb-5 pt-4 space-y-5">
        {/* CON */}
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <h4 className="text-sm font-semibold text-red-900 mb-2 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500" />
            Certificate of Need (CON) — Binary Gate
          </h4>
          <p className="text-sm text-red-800 mb-2">
            For expansion projects in CON states (~35 states): CON approval is a
            binary gate. Bond counsel cannot issue a tax opinion for a project
            requiring CON until CON is approved.
          </p>
          <p className="text-sm text-red-700 font-medium">
            Starting document preparation before CON approval is wasted spend.
            CON timeline varies by state: 60 days (fast-track) to 18+ months
            (contested).
          </p>
          <p className="text-xs text-red-600 mt-2 italic">
            Before you engage bond counsel, confirm CON status in writing from
            your legal team. Any advisor who begins drafting an OS before CON
            approval is running up hours on work that cannot be used.
          </p>
        </div>

        {/* CMS Reimbursement */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">
            CMS Reimbursement Risk Disclosure
          </h4>
          <p className="text-sm text-gray-700 mb-2">
            All healthcare bonds must disclose CMS reimbursement risk under SEC
            Rule 15c2-12. The OS must include:
          </p>
          <ul className="space-y-1 ml-4 text-sm text-gray-600">
            <li className="flex gap-2">
              <span className="text-gray-400 flex-shrink-0">-</span>
              Current Medicare and Medicaid payer mix percentages
            </li>
            <li className="flex gap-2">
              <span className="text-gray-400 flex-shrink-0">-</span>
              Trend analysis of government reimbursement rate changes (3–5 years)
            </li>
            <li className="flex gap-2">
              <span className="text-gray-400 flex-shrink-0">-</span>
              Impact analysis of pending CMS rule changes
            </li>
            <li className="flex gap-2">
              <span className="text-gray-400 flex-shrink-0">-</span>
              Mitigation discussion through commercial payer mix diversification
            </li>
          </ul>
        </div>

        {/* Tax-Exempt Eligibility */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">
            Tax-Exempt Eligibility
          </h4>
          <p className="text-sm text-gray-700">
            Healthcare revenue bonds qualify as hospital bonds under IRC 145
            (501(c)(3) borrowers) or as conduit bonds under state health
            facilities authority statutes. Key requirement:{' '}
            <strong>
              501(c)(3) determination letter must be current
            </strong>{' '}
            — organizations that have changed their corporate structure must
            confirm continued qualification.
          </p>
        </div>

        {/* Post-Issuance Compliance */}
        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900 mb-2">
            Post-Issuance Compliance
          </h4>
          <ul className="space-y-1.5 text-sm text-gray-700">
            <li className="flex gap-2">
              <span className="text-gray-400 flex-shrink-0">-</span>
              <span>
                <strong>Continuing disclosure (SEC 15c2-12):</strong> Annual
                financial report + material event notices filed with EMMA
              </span>
            </li>
            <li className="flex gap-2">
              <span className="text-gray-400 flex-shrink-0">-</span>
              <span>
                <strong>IRS arbitrage rebate:</strong> Calculated every 5 years;
                investment above bond yield must be rebated to Treasury
              </span>
            </li>
            <li className="flex gap-2">
              <span className="text-gray-400 flex-shrink-0">-</span>
              <span>
                <strong>Expenditure deadlines:</strong> Proceeds must be spent
                within IRS timelines (typically 3 years)
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

/* ---------- Section 6: Pricing Grid ---------- */

const YIELD_CURVE: { rating: string; y5: string; y10: string; y15: string; y20: string; y25: string; y30: string }[] = [
  { rating: 'AAA', y5: '3.35%', y10: '3.85%', y15: '4.15%', y20: '4.35%', y25: '4.42%', y30: '4.45%' },
  { rating: 'AA',  y5: '3.55%', y10: '4.05%', y15: '4.35%', y20: '4.55%', y25: '4.62%', y30: '4.65%' },
  { rating: 'A',   y5: '3.97%', y10: '4.47%', y15: '4.77%', y20: '4.97%', y25: '5.04%', y30: '5.07%' },
  { rating: 'BBB', y5: '4.80%', y10: '5.30%', y15: '5.60%', y20: '5.80%', y25: '5.87%', y30: '5.90%' },
]

const TIC_GRID: { rating: string; tic10: string; tic20: string; tic30: string; obs: number }[] = [
  { rating: 'AA',  tic10: '4.74%', tic20: '5.24%', tic30: '5.34%', obs: 15 },
  { rating: 'A',   tic10: '5.11%', tic20: '5.61%', tic30: '5.71%', obs: 28 },
  { rating: 'BBB', tic10: '5.87%', tic20: '6.37%', tic30: '6.47%', obs: 12 },
]

const DOLLAR_COST: { rating: string; annual: string; total25: string }[] = [
  { rating: 'AA',  annual: '~$5.4M', total25: '~$135M' },
  { rating: 'A',   annual: '~$5.8M', total25: '~$145M' },
  { rating: 'BBB', annual: '~$6.5M', total25: '~$162M' },
]

export function PricingGrid() {
  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
      <div className="px-5 py-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900 text-base">
          Current Pricing — What Healthcare Bonds Cost Now
        </h3>
        <p className="text-sm text-gray-500 mt-1">
          Municipal yield curve as of March 27, 2026. All-in TIC = yield +
          issuer fees (~7 bps) + structural/underwriting costs (~95 bps).
        </p>
      </div>
      <div className="px-5 pb-5 pt-4 space-y-5">
        {/* Yield Curve Table */}
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-2">
            Municipal Yield Curve
          </h4>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2.5 px-3 font-medium text-gray-600">
                    Rating
                  </th>
                  <th className="text-right py-2.5 px-3 font-medium text-gray-600">5yr</th>
                  <th className="text-right py-2.5 px-3 font-medium text-gray-600">10yr</th>
                  <th className="text-right py-2.5 px-3 font-medium text-gray-600">15yr</th>
                  <th className="text-right py-2.5 px-3 font-medium text-gray-600">20yr</th>
                  <th className="text-right py-2.5 px-3 font-medium text-gray-600 bg-blue-50">25yr</th>
                  <th className="text-right py-2.5 px-3 font-medium text-gray-600">30yr</th>
                </tr>
              </thead>
              <tbody>
                {YIELD_CURVE.map((row) => (
                  <tr key={row.rating} className="border-b border-gray-100">
                    <td className="py-2.5 px-3 text-gray-800 font-medium">
                      {row.rating}
                    </td>
                    <td className="py-2.5 px-3 text-gray-600 text-right">{row.y5}</td>
                    <td className="py-2.5 px-3 text-gray-600 text-right">{row.y10}</td>
                    <td className="py-2.5 px-3 text-gray-600 text-right">{row.y15}</td>
                    <td className="py-2.5 px-3 text-gray-600 text-right">{row.y20}</td>
                    <td className="py-2.5 px-3 text-gray-800 font-semibold text-right bg-blue-50">{row.y25}</td>
                    <td className="py-2.5 px-3 text-gray-600 text-right">{row.y30}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* All-In TIC Grid */}
        <div>
          <h4 className="text-sm font-medium text-gray-600 mb-2">
            All-In TIC — Healthcare Borrowers (Corpus-Calibrated)
          </h4>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2.5 px-3 font-medium text-gray-600">
                    Rating
                  </th>
                  <th className="text-right py-2.5 px-3 font-medium text-gray-600">
                    10-Year TIC
                  </th>
                  <th className="text-right py-2.5 px-3 font-medium text-gray-600">
                    20-Year TIC
                  </th>
                  <th className="text-right py-2.5 px-3 font-medium text-gray-600">
                    30-Year TIC
                  </th>
                  <th className="text-right py-2.5 px-3 font-medium text-gray-600">
                    Corpus Obs.
                  </th>
                </tr>
              </thead>
              <tbody>
                {TIC_GRID.map((row) => (
                  <tr key={row.rating} className="border-b border-gray-100">
                    <td className="py-2.5 px-3 text-gray-800 font-semibold">
                      {row.rating}
                    </td>
                    <td className="py-2.5 px-3 text-gray-800 font-semibold text-right">
                      {row.tic10}
                    </td>
                    <td className="py-2.5 px-3 text-gray-800 font-semibold text-right">
                      {row.tic20}
                    </td>
                    <td className="py-2.5 px-3 text-gray-800 font-semibold text-right">
                      {row.tic30}
                    </td>
                    <td className="py-2.5 px-3 text-gray-500 text-right">
                      {row.obs}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-2 text-xs text-gray-500 space-y-1">
            <p>AA healthcare bonds trade at <strong>-12.6 bps</strong> to AAA MMD — strong institutional demand</p>
            <p>A healthcare bonds trade at <strong>+23.9 bps</strong> to AAA MMD — 28 corpus observations = reliable benchmark</p>
            <p>BBB healthcare bonds carry <strong>+100 bps</strong> — materially higher cost but accessible to well-documented credits</p>
          </div>
        </div>

        {/* Dollar Cost Table */}
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">
            What a Rating Tier Costs in Dollar Terms
          </h4>
          <p className="text-xs text-blue-700 mb-3">
            For a $75M, 25-year healthcare revenue bond:
          </p>
          <div className="grid grid-cols-3 gap-3">
            {DOLLAR_COST.map((row) => (
              <div
                key={row.rating}
                className="bg-white rounded-lg px-4 py-3 text-center border border-blue-100"
              >
                <div className="text-xs text-gray-500 uppercase font-medium">
                  {row.rating}-Rated
                </div>
                <div className="text-lg font-bold text-blue-900 mt-1">
                  {row.annual}
                </div>
                <div className="text-xs text-gray-500">annual debt service</div>
                <div className="text-sm font-semibold text-gray-700 mt-1">
                  {row.total25}
                </div>
                <div className="text-xs text-gray-400">25-year total</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-blue-800 mt-3 font-medium">
            The AA vs. BBB spread costs approximately $27M over 25 years on a
            $75M deal. The investment in achieving and maintaining an A or better
            rating pays for itself multiple times over.
          </p>
        </div>
      </div>
    </div>
  )
}

/* ---------- Section 9: Engagement Path ---------- */

const ENGAGEMENT_STEPS: { step: string; description: string; cost: string }[] = [
  {
    step: 'Market Intelligence Report',
    description: 'Market benchmarks: DSCR, pricing, risk profile, Pareto framework',
    cost: 'Free',
  },
  {
    step: 'Readiness Scan',
    description: 'Automated BFMS pre-screen: sector fit, deal size, top 3 gaps',
    cost: 'Free',
  },
  {
    step: 'Bond Readiness Diagnostic',
    description: 'BFMS score + gap analysis + critical path to close',
    cost: '$15,000–$25,000',
  },
  {
    step: 'Bond Readiness Accelerator',
    description: 'Full evidence assembly, disclosure prep, underwriter coordination',
    cost: '$45,000–$75,000',
  },
]

export function EngagementPath() {
  return (
    <div className="bg-gradient-to-br from-muni-navy to-indigo-900 rounded-lg p-6 text-white">
      <h3 className="font-semibold text-base mb-1">
        How to Engage — The Bond Readiness Path
      </h3>
      <p className="text-sm text-gray-300 mb-4">
        For a $75M healthcare bond, the Diagnostic costs less than 0.04% of deal
        size.
      </p>
      <div className="space-y-2">
        {ENGAGEMENT_STEPS.map((s, i) => (
          <div
            key={i}
            className={`flex items-center gap-3 rounded-lg p-3 ${
              i === 0
                ? 'bg-white/10 border border-muni-teal/30'
                : 'bg-white/5'
            }`}
          >
            <span className="text-muni-teal font-bold text-sm w-6 text-center flex-shrink-0">
              {i + 1}
            </span>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-white">{s.step}</div>
              <div className="text-xs text-gray-400">{s.description}</div>
            </div>
            <span
              className={`text-xs font-semibold flex-shrink-0 px-2 py-1 rounded ${
                s.cost === 'Free'
                  ? 'bg-muni-teal/20 text-muni-teal'
                  : 'bg-white/10 text-gray-300'
              }`}
            >
              {s.cost}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
