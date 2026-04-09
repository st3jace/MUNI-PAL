/**
 * Healthcare CFO Landing — Standalone Frontend Entry Point
 *
 * Renders the healthcare CFO landing page for muni-pal.io.
 * Includes the landing page + MIR tools flow so CTAs work end-to-end.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Analytics } from '@vercel/analytics/react'
import { SensingProvider } from './contexts/SensingContext'
import HealthcareCFOLanding from './pages/tools/HealthcareCFOLanding'
import HealthcareReadiness from './pages/tools/HealthcareReadiness'
import ToolsHub from './pages/tools/ToolsHub'
import MarketIntelligence from './pages/tools/MarketIntelligence'
import BenchmarkCalculator from './pages/tools/BenchmarkCalculator'
import ReadinessAssess from './pages/tools/ReadinessAssess'
import CreditSpreadMonitor from './pages/tools/CreditSpreadMonitor'
import ReportExport from './pages/tools/ReportExport'
import './styles/index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
})

const root = document.getElementById('root')!

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
    <BrowserRouter>
      <SensingProvider>
        <div className="min-h-screen bg-gray-50">
          <div className="py-8 px-4 sm:px-6 lg:px-8">
            <Routes>
              {/* Landing page is the root */}
              <Route path="/" element={<HealthcareCFOLanding />} />
              <Route path="/healthcare" element={<HealthcareCFOLanding />} />
              {/* Tools hub */}
              <Route path="/tools" element={<ToolsHub />} />
              {/* MIR tools flow — CTAs link here */}
              <Route path="/tools/market-intelligence" element={<MarketIntelligence />} />
              <Route path="/tools/benchmark" element={<BenchmarkCalculator />} />
              <Route path="/tools/readiness" element={<ReadinessAssess />} />
              <Route path="/tools/credit-spreads" element={<CreditSpreadMonitor />} />
              <Route path="/tools/healthcare-readiness" element={<HealthcareReadiness />} />
              <Route path="/tools/export" element={<ReportExport />} />
              {/* Catch-all back to landing */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </div>
      </SensingProvider>
    </BrowserRouter>
    <Analytics />
    </QueryClientProvider>
  </StrictMode>,
)
