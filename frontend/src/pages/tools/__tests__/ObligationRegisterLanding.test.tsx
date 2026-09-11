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
      screen.getByText(/Muni-Pal does not independently decide which undertaking controls/i)
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

  it('states registration status as a fact, never a legal conclusion about the activity', () => {
    const { container } = renderPage()
    const text = container.textContent ?? ''
    expect(text).toMatch(/not a registered municipal advisor, broker-dealer, or law firm/i)
    expect(text).not.toMatch(/as defined under Section 15B/i)
  })

  it('states the guarantee in the letter §6.9 terms, with fine print that never contradicts the big line', () => {
    const { container } = renderPage()
    const text = container.textContent ?? ''
    expect(text).toMatch(/money back for each late business day/i)
    expect(text).toMatch(/by business day 20, you can end it and get the full fee back/i)
    expect(text).toMatch(/terms apply/i)
    expect(text).toMatch(/2% of the fee, up to 20%/i)
    expect(text).not.toMatch(/within 10 business days of a complete drop, we refund the fee in full/i)
  })

  it('stops the form when the bonds have not closed', () => {
    renderPage()
    fireEvent.click(screen.getByRole('radio', { name: /^no$/i }))
    expect(screen.getByRole('alert')).toHaveTextContent(/only for private borrowers whose bonds have already closed/i)
    expect(screen.queryByLabelText(/legal name/i)).not.toBeInTheDocument()
  })

  it('stops the form for a municipal entity after the gate', () => {
    renderPage()
    fireEvent.click(screen.getByRole('radio', { name: /^yes$/i }))
    fireEvent.change(screen.getByRole('combobox', { name: /entity type/i }), { target: { value: 'municipal_entity' } })
    expect(screen.getByRole('alert')).toHaveTextContent(/no path for cities, districts, or other public bodies/i)
    expect(screen.queryByLabelText(/^email$/i)).not.toBeInTheDocument()
  })

  it('opens the full form for a private obligated person', () => {
    renderPage()
    fireEvent.click(screen.getByRole('radio', { name: /^yes$/i }))
    fireEvent.change(screen.getByRole('combobox', { name: /entity type/i }), { target: { value: 'private_obligated_person' } })
    expect(screen.getByLabelText(/^email$/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/bond issues that have already closed/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /request fixed-fee quote/i })).toBeDisabled()
  })
})
