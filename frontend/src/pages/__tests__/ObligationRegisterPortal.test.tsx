import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import Portal from '../ObligationRegisterPortal'

const auth = vi.hoisted(() => ({ user: { id: 'client' } as { id: string } | null, loading: false, getAccessToken: () => 'token' }))
vi.mock('../../contexts/AuthContext', () => ({ useAuth: () => auth }))
let operator: boolean
let status: string
let deny: boolean
let reports: object[]
const deal = { id: 'deal', name: 'Series 2025', legal_name: 'Example LLC', professional_contact: 'Counsel', amount_cents: 125000, currency: 'usd', quote_note: 'One deal', quote_version: 1, created_at: '2026-09-17' }
const requests: { url: string; init?: RequestInit }[] = []

beforeEach(() => {
  auth.user = { id: 'client' }; operator = false; status = 'awaiting_payment'; deny = false; reports = []; requests.length = 0
  vi.stubGlobal('fetch', vi.fn(async (url: string, init?: RequestInit) => {
    requests.push({ url, init })
    expect((init?.headers as Record<string, string>).Authorization).toBe('Bearer token')
    expect(init?.cache).toBe('no-store')
    if (deny) return new Response('{"detail":"Not found"}', { status: 404 })
    if (url.endsWith('/account')) return new Response(JSON.stringify({ operator }))
    if (url.endsWith('/build')) { reports = [{ id: 'r1', version: 1, kind: 'candidate_package', candidate_count: 2, document_count: 1, created_at: '2026-09-17' }]; return new Response('{}') }
    if (url.endsWith('/documents')) return new Response('{}', { status: 201 })
    return new Response(JSON.stringify(url.includes('?offset=') ? [{ ...deal, payment_status: status }] : {
      ...deal, payment_status: status, documents: [{ id: 'doc', filename: 'CDA.txt', size: 500 }], folders: [], reports,
    }))
  }))
})
afterEach(() => { cleanup(); vi.unstubAllGlobals() })

function mount(path = '/register/deal') {
  return render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/register" element={<Portal />} /><Route path="/register/:dealId" element={<Portal />} /></Routes></MemoryRouter>)
}

it('requires sign-in and preserves the requested deal', () => {
  auth.user = null; mount()
  expect(screen.getByRole('link', { name: /Sign in or create/ })).toHaveAttribute('href', '/auth?returnTo=%2Fregister%2Fdeal')
  expect(requests).toHaveLength(0)
})

it('shows per-deal payment and locks report generation', async () => {
  mount()
  expect(await screen.findByText('Series 2025')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Build candidate package' })).toBeDisabled()
  expect(screen.getByRole('button', { name: /Pay securely/ })).toBeEnabled()
  expect(screen.queryByRole('button', { name: 'Issue quote' })).not.toBeInTheDocument()
})

it('builds and reloads a paid report version', async () => {
  status = 'paid'; mount()
  fireEvent.click(await screen.findByRole('button', { name: 'Build candidate package' }))
  expect(await screen.findByText('Candidate package · Version 1')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Download ZIP' })).toBeEnabled()
  expect(requests.some(x => x.url.endsWith('/build') && x.init?.method === 'POST')).toBe(true)
})

it('uploads real multipart files without a fabricated content type', async () => {
  mount(); const control = await screen.findByLabelText('Upload closing documents')
  fireEvent.change(control, { target: { files: [new File(['The Borrower shall deliver a report.'], 'CDA.txt', { type: 'text/plain' })] } })
  await waitFor(() => expect(requests.some(x => x.url.endsWith('/documents'))).toBe(true))
  const request = requests.find(x => x.url.endsWith('/documents'))!
  expect(request.init?.body).toBeInstanceOf(FormData)
  expect((request.init?.headers as Record<string, string>)['Content-Type']).toBeUndefined()
})

it('clears client records after an authorization failure', async () => {
  mount(); await screen.findByText('Series 2025'); deny = true
  fireEvent.click(screen.getByRole('button', { name: 'Refresh' }))
  await screen.findByRole('alert')
  expect(screen.queryByText('Series 2025')).not.toBeInTheDocument()
  expect(screen.queryByText('CDA.txt')).not.toBeInTheDocument()
})

it('exposes quoting only to the server-authorized operator', async () => {
  operator = true; mount()
  expect(await screen.findByRole('button', { name: 'Issue quote' })).toBeEnabled()
  expect(screen.queryByRole('button', { name: /Pay securely/ })).not.toBeInTheDocument()
})

it('preserves the library across page reloads', async () => {
  status = 'paid'; reports = [{ id: 'r1', version: 3, kind: 'team_delivery', note: 'Approved inputs reference 1', created_at: '2026-09-17' }]
  const page = mount(); await screen.findByText('Team delivery · Version 3'); page.unmount()
  mount(); expect(await screen.findByText('Team delivery · Version 3')).toBeInTheDocument()
  expect(screen.getByText('Approved inputs reference 1')).toBeInTheDocument()
})
