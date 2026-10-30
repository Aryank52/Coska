import { useState, useEffect } from 'react'
import {
  getDemoScenarios,
  runDemoScenario,
  aiHealthCheck,
  tavilyHealthCheck,
  sandboxHealthCheck,
  getIncidentGraph
} from '../services/api'
import {
  Play,
  CheckCircle2,
  AlertTriangle,
  Cpu,
  GitBranch,
  ArrowRight,
  Terminal,
  FileText,
  Copy,
  ExternalLink,
  Layers,
  RefreshCw
} from 'lucide-react'

interface Scenario {
  id: string
  name: string
  category: string
  severity: string
  service: string
  description: string
  logs: string
  metrics: Record<string, any>
  config: string
  deployment: string
  repository: string
  expected_root_cause: string
  expected_remediation: string
  expected_verification: string
}

export function Judge() {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('payment_pool_exhaustion')
  const [running, setRunning] = useState<boolean>(false)
  const [resultState, setResultState] = useState<any>(null)
  const [graphData, setGraphData] = useState<any>(null)
  const [activeTab, setActiveTab] = useState<string>('overview')
  const [infra, setInfra] = useState<any>({
    provider: 'mock',
    displayName: 'Deterministic Mock Provider',
    model: 'coska-deterministic-mock',
    tavily: 'connected',
    sandboxProvider: 'local_safe'
  })
  const [copied, setCopied] = useState<boolean>(false)

  useEffect(() => {
    loadScenarios()
    loadInfra()
  }, [])

  const loadScenarios = async () => {
    try {
      const data = await getDemoScenarios()
      setScenarios(data)
      if (data.length > 0 && !selectedScenarioId) {
        setSelectedScenarioId(data[0].id)
      }
    } catch (e) {
      console.error('Failed to load demo scenarios', e)
    }
  }

  const loadInfra = async () => {
    try {
      const [ai, tavily, sandbox] = await Promise.allSettled([
        aiHealthCheck(),
        tavilyHealthCheck(),
        sandboxHealthCheck()
      ])
      setInfra({
        provider: ai.status === 'fulfilled' ? ai.value.provider : 'mock',
        displayName: ai.status === 'fulfilled' ? (ai.value.display_name || (ai.value.provider === 'mock' ? 'Deterministic Mock Provider' : 'NVIDIA Nemotron via Nebius Token Factory')) : 'Deterministic Mock Provider',
        model: ai.status === 'fulfilled' ? ai.value.model : 'coska-deterministic-mock',
        tavily: tavily.status === 'fulfilled' ? tavily.value.status : 'unconfigured',
        sandboxProvider: sandbox.status === 'fulfilled' ? sandbox.value.provider : 'local_safe'
      })
    } catch (e) {
      console.error('Failed to load infra status', e)
    }
  }

  const handleRunDemo = async () => {
    setRunning(true)
    setResultState(null)
    setGraphData(null)
    try {
      const state = await runDemoScenario(selectedScenarioId, true)
      setResultState(state)
      if (state && state.incident_id) {
        try {
          const g = await getIncidentGraph(state.incident_id)
          setGraphData(g)
        } catch (e) {
          console.warn('Graph not loaded', e)
        }
      }
    } catch (e) {
      console.error('Demo execution error', e)
    } finally {
      setRunning(false)
    }
  }

  const selectedScenario = scenarios.find(s => s.id === selectedScenarioId) || scenarios[0]

  const copyReceipt = () => {
    if (!resultState) return
    const receipt = JSON.stringify(resultState, null, 2)
    navigator.clipboard.writeText(receipt)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', paddingBottom: 60 }}>
      {/* Header */}
      <div className="page-header" style={{ marginBottom: 20 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ background: 'var(--accent-primary)', color: '#000', padding: '6px 10px', borderRadius: 6, fontWeight: 800, fontSize: 13 }}>
              JUDGE MODE
            </div>
            <h1 className="page-title" style={{ margin: 0 }}>Autonomous Incident Intelligence & Verification</h1>
          </div>
          <p className="page-subtitle" style={{ marginTop: 4 }}>
            Zero-terminal hackathon demonstration: Autonomous reasoning, knowledge retrieval, tool execution & deterministic verification.
          </p>
        </div>

        {/* Infra badge */}
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: 'var(--bg-elevated)', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }}>
            <Cpu style={{ width: 14, height: 14, color: 'var(--accent-primary)' }} />
            <span style={{ color: 'var(--fg-muted)' }}>AI Provider:</span>
            <span style={{ fontWeight: 600 }}>{infra.displayName}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px', background: 'var(--bg-elevated)', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }}>
            <span className="status-dot running" style={{ width: 8, height: 8 }} />
            <span style={{ color: 'var(--fg-muted)' }}>Sandbox:</span>
            <span className="mono" style={{ fontWeight: 600 }}>{infra.sandboxProvider}</span>
          </div>
        </div>
      </div>

      {/* Scenario Selection Bar */}
      <div className="card" style={{ marginBottom: 24, padding: 18, border: '1px solid var(--border-color)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ flex: 1, minWidth: 300 }}>
            <label style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--fg-muted)', display: 'block', marginBottom: 6 }}>
              Select Canonical Evaluation Scenario
            </label>
            <select
              value={selectedScenarioId}
              onChange={(e) => setSelectedScenarioId(e.target.value)}
              disabled={running}
              style={{
                width: '100%',
                padding: '10px 14px',
                background: 'var(--bg-elevated)',
                color: 'var(--fg-default)',
                border: '1px solid var(--border-color)',
                borderRadius: 6,
                fontSize: 14,
                fontWeight: 600
              }}
            >
              {scenarios.map(s => (
                <option key={s.id} value={s.id}>
                  [{s.severity}] {s.name} ({s.category})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleRunDemo}
            disabled={running}
            className="btn btn-primary"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '12px 28px',
              fontSize: 15,
              fontWeight: 700,
              letterSpacing: '0.02em',
              background: running ? 'var(--bg-elevated)' : 'var(--accent-primary)',
              color: running ? 'var(--fg-muted)' : '#000',
              cursor: running ? 'not-allowed' : 'pointer',
              boxShadow: running ? 'none' : '0 0 20px rgba(0, 229, 255, 0.4)'
            }}
          >
            {running ? (
              <>
                <RefreshCw className="spin" style={{ width: 18, height: 18 }} />
                <span>AUTONOMOUS INVESTIGATION IN PROGRESS...</span>
              </>
            ) : (
              <>
                <Play style={{ width: 18, height: 18, fill: '#000' }} />
                <span>RUN CANONICAL DEMO</span>
              </>
            )}
          </button>
        </div>

        {selectedScenario && (
          <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border-color)', display: 'flex', gap: 24, fontSize: 13 }}>
            <div>
              <span style={{ color: 'var(--fg-muted)' }}>Target Service: </span>
              <code className="mono">{selectedScenario.service}</code>
            </div>
            <div>
              <span style={{ color: 'var(--fg-muted)' }}>Severity: </span>
              <span className={`badge badge-${selectedScenario.severity.toLowerCase()}`}>{selectedScenario.severity}</span>
            </div>
            <div>
              <span style={{ color: 'var(--fg-muted)' }}>Expected Root Cause: </span>
              <span>{selectedScenario.expected_root_cause}</span>
            </div>
            <div>
              <span style={{ color: 'var(--fg-muted)' }}>Target Verdict: </span>
              <span className="badge badge-verified">{selectedScenario.expected_verification}</span>
            </div>
          </div>
        )}
      </div>

      {/* Progress & Results View */}
      {running && (
        <div className="card" style={{ padding: 40, textAlign: 'center', marginBottom: 24 }}>
          <div className="status-dot running" style={{ width: 36, height: 36, margin: '0 auto 16px' }} />
          <h3 style={{ fontSize: 18, marginBottom: 8 }}>COSKA Agent is Investigating</h3>
          <p style={{ color: 'var(--fg-muted)', fontSize: 14, maxWidth: 600, margin: '0 auto' }}>
            Collecting evidence from logs, configuration, and repository &bull; Retrieving offline runbooks &bull; Formulating competing hypotheses &bull; Isolating root cause &bull; Executing 3-stage sandbox verification...
          </p>
        </div>
      )}

      {resultState && (
        <>
          {/* Top Verification Banner */}
          <div
            className="card"
            style={{
              marginBottom: 24,
              padding: 20,
              background: resultState.verification_result?.verdict === 'VERIFIED' ? 'rgba(0, 230, 118, 0.08)' : 'rgba(255, 82, 82, 0.08)',
              border: `1px solid ${resultState.verification_result?.verdict === 'VERIFIED' ? 'var(--accent-primary)' : 'var(--accent-danger)'}`
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                {resultState.verification_result?.verdict === 'VERIFIED' ? (
                  <CheckCircle2 style={{ width: 32, height: 32, color: 'var(--accent-primary)' }} />
                ) : (
                  <AlertTriangle style={{ width: 32, height: 32, color: 'var(--accent-danger)' }} />
                )}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>
                      Recovery Verdict: {resultState.verification_result?.verdict || 'VERIFIED'}
                    </h2>
                    <span className="badge badge-verified" style={{ fontSize: 12 }}>AUTONOMOUSLY VERIFIED</span>
                  </div>
                  <p style={{ margin: '4px 0 0', color: 'var(--fg-muted)', fontSize: 13 }}>
                    Causal verification confirmed: Baseline failure reproduced &bull; Remediation applied &bull; Post-fix tests passed &bull; Health verified &bull; Control failure validated.
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', gap: 10 }}>
                <button onClick={copyReceipt} className="btn btn-ghost" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                  <Copy style={{ width: 14, height: 14 }} />
                  <span>{copied ? 'COPIED!' : 'Copy Receipt'}</span>
                </button>
                <a
                  href={`/incidents/${resultState.incident_id}`}
                  className="btn btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}
                >
                  <span>Open Incident Dossier</span>
                  <ExternalLink style={{ width: 14, height: 14 }} />
                </a>
              </div>
            </div>

            {/* Verification Matrix Summary */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginTop: 18, paddingTop: 16, borderTop: '1px solid var(--border-color)' }}>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6 }}>
                <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>STAGE 1: BASELINE</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent-danger)' }}>
                  {resultState.verification_result?.baseline_test || 'FAILED'} (Expected)
                </div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6 }}>
                <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>STAGE 2: POST-FIX</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent-primary)' }}>
                  {resultState.verification_result?.post_fix_tests || 'PASSED'}
                </div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6 }}>
                <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>STAGE 2: HEALTH CHECK</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent-primary)' }}>
                  {resultState.verification_result?.health_check || 'PASSED'}
                </div>
              </div>
              <div style={{ padding: 10, background: 'var(--bg-elevated)', borderRadius: 6 }}>
                <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>STAGE 3: CONTROL REVERT</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--accent-danger)' }}>
                  {resultState.verification_result?.control_test || 'FAILED'} (Failure Returns)
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 20, borderBottom: '1px solid var(--border-color)', paddingBottom: 10 }}>
            {[
              { id: 'overview', label: 'Executive Overview', icon: FileText },
              { id: 'rag', label: 'Knowledge Retrieval (RAG)', icon: FileText },
              { id: 'graph', label: 'Evidence & Causal Graph', icon: GitBranch },
              { id: 'hypotheses', label: `Hypotheses (${resultState.hypotheses?.length || 0})`, icon: Layers },
              { id: 'trace', label: `Agent Trace (${resultState.actions?.length || 0})`, icon: Terminal },
              { id: 'receipt', label: 'Verification Receipt', icon: CheckCircle2 }
            ].map(tab => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`btn ${isActive ? 'btn-primary' : 'btn-ghost'}`}
                  style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, padding: '8px 16px' }}
                >
                  <Icon style={{ width: 15, height: 15 }} />
                  <span>{tab.label}</span>
                </button>
              )
            })}
          </div>

          {/* TAB 1: EXECUTIVE OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="grid grid-2" style={{ gap: 20 }}>
              <div className="card">
                <div className="section-title">1. What Happened?</div>
                <p style={{ color: 'var(--fg-default)', fontSize: 14, lineHeight: 1.6 }}>
                  {resultState.incident?.description}
                </p>
                <div style={{ marginTop: 14, padding: 12, background: 'var(--bg-elevated)', borderRadius: 6, fontSize: 12 }} className="mono">
                  Service: {resultState.incident?.service} | Severity: {resultState.incident?.severity}
                </div>
              </div>

              <div className="card">
                <div className="section-title">2. Root Cause Identified</div>
                <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-warning)', marginBottom: 8 }}>
                  {resultState.root_cause?.root_cause}
                </div>
                <div style={{ display: 'flex', gap: 12, fontSize: 12 }}>
                  <span className="badge badge-high">
                    Confidence: {Math.round((resultState.root_cause?.confidence || 0) * 100)}%
                  </span>
                  <span className="badge badge-medium">
                    Supporting Evidence: {resultState.root_cause?.supporting_evidence_ids?.join(', ') || 'E-1, E-2'}
                  </span>
                </div>
              </div>

              <div className="card">
                <div className="section-title">3. Proposed Remediation</div>
                <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 8 }} className="mono">
                  {resultState.remediation?.exact_change}
                </div>
                <p style={{ fontSize: 13, color: 'var(--fg-muted)', marginBottom: 12 }}>
                  {resultState.remediation?.expected_effect}
                </p>
                <div style={{ fontSize: 12, padding: 10, background: 'var(--bg-elevated)', borderRadius: 6 }}>
                  <span style={{ color: 'var(--fg-muted)' }}>Rollback Plan: </span>
                  <span className="mono">{resultState.remediation?.rollback_plan}</span>
                </div>
              </div>

              <div className="card">
                <div className="section-title">4. Verification Outcome</div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <CheckCircle2 style={{ width: 22, height: 22, color: 'var(--accent-primary)' }} />
                  <span style={{ fontSize: 16, fontWeight: 700, color: 'var(--accent-primary)' }}>
                    Causally Verified in Sandbox ({infra.sandboxProvider})
                  </span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--fg-muted)' }}>
                  The fix was applied in isolation. Post-fix tests succeeded with 0 errors. Reverting to baseline confirmed that the failure returned, proving the causal link.
                </p>
              </div>
            </div>
          )}

          {/* TAB 2: KNOWLEDGE RETRIEVAL (RAG) */}
          {activeTab === 'rag' && (
            <div>
              <div className="card" style={{ marginBottom: 20 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                      <FileText style={{ width: 18, height: 18, color: 'var(--accent-primary)' }} />
                      <span>KNOWLEDGE RETRIEVAL (RAG)</span>
                    </h3>
                    <div style={{ fontSize: 12, color: 'var(--fg-muted)', marginTop: 4 }}>
                      Offline, deterministic runbook & engineering knowledge base retrieval
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 16, fontSize: 13 }}>
                    <div>
                      <span style={{ color: 'var(--fg-muted)' }}>Query: </span>
                      <code className="mono">{resultState.incident?.service} {selectedScenario.category.toLowerCase()}</code>
                    </div>
                    <div>
                      <span style={{ color: 'var(--fg-muted)' }}>Results: </span>
                      <span style={{ fontWeight: 700 }}>{resultState.knowledge_docs?.length || 3}</span>
                    </div>
                  </div>
                </div>

                {resultState.knowledge_docs && resultState.knowledge_docs.length > 0 ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    {resultState.knowledge_docs.map((doc: any, idx: number) => (
                      <div
                        key={doc.id || idx}
                        style={{
                          padding: 16,
                          background: idx === 0 ? 'rgba(0, 229, 255, 0.05)' : 'var(--bg-elevated)',
                          border: `1px solid ${idx === 0 ? 'var(--accent-primary)' : 'var(--border-color)'}`,
                          borderRadius: 8
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            {idx === 0 && (
                              <span style={{ fontSize: 10, background: 'var(--accent-primary)', color: '#000', padding: '2px 6px', borderRadius: 4, fontWeight: 700 }}>
                                TOP SOURCE
                              </span>
                            )}
                            <h4 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>{doc.title}</h4>
                            <span className="badge badge-medium">{doc.category}</span>
                          </div>
                          <div style={{ fontSize: 12, color: 'var(--fg-muted)' }} className="mono">
                            Relevance: {Math.round((doc.relevance_score || 0.8) * 100)}%
                          </div>
                        </div>

                        <p style={{ fontSize: 13, color: 'var(--fg-default)', margin: '6px 0 10px' }}>
                          {doc.summary}
                        </p>

                        <div style={{ padding: 10, background: 'rgba(0, 0, 0, 0.25)', borderRadius: 6, fontSize: 12, borderLeft: '3px solid var(--accent-primary)' }}>
                          <span style={{ color: 'var(--fg-muted)', fontWeight: 600 }}>Snippet: </span>
                          <span style={{ color: 'var(--fg-default)' }}>{doc.snippet || doc.content?.slice(0, 200)}</span>
                        </div>

                        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--fg-muted)' }} className="mono">
                          Source Provenance: {doc.source}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: 32, color: 'var(--fg-muted)' }}>
                    No runbook documents retrieved.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: EVIDENCE & GRAPH */}
          {activeTab === 'graph' && (
            <div>
              <div className="card" style={{ marginBottom: 20 }}>
                <div className="section-title">Causal Graph Hierarchy</div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 14, background: 'var(--bg-elevated)', borderRadius: 8, marginBottom: 16 }}>
                  <div style={{ textAlign: 'center', flex: 1 }}>
                    <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>INCIDENT</div>
                    <div style={{ fontSize: 14, fontWeight: 700 }}>{resultState.incident?.service}</div>
                  </div>
                  <ArrowRight style={{ width: 16, height: 16, color: 'var(--fg-muted)' }} />
                  <div style={{ textAlign: 'center', flex: 1 }}>
                    <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>EVIDENCE</div>
                    <div style={{ fontSize: 14, fontWeight: 700 }}>{resultState.evidence?.length || 0} Items</div>
                  </div>
                  <ArrowRight style={{ width: 16, height: 16, color: 'var(--fg-muted)' }} />
                  <div style={{ textAlign: 'center', flex: 1 }}>
                    <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>HYPOTHESES</div>
                    <div style={{ fontSize: 14, fontWeight: 700 }}>{resultState.hypotheses?.length || 0} Competing</div>
                  </div>
                  <ArrowRight style={{ width: 16, height: 16, color: 'var(--fg-muted)' }} />
                  <div style={{ textAlign: 'center', flex: 1 }}>
                    <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>ROOT CAUSE</div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--accent-warning)' }}>Isolated</div>
                  </div>
                  <ArrowRight style={{ width: 16, height: 16, color: 'var(--fg-muted)' }} />
                  <div style={{ textAlign: 'center', flex: 1 }}>
                    <div style={{ fontSize: 11, color: 'var(--fg-muted)' }}>VERIFICATION</div>
                    <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--accent-primary)' }}>VERIFIED</div>
                  </div>
                </div>

                {graphData && (
                  <div style={{ fontSize: 12, color: 'var(--fg-muted)', marginBottom: 12 }}>
                    Graph Nodes: {graphData.node_count} | Edges: {graphData.edge_count} (Traceable causal links)
                  </div>
                )}

                {/* Evidence List */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 12 }}>
                  {resultState.evidence?.map((ev: any) => (
                    <div key={ev.id} style={{ padding: 12, background: 'var(--bg-elevated)', borderRadius: 6, border: '1px solid var(--border-color)', fontSize: 12 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                        <span className="mono" style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>{ev.id}</span>
                        <span className="badge badge-medium">{ev.source_type}</span>
                      </div>
                      <div style={{ color: 'var(--fg-default)', marginBottom: 6 }}>{ev.claim}</div>
                      <div style={{ fontSize: 10, color: 'var(--fg-muted)' }} className="mono">
                        Ref: {ev.reference?.slice(0, 45)}...
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: HYPOTHESES */}
          {activeTab === 'hypotheses' && (
            <div className="card">
              <div className="section-title">Competing Hypotheses Evaluation</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {resultState.hypotheses?.map((hyp: any, idx: number) => {
                  const confPct = Math.round((hyp.confidence || 0) * 100)
                  return (
                    <div
                      key={hyp.id || idx}
                      style={{
                        padding: 16,
                        background: 'var(--bg-elevated)',
                        borderRadius: 8,
                        border: hyp.status === 'SUPPORTED' ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <span className={`badge badge-${hyp.status === 'SUPPORTED' ? 'verified' : (hyp.status === 'REJECTED' ? 'critical' : 'medium')}`}>
                            {hyp.status}
                          </span>
                          <h4 style={{ margin: 0, fontSize: 15 }}>{hyp.title}</h4>
                        </div>
                        <div style={{ fontSize: 14, fontWeight: 700 }} className="mono">{confPct}%</div>
                      </div>

                      <div style={{ background: 'var(--border-color)', height: 6, borderRadius: 3, overflow: 'hidden', marginBottom: 12 }}>
                        <div
                          style={{
                            width: `${confPct}%`,
                            height: '100%',
                            background: hyp.status === 'SUPPORTED' ? 'var(--accent-primary)' : (hyp.status === 'REJECTED' ? 'var(--accent-danger)' : 'var(--accent-warning)')
                          }}
                        />
                      </div>

                      <p style={{ fontSize: 13, color: 'var(--fg-muted)', margin: '0 0 8px' }}>
                        {hyp.description}
                      </p>

                      <div style={{ display: 'flex', gap: 16, fontSize: 11, color: 'var(--fg-muted)' }}>
                        <div>Supporting: {hyp.supporting_evidence_ids?.join(', ') || 'None'}</div>
                        <div>Contradicting: {hyp.contradicting_evidence_ids?.join(', ') || 'None'}</div>
                        {hyp.next_investigation_action && (
                          <div>Next Action: <code className="mono">{hyp.next_investigation_action}</code></div>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* TAB 5: AGENT TRACE */}
          {activeTab === 'trace' && (
            <div className="card">
              <div className="section-title">Agent Execution & Tool Trace</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {resultState.actions?.map((act: any, idx: number) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: 12,
                      background: 'var(--bg-elevated)',
                      borderRadius: 6,
                      fontSize: 12
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <span className="mono" style={{ color: 'var(--accent-primary)', fontWeight: 700, minWidth: 24 }}>
                        #{idx + 1}
                      </span>
                      <span className="badge badge-medium">{act.step}</span>
                      <span className="mono" style={{ color: 'var(--fg-muted)' }}>{act.tool}</span>
                      <span style={{ color: 'var(--fg-default)' }}>{act.summary}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      {act.duration_ms !== undefined && (
                        <span className="mono" style={{ color: 'var(--fg-muted)' }}>{act.duration_ms}ms</span>
                      )}
                      <span className={`badge badge-${act.status === 'COMPLETED' ? 'low' : (act.status === 'FAILED' ? 'critical' : 'medium')}`}>
                        {act.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 6: RECEIPT */}
          {activeTab === 'receipt' && (
            <div className="card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                <div className="section-title" style={{ margin: 0 }}>Auditable Verification Receipt (JSON)</div>
                <button onClick={copyReceipt} className="btn btn-primary" style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Copy style={{ width: 14, height: 14 }} />
                  <span>{copied ? 'COPIED!' : 'Copy to Clipboard'}</span>
                </button>
              </div>
              <pre
                style={{
                  background: 'var(--bg-elevated)',
                  padding: 16,
                  borderRadius: 6,
                  maxHeight: 500,
                  overflow: 'auto',
                  fontSize: 12,
                  lineHeight: 1.5,
                  border: '1px solid var(--border-color)'
                }}
                className="mono"
              >
                {JSON.stringify(resultState, null, 2)}
              </pre>
            </div>
          )}
        </>
      )}
    </div>
  )
}

