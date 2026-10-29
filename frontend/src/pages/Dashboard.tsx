import { useState, useEffect } from 'react'
import { api } from '../services/api'
import { Incident, IncidentResponse } from '../types/incident'
import { Clock, AlertTriangle, Activity, CheckCircle, TrendingUp } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export function Dashboard() {
  const [incidents, setIncidents] = useState<IncidentResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    active: 0,
    critical: 0,
    investigating: 0,
    resolvedToday: 0
  })

  useEffect(() => {
    loadIncidents()
    const interval = setInterval(loadIncidents, 10000)
    return () => clearInterval(interval)
  }, [])

  const loadIncidents = async () => {
    try {
      const data = await api.getIncidents()
      setIncidents(data)
      
      const now = new Date()
      const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
      
      setStats({
        active: data.filter(i => i.status !== 'RESOLVED').length,
        critical: data.filter(i => i.severity === 'CRITICAL' && i.status !== 'RESOLVED').length,
        investigating: data.filter(i => i.status === 'INVESTIGATING').length,
        resolvedToday: data.filter(i => 
          i.status === 'RESOLVED' && new Date(i.updated_at) >= todayStart
        ).length
      })
    } catch (error) {
      console.error('Failed to load incidents:', error)
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CRITICAL': return 'badge-critical'
      case 'HIGH': return 'badge-high'
      case 'MEDIUM': return 'badge-medium'
      case 'LOW': return 'badge-low'
      default: return 'badge-low'
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'badge-critical'
      case 'HIGH': return 'badge-high'
      case 'MEDIUM': return 'badge-medium'
      case 'LOW': return 'badge-low'
      default: return 'badge-low'
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '400px' }}>
        <div className="status-dot running" style={{ width: 24, height: 24 }} />
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Incident command center overview</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span className="status-indicator">
            <span className="status-dot running" />
            <span>LIVE</span>
          </span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-4" style={{ marginBottom: 24 }}>
        <div className="stat-card">
          <div className="stat-label">Active Incidents</div>
          <div className="stat-value" style={{ color: 'var(--accent-danger)' }}>{stats.active}</div>
          <div className="stat-trend up">
            <TrendingUp style={{ width: 14, height: 14 }} />
            <span>{stats.critical} critical</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Critical</div>
          <div className="stat-value" style={{ color: 'var(--accent-danger)' }}>{stats.critical}</div>
          <div className="stat-trend">
            <AlertTriangle style={{ width: 14, height: 14 }} />
            <span>Requires immediate attention</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Investigating</div>
          <div className="stat-value" style={{ color: 'var(--accent-info)' }}>{stats.investigating}</div>
          <div className="stat-trend">
            <Activity style={{ width: 14, height: 14 }} />
            <span>Autonomous analysis in progress</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Resolved Today</div>
          <div className="stat-value" style={{ color: 'var(--accent-primary)' }}>{stats.resolvedToday}</div>
          <div className="stat-trend down">
            <CheckCircle style={{ width: 14, height: 14 }} />
            <span>Verified recoveries</span>
          </div>
        </div>
      </div>

      {/* Active Incidents Table */}
      <div className="card">
        <div className="section-title">Active Incidents</div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Service</th>
                <th>Severity</th>
                <th>Status</th>
                <th>Description</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {incidents.filter(i => i.status !== 'RESOLVED').map(incident => (
                <tr key={incident.id}>
                  <td><code className="mono">{incident.id}</code></td>
                  <td><span className="mono">{incident.service}</span></td>
                  <td><span className={`badge ${getSeverityColor(incident.severity)}`}>{incident.severity}</span></td>
                  <td><span className={`badge ${getStatusColor(incident.status)}`}>{incident.status.replace('_', ' ')}</span></td>
                  <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {incident.description}
                  </td>
                  <td className="mono" style={{ color: 'var(--fg-muted)' }}>
                    {formatDistanceToNow(new Date(incident.created_at), { addSuffix: true })}
                  </td>
                  <td>
                    <a href={`/incidents/${incident.id}`} className="btn btn-ghost" style={{ padding: '6px 12px', fontSize: 12 }}>
                      Investigate
                    </a>
                  </td>
                </tr>
              ))}
              {incidents.filter(i => i.status !== 'RESOLVED').length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', padding: 48, color: 'var(--fg-muted)' }}>
                    No active incidents. All systems operational.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Resolved */}
      <div className="card">
        <div className="section-title">Recently Resolved</div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Service</th>
                <th>Root Cause</th>
                <th>Verdict</th>
                <th>Resolved</th>
              </tr>
            </thead>
            <tbody>
              {incidents.filter(i => i.status === 'RESOLVED').slice(0, 5).map(incident => (
                <tr key={incident.id}>
                  <td><code className="mono">{incident.id}</code></td>
                  <td><span className="mono">{incident.service}</span></td>
                  <td>Root cause analysis completed</td>
                  <td><span className="badge badge-verified">VERIFIED</span></td>
                  <td className="mono" style={{ color: 'var(--fg-muted)' }}>
                    {formatDistanceToNow(new Date(incident.updated_at), { addSuffix: true })}
                  </td>
                </tr>
              ))}
              {incidents.filter(i => i.status === 'RESOLVED').length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: 32, color: 'var(--fg-muted)' }}>
                    No resolved incidents yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}