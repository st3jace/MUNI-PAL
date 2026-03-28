import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ProjectList from './pages/ProjectList'
import ProjectDetail from './pages/ProjectDetail'
import FactsReview from './pages/FactsReview'
import Checklist from './pages/Checklist'
import Readiness from './pages/Readiness'
import DeliverablePack from './pages/DeliverablePack'
// v2 - WP7, WP8, Bifurcated Deliverables
import Disclosure from './pages/Disclosure'
import InformationRequests from './pages/InformationRequests'
import AdvisoryPackages from './pages/AdvisoryPackages'
import RevenueDiversification from './pages/RevenueDiversification'
// Sensing Component Tools
import { SensingProvider } from './contexts/SensingContext'
import ToolsHub from './pages/tools/ToolsHub'
import MarketIntelligence from './pages/tools/MarketIntelligence'
import BenchmarkCalculator from './pages/tools/BenchmarkCalculator'
import ReadinessAssess from './pages/tools/ReadinessAssess'
import ReportExport from './pages/tools/ReportExport'
import CreditSpreadMonitor from './pages/tools/CreditSpreadMonitor'

function App() {
  return (
    <BrowserRouter>
      <SensingProvider>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="projects" element={<ProjectList />} />
            <Route path="projects/:projectId" element={<ProjectDetail />} />
            <Route path="projects/:projectId/facts" element={<FactsReview />} />
            <Route path="projects/:projectId/checklist" element={<Checklist />} />
            <Route path="projects/:projectId/readiness" element={<Readiness />} />
            <Route path="projects/:projectId/handoff" element={<DeliverablePack />} />
            {/* v2 - WP7, WP8, Bifurcated Deliverables */}
            <Route path="projects/:projectId/disclosure" element={<Disclosure />} />
            <Route path="projects/:projectId/requests" element={<InformationRequests />} />
            <Route path="projects/:projectId/packages" element={<AdvisoryPackages />} />
            <Route
              path="projects/:projectId/revenue-diversification"
              element={<RevenueDiversification />}
            />
            {/* Sensing Component Tools */}
            <Route path="tools" element={<ToolsHub />} />
            <Route path="tools/market-intelligence" element={<MarketIntelligence />} />
            <Route path="tools/benchmark" element={<BenchmarkCalculator />} />
            <Route path="tools/readiness" element={<ReadinessAssess />} />
            <Route path="tools/credit-spreads" element={<CreditSpreadMonitor />} />
            <Route path="tools/export" element={<ReportExport />} />
          </Route>
        </Routes>
      </SensingProvider>
    </BrowserRouter>
  )
}

export default App
