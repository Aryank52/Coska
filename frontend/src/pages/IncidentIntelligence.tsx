import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getIncidentIntelligence } from '../services/api'
import type { IncidentIntelligence } from '../types/incident'
import { Brain, Target, AlertTriangle, Server, Database, Network, AlertCircle, Zap, FileText, Tag, Search } from 'lucide-react'

const SEVERITY_COLORS = {
  LOW: 'var(--accent-primary)',
  MEDIUM: 'var(--accent-warning)',
  HIGH: 'var(--accent-danger)',
  CRITICAL: '#ff2222',
}

const METHOD_COLORS = {
  deterministic: 'var(--accent-primary)',
  ai_enhanced: 'var(--accent-info)',
}

const METHOD_LABELS = {
  deterministic: 'DETERMINISTIC',
  ai_enhanced: 'AI ENHANCED',
}

const ICON_MAP: Record<string, any> = {
  database: Database,
  network: Network,
  memory: AlertCircle,
  deployment: Server,
  cache: Database,
  dependency: Network,
  runtime: Server,
}

export function IncidentIntelligence() {
  const { id } = useParams<{ id: string }>()
  const [intelligence, setIntelligence] = useState<IncidentIntelligence | null>(null)
  const [loading, setLoading] = useState(true)
  const [useAI, setUseAI] = useState(false)

  useEffect(() => {
    if (!id) return
    loadIntelligence()
  }, [id, useAI])

  const loadIntelligence = async () => {
    try {
      const data = await getIncidentIntelligence(id!, useAI)
      setIntelligence(data)
    } catch (error) {
      console.error('Failed to load incident intelligence:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="card" style={{ padding: 48, textAlign: 'center' }}>Analyzing incident...</div>

  if (!intelligence) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 48 }}>
        <Brain style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
        <h3>Intelligence not available</h3>
        <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
          Incident intelligence will appear here once the incident is created.
        </p>
      </div>
    )
  }

  const methodColor = (METHOD_COLORS as Record<string, string>)[intelligence.extraction_method] || 'var(--fg-muted)'
  const methodLabel = (METHOD_LABELS as Record<string, string>)[intelligence.extraction_method] || intelligence.extraction_method

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 className="page-title">Incident Intelligence</h2>
          <p className="page-subtitle">Structured understanding extracted from incident data</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={useAI}
              onChange={(e) => setUseAI(e.target.checked)}
              style={{ width: 16, height: 16, accentColor: 'var(--accent-primary)' }}
            />
            <span style={{ fontSize: 13 }}>AI Enhanced</span>
          </label>
          <span className="badge" style={{ background: `${methodColor}20`, color: methodColor }}>
            {methodLabel}
          </span>
        </div>
      </div>

      {/* Service & Severity */}
      <div className="grid grid-4" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="section-title">Service</div>
          <div style={{ fontSize: 18, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{intelligence.service}</div>
        </div>
        <div className="card">
          <div className="section-title">Severity</div>
          <div style={{ fontSize: 18, fontWeight: 600, fontFamily: 'var(--font-mono)', color: SEVERITY_COLORS[intelligence.severity] }}>
            {intelligence.severity}
          </div>
        </div>
        <div className="card">
          <div className="section-title">Environment</div>
          <div style={{ fontSize: 14, fontFamily: 'var(--font-mono)' }}>{intelligence.environment}</div>
        </div>
        <div className="card">
          <div className="section-title">Business Impact</div>
          <div style={{ fontSize: 12, color: 'var(--fg-secondary)' }}>{intelligence.business_impact}</div>
        </div>
      </div>

      {/* Symptoms */}
      {intelligence.symptoms.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <AlertTriangle style={{ width: 20, height: 20, color: 'var(--accent-warning)' }} />
            <div className="section-title" style={{ margin: 0 }}>Observed Symptoms ({intelligence.symptoms.length})</div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {intelligence.symptoms.map((symptom, i) => (
              <span key={i} className="badge badge-warning" style={{ fontSize: 12 }}>
                {symptom}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Components */}
      {intelligence.components.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Server style={{ width: 20, height: 20, color: 'var(--accent-info)' }} />
            <div className="section-title" style={{ margin: 0 }}>Affected Components ({intelligence.components.length})</div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {intelligence.components.map((comp, i) => {
              const Icon = ICON_MAP[comp.toLowerCase()] || Server
              return (
                <span key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
                  <Icon style={{ width: 14, height: 14, color: 'var(--accent-info)' }} />
                  <span style={{ fontSize: 13, fontFamily: 'var(--font-mono)' }}>{comp}</span>
                </span>
              )
            })}
          </div>
        </div>
      )}

      {/* Error Types */}
      {intelligence.error_types.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Zap style={{ width: 20, height: 20, color: 'var(--accent-danger)' }} />
            <div className="section-title" style={{ margin: 0 }}>Error Types ({intelligence.error_types.length})</div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {intelligence.error_types.map((err, i) => (
              <span key={i} className="badge badge-danger" style={{ fontSize: 12 }}>{err}</span>
            ))}
          </div>
        </div>
      )}

      {/* Configuration Values */}
      {Object.keys(intelligence.configuration_values).length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <FileText style={{ width: 20, height: 20, color: 'var(--accent-warning)' }} />
            <div className="section-title" style={{ margin: 0 }}>Configuration Values</div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
            {Object.entries(intelligence.configuration_values).map(([key, value]) => (
              <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
                <span className="mono" style={{ fontSize: 12 }}>{key}</span>
                <span className="mono" style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-primary)' }}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Probable Causes */}
      {intelligence.probable_causes.length > 0 && (
        <div className="card" style={{ marginBottom: 24, borderColor: 'var(--accent-primary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Target style={{ width: 20, height: 20, color: 'var(--accent-primary)' }} />
            <div className="section-title" style={{ margin: 0 }}>Probable Root Causes ({intelligence.probable_causes.length})</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {intelligence.probable_causes.map((cause, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, padding: '12px 16px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)', borderLeft: '3px solid var(--accent-primary)' }}>
                <span style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--accent-primary)', color: 'var(--bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 600, flexShrink: 0 }}>
                  {i + 1}
                </span>
                <span style={{ fontSize: 14, color: 'var(--fg-primary)' }}>{cause}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suspected Dependencies */}
      {intelligence.suspected_dependencies.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Network style={{ width: 20, height: 20, color: 'var(--accent-secondary)' }} />
            <div className="section-title" style={{ margin: 0 }}>Suspected Dependencies ({intelligence.suspected_dependencies.length})</div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {intelligence.suspected_dependencies.map((dep, i) => (
              <span key={i} className="badge" style={{ background: 'var(--accent-secondary)20', color: 'var(--accent-secondary)' }}>{dep}</span>
            ))}
          </div>
        </div>
      )}

      {/* Timestamps */}
      {intelligence.timestamps.length > 0 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Tag style={{ width: 20, height: 20, color: 'var(--fg-muted)' }} />
            <div className="section-title" style={{ margin: 0 }}>Key Timestamps ({intelligence.timestamps.length})</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--fg-secondary)' }}>
            {intelligence.timestamps.slice(0, 10).map((ts, i) => (
              <span key={i}>{ts}</span>
            ))}
            {intelligence.timestamps.length > 10 && (
              <span style={{ color: 'var(--fg-muted)' }}>... and {intelligence.timestamps.length - 10} more</span>
            )}
          </div>
        </div>
      )}

      {/* Keywords & Technical Entities */}
      <div className="grid grid-2" style={{ marginBottom: 24 }}>
        {intelligence.keywords.length > 0 && (
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <Tag style={{ width: 20, height: 20, color: 'var(--fg-muted)' }} />
              <div className="section-title" style={{ margin: 0 }}>Keywords ({intelligence.keywords.length})</div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {intelligence.keywords.slice(0, 20).map((kw, i) => (
                <span key={i} className="badge badge-low" style={{ fontSize: 11 }}>{kw}</span>
              ))}
            </div>
          </div>
        )}

        {intelligence.technical_entities.length > 0 && (
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <Search style={{ width: 20, height: 20, color: 'var(--accent-info)' }} />
              <div className="section-title" style={{ margin: 0 }}>Technical Entities ({intelligence.technical_entities.length})</div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {intelligence.technical_entities.map((ent, i) => (
                <span key={i} className="badge" style={{ background: 'var(--accent-info)20', color: 'var(--accent-info)', fontSize: 11 }}>{ent}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Investigation Priority */}
      {intelligence.metadata?.investigation_priority && (
        <div className="card" style={{ borderColor: 'var(--accent-info)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Search style={{ width: 20, height: 20, color: 'var(--accent-info)' }} />
            <div className="section-title" style={{ margin: 0 }}>Recommended Investigation Priority</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {intelligence.metadata.investigation_priority.map((action: string, i: number) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--accent-info)', color: 'var(--bg-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 600, flexShrink: 0 }}>
                  {i + 1}
                </span>
                <span className="mono" style={{ fontSize: 13 }}>{action}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}