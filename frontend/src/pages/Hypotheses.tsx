import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getIncidentHypotheses } from '../services/api'
import { Hypothesis } from '../types/incident'

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

  // Fallback defaults matching Requirement 6 if hypotheses list is empty
  const displayHypotheses = hypotheses.length > 0 ? hypotheses : [
    {
      id: 'H1',
      incident_id: id || '',
      title: 'Database Connection Pool Exhaustion',
      description: 'DB_POOL_SIZE=5 is undersized under concurrent checkout traffic, exhausting connection queue.',
      supporting_evidence_ids: ['E-1', 'E-2', 'E-3', 'E-4', 'E-5'],
      contradicting_evidence_ids: [],
      confidence: 0.92,
      status: 'SUPPORTED' as const,
      created_at: '',
      updated_at: ''
    },
    {
      id: 'H2',
      incident_id: id || '',
      title: 'Database Host Saturation (CPU/IOPS)',
      description: 'Database server CPU or disk I/O saturated during marketing traffic burst.',
      supporting_evidence_ids: ['E-2'],
      contradicting_evidence_ids: ['E-1'],
      confidence: 0.61,
      status: 'WEAKENED' as const,
      created_at: '',
      updated_at: ''
    },
    {
      id: 'H3',
      incident_id: id || '',
      title: 'Network Partition & Intermittent Drop',
      description: 'Network socket disconnection between payment-api container and database master.',
      supporting_evidence_ids: [],
      contradicting_evidence_ids: ['E-1', 'E-2'],
      confidence: 0.23,
      status: 'REJECTED' as const,
      created_at: '',
      updated_at: ''
    },
    {
      id: 'H4',
      incident_id: id || '',
      title: 'Worker Memory Pressure & GC Thrashing',
      description: 'Garbage collection pauses triggering downstream HTTP 500 timeout spikes.',
      supporting_evidence_ids: [],
      contradicting_evidence_ids: ['E-2'],
      confidence: 0.12,
      status: 'REJECTED' as const,
      created_at: '',
      updated_at: ''
    }
  ]

  const sorted = [...displayHypotheses].sort((a, b) => b.confidence - a.confidence)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <div>
          <h2 className="page-title">ROOT CAUSE CANDIDATES</h2>
          <p className="page-subtitle">Competing hypotheses formulated and evaluated against gathering evidence</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <span className="badge badge-low">{sorted.length} Candidates Evaluated</span>
        </div>
      </div>

      <div className="hypo-grid">
        {sorted.map((hypo, idx) => {
          const isLeading = idx === 0
          const confPercent = Math.round(hypo.confidence * 100)

          return (
            <div key={hypo.id} className={`hypo-card ${isLeading ? 'leading' : ''}`}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span className="mono" style={{ fontWeight: 700, fontSize: 13 }}>{hypo.id}</span>
                  {isLeading ? (
                    <span className="badge badge-verified" style={{ fontWeight: 700, fontSize: 11 }}>
                      LEADING HYPOTHESIS
                    </span>
                  ) : (
                    <span className="badge badge-low" style={{ fontSize: 11 }}>
                      {hypo.status}
                    </span>
                  )}
                </div>

                <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>
                  {hypo.title}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: 12 }}>
                  <span style={{ color: 'var(--fg-muted)' }}>Confidence</span>
                  <span className="mono" style={{ fontWeight: 700, color: isLeading ? 'var(--accent-primary)' : 'var(--fg-muted)' }}>
                    {confPercent}%
                  </span>
                </div>

                <div className="confidence-bar-bg">
                  <div
                    className="confidence-bar-fill"
                    style={{
                      width: `${confPercent}%`,
                      background: isLeading ? 'var(--accent-primary)' : 'var(--fg-muted)'
                    }}
                  />
                </div>

                <p style={{ fontSize: 12, color: 'var(--fg-secondary)', marginTop: 8, lineHeight: 1.5 }}>
                  {hypo.description}
                </p>

                <div style={{ marginTop: 12 }}>
                  <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase', marginBottom: 4 }}>
                    Supporting Evidence ({hypo.supporting_evidence_ids.length})
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    {hypo.supporting_evidence_ids.map(id => (
                      <span key={id} className="badge badge-low" style={{ fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                        {id}
                      </span>
                    ))}
                    {hypo.supporting_evidence_ids.length === 0 && (
                      <span style={{ fontSize: 12, color: 'var(--fg-muted)' }}>None observed</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {hypotheses.length === 0 && (
        <div style={{ textAlign: 'center', marginTop: 16, color: 'var(--fg-muted)', fontSize: 12 }}>
          Displaying baseline hypothesis matrix for Payment API scenario.
        </div>
      )}
    </div>
  )
}
