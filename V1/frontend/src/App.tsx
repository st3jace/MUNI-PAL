import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ProjectList from './pages/ProjectList'
import ProjectDetail from './pages/ProjectDetail'
import FactsReview from './pages/FactsReview'
import Checklist from './pages/Checklist'
import Readiness from './pages/Readiness'
import DeliverablePack from './pages/DeliverablePack'

function App() {
  return (
    <BrowserRouter>
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
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
