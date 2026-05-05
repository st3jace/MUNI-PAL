import { MemoryRouter } from 'react-router-dom'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SensingProvider } from '../../../contexts/SensingContext'
import ToolsHub from '../ToolsHub'
import PilotNavigation from '../PilotNavigation'

function renderWithProviders(ui: React.ReactElement) {
  return render(
    <MemoryRouter>
      <SensingProvider>{ui}</SensingProvider>
    </MemoryRouter>
  )
}

describe('Pilot Navigation sensing tool', () => {
  it('surfaces Pilot Navigation from the sensing tools hub', () => {
    renderWithProviders(<ToolsHub />)

    const link = screen.getByRole('link', { name: /pilot navigation/i })

    expect(link).toHaveAttribute('href', '/tools/pilot-navigation')
    expect(
      screen.getByText(/lead capture to pilot qualification/i)
    ).toBeInTheDocument()
  })

  it('explains the prospect-safe lead-to-pilot path and gates', () => {
    renderWithProviders(<PilotNavigation />)

    expect(
      screen.getByRole('heading', { name: /pilot navigation/i })
    ).toBeInTheDocument()
    expect(screen.getAllByText(/lead capture/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/pilot qualification/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/bfms project creation/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/pilot onboarding/i).length).toBeGreaterThan(0)

    expect(screen.getAllByText(/registered ma confirmed/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/pilot smoke test green/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/engagement scope signed/i).length).toBeGreaterThan(0)

    expect(screen.getByText(/healthcare is the primary/i)).toBeInTheDocument()
    expect(screen.getByText(/housing is pilot-stage/i)).toBeInTheDocument()
    expect(screen.getByText(/ucs\/wte remains supported/i)).toBeInTheDocument()

    expect(screen.getByText(/not deal approval/i)).toBeInTheDocument()
    expect(screen.getByText(/not municipal advisory advice/i)).toBeInTheDocument()
  })
})
