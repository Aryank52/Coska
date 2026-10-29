import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getIncidentHypotheses } from '../services/api'
import { Hypothesis, HypothesisStatus } from '../types/incident'
import { CheckCircle, XCircle, AlertTriangle, Radio } from 'lucide-react'

const STATUS_CONFIG: Record<HypothesisStatus, { color: string; icon: any; label: string }> = {
  SUPPORTED: { color: 'var(--accent-primary)', icon: CheckCircle, label: 'SUPPORTED' },
  REJECTED: { color: 'var(--accent-danger)', icon: XCircle, label: 'REJECTED' },
  WEAKENED: { color: 'var(--accent-warning)', icon: AlertTriangle, label: 'WEAKENED' },
  ACTIVE: { color: 'var(--accent-info)', icon: Radio, label: 'ACTIVE' },
}

export function Hypotheses() {
  const { id } = useParams<{ id: string }>()
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    loadHypotheses()
  }, [id])

  const loadHypotheses = async () => {
    try {
      const data = await getIncidentHypotheses(id!)
      setHypotheses(data.hypotheses || [])
    } catch (error) {
      console.error('Failed to load hypotheses:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="card" style={{ padding: 48, textAlign: 'center' }}>Loading hypotheses...</div>

  const sorted = [...hypotheses].sort((a, b) => b.confidence - a.confidence)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h2 className="page-title">Hypotheses</h2>
          <p className="page-subtitle">Competing root cause explanations ranked by confidence</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <span className="badge badge-low">{hypotheses.length} hypotheses</span>
        </div>
      </div>

      {hypotheses.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <Radio style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
          <h3>No hypotheses generated yet</h3>
          <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
            Hypotheses will be generated during the investigation phase based on collected evidence.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {sorted.map((h, index) => {
            const config = STATUS_CONFIG[h.status]
            const Icon = config.icon
            
            return (
              <div key={h.id} className={`hypothesis-card ${h.status.toLowerCase()}`}>
                <div className="hypothesis-header">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span style={{ 
                      width: 32, 
                      height: 32, 
                      borderRadius: '50%', 
                      background: `${config.color}20`,
                      color: config.color,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}>
                      <Icon style={{ width: 16, height: 16 }} />
                    </span>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span className="hypothesis-title">{index + 1}. {h.title}</span>
                        <span className={`badge ${h.status === 'SUPPORTED' ? 'badge-verified' : h.status === 'REJECTED' ? 'badge-failed' : 'badge-unverified'}`}>
                          {config.label}
                        </span>
                      </div>
                      <div style={{ fontSize: 12, color: 'var(--fg-muted)', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
                        ID: {h.id}
                      </div>
                    </div>
                  </div>
                  <div className="hypothesis-confidence" style={{ color: config.color }}>
                    {(h.confidence * 100).toFixed(0)}%
                  </div>
                </div>
                
                <div className="hypothesis-description">{h.description}</div>
                
                <div className="hypothesis-evidence">
                  {h.supporting_evidence_ids.map(eid => (
                    <span key={eid} className="evidence-tag supporting">{eid}</span>
                  ))}
                  {h.contradicting_evidence_ids.map(eid => (
                    <span key={eid} className="evidence-tag contradicting">{eid}</span>
                  ))}
                  {(h.supporting_evidence_ids.length === 0 && h.contradicting_evidence_ids.length === 0) && (
                    <span className="evidence-tag" style={{ background: 'var(--bg-tertiary)', color: 'var(--fg-muted)' }}>
                      No linked evidence
                    </span>
                  )}
                </div>
                
                {h.next_investigation_action && (
                  <div className="hypothesis-action">
                    Next: {h.next_investigation_action}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}