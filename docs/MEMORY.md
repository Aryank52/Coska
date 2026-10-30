# MEMORY.md - Architectural Decisions & Constraints

## Architectural Decisions

### 1. Monolithic FastAPI + React (Not Microservices)
**Decision:** Single FastAPI backend serving React SPA
**Rationale:** Hackathon scope, simpler deployment, shared SQLite, easier debugging
**Constraint:** Must remain single deployable unit

### 2. SQLite for Persistence (Not PostgreSQL)
**Decision:** SQLite with SQLAlchemy async
**Rationale:** Zero-config, portable, sufficient for demo, WAL mode for concurrency
**Constraint:** No schema migrations in demo; schema in `StorageService._init_db()`

### 3. Deterministic Verification Over LLM Judgment
**Decision:** 3-stage causal verification (Baseline→Post-Fix→Health→Control) is the ONLY way to get VERIFIED
**Rationale:** LLM hallucinations; causal proof requires actual execution
**Constraint:** Never allow LLM to declare VERIFIED. Verifier class is final authority.

### 4. Mock-First Provider Strategy
**Decision:** `AI_PROVIDER=mock` default; Nebius/Tavily optional
**Rationale:** Offline development, no API costs, deterministic tests, hackathon demo without keys
**Constraint:** Mock must be first-class, not a stub. All features work with mock.

### 5. BM25 RAG (Not Vector Embeddings)
**Decision:** Offline BM25 with 20 runbooks
**Rationale:** No embedding model, no vector DB, deterministic scores, works offline
**Constraint:** No semantic search beyond BM25; exact token matching

### 5. LocalSafe Sandbox (Default)
**Decision:** Subprocess with allowlist, not Docker by default
**Rationale:** Works without Docker, faster startup, path containment via allowlist
**Constraint:** Docker optional; local_safe must execute remediation verification

### 6. 8-Phase Investigation (Fixed)
**Decision:** Fixed phase sequence with safety budgets
**Rationale:** Predictable, auditable, bounded execution
**Constraint:** Phases cannot be skipped or reordered; safety limits enforced

### 7. 6 Canonical Demo Scenarios
**Decision:** Fixed scenarios with known expected outcomes
**Rationale:** Judge Mode reproducibility, evaluation harness, regression testing
**Constraint:** Scenarios must produce VERIFIED with expected root cause/remediation

### 8. TypeScript Strict Mode
**Decision:** Strict TS, no `any` unless unavoidable
**Rationale:** Catch regressions at compile time, IDE support
**Constraint:** All API responses typed; shared types in `types/incident.ts`

---

## Important Constraints

### Safety Budgets (Enforced in Orchestrator)
| Limit | Default | Enforcement |
|-------|---------|-------------|
| `MAX_AGENT_STEPS` | 40 | `Orchestrator._check_safety_limits()` |
| `MAX_TOOL_CALLS` | 25 | Counter incremented per tool call |
| `MAX_RETRIES` | 3 | Retry logic in tool execution |
| `MAX_INVESTIGATION_TIME` | 300s | Wall-clock timeout |

### Tool Allowlist (Registry)
Only these tools exist - model CANNOT invent tools:
- `inspect_logs`
- `inspect_configuration`
- `inspect_deployment`
- `inspect_runtime`
- `inspect_repository`
- `search_web` (Tavily)

### Path Containment (Sandbox)
- All file writes resolved to canonical path
- Must be within workspace directory
- Symlinks rejected
- Atomic writes with backup

### Command Allowlist (Sandbox)
Only allowlisted commands executable in sandbox:
- `python`, `pytest`, `uvicorn`, `pip`
- No `rm`, `mv`, `chmod`, `curl`, `wget`, `ssh`

### Provider Secrets
- `NEBIUS_API_KEY` and `TAVILY_API_KEY` ONLY in `.env` / deployment secrets
- NEVER in: code, logs, database, responses, git, README
- Status only: "configured" / "not configured"

### Verification Immutability
```
VERIFIED = Baseline FAIL + Post-Fix PASS + Health PASS + Control FAIL
```
- No LLM override
- Verifier class is single source of truth
- Receipt is append-only audit record

---

## Demo Scenarios (Fixed - Do Not Modify Expected Outcomes)

| Scenario ID | Service | Expected Root Cause | Expected Remediation |
|-------------|---------|---------------------|---------------------|
| `payment_pool_exhaustion` | payment-api | DB pool exhaustion (DB_POOL_SIZE=5) | DB_POOL_SIZE: 5 → 30 |
| `external_api_retry_misconfiguration` | payment-gateway | Retry storm (RETRY_COUNT=10) | RETRY_COUNT: 10 → 3 + backoff |
| `bad_deployment_config_regression` | user-service | Bad config (wrong password) | Fix DB_PASSWORD |
| `cache_stampede` | catalog-service | Cache stampede (TTL=0) | Fix TTL + singleflight |
| `memory_leak` | notification-service | Unbounded event buffer | Bounded LRU cache |
| `database_saturation` | order-service | Missing index (Seq Scan) | CREATE INDEX CONCURRENTLY |

**Evaluation expects:** VERDICT=VERIFIED for all 6 scenarios

---

## Current Provider Strategy

| Provider | Mode | Status | Use Case |
|----------|------|--------|----------|
| MockAIProvider | Default | ✅ Working | All development, tests, demo |
| NebiusTokenFactoryProvider | Optional | ⚠️ Needs key | Live integration only |
| TavilyClient | Optional | ⚠️ Needs key | Live web research only |

**Switching:** `export AI_PROVIDER=nebius && export NEBIUS_API_KEY=...`

---

## Security Strategy

| Layer | Implementation |
|-------|---------------|
| Secrets | `.env` only; never in code/db/logs |
| Auth | Optional (AUTH_REQUIRED=false for demo) |
| Sessions | HttpOnly cookies, Argon2, secure flags |
| Tenancy | `user_id` on all tables; query scoping |
| Rate Limits | Local (login, register, investigation, tools) |
| Input Validation | Pydantic on all endpoints |
| Tool Security | Allowlist, path containment, timeouts |
| File Safety | Canonical paths, atomic writes, no traversal |
| Error Handling | Structured errors; no stack traces to client |
| Audit Log | Login, investigation, tool, remediation, approval |
| CORS | Strict origins in production |
| Headers | CSP, X-Content-Type-Options, Referrer-Policy |

---

## Evaluation Baseline (Must Maintain)

| Metric | Target |
|--------|--------|
| Backend Tests | 43/43 PASS |
| Evaluation Harness | 24/24 PASS (3 scenarios × 8 checks) |
| Frontend TypeScript | 0 errors |
| Frontend Build | Success |
| Health Checks | 8/8 PASS |
| Doctor | 9/11 PASS (2 Docker WARN OK) |
| Security Scan | No CRITICAL/SECRET in code |
| Demo E2E | VERIFIED verdict |