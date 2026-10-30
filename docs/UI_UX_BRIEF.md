# UI_UX_BRIEF.md - COSKA Design System

## Visual Language: Professional SRE Control Center

### Design Philosophy
- **Not a chatbot** - Structured investigation workspace
- **Data-dense but scannable** - Monospace for technical data, clear hierarchy
- **Status-first** - Color = meaning, not decoration
- **Dark operational theme** - Reduced eye strain for on-call
- **Keyboard-first** - All actions accessible via keyboard

---

## Color System (CSS Custom Properties)

### Semantic Colors
```css
:root {
  /* Backgrounds */
  --bg-primary: #0a0e14;        /* Deep navy-black */
  --bg-secondary: #0f141a;      /* Cards, panels */
  --bg-tertiary: #151b23;       /* Inputs, elevated */
  --bg-elevated: #1a222d;       /* Modals, dropdowns */
  
  /* Foregrounds */
  --fg-primary: #e8edf3;        /* Primary text */
  --fg-secondary: #94a3b8;      /* Secondary text */
  --fg-muted: #5e6e82;          /* Labels, placeholders */
  
  /* Borders */
  --border-primary: #1e2a38;    /* Default borders */
  --border-secondary: #2d3a4a;  /* Focused/active borders */
  
  /* Accents (Semantic - never decorative) */
  --accent-primary: #00e599;    /* Success, verified, healthy, primary actions */
  --accent-info: #00c8ff;       /* Information, active, investigating */
  --accent-warning: #ffaa00;    /* Warning, weakened, degraded */
  --accent-danger: #ff5252;     /* Error, critical, rejected, failed */
  --accent-secondary: #b88cff;  /* Secondary actions, repository */
  
  /* Status Colors (Direct mapping) */
  --status-healthy: #00e599;
  --status-degraded: #ffaa00;
  --status-critical: #ff5252;
  --status-unknown: #5e6e82;
  
  /* Severity Colors */
  --severity-low: #00e599;
  --severity-medium: #00c8ff;
  --severity-high: #ffaa00;
  --severity-critical: #ff5252;
  
  /* Verdict Colors */
  --verdict-verified: #00e599;
  --verdict-failed: #ff5252;
  --verdict-unverified: #ffaa00;
  --verdict-insufficient: #5e6e82;
  
  /* Source Type Colors */
  --source-log: #00c8ff;
  --source-repo: #b88cff;
  --source-config: #ffaa00;
  --source-deployment: #00e599;
  --source-runtime: #ff7b7b;
  --source-web: #ff6464;
  --source-test: #00e599;
  --source-rag: #00e599;
  
  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  
  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-8: 48px;
  
  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.5);
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
  
  /* Z-index */
  --z-dropdown: 100;
  --z-modal: 200;
  --z-toast: 300;
  --z-tooltip: 400;
}
```

### Light Mode (Optional)
```css
@media (prefers-color-scheme: light) {
  :root {
    --bg-primary: #f8fafc;
    --bg-secondary: #ffffff;
    --bg-tertiary: #f1f5f9;
    --bg-elevated: #ffffff;
    --fg-primary: #0f172a;
    --fg-secondary: #475569;
    --fg-muted: #94a3b8;
    --border-primary: #e2e8f0;
    --border-secondary: #cbd5e1;
    /* Accents unchanged - semantic meaning preserved */
  }
}
```

---

## Typography

### Font Stack
```css
font-family: var(--font-sans);  /* UI text, labels, descriptions */
font-family: var(--font-mono);  /* IDs, codes, config values, timestamps, JSON */
```

### Scale
```css
/* Headings */
.text-h1 { font-size: 28px; font-weight: 700; line-height: 1.2; }
.text-h2 { font-size: 22px; font-weight: 600; line-height: 1.3; }
.text-h3 { font-size: 18px; font-weight: 600; line-height: 1.4; }

/* Body */
.text-body { font-size: 14px; line-height: 1.6; }
.text-body-sm { font-size: 13px; line-height: 1.5; }
.text-caption { font-size: 12px; line-height: 1.5; color: var(--fg-muted); }
.text-mono { font-family: var(--font-mono); font-size: 12px; }
.text-mono-lg { font-family: var(--font-mono); font-size: 14px; }

/* Code */
code { font-family: var(--font-mono); font-size: 0.9em; background: var(--bg-tertiary); padding: 2px 6px; border-radius: var(--radius-sm); }
pre { font-family: var(--font-mono); font-size: 11px; line-height: 1.5; overflow: auto; }
```

---

## Component Library

### Layout
```css
.app-layout {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 100vh;
  background: var(--bg-primary);
  color: var(--fg-primary);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-5);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
}

.main-content {
  padding: var(--space-5);
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-5);
  flex-wrap: wrap;
  gap: var(--space-3);
}

.page-title { font-size: 22px; font-weight: 700; }
.page-subtitle { font-size: 13px; color: var(--fg-muted); margin-top: 2px; }
.section-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--fg-muted); margin-bottom: 12px; }
```

### Cards
```css
.card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.card:hover { border-color: var(--border-secondary); }

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--border-primary);
}
```

### Buttons
```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  font-size: 13px;
  font-weight: 600;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: var(--font-sans);
}

.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-primary {
  background: var(--accent-primary);
  color: #000;
  border-color: var(--accent-primary);
}
.btn-primary:hover:not(:disabled) {
  box-shadow: 0 0 20px rgba(0, 229, 153, 0.4);
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--fg-primary);
  border-color: var(--border-primary);
}
.btn-secondary:hover:not(:disabled) {
  background: var(--bg-elevated);
  border-color: var(--border-secondary);
}

.btn-ghost {
  background: transparent;
  color: var(--fg-secondary);
  border-color: transparent;
}
.btn-ghost:hover:not(:disabled) {
  background: var(--bg-tertiary);
  color: var(--fg-primary);
}

.btn-danger {
  background: var(--accent-danger);
  color: #fff;
  border-color: var(--accent-danger);
}
```

### Badges
```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-radius: 999px;
  font-family: var(--font-mono);
}

.badge-low { background: var(--bg-tertiary); color: var(--fg-muted); }
.badge-verified { background: rgba(0, 229, 153, 0.15); color: var(--accent-primary); }
.badge-unverified { background: rgba(255, 170, 0, 0.15); color: var(--accent-warning); }
.badge-failed { background: rgba(255, 82, 82, 0.15); color: var(--accent-danger); }
.badge-critical { background: rgba(255, 82, 82, 0.15); color: var(--accent-danger); }
.badge-high { background: rgba(255, 170, 0, 0.15); color: var(--accent-warning); }
.badge-medium { background: rgba(0, 200, 255, 0.15); color: var(--accent-info); }
.badge-primary { background: rgba(0, 229, 153, 0.15); color: var(--accent-primary); }
```

### Status Indicators
```css
.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--fg-secondary);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--fg-muted);
}

.status-dot.running {
  background: var(--accent-primary);
  animation: pulse 2s infinite;
}

.status-dot.warning { background: var(--accent-warning); }
.status-dot.critical { background: var(--accent-danger); }
.status-dot.healthy { background: var(--accent-primary); }
.status-dot.degraded { background: var(--accent-warning); }
.status-dot.unknown { background: var(--fg-muted); }

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.9); }
}

.simulation-pill {
  background: rgba(255, 170, 0, 0.15);
  color: var(--accent-warning);
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
```

### Tables
```css
.table-container { overflow-x: auto; border-radius: var(--radius-md); border: 1px solid var(--border-primary); }

table { width: 100%; border-collapse: collapse; font-size: 13px; }

th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  background: var(--bg-tertiary);
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--fg-muted);
  border-bottom: 1px solid var(--border-primary);
}

td {
  padding: var(--space-2) var(--space-4);
  border-bottom: 1px solid var(--border-primary);
  vertical-align: middle;
}

tr:last-child td { border-bottom: none; }
tr:hover td { background: var(--bg-tertiary); }

.mono { font-family: var(--font-mono); font-size: 12px; }
```

### Forms
```css
.input {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  color: var(--fg-primary);
  font-size: 13px;
  font-family: var(--font-sans);
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(0, 229, 153, 0.15);
}

.input::placeholder { color: var(--fg-muted); }

.input-error { border-color: var(--accent-danger); }
```

### Grids
```css
.grid { display: grid; gap: var(--space-4); }
.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }
.grid-5 { grid-template-columns: repeat(5, 1fr); }

@media (max-width: 1024px) {
  .grid-5, .grid-4 { grid-template-columns: repeat(2, 1fr); }
  .grid-3 { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 640px) {
  .grid-2, .grid-3, .grid-4, .grid-5 { grid-template-columns: 1fr; }
}
```

### Status Pills
```css
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  font-size: 12px;
}

.status-pill.success { border-color: rgba(0, 229, 153, 0.4); background: rgba(0, 229, 153, 0.08); }
.status-pill.warning { border-color: rgba(255, 170, 0, 0.4); background: rgba(255, 170, 0, 0.08); }
.status-pill.error { border-color: rgba(255, 82, 82, 0.4); background: rgba(255, 82, 82, 0.08); }
```

### Evidence Tags
```css
.evidence-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 600;
  border-radius: 999px;
  font-family: var(--font-mono);
}

.evidence-tag.supporting { background: rgba(0, 229, 153, 0.15); color: var(--accent-primary); }
.evidence-tag.contradicting { background: rgba(255, 82, 82, 0.15); color: var(--accent-danger); }
```

### Hypothesis Cards
```css
.hypothesis-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  padding: var(--space-4);
  transition: border-color var(--transition-fast);
}

.hypothesis-card.supported { border-color: var(--accent-primary); }
.hypothesis-card.rejected { border-color: var(--accent-danger); opacity: 0.7; }
.hypothesis-card.weakened { border-color: var(--accent-warning); }
.hypothesis-card.active { border-color: var(--accent-info); }

.hypothesis-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}

.hypothesis-confidence {
  font-size: 24px;
  font-weight: 700;
  font-family: var(--font-mono);
}

.hypothesis-confidence-bar {
  height: 6px;
  background: var(--bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: var(--space-3);
}

.hypothesis-confidence-bar > div {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s ease;
}

.hypothesis-evidence {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: var(--space-3);
}

.evidence-tag { ... } /* See above */
```

### Verification Stages
```css
.verification-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
}

.verification-stage {
  padding: var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  text-align: center;
}

.verification-stage.passed { border-color: var(--accent-primary); }
.verification-stage.failed { border-color: var(--accent-danger); }

.verification-stage-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--fg-muted);
  margin-bottom: var(--space-2);
}

.verification-stage-result {
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-mono);
  margin-bottom: var(--space-2);
}

.verification-stage-result.passed { color: var(--accent-primary); }
.verification-stage-result.failed { color: var(--accent-danger); }

.verification-verdict {
  padding: var(--space-5);
  text-align: center;
  border-radius: var(--radius-lg);
  margin-top: var(--space-4);
}

.verification-verdict.verified { background: rgba(0, 229, 153, 0.1); border: 1px solid var(--accent-primary); }
.verification-verdict.failed { background: rgba(255, 82, 82, 0.1); border: 1px solid var(--accent-danger); }
.verification-verdict.unverified { background: rgba(255, 170, 0, 0.1); border: 1px solid var(--accent-warning); }

.verdict-value {
  font-size: 36px;
  font-weight: 800;
  font-family: var(--font-mono);
  letter-spacing: 0.02em;
}

.verdict-value.verified { color: var(--accent-primary); }
.verdict-value.failed { color: var(--accent-danger); }
.verdict-value.unverified { color: var(--accent-warning); }
```

### Modal
```css
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  animation: fadeIn var(--transition-fast);
}

.modal {
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow: auto;
  animation: slideUp var(--transition-normal);
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
```

### Toast Notifications
```css
.toast-container {
  position: fixed;
  bottom: var(--space-5);
  right: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  z-index: var(--z-toast);
}

.toast {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  min-width: 280px;
  max-width: 400px;
  animation: slideInRight var(--transition-normal);
}

.toast.success { border-left: 4px solid var(--accent-primary); }
.toast.warning { border-left: 4px solid var(--accent-warning); }
.toast.error { border-left: 4px solid var(--accent-danger); }
.toast.info { border-left: 4px solid var(--accent-info); }

@keyframes slideInRight { from { opacity: 0; transform: translateX(100%); } to { opacity: 1; transform: translateX(0); } }
```

---

## Key Interactions

### Investigation Progress Bar
```tsx
// 8 phases with icons
const STEPS = [
  { key: 'TRIAGING', label: 'Triage', icon: AlertTriangle },
  { key: 'COLLECTING_EVIDENCE', label: 'Collect Evidence', icon: Search },
  { key: 'BUILDING_TIMELINE', label: 'Build Timeline', icon: Clock },
  { key: 'GENERATING_HYPOTHESES', label: 'Generate Hypotheses', icon: Lightbulb },
  { key: 'INVESTIGATING', label: 'Investigate', icon: Target },
  { key: 'RESEARCHING', label: 'Research External', icon: Shield },
  { key: 'ROOT_CAUSE_IDENTIFIED', label: 'Root Cause', icon: CheckCircle },
  { key: 'REMEDIATION_PROPOSED', label: 'Remediation', icon: Shield },
  // ... verification, resolved
];

// Render: Completed = green check, Current = spinning, Future = gray icon
```

### Confidence Bars
```tsx
// Animated width transition
<div className="hypothesis-confidence-bar">
  <div style={{ width: `${confidence}%`, background: statusColor }} />
</div>
```

### Verification Matrix
```tsx
// 4-column grid with color-coded pass/fail
// Baseline: Red=FAIL (expected), Post-Fix: Green=PASS, Health: Green=PASS, Control: Red=FAIL (expected)
```

### Blast Radius Visualization
```tsx
// Service cards with impact badges
// Dependency edges: Red=Critical, Orange=Degraded, Green=Optional
```

---

## Responsive Behavior

| Breakpoint | Behavior |
|------------|----------|
| ≥1200px | Full 5-column KPI grid, 4-column verification, side panels |
| 1024-1199px | 2-3 column grids, stacked side panels |
| 768-1023px | 2-column grids, collapsible navigation |
| <768px | Single column, hamburger menu, stacked cards |

---

## Accessibility

### Color Contrast (WCAG AA)
- All text on backgrounds: ≥4.5:1
- Large text (≥18px): ≥3:1
- Status colors tested against backgrounds

### Keyboard Navigation
- All interactive elements: focus-visible outline
- Tab order logical
- Escape closes modals/dropdowns
- Enter/Space activates buttons

### Screen Readers
- Semantic HTML (nav, main, section, article)
- ARIA labels on icon-only buttons
- Status announcements for live regions
- Table headers with scope

### Motion
- `prefers-reduced-motion`: Disable animations
- Pulse animation respects preference

---

## Empty States
```tsx
// Pattern: Icon + Title + Description + Action
<div className="card" style={{ textAlign: 'center', padding: 48 }}>
  <Icon size={48} color="var(--fg-muted)" />
  <h3>No evidence collected yet</h3>
  <p style={{ color: 'var(--fg-secondary)', marginTop: 8 }}>
    Start an investigation to begin collecting evidence...
  </p>
  <Button onClick={startInvestigation}>Start Investigation</Button>
</div>
```

---

## Loading States
```tsx
// Skeleton cards for lists
<div className="card skeleton">
  <div className="skeleton-line" style={{ width: '60%', height: 16 }} />
  <div className="skeleton-line" style={{ width: '40%', height: 12 }} />
  <div className="skeleton-line" style={{ width: '80%', height: 12 }} />
</div>

// Spinner for actions
<RotateCcw className="spin" size={20} />
```

### Skeleton Animation
```css
.skeleton-line {
  background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-elevated) 50%, var(--bg-tertiary) 75%);
  background-size: 200% 100%;
  border-radius: var(--radius-sm);
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```

---

## Icon System
- **Lucide React** only
- Consistent sizing: 14px (inline), 16px (buttons), 18px (headers), 20-24px (feature)
- Never mix icon libraries

---

## Animation Principles
- **Fast** (150-250ms) for UI feedback
- **Meaningful** - Loading, transitions, not decoration
- **Respects** `prefers-reduced-motion`
- **No** bounce, elastic, or playful easings