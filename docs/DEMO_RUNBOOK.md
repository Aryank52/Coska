# DEMO_RUNBOOK.md - COSKA Demo Scenarios Runbook

## Overview

COSKA includes **6 canonical demo scenarios** that demonstrate the full autonomous investigation workflow. Each scenario is designed to produce a **VERIFIED** verdict with a specific, expected root cause and remediation.

### Demo Modes

| Mode | Command | Purpose |
|------|---------|---------|
| **Judge Mode** | `/judge` (UI) | One-click canonical demo |
| **CLI Demo** | `python scripts/run_demo.py` | Automated end-to-end |
| **Evaluation** | `python scripts/evaluate_coska.py` | 24-check regression suite |
| **Seed Data** | `python scripts/seed_demo_data.py` | Populate demo data |

---

## Canonical Scenarios (6)

### 1. Payment API DB Pool Exhaustion (Canonical)
**ID**: `payment_pool_exhaustion`  
**Service**: `payment-api`  
**Severity**: `CRITICAL`

**Incident**:
```
HTTP 500 error rate increased from 1.2% to 38%. Users experiencing payment failures.
Logs show: "connection pool exhausted", "timeout waiting for database connection" (17 events in 90s)
Deployment: payment-api v1.8.2 deployed at 2026-10-29T10:10:00Z
Config: DB_POOL_SIZE=5, DB_POOL_TIMEOUT=5
```

**Expected Root Cause**:
> Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)

**Expected Remediation**:
```json
{
  "type": "CONFIGURATION_CHANGE",
  "exact_change": "DB_POOL_SIZE: 5 -> 30",
  "expected_effect": "Eliminate connection pool exhaustion and reduce HTTP 500 error rate to baseline",
  "risk": "LOW",
  "blast_radius": "SANDBOX_ONLY",
  "rollback_plan": "Revert DB_POOL_SIZE to 5 in configuration"
}
```

**Expected Verification**: `VERIFIED` (Baseline FAIL → Post-Fix PASS → Health PASS → Control FAIL)

---

### 2. External API Retry Misconfiguration
**ID**: `external_api_retry_misconfiguration`  
**Service**: `payment-gateway`  
**Severity**: `CRITICAL`

**Incident**:
```
Cascading HTTP 504 Gateway Timeouts. Queue buildup causing complete checkout failure.
Logs show: RETRY_COUNT=10, no backoff, upstream timeout 5s (127 retry storms in 5 min)
Deployment: checkout-api v2.3.1 deployed at 2026-10-28T14:20:00Z
Config: RETRY_COUNT=10, RETRY_BACKOFF=0, TIMEOUT=5
```

**Expected Root Cause**:
> Upstream timeout and cascading retry storm caused by excessive RETRY_COUNT=10 with no backoff or jitter

**Expected Remediation**:
```json
{
  "type": "CONFIGURATION_CHANGE",
  "exact_change": "RETRY_COUNT: 10 -> 3, RETRY_BACKOFF: 0 -> exponential_jitter, CIRCUIT_BREAKER_THRESHOLD: 0 -> 50",
  "expected_effect": "Prevent thundering herd, allow upstream recovery, reduce cascade failures by 95%",
  "risk": "LOW",
  "blast_radius": "SANDBOX_ONLY",
  "rollback_plan": "Revert RETRY_COUNT to 10, disable circuit breaker"
}
```

---

### 3. Bad Deployment Configuration Regression
**ID**: `bad_deployment_config_regression`  
**Service**: `user-service`  
**Severity**: `CRITICAL`

**Incident**:
```
Immediate 100% HTTP 500 failure rate immediately following v3.0.0 deployment. All requests failing.
Logs: "FATAL: database authentication failed for user 'prod_user'" (repeated)
Deployment: user-service v3.0.0 deployed at 2026-10-27T09:00:00Z
Config: DB_USER=prod_user, DB_PASSWORD=old_password (stale)
```

**Expected Root Cause**:
> Bad deployment configuration: DB_PASSWORD not updated in deployment, using stale credentials

**Expected Remediation**:
```json
{
  "type": "CONFIGURATION_CHANGE",
  "exact_change": "DB_PASSWORD: old_password -> current_prod_password_2026",
  "expected_effect": "Restore database connectivity and eliminate authentication failures",
  "risk": "LOW",
  "blast_radius": "SANDBOX_ONLY",
  "rollback_plan": "Rollback to user-service v2.9.1 deployment artifact"
}
```

---

### 4. Cache Stampede
**ID**: `cache_stampede`  
**Service**: `catalog-api`  
**Severity**: `HIGH`

**Incident**:
```
Database CPU spike to 100% after hot cache key expiration. Query latency 5ms → 5000ms.
Logs: 234 concurrent requests rebuilding same cache key 'product_catalog_v2'
Config: CACHE_TTL=300, CACHE_BACKEND=redis
```

**Expected Root Cause**:
> Cache stampede (thundering herd) where 200+ concurrent requests simultaneously recomputed expired catalog cache key

**Expected Remediation**:
```json
{
  "type": "CODE_CHANGE",
  "exact_change": "Add mutex lock around cache rebuild: singleflight.Do(key, rebuild_fn) in catalog service",
  "expected_effect": "Only 1 request recomputes cache, others wait for result. Eliminates stampede.",
  "risk": "MEDIUM",
  "blast_radius": "SANDBOX_ONLY",
  "rollback_plan": "Revert catalog-api to v1.4.9 without singleflight"
}
```

---

### 5. Memory Leak
**ID**: `memory_leak`  
**Service**: `notification-api`  
**Severity**: `HIGH`

**Incident**:
```
Gradually increasing memory usage over 6 hours. Periodic 15-30s latency spikes. 3 OOM kills in last hour.
Logs: RSS 450MB → 920MB in 6h, GC pause 18.7s, health check timeout
Config: MEMORY_LIMIT=1024m, EVENT_BUFFER_SIZE=unbounded
```

**Expected Root Cause**:
> Application memory leak: unbounded EVENT_BUFFER_SIZE global list accumulating event objects without eviction

**Expected Remediation**:
```json
{
  "type": "CODE_CHANGE",
  "exact_change": "EVENT_BUFFER_SIZE: unbounded -> 10000 with TTL 300s, use functools.lru_cache or cachetools.LRUCache",
  "expected_effect": "Memory ceiling remains flat, GC pauses eliminated, no OOM kills",
  "risk": "MEDIUM",
  "blast_radius": "SANDBOX_ONLY",
  "rollback_plan": "Revert notification-api to v2.0.5 with original buffer implementation"
}
```

---

### 6. Database Saturation (Missing Index)
**ID**: `database_saturation`  
**Service**: `order-api`  
**Severity**: `CRITICAL`

**Incident**:
```
Database CPU at 100%, all queries timing out. Order creation latency >30s. Complete service degradation.
Logs: "query timeout (30s) SELECT * FROM orders WHERE user_id=? AND status=?"
pg_stat_statements: Seq Scan on orders (4.2M rows)
Config: DB_POOL_SIZE=50, WORK_MEM=4MB
```

**Expected Root Cause**:
> Database saturation: missing composite index on orders(user_id, status) causing sequential scans on 4.2M row table

**Expected Remediation**:
```json
{
  "type": "CODE_CHANGE",
  "exact_change": "CREATE INDEX CONCURRENTLY idx_orders_user_status ON orders(user_id, status) WHERE status IN ('pending', 'processing')",
  "expected_effect": "Query execution changes from Seq Scan to Index Scan, latency drops from 30s+ to <10ms",
  "risk": "LOW",
  "blast_radius": "SANDBOX_ONLY",
  "rollback_plan": "DROP INDEX CONCURRENTLY idx_orders_user_status"
}
```

---

## Running Demos

### Judge Mode (UI) - Recommended
```bash
# 1. Start services
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev

# 2. Open http://localhost:5173/judge
# 3. Select scenario (default: Payment Pool Exhaustion)
# 4. Click "RUN CANONICAL DEMO"
# 5. Watch real-time progress through all 8 phases
# 6. Review tabs: Overview, RAG, Graph, Hypotheses, Trace, Receipt
```

### CLI Demo
```bash
python scripts/run_demo.py

# Output:
# [INFO] COSKA Demo - Autonomous Incident Intelligence & Verified Recovery
# [OK] Backend API is running
# [OK] Nebius AI provider connected
# [INFO] Created incident: INC-A1B2C3D4
# [INFO] Starting COSKA investigation...
# ... real-time logs ...
# [RESULTS] INVESTIGATION RESULTS
# [VERIFIED] Verdict: VERIFIED
```

### Evaluation Harness (Regression Suite)
```bash
python scripts/evaluate_coska.py

# Runs 3 scenarios (8 checks each = 24 total)
# SCENARIO: Payment API Connection Pool Exhaustion
# [PASS] Investigation completed: Status: RESOLVED
# [PASS] Evidence coverage: 18 items (min: 10)
# [PASS] Hypotheses generation: 4 hypotheses (min: 3)
# [PASS] Root cause: Database connection pool exhaustion... (confidence: 92%)
# [PASS] Remediation: DB_POOL_SIZE: 5 -> 30
# [PASS] Verification: Verdict: VERIFIED (expected: VERIFIED)
# [PASS] Hypothesis quality: Supported: 2, Weakened: 0, Rejected: 2
# [PASS] Evidence diversity: Source types: CONFIG, DEPLOYMENT, LOG, REPOSITORY, WEB
# Passed: 8/8
# Overall: PASS

# All 3 scenarios: PASS
# Total: 24/24 checks passed
```

---

## Seeding Demo Data

```bash
# Seed all scenarios
python scripts/seed_demo_data.py seed-all

# Seed specific scenario
python scripts/seed_demo_data.py seed-scenario payment_pool_exhaustion

# List available scenarios
python scripts/seed_demo_data.py list

# Reset database (keep runbooks)
python scripts/seed_demo_data.py reset

# Export scenarios to JSON
python scripts/seed_demo_data.py export demo_scenarios_export.json

# Generate synthetic incidents (for load testing)
python scripts/seed_demo_data.py generate --count 50
```

---

## Judge Mode Walkthrough

### 1. Scenario Selection
```
┌─────────────────────────────────────────────────────────────┐
│  Select Canonical Evaluation Scenario                        │
│  [Payment Pool Exhaustion ▼]  [CRITICAL] payment-api        │
│  [Retry Storm]                  [CRITICAL] payment-gateway  │
│  [Bad Deployment Config]        [CRITICAL] user-service     │
│  [Cache Stampede]               [HIGH] catalog-api          │
│  [Memory Leak]                  [HIGH] notification-api     │
│  [DB Saturation]                [CRITICAL] order-api        │
└─────────────────────────────────────────────────────────────┘
```

### 2. Infra Status
```
AI Provider: MOCK (Deterministic Mock Provider)  ✓
Sandbox: local_safe                               ✓
Tavily: Offline Cached Research                   ✓
Verification: Deterministic Causal Verifier       ✓
```

### 3. Run Demo
```
[RUN CANONICAL DEMO]  →  Click to start

Progress Animation:
Incident → NLP → RAG → Planner → Evidence → Hypotheses → Root Cause → Remediation → Sandbox → Verification → VERIFIED
```

### 4. Results Tabs

#### Overview Tab
- Executive summary
- Verification matrix (4 stages)
- Root cause + confidence
- Remediation + risk
- Final verdict badge

#### RAG Tab
- Retrieved runbooks with relevance scores
- Match reasons ("tags match: pool, exhaustion")
- Source provenance
- Snippets with matched terms highlighted

#### Graph Tab
- Causal hierarchy: Incident → Evidence → Hypotheses → Root Cause → Remediation → Verification
- Evidence list per source type

#### Hypotheses Tab
- 4 competing hypotheses with confidence bars
- Status badges (SUPPORTED/WEAKENED/REJECTED)
- Supporting/contradicting evidence tags

#### Trace Tab
- 31-step agent execution log
- Timestamps, tools, duration, status
- Step-by-step visibility

#### Receipt Tab
- Full JSON verification receipt
- Copy to clipboard button
- All verification details

---

## Expected Outputs (Verification)

### Payment Pool Exhaustion - Expected Outputs

| Check | Expected |
|-------|----------|
| Investigation Status | RESOLVED |
| Evidence Count | ≥ 10 (typically 18) |
| Hypotheses Count | 4 |
| Root Cause | "Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)" |
| Root Cause Confidence | 92% |
| Supporting Evidence | E-1, E-2, E-3, E-4 (LOG + CONFIG) |
| Rejected Hypotheses | 3 (DB saturation, Network, Memory) |
| Remediation Exact Change | `DB_POOL_SIZE: 5 -> 30` |
| Remediation Risk | LOW |
| Verification Verdict | VERIFIED |
| Baseline Test | FAIL |
| Post-Fix Test | PASS |
| Health Check | PASS |
| Control Test | FAIL |

---

## Custom Scenario Creation

```python
# backend/app/services/demo_scenarios.py

from app.services.demo_scenarios import DemoScenario

CUSTOM_SCENARIO = DemoScenario(
    id="my_custom_scenario",
    name="My Custom Scenario",
    description="Description of the incident",
    category="custom_category",
    incident={
        "service": "my-service",
        "severity": "CRITICAL",
        "description": "Incident description...",
        "logs": "Log lines...",
        "deployment": "my-service v1.0.0 deployed at 2026-10-30T10:00:00Z",
        "repository": "https://github.com/org/repo",
        "metadata": {"configuration": "KEY=VALUE\nKEY2=VALUE2"}
    },
    expected_root_cause="Expected root cause description",
    expected_remediation={
        "type": "CONFIGURATION_CHANGE",
        "exact_change": "KEY: old -> new",
        "expected_effect": "Effect description",
        "risk": "LOW",
        "blast_radius": "SANDBOX_ONLY",
        "rollback_plan": "Rollback steps"
    },
    expected_verification={
        "baseline_test": "FAILED",
        "post_fix_tests": "PASSED",
        "health_check": "PASSED",
        "control_test": "FAILED",
        "verdict": "VERIFIED"
    },
    difficulty="medium",
    estimated_duration_seconds=30,
    tags=["custom", "tags"]
)

# Register
from app.services.demo_scenarios import ALL_SCENARIOS
ALL_SCENARIOS["my_custom_scenario"] = CUSTOM_SCENARIO
```

---

## Troubleshooting Demos

| Issue | Cause | Fix |
|-------|-------|-----|
| Demo hangs | Sandbox not available | Check Docker, fallback to local_safe |
| Verdict UNVERIFIED | Baseline test passed | Incident not reproducing - check config |
| Verdict FAILED | Post-fix test failed | Remediation not applied correctly |
| Evidence count low | Tools not executing | Check tool registry, tool allowlist |
| Hypotheses not generating | LLM provider issue | Check AI provider health |
| Judge Mode not loading | Frontend build issue | `npm run build`, check console |
| Evaluation fails | Scenario not seeded | Run `seed_demo_data.py seed-all` |

---

## CI/CD Integration

```yaml
# .github/workflows/demo.yml
name: Demo Validation

on: [push, pull_request]

jobs:
  demo:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      
      - name: Install deps
        run: |
          cd backend && pip install -r requirements.txt
      
      - name: Run evaluation harness
        run: python scripts/evaluate_coska.py
        # Must pass 24/24 checks
```

---

## Demo Checklist (Pre-Submission)

- [ ] All 6 scenarios seeded: `python scripts/seed_demo_data.py seed-all`
- [ ] Evaluation passes: `python scripts/evaluate_coska.py` → 24/24 PASS
- [ ] Judge Mode loads: `/judge` shows all 6 scenarios
- [ ] Canonical scenario works: Payment Pool Exhaustion → VERIFIED
- [ ] All tabs work: Overview, RAG, Graph, Hypotheses, Trace, Receipt
- [ ] Voice assistant works: "Investigate payment pool exhaustion"
- [ ] Voice states: LISTENING → THINKING → EXECUTING → COMPLETE
- [ ] Service map loads: 12 services, blast radius clickable
- [ ] Knowledge base searches: "pool exhaustion" returns runbook
- [ ] Verification receipt: Copy JSON works
- [ ] Architecture page loads: Diagram visible
- [ ] All 43 tests pass: `pytest -q`
- [ ] Frontend builds: `npm run build`
- [ ] Health checks pass: 8/8
- [ ] Security scan: No CRITICAL/SECRET in code