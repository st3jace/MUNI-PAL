import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import AdvisoryPackages from '../AdvisoryPackages'
import { api } from '../../services/api'
import type { RiskBfmsIntegrationResponse } from '../../types'

vi.mock('../../services/api', () => ({
  api: {
    getLatestInternalReport: vi.fn(),
    listInternalReports: vi.fn(),
    getLatestExternalPackage: vi.fn(),
    listExternalPackages: vi.fn(),
    validateExternalPackage: vi.fn(),
    getRiskBfmsIntegration: vi.fn(),
  },
}))

const mockedApi = vi.mocked(api)

function renderAdvisoryPackagesPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })

  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/projects/test-project-id/packages']}>
        <Routes>
          <Route path="/projects/:projectId/packages" element={<AdvisoryPackages />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

function openExternalTab() {
  fireEvent.click(screen.getByRole('button', { name: /External Advisory Package/i }))
}

describe('AdvisoryPackages risk integration rendering', () => {
  beforeEach(() => {
    mockedApi.getLatestInternalReport.mockResolvedValue(null)
    mockedApi.listInternalReports.mockResolvedValue({ reports: [], total: 0 })
    mockedApi.getLatestExternalPackage.mockResolvedValue(null)
    mockedApi.listExternalPackages.mockResolvedValue({ packages: [], total: 0 })
    mockedApi.validateExternalPackage.mockResolvedValue({
      ready_for_distribution: true,
      issues: [],
      warnings: [],
      recommendations: [],
    })
    mockedApi.getRiskBfmsIntegration.mockResolvedValue(null)
  })

  it('renders fallback risk integration details in external advisory tab', async () => {
    const payload: RiskBfmsIntegrationResponse = {
      generated_at: '2026-02-19T20:00:00Z',
      project_id: 'test-project-id',
      contract_version: 'risk-bfms-integration-v1',
      integration_mode: 'fallback',
      overall_benchmark_position: 'above',
      overall_posture_score: 0.812,
      reliability_low_dimensions: 2,
      directional_guidance_only: true,
      fallback_reasons: ['One or more risk dimensions are low reliability.'],
      critical_risk_flags: ['DSCR covenant headroom breached.'],
      advisory_next_steps: [
        {
          action_id: 'action.dscr.coverage',
          priority: 'high',
          owner: 'Financial Advisor',
          title: 'Strengthen DSCR coverage package',
          target_date_hint: '7 days',
          expected_impact: 'Improves covenant resilience.',
        },
      ],
      cohort: {
        sector: 'waste_to_energy',
        issuer_size_band: 'mid',
        deal_type: 'revenue',
        recency_window: '5y',
        sample_size: 50,
      },
      key_assumptions: ['Directional due to sample size limits.'],
      compliance_checks: [],
      internal_report_contract_version: 'risk-internal-v1',
      external_brief_contract_version: 'risk-external-v1',
      material_risk_statements: [],
    }
    mockedApi.getRiskBfmsIntegration.mockResolvedValue(payload)

    renderAdvisoryPackagesPage()
    openExternalTab()

    expect(await screen.findByText(/BFMS Risk Integration Input: Fallback Mode/i)).toBeInTheDocument()
    expect(screen.getByText('Directional Guidance')).toBeInTheDocument()
    expect(screen.getByText(/Fallback Reasons/i)).toBeInTheDocument()
    expect(screen.getByText(/Strengthen DSCR coverage package/i)).toBeInTheDocument()
  })

  it('renders full mode without fallback reason section', async () => {
    const payload: RiskBfmsIntegrationResponse = {
      generated_at: '2026-02-19T20:00:00Z',
      project_id: 'test-project-id',
      contract_version: 'risk-bfms-integration-v1',
      integration_mode: 'full',
      overall_benchmark_position: 'at',
      overall_posture_score: 0.336,
      reliability_low_dimensions: 0,
      directional_guidance_only: false,
      fallback_reasons: [],
      cohort: {
        sector: 'waste_to_energy',
        issuer_size_band: 'mid',
        deal_type: 'revenue',
        recency_window: '5y',
        sample_size: 50,
      },
      critical_risk_flags: ['No critical risk flags from current evidence baseline.'],
      advisory_next_steps: [],
      key_assumptions: ['No material assumptions beyond validated evidence set.'],
      compliance_checks: [],
      internal_report_contract_version: 'risk-internal-v1',
      external_brief_contract_version: 'risk-external-v1',
      material_risk_statements: [],
    }
    mockedApi.getRiskBfmsIntegration.mockResolvedValue(payload)

    renderAdvisoryPackagesPage()
    openExternalTab()

    expect(await screen.findByText(/BFMS Risk Integration Input: Full Mode/i)).toBeInTheDocument()
    expect(screen.getByText('Execution Grade')).toBeInTheDocument()
    expect(screen.queryByText(/Fallback Reasons/i)).not.toBeInTheDocument()
  })

  it('renders unavailable note when integration endpoint is not enabled', async () => {
    mockedApi.getRiskBfmsIntegration.mockResolvedValue(null)

    renderAdvisoryPackagesPage()
    openExternalTab()

    expect(await screen.findByText(/BFMS Risk Integration Input unavailable/i)).toBeInTheDocument()
    expect(
      screen.getByText(/Risk integration contract is not enabled for this environment/i)
    ).toBeInTheDocument()
  })
})
