import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getIncident, getIncidentRootCause, getIncidentRemediation } from '../services/api'
import { IncidentResponse, RootCause, Remediation } from '../types/incident'
import { AlertTriangle, CheckCircle, Clock, Search, Lightbulb, Target, Shield, CheckCircle2, RotateCcw } from 'lucide-react'

const STEPS = [
  { key: 'TRIAGING', label: 'Triage', icon: AlertTriangle },
  { key: 'COLLECTING_EVIDENCE', label: 'Collect Evidence', icon: Search },
  { key: 'BUILDING_TIMELINE', label: 'Build Timeline', icon: Clock },
  { key: 'GENERATING_HYPOTHESES', label: 'Generate Hypotheses', icon: Lightbulb },
  { key: 'INVESTIGATING', label: 'Investigate', icon: Target },
  { key: 'RESEARCHING', label: 'Research External', icon: Shield },
  { key: 'ROOT_CAUSE_IDENTIFIED', label: 'Root Cause', icon: CheckCircle },
  { key: 'REMEDIATION_PROPOSED', label: 'Remediation', icon: Shield },
  { key: 'APPLYING_FIX', label: 'Apply Fix', icon: Target },
  { key: 'VERIFYING', label: 'Verify', icon: CheckCircle2 },
  { key: 'RESOLVED', label: 'Resolved', icon: CheckCircle2 },
]

export function Investigation() {
  const { id } = useParams<{ id: string }>()
  const [incident, setIncident] = useState<IncidentResponse | null>(null)
  const [rootCause, setRootCause] = useState<RootCause | null>(null)
  const [remediation, setRemediation] = useState<Remediation | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    loadData()
    const interval = setInterval(loadData, 5000)
    return () => clearInterval(interval)
  }, [id])

  const loadData = async () => {
    try {
      const [incidentData, rootCauseData, remediationData] = await Promise.all([
        getIncident(id!),
        getIncidentRootCause(id!).catch(() => null),
        getIncidentRemediation(id!).catch(() => null),
      ])
      setIncident(incidentData)
      setRootCause(rootCauseData?.root_cause || null)
      setRemediation(remediationData || null)
    } catch (error) {
      console.error('Failed to load investigation:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="card" style={{ padding: 48, textAlign: 'center' }}>Loading...</div>
  }

  if (!incident) {
    return <div className="card" style={{ padding: 48, textAlign: 'center' }}>Incident not found</div>
  }

  const currentStepIndex = STEPS.findIndex(s => s.key === incident.status)
  const completedSteps = currentStepIndex >= 0 ? currentStepIndex : 0

  return (
    <div>
      {/* Investigation Progress */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="section-title">Investigation Progress</div>
        <div style={{ display: 'flex', gap: 8, overflowX: 'auto', padding: '8px 4px' }}>
          {STEPS.map((step, index) => {
            const isCompleted = index < completedSteps
            const isCurrent = index === completedSteps && incident.status !== 'RESOLVED'
            const isFuture = index > completedSteps
            
            return (
              <div key={step.key} style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                minWidth: 120,
                opacity: isFuture ? 0.4 : 1,
                position: 'relative'
              }}>
                <div style={{
                  width: 40,
                  height: 40,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: isCompleted ? 'var(--accent-primary)' : isCurrent ? 'var(--accent-info)' : 'var(--bg-tertiary)',
                  border: isCurrent ? '2px solid var(--accent-info)' : '1px solid var(--border-primary)',
                  color: isCompleted || isCurrent ? 'var(--bg-primary)' : 'var(--fg-muted)',
                  transition: 'all 0.3s',
                }}>
                  {isCompleted ? (
                    <CheckCircle style={{ width: 20, height: 20 }} />
                  ) : isCurrent ? (
                    <RotateCcw style={{ width: 20, height: 20, animation: 'spin 1s linear infinite' }} />
                  ) : (
                    <step.icon style={{ width: 20, height: 20 }} />
                  )}
                </div>
                <span style={{ 
                  marginTop: 8, 
                  fontSize: 11, 
                  textAlign: 'center',
                  color: isFuture ? 'var(--fg-muted)' : 'var(--fg-primary)',
                  fontWeight: isCurrent ? 600 : 400
                }}>
                  {step.label}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Current Status Summary */}
      <div className="grid grid-3" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="section-title">Current Phase</div>
          <div style={{ fontSize: 24, fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--accent-info)' }}>
            {incident.status.replace('_', ' ')}
          </div>
        </div>
        <div className="card">
          <div className="section-title">Evidence Collected</div>
          <div style={{ fontSize: 24, fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>
            {rootCause ? 'Analyzed' : 'In Progress'}
          </div>
        </div>
        <div className="card">
          <div className="section-title">Hypotheses</div>
          <div style={{ fontSize: 24, fontWeight: 600, fontFamily: 'var(--font-mono)', color: 'var(--accent-warning)' }}>
            {rootCause ? 'Evaluated' : 'Generating...'}
          </div>
        </div>
      </div>

      {/* Root Cause Preview */}
      {rootCause && (
        <div className="card" style={{ marginBottom: 24, borderColor: 'var(--accent-primary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <CheckCircle style={{ width: 20, height: 20, color: 'var(--accent-primary)' }} />
            <div className="section-title" style={{ margin: 0 }}>Root Cause Identified</div>
          </div>
          <div style={{ fontSize: 16, fontWeight: 500, marginBottom: 8 }}>{rootCause.root_cause}</div>
          <div style={{ display: 'flex', gap: 16, fontSize: 13, color: 'var(--fg-muted)' }}>
            <span>Confidence: <strong style={{ color: 'var(--accent-primary)' }}>{(rootCause.confidence * 100).toFixed(0)}%</strong></span>
            <span>Evidence: <strong>{rootCause.supporting_evidence_ids.length}</strong> supporting</span>
          </div>
        </div>
      )}

      {/* Remediation Preview */}
      {remediation && (
        <div className="card" style={{ marginBottom: 24, borderColor: 'var(--accent-info)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <Shield style={{ width: 20, height: 20, color: 'var(--accent-info)' }} />
            <div className="section-title" style={{ margin: 0 }}>Remediation Proposed</div>
          </div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 14, marginBottom: 8 }}>
            {remediation.exact_change}
          </div>
          <div style={{ fontSize: 13, color: 'var(--fg-secondary)' }}>
            {remediation.description}
          </div>
          <div style={{ marginTop: 12, display: 'flex', gap: 16, fontSize: 12, color: 'var(--fg-muted)' }}>
            <span>Risk: <strong>{remediation.risk}</strong></span>
            <span>Blast Radius: <strong>{remediation.blast_radius}</strong></span>
          </div>
        </div>
      )}

      {/* Next Actions */}
      <div className="card">
        <div className="section-title">Next Actions</div>
        {incident.status === 'RESOLVED' ? (
          <div style={{ textAlign: 'center', padding: 24 }}>
            <CheckCircle2 style={{ width: 48, height: 48, color: 'var(--accent-primary)', marginBottom: 16 }} />
            <h3>Investigation Complete</h3>
            <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
              Root cause identified, remediation applied and verified.
            </p>
            <div style={{ marginTop: 16, display: 'flex', gap: 12, justifyContent: 'center' }}>
              <a href={`/incidents/${id}/verification`} className="btn btn-primary">
                View Verification Report
              </a>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div className="status-indicator">
              <span className="status-dot running" />
              <span>Autonomous investigation in progress...</span>
            </div>
            <div style={{ fontSize: 13, color: 'var(--fg-muted)' }}>
              The agent is currently executing the investigation workflow. Check the Evidence, Hypotheses, 
              and Root Cause tabs for detailed findings as they become available.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}