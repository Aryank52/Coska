import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getIncidentRootCause } from '../services/api'
import { RootCause } from '../types/incident'
import { CheckCircle, XCircle, AlertTriangle, Target, Shield, Info } from 'lucide-react'

export function RootCause() {
  const { id } = useParams<{ id: string }>()
  const [rootCause, setRootCause] = useState<RootCause | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    loadRootCause()
  }, [id])

  const loadRootCause = async () => {
    try {
      const data = await getIncidentRootCause(id!)
      setRootCause(data.root_cause || null)
    } catch (error) {
      console.error('Failed to load root cause:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="card" style={{ padding: 48, textAlign: 'center' }}>Loading root cause analysis...</div>

  if (!rootCause) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 48 }}>
        <Target style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
        <h3>Root cause not yet identified</h3>
        <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
          The root cause analysis will appear here once the investigation reaches the root cause identification phase.
        </p>
      </div>
    )
  }

  const confidenceColor = rootCause.confidence >= 0.8 ? 'var(--accent-primary)' : 
                          rootCause.confidence >= 0.5 ? 'var(--accent-warning)' : 'var(--accent-danger)'

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h2 className="page-title">Root Cause Analysis</h2>
          <p className="page-subtitle">Evidence-backed root cause identification</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="badge" style={{ background: `${confidenceColor}20`, color: confidenceColor }}>
            Confidence: {(rootCause.confidence * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Root Cause */}
      <div className="card" style={{ marginBottom: 24, borderColor: 'var(--accent-primary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <Target style={{ width: 20, height: 20, color: 'var(--accent-primary)' }} />
          <div className="section-title" style={{ margin: 0 }}>Root Cause</div>
        </div>
        <div style={{ fontSize: 20, fontWeight: 600, lineHeight: 1.3, marginBottom: 16 }}>
          {rootCause.root_cause}
        </div>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', fontSize: 13, color: 'var(--fg-muted)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <span style={{ width: 8, height: 8, borderRadius: '50%', background: confidenceColor }} />
            <span>Confidence: <strong style={{ color: confidenceColor }}>{(rootCause.confidence * 100).toFixed(0)}%</strong></span>
          </div>
          {rootCause.uncertainty && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--accent-warning)' }}>
              <AlertTriangle style={{ width: 14, height: 14 }} />
              <span>Uncertainty: {rootCause.uncertainty}</span>
            </div>
          )}
        </div>
      </div>

      {/* Why - Explanation */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <Info style={{ width: 20, height: 20, color: 'var(--accent-secondary)' }} />
          <div className="section-title" style={{ margin: 0 }}>Why</div>
        </div>
        <div style={{ 
          background: 'var(--bg-tertiary)', 
          borderRadius: 'var(--radius-sm)', 
          padding: 16, 
          fontSize: 14, 
          lineHeight: 1.7,
          border: '1px solid var(--border-primary)',
          fontFamily: 'var(--font-mono)',
          whiteSpace: 'pre-wrap'
        }}>
          {rootCause.supporting_evidence_ids.length > 0 ? (
            <>
              This conclusion is based on the following evidence chain:<br/><br/>
              {rootCause.supporting_evidence_ids.map((eid, i) => (
                <span key={eid} style={{ display: 'block', marginBottom: 4 }}>
                  {i + 1}. {eid} - Supporting evidence
                </span>
              ))}
            </>
          ) : (
            <span style={{ color: 'var(--fg-muted)' }}>Detailed evidence trace available in Evidence tab.</span>
          )}
        </div>
      </div>

      {/* Supporting Evidence */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <CheckCircle style={{ width: 20, height: 20, color: 'var(--accent-primary)' }} />
          <div className="section-title" style={{ margin: 0 }}>Supporting Evidence ({rootCause.supporting_evidence_ids.length})</div>
        </div>
        {rootCause.supporting_evidence_ids.length > 0 ? (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {rootCause.supporting_evidence_ids.map(eid => (
              <span key={eid} className="evidence-tag supporting">{eid}</span>
            ))}
          </div>
        ) : (
          <p style={{ color: 'var(--fg-muted)' }}>No supporting evidence linked.</p>
        )}
      </div>

      {/* Contradicting Evidence */}
      {rootCause.contradicting_evidence_ids.length > 0 && (
        <div className="card" style={{ marginBottom: 24, borderColor: 'var(--accent-danger)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <XCircle style={{ width: 20, height: 20, color: 'var(--accent-danger)' }} />
            <div className="section-title" style={{ margin: 0 }}>Contradicting Evidence ({rootCause.contradicting_evidence_ids.length})</div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {rootCause.contradicting_evidence_ids.map(eid => (
              <span key={eid} className="evidence-tag contradicting">{eid}</span>
            ))}
          </div>
        </div>
      )}

      {/* Rejected Hypotheses */}
      {rootCause.rejected_hypotheses.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <XCircle style={{ width: 20, height: 20, color: 'var(--accent-danger)' }} />
            <div className="section-title" style={{ margin: 0 }}>Rejected Hypotheses ({rootCause.rejected_hypotheses.length})</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {rootCause.rejected_hypotheses.map((rh, i) => (
              <div key={i} style={{ 
                background: 'var(--bg-tertiary)', 
                borderRadius: 'var(--radius-sm)', 
                padding: '12px 16px',
                border: '1px solid var(--border-primary)',
                opacity: 0.7
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="mono" style={{ fontSize: 11 }}>{rh.id}</span>
                  <span style={{ color: 'var(--fg-secondary)' }}>{rh.reason}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Remediation Preview */}
      {rootCause.recommended_remediation && (
        <div className="card" style={{ borderColor: 'var(--accent-info)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Shield style={{ width: 20, height: 20, color: 'var(--accent-info)' }} />
            <div className="section-title" style={{ margin: 0 }}>Recommended Remediation</div>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 16, fontWeight: 600, marginBottom: 8, color: 'var(--accent-info)' }}>
            {rootCause.recommended_remediation.exact_change}
          </div>
          <div style={{ color: 'var(--fg-secondary)', marginBottom: 12 }}>
            {rootCause.recommended_remediation.description}
          </div>
          <div style={{ display: 'flex', gap: 24, fontSize: 12, color: 'var(--fg-muted)', flexWrap: 'wrap' }}>
            <span>Expected: {rootCause.recommended_remediation.expected_effect}</span>
            <span>Risk: <strong>{rootCause.recommended_remediation.risk}</strong></span>
            <span>Rollback: {rootCause.recommended_remediation.rollback_plan}</span>
          </div>
        </div>
      )}
    </div>
  )
}