import { useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, CheckCircle2, Download, FileText, FolderOpen, Link2, LockKeyhole, Plus, RefreshCw } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { downloadRegisterFile, RegisterError, registerRequest, type Deal, type Detail, type Folder } from '../services/registerApi'

const input = 'mt-2 w-full rounded-lg border border-gray-300 bg-white p-3 text-sm focus:border-muni-teal focus:outline-none focus:ring-2 focus:ring-muni-teal/20'
const primary = 'btn bg-muni-navy text-white hover:bg-muni-teal focus:ring-muni-teal'
const statusText: Record<string, string> = { awaiting_quote: 'Intake review', awaiting_payment: 'Quote ready', paid: 'Paid', refunded: 'Refunded' }
const money = (deal: Deal) => deal.amount_cents == null ? 'Quoted after review' : new Intl.NumberFormat('en-US', { style: 'currency', currency: deal.currency }).format(deal.amount_cents / 100)

function Field({ label, children }: { label: string; children: ReactNode }) {
  return <label className="block text-sm font-medium text-muni-navy">{label}{children}</label>
}

export default function ObligationRegisterPortal() {
  const auth = useAuth()
  const { dealId } = useParams()
  const token = auth.getAccessToken()
  if (auth.loading) return <p role="status">Opening your workspace…</p>
  if (!auth.user || !token) return <section className="mx-auto max-w-xl rounded-2xl border bg-white p-10">
    <LockKeyhole className="mb-6 text-muni-teal" size={32} />
    <p className="text-xs font-semibold uppercase tracking-widest text-muni-teal">Muni-Pal client workspace</p>
    <h1 className="my-3 text-3xl font-semibold text-muni-navy">Your Obligation Register, in one place.</h1>
    <p className="mb-7 text-gray-600">Share your closing documents, receive a quote for each deal, and keep your candidate maps and AI skill packages together.</p>
    <Link className={primary} to={`/auth?returnTo=${encodeURIComponent(dealId ? `/register/${dealId}` : '/register')}`}>Sign in or create an account <ArrowRight size={16} className="ml-2" /></Link>
  </section>
  return <Workspace key={`${auth.user.id}:${token}:${dealId || 'list'}`} token={token} dealId={dealId} />
}

function Workspace({ token, dealId }: { token: string; dealId?: string }) {
  const { logout } = useAuth()
  const navigate = useNavigate()
  const [deals, setDeals] = useState<Deal[]>([])
  const [detail, setDetail] = useState<Detail | null>(null)
  const [operator, setOperator] = useState(false)
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')
  const [denied, setDenied] = useState(false)
  const [newDeal, setNewDeal] = useState(false)
  const [notice, setNotice] = useState('')
  const [offset, setOffset] = useState(0)
  const alive = useRef(true)

  const load = useCallback(async () => {
    const [account, value] = await Promise.all([
      registerRequest<{ operator: boolean }>(token, '/account'),
      dealId ? registerRequest<Detail>(token, `/deals/${dealId}`) : registerRequest<Deal[]>(token, `/deals?offset=${offset}`),
    ])
    if (!alive.current) return
    setOperator(account.operator)
    if (dealId) setDetail(value as Detail)
    else setDeals(value as Deal[])
  }, [token, dealId, offset])

  const fail = useCallback((e: unknown) => {
    if (!alive.current) return
    if (e instanceof RegisterError && [401, 403, 404].includes(e.status)) {
      setDetail(null); setDeals([]); setDenied(true)
    }
    setError(e instanceof Error ? e.message : 'Could not complete the request. Please try again.')
  }, [])

  useEffect(() => {
    alive.current = true
    let cancelled = false
    setBusy(true)
    load().catch(e => { if (!cancelled) fail(e) }).finally(() => { if (!cancelled) setBusy(false) })
    return () => { cancelled = true; alive.current = false }
  }, [load, fail])

  async function perform(action: () => Promise<void>) {
    if (busy) return
    setBusy(true); setError(''); setNotice('')
    try { await action() } catch (e) { fail(e) }
    finally { if (alive.current) setBusy(false) }
  }

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    await perform(async () => {
      const deal = await registerRequest<Deal>(token, '/deals', { method: 'POST', body: JSON.stringify({
        name: form.get('name'), legal_name: form.get('legal_name'), professional_contact: form.get('professional_contact'),
        bonds_already_closed: form.get('closed') === 'on', entity_type: 'private_obligated_person', privacy_consent: form.get('consent') === 'on',
      }) })
      if (alive.current) navigate(`/register/${deal.id}`)
    })
  }

  async function checkout() {
    await perform(async () => {
      const result = await registerRequest<{ url: string }>(token, `/deals/${dealId}/checkout`, { method: 'POST' })
      const url = new URL(result.url)
      if (url.protocol !== 'https:' || url.hostname !== 'checkout.stripe.com') throw new Error('Unexpected payment link. Please contact the team.')
      if (alive.current) window.location.assign(url.href)
    })
  }

  return <main className="mx-auto max-w-6xl space-y-7 pb-12 text-gray-700">
    <header className="flex flex-wrap items-end justify-between gap-5 border-b border-gray-200 pb-6">
      <div>
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.2em] text-muni-teal">Muni-Pal / {operator ? 'Register operations' : 'Client workspace'}</p>
        <h1 className="text-3xl font-semibold tracking-tight text-muni-navy">Obligation Register</h1>
        <p className="mt-2 text-sm">Your deals. Your documents. A clear next step.</p>
      </div>
      <div className="flex gap-2">
        <button className="btn-secondary" onClick={logout}>Sign out</button>
        <button disabled={busy} className="btn-secondary" onClick={() => perform(load)}><RefreshCw size={16} className="mr-2" />Refresh</button>
        {!dealId && <button disabled={busy} className={primary} onClick={() => setNewDeal(!newDeal)}><Plus size={16} className="mr-2" />New deal</button>}
      </div>
    </header>
    {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">{error} {denied && <Link to="/auth?returnTo=/register" className="underline">Sign in</Link>}</div>}
    {notice && <p role="status" className="rounded-lg bg-muni-teal/10 p-4 text-sm text-muni-navy">{notice}</p>}
    {busy && <p role="status" className="text-sm text-gray-500">Working…</p>}
    {!denied && !dealId && <>
      <section className="grid gap-4 sm:grid-cols-3" aria-label="How your register works">
        {[['01', 'Share your documents', 'Upload the closing pack or attach your shared folder.'], ['02', 'Review your quote', 'One fixed fee for this deal. Pay securely in the portal.'], ['03', 'Keep your package', 'Download candidate maps and your AI skill package.']].map(([number, title, copy]) =>
          <div key={number} className="card p-5"><span className="text-xs font-bold tracking-widest text-muni-teal">{number}</span><h2 className="mt-3 font-semibold text-muni-navy">{title}</h2><p className="mt-2 text-sm leading-6 text-gray-500">{copy}</p></div>)}
      </section>
      {newDeal && <form onSubmit={create} className="card space-y-5 p-6">
        <h2 className="text-xl font-semibold text-muni-navy">Start a deal workspace</h2>
        <div className="grid gap-5 sm:grid-cols-2">
          <Field label="Deal name"><input name="name" required minLength={2} maxLength={200} placeholder="e.g. Series 2025 Housing Bonds" className={input} /></Field>
          <Field label="Borrower / obligated person legal name"><input name="legal_name" required minLength={2} maxLength={255} className={input} /></Field>
        </div>
        <Field label="Bond counsel or dissemination agent contact"><input name="professional_contact" required minLength={2} maxLength={1000} placeholder="Name and contact details" className={input} /></Field>
        <label className="flex items-start gap-3 text-sm"><input type="checkbox" name="closed" required className="mt-1" />These bonds have already closed and this is for a private borrower or obligated person, not a municipal entity or public authority.</label>
        <label className="flex items-start gap-3 text-sm"><input type="checkbox" name="consent" required className="mt-1" />I authorize Muni-Pal to store these details and the documents I share to review this deal, provide a quote, and prepare the package.</label>
        <button disabled={busy} className={primary}>Create workspace <ArrowRight size={16} className="ml-2" /></button>
      </form>}
      <section className="card overflow-hidden">
        <div className="border-b p-5"><h2 className="font-semibold text-muni-navy">{operator ? 'Client deal inbox' : 'Your deals'}</h2></div>
        {!busy && deals.length === 0 ? <div className="px-6 py-14 text-center"><FolderOpen size={36} className="mx-auto mb-4 text-muni-teal" /><h3 className="font-semibold text-muni-navy">A home for every closing pack</h3><p className="mx-auto mt-2 max-w-sm text-sm text-gray-500">Start your first deal to share documents with the team. You can review the quote before paying.</p><button className={`${primary} mt-5`} onClick={() => setNewDeal(true)}>Start your first deal</button></div> :
          <div className="divide-y">{deals.map(deal => <Link key={deal.id} to={`/register/${deal.id}`} className="flex flex-wrap items-center justify-between gap-4 px-6 py-5 hover:bg-gray-50"><div><h3 className="font-semibold text-muni-navy">{deal.name}</h3><p className="mt-1 text-sm text-gray-500">{deal.legal_name}</p></div><div className="flex items-center gap-5 text-sm"><span className="rounded-full bg-muni-teal/10 px-3 py-1 text-muni-teal">{statusText[deal.payment_status]}</span><span>{money(deal)}</span><ArrowRight size={18} /></div></Link>)}</div>}
        {(offset > 0 || deals.length === 50) && <div className="flex justify-between border-t p-4"><button className="btn-secondary" disabled={busy || offset === 0} onClick={() => setOffset(Math.max(0, offset - 50))}>Previous</button><button className="btn-secondary" disabled={busy || deals.length < 50} onClick={() => setOffset(offset + 50)}>Next</button></div>}
      </section>
    </>}
    {!denied && detail && <>
      <Link to="/register" className="inline-flex items-center gap-2 text-sm text-muni-teal"><ArrowLeft size={15} />All deals</Link>
      <section className="flex flex-wrap justify-between gap-5 rounded-xl bg-muni-navy p-7 text-white">
        <div><p className="text-xs uppercase tracking-widest text-white/60">Deal workspace</p><h2 className="mt-2 text-2xl font-semibold">{detail.name}</h2><p className="mt-2 text-sm text-white/70">{detail.legal_name}</p></div>
        <div className="text-left sm:text-right"><span className="inline-flex rounded-full bg-white/10 px-3 py-1 text-sm">{statusText[detail.payment_status]}</span><p className="mt-3 text-lg font-semibold">{money(detail)}</p><p className="mt-1 text-xs text-white/60">Per-deal purchase</p></div>
      </section>
      {new URLSearchParams(window.location.search).get('checkout') === 'success' && detail.payment_status !== 'paid' && <p role="status" className="rounded-lg border border-muni-gold/40 bg-muni-gold/10 p-4 text-sm">We’re waiting for payment confirmation. Refresh shortly; your package unlocks after confirmation.</p>}
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-6">
          <section className="card p-6">
            <h2 className="text-lg font-semibold text-muni-navy">Source documents</h2>
            <p className="mt-2 text-sm leading-6 text-gray-500">Start with the continuing disclosure agreement, loan agreement, indenture and closing index. Add tax or regulatory agreements where available.</p>
            <label className="mt-5 flex cursor-pointer flex-col items-center rounded-xl border-2 border-dashed border-muni-teal/30 bg-muni-teal/5 p-6 text-center">
              <FolderOpen className="mb-3 text-muni-teal" size={28} /><span className="font-medium text-muni-navy">Upload closing documents</span><span className="mt-1 text-xs text-gray-500">Searchable PDF, DOCX, TXT or Markdown · 10 MB per file · 30 files / 50 MB per deal</span>
              <input aria-label="Upload closing documents" type="file" multiple accept=".pdf,.docx,.txt,.md" disabled={busy} className="mt-4 max-w-full text-sm" onChange={e => {
                const uploads = Array.from(e.target.files || []); e.target.value = ''
                perform(async () => {
                  try { for (const file of uploads) {
                    if (file.size > 10_000_000) throw new Error(`${file.name} exceeds the 10 MB limit.`)
                    const body = new FormData(); body.append('file', file)
                    await registerRequest(token, `/deals/${dealId}/documents`, { method: 'POST', body })
                  } } finally { await load() }
                  if (alive.current) setNotice('Documents saved. Your team can review the intake.')
                })
              }} />
            </label>
            <ul className="mt-5 divide-y">{detail.documents.map(doc => <li key={doc.id} className="flex items-center justify-between gap-4 py-3 text-sm"><div className="flex min-w-0 items-center gap-3"><FileText size={19} className="shrink-0 text-muni-teal" /><span className="break-all">{doc.filename}<span className="ml-2 text-xs text-gray-400">{Math.ceil(doc.size / 1024)} KB</span></span></div><button className="rounded p-2 text-muni-teal hover:bg-gray-100" disabled={busy} aria-label={`Download ${doc.filename}`} onClick={() => perform(() => downloadRegisterFile(token, `/deals/${dealId}/documents/${doc.id}`, doc.filename))}><Download size={17} /></button></li>)}</ul>
            <form className="mt-6 border-t pt-5" onSubmit={e => {
              e.preventDefault(); const form = e.currentTarget; const url = new FormData(form).get('url')
              perform(async () => { await registerRequest(token, `/deals/${dealId}/folders`, { method: 'POST', body: JSON.stringify({ url }) }); form.reset(); await load() })
            }}>
              <Field label="Or attach a shared folder"><div className="flex gap-2"><input type="url" name="url" required maxLength={2000} className={input} placeholder="Paste a shared cloud folder link" /><button disabled={busy} className="btn-secondary mt-2"><Link2 size={16} className="mr-2" />Attach</button></div></Field>
              <p className="mt-2 text-xs leading-5 text-gray-500">Google Drive, Dropbox, OneDrive, SharePoint or Box. The team imports shared files before processing; attaching a link does not connect or sync your account.</p>
            </form>
            {detail.folders.map(folder => <div key={folder.id} className="mt-4 rounded-lg border p-4 text-sm"><a href={folder.url} target="_blank" rel="noopener noreferrer" className="break-all text-muni-teal underline">{folder.url}</a><p className="mt-2 font-medium">{folder.status === 'imported' ? 'Imported by the team' : folder.status === 'access_needed' ? 'Folder access needed' : 'Awaiting team import'}</p>{folder.note && <p className="mt-1 text-gray-500">{folder.note}</p>}{operator && <FolderReview folder={folder} busy={busy} save={(status, note) => perform(async () => { await registerRequest(token, `/deals/${dealId}/folders/${folder.id}`, { method: 'PATCH', body: JSON.stringify({ status, note }) }); await load() })} />}</div>)}
          </section>
          <section className="card p-6">
            <div className="flex flex-wrap items-center justify-between gap-4"><h2 className="text-lg font-semibold text-muni-navy">Report library</h2><button disabled={busy || detail.payment_status !== 'paid' || !detail.documents.length || detail.folders.some(f => f.status !== 'imported')} className={primary} onClick={() => perform(async () => { await registerRequest(token, `/deals/${dealId}/build`, { method: 'POST' }); await load(); if (alive.current) setNotice('A new candidate package is saved in your report library.') })}>Build candidate package</button></div>
            <p className="mt-3 text-sm leading-6 text-gray-500">Each version includes a candidate map with source excerpts, the AI skill, an intake checklist and register template. The automated first pass finds duty language; use the skill and professional review to complete and approve the map.</p>
            {detail.payment_status !== 'paid' && <p className="mt-5 flex items-center gap-2 rounded-lg bg-gray-50 p-4 text-sm"><LockKeyhole size={17} />Report generation and downloads unlock when this deal is paid.</p>}
            {!detail.reports.length && detail.payment_status === 'paid' && <p className="mt-5 rounded-lg bg-gray-50 p-4 text-sm">Your library is ready. Build your first package once all source documents are here.</p>}
            <div className="mt-4 space-y-3">{detail.reports.map(report => <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-4" key={report.id}><div><h3 className="font-medium text-muni-navy">{report.kind === 'team_delivery' ? 'Team delivery' : 'Candidate package'} · Version {report.version}</h3><p className="mt-1 text-xs text-gray-500">{new Date(report.created_at).toLocaleDateString()}{report.kind !== 'team_delivery' && ` · ${report.document_count} documents · ${report.candidate_count} candidate excerpts`}</p>{report.note && <p className="mt-2 whitespace-pre-wrap text-sm text-gray-600">{report.note}</p>}</div><button disabled={busy || detail.payment_status !== 'paid'} className="btn-secondary" onClick={() => perform(() => downloadRegisterFile(token, `/deals/${dealId}/reports/${report.id}`, `obligation-package-v${report.version}.zip`))}><Download size={16} className="mr-2" />Download ZIP</button></div>)}</div>
            {operator && detail.payment_status === 'paid' && <form className="mt-6 space-y-4 border-t pt-5" onSubmit={e => {
              e.preventDefault(); const form = e.currentTarget; const body = new FormData(form)
              perform(async () => { await registerRequest(token, `/deals/${dealId}/deliveries`, { method: 'POST', body }); form.reset(); await load(); if (alive.current) setNotice('Team delivery published to the client report library.') })
            }}><h3 className="font-semibold text-muni-navy">Publish a team delivery</h3><p className="text-sm leading-6 text-gray-500">Upload reviewed engine outputs, the completed map, or the register package backed by written professional inputs.</p><Field label="Delivery ZIP"><input name="file" type="file" accept=".zip" required className={input} /></Field><Field label="Delivery note and approval reference"><textarea name="note" required minLength={3} maxLength={4000} rows={3} className={input} placeholder="What is included, what remains open, and the written approval reference for any register rows." /></Field><button disabled={busy} className={primary}>Publish to client library</button></form>}
          </section>
        </div>
        <aside className="space-y-5">
          <section className="card p-6"><h2 className="font-semibold text-muni-navy">{detail.payment_status === 'paid' ? 'Purchase confirmed' : 'Your fixed-fee quote'}</h2><p className="mt-4 text-2xl font-semibold text-muni-navy">{money(detail)}</p><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-gray-500">{detail.quote_note || 'The team reviews your document pack and confirms the scope before quoting. No payment is taken when you open a workspace.'}</p>
            {detail.payment_status === 'awaiting_payment' && !operator && <button disabled={busy} className={`${primary} mt-5 w-full`} onClick={checkout}><LockKeyhole size={15} className="mr-2" />Pay securely with Stripe</button>}
            {detail.payment_status === 'paid' && <p className="mt-4 flex items-center gap-2 text-sm text-muni-teal"><CheckCircle2 size={17} />This deal’s package is unlocked.</p>}
            {operator && !['paid', 'refunded'].includes(detail.payment_status) && <form className="mt-5 space-y-4 border-t pt-5" onSubmit={e => {
              e.preventDefault(); const form = new FormData(e.currentTarget)
              perform(async () => { await registerRequest(token, `/deals/${dealId}/quote`, { method: 'PUT', body: JSON.stringify({ amount_cents: Math.round(Number(form.get('amount')) * 100), note: form.get('note') }) }); await load(); if (alive.current) setNotice('Quote saved. The client can now pay from this workspace.') })
            }}><Field label="Quote amount (USD)"><input name="amount" type="number" min="0.50" max="100000" step="0.01" required className={input} defaultValue={detail.amount_cents ? detail.amount_cents / 100 : undefined} /></Field><Field label="Included scope and delivery terms"><textarea name="note" required minLength={3} maxLength={4000} rows={4} className={input} defaultValue={detail.quote_note || ''} /></Field><button disabled={busy || !detail.documents.length} className={primary}>Issue quote</button><p className="text-xs text-gray-500">Review imported documents before quoting. A quote locks when checkout begins.</p></form>}
          </section>
          <section className="card p-6"><h2 className="font-semibold text-muni-navy">Your professional team</h2><p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-gray-500">{detail.professional_contact}</p><p className="mt-3 text-xs leading-5 text-gray-400">Bring them the candidate map for written approval of the obligations and dates.</p></section>
          <section className="rounded-xl border border-muni-teal/20 bg-muni-teal/5 p-6"><p className="text-xs font-semibold uppercase tracking-widest text-muni-teal">Next, when you’re ready</p><h2 className="mt-3 font-semibold text-muni-navy">Put your approved register to work.</h2><p className="mt-3 text-sm leading-6 text-gray-600">You manage reminders and automation in your own tools. Ask your Muni-Pal contact about help implementing an approved schedule.</p></section>
        </aside>
      </div>
    </>}
    <footer className="border-t pt-5 text-xs leading-5 text-gray-500">Candidate maps require your professional team’s written approval. Muni-Pal does not determine compliance, calculate formula-based deadlines, file notices, or activate reminders in this workspace.</footer>
  </main>
}

function FolderReview({ folder, busy, save }: { folder: Folder; busy: boolean; save: (status: string, note: string) => void }) {
  return <form className="mt-3 space-y-2 border-t pt-3" onSubmit={e => { e.preventDefault(); const data = new FormData(e.currentTarget); save(String(data.get('status')), String(data.get('note'))) }}>
    <label className="block">Import status<select name="status" defaultValue={folder.status} className={input}><option value="awaiting_import">Awaiting import</option><option value="access_needed">Access needed</option><option value="imported">Imported</option></select></label>
    <label className="block">Client-visible import note<input name="note" required maxLength={2000} defaultValue={folder.note || ''} placeholder="Files imported or access instructions" className={input} /></label>
    <button disabled={busy} className="btn-secondary">Update folder</button>
  </form>
}
