import { AlertTriangle, CheckCircle2, ArrowRight } from 'lucide-react'
import { NavLink } from 'react-router-dom'

export function WhyCoska() {
  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', paddingBottom: 60 }}>
      <div className="page-header" style={{ marginBottom: 24 }}>
        <div>
          <h1 className="page-title">WHY COSKA?</h1>
          <p className="page-subtitle">
            Autonomous Incident Intelligence & Verified Recovery vs Traditional Hope-Driven Operations
          </p>
        </div>
        <NavLink to="/judge" className="btn btn-primary" style={{ padding: '8px 18px', fontWeight: 600 }}>
          RUN JUDGE DEMO
        </NavLink>
      </div>

      {/* Visual Contrast */}
      <div className="grid grid-2" style={{ gap: 24, marginBottom: 32 }}>
        {/* Legacy Manual Flow */}
        <div className="card" style={{ padding: 24, background: 'rgba(255, 77, 79, 0.05)', borderColor: 'rgba(255, 77, 79, 0.3)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--accent-danger)', fontWeight: 700, fontSize: 16, marginBottom: 16 }}>
            <AlertTriangle style={{ width: 20, height: 20 }} />
            <span>Traditional Manual Incident Response</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--accent-danger)', fontWeight: 700 }}>1. LOGS & ALERTS</div>
              <div style={{ fontSize: 13, color: 'var(--fg-secondary)', marginTop: 2 }}>
                PagerDuty wakes on-call engineer at 3:00 AM with vague alert signals.
              </div>
            </div>
            <div style={{ textAlign: 'center', color: 'var(--fg-muted)' }}>↓</div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--accent-danger)', fontWeight: 700 }}>2. HUMAN TRIAGE</div>
              <div style={{ fontSize: 13, color: 'var(--fg-secondary)', marginTop: 2 }}>
                Engineer manually sifts through thousands of lines of noisy logs across multiple services.
              </div>
            </div>
            <div style={{ textAlign: 'center', color: 'var(--fg-muted)' }}>↓</div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--accent-danger)', fontWeight: 700 }}>3. SEARCH DOCUMENTATION</div>
              <div style={{ fontSize: 13, color: 'var(--fg-secondary)', marginTop: 2 }}>
                Frantically searches stale wiki runbooks, outdated Notion docs, and Slack history.
              </div>
            </div>
            <div style={{ textAlign: 'center', color: 'var(--fg-muted)' }}>↓</div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--accent-danger)', fontWeight: 700 }}>4. COMPARE HYPOTHESES</div>
              <div style={{ fontSize: 13, color: 'var(--fg-secondary)', marginTop: 2 }}>
                Guesses between network outage, database saturation, or recent release regression.
              </div>
            </div>
            <div style={{ textAlign: 'center', color: 'var(--fg-muted)' }}>↓</div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--accent-danger)', fontWeight: 700 }}>5. TEST FIX</div>
              <div style={{ fontSize: 13, color: 'var(--fg-secondary)', marginTop: 2 }}>
                Applies untested hotfix directly in production under high cognitive stress.
              </div>
            </div>
            <div style={{ textAlign: 'center', color: 'var(--fg-muted)' }}>↓</div>
            <div style={{ background: 'rgba(255, 77, 79, 0.12)', padding: 12, borderRadius: 6, border: '1px solid rgba(255, 77, 79, 0.4)' }}>
              <div style={{ fontSize: 12, color: 'var(--accent-danger)', fontWeight: 800 }}>6. HOPE IT WORKED</div>
              <div style={{ fontSize: 13, color: 'var(--fg-primary)', marginTop: 2 }}>
                Stares at Grafana dashboard for 30 minutes hoping the spike doesn't recur. Zero proof of causal resolution.
              </div>
            </div>
          </div>
        </div>

        {/* COSKA Autonomous Flow */}
        <div className="card" style={{ padding: 24, background: 'rgba(0, 212, 170, 0.05)', borderColor: 'rgba(0, 212, 170, 0.4)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--accent-primary)', fontWeight: 700, fontSize: 16, marginBottom: 16 }}>
            <CheckCircle2 style={{ width: 20, height: 20 }} />
            <span>COSKA Autonomous Response</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--accent-primary)', fontWeight: 700 }}>1. OBSERVE</div>
              <div style={{ fontSize: 13, color: 'var(--fg-primary)', marginTop: 2 }}>
                Ingests logs, configuration, and runtime metrics instantaneously upon anomaly detection.
              </div>
            </div>
            <div style={{ textAlign: 'center', color: 'var(--accent-primary)' }}>↓</div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--accent-primary)', fontWeight: 700 }}>2. RETRIEVE</div>
              <div style={{ fontSize: 13, color: 'var(--fg-primary)', marginTop: 2 }}>
                RAG engine retrieves relevant runbooks, postmortems, and live external documentation in milliseconds.
              </div>
            </div>
            <div style={{ textAlign: 'center', color: 'var(--accent-primary)' }}>↓</div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--accent-primary)', fontWeight: 700 }}>3. REASON</div>
              <div style={{ fontSize: 13, color: 'var(--fg-primary)', marginTop: 2 }}>
                Multi-agent reasoning weighs competing hypotheses and pinpoints root cause with 90%+ confidence.
              </div>
            </div>
            <div style={{ textAlign: 'center', color: 'var(--accent-primary)' }}>↓</div>
            <div style={{ background: 'var(--bg-tertiary)', padding: 12, borderRadius: 6 }}>
              <div style={{ fontSize: 11, color: 'var(--accent-primary)', fontWeight: 700 }}>4. ACT</div>
              <div style={{ fontSize: 13, color: 'var(--fg-primary)', marginTop: 2 }}>
                Simulates exact, bounded configuration or code remediation in an isolated safe sandbox.
              </div>
            </div>
            <div style={{ textAlign: 'center', color: 'var(--accent-primary)' }}>↓</div>
            <div style={{ background: 'rgba(0, 212, 170, 0.15)', padding: 12, borderRadius: 6, border: '1px solid var(--accent-primary)' }}>
              <div style={{ fontSize: 12, color: 'var(--accent-primary)', fontWeight: 800 }}>5. VERIFY (CAUSAL PROOF)</div>
              <div style={{ fontSize: 13, color: 'var(--fg-primary)', marginTop: 2 }}>
                Executes 4-stage causal verifier: Baseline (FAIL), Post-Fix (PASS), Health (PASS), Control (FAIL). Proves causality mathematically.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* The Core Truth Banner */}
      <div className="card" style={{ padding: 24, textAlign: 'center', background: 'var(--bg-card)', border: '1px solid var(--border-secondary)' }}>
        <h3 style={{ fontSize: 18, color: 'var(--fg-primary)', marginBottom: 8 }}>
          "This is not an LLM claim. This is the deterministic verifier result."
        </h3>
        <p style={{ color: 'var(--fg-secondary)', fontSize: 13, maxWidth: 700, margin: '0 auto 16px auto' }}>
          COSKA does not ask the LLM "did you fix it?". It runs a strict, independent control test that reverts the fix to verify that the failure returns. Only then is the recovery declared VERIFIED.
        </p>
        <NavLink to="/judge" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <span>Experience the 90-Second Canonical Demo</span>
          <ArrowRight style={{ width: 16, height: 16 }} />
        </NavLink>
      </div>
    </div>
  )
}
