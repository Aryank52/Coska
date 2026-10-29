import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getIncidentEvidence } from '../services/api'
import { Evidence, SourceType } from '../types/incident'
import { FileText, Database, Server, Globe, TestTube, Code, Rocket } from 'lucide-react'

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
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h2 className="page-title">Evidence</h2>
          <p className="page-subtitle">{evidence.length} evidence items collected</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <span className="badge badge-low">{evidence.length} total</span>
        </div>
      </div>

      {evidence.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 48 }}>
          <FileText style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
          <h3>No evidence collected yet</h3>
          <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
            Start an investigation to begin collecting evidence from logs, configuration, deployment, and external sources.
          </p>
        </div>
      ) : (
        <>
          {/* Source Type Summary */}
          <div className="grid grid-4" style={{ marginBottom: 24 }}>
            {(Object.keys(SOURCE_ICONS) as SourceType[]).map(type => {
              const items = grouped[type] || []
              const Icon = SOURCE_ICONS[type]
              return (
                <div key={type} className="card" style={{ textAlign: 'center' }}>
                  <Icon style={{ width: 24, height: 24, color: SOURCE_COLORS[type], marginBottom: 8 }} />
                  <div style={{ fontSize: 18, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{items.length}</div>
                  <div style={{ fontSize: 11, textTransform: 'uppercase', color: 'var(--fg-muted)', letterSpacing: '0.5px' }}>
                    {type}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Evidence Details */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {(Object.keys(SOURCE_ICONS) as SourceType[]).map(type => {
              const items = grouped[type] || []
              if (items.length === 0) return null
              
              const Icon = SOURCE_ICONS[type]
              return (
                <div key={type} className="card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                    <Icon style={{ width: 18, height: 18, color: SOURCE_COLORS[type] }} />
                    <h3 style={{ fontSize: 14, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{type}</h3>
                    <span className="badge badge-low">{items.length} items</span>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {items.map(e => (
                      <div key={e.id} className="evidence-card">
                        <div className="evidence-header">
                          <div className="evidence-source">
                            <span className="evidence-source-icon" style={{ background: `${SOURCE_COLORS[type]}20`, color: SOURCE_COLORS[type] }}>
                              {type.charAt(0)}
                            </span>
                            <span className="mono" style={{ fontSize: 11 }}>{e.id}</span>
                          </div>
                          <div style={{ display: 'flex', gap: 12, fontSize: 11, color: 'var(--fg-muted)', fontFamily: 'var(--font-mono)' }}>
                            <span>Confidence: {(e.confidence * 100).toFixed(0)}%</span>
                            {e.related_component && <span>Component: {e.related_component}</span>}
                          </div>
                        </div>
                        <div className="evidence-claim">{e.claim}</div>
                        <div className="evidence-meta">
                          <span>Reference: {e.reference}</span>
                          <span>{new Date(e.timestamp).toLocaleString()}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}