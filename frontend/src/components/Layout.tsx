import { Outlet, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Gavel, Cpu, Globe, Shield, CheckCircle2, HelpCircle, Code } from 'lucide-react'
import { useState, useEffect } from 'react'
import { aiHealthCheck, tavilyHealthCheck, sandboxHealthCheck } from '../services/api'
import { VoiceControl } from './VoiceControl'

export function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const isJudgeMode = location.pathname === '/judge'

  const [infra, setInfra] = useState({
    aiProvider: 'mock',
    aiModel: 'Deterministic Mock Provider',
    tavilyStatus: 'connected',
    sandboxMode: 'local_safe',
  })

  useEffect(() => {
    Promise.allSettled([aiHealthCheck(), tavilyHealthCheck(), sandboxHealthCheck()]).then(results => {
      const [ai, tavily, sandbox] = results
      setInfra({
        aiProvider: ai.status === 'fulfilled' ? ai.value.provider : 'mock',
        aiModel: ai.status === 'fulfilled' ? ai.value.model : 'Deterministic Mock Provider',
        tavilyStatus: tavily.status === 'fulfilled' ? tavily.value.status : 'offline',
        sandboxMode: sandbox.status === 'fulfilled' ? (sandbox.value.mode || sandbox.value.provider) : 'local_safe',
      })
    })
  }, [])

  const aiLabel = infra.aiProvider === 'nebius' 
    ? 'NVIDIA Nemotron via Nebius Token Factory'
    : 'Deterministic Mock Provider'

  const tavilyLabel = infra.tavilyStatus === 'healthy' || infra.tavilyStatus === 'connected'
    ? 'Tavily Search Engine'
    : 'Offline Cached Operational Knowledge'

  const sandboxLabel = infra.sandboxMode.includes('docker')
    ? 'Docker Container Sandbox'
    : 'Local Safe Sandbox'

  const handleVoiceCommand = (command?: string) => {
    const cmd = (command || '').toLowerCase()
    let scenario = 'payment_pool_exhaustion'
    if (cmd.includes('retry')) {
      scenario = 'external_api_retry_misconfiguration'
    } else if (cmd.includes('config') || cmd.includes('bad') || cmd.includes('regression')) {
      scenario = 'bad_deployment_config_regression'
    } else if (cmd.includes('cache') || cmd.includes('stampede')) {
      scenario = 'cache_stampede'
    } else if (cmd.includes('memory') || cmd.includes('leak')) {
      scenario = 'memory_leak'
    } else if (cmd.includes('saturation')) {
      scenario = 'database_saturation'
    }
    navigate(`/judge?scenario=${scenario}&autostart=true`)
  }

  return (
    <div className="app-layout">
      <header className="header">
        <div className="header-brand">
          <NavLink to="/" style={{ display: 'flex', alignItems: 'center', gap: 12, textDecoration: 'none' }}>
            <div className="header-logo">C</div>
            <div>
              <div className="header-title" style={{ color: 'var(--fg-primary)' }}>COSKA</div>
              <div className="header-tagline">Autonomous Incident Intelligence</div>
            </div>
          </NavLink>
        </div>

        {/* Central Operational Status Pills */}
        <div className="status-pill-group" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div className="status-pill" title="AI Provider">
            <Cpu style={{ width: 13, height: 13, color: 'var(--accent-primary)' }} />
            <span>AI: <strong>{aiLabel}</strong></span>
          </div>

          <div className="status-pill" title="Research Provider">
            <Globe style={{ width: 13, height: 13, color: 'var(--accent-secondary)' }} />
            <span>Research: <strong>{tavilyLabel}</strong></span>
          </div>

          <div className="status-pill" title="Sandbox Provider">
            <Shield style={{ width: 13, height: 13, color: 'var(--accent-warning)' }} />
            <span>Sandbox: <strong>{sandboxLabel}</strong></span>
          </div>

          <div className="status-pill" style={{ borderColor: 'rgba(0, 212, 170, 0.4)', background: 'rgba(0, 212, 170, 0.08)' }}>
            <CheckCircle2 style={{ width: 13, height: 13, color: 'var(--accent-primary)' }} />
            <span>Verification: <strong style={{ color: 'var(--accent-primary)' }}>Deterministic Causal Verifier: READY</strong></span>
          </div>

          <span className="simulation-pill" style={{ padding: '3px 8px', fontSize: 10 }}>
            SIMULATION / DEMO ENVIRONMENT
          </span>

          {/* Voice Assistant Push-To-Talk Control */}
          <VoiceControl onCommandTrigger={handleVoiceCommand} isCompact />
        </div>

        {/* Navigation Actions */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <NavLink
            to="/"
            className={({ isActive }) => `btn ${isActive && !isJudgeMode ? 'btn-primary' : 'btn-ghost'}`}
            style={{ padding: '8px 14px', fontSize: 13 }}
          >
            <LayoutDashboard style={{ width: 15, height: 15 }} />
            <span style={{ marginLeft: 6 }}>Command Center</span>
          </NavLink>

          <NavLink
            to="/judge"
            className={({ isActive }) => `btn ${isActive ? 'btn-primary' : 'btn-secondary'}`}
            style={{
              padding: '8px 16px',
              fontSize: 13,
              fontWeight: 700,
              background: isJudgeMode ? 'var(--accent-primary)' : 'rgba(0, 212, 170, 0.12)',
              color: isJudgeMode ? '#0a0e14' : 'var(--accent-primary)',
              borderColor: 'var(--accent-primary)'
            }}
          >
            <Gavel style={{ width: 15, height: 15 }} />
            <span style={{ marginLeft: 6 }}>JUDGE MODE</span>
          </NavLink>

          <NavLink
            to="/why"
            className={({ isActive }) => `btn ${isActive ? 'btn-primary' : 'btn-ghost'}`}
            style={{ padding: '8px 12px', fontSize: 13 }}
            title="Why COSKA?"
          >
            <HelpCircle style={{ width: 15, height: 15 }} />
            <span style={{ marginLeft: 6 }}>Why COSKA?</span>
          </NavLink>

          <NavLink
            to="/architecture"
            className={({ isActive }) => `btn ${isActive ? 'btn-primary' : 'btn-ghost'}`}
            style={{ padding: '8px 12px', fontSize: 13 }}
            title="Technical Architecture"
          >
            <Code style={{ width: 15, height: 15 }} />
            <span style={{ marginLeft: 6 }}>Architecture</span>
          </NavLink>
        </nav>
      </header>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}
