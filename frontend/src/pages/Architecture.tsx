import { Code, Cpu, Globe, Shield, Database, CheckCircle2, ArrowRight } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { aiHealthCheck, tavilyHealthCheck, sandboxHealthCheck } from '../services/api'

export function Architecture() {
  const [infra, setInfra] = useState({
    aiProvider: 'mock',
    aiModel: 'nvidia/nemotron-3-ultra-550b-a55b',
    tavilyStatus: 'connected',
    sandboxMode: 'local_safe',
  })

  useEffect(() => {
    Promise.allSettled([aiHealthCheck(), tavilyHealthCheck(), sandboxHealthCheck()]).then(results => {
      const [ai, tavily, sandbox] = results
      setInfra({
        aiProvider: ai.status === 'fulfilled' ? ai.value.provider : 'mock',
        aiModel: ai.status === 'fulfilled' ? ai.value.model : 'nvidia/nemotron-3-ultra-550b-a55b',
        tavilyStatus: tavily.status === 'fulfilled' ? tavily.value.status : 'offline',
        sandboxMode: sandbox.status === 'fulfilled' ? (sandbox.value.mode || sandbox.value.provider) : 'local_safe',
      })
    })
  }, [])

  const aiName = infra.aiProvider === 'nebius'
    ? 'NVIDIA Nemotron via Nebius Token Factory'
    : 'Deterministic Mock Provider'

  const tavilyName = infra.tavilyStatus === 'healthy' || infra.tavilyStatus === 'connected'
    ? 'Tavily Search Engine (Live)'
    : 'Offline Cached Research'

  const sandboxName = infra.sandboxMode.includes('docker')
    ? 'Docker Container Sandbox'
    : 'Local Safe Sandbox'

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', paddingBottom: 60 }}>
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div>
          <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Code style={{ width: 24, height: 24, color: 'var(--accent-primary)' }} />
            <span>TECHNICAL ARCHITECTURE</span>
          </h1>
          <p className="page-subtitle">
            Subsystems, Execution Boundaries, Safety Limits, and Causal Verification Pipeline
          </p>
        </div>
        <NavLink to="/judge" className="btn btn-primary" style={{ padding: '8px 18px', fontWeight: 600 }}>
          RUN JUDGE DEMO
        </NavLink>
      </div>

      {/* Grid of Subsystems */}
      <div className="grid grid-3" style={{ gap: 20, marginBottom: 32 }}>
        <div className="card" style={{ padding: 22 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <Code style={{ width: 22, height: 22, color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: 16 }}>Frontend Client</h3>
          </div>
          <div className="mono" style={{ fontSize: 13, color: 'var(--accent-primary)', marginBottom: 8 }}>
            React 18 / TypeScript / Vite
          </div>
          <p style={{ fontSize: 13, color: 'var(--fg-secondary)', lineHeight: 1.6 }}>
            Command Center UI, live telemetry trace streaming, interactive causal graph visualization, before/after diff viewer, and cryptographic receipt generator.
          </p>
        </div>

        <div className="card" style={{ padding: 22 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <Database style={{ width: 22, height: 22, color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: 16 }}>Backend Orchestrator</h3>
          </div>
          <div className="mono" style={{ fontSize: 13, color: 'var(--accent-primary)', marginBottom: 8 }}>
            FastAPI / Python 3.12 / SQLite
          </div>
          <p style={{ fontSize: 13, color: 'var(--fg-secondary)', lineHeight: 1.6 }}>
            8-phase asynchronous investigation orchestrator. Enforces safety limits: MAX_AGENT_STEPS=40, MAX_TOOL_CALLS=25, and atomic state checkpointing in SQLite.
          </p>
        </div>

        <div className="card" style={{ padding: 22 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <Cpu style={{ width: 22, height: 22, color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: 16 }}>AI Reasoning Layer</h3>
          </div>
          <div className="mono" style={{ fontSize: 13, color: 'var(--accent-primary)', marginBottom: 8 }}>
            {aiName}
          </div>
          <p style={{ fontSize: 13, color: 'var(--fg-secondary)', lineHeight: 1.6 }}>
            Structured hypothesis formulation, multi-evidence weighted confidence scoring, and minimal remediation generation.
          </p>
        </div>

        <div className="card" style={{ padding: 22 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <Globe style={{ width: 22, height: 22, color: 'var(--accent-secondary)' }} />
            <h3 style={{ fontSize: 16 }}>Research & RAG Engine</h3>
          </div>
          <div className="mono" style={{ fontSize: 13, color: 'var(--accent-secondary)', marginBottom: 8 }}>
            {tavilyName} + Offline Index
          </div>
          <p style={{ fontSize: 13, color: 'var(--fg-secondary)', lineHeight: 1.6 }}>
            Hybrid retrieval system indexing local postmortems and runbooks with BM25/cosine similarity, enriched by live Tavily research queries for external error codes.
          </p>
        </div>

        <div className="card" style={{ padding: 22 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <Shield style={{ width: 22, height: 22, color: 'var(--accent-warning)' }} />
            <h3 style={{ fontSize: 16 }}>Execution Sandbox</h3>
          </div>
          <div className="mono" style={{ fontSize: 13, color: 'var(--accent-warning)', marginBottom: 8 }}>
            {sandboxName}
          </div>
          <p style={{ fontSize: 13, color: 'var(--fg-secondary)', lineHeight: 1.6 }}>
            Isolated execution environment with path containment, command allowlisting, memory quotas, and guaranteed rollback cleanup.
          </p>
        </div>

        <div className="card" style={{ padding: 22, borderColor: 'var(--accent-primary)', background: 'rgba(0, 212, 170, 0.04)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <CheckCircle2 style={{ width: 22, height: 22, color: 'var(--accent-primary)' }} />
            <h3 style={{ fontSize: 16, color: 'var(--accent-primary)' }}>Deterministic Verifier</h3>
          </div>
          <div className="mono" style={{ fontSize: 13, color: 'var(--accent-primary)', marginBottom: 8 }}>
            4-Stage Causal Proof
          </div>
          <p style={{ fontSize: 13, color: 'var(--fg-secondary)', lineHeight: 1.6 }}>
            Deterministic verification matrix. Executes Baseline (FAIL), Post-Fix (PASS), Health (PASS), and Control (FAIL) before certifying recovery.
          </p>
        </div>
      </div>

      {/* Verification Matrix Table */}
      <div className="card" style={{ padding: 24, marginBottom: 24 }}>
        <h3 style={{ fontSize: 16, marginBottom: 16 }}>Deterministic Causal Verification Decision Matrix</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Baseline Test</th>
                <th>Post-Fix Tests</th>
                <th>Health Check</th>
                <th>Control Test</th>
                <th>Final Verdict</th>
                <th>Causal Interpretation</th>
              </tr>
            </thead>
            <tbody>
              <tr style={{ background: 'rgba(0, 212, 170, 0.08)' }}>
                <td><span className="badge badge-failed">FAILED</span></td>
                <td><span className="badge badge-verified">PASSED</span></td>
                <td><span className="badge badge-verified">PASSED</span></td>
                <td><span className="badge badge-failed">FAILED</span></td>
                <td><strong style={{ color: 'var(--accent-primary)' }}>VERIFIED</strong></td>
                <td>Recovery mathematically proven by independent control reversion.</td>
              </tr>
              <tr>
                <td><span className="badge badge-verified">PASSED</span></td>
                <td><span className="badge badge-verified">PASSED</span></td>
                <td><span className="badge badge-verified">PASSED</span></td>
                <td><span className="badge badge-failed">FAILED</span></td>
                <td><span className="badge badge-unverified">UNVERIFIED</span></td>
                <td>Baseline passed; failure was not reproduced (flaky test or external heal).</td>
              </tr>
              <tr>
                <td><span className="badge badge-failed">FAILED</span></td>
                <td><span className="badge badge-failed">FAILED</span></td>
                <td><span className="badge badge-failed">FAILED</span></td>
                <td><span className="badge badge-failed">FAILED</span></td>
                <td><span className="badge badge-failed">FAILED</span></td>
                <td>Remediation failed to resolve the failure state.</td>
              </tr>
              <tr>
                <td><span className="badge badge-failed">FAILED</span></td>
                <td><span className="badge badge-verified">PASSED</span></td>
                <td><span className="badge badge-verified">PASSED</span></td>
                <td><span className="badge badge-verified">PASSED</span></td>
                <td><span className="badge badge-unverified">UNVERIFIED</span></td>
                <td>Control passed without fix; recovery was coincidental, not causal.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div style={{ textAlign: 'center' }}>
        <NavLink to="/judge" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '10px 24px' }}>
          <span>Launch Judge Mode Experience</span>
          <ArrowRight style={{ width: 16, height: 16 }} />
        </NavLink>
      </div>
    </div>
  )
}
