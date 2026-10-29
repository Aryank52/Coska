import { Outlet } from 'react-router-dom'
import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getIncident, getIncidentTimeline, getIncidentActions, investigateIncident } from '../services/api'
import { IncidentResponse, TimelineEvent, AgentAction } from '../types/incident'
import { NavLink } from 'react-router-dom'
import { Play, RotateCcw, AlertTriangle, CheckCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

const TABS = [
  { path: '', label: 'Investigation', icon: '🔍' },
  { path: 'evidence', label: 'Evidence', icon: '📋' },
  { path: 'hypotheses', label: 'Hypotheses', icon: '💡' },
  { path: 'root-cause', label: 'Root Cause', icon: '🎯' },
  { path: 'remediation', label: 'Remediation', icon: '🛠️' },
  { path: 'verification', label: 'Verification', icon: '✅' },
]

export function IncidentDetail() {
  const { id } = useParams<{ id: string }>()
  const [incident, setIncident] = useState<IncidentResponse | null>(null)
  const [timeline, setTimeline] = useState<TimelineEvent[]>([])
  const [actions, setActions] = useState<AgentAction[]>([])
  const [loading, setLoading] = useState(true)
  const [investigating, setInvestigating] = useState(false)

  useEffect(() => {
    if (!id) return
    loadIncident()
    
    const interval = setInterval(() => {
      if (!investigating) loadIncident()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [id, investigating])

  const loadIncident = async () => {
    try {
      const [incidentData, timelineData, actionsData] = await Promise.all([
        getIncident(id!),
        getIncidentTimeline(id!),
        getIncidentActions(id!),
      ])
      setIncident(incidentData)
      setTimeline(timelineData.timeline || [])
      setActions(actionsData.actions || [])
    } catch (error) {
      console.error('Failed to load incident:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleInvestigate = async () => {
    if (!incident) return
    setInvestigating(true)
    try {
      await investigateIncident(id!, true)
      // Poll for completion
      const pollInterval = setInterval(async () => {
        const updated = await getIncident(id!)
        setIncident(updated)
        if (updated.status === 'RESOLVED' || updated.status === 'VERIFICATION_FAILED') {
          clearInterval(pollInterval)
          setInvestigating(false)
        }
      }, 3000)
    } catch (error) {
      console.error('Investigation failed:', error)
      setInvestigating(false)
    }
  }

  const getStatusBadge = (status: string) => {
    const badges: Record<string, string> = {
      'CRITICAL': 'badge-critical',
      'HIGH': 'badge-high',
      'MEDIUM': 'badge-medium',
      'LOW': 'badge-low',
      'RESOLVED': 'badge-verified',
      'VERIFYING': 'badge-unverified',
      'INVESTIGATING': 'badge-unverified',
      'RECEIVED': 'badge-low',
    }
    return badges[status] || 'badge-low'
  }

  const getSeverityBadge = (severity: string) => {
    const badges: Record<string, string> = {
      'CRITICAL': 'badge-critical',
      'HIGH': 'badge-high',
      'MEDIUM': 'badge-medium',
      'LOW': 'badge-low',
    }
    return badges[severity] || 'badge-low'
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '500px' }}>
        <div className="status-dot running" style={{ width: 24, height: 24, marginBottom: 16 }} />
        <p>Loading investigation...</p>
      </div>
    )
  }

  if (!incident) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 48 }}>
        <AlertTriangle style={{ width: 48, height: 48, color: 'var(--accent-warning)', marginBottom: 16 }} />
        <h2>Incident not found</h2>
        <p className="mono" style={{ marginTop: 8 }}>{id}</p>
      </div>
    )
  }

  return (
    <div>
      {/* Incident Header */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
              <code className="mono" style={{ fontSize: 18, fontWeight: 600 }}>{incident.id}</code>
              <span className={`badge ${getSeverityBadge(incident.severity)}`}>{incident.severity}</span>
              <span className={`badge ${getStatusBadge(incident.status)}`}>{incident.status.replace('_', ' ')}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, color: 'var(--fg-secondary)', fontSize: 13 }}>
              <span><strong>Service:</strong> <code className="mono">{incident.service}</code></span>
              <span><strong>Created:</strong> {formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}</span>
              <span><strong>Updated:</strong> {formatDistanceToNow(new Date(incident.updated_at), { addSuffix: true })}</span>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {incident.status !== 'RESOLVED' && incident.status !== 'VERIFYING' && incident.status !== 'INVESTIGATING' && (
              <button 
                onClick={handleInvestigate}
                disabled={investigating}
                className="btn btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: 8 }}
              >
                {investigating ? (
                  <>
                    <div className="status-dot running" style={{ width: 14, height: 14 }} />
                    Investigating...
                  </>
                ) : (
                  <>
                    <Play style={{ width: 16, height: 16 }} />
                    Start Investigation
                  </>
                )}
              </button>
            )}
            {incident.status === 'INVESTIGATING' && (
              <button className="btn btn-secondary" disabled>
                <RotateCcw className="mono" style={{ width: 16, height: 16, animation: 'spin 1s linear infinite' }} />
                Investigating...
              </button>
            )}
            {incident.status === 'VERIFYING' && (
              <button className="btn btn-secondary" disabled>
                <CheckCircle style={{ width: 16, height: 16 }} />
                Verifying...
              </button>
            )}
            {incident.status === 'RESOLVED' && (
              <span className="badge badge-verified" style={{ padding: '8px 16px', fontSize: 13 }}>
                <CheckCircle style={{ width: 14, height: 14, marginRight: 6 }} />
                RESOLVED - VERIFIED
              </span>
            )}
          </div>
        </div>

        <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border-primary)' }}>
          <p style={{ color: 'var(--fg-secondary)', lineHeight: 1.6 }}>{incident.description}</p>
          
          {(incident.deployment || incident.repository) && (
            <div style={{ marginTop: 16, display: 'flex', gap: 24, flexWrap: 'wrap', fontSize: 13, color: 'var(--fg-muted)' }}>
              {incident.deployment && (
                <div><strong>Deployment:</strong> <code className="mono">{incident.deployment}</code></div>
              )}
              {incident.repository && (
                <div><strong>Repository:</strong> <code className="mono">{incident.repository}</code></div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 16, borderBottom: '1px solid var(--border-primary)', paddingBottom: 4 }}>
        {TABS.map((tab) => (
          <NavLink
            key={tab.path}
            to={`${id}${tab.path ? '/' + tab.path : ''}`}
            className={({ isActive }) => 
              `btn ${isActive ? 'btn-primary' : 'btn-ghost'}`}
            style={{ 
              padding: '10px 16px', 
              fontSize: 13,
              borderRadius: 'var(--radius-sm)  var(--radius-sm) 0 0',
              borderBottom: 'none'
            }}
          >
            <span style={{ marginRight: 6 }}>{tab.icon}</span>
            {tab.label}
          </NavLink>
        ))}
      </div>

      {/* Agent Activity Timeline */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="section-title">Agent Activity</div>
        <div className="timeline">
          {actions.slice().reverse().map((action, _index) => (
            <div key={action.id} className="timeline-item">
              <div 
                className={`timeline-dot ${action.status === 'COMPLETED' ? 'info' : action.status === 'FAILED' ? 'critical' : 'info'}`}
                style={{ background: action.status === 'COMPLETED' ? 'var(--accent-primary)' : 'var(--accent-danger)' }}
              />
              <div className="timeline-content">
                <div className="timeline-header">
                  <span className="timeline-title">{action.step.replace('_', ' ')}</span>
                  <span className="timeline-time mono">
                    {formatDistanceToNow(new Date(action.timestamp), { addSuffix: true })}
                    {action.duration_ms > 0 && ` • ${action.duration_ms}ms`}
                  </span>
                </div>
                <div className="timeline-description">{action.summary}</div>
                {action.tool && (
                  <div style={{ marginTop: 8, fontSize: 11, color: 'var(--fg-muted)', fontFamily: 'var(--font-mono)' }}>
                    Tool: {action.tool}
                  </div>
                )}
              </div>
            </div>
          ))}
          {actions.length === 0 && (
            <div className="timeline-item">
              <div className="timeline-dot idle" />
              <div className="timeline-content">
                <p style={{ color: 'var(--fg-muted)' }}>No agent activity yet. Start investigation to begin.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Incident Timeline */}
      <div className="card">
        <div className="section-title">Incident Timeline</div>
        <div className="timeline">
          {timeline.map((event, index) => (
            <div key={index} className="timeline-item">
              <div className={`timeline-dot ${event.severity.toLowerCase()}`} />
              <div className="timeline-content">
                <div className="timeline-header">
                  <span className="timeline-title">{event.title}</span>
                  <span className="timeline-time mono">
                    {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                  </span>
                </div>
                <div className="timeline-description">{event.description}</div>
                <div style={{ marginTop: 8, fontSize: 11, color: 'var(--fg-muted)' }}>
                  Source: {event.source_type} {event.evidence_ids.length > 0 && ` • Evidence: ${event.evidence_ids.join(', ')}`}
                </div>
              </div>
            </div>
          ))}
          {timeline.length === 0 && (
            <div className="timeline-item">
              <div className="timeline-dot idle" />
              <div className="timeline-content">
                <p style={{ color: 'var(--fg-muted)' }}>Timeline will be built during investigation.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Child routes render here */}
      <Outlet />
    </div>
  )
}