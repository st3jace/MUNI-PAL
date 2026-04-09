/**
 * Readiness MVP — Standalone Entry Point for readiness.elaunchshop.com
 *
 * Routes `/` directly to the ReadinessAssess component.
 * Works fully client-side when the sensing API is unavailable.
 */

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Analytics } from '@vercel/analytics/react'
import { SensingProvider } from './contexts/SensingContext'
import ReadinessAssess from './pages/tools/ReadinessAssess'
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
              {/* Readiness assessment is the hero — root route */}
              <Route path="/" element={<ReadinessAssess />} />
              <Route path="/tools/readiness" element={<ReadinessAssess />} />
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
