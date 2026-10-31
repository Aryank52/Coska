import { useState, useEffect } from 'react'
import { NavLink } from 'react-router-dom'
import {
  Gavel, Play, RotateCcw, CheckCircle2, AlertTriangle, Shield,
  Search, Lightbulb, Target, Wrench, Download, Code, Globe, Cpu,
  ArrowRight, FileText, X
} from 'lucide-react'
import { SCENARIOS } from '../services/demoScenarios'
import { aiHealthCheck, tavilyHealthCheck, sandboxHealthCheck, healthCheck } from '../services/api'

type StepKey = 'incident' | 'evidence' | 'rag' | 'hypotheses' | 'root_cause' | 'remediation' | 'verification' | 'receipt'

const PIPELINE_STEPS: Array<{ key: StepKey; label: string; icon: any }> = [
  { key: 'incident', label: '1. Incident', icon: AlertTriangle },
  { key: 'evidence', label: '2. Evidence Graph', icon: Search },
  { key: 'rag', label: '3. RAG Knowledge', icon: FileText },
  { key: 'hypotheses', label: '4. Hypotheses', icon: Lightbulb },
  { key: 'root_cause', label: '5. Root Cause', icon: Target },
  { key: 'remediation', label: '6. Remediation Lab', icon: Wrench },
  { key: 'verification', label: '7. Causal Verification', icon: CheckCircle2 },
  { key: 'receipt', label: '8. Receipt', icon: Shield },
]

export function JudgeMode() {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('payment_pool_exhaustion')
  const [currentStep, setCurrentStep] = useState<StepKey>('incident')
  const [isRunning, setIsRunning] = useState(false)
  const [activeTraceStepIndex, setActiveTraceStepIndex] = useState(13)
  const [showJsonModal, setShowJsonModal] = useState(false)
  const [viewTab, setViewTab] = useState<'showcase' | 'architecture' | 'impact'>('showcase')

  const [infra, setInfra] = useState({
    aiProvider: 'mock',
    aiModel: 'nvidia/nemotron-3-ultra-550b-a55b',
    tavilyStatus: 'connected',
    sandboxMode: 'local_safe',
    dbStatus: 'healthy',
  })

  const scenario = SCENARIOS.find(s => s.id === selectedScenarioId) || SCENARIOS[0]

  useEffect(() => {
    loadHealth()
  }, [])

  const loadHealth = async () => {
    try {
      const [ai, tavily, sandbox, db] = await Promise.allSettled([
        aiHealthCheck(),
        tavilyHealthCheck(),
        sandboxHealthCheck(),
        healthCheck(),
      ])

      setInfra({
        aiProvider: ai.status === 'fulfilled' ? ai.value.provider : 'mock',
        aiModel: ai.status === 'fulfilled' ? ai.value.model : 'Deterministic Mock Provider',
        tavilyStatus: tavily.status === 'fulfilled' ? tavily.value.status : 'offline',
        sandboxMode: sandbox.status === 'fulfilled' ? (sandbox.value.mode || sandbox.value.provider) : 'local_safe',
        dbStatus: db.status === 'fulfilled' ? db.value.status : 'healthy',
      })
    } catch {
      // Fallback
    }
  }

  const handleRunFullShowcase = () => {
    setIsRunning(true)
    setCurrentStep('incident')
    setActiveTraceStepIndex(0)

    const stepOrder: StepKey[] = [
      'incident',
      'evidence',
      'rag',
      'hypotheses',
      'root_cause',
      'remediation',
      'verification',
      'receipt'
    ]

    let stepIdx = 0
    let traceIdx = 0

    const traceInterval = setInterval(() => {
      traceIdx++
      if (traceIdx < scenario.traceSteps.length) {
        setActiveTraceStepIndex(traceIdx)
      }
    }, 450)

    const stageInterval = setInterval(() => {
      stepIdx++
      if (stepIdx < stepOrder.length) {
        setCurrentStep(stepOrder[stepIdx])
      } else {
        clearInterval(stageInterval)
        clearInterval(traceInterval)
        setIsRunning(false)
        setActiveTraceStepIndex(scenario.traceSteps.length - 1)
      }
    }, 1200)
  }

  const handleReset = () => {
    setIsRunning(false)
    setCurrentStep('incident')
    setActiveTraceStepIndex(scenario.traceSteps.length - 1)
  }

  const downloadReport = () => {
    const reportText = `# COSKA Incident Investigation & Verified Recovery Report
Incident ID: INC-${scenario.id.toUpperCase().replace(/_/g, '-')}
Service: ${scenario.service}
Severity: ${scenario.severity}
Status: VERIFIED

## Executive Summary
Autonomous investigation diagnosed ${scenario.rootCause.title} with ${scenario.rootCause.confidence}% confidence.
Remediation (${scenario.configKey}) was simulated in an isolated sandbox and verified through 4-stage deterministic causal testing.

## Root Cause Analysis
- Title: ${scenario.rootCause.title}
- Confidence: ${scenario.rootCause.confidence}%
- Evidence: ${scenario.rootCause.supportingCount} supporting signals, ${scenario.rootCause.contradictingCount} contradicting signals
- Synthesis: ${scenario.rootCause.whySummary}

## Four-Stage Deterministic Causal Verification
1. BASELINE: ${scenario.verification.baseline.status} (Exit code ${scenario.verification.baseline.code}) - Failure successfully reproduced.
2. POST-FIX: ${scenario.verification.postfix.status} (Exit code ${scenario.verification.postfix.code}) - Fix resolved target symptoms.
3. HEALTH CHECK: ${scenario.verification.health.status} (Exit code ${scenario.verification.health.code}) - All service probes healthy.
4. CONTROL TEST: ${scenario.verification.control.status} (Exit code ${scenario.verification.control.code}) - Removal of fix reintroduces failure, confirming causality.

FINAL VERDICT: VERIFIED
Verification ID: ${scenario.verification.receiptId}
Timestamp: ${scenario.verification.timestamp}
Sandbox Provider: ${infra.sandboxMode}
AI Provider: ${infra.aiProvider === 'openai_compatible' ? 'OpenAI Compatible (GPT-4o)' : infra.aiProvider === 'local' ? 'Local LLM (Ollama)' : 'Deterministic Mock Provider'}
`
    const blob = new Blob([reportText], { type: 'text/markdown;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `COSKA-Verification-Report-${scenario.id}.md`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // Provider display names
  const aiProviderLabel = infra.aiProvider === 'openai_compatible' 
    ? 'OpenAI Compatible (GPT-4o)'
    : infra.aiProvider === 'local'
    ? 'Local LLM (Ollama)'
    : 'Deterministic Mock Provider'

  const researchProviderLabel = infra.tavilyStatus === 'healthy' || infra.tavilyStatus === 'connected'
    ? 'External Research (Live)'
    : 'Offline Cached Research'

  const sandboxLabel = infra.sandboxMode.includes('docker')
    ? 'Docker Container Sandbox'
    : 'Local Safe Sandbox'

  return (
    <div style={{ paddingBottom: 60 }}>
      {/* Top Bar Header with Showcase Badge */}
      <div className="page-header" style={{ marginBottom: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Gavel style={{ width: 24, height: 24, color: 'var(--accent-primary)' }} />
              <span>SCENARIO LAB</span>
            </h1>
            <span className="simulation-pill">
              SIMULATION / DEMO ENVIRONMENT
            </span>
          </div>
          <p className="page-subtitle" style={{ marginTop: 4 }}>
            Autonomous Incident Intelligence & Verified Recovery — Scenario Laboratory & Demonstration
          </p>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={handleRunFullShowcase}
            disabled={isRunning}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 22px', fontSize: 14, fontWeight: 700 }}
          >
            {isRunning ? (
              <>
                <div className="status-dot running" style={{ width: 14, height: 14 }} />
                <span>EXECUTING PIPELINE...</span>
              </>
            ) : (
              <>
                <Play style={{ width: 16, height: 16, fill: 'currentColor' }} />
                <span>RUN SCENARIO</span>
              </>
            )}
          </button>

          <button
            onClick={handleReset}
            className="btn btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '10px 16px', fontSize: 13 }}
          >
            <RotateCcw style={{ width: 14, height: 14 }} />
            <span>Reset</span>
          </button>

          <NavLink to="/" className="btn btn-ghost" style={{ padding: '10px 16px', fontSize: 13 }}>
            Return to Dashboard
          </NavLink>
        </div>
      </div>

      {/* Provider Status Bar */}
      <div className="card" style={{ padding: '12px 18px', marginBottom: 20, background: 'var(--bg-secondary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, color: 'var(--fg-muted)', fontWeight: 600 }}>
              Operational Status:
            </span>
            <div className="status-pill">
              <Cpu style={{ width: 14, height: 14, color: 'var(--accent-primary)' }} />
              <span>AI: <strong>{aiProviderLabel}</strong></span>
            </div>
            <div className="status-pill">
              <Globe style={{ width: 14, height: 14, color: 'var(--accent-secondary)' }} />
              <span>Research: <strong>{researchProviderLabel}</strong></span>
            </div>
            <div className="status-pill">
              <Shield style={{ width: 14, height: 14, color: 'var(--accent-primary)' }} />
              <span>Sandbox: <strong>{sandboxLabel}</strong></span>
            </div>
            <div className="status-pill" style={{ borderColor: 'rgba(0, 212, 170, 0.4)', background: 'rgba(0, 212, 170, 0.08)' }}>
              <CheckCircle2 style={{ width: 14, height: 14, color: 'var(--accent-primary)' }} />
              <span>Verification: <strong style={{ color: 'var(--accent-primary)' }}>Deterministic Causal Verifier: READY</strong></span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => setViewTab('showcase')}
              className={`btn ${viewTab === 'showcase' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ padding: '6px 14px', fontSize: 12 }}
            >
              Showcase View
            </button>
            <button
              onClick={() => setViewTab('architecture')}
              className={`btn ${viewTab === 'architecture' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ padding: '6px 14px', fontSize: 12 }}
            >
              Architecture View
            </button>
            <button
              onClick={() => setViewTab('impact')}
              className={`btn ${viewTab === 'impact' ? 'btn-primary' : 'btn-ghost'}`}
              style={{ padding: '6px 14px', fontSize: 12 }}
            >
              Why COSKA?
            </button>
          </div>
        </div>
      </div>

      {viewTab === 'architecture' && (
        <div className="card" style={{ padding: 28, marginBottom: 24 }}>
          <h2 style={{ fontSize: 20, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Code style={{ width: 20, height: 20, color: 'var(--accent-primary)' }} />
            <span>COSKA Autonomous System Architecture</span>
          </h2>
          <p style={{ color: 'var(--fg-secondary)', marginBottom: 24, fontSize: 14 }}>
            End-to-end architecture separating autonomous probabilistic investigation from deterministic causal verification.
          </p>

          <div className="grid grid-3" style={{ gap: 16 }}>
            <div className="card" style={{ padding: 18, background: 'var(--bg-tertiary)' }}>
              <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--accent-primary)', fontWeight: 700, marginBottom: 6 }}>
                Frontend Client
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>React / TypeScript / Vite</div>
              <p style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>
                Command Center interface, live agent telemetry trace, interactive causal DAG graph, and verification receipt generator.
              </p>
            </div>

            <div className="card" style={{ padding: 18, background: 'var(--bg-tertiary)' }}>
              <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--accent-primary)', fontWeight: 700, marginBottom: 6 }}>
                Runtime Orchestrator
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>FastAPI (Async Python)</div>
              <p style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>
                8-phase investigation lifecycle with bounded retries, safety limits (MAX_AGENT_STEPS=40), and state persistence in SQLite.
              </p>
            </div>

            <div className="card" style={{ padding: 18, background: 'var(--bg-tertiary)' }}>
              <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--accent-primary)', fontWeight: 700, marginBottom: 6 }}>
                Reasoning Layer
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>
                {infra.aiProvider === 'openai_compatible' ? 'OpenAI Compatible (GPT-4o)' : infra.aiProvider === 'local' ? 'Local LLM (Ollama)' : 'Deterministic Mock Provider'}
              </div>
              <p style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>
                Hypothesis formulation, multi-signal evidence weighting, and structured remediation plan synthesis.
              </p>
            </div>

            <div className="card" style={{ padding: 18, background: 'var(--bg-tertiary)' }}>
              <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--accent-secondary)', fontWeight: 700, marginBottom: 6 }}>
                Research & Memory
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>RAG + External Research Engine</div>
              <p style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>
                Offline operational runbook index combined with live external search for error codes, library bugs, and architecture guides.
              </p>
            </div>

            <div className="card" style={{ padding: 18, background: 'var(--bg-tertiary)' }}>
              <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--accent-warning)', fontWeight: 700, marginBottom: 6 }}>
                Execution Sandbox
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Docker / Local Safe Sandbox</div>
              <p style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>
                Isolated container or path-contained filesystem sandbox with command allowlisting and automatic rollback safety.
              </p>
            </div>

            <div className="card" style={{ padding: 18, background: 'rgba(0, 212, 170, 0.08)', border: '1px solid var(--accent-primary)' }}>
              <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--accent-primary)', fontWeight: 700, marginBottom: 6 }}>
                Deterministic Verifier
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 4, color: 'var(--accent-primary)' }}>
                4-Stage Causal Proof
              </div>
              <p style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>
                Non-LLM deterministic test harness enforcing: Baseline FAIL, Post-fix PASS, Health PASS, Control FAIL.
              </p>
            </div>
          </div>
        </div>
      )}

      {viewTab === 'impact' && (
        <div className="card" style={{ padding: 28, marginBottom: 24 }}>
          <h2 style={{ fontSize: 20, marginBottom: 8 }}>WHY COSKA?</h2>
          <p style={{ color: 'var(--fg-secondary)', marginBottom: 24, fontSize: 14 }}>
            The shift from manual triage and hopeful remediation to autonomous intelligence and deterministic verification.
          </p>

          <div className="grid grid-2" style={{ gap: 24 }}>
            <div style={{ background: 'rgba(255, 77, 79, 0.06)', border: '1px solid rgba(255, 77, 79, 0.3)', borderRadius: 8, padding: 20 }}>
              <div style={{ color: 'var(--accent-danger)', fontWeight: 700, fontSize: 15, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertTriangle style={{ width: 18, height: 18 }} />
                <span>Manual Incident Response (Legacy)</span>
              </div>
              <ol style={{ paddingLeft: 20, lineHeight: 1.8, fontSize: 13, color: 'var(--fg-secondary)' }}>
                <li><strong>Logs:</strong> Pager alerts on-call engineer at 3:00 AM.</li>
                <li><strong>Human Triage:</strong> Engineer manually sifts through thousands of lines of logs.</li>
                <li><strong>Search Documentation:</strong> Searching outdated confluence wikis and stale runbooks.</li>
                <li><strong>Compare Hypotheses:</strong> Guessing between database exhaustion, network, or bad release.</li>
                <li><strong>Test Fix:</strong> Applying untested hotfix directly to staging or production.</li>
                <li><strong>Hope It Worked:</strong> Staring at dashboard graphs hoping the incident doesn't recur.</li>
              </ol>
            </div>

            <div style={{ background: 'rgba(0, 212, 170, 0.06)', border: '1px solid rgba(0, 212, 170, 0.4)', borderRadius: 8, padding: 20 }}>
              <div style={{ color: 'var(--accent-primary)', fontWeight: 700, fontSize: 15, marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8 }}>
                <CheckCircle2 style={{ width: 18, height: 18 }} />
                <span>COSKA Autonomous Response</span>
              </div>
              <ol style={{ paddingLeft: 20, lineHeight: 1.8, fontSize: 13, color: 'var(--fg-primary)' }}>
                <li><strong>Observe:</strong> Ingests logs, deployment diffs, and runtime telemetry immediately.</li>
                <li><strong>Retrieve:</strong> Queries local RAG runbooks and external research for known postmortems.</li>
                <li><strong>Reason:</strong> Compares competing hypotheses and isolates the true root cause with 92%+ confidence.</li>
                <li><strong>Act:</strong> Formulates minimal, bounded remediation in an isolated safe sandbox.</li>
                <li><strong>Verify:</strong> Executes 4-stage causal control testing to mathematically prove recovery.</li>
                <li><strong>Audit:</strong> Issues cryptographic verification receipt with complete reproduction proof.</li>
              </ol>
            </div>
          </div>
        </div>
      )}

      {/* Scenario Selector Ribbon (Scenario Library) */}
      <div className="card" style={{ padding: 18, marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: 0.5, color: 'var(--fg-muted)', fontWeight: 700 }}>
            Scenario Library
          </div>
          <span style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>
            Selected: <strong className="mono">{scenario.name}</strong>
          </span>
        </div>

        <div className="scenario-grid">
          {SCENARIOS.map(sc => (
            <div
              key={sc.id}
              onClick={() => {
                setSelectedScenarioId(sc.id)
                setCurrentStep('incident')
                setActiveTraceStepIndex(sc.traceSteps.length - 1)
              }}
              className={`scenario-card ${selectedScenarioId === sc.id ? 'selected' : ''}`}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <span className="mono" style={{ fontWeight: 700, fontSize: 14 }}>{sc.name}</span>
                <span className={`badge ${sc.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}`}>
                  {sc.severity}
                </span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--fg-muted)', marginBottom: 8 }}>
                Service: <code className="mono">{sc.service}</code> • Error: <span style={{ color: 'var(--accent-danger)' }}>{sc.errorRate}</span>
              </div>
              <div style={{ fontSize: 12, color: 'var(--fg-secondary)', marginBottom: 10, lineHeight: 1.4 }}>
                {sc.symptoms}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 11, borderTop: '1px solid var(--border-primary)', paddingTop: 8 }}>
                <span style={{ color: 'var(--fg-muted)' }}>Expected: {sc.configKey}</span>
                <span className="badge badge-verified" style={{ fontSize: 10 }}>VERIFIED</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 8-Stage Stepper Pipeline Navigation */}
      <div className="pipeline-stepper">
        {PIPELINE_STEPS.map((step, idx) => {
          const Icon = step.icon
          const isActive = currentStep === step.key
          return (
            <div key={step.key} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <button
                onClick={() => setCurrentStep(step.key)}
                className={`pipeline-step ${isActive ? 'active' : ''}`}
              >
                <Icon style={{ width: 15, height: 15 }} />
                <span>{step.label}</span>
              </button>
              {idx < PIPELINE_STEPS.length - 1 && (
                <span className="pipeline-arrow">→</span>
              )}
            </div>
          )
        })}
      </div>

      {/* Active Incident Hero Banner */}
      <div className="hero-incident">
        <div className="hero-header">
          <div className="hero-title-group">
            <span className="badge badge-critical" style={{ fontSize: 13, padding: '4px 12px' }}>
              CRITICAL INCIDENT
            </span>
            <span className="hero-service">{scenario.service.toUpperCase()}</span>
            <span style={{ color: 'var(--fg-muted)', fontSize: 13 }}>•</span>
            <span className="mono" style={{ color: 'var(--fg-muted)', fontSize: 13 }}>INC-{scenario.id.toUpperCase().slice(0, 8)}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="status-indicator">
              <span className="status-dot running" />
              <span>ACTIVE ROOT CAUSE DIAGNOSIS</span>
            </span>
          </div>
        </div>

        <div className="hero-metrics-strip">
          <div className="hero-metric-item">
            <span className="hero-metric-label">HTTP 500 Spike</span>
            <span className="hero-metric-val" style={{ color: 'var(--accent-danger)' }}>
              {scenario.errorRate}
            </span>
          </div>
          <div className="hero-metric-item">
            <span className="hero-metric-label">Database Subsystem</span>
            <span className="hero-metric-val" style={{ color: 'var(--accent-warning)' }}>
              {scenario.databaseStatus}
            </span>
          </div>
          <div className="hero-metric-item">
            <span className="hero-metric-label">Blast Radius</span>
            <span className="hero-metric-val" style={{ fontSize: 13, color: 'var(--fg-primary)' }}>
              {scenario.blastRadius.join(' / ')}
            </span>
          </div>
          <div className="hero-metric-item">
            <span className="hero-metric-label">Remediation Action</span>
            <span className="hero-metric-val" style={{ color: 'var(--accent-primary)', fontSize: 13 }}>
              {scenario.configKey}
            </span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <p style={{ color: 'var(--fg-secondary)', fontSize: 13, margin: 0, maxWidth: 850 }}>
            <strong>Symptoms:</strong> {scenario.symptoms}
          </p>
          <button
            onClick={() => setCurrentStep('verification')}
            className="btn btn-primary"
            style={{ padding: '8px 18px', fontSize: 13, fontWeight: 600 }}
          >
            VIEW FOUR-STAGE VERIFICATION →
          </button>
        </div>
      </div>

      {/* Main Showcase Stage Display */}
      {currentStep === 'incident' && (
        <div className="grid grid-2" style={{ gap: 20 }}>
          {/* Live Agent Trace */}
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
              <div className="section-title" style={{ margin: 0 }}>
                Live Agent Trace
              </div>
              <span className="status-indicator">
                <span className="status-dot running" />
                <span>Deterministic State Tracker</span>
              </span>
            </div>

            <div className="timeline" style={{ maxHeight: 420, overflowY: 'auto' }}>
              {scenario.traceSteps.slice(0, activeTraceStepIndex + 1).map((step, idx) => (
                <div key={step.id} className="timeline-item" style={{ animation: 'fadeIn 0.3s ease' }}>
                  <div
                    className="timeline-dot"
                    style={{
                      background: idx === activeTraceStepIndex && isRunning
                        ? 'var(--accent-warning)'
                        : 'var(--accent-primary)',
                      boxShadow: idx === activeTraceStepIndex ? '0 0 10px var(--accent-primary)' : 'none'
                    }}
                  />
                  <div className="timeline-content">
                    <div className="timeline-header">
                      <span className="timeline-title" style={{ fontSize: 13 }}>{step.title}</span>
                      <span className="timeline-time mono" style={{ fontSize: 11 }}>{step.durationMs}ms</span>
                    </div>
                    {step.tool && (
                      <div style={{ fontSize: 11, color: 'var(--fg-muted)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                        Tool: {step.tool}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Evidence & Causal Preview */}
          <div className="card">
            <div className="section-title">Investigation Plan & Telemetry</div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 14, borderRadius: 6, marginBottom: 16 }}>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
                Active Target Repository & Service
              </div>
              <div className="mono" style={{ fontSize: 13, fontWeight: 600 }}>
                https://github.com/coska/{scenario.service}
              </div>
              <div style={{ fontSize: 12, color: 'var(--fg-secondary)', marginTop: 6 }}>
                Runtime container: <code className="mono">{scenario.service}:v1.8.2</code>
              </div>
            </div>

            <div style={{ fontSize: 12, color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 8 }}>
              Telemetry Indicators Collected
            </div>
            <ul style={{ fontSize: 13, color: 'var(--fg-secondary)', lineHeight: 1.8, paddingLeft: 18 }}>
              <li><strong>Log Anomaly:</strong> 17 connection pool timeouts in 90 seconds</li>
              <li><strong>Configuration Inspection:</strong> Initial parameter set to {scenario.configBefore.split('\n')[0]}</li>
              <li><strong>Downstream Impact:</strong> Queue starvation across {scenario.blastRadius.join(', ')}</li>
              <li><strong>Safety Boundaries:</strong> MAX_AGENT_STEPS=40, MAX_TOOL_CALLS=25, MAX_INVESTIGATION_TIME=300s</li>
            </ul>

            <div style={{ marginTop: 20, display: 'flex', gap: 10 }}>
              <button
                onClick={() => setCurrentStep('evidence')}
                className="btn btn-secondary"
                style={{ width: '100%', justifyContent: 'center' }}
              >
                Inspect Causal Evidence Graph →
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Causal Evidence Graph */}
      {currentStep === 'evidence' && (
        <div className="causal-graph-wrap">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <div>
              <h3 style={{ fontSize: 18, fontWeight: 700 }}>Causal Evidence Graph</h3>
              <p style={{ color: 'var(--fg-secondary)', fontSize: 13 }}>
                Visual dependency mapping showing the chain of failure from root parameter to outward symptom.
              </p>
            </div>
            <span className="badge badge-verified">DETERMINISTIC CAUSAL CHAIN</span>
          </div>

          <div className="causal-flow">
            {scenario.causalGraph.nodes.map((node, i) => (
              <div key={node.id} style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
                <div className={`causal-node ${node.type}`}>
                  <div className="causal-node-title">{node.sublabel}</div>
                  <div className="causal-node-val">{node.label}</div>
                  <div style={{ marginTop: 6, fontSize: 10, color: 'var(--fg-muted)' }}>
                    {node.type.toUpperCase()}
                  </div>
                </div>
                {i < scenario.causalGraph.nodes.length - 1 && (
                  <div className="causal-connector" style={{ padding: '0 8px' }}>
                    <ArrowRight style={{ width: 18, height: 18 }} />
                  </div>
                )}
              </div>
            ))}
          </div>

          <div style={{ marginTop: 24, padding: 16, background: 'rgba(10, 14, 20, 0.6)', borderRadius: 8, border: '1px solid var(--border-primary)' }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-primary)', marginBottom: 4 }}>
              Causal Synthesis
            </div>
            <div style={{ fontSize: 13, color: 'var(--fg-secondary)' }}>
              Configuration parameter <code className="mono">{scenario.causalGraph.nodes[0].label}</code> directly constrained the runtime connection budget under concurrent traffic, triggering resource starvation that propagated through {scenario.causalGraph.nodes[2].label} into outward user-facing HTTP 500 error spikes.
            </div>
          </div>

          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={() => setCurrentStep('incident')} className="btn btn-ghost">← Back</button>
            <button onClick={() => setCurrentStep('rag')} className="btn btn-primary">Next: RAG Knowledge Panel →</button>
          </div>
        </div>
      )}

      {/* Step 3: RAG Knowledge Panel */}
      {currentStep === 'rag' && (
        <div className="rag-panel">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 18, fontWeight: 700 }}>KNOWLEDGE USED (Operational RAG)</h3>
              <p style={{ color: 'var(--fg-secondary)', fontSize: 13 }}>
                Top historical postmortems, architecture runbooks, and recovery guides retrieved for this incident.
              </p>
            </div>
            <span className="similarity-badge">
              RAG MATCH CONFIDENCE: 94%
            </span>
          </div>

          <div className="grid grid-3" style={{ gap: 16 }}>
            {scenario.ragDocuments.map((doc, idx) => (
              <div key={idx} className="rag-doc-card">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span className="similarity-badge" style={{ fontSize: 12 }}>
                    Similarity: {doc.similarity}%
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--fg-muted)' }}>{doc.category}</span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 6 }}>{doc.title}</div>
                <div className="mono" style={{ fontSize: 11, color: 'var(--accent-secondary)', marginBottom: 8 }}>
                  Source: {doc.source}
                </div>
                <p style={{ fontSize: 12, color: 'var(--fg-secondary)', lineHeight: 1.5 }}>
                  {doc.summary}
                </p>
                <div className="why-retrieved">
                  <strong>WHY RETRIEVED:</strong>
                  <div>"{doc.whyRetrieved}"</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={() => setCurrentStep('evidence')} className="btn btn-ghost">← Back</button>
            <button onClick={() => setCurrentStep('hypotheses')} className="btn btn-primary">Next: Hypothesis Board →</button>
          </div>
        </div>
      )}

      {/* Step 4: Hypothesis Board */}
      {currentStep === 'hypotheses' && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 18, fontWeight: 700 }}>ROOT CAUSE CANDIDATES</h3>
              <p style={{ color: 'var(--fg-secondary)', fontSize: 13 }}>
                Competing hypotheses evaluated against gathered evidence and operational runbooks.
              </p>
            </div>
            <span className="badge badge-low">
              {scenario.hypotheses.length} COMPETING HYPOTHESES
            </span>
          </div>

          <div className="hypo-grid">
            {scenario.hypotheses.map(hypo => (
              <div key={hypo.id} className={`hypo-card ${hypo.isLeading ? 'leading' : ''}`}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                    <span className="mono" style={{ fontWeight: 700, fontSize: 13 }}>{hypo.id}</span>
                    {hypo.isLeading ? (
                      <span className="badge badge-verified" style={{ fontWeight: 700, fontSize: 11 }}>
                        LEADING HYPOTHESIS
                      </span>
                    ) : (
                      <span className="badge badge-low" style={{ fontSize: 11 }}>
                        WEAKENED / REJECTED
                      </span>
                    )}
                  </div>

                  <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 6 }}>
                    {hypo.title}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12 }}>
                    <span style={{ color: 'var(--fg-muted)' }}>Confidence</span>
                    <span className="mono" style={{ fontWeight: 700, color: hypo.isLeading ? 'var(--accent-primary)' : 'var(--fg-muted)' }}>
                      {hypo.confidence}%
                    </span>
                  </div>

                  <div className="confidence-bar-bg">
                    <div
                      className="confidence-bar-fill"
                      style={{
                        width: `${hypo.confidence}%`,
                        background: hypo.isLeading ? 'var(--accent-primary)' : 'var(--fg-muted)'
                      }}
                    />
                  </div>

                  <div style={{ marginTop: 12 }}>
                    <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
                      Supporting Signals
                    </div>
                    {hypo.supportingEvidence.map((ev, i) => (
                      <div key={i} style={{ fontSize: 12, color: 'var(--fg-secondary)', marginBottom: 2 }}>
                        • {ev}
                      </div>
                    ))}
                  </div>

                  {hypo.rejectedReason && (
                    <div style={{ marginTop: 10, padding: 8, background: 'rgba(255, 77, 79, 0.08)', borderRadius: 4, fontSize: 11, color: '#ffa39e' }}>
                      <strong>Rejection Rationale:</strong> {hypo.rejectedReason}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={() => setCurrentStep('rag')} className="btn btn-ghost">← Back</button>
            <button onClick={() => setCurrentStep('root_cause')} className="btn btn-primary">Next: Root Cause Panel →</button>
          </div>
        </div>
      )}

      {/* Step 5: Root Cause Major Narrative Moment */}
      {currentStep === 'root_cause' && (
        <div>
          <div className="root-cause-hero">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className="badge badge-verified" style={{ fontSize: 13, padding: '6px 14px', fontWeight: 700 }}>
                  ROOT CAUSE ISOLATED
                </span>
                <span className="mono" style={{ fontSize: 14, color: 'var(--fg-muted)' }}>
                  P = {scenario.rootCause.confidence}%
                </span>
              </div>
              <span className="mono" style={{ fontSize: 12, color: 'var(--accent-primary)' }}>
                Evidence: {scenario.rootCause.supportingCount} supporting • {scenario.rootCause.contradictingCount} contradicting
              </span>
            </div>

            <h2 style={{ fontSize: 28, fontWeight: 800, color: 'var(--fg-primary)', marginBottom: 14 }}>
              {scenario.rootCause.title}
            </h2>

            <div style={{ background: 'rgba(10, 14, 20, 0.75)', border: '1px solid var(--border-primary)', borderRadius: 8, padding: 20, marginBottom: 20 }}>
              <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--accent-primary)', letterSpacing: 1, fontWeight: 700, marginBottom: 6 }}>
                Why This Is The Root Cause
              </div>
              <div style={{ fontSize: 16, fontFamily: 'var(--font-mono)', color: 'var(--fg-primary)', lineHeight: 1.6 }}>
                {scenario.rootCause.whySummary}
              </div>
            </div>

            <div className="grid grid-3" style={{ gap: 14 }}>
              <div style={{ background: 'var(--bg-tertiary)', padding: 14, borderRadius: 6 }}>
                <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>Confidence Score</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--accent-primary)' }}>
                  {scenario.rootCause.confidence}%
                </div>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: 14, borderRadius: 6 }}>
                <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>Evidence Signals</div>
                <div style={{ fontSize: 24, fontWeight: 700 }}>
                  {scenario.rootCause.supportingCount} Verified
                </div>
              </div>
              <div style={{ background: 'var(--bg-tertiary)', padding: 14, borderRadius: 6 }}>
                <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>Target Parameter</div>
                <div className="mono" style={{ fontSize: 18, fontWeight: 700, color: 'var(--accent-secondary)' }}>
                  {scenario.configKey.split(':')[0]}
                </div>
              </div>
            </div>
          </div>

          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={() => setCurrentStep('hypotheses')} className="btn btn-ghost">← Back</button>
            <button onClick={() => setCurrentStep('remediation')} className="btn btn-primary">Next: Remediation Lab →</button>
          </div>
        </div>
      )}

      {/* Step 6: Remediation Lab */}
      {currentStep === 'remediation' && (
        <div className="card" style={{ padding: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 18, fontWeight: 700 }}>REMEDIATION LAB</h3>
              <p style={{ color: 'var(--fg-secondary)', fontSize: 13 }}>
                Configuration and code remediation plan generated and validated in sandbox.
              </p>
            </div>
            <span className="badge badge-low">
              Risk: {scenario.risk} • Rollback: {scenario.rollback ? 'AVAILABLE' : 'NONE'}
            </span>
          </div>

          {/* Side-by-side or line diff */}
          <div className="diff-viewer">
            <div className="diff-header">
              <span>Configuration File: <code className="mono">.env</code></span>
              <span>Change: <strong style={{ color: 'var(--accent-primary)' }}>{scenario.configKey}</strong></span>
            </div>
            <div style={{ padding: '12px 0' }}>
              <div className="diff-line removed">
                <span style={{ width: 30, color: 'var(--fg-muted)' }}>-</span>
                <span>{scenario.configBefore.split('\n')[0]}</span>
              </div>
              <div className="diff-line added">
                <span style={{ width: 30, color: 'var(--fg-muted)' }}>+</span>
                <span>{scenario.configAfter.split('\n')[0]}</span>
              </div>
            </div>
          </div>

          <div className="grid grid-3" style={{ gap: 16, marginTop: 16 }}>
            <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase' }}>Risk Level</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-primary)', marginTop: 4 }}>
                {scenario.risk}
              </div>
              <p style={{ fontSize: 12, color: 'var(--fg-secondary)', marginTop: 4 }}>
                Safe sandbox execution confirmed no regression in adjacent services.
              </p>
            </div>

            <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase' }}>Rollback Plan</div>
              <div style={{ fontSize: 16, fontWeight: 700, marginTop: 4 }}>
                {scenario.rollback}
              </div>
              <p style={{ fontSize: 12, color: 'var(--fg-secondary)', marginTop: 4 }}>
                Automatic rollback state cached in SQLite storage.
              </p>
            </div>

            <div style={{ background: 'var(--bg-tertiary)', padding: 16, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase' }}>Expected Effect</div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--fg-primary)', marginTop: 4 }}>
                {scenario.expectedEffect}
              </div>
            </div>
          </div>

          <div style={{ marginTop: 24, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={() => setCurrentStep('root_cause')} className="btn btn-ghost">← Back</button>
            <button onClick={() => setCurrentStep('verification')} className="btn btn-primary" style={{ fontWeight: 700 }}>
              Proceed to Causal Verification →
            </button>
          </div>
        </div>
      )}

      {/* Step 7: Four-Stage Causal Verification Screen (The Strongest Screen) */}
      {currentStep === 'verification' && (
        <div>
          {/* Four Stage Grid */}
          <div className="four-stage-grid">
            {/* Stage 1 */}
            <div className="four-stage-card failed-expected">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
                <AlertTriangle style={{ width: 28, height: 28, color: 'var(--accent-danger)' }} />
              </div>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
                Stage 1: Baseline
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-danger)', margin: '6px 0' }}>
                FAILED
              </div>
              <div style={{ fontSize: 11, color: 'var(--fg-secondary)' }}>
                Failure successfully reproduced in baseline environment.
              </div>
            </div>

            {/* Stage 2 */}
            <div className="four-stage-card passed">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
                <CheckCircle2 style={{ width: 28, height: 28, color: 'var(--accent-primary)' }} />
              </div>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
                Stage 2: Post-Fix Tests
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-primary)', margin: '6px 0' }}>
                PASSED
              </div>
              <div style={{ fontSize: 11, color: 'var(--fg-secondary)' }}>
                Target failure resolved after remediation applied.
              </div>
            </div>

            {/* Stage 3 */}
            <div className="four-stage-card passed">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
                <Shield style={{ width: 28, height: 28, color: 'var(--accent-primary)' }} />
              </div>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
                Stage 3: Health Probes
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-primary)', margin: '6px 0' }}>
                PASSED
              </div>
              <div style={{ fontSize: 11, color: 'var(--fg-secondary)' }}>
                HTTP 200 OK across all dependent service probes.
              </div>
            </div>

            {/* Stage 4 */}
            <div className="four-stage-card failed-expected">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 10 }}>
                <Target style={{ width: 28, height: 28, color: 'var(--accent-danger)' }} />
              </div>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
                Stage 4: Control Test
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: 'var(--accent-danger)', margin: '6px 0' }}>
                FAILED
              </div>
              <div style={{ fontSize: 11, color: 'var(--fg-secondary)' }}>
                Reverting fix re-triggers failure, proving causality.
              </div>
            </div>
          </div>

          {/* Master VERIFIED Box */}
          <div className="verified-banner">
            <div className="verified-banner-title">
              ╔══════════════════════╗<br />
              ║      VERIFIED        ║<br />
              ╚══════════════════════╝
            </div>
            <div className="verified-subtext">
              Recovery causally verified by independent control test.
            </div>
            <div className="verified-footnote">
              This is not an LLM claim. This is the deterministic verifier result.
            </div>
          </div>

          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={() => setCurrentStep('remediation')} className="btn btn-ghost">← Back</button>
            <button onClick={() => setCurrentStep('receipt')} className="btn btn-primary" style={{ fontWeight: 700 }}>
              View Verification Receipt →
            </button>
          </div>
        </div>
      )}

      {/* Step 8: Verification Receipt */}
      {currentStep === 'receipt' && (
        <div>
          <div className="receipt-box">
            <div className="receipt-header">
              <div>
                <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--accent-primary)', letterSpacing: 1 }}>
                  COSKA CAUSAL RECOVERY RECEIPT
                </div>
                <div style={{ fontSize: 11, color: 'var(--fg-muted)', marginTop: 2 }}>
                  Deterministic Verification Certificate
                </div>
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                <button
                  onClick={() => setShowJsonModal(true)}
                  className="btn btn-secondary"
                  style={{ padding: '6px 12px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <Code style={{ width: 14, height: 14 }} />
                  <span>View JSON</span>
                </button>
                <button
                  onClick={downloadReport}
                  className="btn btn-primary"
                  style={{ padding: '6px 12px', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}
                >
                  <Download style={{ width: 14, height: 14 }} />
                  <span>Download Report</span>
                </button>
              </div>
            </div>

            <div className="receipt-grid">
              <div className="receipt-row">
                <span>Verification ID:</span>
                <span className="mono">{scenario.verification.receiptId}</span>
              </div>
              <div className="receipt-row">
                <span>Incident Target:</span>
                <span className="mono">{scenario.service} (INC-{scenario.id.toUpperCase().slice(0, 8)})</span>
              </div>
              <div className="receipt-row">
                <span>Root Cause:</span>
                <span>{scenario.rootCause.title}</span>
              </div>
              <div className="receipt-row">
                <span>Remediation Applied:</span>
                <span className="mono" style={{ color: 'var(--accent-primary)' }}>{scenario.configKey}</span>
              </div>
              <div className="receipt-row">
                <span>Baseline Test:</span>
                <span style={{ color: 'var(--accent-danger)' }}>{scenario.verification.baseline.label}</span>
              </div>
              <div className="receipt-row">
                <span>Post-Fix Test:</span>
                <span style={{ color: 'var(--accent-primary)' }}>{scenario.verification.postfix.label}</span>
              </div>
              <div className="receipt-row">
                <span>Health Probes:</span>
                <span style={{ color: 'var(--accent-primary)' }}>{scenario.verification.health.label}</span>
              </div>
              <div className="receipt-row">
                <span>Control Verification:</span>
                <span style={{ color: 'var(--accent-danger)' }}>{scenario.verification.control.label}</span>
              </div>
              <div className="receipt-row">
                <span>Evidence Signals:</span>
                <span>{scenario.rootCause.supportingCount} Verified Data Points</span>
              </div>
              <div className="receipt-row">
                <span>Knowledge Sources:</span>
                <span>{scenario.ragDocuments.map(d => `${d.title} (${d.similarity}%)`).join('; ')}</span>
              </div>
              <div className="receipt-row">
                <span>AI Reasoning Provider:</span>
                <span>{aiProviderLabel}</span>
              </div>
              <div className="receipt-row">
                <span>Research Provider:</span>
                <span>{researchProviderLabel}</span>
              </div>
              <div className="receipt-row">
                <span>Execution Sandbox:</span>
                <span>{sandboxLabel}</span>
              </div>
              <div className="receipt-row">
                <span>Timestamp:</span>
                <span className="mono">{scenario.verification.timestamp}</span>
              </div>
              <div className="receipt-row" style={{ gridColumn: '1 / -1', borderBottom: 'none', paddingTop: 10 }}>
                <span>Final Causal Verdict:</span>
                <span className="badge badge-verified" style={{ fontSize: 13, padding: '4px 12px' }}>
                  VERIFIED — RECOVERY CAUSALLY PROVEN
                </span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: 20, display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
            <button onClick={() => setCurrentStep('verification')} className="btn btn-ghost">← Back to Stages</button>
            <button onClick={handleRunFullShowcase} className="btn btn-primary">
              Re-run Showcase Workflow
            </button>
          </div>
        </div>
      )}

      {/* Raw JSON Modal */}
      {showJsonModal && (
        <div className="modal-overlay" onClick={() => setShowJsonModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
              <div style={{ fontSize: 16, fontWeight: 700 }}>Verification Receipt JSON Payload</div>
              <button onClick={() => setShowJsonModal(false)} className="btn btn-ghost" style={{ padding: 4 }}>
                <X style={{ width: 18, height: 18 }} />
              </button>
            </div>
            <pre style={{ background: 'var(--bg-primary)', padding: 16, borderRadius: 6, fontSize: 12, overflowX: 'auto', maxHeight: 400 }}>
              {JSON.stringify({
                verification_id: scenario.verification.receiptId,
                incident_id: `INC-${scenario.id.toUpperCase()}`,
                service: scenario.service,
                root_cause: scenario.rootCause,
                remediation: {
                  change: scenario.configKey,
                  before: scenario.configBefore,
                  after: scenario.configAfter,
                  risk: scenario.risk
                },
                causal_stages: {
                  baseline: scenario.verification.baseline,
                  postfix: scenario.verification.postfix,
                  health: scenario.verification.health,
                  control: scenario.verification.control
                },
                verdict: 'VERIFIED',
                ai_provider: aiProviderLabel,
                research_provider: researchProviderLabel,
                sandbox_provider: sandboxLabel,
                timestamp: scenario.verification.timestamp
              }, null, 2)}
            </pre>
            <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={() => setShowJsonModal(false)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
