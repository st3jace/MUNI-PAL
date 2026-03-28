import { useState, useRef, useEffect, useCallback } from 'react'
import {
  MessageSquare,
  Send,
  X,
  Loader2,
  Bot,
  User,
  RotateCcw,
  ChevronDown,
} from 'lucide-react'
import { advisorApi, type StreamEvent } from '../services/advisorApi'

// ── Types ────────────────────────────────────────────────────────────

interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  toolCalls?: { name: string; status: 'running' | 'done' }[]
}

// ── Simple Markdown Renderer ─────────────────────────────────────────

function renderMarkdown(text: string): string {
  return text
    // Code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre class="bg-gray-800 text-gray-100 rounded-md p-3 my-2 overflow-x-auto text-xs"><code>$2</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code class="bg-gray-100 text-primary-700 px-1 py-0.5 rounded text-xs font-mono">$1</code>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // Headers
    .replace(/^### (.+)$/gm, '<h4 class="font-semibold text-sm mt-3 mb-1">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 class="font-semibold text-base mt-3 mb-1">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 class="font-bold text-lg mt-3 mb-1">$1</h2>')
    // Lists
    .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc text-sm">$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal text-sm">$1</li>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr class="my-3 border-gray-200"/>')
    // Line breaks
    .replace(/\n/g, '<br/>')
}

// ── Component ────────────────────────────────────────────────────────

export default function AdvisorChat() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        "I'm your **Muni-Pal Municipal Advisor**. I can analyze deals, " +
        'search the bond corpus, run credit assessments, match banks, ' +
        'and generate reports. How can I help?',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [streamingText, setStreamingText] = useState('')
  const [activeTools, setActiveTools] = useState<
    { name: string; status: 'running' | 'done' }[]
  >([])

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const abortRef = useRef<AbortController | null>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) inputRef.current?.focus()
  }, [isOpen])

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || isLoading) return

    // Add user message
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsLoading(true)
    setStreamingText('')
    setActiveTools([])

    // Stream response
    let fullText = ''

    abortRef.current = advisorApi.chatStream(
      { message: text, session_id: sessionId || undefined },
      (event: StreamEvent) => {
        switch (event.type) {
          case 'session':
            if (event.session_id) setSessionId(event.session_id)
            break
          case 'text_delta':
            fullText += event.text || ''
            setStreamingText(fullText)
            break
          case 'tool_call':
            setActiveTools((prev) => [
              ...prev,
              { name: event.name || 'unknown', status: 'running' },
            ])
            break
          case 'tool_result':
            setActiveTools((prev) =>
              prev.map((t) =>
                t.name === event.name ? { ...t, status: 'done' } : t
              )
            )
            break
          case 'confirmation_required':
            // The confirmation text comes in text_deltas before this
            break
          case 'done': {
            const finalText = event.text || fullText
            if (finalText) {
              setMessages((prev) => [
                ...prev,
                {
                  id: `assistant-${Date.now()}`,
                  role: 'assistant',
                  content: finalText,
                  timestamp: new Date(),
                  toolCalls: activeTools.length > 0 ? [...activeTools] : undefined,
                },
              ])
            }
            setStreamingText('')
            setActiveTools([])
            setIsLoading(false)
            break
          }
          case 'error':
            setMessages((prev) => [
              ...prev,
              {
                id: `error-${Date.now()}`,
                role: 'system',
                content: `Error: ${event.message}`,
                timestamp: new Date(),
              },
            ])
            setStreamingText('')
            setIsLoading(false)
            break
        }
      },
      (error) => {
        setMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: 'system',
            content: `Connection error: ${error.message}`,
            timestamp: new Date(),
          },
        ])
        setStreamingText('')
        setIsLoading(false)
      },
      () => {
        setIsLoading(false)
      }
    )
  }, [input, isLoading, sessionId, activeTools])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewSession = () => {
    setSessionId(null)
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'New session started. How can I help?',
        timestamp: new Date(),
      },
    ])
    setStreamingText('')
    setActiveTools([])
    if (abortRef.current) abortRef.current.abort()
  }

  // ── Render ──────────────────────────────────────────────────────

  return (
    <>
      {/* Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 bg-primary-600 text-white rounded-full p-4 shadow-lg hover:bg-primary-700 transition-all hover:scale-105 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          aria-label="Open advisor chat"
        >
          <MessageSquare className="h-6 w-6" />
        </button>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-0 right-0 z-50 w-full sm:w-[420px] h-[600px] sm:h-[680px] sm:bottom-4 sm:right-4 flex flex-col bg-white rounded-t-xl sm:rounded-xl shadow-2xl border border-gray-200 overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-muni-navy text-white">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-muni-teal flex items-center justify-center">
                <Bot className="h-5 w-5 text-muni-navy" />
              </div>
              <div>
                <h3 className="font-semibold text-sm">Municipal Advisor</h3>
                <p className="text-xs text-gray-300">
                  {sessionId ? `Session: ${sessionId.slice(0, 8)}...` : 'Ready'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={handleNewSession}
                className="p-1.5 rounded hover:bg-white/10 transition-colors"
                title="New session"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded hover:bg-white/10 transition-colors"
                title="Minimize"
              >
                <ChevronDown className="h-4 w-4" />
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded hover:bg-white/10 transition-colors"
                title="Close"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4 bg-gray-50">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex gap-2 ${
                  msg.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {msg.role !== 'user' && (
                  <div className="flex-shrink-0 mt-1">
                    <div className="h-7 w-7 rounded-full bg-primary-100 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-primary-700" />
                    </div>
                  </div>
                )}
                <div
                  className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
                    msg.role === 'user'
                      ? 'bg-primary-600 text-white rounded-br-sm'
                      : msg.role === 'system'
                      ? 'bg-red-50 text-red-700 border border-red-200'
                      : 'bg-white text-gray-800 shadow-sm border border-gray-100 rounded-bl-sm'
                  }`}
                >
                  {msg.role === 'user' ? (
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <div
                      className="prose prose-sm max-w-none [&_pre]:my-1 [&_li]:my-0"
                      dangerouslySetInnerHTML={{
                        __html: renderMarkdown(msg.content),
                      }}
                    />
                  )}
                  {msg.toolCalls && msg.toolCalls.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-gray-100">
                      <p className="text-xs text-gray-400 mb-1">Tools used:</p>
                      {msg.toolCalls.map((tc, i) => (
                        <span
                          key={i}
                          className="inline-block text-xs bg-gray-50 text-gray-500 px-1.5 py-0.5 rounded mr-1 mb-1"
                        >
                          {tc.name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="flex-shrink-0 mt-1">
                    <div className="h-7 w-7 rounded-full bg-primary-600 flex items-center justify-center">
                      <User className="h-4 w-4 text-white" />
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Streaming indicator */}
            {(isLoading || streamingText) && (
              <div className="flex gap-2 justify-start">
                <div className="flex-shrink-0 mt-1">
                  <div className="h-7 w-7 rounded-full bg-primary-100 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary-700" />
                  </div>
                </div>
                <div className="max-w-[85%] rounded-xl rounded-bl-sm px-3 py-2 bg-white text-gray-800 shadow-sm border border-gray-100">
                  {/* Active tool calls */}
                  {activeTools.length > 0 && (
                    <div className="mb-2 space-y-1">
                      {activeTools.map((tc, i) => (
                        <div
                          key={i}
                          className="flex items-center gap-1.5 text-xs text-gray-500"
                        >
                          {tc.status === 'running' ? (
                            <Loader2 className="h-3 w-3 animate-spin text-primary-500" />
                          ) : (
                            <span className="text-green-500">&#10003;</span>
                          )}
                          <span>{tc.name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {streamingText ? (
                    <div
                      className="prose prose-sm max-w-none text-sm"
                      dangerouslySetInnerHTML={{
                        __html: renderMarkdown(streamingText),
                      }}
                    />
                  ) : (
                    <div className="flex items-center gap-2 text-sm text-gray-400">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span>Thinking...</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-200 bg-white px-3 py-3">
            <div className="flex items-end gap-2">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about a deal, run analysis, match banks..."
                className="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-1 focus:ring-primary-500 outline-none max-h-32"
                rows={1}
                disabled={isLoading}
                onInput={(e) => {
                  const target = e.target as HTMLTextAreaElement
                  target.style.height = 'auto'
                  target.style.height = `${Math.min(target.scrollHeight, 128)}px`
                }}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="flex-shrink-0 bg-primary-600 text-white rounded-lg p-2 hover:bg-primary-700 disabled:opacity-50 disabled:hover:bg-primary-600 transition-colors"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-1.5 text-center">
              Powered by Claude Opus 4.6 &middot; Shift+Enter for new line
            </p>
          </div>
        </div>
      )}
    </>
  )
}
