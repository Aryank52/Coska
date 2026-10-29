# COSKA Demo Guide

## Overview

This guide walks through running the COSKA demo with the Payment API, a deliberately flawed service that demonstrates the complete investigation → verification workflow.

## Demo Components

### Payment API (Demo Target)

**Stack:** FastAPI + SQLite + SQLAlchemy
**Intentional Fault:** `DB_POOL_SIZE=5` (severely undersized for concurrent load)

**Behavior Under Load:**
- Normal: ~1-2% HTTP 500 error rate
- Under load (100 requests, 20 concurrent): ~30-40% HTTP 500 errors
- Errors: "connection pool exhausted", "timeout waiting for database connection"

### Incident Scenario

```json
{
  "service": "payment-api",
  "severity": "CRITICAL",
  "description": "HTTP 500 error rate increased from 1.2% to 38%. Users experiencing payment failures.",
  "logs": "17 database timeout events in 90 seconds...",
  "deployment": "payment-api v1.8.2 deployed at 2026-10-29T10:10:00Z",
  "repository": "https://github.com/coska/payment-api",
  "metadata": {
    "configuration": "DB_POOL_SIZE=5\nDB_POOL_TIMEOUT=5"
  }
}
```

## Quick Start

### 1. Start Payment API (Target System)
```bash
cd demo/payment-api
pip install -r requirements.txt
cp .env.example .env  # Has DB_POOL_SIZE=5
uvicorn app.main:app --port 8001 --reload
```

Verify it's running:
```bash
curl http://localhost:8001/health
# {"status":"healthy","database":"connected","pool_size":5}
```

### 2. Generate Load (Trigger Incident)
```bash
cd demo/scripts
python run_load_test.py
# Or use the API directly:
curl -X POST http://localhost:8001/load-test \
  -H "Content-Type: application/json" \
  -d '{"requests": 100, "concurrency": 20}'
```

Expected output:
```json
{
  "total_requests": 100,
  "concurrency": 20,
  "results": {"200": 67, "500": 33},
  "error_rate": 0.33
}
```

### 3. Start COSKA Backend
```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env  # Add your NEBIUS_API_KEY and TAVILY_API_KEY
uvicorn app.main:app --reload --port 8000
```

Verify AI health:
```bash
curl http://localhost:8000/api/health/ai
```

### 4. Start COSKA Frontend
```bash
cd frontend
npm install
npm run dev
# Opens http://localhost:5173
```

### 5. Create Incident in COSKA

**Option A: Via API**
```bash
curl -X POST http://localhost:8000/api/incidents \
  -H "Content-Type: application/json" \
  -d @demo/incidents/payment-api-incident.json
```

**Option B: Via Frontend**
1. Open http://localhost:5173
2. Click "Create Incident" (if implemented) or use API
3. Incident appears in dashboard

### 6. Run Investigation
```bash
# Get incident ID from step 5 (e.g., INC-A1B2C3D4)
curl -X POST http://localhost:8000/api/incidents/INC-A1B2C3D4/investigate \
  -H "Content-Type: application/json" \
  -d '{"auto_approve": true}'
```

Or in Frontend:
1. Click on the incident in Dashboard
2. Click "Start Investigation"
3. Watch the agent activity timeline update in real-time

## Expected Investigation Flow

### Phase 1: Evidence Collection (10-15s)
- Log analysis: 17 pool exhaustion events found
- Config inspection: `DB_POOL_SIZE=5` identified
- Deployment: v1.8.2 deployed before incident

### Phase 2: Timeline (5s)
- Last healthy: pre-deployment
- Deployment: v1.8.2 at 10:10
- First anomaly: pool exhaustion at 10:15
- Escalation: HTTP 500 spike

### Phase 3: Hypotheses (10-20s)
| Hypothesis | Confidence | Status |
|------------|------------|--------|
| DB connection pool exhaustion | 91% | SUPPORTED |
| Database server saturation | 5% | REJECTED |
| Network instability | 3% | REJECTED |
| Memory pressure | 1% | REJECTED |

### Phase 4: Root Cause (15-30s)
**Root Cause:** "Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)"

**Supporting Evidence:** E-001 (log timeouts), E-002 (config pool=5), E-003 (deployment timing)

### Phase 5: Remediation (10s)
**Fix:** `DB_POOL_SIZE: 5 → 30`
**Risk:** LOW
**Blast Radius:** SANDBOX_ONLY
**Rollback:** Restore DB_POOL_SIZE=5

### Phase 6: Verification (30-60s)
| Stage | Action | Expected |
|-------|--------|----------|
| BASELINE | Run tests with pool=5 | FAIL |
| POST-FIX | Apply pool=30, run tests | PASS |
| HEALTH | Service health check | PASS |
| CONTROL | Revert to pool=5, run tests | FAIL |

**Final Verdict:** VERIFIED ✅

## Frontend Walkthrough

### Dashboard
- Active incidents count
- Critical severity badge
- Investigation in progress indicator
- Resolved today counter

### Investigation Tab
- Progress bar through 11 phases
- Real-time agent activity timeline
- Incident timeline visualization
- Current phase highlight

### Evidence Tab
- Grouped by source: LOG, CONFIG, DEPLOYMENT, WEB
- Each item: source icon, claim, confidence, reference
- Expandable raw data

### Hypotheses Tab
- Ranked by confidence (highest first)
- Color-coded status badges
- Supporting/contradicting evidence tags
- Next investigation action

### Root Cause Tab
- Large root cause statement
- Confidence percentage
- Supporting evidence list
- Rejected hypotheses with reasons
- Recommended remediation preview

### Remediation Tab
- Exact change in monospace
- Risk level badge
- Expected effect description
- Rollback plan in code block
- "Apply to Sandbox" button

### Verification Tab (Strongest Visual)
- Four-stage grid: BASELINE, POST-FIX, HEALTH, CONTROL
- Large PASS/FAIL labels with color coding
- Final verdict banner: **VERIFIED** in green
- "COSKA proved the recovery" tagline
- Downloadable JSON receipt

## Verification Receipt

```json
{
  "incident_id": "INC-A1B2C3D4",
  "service": "payment-api",
  "root_cause": "Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)",
  "remediation": "Increase DB_POOL_SIZE from 5 to 30",
  "baseline_test": "FAILED",
  "post_fix_tests": "PASSED",
  "health_check": "PASSED",
  "control_test": "FAILED_WITHOUT_FIX",
  "verdict": "VERIFIED",
  "evidence_count": 8,
  "model": "nvidia/nemotron-3-ultra-550b-a55b",
  "timestamp": "2026-10-29T..."
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Payment API health check fails | Check SQLite file permissions |
| Load test returns 0 errors | Increase concurrency to 50+ |
| COSKA investigation stalls | Check Nebius API key and quota |
| Tavily searches fail | Verify TAVILY_API_KEY |
| Sandbox tests fail | Ensure Docker is running |
| Frontend shows "Network Error" | Check backend CORS and port 8000 |

## Demo Script (3 Minutes)

| Time | Action |
|------|--------|
| 0:00 | Show Dashboard, explain COSKA |
| 0:15 | Create incident (or show pre-created) |
| 0:25 | Click "Start Investigation" |
| 0:40 | Evidence tab: logs + config appear |
| 0:55 | Tavily research completes |
| 1:10 | Hypotheses tab: 4 competing explanations |
| 1:25 | Root Cause tab: pool exhaustion identified |
| 1:40 | Remediation tab: `DB_POOL_SIZE: 5 → 30` |
| 1:55 | Click "Apply to Sandbox" |
| 2:10 | Tests executing in sandbox |
| 2:25 | Health check passes |
| 2:35 | Control test: revert → failure returns |
| 2:45 | **VERIFIED** banner appears |
| 2:55 | Show: Nemotron 3 Ultra, Nebius, Tavily badges |
| 3:00 | "Investigate. Resolve. Verify." |