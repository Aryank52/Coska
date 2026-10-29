import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { getVerificationReport } from '../services/api'
import { type VerificationReport } from '../types/incident'
import { CheckCircle, XCircle, AlertTriangle, Shield, CheckCircle2, Target } from 'lucide-react'

const STAGE_CONFIG = {
  baseline: { label: 'BASELINE', icon: AlertTriangle, passedColor: 'var(--accent-danger)', passedLabel: 'FAILED', failedColor: 'var(--accent-primary)', failedLabel: 'PASSED' },
  post_fix: { label: 'POST-FIX TESTS', icon: CheckCircle, passedColor: 'var(--accent-primary)', passedLabel: 'PASSED', failedColor: 'var(--accent-danger)', failedLabel: 'FAILED' },
  health: { label: 'HEALTH CHECK', icon: Shield, passedColor: 'var(--accent-primary)', passedLabel: 'PASSED', failedColor: 'var(--accent-danger)', failedLabel: 'FAILED' },
  control: { label: 'CONTROL TEST', icon: Target, passedColor: 'var(--accent-danger)', passedLabel: 'FAILED (Expected)', failedColor: 'var(--accent-primary)', failedLabel: 'PASSED (Unexpected)' },
}

const VERDICT_CONFIG = {
  VERIFIED: { color: 'var(--accent-primary)', icon: CheckCircle2, label: 'VERIFIED', tagline: 'COSKA proved the recovery.' },
  FAILED: { color: 'var(--accent-danger)', icon: XCircle, label: 'FAILED', tagline: 'Remediation did not resolve the incident.' },
  UNVERIFIED: { color: 'var(--accent-warning)', icon: AlertTriangle, label: 'UNVERIFIED', tagline: 'Insufficient evidence to confirm causal relationship.' },
  INSUFFICIENT_EVIDENCE: { color: 'var(--fg-muted)', icon: AlertTriangle, label: 'INSUFFICIENT EVIDENCE', tagline: 'More evidence needed to verify.' },
}

export function Verification() {
  const { id } = useParams<{ id: string }>()
  const [report, setReport] = useState<VerificationReport | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!id) return
    loadReport()
  }, [id])

  const loadReport = async () => {
    try {
      const data = await getVerificationReport(id!)
      setReport(data)
    } catch (error) {
      console.error('Failed to load verification report:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="card" style={{ padding: 48, textAlign: 'center' }}>Loading verification report...</div>

  if (!report) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: 48 }}>
        <Target style={{ width: 48, height: 48, color: 'var(--fg-muted)', marginBottom: 16 }} />
        <h3>Verification not yet run</h3>
        <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
          Apply a remediation in the sandbox to run the three-stage verification.
        </p>
      </div>
    )
  }

  const verdictConfig = VERDICT_CONFIG[report.verdict]

  // Generate receipt object
  const receipt = {
    incident_id: id || '',
    service: '', // Would need incident data
    root_cause: '', // Would need root cause data
    remediation: '', // Would need remediation data
    baseline_test: report.baseline_test ? 'PASSED' : 'FAILED',
    post_fix_tests: report.post_fix_tests ? 'PASSED' : 'FAILED',
    health_check: report.health_check ? 'PASSED' : 'FAILED',
    control_test: !report.control_test ? 'FAILED_WITHOUT_FIX' : 'PASSED_WITH_FIX',
    verdict: report.verdict,
    evidence_count: report.evidence_count,
    model: report.model,
    timestamp: new Date().toISOString()
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h2 className="page-title">Verification</h2>
          <p className="page-subtitle">Three-stage causal verification</p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span className="badge" style={{ 
            background: `${verdictConfig.color}20`, 
            color: verdictConfig.color,
            fontSize: 14,
            padding: '8px 16px'
          }}>
            {verdictConfig.label}
          </span>
        </div>
      </div>

      {/* Three Stages */}
      <div className="verification-grid" style={{ marginBottom: 24 }}>
        {[
          { key: 'baseline', passed: !report.baseline_test, data: report.baseline_test },
          { key: 'post_fix', passed: report.post_fix_tests, data: report.post_fix_tests },
          { key: 'health', passed: report.health_check, data: report.health_check },
          { key: 'control', passed: !report.control_test, data: report.control_test },
        ].map(stage => {
          const config = STAGE_CONFIG[stage.key as keyof typeof STAGE_CONFIG]
          const Icon = config.icon
          const passed = stage.passed
          
          return (
            <div key={stage.key} className={`verification-stage ${passed ? 'passed' : 'failed'}`}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginBottom: 16 }}>
                <Icon style={{ 
                  width: 24, 
                  height: 24, 
                  color: passed ? config.passedColor : config.failedColor 
                }} />
                <span className="verification-stage-label">{config.label}</span>
              </div>
              <div className={`verification-stage-result ${passed ? 'passed' : 'failed'}`}>
                {passed ? config.passedLabel : config.failedLabel}
              </div>
              <div className="verification-stage-desc">
                {stage.key === 'baseline' && 'Incident reproduced before fix'}
                {stage.key === 'post_fix' && 'Tests pass after remediation'}
                {stage.key === 'health' && 'Service health validated'}
                {stage.key === 'control' && 'Failure returns without fix'}
              </div>
              <div style={{ 
                marginTop: 16, 
                padding: 12, 
                background: 'var(--bg-tertiary)', 
                borderRadius: 'var(--radius-sm)',
                fontSize: 11,
                fontFamily: 'var(--font-mono)',
                color: 'var(--fg-muted)',
                textAlign: 'left'
              }}>
                Exit code: {stage.data?.exit_code ?? 'N/A'}
              </div>
            </div>
          )
        })}
      </div>

      {/* Final Verdict */}
      <div className={`verification-verdict ${report.verdict.toLowerCase()}`}>
        <div className="verdict-label">FINAL VERDICT</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 16, marginBottom: 8 }}>
          <verdictConfig.icon style={{ 
            width: 48, 
            height: 48, 
            color: verdictConfig.color 
          }} />
          <div className={`verdict-value ${report.verdict.toLowerCase()}`}>
            {verdictConfig.label}
          </div>
        </div>
        <div className="verdict-tagline">{verdictConfig.tagline}</div>
      </div>

      {/* Details */}
      <div style={{ marginTop: 24 }}>
        <div className="section-title">Verification Details</div>
        <div className="grid grid-2" style={{ marginTop: 16 }}>
          <div className="card">
            <div className="section-title">Summary</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, fontSize: 13 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--fg-muted)' }}>Evidence Count</span>
                <span className="mono" style={{ fontWeight: 600 }}>{report.evidence_count}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--fg-muted)' }}>Model</span>
                <span className="mono" style={{ fontWeight: 600 }}>{report.model}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--fg-muted)' }}>Baseline Test</span>
                <span className="mono" style={{ fontWeight: 600, color: report.baseline_test ? 'var(--accent-primary)' : 'var(--accent-danger)' }}>
                  {report.baseline_test ? 'PASSED' : 'FAILED'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--fg-muted)' }}>Post-Fix Tests</span>
                <span className="mono" style={{ fontWeight: 600, color: report.post_fix_tests ? 'var(--accent-primary)' : 'var(--accent-danger)' }}>
                  {report.post_fix_tests ? 'PASSED' : 'FAILED'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--fg-muted)' }}>Health Check</span>
                <span className="mono" style={{ fontWeight: 600, color: report.health_check ? 'var(--accent-primary)' : 'var(--accent-danger)' }}>
                  {report.health_check ? 'PASSED' : 'FAILED'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: 'var(--fg-muted)' }}>Control Test</span>
                <span className="mono" style={{ fontWeight: 600, color: !report.control_test ? 'var(--accent-primary)' : 'var(--accent-danger)' }}>
                  {!report.control_test ? 'FAILED (Expected)' : 'PASSED (Unexpected)'}
                </span>
              </div>
            </div>
          </div>
          
          <div className="card">
            <div className="section-title">Raw Details</div>
            <pre style={{ 
              fontSize: 11, 
              fontFamily: 'var(--font-mono)', 
              color: 'var(--fg-secondary)',
              overflow: 'auto',
              maxHeight: 300,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word'
            }}>
              {JSON.stringify(report.details, null, 2)}
            </pre>
          </div>
        </div>
      </div>

      {/* Verification Receipt JSON */}
      <div className="card" style={{ marginTop: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <div className="section-title" style={{ margin: 0 }}>Verification Receipt (JSON)</div>
          <button className="btn btn-ghost" onClick={() => navigator.clipboard.writeText(JSON.stringify(receipt, null, 2))}>
            Copy JSON
          </button>
        </div>
        <pre style={{ 
          fontSize: 11, 
          fontFamily: 'var(--font-mono)', 
          color: 'var(--fg-secondary)',
          overflow: 'auto',
          maxHeight: 400,
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          background: 'var(--bg-tertiary)',
          padding: 16,
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--border-primary)'
        }}>
          {JSON.stringify(receipt, null, 2)}
        </pre>
      </div>
    </div>
  )
}