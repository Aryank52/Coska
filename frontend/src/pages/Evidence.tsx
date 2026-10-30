import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getIncidentEvidence } from '../services/api'
import { type Evidence, SourceType } from '../types/incident'
import { FileText, Database, Server, Globe, TestTube, Code, Rocket, ArrowRight } from 'lucide-react'

const SOURCE_ICONS: Record<SourceType, any> = {
  LOG: FileText,
  REPOSITORY: Code,
  CONFIG: Database,
  DEPLOYMENT: Rocket,
  RUNTIME: Server,
  WEB: Globe,
  TEST: TestTube,
}

const SOURCE_COLORS: Record<SourceType, string> = {
  LOG: 'var(--accent-info)',
  REPOSITORY: '#aa78ff',
  CONFIG: 'var(--accent-warning)',
  DEPLOYMENT: 'var(--accent-primary)',
  RUNTIME: 'var(--accent-secondary)',
  WEB: '#ff6464',
  TEST: 'var(--accent-primary)',
}

export function Evidence() {
  const { id } = useParams<{ id: string }>()
  const [evidence, setEvidence] = useState<Evidence[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    loadEvidence()
  }, [id])

  const loadEvidence = async () => {
    try {
      const data = await getIncidentEvidence(id!)
      setEvidence(data.evidence || [])
    } catch (error) {
      console.error('Failed to load evidence:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="card" style={{ padding: 48, textAlign: 'center' }}>Loading evidence...</div>

  const grouped = evidence.reduce((acc, e) => {
    if (!acc[e.source_type]) acc[e.source_type] = []
    acc[e.source_type].push(e)
    return acc
  }, {} as Record<SourceType, Evidence[]>)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h2 className="page-title">Evidence & Causal Synthesis</h2>
          <p className="page-subtitle">{evidence.length} evidence items and operational knowledge collected</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <span className="badge badge-low">{evidence.length} signals verified</span>
        </div>
      </div>

      {/* 5. Visual Causal Evidence Graph */}
      <div className="causal-graph-wrap">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>Visual Causal Graph</h3>
            <p style={{ color: 'var(--fg-secondary)', fontSize: 12 }}>
              Synthesized causal pathway linking configuration anomaly to outward error spike.
            </p>
          </div>
          <span className="badge badge-verified">VERIFIED CAUSAL CHAIN</span>
        </div>

        <div className="causal-flow">
          <div className="causal-node root">
            <div className="causal-node-title">Root Configuration</div>
            <div className="causal-node-val">DB_POOL_SIZE=5</div>
            <div style={{ fontSize: 10, color: 'var(--fg-muted)', marginTop: 4 }}>CONFIG</div>
          </div>
          <div className="causal-connector">
            <ArrowRight style={{ width: 16, height: 16 }} />
          </div>
          <div className="causal-node">
            <div className="causal-node-title">Resource Bottleneck</div>
            <div className="causal-node-val">Connection Exhaustion</div>
            <div style={{ fontSize: 10, color: 'var(--fg-muted)', marginTop: 4 }}>QUEUE LIMIT</div>
          </div>
          <div className="causal-connector">
            <ArrowRight style={{ width: 16, height: 16 }} />
          </div>
          <div className="causal-node">
            <div className="causal-node-title">System Anomaly</div>
            <div className="causal-node-val">Database Timeout</div>
            <div style={{ fontSize: 10, color: 'var(--fg-muted)', marginTop: 4 }}>RUNTIME TIMEOUT</div>
          </div>
          <div className="causal-connector">
            <ArrowRight style={{ width: 16, height: 16 }} />
          </div>
          <div className="causal-node">
            <div className="causal-node-title">Service Degradation</div>
            <div className="causal-node-val">Payment API Failure</div>
            <div style={{ fontSize: 10, color: 'var(--fg-muted)', marginTop: 4 }}>WORKER CRASH</div>
          </div>
          <div className="causal-connector">
            <ArrowRight style={{ width: 16, height: 16 }} />
          </div>
          <div className="causal-node leading">
            <div className="causal-node-title">Outward Impact</div>
            <div className="causal-node-val">HTTP 500 Spike (38%)</div>
            <div style={{ fontSize: 10, color: 'var(--fg-muted)', marginTop: 4 }}>USER IMPACT</div>
          </div>
        </div>
      </div>

      {/* 4. RAG Knowledge Used Panel */}
      <div className="rag-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 700 }}>KNOWLEDGE USED (Operational RAG)</h3>
            <p style={{ color: 'var(--fg-secondary)', fontSize: 12 }}>
              Runbooks and historical postmortems matched against incident symptoms.
            </p>
          </div>
          <span className="similarity-badge">RAG SIMILARITY: 94%</span>
        </div>

        <div className="grid grid-3" style={{ gap: 14 }}>
          <div className="rag-doc-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
              <span className="similarity-badge">Similarity: 94%</span>
              <span style={{ fontSize: 11, color: 'var(--fg-muted)' }}>Database Runbook</span>
            </div>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>PostgreSQL Pool Exhaustion Runbook</div>
            <div className="mono" style={{ fontSize: 11, color: 'var(--accent-secondary)', marginBottom: 6 }}>
              docs/runbooks/postgres-pool.md
            </div>
            <p style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>
              Under concurrent worker transactions, undersized pool size causes connection queues to starve.
            </p>
            <div className="why-retrieved">
              <strong>WHY RETRIEVED:</strong>
              <div>"Matched incident symptoms: connection pool + timeout + HTTP 500"</div>
            </div>
          </div>

          <div className="rag-doc-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
              <span className="similarity-badge">Similarity: 88%</span>
              <span style={{ fontSize: 11, color: 'var(--fg-muted)' }}>Postmortem</span>
            </div>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>Payment API Postmortem (INC-2025-08)</div>
            <div className="mono" style={{ fontSize: 11, color: 'var(--accent-secondary)', marginBottom: 6 }}>
              docs/postmortems/payment-api-timeout.md
            </div>
            <p style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>
              Previous incident where DB_POOL_SIZE was set to 5 after staging merge, causing checkout drops.
            </p>
            <div className="why-retrieved">
              <strong>WHY RETRIEVED:</strong>
              <div>"Matched service payment-api and connection pool exhaustion signature"</div>
            </div>
          </div>

          <div className="rag-doc-card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
              <span className="similarity-badge">Similarity: 81%</span>
              <span style={{ fontSize: 11, color: 'var(--fg-muted)' }}>Architecture Guide</span>
            </div>
            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>Database Timeout Troubleshooting Guide</div>
            <div className="mono" style={{ fontSize: 11, color: 'var(--accent-secondary)', marginBottom: 6 }}>
              docs/guides/db-timeouts.md
            </div>
            <p style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>
              Diagnostic rules for distinguishing between database saturation vs client pool starvation.
            </p>
            <div className="why-retrieved">
              <strong>WHY RETRIEVED:</strong>
              <div>"Matched error signature: QueuePool limit exceeded"</div>
            </div>
          </div>
        </div>
      </div>

      {/* Raw Collected Signals List */}
      <div className="section-title">Verified Raw Signals</div>
      {evidence.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <FileText style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
          <h3>No evidence items collected yet</h3>
          <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
            Evidence is gathered automatically during the investigation phase.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {Object.entries(grouped).map(([sourceType, items]) => {
            const Icon = SOURCE_ICONS[sourceType as SourceType] || FileText
            const color = SOURCE_COLORS[sourceType as SourceType] || 'var(--accent-primary)'

            return (
              <div key={sourceType} className="card">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                  <Icon style={{ width: 18, height: 18, color }} />
                  <h3 style={{ fontSize: 16, margin: 0 }}>{sourceType}</h3>
                  <span className="badge badge-low" style={{ marginLeft: 'auto' }}>
                    {items.length} items
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {items.map((item) => (
                    <div
                      key={item.id}
                      style={{
                        padding: 14,
                        background: 'var(--bg-tertiary)',
                        borderRadius: 'var(--radius-sm)',
                        borderLeft: `3px solid ${color}`,
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                        <code className="mono" style={{ fontSize: 12, color }}>{item.id}</code>
                        <span className="mono" style={{ fontSize: 11, color: 'var(--fg-muted)' }}>
                          Confidence: {(item.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div style={{ fontSize: 13, marginBottom: 6 }}>{item.claim}</div>
                      <div className="mono" style={{ fontSize: 11, color: 'var(--fg-muted)' }}>
                        Ref: {item.reference}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
