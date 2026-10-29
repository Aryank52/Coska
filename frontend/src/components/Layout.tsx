import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { LayoutDashboard, Search, GitBranch, Lightbulb, Target, Shield, CheckCircle, Settings } from 'lucide-react'

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/incidents/:id', label: 'Investigation', icon: Search, children: [
    { path: '', label: 'Overview', icon: Search },
    { path: 'evidence', label: 'Evidence', icon: GitBranch },
    { path: 'hypotheses', label: 'Hypotheses', icon: Lightbulb },
    { path: 'root-cause', label: 'Root Cause', icon: Target },
    { path: 'remediation', label: 'Remediation', icon: Shield },
    { path: 'verification', label: 'Verification', icon: CheckCircle },
  ]}
]

export function Layout() {
  const location = useLocation()
  const isIncidentPage = location.pathname.startsWith('/incidents/')
  
  return (
    <div className="app-layout">
      <header className="header">
        <div className="header-brand">
          <div className="header-logo">C</div>
          <div>
            <div className="header-title">COSKA</div>
            <div className="header-tagline">Autonomous Incident Intelligence</div>
          </div>
        </div>
        
        <nav style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <NavLink to="/" className={({ isActive }) => 
            `btn ${isActive ? 'btn-primary' : 'btn-ghost'}`} style={{ padding: '8px 16px' }}>
            <LayoutDashboard className="mono" style={{ width: 16, height: 16 }} />
            <span style={{ marginLeft: 8 }}>Dashboard</span>
          </NavLink>
          
          {isIncidentPage && (
            <>
              <span style={{ color: 'var(--fg-muted)', padding: '0 8px' }}>|</span>
              <NavLink to={`/incidents/${location.pathname.split('/')[2]}`} className="btn btn-ghost" style={{ padding: '8px 16px' }}>
                <Search className="mono" style={{ width: 16, height: 16 }} />
                <span style={{ marginLeft: 8 }}>Investigation</span>
              </NavLink>
            </>
          )}
        </nav>
      </header>
      
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  )
}