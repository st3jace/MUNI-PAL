/**
 * Combined login/register page for Muni-Pal.
 */

import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { ArrowRight, ChevronLeft, AlertCircle } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function AuthPage() {
  const [searchParams] = useSearchParams()
  const defaultMode = searchParams.get('mode') === 'register' ? 'register' : 'login'
  const returnTo = searchParams.get('returnTo') || '/pricing'

  const [mode, setMode] = useState<'login' | 'register'>(defaultMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [organization, setOrganization] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)

    try {
      if (mode === 'login') {
        await login(email, password)
      } else {
        if (password.length < 8) {
          setError('Password must be at least 8 characters.')
          setSubmitting(false)
          return
        }
        await register(email, password, fullName, organization)
      }
      navigate(returnTo)
    } catch (err: any) {
      setError(err.message || 'Something went wrong.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-md mx-auto">
      <Link
        to="/"
        className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-muni-navy mb-8 transition-colors"
      >
        <ChevronLeft className="h-4 w-4" />
        Back to Home
      </Link>

      <div className="flex items-center gap-3 mb-6">
        <img
          src="/muni-pal-emblem.png"
          alt="Muni-Pal"
          className="h-10 w-10 rounded-xl object-contain"
        />
        <h1 className="text-xl font-bold text-gray-900">
          {mode === 'login' ? 'Sign In' : 'Create Account'}
        </h1>
      </div>

      {error && (
        <div className="mb-4 flex items-start gap-2 bg-red-50 text-red-700 text-sm rounded-lg p-3 border border-red-100">
          <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {mode === 'register' && (
          <>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-muni-teal"
                placeholder="Jane Smith"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Organization
              </label>
              <input
                type="text"
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-muni-teal"
                placeholder="Community Hospital of Springfield"
              />
            </div>
          </>
        )}

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Email
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-muni-teal"
            placeholder="cfo@hospital.org"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Password
          </label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-muni-teal"
            placeholder={mode === 'register' ? 'At least 8 characters' : ''}
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full inline-flex items-center justify-center gap-2 bg-muni-navy hover:bg-[#15304d] text-white font-semibold px-4 py-2.5 rounded-lg transition-colors text-sm disabled:opacity-60"
        >
          {submitting
            ? 'Please wait...'
            : mode === 'login'
              ? 'Sign In'
              : 'Create Account'}
          {!submitting && <ArrowRight className="h-4 w-4" />}
        </button>
      </form>

      <div className="mt-6 text-center text-sm text-gray-500">
        {mode === 'login' ? (
          <>
            No account?{' '}
            <button
              onClick={() => { setMode('register'); setError(null) }}
              className="text-muni-teal font-semibold hover:underline"
            >
              Create one
            </button>
          </>
        ) : (
          <>
            Already have an account?{' '}
            <button
              onClick={() => { setMode('login'); setError(null) }}
              className="text-muni-teal font-semibold hover:underline"
            >
              Sign in
            </button>
          </>
        )}
      </div>

      <p className="mt-8 text-[11px] text-gray-400 text-center">
        By continuing, you agree to Muni-Pal's terms of service.
        Your data is used solely for bond readiness and advisory services.
      </p>
    </div>
  )
}
