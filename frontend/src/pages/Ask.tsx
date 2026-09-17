import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { AskError, askRequest, type Citation, type Conversation, type History, type Scope } from '../services/askApi'

const button = 'rounded-md border border-gray-300 px-3 py-2 text-sm font-medium hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-700'

export default function Ask() {
  const auth = useAuth()
  if (auth.loading) return <p role="status">Checking your account…</p>
  const token = auth.getAccessToken()
  if (!auth.user || !token) return <SignIn />
  // Changing identity discards all private UI state and ignores outstanding responses.
  return <AskWorkspace key={`${auth.user.id}:${token}`} token={token} />
}

function SignIn() {
  return <section><h1 className="text-2xl font-semibold">Ask where it is</h1>
    <p className="my-4">Sign in to search your project records.</p>
    <Link className="text-blue-700 underline" to="/auth?returnTo=/ask">Sign in</Link></section>
}

function AskWorkspace({ token }: { token: string }) {
  const [scopes, setScopes] = useState<Scope[]>([])
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [history, setHistory] = useState<History | null>(null)
  const [project, setProject] = useState('')
  const [document, setDocument] = useState('')
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(true)
  const [error, setError] = useState('')
  const [gate, setGate] = useState('')
  const [retry, setRetry] = useState(0)
  const [source, setSource] = useState<Citation | null>(null)
  const [more, setMore] = useState(false)
  const alive = useRef(true)
  const historyLog = useRef<HTMLDivElement>(null)

  const fail = useCallback((e: unknown) => {
    if (e instanceof AskError && (e.status === 401 || e.status === 403)) {
      setHistory(null); setConversations([]); setScopes([]); setSource(null); setDraft('')
      setGate(e.status === 401 ? 'signin' : e.code === 'subscription_required' ? 'upgrade' : 'inactive')
    } else {
      if (e instanceof AskError && e.status === 404) { setHistory(null); setSource(null) }
      setError(e instanceof AskError && e.status === 404
      ? 'This conversation or source is no longer available.'
      : e instanceof AskError && e.status === 409
        ? 'This conversation is full. Start a new chat.'
        : 'Could not complete the request. Please try again. If sending failed, reload the chat before retrying to check whether it was saved.')
    }
  }, [])

  useEffect(() => {
    alive.current = true
    let cancelled = false
    setBusy(true); setError('')
    Promise.all([
      askRequest<Scope[]>(token, '/scopes'),
      askRequest<Conversation[]>(token, '/conversations'),
    ]).then(([nextScopes, chats]) => {
      if (!cancelled) { setScopes(nextScopes); setConversations(chats); setMore(chats.length === 50) }
    }).catch(e => { if (!cancelled) fail(e) })
      .finally(() => { if (!cancelled) setBusy(false) })
    return () => { cancelled = true; alive.current = false }
  }, [token, retry, fail])

  useEffect(() => {
    const log = historyLog.current
    if (log) log.scrollTop = log.scrollHeight
  }, [history?.messages.length])

  async function perform(action: () => Promise<void>) {
    if (busy) return
    setBusy(true); setError('')
    try { await action() } catch (e) { if (alive.current) fail(e) }
    finally { if (alive.current) setBusy(false) }
  }

  async function openConversation(id: string) {
    setHistory(null); setSource(null); setDraft('')
    await perform(async () => {
      const next = await askRequest<History>(token, `/conversations/${id}`)
      if (alive.current) setHistory(next)
    })
  }

  if (gate === 'signin') return <SignIn />
  if (gate === 'upgrade') return <section><h1 className="text-2xl font-semibold">Ask where it is</h1>
    <p className="my-4">An active paid subscription is required to access your conversations and search records.</p>
    <Link to="/pricing" className="text-blue-700 underline">View plans</Link></section>
  if (gate === 'inactive') return <p role="alert">Your account is inactive. Contact your account administrator.</p>

  return <section aria-labelledby="ask-title" className="mx-auto max-w-6xl min-w-0">
    <header className="mb-6"><p className="text-xs uppercase tracking-widest text-blue-800">Your records, with evidence</p>
      <h1 id="ask-title" className="mt-2 text-3xl font-semibold text-gray-900">Ask where it is</h1>
      <p className="mt-2 max-w-3xl text-gray-600">Find exact excerpts in your project documents. Ask for a record, such as “annual report” or “listed events”. Judgment and deadline calculations are refused and recorded here.</p>
    </header>
    {error && <div role="alert" className="mb-4 rounded border border-red-300 bg-red-50 p-3 text-red-900">{error}
      <button className={`${button} ml-3`} disabled={busy} onClick={() => setRetry(n => n + 1)}>Reload conversations</button></div>}
    {busy && <p role="status" className="mb-3 text-sm text-gray-600">Loading…</p>}
    <div className="grid min-w-0 gap-5 md:grid-cols-[16rem_minmax(0,1fr)]" aria-busy={busy}>
      <aside aria-label="Conversations" className="min-w-0 rounded-xl border border-gray-200 bg-white p-4">
        <h2 className="mb-3 font-semibold">Conversations</h2>
        <label htmlFor="ask-project" className="block text-sm font-medium">Project</label>
        <select id="ask-project" className="my-2 w-full rounded border p-2" value={project} disabled={busy}
          onChange={e => { setProject(e.target.value); setDocument('') }}>
          <option value="">Choose a project</option>{scopes.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <label htmlFor="ask-document" className="block text-sm font-medium">Document</label>
        <select id="ask-document" className="my-2 w-full rounded border p-2" value={document} disabled={busy || !project}
          onChange={e => setDocument(e.target.value)}><option value="">All project documents</option>
          {scopes.find(s => s.id === project)?.documents.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
        <button className={`${button} mb-4 w-full`} disabled={busy || !project} onClick={() => perform(async () => {
          const chat = await askRequest<Conversation>(token, '/conversations', 'POST', { project_id: project, artifact_id: document || null })
          if (alive.current) { setConversations(c => [chat, ...c]); setHistory({ ...chat, messages: [] }); setDraft(''); setSource(null) }
        })}>New chat</button>
        {!busy && !scopes.length && <p className="text-sm text-gray-600">No owned projects available. Ask searches documents already added to your project workspace.</p>}
        {!conversations.length && <p className="text-sm text-gray-500">No conversations yet.</p>}
        <ul className="max-h-72 space-y-2 overflow-y-auto md:max-h-[32rem]">{conversations.map(c => <li key={c.id}>
          <button className={`${button} w-full text-left break-words ${history?.id === c.id ? 'bg-blue-50 border-blue-400' : ''}`}
            aria-current={history?.id === c.id ? 'true' : undefined} disabled={busy} onClick={() => openConversation(c.id)}>
            {c.title}<time className="mt-1 block text-xs text-gray-500" dateTime={c.updated_at}>{new Date(c.updated_at).toLocaleDateString()}</time>
          </button></li>)}</ul>
        {more && <button className={`${button} mt-2`} disabled={busy} onClick={() => perform(async () => {
          const chats = await askRequest<Conversation[]>(token, `/conversations?offset=${conversations.length}`)
          if (alive.current) { setConversations(c => [...c, ...chats]); setMore(chats.length === 50) }
        })}>Load older chats</button>}
      </aside>
      <div className="min-w-0 rounded-xl border border-gray-200 bg-white p-4 sm:p-6">
        {!history ? <div className="py-12 text-center text-gray-600"><h2 className="text-xl font-medium">Find the source</h2>
          <p className="mt-3">Choose a project and start a chat, or open a saved conversation.</p></div> : <>
          <div className="mb-5 flex flex-wrap items-start justify-between gap-3 border-b pb-4">
            <div className="min-w-0"><h2 className="break-words font-semibold">{history.title}</h2>
              <p className="text-sm text-gray-600">{scopes.find(s => s.id === history.project_id)?.name || 'Project records'} · {history.artifact_id ? scopes.flatMap(s => s.documents).find(d => d.id === history.artifact_id)?.name || 'Selected document' : 'All project documents'}</p>
              <p className="mt-1 text-xs text-gray-500">Scope is fixed for this chat. Start a new chat to change it.</p></div>
            <button className={button} disabled={busy} onClick={() => perform(async () => {
              await askRequest(token, `/conversations/${history.id}`, 'DELETE')
              if (alive.current) { setConversations(c => c.filter(v => v.id !== history.id)); setHistory(null); setSource(null) }
            })}>Delete chat</button>
          </div>
          <div ref={historyLog} role="log" aria-label="Message history" aria-live="polite" className="max-h-[55vh] space-y-5 overflow-y-auto break-words">
            {!history.messages.length && <p className="py-6 text-gray-500">No messages yet. What record are you looking for?</p>}
            {history.messages.map(m => <article key={m.id} className={`rounded-lg p-4 ${m.role === 'user' ? 'bg-gray-100' : m.kind === 'refusal' ? 'border border-amber-300 bg-amber-50' : 'bg-blue-50'}`}>
              <h3 className="mb-2 text-sm font-semibold">{m.role === 'user' ? 'You' : m.kind === 'refusal' ? 'Judgment question refused' : 'Source lookup'}</h3>
              <p className="whitespace-pre-wrap">{m.content}</p>
              {m.citations.map(c => <div key={c.chunk_id} className="mt-3 min-w-0 rounded border bg-white p-3">
                <p className="font-medium">{c.document_name}</p><p className="text-sm text-gray-600">{c.locator}</p>
                <blockquote className="my-3 whitespace-pre-wrap border-l-2 border-blue-300 pl-3 text-sm">{c.excerpt}</blockquote>
                <button className={button} disabled={busy} aria-label={`View source: ${c.document_name}`} onClick={() => perform(async () => {
                  const next = await askRequest<Citation>(token, `/sources/${encodeURIComponent(c.chunk_id)}`)
                  if (alive.current) setSource(next)
                })}>View source</button>
                <p className="mt-2 break-all text-xs text-gray-500">Source ID: {c.chunk_id}</p>
              </div>)}
            </article>)}
          </div>
          {source && <section aria-label="Source excerpt" className="my-4 rounded border border-blue-300 p-4">
            <h3 className="font-semibold">{source.document_name} · {source.locator}</h3>
            <blockquote className="my-3 whitespace-pre-wrap break-words text-sm">{source.excerpt}</blockquote>
            <button className={button} onClick={() => setSource(null)}>Close source</button></section>}
          <form className="mt-5 border-t pt-4" onSubmit={e => { e.preventDefault(); if (!draft.trim()) return; perform(async () => {
            const next = await askRequest<History>(token, `/conversations/${history.id}/messages`, 'POST', { question: draft.trim() })
            if (alive.current) { setHistory(next); setDraft(''); setConversations(c => [next, ...c.filter(v => v.id !== next.id)]) }
          }) }}>
            <label htmlFor="ask-question" className="font-medium">Question</label>
            <textarea id="ask-question" value={draft} maxLength={2000} rows={3} disabled={busy} required
              aria-describedby="ask-limit" className="mt-2 w-full resize-y rounded border p-3" placeholder="Where is the annual reporting clause?"
              onChange={e => setDraft(e.target.value)} />
            <div className="mt-2 flex flex-wrap items-center justify-between gap-2"><p id="ask-limit" className="text-xs text-gray-500">{draft.length}/2,000 characters · Saved to this account</p>
              <button className={`${button} bg-blue-50`} disabled={busy || !draft.trim()} type="submit">Send question</button></div>
          </form>
        </>}
      </div>
    </div>
  </section>
}
