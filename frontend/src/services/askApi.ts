import type { components } from '../types/openapi.generated'

export type Conversation = components['schemas']['AskConversationRead']
export type History = components['schemas']['AskHistory']
export type Scope = components['schemas']['AskScope']
export type Citation = components['schemas']['AskCitation']

export class AskError extends Error {
  constructor(public status: number, public code?: string) {
    super('Could not complete the request. Please try again.')
  }
}

export async function askRequest<T>(token: string, path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`/api/v1/ask${path}`, {
    method, cache: 'no-store',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new AskError(response.status, error.detail?.code)
  }
  return response.status === 204 ? undefined as T : response.json()
}
