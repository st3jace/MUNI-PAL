/**
 * Auth context — JWT-based authentication with token persistence.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'

const API_URL = ''  // Relative paths — Vercel/vite proxy rewrites to backend

interface User {
  id: string
  email: string
  full_name: string | null
  organization: string | null
  subscription_tier: string | null
  is_active: boolean
}

interface Tokens {
  access_token: string
  refresh_token: string
  expires_in: number
}

interface AuthState {
  user: User | null
  loading: boolean
  error: string | null
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<void>
  register: (
    email: string,
    password: string,
    fullName?: string,
    organization?: string,
  ) => Promise<void>
  logout: () => void
  getAccessToken: () => string | null
  isSubscribed: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

const TOKEN_KEY = 'munipal_tokens'

function loadTokens(): Tokens | null {
  try {
    const raw = localStorage.getItem(TOKEN_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveTokens(tokens: Tokens) {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens))
}

function clearTokens() {
  localStorage.removeItem(TOKEN_KEY)
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  })
  const [tokens, setTokens] = useState<Tokens | null>(loadTokens)

  const fetchProfile = useCallback(async (accessToken: string) => {
    const res = await fetch(`${API_URL}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
    if (!res.ok) throw new Error('Failed to load profile')
    return (await res.json()) as User
  }, [])

  // Bootstrap — load profile from stored tokens
  useEffect(() => {
    if (!tokens) {
      setState({ user: null, loading: false, error: null })
      return
    }
    fetchProfile(tokens.access_token)
      .then((user) => setState({ user, loading: false, error: null }))
      .catch(() => {
        clearTokens()
        setTokens(null)
        setState({ user: null, loading: false, error: null })
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Proactive token refresh — refresh 2 minutes before expiry
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
    if (!tokens?.refresh_token || !tokens.expires_in) return

    // Refresh 2 minutes before expiry (minimum 10s from now)
    const refreshMs = Math.max((tokens.expires_in - 120) * 1000, 10_000)

    refreshTimerRef.current = setTimeout(async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: tokens.refresh_token }),
        })
        if (!res.ok) throw new Error('Refresh failed')
        const newTokens: Tokens = await res.json()
        saveTokens(newTokens)
        setTokens(newTokens)
      } catch {
        // Refresh failed — clear session so user re-authenticates
        clearTokens()
        setTokens(null)
        setState({ user: null, loading: false, error: null })
      }
    }, refreshMs)

    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
    }
  }, [tokens]) // re-arm whenever tokens change

  const login = useCallback(async (email: string, password: string) => {
    setState((s) => ({ ...s, loading: true, error: null }))
    try {
      const res = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Login failed')
      }
      const newTokens: Tokens = await res.json()
      saveTokens(newTokens)
      setTokens(newTokens)
      const user = await fetchProfile(newTokens.access_token)
      setState({ user, loading: false, error: null })
    } catch (e: any) {
      setState({ user: null, loading: false, error: e.message })
      throw e
    }
  }, [fetchProfile])

  const register = useCallback(
    async (
      email: string,
      password: string,
      fullName?: string,
      organization?: string,
    ) => {
      setState((s) => ({ ...s, loading: true, error: null }))
      try {
        const res = await fetch(`${API_URL}/api/v1/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email,
            password,
            full_name: fullName || null,
            organization: organization || null,
          }),
        })
        if (!res.ok) {
          const err = await res.json().catch(() => ({}))
          throw new Error(err.detail || 'Registration failed')
        }
        const newTokens: Tokens = await res.json()
        saveTokens(newTokens)
        setTokens(newTokens)
        const user = await fetchProfile(newTokens.access_token)
        setState({ user, loading: false, error: null })
      } catch (e: any) {
        setState({ user: null, loading: false, error: e.message })
        throw e
      }
    },
    [fetchProfile],
  )

  const logout = useCallback(() => {
    clearTokens()
    setTokens(null)
    setState({ user: null, loading: false, error: null })
  }, [])

  const getAccessToken = useCallback(() => tokens?.access_token ?? null, [tokens])

  const isSubscribed = state.user?.subscription_tier === 'subscription' ||
    state.user?.subscription_tier === 'per_project'

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      register,
      logout,
      getAccessToken,
      isSubscribed,
    }),
    [state, login, register, logout, getAccessToken, isSubscribed],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
