# BACKEND_SCHEMA.md - Database Schema & API Contracts

## Database Schema (SQLite)

### Core Tables

```sql
-- Users (for multi-tenancy)
CREATE TABLE users (
    id TEXT PRIMARY KEY,                    -- USR-<uuid>
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,            -- Argon2id
    full_name TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Sessions
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,                    -- SES-<uuid>
    user_id TEXT NOT NULL REFERENCES users(id),
    token_hash TEXT NOT NULL,               -- SHA256 of session token
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revoked_at TEXT
);

-- Incidents
CREATE TABLE incidents (
    id TEXT PRIMARY KEY,                    -- INC-<uuid>
    user_id TEXT NOT NULL REFERENCES users(id),
    service TEXT NOT NULL,
    severity TEXT NOT NULL,                 -- LOW|MEDIUM|HIGH|CRITICAL
    description TEXT NOT NULL,
    logs TEXT,
    deployment TEXT,
    repository TEXT,
    metadata TEXT,                          -- JSON
    status TEXT NOT NULL,                   -- IncidentStatus enum
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_incidents_user ON incidents(user_id);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_service ON incidents(service);

-- Evidence
CREATE TABLE evidence (
    id TEXT PRIMARY KEY,                    -- E-<uuid>
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    source_type TEXT NOT NULL,              -- LOG|REPOSITORY|CONFIG|DEPLOYMENT|RUNTIME|WEB|TEST|RAG
    claim TEXT NOT NULL,
    reference TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    confidence REAL NOT NULL,               -- 0.0-1.0
    related_component TEXT,
    raw_data TEXT                           -- JSON
);

CREATE INDEX idx_evidence_incident ON evidence(incident_id);
CREATE INDEX idx_evidence_source ON evidence(source_type);

-- Hypotheses
CREATE TABLE hypotheses (
    id TEXT PRIMARY KEY,                    -- H-<uuid>
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    supporting_evidence_ids TEXT NOT NULL,  -- JSON array
    contradicting_evidence_ids TEXT NOT NULL, -- JSON array
    confidence REAL NOT NULL,               -- 0.0-1.0
    next_investigation_action TEXT,
    status TEXT NOT NULL,                   -- ACTIVE|WEAKENED|REJECTED|SUPPORTED
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_hypotheses_incident ON hypotheses(incident_id);

-- Remediations
CREATE TABLE remediations (
    id TEXT PRIMARY KEY,                    -- R-<uuid>
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    hypothesis_id TEXT NOT NULL REFERENCES hypotheses(id),
    type TEXT NOT NULL,                     -- CONFIGURATION_CHANGE|CODE_CHANGE|DEPENDENCY_CHANGE|SAFE_ROLLBACK|FEATURE_FLAG_CHANGE
    description TEXT NOT NULL,
    exact_change TEXT NOT NULL,
    expected_effect TEXT NOT NULL,
    risk TEXT NOT NULL,                     -- LOW|MEDIUM|HIGH
    blast_radius TEXT NOT NULL,
    rollback_plan TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_remediations_incident ON remediations(incident_id);

-- Verification Runs
CREATE TABLE verification_runs (
    id TEXT PRIMARY KEY,                    -- V-<uuid>
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    remediation_id TEXT NOT NULL REFERENCES remediations(id),
    baseline_test TEXT NOT NULL,            -- PASSED|FAILED|NOT_RUN
    post_fix_tests TEXT NOT NULL,           -- PASSED|FAILED|NOT_RUN
    health_check TEXT NOT NULL,             -- PASSED|FAILED|NOT_RUN
    control_test TEXT NOT NULL,             -- PASSED|FAILED|NOT_RUN
    verdict TEXT NOT NULL,                  -- VERIFIED|FAILED|UNVERIFIED|INSUFFICIENT_EVIDENCE
    evidence_count INTEGER NOT NULL,
    model TEXT NOT NULL,
    details TEXT NOT NULL,                  -- JSON
    created_at TEXT NOT NULL
);

CREATE INDEX idx_verification_incident ON verification_runs(incident_id);

-- Agent Actions (Audit Trail)
CREATE TABLE agent_actions (
    id TEXT PRIMARY KEY,                    -- A-<uuid>
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    step TEXT NOT NULL,
    tool TEXT,
    timestamp TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    status TEXT NOT NULL,                   -- STARTED|COMPLETED|FAILED|SKIPPED
    summary TEXT NOT NULL,
    input_data TEXT,                        -- JSON
    output_data TEXT,                       -- JSON
    error TEXT
);

CREATE INDEX idx_actions_incident ON agent_actions(incident_id);
CREATE INDEX idx_actions_timestamp ON agent_actions(timestamp);

-- Investigations (Full State Snapshots)
CREATE TABLE investigations (
    id TEXT PRIMARY KEY,                    -- RUN-<uuid>
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    current_phase TEXT NOT NULL,            -- InvestigationPhase enum
    state_json TEXT NOT NULL,               -- Full serialized InvestigationState
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_investigations_incident ON investigations(incident_id);

-- Incident Memory (Verified incidents for similarity search)
CREATE TABLE incident_memory (
    id TEXT PRIMARY KEY,                    -- MEM-<uuid>
    user_id TEXT NOT NULL REFERENCES users(id),
    service TEXT NOT NULL,
    symptoms TEXT NOT NULL,
    root_cause TEXT NOT NULL,
    evidence TEXT NOT NULL,                 -- JSON array
    remediation TEXT NOT NULL,              -- JSON
    verification_result TEXT NOT NULL,      -- JSON
    created_at TEXT NOT NULL
);

CREATE INDEX idx_memory_user ON incident_memory(user_id);
CREATE INDEX idx_memory_service ON incident_memory(service);

-- Audit Events
CREATE TABLE audit_events (
    id TEXT PRIMARY KEY,                    -- AUD-<uuid>
    user_id TEXT NOT NULL REFERENCES users(id),
    action TEXT NOT NULL,                   -- LOGIN|LOGOUT|INVESTIGATION_START|TOOL_EXECUTE|REMEDIATION_PROPOSE|REMEDIATION_APPROVE|VERIFICATION_COMPLETE|PROVIDER_FAILURE|SECURITY_REJECTION
    resource_type TEXT,                     -- INCIDENT|INVESTIGATION|REMEDIATION|VERIFICATION
    resource_id TEXT,
    details TEXT,                           -- JSON
    ip_address TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_audit_user ON audit_events(user_id);
CREATE INDEX idx_audit_action ON audit_events(action);
CREATE INDEX idx_audit_created ON audit_events(created_at);
```

---

## API Contracts (Typed)

### Base Response Wrapper
```typescript
interface ApiResponse<T> {
  data: T;
  request_id: string;
}

interface ApiError {
  request_id: string;
  error_code: string;
  message: string;
  timestamp: string;
  details?: Record<string, any>;
}
```

---

### Incidents API

#### Create Incident
```http
POST /api/incidents
Content-Type: application/json

{
  "service": "payment-api",
  "severity": "CRITICAL",
  "description": "HTTP 500 error rate increased from 1.2% to 38%",
  "logs": "2026-10-29T10:15:23.456Z ERROR payment-api: connection pool exhausted\n...",
  "deployment": "payment-api v1.8.2 deployed at 2026-10-29T10:10:00Z",
  "repository": "https://github.com/coska/payment-api",
  "metadata": {
    "configuration": "DB_POOL_SIZE=5\nDB_POOL_TIMEOUT=5\nDATABASE_URL=sqlite+aiosqlite:///./payments.db"
  }
}

Response 201:
{
  "id": "INC-A1B2C3D4",
  "service": "payment-api",
  "severity": "CRITICAL",
  "description": "HTTP 500 error rate increased from 1.2% to 38%",
  "logs": "...",
  "deployment": "...",
  "repository": "...",
  "metadata": {...},
  "status": "RECEIVED",
  "created_at": "2026-10-30T18:00:00Z",
  "updated_at": "2026-10-30T18:00:00Z"
}
```

#### List Incidents
```http
GET /api/incidents

Response 200:
[
  { "id": "INC-A1B2C3D4", "service": "payment-api", "severity": "CRITICAL", ... }
]
```

#### Get Incident
```http
GET /api/incidents/INC-A1B2C3D4

Response 200:
{ "id": "INC-A1B2C3D4", "service": "payment-api", ... }
```

#### Start Investigation
```http
POST /api/incidents/INC-A1B2C3D4/investigate
Content-Type: application/json

{ "auto_approve": false }

Response 200:
{ "incident_id": "INC-A1B2C3D4", "status": "started", "message": "Investigation started in background" }
```

#### Get Incident Timeline
```http
GET /api/incidents/INC-A1B2C3D4/timeline

Response 200:
{
  "incident_id": "INC-A1B2C3D4",
  "timeline": [
    { "timestamp": "2026-10-29T10:15:23Z", "event_type": "LOG", "title": "Connection pool exhausted", "description": "...", "source_type": "LOG", "evidence_ids": ["E-1"], "severity": "CRITICAL" },
    ...
  ]
}
```

#### Get Incident Evidence
```http
GET /api/incidents/INC-A1B2C3D4/evidence

Response 200:
{
  "incident_id": "INC-A1B2C3D4",
  "evidence": [
    { "id": "E-1", "incident_id": "INC-A1B2C3D4", "source_type": "LOG", "claim": "Found 14 timestamped log entries...", "reference": "Log lines 1-14", "timestamp": "2026-10-30T18:00:00Z", "confidence": 0.9, "related_component": "logging", "raw_data": {...} },
    ...
  ]
}
```

#### Get Incident Hypotheses
```http
GET /api/incidents/INC-A1B2C3D4/hypotheses

Response 200:
{
  "incident_id": "INC-A1B2C3D4",
  "hypotheses": [
    { "id": "H-1", "incident_id": "INC-A1B2C3D4", "title": "Database connection pool exhaustion", "description": "Application cannot acquire database connections...", "supporting_evidence_ids": ["E-1","E-2","E-3"], "contradicting_evidence_ids": [], "confidence": 0.91, "next_investigation_action": "inspect_configuration:DB_POOL_SIZE", "status": "SUPPORTED", "created_at": "...", "updated_at": "..." },
    ...
  ]
}
```

#### Get Agent Actions
```http
GET /api/incidents/INC-A1B2C3D4/actions

Response 200:
{
  "incident_id": "INC-A1B2C3D4",
  "actions": [
    { "id": "A-1", "incident_id": "INC-A1B2C3D4", "step": "INCIDENT_INTAKE", "tool": "orchestrator", "timestamp": "2026-10-30T18:00:00Z", "duration_ms": 0, "status": "COMPLETED", "summary": "Ingested incident INC-A1B2C3D4 for service payment-api", "input_data": {}, "output_data": {}, "error": null },
    ...
  ]
}
```

#### Get Root Cause
```http
GET /api/incidents/INC-A1B2C3D4/root-cause

Response 200:
{
  "incident_id": "INC-A1B2C3D4",
  "root_cause": {
    "root_cause": "Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)",
    "confidence": 0.92,
    "supporting_evidence_ids": ["E-1","E-2","E-3","E-4"],
    "contradicting_evidence_ids": [],
    "rejected_hypotheses": [{"id": "H-2", "reason": "No evidence of database CPU/memory saturation"}, ...],
    "uncertainty": null,
    "recommended_remediation": {
      "description": "Increase database connection pool size from 5 to 30...",
      "exact_change": "DB_POOL_SIZE: 5 -> 30",
      "expected_effect": "Eliminate connection pool exhaustion...",
      "risk": "LOW",
      "blast_radius": "SANDBOX_ONLY",
      "rollback_plan": "Revert DB_POOL_SIZE to 5 in configuration"
    }
  }
}
```

#### Get Remediation
```http
GET /api/incidents/INC-A1B2C3D4/remediation

Response 200:
{
  "incident_id": "INC-A1B2C3D4",
  "remediation": {
    "id": "R-1", "incident_id": "INC-A1B2C3D4", "hypothesis_id": "H-1",
    "type": "CONFIGURATION_CHANGE",
    "description": "Increase database connection pool size from 5 to 30...",
    "exact_change": "DB_POOL_SIZE: 5 -> 30",
    "expected_effect": "Eliminate connection pool exhaustion...",
    "risk": "LOW",
    "blast_radius": "SANDBOX_ONLY",
    "rollback_plan": "Revert DB_POOL_SIZE to 5 in configuration",
    "created_at": "2026-10-30T18:00:00Z"
  }
}
```

#### Simulate Fix (Dry Run)
```http
POST /api/incidents/INC-A1B2C3D4/simulate-fix

Response 200:
{ "incident_id": "INC-A1B2C3D4", "status": "simulated", "remediation": "DB_POOL_SIZE: 5 -> 30", "message": "Fix simulation completed (dry run)" }
```

#### Apply Fix + Verify
```http
POST /api/incidents/INC-A1B2C3D4/apply-fix

Response 200:
{ "incident_id": "INC-A1B2C3D4", "status": "verification_started", "message": "Fix application and verification started" }
```

---

### Enhanced API

#### Incident Intelligence
```http
GET /api/incidents/INC-A1B2C3D4/intelligence?use_ai=false

Response 200:
{
  "service": "payment-api",
  "severity": "CRITICAL",
  "symptoms": ["HTTP 500 spike", "Database timeout", "Connection pool exhaustion"],
  "components": ["payment-api", "postgresql"],
  "environment": "production",
  "error_types": ["database", "timeout"],
  "probable_causes": ["Database connection pool exhaustion", "Undersized connection pool configuration"],
  "timestamps": ["2026-10-29T10:15:23.456Z", ...],
  "configuration_values": { "DB_POOL_SIZE": "5", "DB_POOL_TIMEOUT": "5" },
  "suspected_dependencies": ["postgresql", "stripe"],
  "business_impact": "High - Customer-facing payment failures, revenue impact",
  "keywords": ["connection", "pool", "exhaustion", "timeout", "database"],
  "technical_entities": ["PostgreSQL", "SQLAlchemy", "payment-api"],
  "extraction_method": "deterministic"
}
```

#### RAG Search
```http
POST /api/rag/search
Content-Type: application/json

{ "query": "connection pool exhaustion", "top_k": 3, "include_trace": true }

Response 200:
{
  "documents": [
    {
      "id": "KB-RUNBOOK-001",
      "title": "PostgreSQL Pool Exhaustion Runbook",
      "category": "database",
      "source": "docs/runbooks/database-pool-exhaustion.md",
      "summary": "Mitigation steps and diagnostics for SQLAlchemy/PostgreSQL connection pool exhaustion",
      "content": "Symptoms: High HTTP 500 error rates...",
      "tags": ["database", "postgres", "pool", "sqlalchemy", "db_pool_size", "connection pool", "500"],
      "relevance_score": 0.94,
      "snippet": "Root Cause: DB_POOL_SIZE undersized for concurrency spike or connection leaks.",
      "matched_terms": ["pool", "exhaustion", "connection", "db_pool_size"],
      "match_reason": "tags match: pool, exhaustion, connection, db_pool_size; title matches query"
    },
    ...
  ],
  "query": "connection pool exhaustion",
  "query_tokens": ["connection", "pool", "exhaustion"],
  "trace": {
    "total_documents": 20,
    "top_results": [{ "id": "KB-RUNBOOK-001", "title": "...", "relevance_score": 0.94, "matched_terms": [...], "match_reason": "..." }]
  }
}
```

#### Evidence Graph
```http
GET /api/incidents/INC-A1B2C3D4/evidence-graph

Response 200:
{
  "incident_id": "INC-A1B2C3D4",
  "nodes": [
    { "id": "incident-INC-A1B2C3D4", "type": "incident", "label": "INC-A1B2C3D4", "data": {"service": "payment-api", "severity": "CRITICAL", ...}, "position": {"x": 0, "y": 0} },
    { "id": "evidence-E-1", "type": "evidence", "label": "E-1", "data": {"source_type": "LOG", "claim": "...", "confidence": 0.9}, "position": {"x": -200, "y": 150} },
    { "id": "hypothesis-H-1", "type": "hypothesis", "label": "H-1", "data": {"title": "Database connection pool exhaustion", "confidence": 0.91, "status": "SUPPORTED"}, "position": {"x": 0, "y": 300} },
    { "id": "root-cause", "type": "root_cause", "label": "ROOT CAUSE", "data": {"cause": "...", "confidence": 0.92}, "position": {"x": 0, "y": 450} },
    ...
  ],
  "edges": [
    { "id": "edge-E-1-H-1", "source": "evidence-E-1", "target": "hypothesis-H-1", "type": "supports", "weight": 0.91, "label": "supports (91%)" },
    { "id": "edge-H-1-root", "source": "hypothesis-H-1", "target": "root-cause", "type": "caused_by", "label": "caused by" },
    ...
  ],
  "metadata": { "node_count": 15, "edge_count": 22, "generated_at": "..." },
  "layout": "hierarchical"
}
```

#### Service Map
```http
GET /api/service-map

Response 200:
{
  "services": [
    { "id": "payment-api", "name": "Payment API", "type": "api", "status": "healthy", "metadata": {"slo_latency_p99_ms": 500, "slo_error_rate": 0.001}, "position": {"x": 0, "y": 150} },
    { "id": "postgresql", "name": "PostgreSQL Cluster", "type": "database", "status": "healthy", "metadata": {"max_connections": 100, "pool_size": 30}, "position": {"x": 0, "y": 450} },
    ...
  ],
  "dependencies": [
    { "id": "e1", "source": "payment-api", "target": "postgresql", "type": "critical", "protocol": "postgresql", "latency_ms": 5 },
    { "id": "e2", "source": "checkout-api", "target": "payment-api", "type": "critical", "protocol": "http", "latency_ms": 50 },
    ...
  ],
  "metadata": { "environment": "production", "region": "us-east-1" }
}
```

#### Blast Radius
```http
GET /api/service-map/blast-radius/payment-api

Response 200:
{
  "affected_service": "payment-api",
  "direct_dependencies": ["postgresql", "redis", "stripe"],
  "transitive_dependencies": ["message-queue"],
  "impacted_services": [
    { "service_id": "checkout-api", "service_name": "Checkout API", "impact_level": "CRITICAL", "dependency_type": "critical", "path": "Payment API -> Checkout API" },
    { "service_id": "order-api", "service_name": "Order API", "impact_level": "CRITICAL", "dependency_type": "critical", "path": "Payment API -> Order API" },
    { "service_id": "notification-api", "service_name": "Notification API", "impact_level": "DEGRADED", "dependency_type": "optional", "path": "Payment API -> Notification API" }
  ],
  "severity": "CRITICAL",
  "error_increase_percent": 75,
  "transaction_impact_percent": 38,
  "estimated_recovery_time_seconds": 120
}
```

#### Create Investigation Plan
```http
POST /api/planner/plan
Content-Type: application/json

{ "incident_id": "INC-A1B2C3D4", "auto_execute": false }

Response 200:
{
  "incident_id": "INC-A1B2C3D4",
  "goal": "Determine root cause and safely verify recovery",
  "steps": [
    { "step_id": 1, "type": "tool_call", "description": "Collect evidence via inspect_logs", "tool_name": "inspect_logs", "tool_input": {"incident_id": "INC-A1B2C3D4"}, "reasoning": "Collect log evidence for analysis", "expected_outcome": "Structured evidence from inspect_logs", "depends_on": [] },
    { "step_id": 2, "type": "tool_call", "description": "Collect evidence via inspect_configuration", "tool_name": "inspect_configuration", "tool_input": {"incident_id": "INC-A1B2C3D4", "config_keys": ["DB_POOL_SIZE"]}, "reasoning": "Validate pool size configuration", "expected_outcome": "Configuration evidence supporting or refuting cause", "depends_on": [1] },
    ...
  ],
  "current_step_index": 0,
  "created_at": "2026-10-30T18:00:00Z",
  "updated_at": "2026-10-30T18:00:00Z",
  "status": "planning",
  "total_budget": 40,
  "tool_budget": 25,
  "step_budget": 40,
  "time_budget_seconds": 300
}
```

#### Execute Plan
```http
POST /api/planner/execute
Content-Type: application/json

{ "incident_id": "INC-A1B2C3D4", "auto_execute": true }

Response 200:
{
  "success": true,
  "completed_steps": 8,
  "total_steps": 8,
  "root_cause": { "root_cause": "...", "confidence": 0.92, ... },
  "remediation": { "exact_change": "DB_POOL_SIZE: 5 -> 30", ... },
  "verification": { "verdict": "VERIFIED", ... },
  "final_state": "completed",
  "trace": [...]
}
```

#### Verification Receipt
```http
GET /api/incidents/INC-A1B2C3D4/verification-receipt

Response 200:
{
  "incident_id": "INC-A1B2C3D4",
  "service": "payment-api",
  "timestamp": "2026-10-30T18:00:00Z",
  "root_cause": "Database connection pool exhaustion...",
  "root_cause_confidence": 0.92,
  "remediation": { "exact_change": "DB_POOL_SIZE: 5 -> 30", ... },
  "verification": { "verdict": "VERIFIED", "baseline_test": "FAILED", "post_fix_tests": "PASSED", "health_check": "PASSED", "control_test": "FAILED" },
  "evidence_count": 18,
  "hypotheses_count": 4,
  "ai_provider": "mock",
  "knowledge_sources": ["KB-RUNBOOK-001", "KB-RUNBOOK-014"],
  "tavily_usage": "1 call, 5 results, 0.002 credits",
  "final_determination": "VERIFIED"
}
```

#### Incident Report
```http
GET /api/incidents/INC-A1B2C3D4/report?format=json

Response 200:
{
  "executive_summary": { "incident_id": "INC-A1B2C3D4", "service": "payment-api", "severity": "CRITICAL", "status": "RESOLVED", "description": "...", "created_at": "...", "resolved_at": "..." },
  "incident_timeline": [...],
  "affected_services": ["payment-api"],
  "evidence": [...],
  "competing_hypotheses": [...],
  "root_cause": {...},
  "remediation": {...},
  "verification": {...},
  "knowledge_sources": [...],
  "external_research": [...],
  "lessons_learned": [],
  "recommended_prevention": []
}
```

---

### Health API

```http
GET /api/health
Response: { "status": "healthy", "service": "coska", "version": "0.1.0" }

GET /api/health/ai
Response: { "status": "healthy", "provider": "mock", "model": "coska-deterministic-mock", "reachable": true, "authenticated": true, "model_available": true, "details": {...} }

GET /api/health/tavily
Response: { "status": "healthy", "configured": true, "connected": true, "details": {"status_code": "TAVILY_READY"} }

GET /api/health/sandbox
Response: { "status": "healthy", "provider": "local_safe", "available": true, "mode": "local", "details": {...} }
```

---

### Demo API

```http
GET /api/demo/scenarios
Response: { "scenarios": [ { "id": "payment_pool_exhaustion", "name": "Payment API DB Pool Exhaustion", "category": "pool_exhaustion", ... } ] }

POST /api/demo/scenarios/payment_pool_exhaustion/run
{ "auto_approve": true }
Response: { "incident_id": "INC-DEMO-...", "status": "started" }
```

---

## Error Response Format

```json
{
  "request_id": "req-abc123def456",
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid incident ID format",
  "timestamp": "2026-10-30T18:00:00Z",
  "details": { "field": "incident_id", "expected": "INC-[A-F0-9]{8}" }
}
```

### Error Codes
| Code | HTTP | Description |
|------|------|-------------|
| VALIDATION_ERROR | 422 | Request body validation failed |
| NOT_FOUND | 404 | Resource not found |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Access denied (tenant isolation) |
| RATE_LIMITED | 429 | Too many requests |
| PROVIDER_ERROR | 503 | AI provider unavailable |
| SANDBOX_ERROR | 500 | Sandbox execution failed |
| INTERNAL_ERROR | 500 | Unexpected server error |

---

## WebSocket (Future)

```typescript
// Future: Real-time investigation updates
// ws://localhost:8000/ws/incidents/{incident_id}

// Messages:
{ "type": "phase_start", "phase": "EVIDENCE_COLLECTION", "timestamp": "..." }
{ "type": "evidence_found", "evidence": {...}, "phase": "EVIDENCE_COLLECTION" }
{ "type": "hypothesis_update", "hypothesis": {...}, "phase": "HYPOTHESIS_GENERATION" }
{ "type": "root_cause", "root_cause": {...} }
{ "type": "verification_progress", "stage": "POST_FIX", "result": "PASS" }
{ "type": "verification_complete", "verdict": "VERIFIED", "receipt": {...} }
```