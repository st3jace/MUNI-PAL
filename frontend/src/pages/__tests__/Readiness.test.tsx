import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import Readiness from '../Readiness'
import { api } from '../../services/api'
import {
  ReadinessDimension,
  type ReadinessAssessment,
  type RiskBfmsIntegrationResponse,
} from '../../types'

vi.mock('../../services/api', () => ({
  api: {
    getReadinessAssessment: vi.fn(),
    getReadinessGaps: vi.fn(),
    getRiskBfmsIntegration: vi.fn(),
  },
}))

const mockedApi = vi.mocked(api)

function buildAssessment(): ReadinessAssessment {
  const score = (dimension: ReadinessDimension) => ({
    dimension,
    dimension_name: dimension,
    score: 6,
    max_score: 10,
    weight: 1 / 6,
    weighted_contribution: 1,
    critical_paths_covered: 4,
    critical_paths_total: 6,
    explanation: 'Coverage in progress.',
    improvement_suggestions: [],
  })

  return {
    project_id: 'test-project-id',
    dimensions: {
      [ReadinessDimension.ISSUER_AUTHORITY]: score(ReadinessDimension.ISSUER_AUTHORITY),
      [ReadinessDimension.PROJECT_TECH]: score(ReadinessDimension.PROJECT_TECH),
      [ReadinessDimension.REVENUE_FEEDSTOCK]: score(ReadinessDimension.REVENUE_FEEDSTOCK),
      [ReadinessDimension.CAB_FINANCIAL]: score(ReadinessDimension.CAB_FINANCIAL),
      [ReadinessDimension.RISK_SECURITY_SLB]: score(ReadinessDimension.RISK_SECURITY_SLB),
      [ReadinessDimension.SLB_VERIFICATION]: score(ReadinessDimension.SLB_VERIFICATION),
    },
    overall_score: 6.0,
    recommendation: 'Ready for Selective Engagement',
    recommendation_rationale: 'Core requirements are progressing.',
    total_facts_approved: 120,
    total_facts_pending: 8,
    critical_gaps_count: 2,
    material_gaps_count: 6,
  }
}

function renderReadinessPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  })
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={['/projects/test-project-id/readiness']}>
        <Routes>
          <Route path="/projects/:projectId/readiness" element={<Readiness />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  )
}

describe('Readiness risk integration rendering', () => {
  beforeEach(() => {
    mockedApi.getReadinessAssessment.mockResolvedValue(buildAssessment())
    mockedApi.getReadinessGaps.mockResolvedValue({
      critical_gaps: [],
      material_gaps: [],
      priority_actions: [],
    })
  })

  it('renders fallback mode details when integration payload is fallback', async () => {
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

    renderReadinessPage()

    expect(await screen.findByText(/BFMS Risk Integration: Fallback Mode/i)).toBeInTheDocument()
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

    renderReadinessPage()

    expect(await screen.findByText(/BFMS Risk Integration: Full Mode/i)).toBeInTheDocument()
    expect(screen.getByText('Execution Grade')).toBeInTheDocument()
    expect(screen.queryByText(/Fallback Reasons/i)).not.toBeInTheDocument()
  })
})
