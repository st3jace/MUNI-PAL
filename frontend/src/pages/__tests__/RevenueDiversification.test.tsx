import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RevenueDiversification from '../RevenueDiversification'
import { api } from '../../services/api'
import type { RevenueDiversificationVisualizationResponse } from '../../types'

vi.mock('../../services/api', () => ({
  api: {
    getRevenueDiversificationVisualization: vi.fn(),
  },
}))

const mockedApi = vi.mocked(api)

function buildVisualization(
  labelPrefix: 'Packet' | 'Native' = 'Packet'
): RevenueDiversificationVisualizationResponse {
  return {
    contract_version: 'revenue-diversification-v1',
    generated_at: '2026-03-12T16:00:00Z',
    project_id: 'test-project-id',
    project_name: 'Test Project',
    debt_service_annual: 5310000,
    covenant_trigger_dscr: 1.35,
    non_diesel_combined_coverage_dscr: labelPrefix === 'Packet' ? 1.84 : null,
    non_diesel_senior_coverage_dscr: labelPrefix === 'Packet' ? 4.32 : null,
    stream_definitions: [
      {
        stream_id: 'diesel',
        label: 'Diesel',
        color: '#1D3557',
        stability_class: 'volatile',
        description: 'Primary but volatile renewable diesel revenue stream.',
      },
      {
        stream_id: 'electricity',
        label: 'Electricity',
        color: '#4EA8DE',
        stability_class: 'stable',
        description: 'Contracted electricity or PPA-backed revenue.',
      },
      {
        stream_id: 'tipping',
        label: 'Tipping',
        color: '#2A9D8F',
        stability_class: 'stable',
        description: 'Tipping-fee or inbound feedstock acceptance revenue.',
      },
      {
        stream_id: 'carbon',
        label: 'Carbon',
        color: '#6C9A8B',
        stability_class: 'balanced',
        description: 'Carbon-credit and environmental attribute revenue.',
      },
      {
        stream_id: 'biochar',
        label: 'Biochar',
        color: '#BC6C25',
        stability_class: 'balanced',
        description: 'Biochar and coproduct revenue with moderate market stability.',
      },
    ],
    revenue_scenarios: [
      {
        scenario_id: 'current_state',
        label: labelPrefix === 'Packet' ? 'Diesel + Biochar' : 'Current State',
        total_revenue: 10296936,
        revenue_streams: [
          {
            stream_id: 'biochar',
            label: 'Biochar',
            amount: 175500,
            pct_of_total: 0.017,
            color: '#BC6C25',
            stability_class: 'balanced',
            is_inferred: false,
            source_path: 'revenue.commodities.biochar',
          },
          {
            stream_id: 'diesel',
            label: 'Diesel',
            amount: 10121436,
            pct_of_total: 0.983,
            color: '#1D3557',
            stability_class: 'volatile',
            is_inferred: false,
            source_path: 'revenue.commodities.renewable-diesel',
          },
        ],
        dscr_mean: 1.52,
        dscr_minimum: 1.2,
        breach_weeks: 25,
        implied_rating: 'AA',
        breakeven_diesel_price: 2.94,
        dscr_parity_diesel_price: labelPrefix === 'Packet' ? 4.05 : null,
        covenant_trigger_diesel_price: 4.44,
        safety_status: 'fragile',
        safety_label: 'Razor-thin',
        assumptions: [],
      },
      {
        scenario_id: 'base_case',
        label: labelPrefix === 'Packet' ? '+ Electricity PPA' : 'Base Case',
        total_revenue: 14865836,
        revenue_streams: [
          {
            stream_id: 'tipping',
            label: 'Tipping',
            amount: 525000,
            pct_of_total: 0.035,
            color: '#2A9D8F',
            stability_class: 'stable',
            is_inferred: false,
            source_path: 'revenue.commodities.tipping',
          },
          {
            stream_id: 'electricity',
            label: 'Electricity',
            amount: 4043900,
            pct_of_total: 0.272,
            color: '#4EA8DE',
            stability_class: 'stable',
            is_inferred: false,
            source_path: 'revenue.commodities.electricity',
          },
          {
            stream_id: 'biochar',
            label: 'Biochar',
            amount: 175500,
            pct_of_total: 0.012,
            color: '#BC6C25',
            stability_class: 'balanced',
            is_inferred: false,
            source_path: 'revenue.commodities.biochar',
          },
          {
            stream_id: 'diesel',
            label: 'Diesel',
            amount: 10121436,
            pct_of_total: 0.681,
            color: '#1D3557',
            stability_class: 'volatile',
            is_inferred: false,
            source_path: 'revenue.commodities.renewable-diesel',
          },
        ],
        dscr_mean: 2.04,
        dscr_minimum: 1.76,
        breach_weeks: 0,
        implied_rating: 'AAA',
        breakeven_diesel_price: 1.14,
        dscr_parity_diesel_price: labelPrefix === 'Packet' ? 2.25 : null,
        covenant_trigger_diesel_price: 2.64,
        safety_status: 'safe',
        safety_label: 'Safe',
        assumptions: [],
      },
      {
        scenario_id: 'full_diversification',
        label: 'Full Diversification',
        total_revenue: 16862310,
        revenue_streams: [
          {
            stream_id: 'tipping',
            label: 'Tipping',
            amount: 1500000,
            pct_of_total: 0.089,
            color: '#2A9D8F',
            stability_class: 'stable',
            is_inferred: false,
            source_path: 'revenue.commodities.tipping',
          },
          {
            stream_id: 'electricity',
            label: 'Electricity',
            amount: 4048560,
            pct_of_total: 0.24,
            color: '#4EA8DE',
            stability_class: 'stable',
            is_inferred: false,
            source_path: 'revenue.commodities.electricity',
          },
          {
            stream_id: 'carbon',
            label: 'Carbon',
            amount: 750000,
            pct_of_total: 0.045,
            color: '#6C9A8B',
            stability_class: 'balanced',
            is_inferred: true,
            source_path: null,
          },
          {
            stream_id: 'biochar',
            label: 'Biochar',
            amount: 438750,
            pct_of_total: 0.026,
            color: '#BC6C25',
            stability_class: 'balanced',
            is_inferred: false,
            source_path: 'revenue.commodities.biochar',
          },
          {
            stream_id: 'diesel',
            label: 'Diesel',
            amount: 10125000,
            pct_of_total: 0.6,
            color: '#1D3557',
            stability_class: 'volatile',
            is_inferred: false,
            source_path: 'revenue.commodities.renewable-diesel',
          },
        ],
        dscr_mean: 3.14,
        dscr_minimum: 2.8,
        breach_weeks: 0,
        implied_rating: 'AAA',
        breakeven_diesel_price: 0,
        dscr_parity_diesel_price: labelPrefix === 'Packet' ? 1.05 : null,
        covenant_trigger_diesel_price: 1.44,
        safety_status: 'fortress',
        safety_label: 'Fortress',
        assumptions: ['Full Diversification includes inferred revenue mix uplifts because explicit future-stream facts were incomplete.'],
      },
    ],
    risk_proof:
      labelPrefix === 'Packet'
        ? {
            title: 'Diversification Proof (S06 vs S08)',
            baseline_label: 'S06: Diesel-Only',
            diversified_label: 'S08: Diversified',
            takeaway: 'Diversification eliminates breach weeks in the packet stress test.',
            metrics: [
              {
                metric_id: 'dscr_mean',
                label: 'DSCR Mean',
                baseline_value: '0.42x',
                diversified_value: '2.04x',
                delta_label: '+1.62x',
              },
            ],
          }
        : null,
    data_quality_notes: [
      'Debt service line derived from approved base-case DSCR evidence and assembled scenario revenue.',
    ],
  }
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/projects/test-project-id/revenue-diversification']}>
        <Routes>
          <Route
            path="/projects/:projectId/revenue-diversification"
            element={<RevenueDiversification />}
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('RevenueDiversification page', () => {
  beforeEach(() => {
    mockedApi.getRevenueDiversificationVisualization.mockImplementation(async (_projectId, mode) =>
      Promise.resolve(buildVisualization(mode === 'native' ? 'Native' : 'Packet'))
    )
  })

  it('renders the comparison workflow, scenarios, and data notes', async () => {
    renderPage()

    expect(
      await screen.findByRole('heading', { name: /Revenue Diversification/i })
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Compare Both/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Packet Overlay/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Native Extracted/i })).toBeInTheDocument()
    expect(screen.getByText(/Overlay Comparison/i)).toBeInTheDocument()
    expect(screen.getAllByText(/Full Diversification/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Packet Overlay/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Base Case/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Razor-thin/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/Fortress/i).length).toBeGreaterThan(0)
  })
})
