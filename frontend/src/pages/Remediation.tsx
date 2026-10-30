import { useParams, Link } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getIncidentRemediation, applyFix } from '../services/api'
import { type Remediation, RemediationType } from '../types/incident'
import { Shield, RotateCcw, ArrowRight, CheckCircle2, FileCode } from 'lucide-react'

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
  const [applied, setApplied] = useState(false)

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
      setApplied(true)
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

  const typeConfig = TYPE_CONFIG[remediation.type] || { color: 'var(--accent-info)', icon: Shield, label: remediation.type }
  const riskColor = RISK_COLORS[remediation.risk as keyof typeof RISK_COLORS] || 'var(--accent-primary)'

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 className="page-title" style={{ margin: 0 }}>Remediation Lab</h2>
            <span className="sim-badge">ISOLATED SANDBOX</span>
          </div>
          <p className="page-subtitle">Deterministic code/configuration patch with automated rollback safety</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="badge" style={{ background: `${typeConfig.color}20`, color: typeConfig.color }}>
            {typeConfig.label}
          </span>
          <span className="badge" style={{ background: `${riskColor}20`, color: riskColor, fontWeight: 700 }}>
            Risk: {remediation.risk}
          </span>
          <span className="badge" style={{ background: 'rgba(0,255,136,0.15)', color: 'var(--accent-primary)' }}>
            Rollback: AVAILABLE
          </span>
        </div>
      </div>

      {/* Code / Configuration Diff Viewer */}
      <div style={{ marginBottom: 24 }}>
        <div className="diff-viewer">
          <div className="diff-header">
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FileCode style={{ width: 14, height: 14, color: 'var(--accent-primary)' }} />
              <span>Target Patch: {remediation.exact_change.split(':')[0] || 'configuration.env'}</span>
            </span>
            <span style={{ color: 'var(--accent-warning)', fontSize: 11, fontWeight: 700, letterSpacing: '0.05em' }}>
              PROPOSED CHANGE • DETERMINISTIC
            </span>
          </div>
          <div className="diff-body">
            <div className="diff-line normal">
              <span className="diff-marker"> </span># Target component configuration
            </div>
            <div className="diff-line normal">
              <span className="diff-marker"> </span># Proposed by COSKA Autonomous Causal Engine
            </div>
            <div className="diff-line removed">
              <span className="diff-marker">-</span>{remediation.exact_change.includes('(was ') 
                ? remediation.exact_change.split('(was ')[1].replace(')', '')
                : 'ORIGINAL_CONFIGURATION (Incident State)'}
            </div>
            <div className="diff-line added">
              <span className="diff-marker">+</span>{remediation.exact_change.includes('(was ') 
                ? remediation.exact_change.split('(was ')[0].trim()
                : remediation.exact_change}
            </div>
            <div className="diff-line normal">
              <span className="diff-marker"> </span># Rollback command: {remediation.rollback_plan.slice(0, 60)}...
            </div>
          </div>
        </div>
      </div>

      {/* Main Fix Description Card */}
      <div className="card" style={{ marginBottom: 24, borderColor: typeConfig.color }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <typeConfig.icon style={{ width: 20, height: 20, color: typeConfig.color }} />
          <div className="section-title" style={{ margin: 0 }}>Recommended Action</div>
        </div>

        <div style={{ color: 'var(--fg-primary)', fontSize: 15, lineHeight: 1.6, marginBottom: 16 }}>
          <strong>Description:</strong> {remediation.description}
        </div>

        <div style={{ 
          background: 'var(--bg-tertiary)', 
          borderRadius: 'var(--radius-sm)', 
          padding: 16,
          border: '1px solid var(--border-primary)',
          color: 'var(--accent-primary)',
          fontSize: 14,
          fontWeight: 600
        }}>
          <strong>Expected Effect:</strong> {remediation.expected_effect}
        </div>
      </div>

      {/* Risk & Safety Metrics */}
      <div className="grid grid-3" style={{ marginBottom: 24 }}>
        <div className="card">
          <div className="section-title">Risk Assessment</div>
          <div style={{ 
            fontSize: 28, 
            fontWeight: 800, 
            fontFamily: 'var(--font-mono)', 
            color: riskColor 
          }}>
            {remediation.risk}
          </div>
          <div style={{ fontSize: 12, color: 'var(--fg-muted)', marginTop: 4 }}>
            Pre-tested against sandboxed baseline
          </div>
        </div>
        <div className="card">
          <div className="section-title">Blast Radius</div>
          <div style={{ fontSize: 15, fontFamily: 'var(--font-mono)', color: 'var(--accent-warning)', fontWeight: 700 }}>
            {remediation.blast_radius}
          </div>
          <div style={{ fontSize: 12, color: 'var(--fg-muted)', marginTop: 4 }}>
            Scoped to affected component only
          </div>
        </div>
        <div className="card">
          <div className="section-title">Rollback Guarantee</div>
          <div style={{ fontSize: 15, fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)', fontWeight: 700 }}>
            Deterministic
          </div>
          <div style={{ fontSize: 12, color: 'var(--fg-muted)', marginTop: 4 }}>
            Zero-downtime revert command staged
          </div>
        </div>
      </div>

      {/* Rollback Procedure */}
      <div className="card" style={{ marginBottom: 24, borderColor: 'var(--accent-info)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <RotateCcw style={{ width: 18, height: 18, color: 'var(--accent-info)' }} />
          <div className="section-title" style={{ margin: 0 }}>Automated Rollback Procedure</div>
        </div>
        <div style={{ 
          background: 'var(--bg-tertiary)', 
          borderRadius: 'var(--radius-sm)', 
          padding: 16,
          border: '1px solid var(--border-primary)',
          fontFamily: 'var(--font-mono)',
          fontSize: 13,
          color: 'var(--fg-secondary)',
          whiteSpace: 'pre-wrap'
        }}>
          {remediation.rollback_plan}
        </div>
      </div>

      {/* Actions */}
      <div className="card">
        <div className="section-title">Execution Controls</div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <button 
            onClick={handleApplyFix}
            disabled={applying}
            className="btn btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 20px', fontSize: 14 }}
          >
            {applying ? (
              <>
                <RotateCcw className="spin" style={{ width: 16, height: 16 }} />
                Applying in Sandbox...
              </>
            ) : applied ? (
              <>
                <CheckCircle2 style={{ width: 16, height: 16 }} />
                Applied to Sandbox
              </>
            ) : (
              <>
                <Shield style={{ width: 16, height: 16 }} />
                Apply Fix in Isolated Sandbox
              </>
            )}
          </button>
          
          <Link 
            to={`/incidents/${id}/verification`}
            className="btn btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none', padding: '10px 18px', fontSize: 14 }}
          >
            <span>Proceed to Causal Verification</span>
            <ArrowRight style={{ width: 16, height: 16 }} />
          </Link>
        </div>
        
        {applying && (
          <div style={{ marginTop: 16, padding: 16, background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-primary)' }}>
            <div className="status-indicator" style={{ marginBottom: 8 }}>
              <span className="status-dot running" />
              <span style={{ fontWeight: 600 }}>Executing remediation in isolated sandbox...</span>
            </div>
            <div style={{ fontSize: 13, color: 'var(--fg-secondary)' }}>
              Applying configuration patch and preparing the four-stage verification protocol (Baseline, Post-Fix, Health, Control).
            </div>
          </div>
        )}

        {applied && !applying && (
          <div style={{ marginTop: 16, padding: 16, background: 'rgba(0,255,136,0.08)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(0,255,136,0.3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--accent-primary)', fontWeight: 600 }}>
              <CheckCircle2 style={{ width: 18, height: 18 }} />
              <span>Remediation successfully applied in sandbox environment.</span>
            </div>
            <div style={{ fontSize: 13, color: 'var(--fg-secondary)', marginTop: 4 }}>
              The sandbox is now primed for four-stage deterministic causal verification.
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
