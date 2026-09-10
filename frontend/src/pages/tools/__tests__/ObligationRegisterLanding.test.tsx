import { MemoryRouter } from 'react-router-dom'
import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ObligationRegisterLanding from '../ObligationRegisterLanding'

function renderPage() {
  return render(
    <MemoryRouter>
      <ObligationRegisterLanding />
    </MemoryRouter>
  )
}

describe('Obligation Register landing page', () => {
  it('shows headline B and sub-headline A1 with the ten-day tweak', () => {
    renderPage()
    expect(
      screen.getByRole('heading', { level: 1, name: /post-close obligation book your counsel can work from/i })
    ).toBeInTheDocument()
    expect(screen.getByText(/in ten business days\. you, or your dissemination agent, file\./i)).toBeInTheDocument()
  })

  it('carries the Arthur control sentence verbatim and only four status codes', () => {
    const { container } = renderPage()
    expect(
      screen.getByText(/Launch Shop does not independently decide which undertaking controls/i)
    ).toBeInTheDocument()
    const codes = Array.from(container.querySelectorAll('code')).map((c) => c.textContent)
    expect(codes).toEqual(['filed', 'not filed', 'evidence missing', 'not testable'])
    expect(container.textContent).not.toMatch(/professional determination required/i)
  })

  it('never prints a price, a claim number, or the word compliant', () => {
    const { container } = renderPage()
    const text = container.textContent ?? ''
    expect(text).not.toMatch(/\$\s?\d/)
    expect(text).not.toMatch(/\b866\b/)
    expect(text).not.toMatch(/compliant/i)
    expect(text).not.toMatch(/bond-ready/i)
  })

  it('stops the form when the bonds have not closed', () => {
    renderPage()
    fireEvent.click(screen.getByRole('radio', { name: /^no$/i }))
    expect(screen.getByRole('alert')).toHaveTextContent(/post-close obligated persons only/i)
    expect(screen.queryByLabelText(/legal name/i)).not.toBeInTheDocument()
  })

  it('stops the form for a municipal entity after the gate', () => {
    renderPage()
    fireEvent.click(screen.getByRole('radio', { name: /^yes$/i }))
    fireEvent.change(screen.getByRole('combobox', { name: /entity type/i }), { target: { value: 'municipal_entity' } })
    expect(screen.getByRole('alert')).toHaveTextContent(/no path for municipal entities/i)
    expect(screen.queryByLabelText(/^email$/i)).not.toBeInTheDocument()
  })

  it('opens the full form for a private obligated person', () => {
    renderPage()
    fireEvent.click(screen.getByRole('radio', { name: /^yes$/i }))
    fireEvent.change(screen.getByRole('combobox', { name: /entity type/i }), { target: { value: 'private_obligated_person' } })
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/series or instruments already closed/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /request fixed-fee quote/i })).toBeDisabled()
  })
})
