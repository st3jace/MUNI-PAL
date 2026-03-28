/**
 * Advisor API client — communicates with the Municipal Advisor engine.
 *
 * Supports both synchronous chat and SSE streaming.
 */
import axios from 'axios'

const BASE = '/advisor-api'

const client = axios.create({ baseURL: BASE })

// ── Types ────────────────────────────────────────────────────────────

export interface ChatRequest {
  message: string
  session_id?: string
}

export interface ChatResponse {
  session_id: string
  response: string
  message_count: number
}

export interface SessionInfo {
  session_id: string
  created_at: string | null
  updated_at: string | null
  message_count: number
  metadata: Record<string, unknown>
}

export interface StreamEvent {
  type:
    | 'session'
    | 'text_delta'
    | 'tool_call'
    | 'tool_result'
    | 'confirmation_required'
    | 'done'
    | 'error'
  session_id?: string
  text?: string
  name?: string
  input?: Record<string, unknown>
  summary?: string
  tool?: string
  message?: string
}

// ── API Functions ────────────────────────────────────────────────────

export const advisorApi = {
  /** Non-streaming chat (returns complete response). */
  async chat(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await client.post<ChatResponse>('/chat', request)
    return data
  },

  /** Streaming chat via SSE. Returns an EventSource-like reader. */
  chatStream(
    request: ChatRequest,
    onEvent: (event: StreamEvent) => void,
    onError?: (error: Error) => void,
    onDone?: () => void
  ): AbortController {
    const controller = new AbortController()

    fetch(`${BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }

        const reader = response.body?.getReader()
        if (!reader) throw new Error('No response body')

        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            const trimmed = line.trim()
            if (!trimmed.startsWith('data: ')) continue

            try {
              const event: StreamEvent = JSON.parse(trimmed.slice(6))
              onEvent(event)

              if (event.type === 'done' || event.type === 'error') {
                onDone?.()
              }
            } catch {
              // Skip malformed events
            }
          }
        }

        onDone?.()
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          onError?.(err)
        }
      })

    return controller
  },

  /** List saved sessions. */
  async listSessions(limit = 20): Promise<SessionInfo[]> {
    const { data } = await client.get<SessionInfo[]>('/sessions', {
      params: { limit },
    })
    return data
  },

  /** Get session history. */
  async getSession(sessionId: string): Promise<Record<string, unknown>> {
    const { data } = await client.get(`/sessions/${sessionId}`)
    return data
  },

  /** Delete a session. */
  async deleteSession(sessionId: string): Promise<void> {
    await client.delete(`/sessions/${sessionId}`)
  },

  /** Health check. */
  async health(): Promise<Record<string, string>> {
    const { data } = await client.get('/health')
    return data
  },
}
