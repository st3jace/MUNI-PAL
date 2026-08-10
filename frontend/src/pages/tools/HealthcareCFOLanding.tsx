import { Link } from 'react-router-dom'
import {
  BarChart3,
  Shield,
  DollarSign,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  XCircle,
  TrendingUp,
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
/*  Data                                                               */
/* ------------------------------------------------------------------ */
const VALUE_PROPS = [
  {
    icon: BarChart3,
    headline: 'Know what “good” looks like',
    copy: 'See the debt-service coverage (DSCR — your cash flow vs. your annual payments), days cash on hand, and payer mix that separate highly rated hospitals from the rest — drawn from real public disclosure filings, not industry averages.',
  },
  {
    icon: DollarSign,
    headline: 'Walk into advisor meetings with context',
    copy: 'See typical borrowing costs by credit rating, so you can ask sharper questions of your registered advisor and deal team — instead of hearing every number for the first time.',
  },
  {
    icon: AlertTriangle,
    headline: 'See your gaps before a lender does',
    copy: 'The readiness dimensions hospitals most often under-document — and the kind of evidence that strengthened comparable borrowers.',
  },
]

const HOW_IT_WORKS = [
  {
    step: 1,
    name: 'Answer questions about your facility',
    description: 'Free, about 15 minutes, no documents required to start.',
  },
  {
    step: 2,
    name: 'See where you stand',
    description:
      'A readiness score across 6 dimensions, benchmarked against 866 real municipal bond transactions — plus your top gaps.',
  },
  {
    step: 3,
    name: 'Take it to your advisors',
    description:
      'You get a report you can put in front of your board and your registered advisor, with the questions worth asking.',
  },
]

const WHAT_YOU_GET = [
  'A readiness score across 6 dimensions',
  'Sector benchmarks from 866 real municipal bond transactions',
  'Your top gaps, with examples of what stronger borrowers documented',
  'A report you can hand to your board and registered advisor',
]

/* ------------------------------------------------------------------ */
/*  Preview Card (hero right side)                                     */
/* ------------------------------------------------------------------ */
function PreviewCard() {
  return (
    <div className="bg-white rounded-xl shadow-2xl overflow-hidden border border-gray-100 max-w-sm">
      <div className="bg-gradient-to-r from-muni-navy to-[#2a4f7a] px-5 py-3">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-400" />
          <span className="text-xs text-gray-300 font-mono">app.muni-pal.io</span>
        </div>
      </div>
      <div className="p-5 space-y-4">
        <div>
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1">Bond Readiness Score</p>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold text-muni-navy">72</span>
            <span className="text-sm text-gray-400 mb-1">/100</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2 mt-2">
            <div className="bg-muni-teal h-2 rounded-full" style={{ width: '72%' }} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {[
            { label: 'DSCR (coverage)', value: '1.45x', color: BRAND.teal },
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
            <span className="text-xs text-gray-600">3 of 6 readiness dimensions ready for advisor review</span>
          </div>
          <p className="text-[10px] text-gray-400 mt-2">
            Sample assessment &mdash; illustrative numbers, not a real facility.
          </p>
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
      <section className="relative bg-gradient-to-br from-muni-navy via-muni-navy to-indigo-900 overflow-hidden">
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
                For healthcare CFOs planning a first bond issue
              </p>
              <h1 className="text-3xl md:text-4xl lg:text-[2.75rem] font-bold leading-tight text-white max-w-xl mb-6">
                Find out if your hospital is bond-ready &mdash; and what
                borrowing will really cost &mdash; before you sit down with
                anyone.
              </h1>
              <p className="text-base md:text-lg text-gray-300 max-w-lg mb-10 leading-relaxed">
                Muni-Pal shows you what municipal deals like yours actually
                looked like, built from{' '}
                <span className="text-white font-semibold">
                  866 real municipal bond transactions
                </span>{' '}
                in public disclosure filings. See where you stand &mdash; for
                free, in about 15 minutes &mdash; before your first advisor
                meeting.
              </p>

              <div className="flex flex-col items-start gap-3">
                <Link
                  to="/tools/readiness"
                  className="inline-flex items-center justify-center gap-2 text-white font-semibold px-7 py-3.5 rounded-lg transition-colors text-base shadow-lg"
                  style={{ backgroundColor: BRAND.orange, boxShadow: `0 8px 24px color-mix(in srgb, ${BRAND.orange} 20%, transparent)` }}
                  onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = BRAND.orangeHover)}
                  onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = BRAND.orange)}
                >
                  Start Your Free Readiness Assessment
                  <ArrowRight className="h-5 w-5" />
                </Link>
                <p className="text-sm text-gray-400">
                  Free. About 15 minutes. No documents required to start.
                </p>
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
      {/*  AUDIENCE FILTER — who it's for                               */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mt-14 mb-14">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <h3 className="text-base font-semibold text-gray-800 px-7 pt-7 pb-4 flex items-center gap-3">
            <Shield className="h-5 w-5 text-gray-400" />
            Who this is for &mdash; and who it isn't
          </h3>
          <div className="grid md:grid-cols-2 gap-0">
            <div className="bg-white p-7 md:border-r border-gray-200">
              <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: BRAND.teal }}>
                Built for
              </p>
              <ul className="space-y-2.5">
                {[
                  'Healthcare CFOs and finance directors thinking about a bond for the first time',
                  'Hospital systems weighing how to fund a major project',
                  'Deals above $10M',
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
                Not for
              </p>
              <ul className="space-y-2.5">
                {[
                  'Deals under $10M',
                  'Issuers outside healthcare',
                  'Anyone looking for personal investment advice',
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
      {/*  PROOF BLOCK — stats                                          */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-14">
        <div className="bg-gray-50 border border-gray-100 rounded-xl py-8 px-6">
          <div className="flex flex-wrap justify-center gap-10 md:gap-16 text-center">
            {[
              { value: '866', label: 'real municipal bond transactions analyzed' },
              { value: '6', label: 'readiness dimensions scored on every assessment' },
              { value: '15 min', label: 'to a first readiness read. Free.' },
            ].map((stat) => (
              <div key={stat.label}>
                <span className="block text-3xl font-bold" style={{ color: BRAND.navy }}>{stat.value}</span>
                <span className="text-sm text-gray-500 mt-1 block">{stat.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  PROOF BLOCK — why check early                                */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-14">
        <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-xl border border-red-100 p-7 md:p-8">
          <div className="flex items-start gap-4">
            <div className="h-12 w-12 rounded-full bg-red-100 flex items-center justify-center flex-shrink-0">
              <TrendingUp className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">
                Why check early: your credit story is worth real money
              </h3>
              <p className="text-sm text-gray-700 leading-relaxed">
                In public healthcare bond filings, higher-rated hospitals
                consistently borrow at lower rates than lower-rated ones
                &mdash; and that gap (the &ldquo;spread,&rdquo; the premium
                over the benchmark rate) compounds every year for the 25&ndash;30
                year life of a deal. The cheapest time to close a readiness gap
                is before anyone prices your deal.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  HOW IT WORKS — 3 free steps                                  */}
      {/* ============================================================ */}
      <section id="how-it-works" className="max-w-6xl mx-auto px-6 lg:px-8 mb-14 scroll-mt-24">
        <h2 className="text-2xl font-bold text-gray-900 mb-8">
          How it works
        </h2>

        <div className="grid gap-0 md:grid-cols-3 relative">
          <div className="hidden md:block absolute top-7 left-[16.7%] right-[16.7%] h-px bg-gray-200" />
          {HOW_IT_WORKS.map((step) => (
            <div key={step.name} className="relative flex flex-col items-center text-center px-4 mb-8 md:mb-0">
              <div className="relative z-10 h-14 w-14 rounded-full flex items-center justify-center text-lg font-bold mb-3 bg-muni-teal text-white">
                {step.step}
              </div>
              <h3 className="text-sm font-semibold text-gray-900 mb-1.5">
                {step.name}
              </h3>
              <p className="text-xs text-gray-500 leading-relaxed">
                {step.description}
              </p>
            </div>
          ))}
        </div>

        <p className="text-sm text-gray-600 mt-8 max-w-2xl">
          A typical healthcare bond deal takes 6&ndash;9 months from first
          conversation to closing &mdash; which is why the free assessment is
          worth doing before you think you need it.
        </p>
        <p className="text-xs text-gray-400 mt-2">
          Deeper paid engagements exist when you're ready &mdash; start free.
        </p>
      </section>

      {/* ============================================================ */}
      {/*  WHAT YOU GET — value props + assessment deliverables         */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-14">
        <div className="grid gap-6 md:grid-cols-3 mb-10">
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

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-7">
          <h3 className="text-base font-semibold text-gray-900 mb-4">
            What you get with the free assessment
          </h3>
          <ul className="space-y-2.5 mb-4">
            {WHAT_YOU_GET.map((item) => (
              <li key={item} className="flex items-start gap-2.5 text-sm text-gray-700">
                <CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5" style={{ color: BRAND.teal }} />
                {item}
              </li>
            ))}
          </ul>
          <p className="text-sm text-gray-600">
            Want to see one first?{' '}
            <Link
              to="/tools/market-intelligence"
              className="font-medium underline underline-offset-2"
              style={{ color: BRAND.teal }}
            >
              View a sample market report
            </Link>
            .
          </p>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  ANALYSIS PREVIEW — plain-English stress test                 */}
      {/* ============================================================ */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-14">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          See what the analysis looks like
        </h2>
        <div className="bg-muni-navy rounded-xl p-6 md:p-8">
          <p className="text-gray-200 text-base leading-relaxed max-w-3xl">
            Before your deal is ever priced, you can stress-test it: what
            happens to your coverage if revenue dips, expenses run hot, or
            both. The platform runs your numbers through hundreds of scenarios
            and shows you the range &mdash; best case, worst case, and most
            likely &mdash; in plain terms.
          </p>
          <p className="text-xs text-gray-400 mt-4">
            Illustrative example using sample inputs &mdash; not a prediction
            for your facility.
          </p>
        </div>
      </section>

      {/* ============================================================ */}
      {/*  BOTTOM CTA                                                   */}
      {/* ============================================================ */}
      <section style={{ backgroundColor: BRAND.navy }} className="py-14 md:py-16">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-3">
            Find out if your hospital is bond-ready.
          </h2>
          <p className="text-gray-300 mb-8 max-w-lg mx-auto text-sm">
            Free. About 15 minutes. No documents required to start. No sales
            call. This is an educational readiness snapshot &mdash; not
            investment advice and not a loan application.
          </p>
          <Link
            to="/tools/readiness"
            className="inline-flex items-center gap-2 text-white font-semibold px-10 py-4 rounded-lg transition-colors text-lg"
            style={{ backgroundColor: BRAND.orange, boxShadow: `0 8px 24px color-mix(in srgb, ${BRAND.orange} 20%, transparent)` }}
            onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = BRAND.orangeHover)}
            onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = BRAND.orange)}
          >
            Start Your Free Readiness Assessment
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
            Muni-Pal is an educational and analytical service. We help you
            understand your numbers and prepare for conversations with your own
            registered advisors &mdash; we are not your municipal advisor, and
            nothing on this site is municipal advisory services as defined
            under Section 15B of the Securities Exchange Act, investment
            advice, or an offer to arrange financing. Bond decisions belong
            with your board and your licensed professionals.
          </p>
        </div>
      </footer>
    </div>
  )
}
