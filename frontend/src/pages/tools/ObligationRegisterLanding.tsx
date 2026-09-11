/**
 * Obligation Register — public landing page (muni-pal.io/obligation-register)
 *
 * Product: 10-Day Obligation Register (LS-A2-POST). Post-close only. Sector-neutral.
 * Copy: Hermosillo 2026-09-10 (workspace/hermosillo/2026-09-10-obligation-register-landing-page.md),
 *       headline B + sub-headline A1 with the ten-day tweak (Stephen 2026-09-10).
 * Controls: Arthur 2026-09-09 letter — approved-input rule verbatim in §3, four status codes,
 *       guarantee verbatim in §6. No price. No claim numbers. No "compliant".
 */
import { useEffect, useState, type FormEvent } from 'react'
import { ArrowRight, CheckCircle2, FileText, Shield, XCircle } from 'lucide-react'

const BRAND = {
  navy: 'var(--brand-primary)',
  teal: 'var(--brand-accent)',
  orange: 'var(--brand-cta)',
  orangeHover: 'var(--brand-cta-hover)',
}

const INTAKE_URL = '/api/v1/sensing/obligation-register/intake'
export const SAMPLE_URL = '/samples/obligation-register-sample.html'
export const DIY_URL = '/diy/index.html'

// Arthur control — verbatim. Do not edit without a ruling.
const ARTHUR_CONTROL =
  'Muni-Pal records or mechanically transcribes obligations, dates, and owners supplied or approved by the client, bond counsel, municipal advisor, or dissemination agent. Muni-Pal does not independently decide which undertaking controls, interpret ambiguous deadline formulas, determine successor/refunding effects, or decide whether an obligation applies.'

// Guarantee — matches letter §6.9; numbers ruled in
// braintrust/workspace/cos/2026-09-09-DECISION-a2post-pricing-and-guarantee.md (2%/day, 20% cap, day 20).
// The big line must stay true without the fine print. Fine print adds detail; it never takes back the promise.
const GUARANTEE =
  'We deliver in ten business days.* If we are late, you get money back for each late business day. If we have not delivered by business day 20, you can end it and get the full fee back.'

const GUARANTEE_FINE_PRINT =
  '* Terms apply. The engagement letter controls. The ten business days start when your document set is complete against our checklist. The clock pauses while we wait for a written answer we asked for from your counsel or from you. Each late business day refunds 2% of the fee, up to 20%. If by business day 20 on that clock we have not delivered the Register and the labeled document vault, you may end the engagement and we refund the full fee within ten business days. No guarantee of filing status on the MSRB’s public filing system, issuer comfort, audit outcome, or future issuance.'

const WHAT_YOU_GET = [
  { name: 'Register', copy: 'Each obligation tied to a source document and clause, with recipient, frequency, next due date when known, and a fixed status.' },
  { name: 'Calendar', copy: 'Due dates from text you designate or written instructions your professionals supply.' },
  { name: 'Gap list', copy: 'Observational only: an approved undertaking, and no matching vault file. No remediation. No impact ranking.' },
  { name: 'Items awaiting input', copy: 'What we asked your professionals for in writing and have not received. Sorted by request date, nothing else.' },
  { name: 'Refusal log', copy: 'Judgment questions routed to your counsel or dissemination agent. Not answered by us.' },
  { name: 'Evidence vault index', copy: 'Labeled files bound back to register rows.' },
]

const STATUSES = ['filed', 'not filed', 'evidence missing', 'not testable']

const HOW_IT_WORKS = [
  'You confirm the bonds have closed and you are the obligated person.',
  'You send the document drop and name your professionals.',
  'We quote a fixed fee after we see your instrument count and CDA pack. Never on par, never contingent, never in basis points.',
  'You sign the purpose-built engagement letter. Payment is due at signature.',
  'We deliver in ten business days from a complete drop, pausing while we wait on your counsel’s written input.',
  'You, or your dissemination agent, file. We do not.',
]

type EntityType = 'private_obligated_person' | 'municipal_entity' | 'unclear'
type Gate = 'unset' | 'yes' | 'no'

const PRE_ISSUANCE_STOP =
  'This offer is for post-close obligated persons only. We do not build registers for deals that have not closed.'
const MUNICIPAL_STOP = 'We have no path for municipal entities or public authorities today.'

function CtaButton({ children, href }: { children: React.ReactNode; href: string }) {
  return (
    <a
      href={href}
      className="inline-flex items-center justify-center gap-2 text-white font-semibold px-7 py-3.5 rounded-lg transition-colors text-base shadow-lg"
      style={{ backgroundColor: BRAND.orange }}
      onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = BRAND.orangeHover)}
      onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = BRAND.orange)}
    >
      {children}
      <ArrowRight className="h-5 w-5" />
    </a>
  )
}

/* ------------------------------------------------------------------ */
/*  Intake form                                                        */
/* ------------------------------------------------------------------ */
export function IntakeForm() {
  const [gate, setGate] = useState<Gate>('unset')
  const [entityType, setEntityType] = useState<EntityType | ''>('')
  const [concurrent, setConcurrent] = useState<'' | 'yes' | 'no'>('')
  const [consent, setConsent] = useState(false)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const municipalStop = entityType === 'municipal_entity'

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    const f = new FormData(e.currentTarget)
    const get = (k: string) => (f.get(k) as string | null)?.trim() || null
    const payload = {
      bonds_already_closed: gate === 'yes',
      legal_name: get('legal_name'),
      entity_type: entityType,
      state: get('state'),
      contact_name: get('contact_name'),
      contact_title: get('contact_title'),
      contact_email: get('contact_email'),
      contact_phone: get('contact_phone'),
      bond_counsel_contact: get('bond_counsel_contact'),
      municipal_advisor_contact: get('municipal_advisor_contact'),
      dissemination_agent_contact: get('dissemination_agent_contact'),
      instrument_list: get('instrument_list'),
      instrument_count: get('instrument_count') ? Number(get('instrument_count')) : null,
      cda_present: get('cda_present'),
      documents_on_hand: get('documents_on_hand'),
      concurrent_preissuance: concurrent === 'yes',
      workshop_session: get('workshop_session'),
      privacy_consent: consent,
      consent_version: 'obligation-intake-v1',
    }
    setBusy(true)
    try {
      const res = await fetch(INTAKE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const body = await res.json().catch(() => ({}))
      if (!res.ok) {
        const detail = typeof body?.detail === 'string' ? body.detail : 'Something in the form did not pass. Check the required fields.'
        setError(detail)
        return
      }
      setDone(body.next ?? 'Received.')
    } catch {
      setError('We could not reach the server. Try again in a minute, or email operations@muni-pal.io.')
    } finally {
      setBusy(false)
    }
  }

  const field = 'w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-muni-teal'
  const label = 'block text-sm font-medium text-gray-800 mb-1'
  const help = 'text-xs text-gray-500 mt-1'

  if (done) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-8" role="status">
        <CheckCircle2 className="h-8 w-8 mb-3" style={{ color: BRAND.teal }} />
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Thanks. We have it.</h3>
        <p className="text-sm text-gray-700">
          We will confirm eligibility and reply with a fixed-fee quote after we review instrument count and the CDA pack. We do not provide filing advice from this form.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={onSubmit} className="bg-white rounded-xl border border-gray-200 p-6 md:p-8 space-y-8" noValidate>
      {/* Gate — first, alone */}
      <fieldset>
        <legend className="text-base font-semibold text-gray-900 mb-2">Have the bonds already closed?</legend>
        <p className={help + ' mb-3'}>Closed, not merely authorized or approved. We only work on obligations that already exist.</p>
        <div className="flex gap-6">
          {(['yes', 'no'] as const).map((v) => (
            <label key={v} className="inline-flex items-center gap-2 text-sm">
              <input type="radio" name="bonds_already_closed" value={v} checked={gate === v} onChange={() => setGate(v)} required />
              {v === 'yes' ? 'Yes' : 'No'}
            </label>
          ))}
        </div>
        {gate === 'no' && (
          <p className="mt-4 rounded-md bg-gray-50 border border-gray-200 p-4 text-sm text-gray-700" role="alert">
            {PRE_ISSUANCE_STOP}
          </p>
        )}
      </fieldset>

      {gate === 'yes' && (
        <>
          <fieldset className="space-y-4">
            <legend className="text-base font-semibold text-gray-900">The entity</legend>
            <div>
              <label className={label} htmlFor="legal_name">Legal name of the obligated person</label>
              <input id="legal_name" name="legal_name" className={field} required />
              <p className={help}>The entity named on the continuing-disclosure undertaking.</p>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className={label} htmlFor="entity_type">Entity type</label>
                <select id="entity_type" name="entity_type" className={field} value={entityType} onChange={(e) => setEntityType(e.target.value as EntityType)} required>
                  <option value="">Choose one</option>
                  <option value="private_obligated_person">Private borrower or obligated person</option>
                  <option value="municipal_entity">Municipal entity or public authority</option>
                  <option value="unclear">Not sure</option>
                </select>
                <p className={help}>Pick what the bond documents call you. "Not sure" holds for a human review.</p>
              </div>
              <div>
                <label className={label} htmlFor="state">State</label>
                <input id="state" name="state" className={field} maxLength={2} placeholder="AZ" />
                <p className={help}>Tells us which document conventions to expect.</p>
              </div>
            </div>
            {municipalStop && (
              <p className="rounded-md bg-gray-50 border border-gray-200 p-4 text-sm text-gray-700" role="alert">
                {MUNICIPAL_STOP}
              </p>
            )}
          </fieldset>

          {!municipalStop && (
            <>
              <fieldset className="space-y-4">
                <legend className="text-base font-semibold text-gray-900">You</legend>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className={label} htmlFor="contact_name">Your name</label>
                    <input id="contact_name" name="contact_name" className={field} required />
                  </div>
                  <div>
                    <label className={label} htmlFor="contact_title">Role</label>
                    <input id="contact_title" name="contact_title" className={field} placeholder="CFO, controller, asset manager" />
                  </div>
                  <div>
                    <label className={label} htmlFor="contact_email">Email</label>
                    <input id="contact_email" name="contact_email" type="email" className={field} required />
                    <p className={help}>Where we send the quote and the letter.</p>
                  </div>
                  <div>
                    <label className={label} htmlFor="contact_phone">Phone</label>
                    <input id="contact_phone" name="contact_phone" type="tel" className={field} />
                    <p className={help}>Optional. Scheduling only.</p>
                  </div>
                </div>
              </fieldset>

              <fieldset className="space-y-4">
                <legend className="text-base font-semibold text-gray-900">The financings</legend>
                <div>
                  <label className={label} htmlFor="instrument_list">Series or instruments already closed</label>
                  <textarea id="instrument_list" name="instrument_list" className={field} rows={3} required placeholder="One per line: issuer, series name, closing year if known" />
                  <p className={help}>Copy it off the closing documents. No advice is requested here.</p>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className={label} htmlFor="instrument_count">How many separate series or issues?</label>
                    <input id="instrument_count" name="instrument_count" type="number" min={1} className={field} />
                  </div>
                  <div>
                    <label className={label} htmlFor="cda_present">Is there a continuing-disclosure agreement in the binder?</label>
                    <select id="cda_present" name="cda_present" className={field} defaultValue="">
                      <option value="">Choose one</option>
                      <option value="yes">Yes</option>
                      <option value="no">No</option>
                      <option value="not_sure">Not sure</option>
                    </select>
                    <p className={help}>"Not sure" is a fine answer.</p>
                  </div>
                </div>
                <div>
                  <label className={label} htmlFor="documents_on_hand">What documents do you have on hand?</label>
                  <textarea id="documents_on_hand" name="documents_on_hand" className={field} rows={2} placeholder="Closing binder, CDA, loan agreement, prior filings, anything missing" />
                  <p className={help}>Labels and file locations only. The document drop itself happens after the quote, through a private link. Please do not ask a question that needs a legal answer here; we would only route it to your counsel.</p>
                </div>
              </fieldset>

              <fieldset className="space-y-4">
                <legend className="text-base font-semibold text-gray-900">Your professionals</legend>
                <p className={help}>We replace none of these. They approve the obligation list. Every judgment question goes to them.</p>
                {[
                  ['bond_counsel_contact', 'Bond counsel', 'Firm and person, if engaged. Judgment calls route here.'],
                  ['municipal_advisor_contact', 'Municipal advisor', 'Firm and person, if engaged.'],
                  ['dissemination_agent_contact', 'Dissemination agent', 'Firm and person, if appointed. They file; we do not.'],
                ].map(([name, lbl, h]) => (
                  <div key={name}>
                    <label className={label} htmlFor={name}>{lbl}</label>
                    <input id={name} name={name} className={field} />
                    <p className={help}>{h}</p>
                  </div>
                ))}
              </fieldset>

              <fieldset>
                <legend className="text-base font-semibold text-gray-900 mb-2">Are you asking us to work a new or contemplated issuance at the same time?</legend>
                <div className="flex gap-6">
                  {(['no', 'yes'] as const).map((v) => (
                    <label key={v} className="inline-flex items-center gap-2 text-sm">
                      <input type="radio" name="concurrent_preissuance" value={v} checked={concurrent === v} onChange={() => setConcurrent(v)} required />
                      {v === 'yes' ? 'Yes' : 'No'}
                    </label>
                  ))}
                </div>
                {concurrent === 'yes' && (
                  <p className={help + ' mt-2'}>We will not quote this product until that is cleared separately. You can still send the form.</p>
                )}
              </fieldset>

              <div>
                <label className={label} htmlFor="workshop_session">Did you attend a live working session? Which one?</label>
                <input id="workshop_session" name="workshop_session" className={field} placeholder="Date and time, or leave blank" />
                <p className={help}>Live attendees who start intake within 24 hours of the session get the workshop price.</p>
              </div>

              <label className="flex items-start gap-3 text-sm text-gray-700">
                <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} required className="mt-1" />
                <span>I consent to Muni-Pal collecting my contact details, entity type, instrument list and professional contacts to confirm eligibility and reply with a fixed-fee quote.</span>
              </label>

              {error && (
                <p className="rounded-md bg-red-50 border border-red-200 p-3 text-sm text-red-800" role="alert">{error}</p>
              )}

              <button
                type="submit"
                disabled={busy || !consent || concurrent === ''}
                className="inline-flex items-center gap-2 text-white font-semibold px-7 py-3.5 rounded-lg disabled:opacity-50"
                style={{ backgroundColor: BRAND.orange }}
              >
                {busy ? 'Sending…' : 'Request fixed-fee quote'}
                <ArrowRight className="h-5 w-5" />
              </button>
            </>
          )}
        </>
      )}
    </form>
  )
}

/* ================================================================== */
/*  Page                                                               */
/* ================================================================== */
export default function ObligationRegisterLanding() {
  useEffect(() => {
    const prev = document.title
    document.title = 'Obligation Register | Muni-Pal'
    return () => {
      document.title = prev
    }
  }, [])

  return (
    <div className="-m-6">
      {/* HERO */}
      <section className="relative bg-gradient-to-br from-muni-navy via-muni-navy to-indigo-900 overflow-hidden">
        <div className="absolute inset-0 opacity-20" style={{ background: 'radial-gradient(ellipse 60% 50% at 30% 40%, rgba(45,174,172,0.4) 0%, transparent 70%)' }} />
        <div className="relative max-w-7xl mx-auto px-6 lg:px-8 py-14 md:py-20">
          <div className="max-w-3xl">
            <p className="text-sm font-semibold tracking-wide uppercase mb-4" style={{ color: BRAND.teal }}>
              10-Day Obligation Register · for obligated persons on closed deals
            </p>
            <h1 className="text-3xl md:text-4xl lg:text-[2.75rem] font-bold leading-tight text-white mb-6">
              The post-close obligation book your counsel can work from.
            </h1>
            <p className="text-base md:text-lg text-gray-300 mb-10 leading-relaxed">
              We build a working register from your closing documents and your professionals&rsquo; written inputs, in ten business days. You, or your dissemination agent, file.
            </p>
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <CtaButton href="#start">Request a fixed-fee quote</CtaButton>
              <a href={SAMPLE_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-sm text-gray-200 underline underline-offset-4">
                <FileText className="h-4 w-4" /> See a sample register (synthetic deal)
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* 1. What this is */}
      <section className="max-w-4xl mx-auto px-6 lg:px-8 mt-14 mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">What this is</h2>
        <p className="text-gray-700 leading-relaxed mb-4">
          The <strong>10-Day Obligation Register</strong> is a post-close working book of your continuing-disclosure and reporting duties on deals that have already closed. It is not a readiness score, not a new-issuance plan, and not a promise about how any filing will be treated. Each undertaking is labeled, bound to the clause that creates it, with evidence beside it when you have provided the file.
        </p>
        <p className="text-gray-600 text-sm leading-relaxed">
          We run this discipline on an issuer-side book with multiple financings whose obligations differ deal to deal.
        </p>
      </section>

      {/* 2. What you get */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">What you get</h2>
        <p className="text-gray-600 text-sm mb-6">What you see on the sample is what you buy.</p>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          {WHAT_YOU_GET.map((item, i) => (
            <div key={item.name} className="bg-white rounded-xl border border-gray-200 p-5">
              <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: BRAND.teal }}>{i + 1}. {item.name}</p>
              <p className="text-sm text-gray-700 leading-relaxed">{item.copy}</p>
            </div>
          ))}
        </div>
        <div className="mt-6 bg-gray-50 border border-gray-200 rounded-xl p-5">
          <p className="text-sm text-gray-800 mb-2"><strong>Every status is one of four words, and nothing else:</strong></p>
          <div className="flex flex-wrap gap-2">
            {STATUSES.map((s) => (
              <code key={s} className="text-sm bg-white border border-gray-200 rounded px-2 py-1 text-gray-800">{s}</code>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-3">No score, no rating, no ranking, no colour by importance. Judgment questions live in the refusal log and the items-awaiting-input list, never in the status column.</p>
        </div>
      </section>

      {/* 3. What we never do */}
      <section className="max-w-4xl mx-auto px-6 lg:px-8 mb-12">
        <div className="bg-white rounded-xl border border-gray-200 p-7">
          <h2 className="text-2xl font-bold text-gray-900 mb-1 flex items-center gap-3"><Shield className="h-6 w-6 text-gray-400" /> What we never do</h2>
          <p className="text-sm text-gray-500 mb-5">Read this first. It is why the file is safe to circulate.</p>
          <p className="text-gray-700 leading-relaxed mb-5">
            We never file on the MSRB&rsquo;s public filing system. We never say you are fine. We never draft notices. We never invent a deadline. We never decide which clause controls.
          </p>
          <blockquote className="border-l-4 pl-4 text-sm text-gray-800 leading-relaxed italic" style={{ borderColor: BRAND.teal }}>
            {ARTHUR_CONTROL}
          </blockquote>
          <p className="text-gray-700 leading-relaxed mt-5 text-sm">
            When a judgment question comes up: that is a call for your bond counsel or dissemination agent. We log it, send it to them, and leave the field empty until they answer in writing.
          </p>
        </div>
      </section>

      {/* 4. Who it is for */}
      <section className="max-w-6xl mx-auto px-6 lg:px-8 mb-12">
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <h2 className="text-base font-semibold text-gray-800 px-7 pt-7 pb-4">Who it is for, and who it is not for</h2>
          <div className="grid md:grid-cols-2 gap-0">
            <div className="p-7 md:border-r border-gray-200">
              <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: BRAND.teal }}>For</p>
              <ul className="space-y-2.5">
                {[
                  'Private obligated persons: operators, CFOs, controllers, asset managers, on closed deals with live continuing-disclosure or reporting undertakings.',
                  'Housing, industrial, food and agriculture, healthcare, education. The sector does not change the work.',
                  'You keep your own bond counsel, municipal advisor, or dissemination agent for the judgment calls.',
                ].map((t) => (
                  <li key={t} className="flex items-start gap-2.5 text-sm text-gray-700"><CheckCircle2 className="h-4 w-4 flex-shrink-0 mt-0.5" style={{ color: BRAND.teal }} />{t}</li>
                ))}
              </ul>
            </div>
            <div className="bg-gray-50 p-7">
              <p className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Not for</p>
              <ul className="space-y-2.5">
                {[
                  'Municipal entities or public authorities. We have no path for you today.',
                  'Advice on a deal that has not closed.',
                  'Filing, materiality calls, or disclosure drafting.',
                  'Pre-issuance document-room work at the same time as this engagement.',
                ].map((t) => (
                  <li key={t} className="flex items-start gap-2.5 text-sm text-gray-500"><XCircle className="h-4 w-4 flex-shrink-0 mt-0.5 text-gray-300" />{t}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* 5. How it works */}
      <section className="max-w-4xl mx-auto px-6 lg:px-8 mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">How it works</h2>
        <ol className="space-y-3">
          {HOW_IT_WORKS.map((step, i) => (
            <li key={step} className="flex items-start gap-4">
              <span className="flex-shrink-0 h-7 w-7 rounded-full text-white text-sm font-bold flex items-center justify-center" style={{ backgroundColor: BRAND.navy }}>{i + 1}</span>
              <p className="text-gray-700 leading-relaxed pt-0.5">{step}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* 6. Guarantee */}
      <section className="max-w-4xl mx-auto px-6 lg:px-8 mb-12">
        <div className="rounded-xl p-7" style={{ backgroundColor: BRAND.navy }}>
          <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: BRAND.teal }}>Guarantee (process only)</p>
          <p className="text-white text-lg font-semibold leading-relaxed mb-4">{GUARANTEE}</p>
          <p className="text-gray-300 text-xs leading-relaxed">{GUARANTEE_FINE_PRINT}</p>
        </div>
      </section>

      {/* DIY kit */}
      <section className="max-w-4xl mx-auto px-6 lg:px-8 mb-12">
        <div className="bg-white rounded-xl border border-gray-200 p-7">
          <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: BRAND.teal }}>Free · do it yourself</p>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">Want to run the first mile yourself?</h2>
          <p className="text-gray-700 leading-relaxed mb-4">
            Take the kit. A set of instructions you paste into the AI assistant you already use, a complete-drop checklist, the register template, and the four-status legend. Your AI builds the candidate map from your own documents. Your counsel approves it. Same method, same rule: candidates only, dates never computed.
          </p>
          <a href={DIY_URL} className="inline-flex items-center gap-2 font-semibold underline underline-offset-4" style={{ color: BRAND.navy }}>
            Get the DIY kit <ArrowRight className="h-4 w-4" />
          </a>
        </div>
      </section>

      {/* 7. How to start */}
      <section id="start" className="max-w-4xl mx-auto px-6 lg:px-8 mb-14 scroll-mt-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">How to start</h2>
        <p className="text-gray-600 text-sm mb-6">
          If the bonds have not closed, the form stops. If you clear the gate, leave contacts, instruments, and your professionals. We reply with a fixed-fee quote and the letter. No invented urgency.
        </p>
        <IntakeForm />
      </section>

      {/* FOOTER */}
      <footer className="max-w-6xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col items-center gap-3 py-8 border-t border-gray-200">
          <img src="/muni-pal-emblem.png" alt="Muni-Pal" className="h-10 w-10 object-contain opacity-50" />
          <p className="text-sm text-gray-400">Muni-Pal &mdash; A Launch Shop product. Built by Innovation Factory.</p>
          <p className="text-[11px] text-gray-400 max-w-2xl text-center leading-relaxed">
            Muni-Pal is not your municipal advisor, not a law firm, and not a dissemination agent. Nothing on this page is municipal advisory services as defined under Section 15B of the Securities Exchange Act, legal advice, or a conclusion about your regulatory status. Filing decisions belong with you and your licensed professionals.
          </p>
        </div>
      </footer>
    </div>
  )
}
