import { cleanup, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, expect, it, vi } from 'vitest'
import Layout from '../Layout'

vi.mock('@tanstack/react-query', () => ({ useQuery: () => ({ data: undefined }) }))
vi.mock('../../contexts/AuthContext', () => ({ useAuth: () => ({ user: { id: 'owner' } }) }))
vi.mock('../../services/api', () => ({ api: { getProject: vi.fn() } }))
vi.mock('../AdvisorChat', () => ({ default: () => <button>Legacy advisor chat</button> }))

afterEach(cleanup)

function renderAt(path: string) {
  render(<MemoryRouter initialEntries={[path]}>
    <Routes>
      <Route element={<Layout />}>
        <Route path="*" element={<p>Page content</p>} />
      </Route>
    </Routes>
  </MemoryRouter>)
}

it('does not render the legacy advisor on the trailing-slash Ask route', () => {
  renderAt('/ask/')
  expect(screen.queryByRole('button', { name: 'Legacy advisor chat' })).not.toBeInTheDocument()
})

it('does not render the legacy advisor on the exact Ask route', () => {
  renderAt('/ask')
  expect(screen.queryByRole('button', { name: 'Legacy advisor chat' })).not.toBeInTheDocument()
})

it('keeps the legacy advisor on non-Ask portal routes', () => {
  renderAt('/dashboard')
  expect(screen.getByRole('button', { name: 'Legacy advisor chat' })).toBeInTheDocument()
})