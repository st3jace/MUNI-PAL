const API = import.meta.env.VITE_API_URL || ''

export interface Deal {
  id: string; name: string; legal_name: string; professional_contact: string
  payment_status: 'awaiting_quote' | 'awaiting_payment' | 'paid' | 'refunded'
  amount_cents: number | null; currency: string; quote_note: string | null
  quote_version: number; created_at: string
}
export interface Source { id: string; filename: string; size: number; sha256: string; created_at: string }
export interface Folder { id: string; url: string; status: string; note: string | null }
export interface Report { id: string; version: number; kind: string; note: string | null; candidate_count: number; document_count: number; created_at: string }
export interface Detail extends Deal { documents: Source[]; folders: Folder[]; reports: Report[] }

export class RegisterError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

export async function registerRequest<T>(token: string, path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API}/api/v1/register${path}`, {
    ...init, cache: 'no-store', headers: {
      ...(init.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...init.headers, Authorization: `Bearer ${token}`,
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new RegisterError(response.status, typeof body.detail === 'string' ? body.detail :
      response.status === 401 ? 'Please sign in again.' : 'This workspace is not available to your account.')
  }
  return response.json()
}

export async function downloadRegisterFile(token: string, path: string, filename: string) {
  const response = await fetch(`${API}/api/v1/register${path}`, {
    cache: 'no-store', headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) throw new RegisterError(response.status, 'The download is not available. Refresh the deal and try again.')
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; a.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
