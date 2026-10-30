# APP_FLOW.md - COSKA Application Flow

## User Journeys

### 1. Dashboard (Command Center)
**Route:** `/`
**Purpose:** System overview, incident triage, quick actions

**Flow:**
```
User lands on Dashboard
    ↓
Auto-loads: Incidents (10s poll), Infra status (AI, Tavily, Sandbox, DB)
    ↓
User sees:
  - KPI Cards: Active, Critical, Investigating, Resolved Today
  - Infrastructure Status: AI Provider, Tavily, Sandbox, Database
  - Active Incidents Table (filterable)
  - Recently Resolved Table
    ↓
Actions:
  - Click "Investigate" → /incidents/{id}
  - Click "RUN JUDGE DEMO" → /judge
  - Click "Incident Intelligence" → /intelligence
  - Click "Knowledge Base" → /knowledge
  - Click "Evidence Graph" → /graph
  - Click "Services" → /services
```

---

### 2. Incident Intake & Intelligence
**Route:** `/intelligence` (standalone) or `/incidents/{id}/intelligence` (tab)
**Purpose:** Structured understanding of incident before investigation

**Flow:**
```
User creates incident (POST /api/incidents) OR selects existing
    ↓
GET /api/incidents/{id}/intelligence?use_ai=false
    ↓
Backend extracts deterministically:
  - Service, Severity, Environment
  - Symptoms (HTTP 500 spike, DB timeout, pool exhaustion)
  - Components (payment-api, postgresql, redis)
  - Error Types (database, network, timeout)
  - Timestamps from logs
  - Config Values (DB_POOL_SIZE=5, TIMEOUT=5)
  - Suspected Dependencies (PostgreSQL, Stripe)
  - Probable Causes (pool exhaustion, retry storm, etc.)
  - Keywords, Technical Entities
  - Business Impact Assessment
    ↓
Optional: use_ai=true → LLM enhancement for semantic interpretation
    ↓
UI displays: Structured cards with severity badges, component icons, config table, probable causes ranked
    ↓
User can: Start Investigation → /incidents/{id}
```

---

### 3. Investigation (8-Phase Autonomous Workflow)
**Route:** `/incidents/{id}` (default tab)
**Purpose:** Execute and monitor autonomous investigation

**Flow:**
```
User clicks "Investigate" on incident
    ↓
POST /api/incidents/{id}/investigate {auto_approve: false}
    ↓
Backend Orchestrator starts 8-phase workflow:
  
  PHASE 1: INCIDENT_INTAKE
  - Ingest incident, check incident memory for similar cases
  - RAG retrieval: search runbooks for symptoms
  - Store top runbook as evidence (source_type=RAG)
  
  PHASE 2: EVIDENCE_COLLECTION
  - inspect_logs: regex analysis → Evidence items
  - inspect_configuration: parse .env → Evidence items
  - inspect_deployment: extract version/changes → Evidence items
  - inspect_runtime: simulated metrics → Evidence items
  - inspect_repository: read repo files → Evidence items
  
  PHASE 3: TIMELINE_BUILD
  - Chronological ordering of all events
  - Format for display
  
  PHASE 4: HYPOTHESIS_GENERATION
  - Template matching on evidence → 3-5 hypotheses
  - LLM refinement with evidence context
  - Confidence scoring + status (ACTIVE/SUPPORTED/WEAKENED/REJECTED)
  
  PHASE 5: INVESTIGATION
  - For each ACTIVE/SUPPORTED hypothesis:
    - Execute next_investigation_action (tool call)
    - New evidence → update hypotheses
  - External research (Tavily) for top 2 hypotheses
  - Update hypotheses with all evidence
  
  PHASE 6: ROOT_CAUSE
  - LLM synthesizes ALL evidence → single root cause
  - Confidence, supporting/contradicting evidence IDs
  - Rejected hypotheses with reasons
  - Recommended remediation
  
  PHASE 7: REMEDIATION
  - LLM generates specific remediation plan
  - Validation: exact_change, risk, rollback_plan
  - If invalid → no remediation
  
  PHASE 8: VERIFICATION (if auto_approve or manual trigger)
  - Sandbox: BASELINE (fail) → POST-FIX (pass) → HEALTH (pass) → CONTROL (fail)
  - Verdict: VERIFIED / FAILED / UNVERIFIED / INSUFFICIENT_EVIDENCE
  - Store VerificationResult + Receipt
  
  PHASE 9: MEMORY
  - If VERIFIED: save to incident_memory for future similarity

Frontend polls /incidents/{id} every 5s
    ↓
UI Updates in Real-time:
  - Progress bar (8 phases with icons)
  - Current phase highlight
  - Evidence count, Hypothesis status
  - Root cause card (when ready)
  - Remediation card (when ready)
  - Verification matrix (when complete)
    ↓
Final State: RESOLVED (VERIFIED) or VERIFICATION_FAILED
    ↓
User can navigate tabs: Evidence, Hypotheses, Root Cause, Remediation, Verification, Graph
```

---

### 4. Evidence Tab
**Route:** `/incidents/{id}/evidence`
**Purpose:** Browse all collected evidence by source type

**Flow:**
```
GET /api/incidents/{id}/evidence
    ↓
Group by source_type: LOG, CONFIG, DEPLOYMENT, RUNTIME, REPOSITORY, WEB, RAG
    ↓
UI: Source type summary cards (count per type)
    ↓
Expandable sections per source type:
  - Evidence cards with: ID, confidence badge, component, claim, reference, timestamp
  - Color-coded by source type
  - Raw data expandable
```

---

### 5. Hypotheses Tab
**Route:** `/incidents/{id}/hypotheses`
**Purpose:** View competing hypotheses with confidence evolution

**Flow:**
```
GET /api/incidents/{id}/hypotheses
    ↓
Sort by confidence (descending)
    ↓
UI: Hypothesis cards with:
  - Rank number + title
  - Status badge (SUPPORTED=green, WEAKENED=yellow, REJECTED=red, ACTIVE=blue)
  - Confidence percentage bar (animated)
  - Description
  - Supporting evidence tags (green)
  - Contradicting evidence tags (red)
  - Next investigation action
    ↓
Click hypothesis ID → shows decision history (confidence changes, evidence added, reasoning)
```

---

### 6. Root Cause Tab
**Route:** `/incidents/{id}/root-cause`
**Purpose:** Display identified root cause with evidence chain

**Flow:**
```
GET /api/incidents/{id}/root-cause
    ↓
UI:
  - Large confidence badge (green≥80%, yellow≥50%, red<50%)
  - Root cause statement (prominent)
  - Why box: Evidence chain with numbered supporting evidence
  - Supporting evidence tags
  - Contradicting evidence tags (if any)
  - Rejected hypotheses with reasons
  - Recommended remediation preview (exact_change, risk, expected effect)
```

---

### 7. Remediation Tab
**Route:** `/incidents/{id}/remediation`
**Purpose:** Review and apply fix

**Flow:**
```
GET /api/incidents/{id}/remediation
    ↓
UI:
  - Exact change in monospace highlight box
  - Description + Expected Effect
  - Risk Assessment: LOW/MEDIUM/HIGH badge
  - Blast Radius
  - Rollback Plan (code block)
    ↓
Actions:
  - "Apply to Sandbox & Verify" → POST /api/incidents/{id}/apply-fix
  - "Simulate (Dry Run)" → POST /api/incidents/{id}/simulate-fix
    ↓
If applied: Shows verification progress in real-time
```

---

### 8. Verification Tab
**Route:** `/incidents/{id}/verification`
**Purpose:** Causal verification matrix + receipt

**Flow:**
```
GET /api/incidents/{id}/verification
    ↓
UI: 4-Stage Matrix
  ┌─────────────┬─────────────┬─────────────┬─────────────┐
  │  BASELINE   │  POST-FIX   │  HEALTH     │  CONTROL    │
  │  (FAIL)     │  (PASS)     │  (PASS)     │  (FAIL)     │
  │  Reproduced │  Fixed works│  Healthy    │  Failure    │
  │  incident   │  after fix  │  with fix   │  returns    │
  └─────────────┴─────────────┴─────────────┴─────────────┘
    ↓
Final Verdict: VERIFIED (green) / FAILED (red) / UNVERIFIED (yellow)
    ↓
Details: Evidence count, Model, Test exit codes, Raw details JSON
    ↓
Verification Receipt (JSON):
  - Incident ID, Root Cause, Remediation
  - Baseline/Post-Fix/Health/Control results
  - Verdict, Evidence count, Model
  - Knowledge sources, Tavily usage
  - Timestamp, Receipt ID, Hash
    ↓
"Copy JSON" button for audit
```

---

### 9. Evidence Graph Tab
**Route:** `/incidents/{id}/graph`
**Purpose:** Visual causal graph

**Flow:**
```
GET /api/incidents/{id}/evidence-graph
    ↓
Canvas rendering (Cytoscape-style):
  Nodes: Incident → Service → Components → Evidence → Hypotheses → Root Cause → Remediation → Verification
  Edges: derived_from, supports, contradicts, caused_by, verified_by
    ↓
Controls: Layout selector (hierarchical/force/radial)
    ↓
Click node → Detail panel with properties
    ↓
Legend: Node types (colors), Edge types (colors)
```

---

### 10. Knowledge Base (RAG)
**Route:** `/knowledge`
**Purpose:** Search offline runbooks

**Flow:**
```
Search bar: "pool exhaustion" → POST /api/rag/search
    ↓
Results with:
  - Rank # + Relevance score (0-99%)
  - Title + Category badge
  - Snippet with matched terms highlighted
  - Match reason: "title matches query; tags match: pool, exhaustion"
  - Source provenance
    ↓
Click result → Modal with full document:
  - Title, Category, Summary, Snippet, Tags
  - Match reason, Source
  - Copy JSON button
    ↓
Category filter pills: database, network, deployment, cache, runtime, kubernetes, process, reference, security
```

---

### 11. Service Map
**Route:** `/services`
**Purpose:** Service topology + blast radius

**Flow:**
```
GET /api/service-map
    ↓
Canvas: 12 services with dependency edges
  - Color by type: client=blue, gateway=orange, api=blue, db=green, cache=yellow, queue=purple, external=magenta
  - Shape by type: rectangle, diamond, ellipse, hexagon, octagon, vee, star
  - Status ring: green=healthy, yellow=degraded, red=critical
    ↓
GET /api/service-map/status → Status badges on each service
    ↓
Click service → Side panel:
  - Service details (SLOs, metadata)
  - Depends on (outgoing edges)
  - Dependents (incoming edges)
  - Status dropdown (healthy/degraded/critical)
  - "Blast Radius" button
    ↓
Blast Radius: GET /api/service-map/blast-radius/{service}
  - Direct dependencies, Transitive dependencies
  - Impacted services with impact level (CRITICAL/DEGRADED/LOW)
  - Error increase %, Transaction impact %, Recovery time estimate
```

---

### 12. Judge Mode (Canonical Demo)
**Route:** `/judge`
**Purpose:** One-click canonical demonstration

**Flow:**
```
Page loads:
  - Scenario selector (6 canonical scenarios)
  - Infra badges: AI Provider, Sandbox, Tavily, Verifier
  
User selects scenario (default: Payment Pool Exhaustion)
    ↓
Click "RUN CANONICAL DEMO"
    ↓
POST /api/demo/scenarios/{id}/run {auto_approve: true}
    ↓
Real-time progress:
  - Animated progress: Incident → NLP → RAG → Planner → Evidence → Hypotheses → Root Cause → Remediation → Sandbox → Verification → VERIFIED
  - Agent trace with timestamps
    ↓
Tabs when complete:
  - Overview: Executive summary + verification matrix
  - RAG: Retrieved runbooks with provenance
  - Graph: Causal hierarchy + evidence list
  - Hypotheses: Confidence bars + status
  - Trace: 31-step agent execution log
  - Receipt: Full JSON verification receipt (copyable)
```

---

### 13. Voice Assistant
**Route:** Global (floating button)
**Purpose:** Voice-driven investigation

**Flow:**
```
User clicks microphone → Web Speech API starts
    ↓
UI: LISTENING (pulsing animation)
    ↓
User speaks: "Investigate payment pool exhaustion"
    ↓
Deterministic intent parsing:
  - "investigate" + "payment" + "pool exhaustion" → scenario: payment_pool_exhaustion
    ↓
UI: THINKING
    ↓
Launches: POST /api/demo/scenarios/payment_pool_exhaustion/run
    ↓
UI: EXECUTING (shows phase progress)
    ↓
Complete → COMPLETE state
    ↓
Voice reads: "Investigation complete. Root cause: Database connection pool exhaustion. Verdict: VERIFIED."
```

---

### 14. Architecture Page
**Route:** `/architecture`
**Purpose:** System diagram + principles

**Flow:**
```
Static page with:
  - Core Principle: LLM REASONS / TOOLS ACT / VERIFIER DECIDES
  - Architecture diagram (Mermaid or static SVG)
  - Component descriptions
  - Data flow
  - Security model
  - Verification logic
```

---

### 15. Login (Optional)
**Route:** `/login`
**Purpose:** Authentication for production

**Flow:**
```
If AUTH_REQUIRED=true:
  - Redirect to /login
  - POST /api/auth/login {email, password}
  - Set HttpOnly Secure cookie
  - Redirect to /
    ↓
All API calls include cookie automatically
    ↓
All queries scoped to user_id
```

---

## State Management

### Frontend
- **React useState/useEffect** for component state
- **React Router** for navigation state
- **No global state library** (kept simple)
- **Polling** for investigation progress (5s interval)

### Backend
- **InvestigationState** class in orchestrator (in-memory + persisted)
- **StorageService** for SQLite persistence
- **Singleton providers** (AI, RAG, Tool Registry)

---

## Error Flows

| Error | Frontend | Backend |
|-------|----------|---------|
| 401 Unauthorized | Redirect to login | Clear cookie, 401 |
| 403 Forbidden | "Access denied" toast | Query scoping |
| 404 Not Found | "Not found" page | Safe 404 (no info leak) |
| 429 Rate Limited | Retry with backoff | 429 + Retry-After |
| 500 Server Error | "Something went wrong" | Structured error log |
| Provider unavailable | "AI offline" badge | Fallback to mock |
| Tavily failed | "Research offline" | Graceful degradation |
| Sandbox failed | "Sandbox error" | LocalSafe fallback |