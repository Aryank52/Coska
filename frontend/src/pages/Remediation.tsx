import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getIncidentRemediation, applyFix } from '../services/api'
import { Remediation, RemediationType } from '../types/incident'
import { Shield, AlertTriangle, RotateCcw, CheckCircle, XCircle, Info } from 'lucide-react'

const TYPE_CONFIG: Record<RemediationType, { color: string; icon: any; label: string }> = {
  CONFIGURATION_CHANGE: { color: 'var(--accent-warning)', icon: Shield, label: 'Config Change' },
  CODE_CHANGE: { color: 'var(--accent-info)', icon: Shield, label: 'Code Change' },
  DEPENDENCY_CHANGE: { color: '#aa78ff', icon: Shield, label: 'Dependency' },
  SAFE_ROLLBACK: { color: 'var(--accent-primary)', icon: RotateCcw, label: 'Rollback' },
  FEATURE_FLAG_CHANGE: { color: 'var(--accent-secondary)', icon: Shield, label: 'Feature Flag' },
}

const RISK_COLORS = {
  LOW: 'var(--accent-primary)',
  MEDIUM: 'var(--accent-warning)',
  HIGH: 'var(--accent-danger)',
}

export function Remediation() {
  const { id } = useParams<{ id: string }>()
  const [remediation, setRemediation] = useState<Remediation | null>(null)
  const [loading, setLoading] = useState(true)
  const [applying, setApplying] = useState(false)

  useEffect(() => {
    if (!id) return
    loadRemediation()
  }, [id])

  const loadRemediation = async () => {
    try {
      const data = await getIncidentRemediation(id!)
      setRemediation(data.remediation || null)
    } catch (error) {
      console.error('Failed to load remediation:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApplyFix = async () => {
    if (!remediation) return
    setApplying(true)
    try {
      await applyFix(id!)
      setLoading(true)
      await loadRemediation()
    } catch (error) {
      console.error('Failed to apply fix:', error)
    } finally {
      setApplying(false)
    }
  }

  if (loading) return <div className="card" style={{ padding: 48, textAlign: 'center' }}>Loading remediation...</div>

  if (!remediation) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 48 }}>
        <Shield style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
        <h3>No remediation proposed yet</h3>
        <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
          A remediation plan will be generated after root cause identification.
        </p>
      </div>
    )
  }

  const typeConfig = TYPE_CONFIG[remediation.type]
  const riskColor = RISK_COLORS[remediation.risk as keyof typeof RISK_COLORS] || 'var(--fg-muted)'

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h2 className="page-title">Remediation Plan</h2>
          <p className="page-subtitle">Proposed fix with risk assessment and rollback procedure</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="badge" style={{ background: `${typeConfig.color}20`, color: typeConfig.color }}>
            {typeConfig.label}
          </span>
          <span className="badge" style={{ background: `${riskColor}20`, color: riskColor }}>
            Risk: {remediation.risk}
          </span>
        </div>
      </div>

      {/* Main Fix */}
      <div className="card" style={{ marginBottom: 24, borderColor: typeConfig.color }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <typeConfig.icon style={{ width: 20, height: 20, color: typeConfig.color }} />
          <div className="section-title" style={{ margin: 0 }}>Recommended Fix</div>
        </div>
        
        <div style={{ 
          background: 'var(--bg-tertiary)', 
          borderRadius: 'var(--radius-md)', 
          padding: 20,
          border: `2px solid ${typeConfig.color}`,
          marginBottom: 16,
        }}>
          <div style={{ 
            fontFamily: 'var(--font-mono)', 
            fontSize: 20, 
            fontWeight: 700, 
            color: typeConfig.color,
            letterSpacing: '0.5px'
          }}>
            {remediation.exact_change}
          </div>
        </div>

        <div style={{ color: 'var(--fg-secondary)', lineHeight: 1.6, marginBottom: 16 }}>
          <strong>Description:</strong> {remediation.description}
        </div>

        <div style={{ color: 'var(--fg-secondary)', lineHeight: 1.6 }}>
          <strong>Expected Effect:</strong> {remediation.expected_effect}
        </div>
      </div>

      {/* Risk Assessment */}
      <div className="grid grid-3" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="section-title">Risk Level</div>
          <div style={{ 
            fontSize: 28, 
            fontWeight: 700, 
            fontFamily: 'var(--font-mono)', 
            color: riskColor 
          }}>
            {remediation.risk}
          </div>
        </div>
        <div className="card">
          <div className="section-title">Blast Radius</div>
          <div style={{ fontSize: 14, fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>
            {remediation.blast_radius}
          </div>
        </div>
        <div className="card">
          <div className="section-title">Type</div>
          <div style={{ fontSize: 14, fontFamily: 'var(--font-mono)', color: typeConfig.color }}>
            {typeConfig.label}
          </div>
        </div>
      </div>

      {/* Rollback Plan */}
      <div className="card" style={{ marginBottom: 24, borderColor: 'var(--accent-info)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
          <RotateCcw style={{ width: 20, height: 20, color: 'var(--accent-info)' }} />
          <div className="section-title" style={{ margin: 0 }}>Rollback Plan</div>
        </div>
        <div style={{ 
          background: 'var(--bg-tertiary)', 
          borderRadius: 'var(--radius-sm)', 
          padding: 16,
          border: '1px solid var(--border-primary)',
          fontFamily: 'var(--font-mono)',
          whiteSpace: 'pre-wrap'
        }}>
          {remediation.rollback_plan}
        </div>
      </div>

      {/* Actions */}
      <div className="card">
        <div className="section-title">Actions</div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <button 
            onClick={handleApplyFix}
            disabled={applying}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 8 }}
          >
            {applying ? (
              <>
                <RotateCcw className="mono" style={{ width: 16, height: 16, animation: 'spin 1s linear infinite' }} />
                Applying in Sandbox...
              </>
            ) : (
              <>
                <Shield style={{ width: 16, height: 16 }} />
                Apply to Sandbox & Verify
              </>
            )}
          </button>
          
          <button className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Info style={{ width: 16, height: 16 }} />
            Simulate (Dry Run)
          </button>
        </div>
        
        {applying && (
          <div style={{ marginTop: 16, padding: 16, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
            <div className="status-indicator" style={{ marginBottom: 8 }}>
              <span className="status-dot running" />
              <span>Applying remediation in isolated sandbox...</span>
            </div>
            <div style={{ fontSize: 13, color: 'var(--fg-secondary)' }}>
              The fix is being applied to a sandboxed environment. Tests and verification will run automatically.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}