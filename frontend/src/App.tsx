import { Routes, Route } from 'react-router-dom'
import { Layout } from './components/Layout'
import { Dashboard } from './pages/Dashboard'
import { JudgeMode } from './pages/JudgeMode'
import { WhyCoska } from './pages/WhyCoska'
import { Architecture } from './pages/Architecture'
import { Investigation } from './pages/Investigation'
import { Evidence } from './pages/Evidence'
import { Hypotheses } from './pages/Hypotheses'
import { RootCause } from './pages/RootCause'
import { Remediation } from './pages/Remediation'
import { Verification } from './pages/Verification'
import { IncidentDetail } from './pages/IncidentDetail'

export function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="judge" element={<JudgeMode />} />
        <Route path="why" element={<WhyCoska />} />
        <Route path="architecture" element={<Architecture />} />
        <Route path="incidents/:id" element={<IncidentDetail />}>
          <Route index element={<Investigation />} />
          <Route path="evidence" element={<Evidence />} />
          <Route path="hypotheses" element={<Hypotheses />} />
          <Route path="root-cause" element={<RootCause />} />
          <Route path="remediation" element={<Remediation />} />
          <Route path="verification" element={<Verification />} />
        </Route>
      </Route>
    </Routes>
  )
}
