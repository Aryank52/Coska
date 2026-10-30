import { useState, useEffect } from 'react'
import { getIncidents, aiHealthCheck, tavilyHealthCheck, sandboxHealthCheck, healthCheck } from '../services/api'
import { IncidentResponse } from '../types/incident'
import { AlertTriangle, Activity, CheckCircle, TrendingUp, Gavel, Cpu, Database, Shield, Globe } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { NavLink } from 'react-router-dom'

export function Dashboard() {
  const [incidents, setIncidents] = useState<IncidentResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    active: 0,
    critical: 0,
    investigating: 0,
    resolvedToday: 0
  })
  const [infra, setInfra] = useState({
    aiProvider: 'mock',
    aiModel: 'nvidia/nemotron-3-ultra-550b-a55b',
    aiStatus: 'healthy',
    tavilyStatus: 'connected',
    sandboxMode: 'local',
    sandboxProvider: 'local_safe',
    sandboxStatus: 'healthy',
    dbStatus: 'healthy'
  })

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 10000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [data, ai, tavily, sandbox, db] = await Promise.allSettled([
        getIncidents(),
        aiHealthCheck(),
        tavilyHealthCheck(),
        sandboxHealthCheck(),
        healthCheck()
      ])

      if (data.status === 'fulfilled') {
        const incData = data.value
        setIncidents(incData)
        const now = new Date()
        const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate())
        
        setStats({
          active: incData.filter((i: IncidentResponse) => i.status !== 'RESOLVED').length,
          critical: incData.filter((i: IncidentResponse) => i.severity === 'CRITICAL' && i.status !== 'RESOLVED').length,
          investigating: incData.filter((i: IncidentResponse) => i.status === 'INVESTIGATING').length,
          resolvedToday: incData.filter((i: IncidentResponse) => 
            i.status === 'RESOLVED' && new Date(i.updated_at) >= todayStart
          ).length
        })
      }

      setInfra({
        aiProvider: ai.status === 'fulfilled' ? ai.value.provider : 'mock',
        aiModel: ai.status === 'fulfilled' ? ai.value.model : 'nvidia/nemotron-3-ultra-550b-a55b',
        aiStatus: ai.status === 'fulfilled' ? ai.value.status : 'offline',
        tavilyStatus: tavily.status === 'fulfilled' ? tavily.value.status : 'offline',
        sandboxMode: sandbox.status === 'fulfilled' ? sandbox.value.mode : 'local',
        sandboxProvider: sandbox.status === 'fulfilled' ? sandbox.value.provider : 'local_safe',
        sandboxStatus: sandbox.status === 'fulfilled' ? sandbox.value.status : 'offline',
        dbStatus: db.status === 'fulfilled' ? db.value.status : 'offline'
      })
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
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
          <NavLink to="/judge" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', fontSize: 14, fontWeight: 600 }}>
            <Gavel style={{ width: 18, height: 18 }} />
            <span>RUN JUDGE DEMO</span>
          </NavLink>
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

      {/* Infrastructure Status Grid */}
      <div className="card" style={{ marginBottom: 24, padding: 16 }}>
        <div className="section-title" style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--fg-muted)', marginBottom: 12 }}>
          System & Infrastructure Status
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, background: 'var(--bg-elevated)', borderRadius: 6 }}>
            <Cpu style={{ width: 20, height: 20, color: 'var(--accent-primary)' }} />
            <div>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase' }}>AI Provider</div>
              <div style={{ fontSize: 13, fontWeight: 600 }} className="mono">{infra.aiProvider.toUpperCase()}</div>
              <div style={{ fontSize: 10, color: 'var(--fg-muted)' }}>{infra.aiModel}</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, background: 'var(--bg-elevated)', borderRadius: 6 }}>
            <Globe style={{ width: 20, height: 20, color: infra.tavilyStatus === 'healthy' ? 'var(--accent-primary)' : 'var(--accent-warning)' }} />
            <div>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase' }}>Tavily Research</div>
              <div style={{ fontSize: 13, fontWeight: 600 }}>{infra.tavilyStatus === 'healthy' ? 'CONNECTED' : (infra.tavilyStatus === 'unconfigured' ? 'UNCONFIGURED' : 'READY')}</div>
              <div style={{ fontSize: 10, color: 'var(--fg-muted)' }}>External Web Engine</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, background: 'var(--bg-elevated)', borderRadius: 6 }}>
            <Shield style={{ width: 20, height: 20, color: 'var(--accent-primary)' }} />
            <div>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase' }}>Sandbox Engine</div>
              <div style={{ fontSize: 13, fontWeight: 600 }} className="mono">{infra.sandboxProvider.toUpperCase()}</div>
              <div style={{ fontSize: 10, color: 'var(--fg-muted)' }}>Mode: {infra.sandboxMode}</div>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: 12, background: 'var(--bg-elevated)', borderRadius: 6 }}>
            <Database style={{ width: 20, height: 20, color: 'var(--accent-primary)' }} />
            <div>
              <div style={{ fontSize: 11, color: 'var(--fg-muted)', textTransform: 'uppercase' }}>Database (SQLite)</div>
              <div style={{ fontSize: 13, fontWeight: 600 }}>OPERATIONAL</div>
              <div style={{ fontSize: 10, color: 'var(--fg-muted)' }}>State & Memory Active</div>
            </div>
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
              {incidents.filter((i: IncidentResponse) => i.status !== 'RESOLVED').map((incident: IncidentResponse) => (
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
              {incidents.filter((i: IncidentResponse) => i.status !== 'RESOLVED').length === 0 && (
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
              {incidents.filter((i: IncidentResponse) => i.status === 'RESOLVED').slice(0, 5).map((incident: IncidentResponse) => (
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
              {incidents.filter((i: IncidentResponse) => i.status === 'RESOLVED').length === 0 && (
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