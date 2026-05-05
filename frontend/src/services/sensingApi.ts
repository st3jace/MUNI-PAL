/**
 * Sensing Component API client.
 *
 * Calls the /api/v1/sensing/ endpoints for market intelligence,
 * benchmarking, readiness assessment, lead capture, and event tracking.
 */
import axios from 'axios'

const BASE = '/api/v1/sensing'

const client = axios.create({ baseURL: BASE })

export interface SectorInfo {
  id: string
  name: string
  children?: SectorInfo[]
}

export interface BenchmarkParams {
  sector: string
  deal_size: number
  state: string
  rating: string
  maturity: number
}

export interface CreditSpreadParams {
  sector: string
  par_amount?: number
  out_of_state?: boolean
}

export interface ReadinessParams {
  sector: string
  project_name: string
  responses: Record<string, boolean>
  evidence_ids: string[]
  dscr?: number
  revenue?: number
  coverage_ratio?: number
}

export interface LeadCaptureParams {
  email: string
  name: string
  organization: string
  title?: string
  phone?: string
  sector: string
  deal_size_estimate?: number
  state?: string
  expected_rating?: string
  referral_source?: string
  session_id: string
  privacy_consent: boolean
  consent_version?: string
  market_intel_json?: string
  benchmark_json?: string
  readiness_json?: string
}

export interface EventParams {
  session_id: string
  event_type: string
  sector?: string
  event_data?: string
}

export const sensingApi = {
  async listSectors(): Promise<SectorInfo[]> {
    const { data } = await client.get('/sectors')
    return data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async getMarketIntelligence(sector: string): Promise<any> {
    const { data } = await client.get('/market-intelligence', {
      params: { sector },
    })
    return data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async runBenchmark(params: BenchmarkParams): Promise<any> {
    const { data } = await client.post('/benchmark', params)
    return data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async getCreditSpreads(params: CreditSpreadParams): Promise<any> {
    const { data } = await client.post('/credit-spreads', params)
    return data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async getQuestionnaire(sector: string): Promise<any[]> {
    const { data } = await client.get('/questionnaire', {
      params: { sector },
    })
    return data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async runReadinessAssessment(params: ReadinessParams): Promise<any> {
    const { data } = await client.post('/readiness', params)
    return data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async getCoiBenchmarks(subSector?: string): Promise<any> {
    const { data } = await client.get('/coi-benchmarks', {
      params: subSector ? { sub_sector: subSector } : {},
    })
    return data
  },

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  async getCoiDealBenchmarks(subSector?: string): Promise<any> {
    const { data } = await client.get('/coi-deal-benchmarks', {
      params: subSector ? { sub_sector: subSector } : {},
    })
    return data
  },

  async captureLead(params: LeadCaptureParams): Promise<{ lead_id: string; status: string }> {
    const { data } = await client.post('/lead', params)
    return data
  },

  async trackEvent(params: EventParams): Promise<void> {
    await client.post('/event', params).catch(() => {
      // Event tracking is best-effort — don't break the UX
    })
  },
}

/**
 * Generate or retrieve a persistent session ID for funnel tracking.
 */
export function getSensingSessionId(): string {
  const KEY = 'muni_sensing_session'
  let id = sessionStorage.getItem(KEY)
  if (!id) {
    id = `ses_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
    sessionStorage.setItem(KEY, id)
  }
  return id
}
