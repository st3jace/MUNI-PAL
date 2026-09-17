import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import AskNavigation from '../AskNavigation'

const auth = vi.hoisted(() => ({ user: null as { id: string } | null }))
vi.mock('../../contexts/AuthContext', () => ({ useAuth: () => auth }))
afterEach(cleanup)

it('provides a website navigation entry for signed-in users', () => {
  auth.user = { id: 'owner' }
  render(<MemoryRouter><AskNavigation /></MemoryRouter>)
  expect(screen.getByRole('link', { name: 'Ask where it is' })).toHaveAttribute('href', '/ask')
})
it('does not show private navigation when signed out', () => {
  auth.user = null
  render(<MemoryRouter><AskNavigation /></MemoryRouter>)
  expect(screen.queryByRole('link', { name: 'Ask where it is' })).not.toBeInTheDocument()
})
