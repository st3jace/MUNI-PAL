import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function AskNavigation() {
  const { user } = useAuth()
  if (!user) return null
  return <nav aria-label="Account tools" className="mx-auto mb-5 flex max-w-6xl flex-wrap gap-5 text-sm">
    <Link to="/" className="text-gray-600 underline">Home</Link>
    <Link to="/ask" className="font-medium text-blue-800 underline">Ask where it is</Link>
    <Link to="/pricing" className="text-gray-600 underline">Subscription</Link>
  </nav>
}
