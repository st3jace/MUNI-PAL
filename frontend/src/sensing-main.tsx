/**
 * Sensing Microservice — Standalone Frontend Entry Point
 *
 * Renders only the /tools/* pages for the public muni-pal.io site.
 * No BFMS, project management, or auth routes are included.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Analytics } from '@vercel/analytics/react'
import { SensingProvider } from './contexts/SensingContext'
import ToolsHub from './pages/tools/ToolsHub'
import MarketIntelligence from './pages/tools/MarketIntelligence'
import BenchmarkCalculator from './pages/tools/BenchmarkCalculator'
import ReadinessAssess from './pages/tools/ReadinessAssess'
import ReportExport from './pages/tools/ReportExport'
import CreditSpreadMonitor from './pages/tools/CreditSpreadMonitor'
import CoiBenchmarking from './pages/tools/CoiBenchmarking'
import PilotNavigation from './pages/tools/PilotNavigation'
import HealthcareCFOLanding from './pages/tools/HealthcareCFOLanding'
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
        <div className="min-h-screen flex flex-col">
          <div className="flex-1">
            <Routes>
              {/* Sector landing pages */}
              <Route path="/healthcare" element={<HealthcareCFOLanding />} />
              {/* Redirect root to tools hub */}
              <Route path="/" element={<Navigate to="/tools" replace />} />
              <Route path="/tools" element={<ToolsHub />} />
              <Route path="/tools/market-intelligence" element={<MarketIntelligence />} />
              <Route path="/tools/benchmark" element={<BenchmarkCalculator />} />
              <Route path="/tools/readiness" element={<ReadinessAssess />} />
              <Route path="/tools/credit-spreads" element={<CreditSpreadMonitor />} />
              <Route path="/tools/pilot-navigation" element={<PilotNavigation />} />
              <Route path="/tools/coi-benchmarking" element={<CoiBenchmarking />} />
              <Route path="/tools/export" element={<ReportExport />} />
              {/* Catch-all back to tools */}
              <Route path="*" element={<Navigate to="/tools" replace />} />
            </Routes>
          </div>
          <footer className="border-t border-gray-200 bg-white px-6 py-4">
            <p className="text-center text-sm text-gray-500">
              Muni-Pal &mdash; A Launch Shop product. Built by Innovation Factory.
            </p>
          </footer>
        </div>
      </SensingProvider>
    </BrowserRouter>
    <Analytics />
    </QueryClientProvider>
  </StrictMode>,
)
