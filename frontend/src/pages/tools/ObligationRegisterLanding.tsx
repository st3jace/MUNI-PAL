/**
 * Obligation Register — public landing page (muni-pal.io/obligation-register)
 *
 * Product: 10-Day Obligation Register (LS-A2-POST). Post-close only. Sector-neutral.
 * Copy: Hermosillo 2026-09-10 (workspace/hermosillo/2026-09-10-obligation-register-landing-page.md),
 *       headline B + sub-headline A1 with the ten-day tweak (Stephen 2026-09-10).
 *       Plain-language pass 2026-09-11 (gtm/webinar/2026-09-11-PLAIN-LANGUAGE-PASS.md).
 * Controls: Arthur 2026-09-09 letter — approved-input rule verbatim in §3, four status codes,
 *       guarantee in §6. No price. No claim numbers. No "compliant".
 *       Disclaimers state facts about registration status, never a conclusion about the activity.
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
  { name: 'Register', copy: 'Every reporting promise, tied to the document and clause that created it, with who gets it, how often, the next due date when known, and one of four status words.' },
  { name: 'Calendar', copy: 'Due dates your lawyer or advisor gave in writing. Where there is no written answer yet, we show the document’s own words and leave the date empty.' },
  { name: 'Gap list', copy: 'A promise your lawyer approved, with no matching file. That is all it says. No fix-it plan. No ranking.' },
  { name: 'Items awaiting input', copy: 'What we asked your lawyer or advisor for in writing and have not received, listed by the date we asked.' },
  { name: 'Refusal log', copy: 'Questions only your lawyer can answer. We log each one and send it to your bond counsel or dissemination agent. We do not answer them.' },
  { name: 'Evidence vault index', copy: 'A labeled folder of every document and report you sent us, each tied to its row in the register.' },
]

const STATUSES = ['filed', 'not filed', 'evidence missing', 'not testable']
const STATUS_MEANINGS =
  'filed: we have the file · not filed: not due yet · evidence missing: the due date passed and there is no file · not testable: no date to check against'

const HOW_IT_WORKS = [
  'You confirm your bonds have closed and that you are the borrower.',
  'You send us your documents and tell us who your lawyer, advisor, and dissemination agent are.',
  'We quote a fixed fee once we know how many bond issues you have and see your disclosure agreement and filed reports. The fee is never a percentage of your bonds and never depends on an outcome.',
  'You sign an engagement letter written for this work. Payment is due when you sign.',
  'We deliver in ten business days from a complete set of documents. The clock pauses while we wait for a written answer from your lawyer.',
  'You, or your dissemination agent, file. We do not.',
]

type EntityType = 'private_obligated_person' | 'municipal_entity' | 'unclear'
type Gate = 'unset' | 'yes' | 'no'

const PRE_ISSUANCE_STOP =
  'This offer is only for private borrowers whose bonds have already closed. We do not build registers for bonds that have not been sold yet.'
const MUNICIPAL_STOP = 'We have no path for cities, districts, or other public bodies today.'

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
          We will confirm this is a fit and reply with a fixed-fee quote once we see how many bond issues you have and your disclosure agreement. We do not give filing advice from this form.
        </p>
      </div>
    )
  }

  return (
    <form onSubmit={onSubmit} className="bg-white rounded-xl border border-gray-200 p-6 md:p-8 space-y-8" noValidate>
      {/* Gate — first, alone */}
      <fieldset>
        <legend className="text-base font-semibold text-gray-900 mb-2">Have the bonds already closed?</legend>
        <p className={help + ' mb-3'}>Closed means the bonds were sold and delivered, not just approved. We only work on promises that already exist.</p>
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
            <legend className="text-base font-semibold text-gray-900">Your organization</legend>
            <div>
              <label className={label} htmlFor="legal_name">Legal name of the borrower</label>
              <input id="legal_name" name="legal_name" className={field} required />
              <p className={help}>The name on your continuing disclosure agreement.</p>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className={label} htmlFor="entity_type">Entity type</label>
                <select id="entity_type" name="entity_type" className={field} value={entityType} onChange={(e) => setEntityType(e.target.value as EntityType)} required>
                  <option value="">Choose one</option>
                  <option value="private_obligated_person">Private borrower (nonprofit or company)</option>
                  <option value="municipal_entity">City, district, or other public body</option>
                  <option value="unclear">Not sure</option>
                </select>
                <p className={help}>Pick what your bond documents call you. If you are not sure, a person on our team will check.</p>
              </div>
              <div>
                <label className={label} htmlFor="state">State</label>
                <input id="state" name="state" className={field} maxLength={2} placeholder="AZ" />
                <p className={help}>Tells us which state&rsquo;s document style to expect.</p>
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
                    <p className={help}>Where we send the quote and the engagement letter.</p>
                  </div>
                  <div>
                    <label className={label} htmlFor="contact_phone">Phone</label>
                    <input id="contact_phone" name="contact_phone" type="tel" className={field} />
                    <p className={help}>Optional. Scheduling only.</p>
                  </div>
                </div>
              </fieldset>

              <fieldset className="space-y-4">
                <legend className="text-base font-semibold text-gray-900">Your bonds</legend>
                <div>
                  <label className={label} htmlFor="instrument_list">Bond issues that have already closed</label>
                  <textarea id="instrument_list" name="instrument_list" className={field} rows={3} required placeholder="One per line: issuer, series name, closing year if you know it" />
                  <p className={help}>Copy it from your closing documents. We are not asking for advice here.</p>
                </div>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className={label} htmlFor="instrument_count">How many separate bond issues?</label>
                    <input id="instrument_count" name="instrument_count" type="number" min={1} className={field} />
                  </div>
                  <div>
                    <label className={label} htmlFor="cda_present">Do you have a continuing disclosure agreement in your closing documents?</label>
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
                  <textarea id="documents_on_hand" name="documents_on_hand" className={field} rows={2} placeholder="Closing binder, disclosure agreement, loan agreement, past filings, anything missing" />
                  <p className={help}>Just list what you have. You send the documents after the quote, through a private link. Please do not ask a legal question here; we would only send it to your lawyer.</p>
                </div>
              </fieldset>

              <fieldset className="space-y-4">
                <legend className="text-base font-semibold text-gray-900">Your professionals</legend>
                <p className={help}>We replace none of them. They approve the list of promises. Every question that needs judgment goes to them.</p>
                {[
                  ['bond_counsel_contact', 'Bond counsel', 'Firm and person, if you have one. Judgment questions go here.'],
                  ['municipal_advisor_contact', 'Municipal advisor', 'Firm and person, if you have one.'],
                  ['dissemination_agent_contact', 'Dissemination agent', 'Firm and person, if appointed. This is the firm that posts your reports to the MSRB’s public site. They file; we do not.'],
                ].map(([name, lbl, h]) => (
                  <div key={name}>
                    <label className={label} htmlFor={name}>{lbl}</label>
                    <input id={name} name={name} className={field} />
                    <p className={help}>{h}</p>
                  </div>
                ))}
              </fieldset>

              <fieldset>
                <legend className="text-base font-semibold text-gray-900 mb-2">Do you also want us to work on a new bond sale at the same time?</legend>
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
                <p className={help}>Live attendees who start this form within 24 hours of the session get the workshop price.</p>
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
              10-Day Obligation Register · for private borrowers whose bonds have closed
            </p>
            <h1 className="text-3xl md:text-4xl lg:text-[2.75rem] font-bold leading-tight text-white mb-6">
              The post-close obligation book your counsel can work from.
            </h1>
            <p className="text-base md:text-lg text-gray-300 mb-10 leading-relaxed">
              We build a register of every reporting promise in your closing documents, using only what your lawyer or advisor approves in writing, in ten business days. You, or your dissemination agent, file.
            </p>
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <CtaButton href="#start">Request a fixed-fee quote</CtaButton>
              <a href={SAMPLE_URL} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 text-sm text-gray-200 underline underline-offset-4">
                <FileText className="h-4 w-4" /> See a sample register (made-up example deal)
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* 1. What this is */}
      <section className="max-w-4xl mx-auto px-6 lg:px-8 mt-14 mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">What this is</h2>
        <p className="text-gray-700 leading-relaxed mb-4">
          The <strong>10-Day Obligation Register</strong> is a record of the reporting promises you made when your bonds closed: annual reports, quarterly reports, event notices, and the rest. It is not a readiness score, not a plan for new bonds, and not a promise about how any filing will be treated. Each promise is tied to the clause that created it, with the file beside it when you have sent us one.
        </p>
        <p className="text-gray-600 text-sm leading-relaxed">
          We use this method today for a bond issuer with many deals, each with different reporting promises.
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
          <p className="text-sm text-gray-700 mt-3">{STATUS_MEANINGS}</p>
          <p className="text-xs text-gray-500 mt-3">No score, no rating, no ranking, no color by importance. Questions for your lawyer go in the refusal log and the items-awaiting-input list, never in the status column.</p>
        </div>
      </section>

      {/* 3. What we never do */}
      <section className="max-w-4xl mx-auto px-6 lg:px-8 mb-12">
        <div className="bg-white rounded-xl border border-gray-200 p-7">
          <h2 className="text-2xl font-bold text-gray-900 mb-1 flex items-center gap-3"><Shield className="h-6 w-6 text-gray-400" /> What we never do</h2>
          <p className="text-sm text-gray-500 mb-5">Read this first. It is why you can share the file with your lawyer and your board.</p>
          <p className="text-gray-700 leading-relaxed mb-5">
            We never file on the MSRB&rsquo;s public filing system. We never say you are fine. We never draft notices. We never invent a deadline. We never decide which clause controls.
          </p>
          <p className="text-gray-800 leading-relaxed mb-3 font-medium">
            In plain words: we copy what your documents say and what your lawyer tells us. We never decide what it means. The exact rule:
          </p>
          <blockquote className="border-l-4 pl-4 text-sm text-gray-800 leading-relaxed italic" style={{ borderColor: BRAND.teal }}>
            {ARTHUR_CONTROL}
          </blockquote>
          <p className="text-gray-700 leading-relaxed mt-5 text-sm">
            When a question needs judgment, it is a call for your bond counsel or dissemination agent. We log it, send it to them, and leave the field empty until they answer in writing.
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
                  'Private borrowers on bonds (nonprofits and companies): operators, CFOs, controllers, and asset managers whose bonds have closed and who still have reporting promises to keep.',
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
                  'Cities, districts, and other public bodies. We have no path for you today.',
                  'Advice on bonds that have not been sold yet.',
                  'Filing, deciding what is material, or writing disclosure documents.',
                  'Work on a new bond sale for you while this engagement is open.',
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
          <h2 className="text-2xl font-bold text-gray-900 mb-3">Want to take the first step yourself?</h2>
          <p className="text-gray-700 leading-relaxed mb-4">
            Take the free kit: instructions you paste into the AI assistant you already use, a checklist of the documents you need, the register template, and a one-page guide to the four status words. Your AI builds a Candidate Map from your own documents: a first-draft list of your reporting promises. Your lawyer approves it. Same method, same rule: nothing counts until it is approved, and the AI never works out a date.
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
          One question comes first: have the bonds already closed? If not, the form stops. If yes, tell us who you are, which bond issues you have, and who your professionals are. We reply with a fixed-fee quote and the engagement letter. No pressure, no countdown.
        </p>
        <IntakeForm />
      </section>

      {/* FOOTER */}
      <footer className="max-w-6xl mx-auto px-6 lg:px-8">
        <div className="flex flex-col items-center gap-3 py-8 border-t border-gray-200">
          <img src="/muni-pal-emblem.png" alt="Muni-Pal" className="h-10 w-10 object-contain opacity-50" />
          <p className="text-sm text-gray-400">Muni-Pal &mdash; A Launch Shop product. Built by Innovation Factory.</p>
          <p className="text-[11px] text-gray-400 max-w-2xl text-center leading-relaxed">
            Muni-Pal is not a registered municipal advisor, broker-dealer, or law firm, and is not your dissemination agent. Nothing on this page is legal advice. Filing decisions belong with you and your own licensed professionals.
          </p>
        </div>
      </footer>
    </div>
  )
}
