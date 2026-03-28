/**
 * Shared state for Sensing Tool results.
 *
 * Each tool page stores its results here so the ReportExport page
 * can access all 3 components for the combined PDF.
 */
import { createContext, useContext, useState, type ReactNode } from 'react'

export interface BenchmarkInputs {
  deal_size: number
  state: string
  rating: string
  maturity: number
}

interface SensingState {
  sector: string
  setSector: (s: string) => void
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  marketIntel: any | null
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setMarketIntel: (data: any) => void
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  benchmark: any | null
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setBenchmark: (data: any) => void
  benchmarkInputs: BenchmarkInputs | null
  setBenchmarkInputs: (inputs: BenchmarkInputs) => void
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  readiness: any | null
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setReadiness: (data: any) => void
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  creditSpreads: any | null
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  setCreditSpreads: (data: any) => void
  /** Number of completed tool sections */
  completedCount: number
}

const SensingContext = createContext<SensingState | null>(null)

export function SensingProvider({ children }: { children: ReactNode }) {
  const [sector, setSector] = useState('waste')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [marketIntel, setMarketIntel] = useState<any>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [benchmark, setBenchmark] = useState<any>(null)
  const [benchmarkInputs, setBenchmarkInputs] =
    useState<BenchmarkInputs | null>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [readiness, setReadiness] = useState<any>(null)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [creditSpreads, setCreditSpreads] = useState<any>(null)

  const completedCount = [marketIntel, benchmark, readiness, creditSpreads].filter(
    Boolean
  ).length

  return (
    <SensingContext.Provider
      value={{
        sector,
        setSector,
        marketIntel,
        setMarketIntel,
        benchmark,
        setBenchmark,
        benchmarkInputs,
        setBenchmarkInputs,
        readiness,
        setReadiness,
        creditSpreads,
        setCreditSpreads,
        completedCount,
      }}
    >
      {children}
    </SensingContext.Provider>
  )
}

export function useSensing(): SensingState {
  const ctx = useContext(SensingContext)
  if (!ctx) throw new Error('useSensing must be used within SensingProvider')
  return ctx
}
