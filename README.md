# COSKA

**Autonomous Incident Intelligence & Verified Recovery**

> INVESTIGATE. RESOLVE. VERIFY.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61dafb.svg)](https://react.dev/)

---

## Problem

When software or infrastructure fails, engineers typically investigate manually across logs, source code, configuration, deployments, databases, runtime signals, documentation, web search, tests, and metrics. This process is fragmented, slow, and error-prone.

## Solution

COSKA turns incident investigation into one autonomous, evidence-driven workflow:

```
INCIDENT → EVIDENCE → HYPOTHESES → INVESTIGATION → ROOT CAUSE
                                                    ↓
                              SANDBOX EXECUTION ← REMEDIATION
                                                    ↓
                                    TEST → HEALTH CHECK → VERIFICATION
                                                    ↓
                                            VERIFIED RECEIPT
```

COSKA does not merely diagnose an incident. **COSKA investigates the evidence, proposes a recovery, safely tests the recovery, and verifies whether the recovery actually worked.**

---

## Why COSKA

| Traditional Approach | COSKA |
|---------------------|-------|
| Manual log grep | Automated log analysis |
| Single hypothesis | Competing hypotheses |
| "Likely cause is X" | Evidence-backed root cause |
| Deploy fix to prod | Sandbox-only execution |
| Hope it works | **Verified recovery** |

---

## Core Workflow

1. **RECEIVE INCIDENT** — Ingest incident with logs, deployment info, service context
2. **TRIAGE** — Classify severity, extract key signals
3. **COLLECT EVIDENCE** — Structured extraction from logs, repo, config, deployments
4. **BUILD TIMELINE** — Last healthy → deployment → first anomaly → escalation → now
5. **GENERATE HYPOTHESES** — Multiple competing explanations with confidence scores
6. **INVESTIGATE** — Tool-driven inspection of logs, repository, configuration, runtime
7. **RESEARCH EXTERNAL** — Tavily-powered web search for technical documentation
8. **IDENTIFY ROOT CAUSE** — Nemotron 3 Ultra reasons over all evidence
9. **GENERATE REMEDIATION** — Concrete, validated fix with risk assessment
10. **APPLY IN SANDBOX** — Isolated Docker execution, no production access
11. **RUN TESTS** — Targeted + regression tests
12. **HEALTH CHECKS** — Service health validation
13. **CONTROLLED VERIFICATION** — Revert fix, prove failure returns
14. **VERIFICATION RECEIPT** — Auditable JSON report with VERIFIED/FAILED/UNVERIFIED verdict

---

## Features

- **Autonomous Investigation** — Multi-step agentic workflow with explicit state machine
- **Evidence Engine** — Structured, traceable evidence with source types (LOG, REPO, CONFIG, DEPLOY, WEB, TEST)
- **Hypothesis Engine** — Competing explanations with supporting/contradicting evidence
- **Verified Recovery** — Three-stage verification: baseline fail → post-fix pass → control fail
- **Sandbox Safety** — Docker-isolated execution, allowlisted commands, no production credentials
- **NVIDIA Nemotron 3 Ultra** — Deep reasoning for root cause, remediation, verification
- **Nebius Token Factory** — Production-grade model inference endpoint
- **Tavily Integration** — Real-time technical web research as evidence
- **Professional Command Center** — React-based UI: Dashboard, Investigation, Evidence, Hypotheses, Root Cause, Remediation, Verification

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
│  Dashboard │ Investigation │ Evidence │ Hypotheses │ Verification│
└─────────────────────────┬───────────────────────────────────────┘
                          │ REST API
┌─────────────────────────▼───────────────────────────────────────┐
│                      BACKEND (FastAPI)                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │ Incident │ │Evidence  │ │Hypothesis│ │Remediation│          │
│  │   API    │ │ Engine   │ │ Engine   │ │ Engine   │           │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │
│       │            │            │            │                  │
│  ┌────▼────────────▼────────────▼────────────▼─────┐           │
│  │              AGENT ORCHESTRATOR                  │           │
│  │  Planner → Investigator → RootCause → Verifier  │           │
│  └────┬──────────────────────┬────────────────────┘           │
│       │                      │                                 │
│  ┌────▼──────┐          ┌────▼──────┐                          │
│  │ NEBIUS    │          │  TAVILY   │                          │
│  │ Nemotron  │          │  Search   │                          │
│  │ 3 Ultra   │          │           │                          │
│  └───────────┘          └───────────┘                          │
│       │                      │                                 │
│  ┌────▼──────────────────────▼──────┐                          │
│  │       SANDBOX (Docker)           │                          │
│  │  Apply Fix → Test → Verify       │                          │
│  └──────────────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## NVIDIA Nemotron Integration

COSKA uses **NVIDIA Nemotron 3 Ultra 550B-A55B** (`nvidia/nemotron-3-ultra-550b-a55b`) as its primary reasoning model for:

- Incident reasoning & evidence synthesis
- Hypothesis generation & investigation planning
- Root cause identification
- Remediation planning
- Final verification reasoning
- Incident report generation

Nemotron 3 Ultra is specifically suited for long-context reasoning, tool calling, and multi-agent workflows.

```python
# Example usage via Nebius Token Factory
from openai import OpenAI

client = OpenAI(
    base_url="https://api.tokenfactory.us-central1.nebius.com/v1/",
    api_key=os.getenv("NEBIUS_API_KEY")
)

response = client.chat.completions.create(
    model="nvidia/nemotron-3-ultra-550b-a55b",
    messages=[{"role": "user", "content": "Analyze this incident..."}],
    tools=coska_tools
)
```

---

## Nebius Token Factory Integration

COSKA connects to **Nebius Token Factory** for model inference:

- **Endpoint**: `https://api.tokenfactory.us-central1.nebius.com/v1/`
- **Authentication**: API key via `NEBIUS_API_KEY`
- **Model**: `nvidia/nemotron-3-ultra-550b-a55b`
- **Compatibility**: OpenAI-compatible API

---

## Tavily Integration

COSKA integrates **Tavily** as a runtime research tool for:

- Official technical documentation
- Known error patterns
- Framework behavior
- Database configuration guidance
- Recent technical information

```python
# Example Tavily search
from tavily import TavilyClient

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
results = tavily.search("PostgreSQL connection pool exhaustion", max_results=5)
```

---

## Evidence Engine

Every meaningful evidence item has:

- `id` — Unique identifier (E-001, E-002, ...)
- `source_type` — LOG, REPOSITORY, CONFIG, DEPLOYMENT, RUNTIME, WEB, TEST
- `claim` — Structured finding
- `reference` — Source location
- `timestamp` — When collected
- `confidence` — Model-assessed confidence
- `related_component` — Affected system component

**The final root cause must be traceable to evidence.**

---

## Verification Engine

Three-stage verification ensuring causal validation:

| Stage | Action | Expected |
|-------|--------|----------|
| **BASELINE** | Reproduce incident | FAIL |
| **POST-FIX** | Apply remediation, run tests | PASS |
| **CONTROL** | Revert fix, re-run | FAIL |

**Only if all three stages align → VERIFIED**

---

## Sandbox Safety

- **Isolated Docker containers** — No host access
- **Allowlisted commands** — No arbitrary shell execution
- **Timeout enforcement** — Prevents runaway processes
- **No production credentials** — Sandbox has zero prod access
- **Rollback capability** — Before/after state capture
- **Audit logging** — Every action recorded

---

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker (for sandbox)
- Nebius Token Factory API key
- Tavily API key

### Installation

```bash
# Clone repository
git clone <repository-url>
cd coska

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Environment configuration
cp ../.env.example ../.env
# Edit .env with your API keys
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AI_PROVIDER` | No | `mock` (default for local development), `nebius`, or `auto` |
| `NEBIUS_API_KEY` | Conditional | Nebius Token Factory API key (required when `AI_PROVIDER=nebius`) |
| `NEBIUS_BASE_URL` | No | `https://api.tokenfactory.us-central1.nebius.com/v1/` |
| `NEBIUS_MODEL` | No | `nvidia/nemotron-3-ultra-550b-a55b` |
| `TAVILY_API_KEY` | No | Tavily API key for real-time web research (gracefully degrades if absent) |
| `SANDBOX_MODE` | No | `local` (safe local isolation), `docker`, or `auto` (default) |
| `DATABASE_URL` | No | SQLite default: `sqlite:///./coska.db` |
| `MAX_AGENT_STEPS` | No | Safety bound on steps (default: 20) |
| `MAX_TOOL_CALLS` | No | Safety bound on tool calls (default: 15) |
| `MAX_RETRIES` | No | Safety bound on retries (default: 2) |
| `MAX_INVESTIGATION_TIME` | No | Safety bound on investigation seconds (default: 180) |
| `APP_ENV` | No | `development` or `production` |
| `LOG_LEVEL` | No | `INFO` or `DEBUG` |

---

## Local Development

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: Demo payment-api (optional)
cd demo/payment-api
docker-compose up
```

Access:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## Demo

COSKA includes a deterministic demo application: **payment-api** (FastAPI + PostgreSQL)

### Intentional Fault

```env
DB_POOL_SIZE=5  # Undersized for load
```

### Incident Scenario

```
Service: payment-api
Severity: CRITICAL
Description: HTTP 500 error rate increased from 1.2% to 38%
Logs: "connection pool exhausted", "timeout waiting for database connection"
Recent deployment: payment-api v1.8.2
```

### Expected COSKA Flow

1. Investigates deployment → configuration → `DB_POOL_SIZE=5`
2. Identifies root cause: **Database connection pool exhaustion**
3. Proposes remediation: `DB_POOL_SIZE: 5 → 30`
4. Applies in sandbox, runs tests, health checks
5. Control verification: reverts fix, failure returns
6. **VERDICT: VERIFIED**

Run demo:
```bash
cd demo/scripts
python run_demo.py
```

---

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# E2E demo test
cd demo/scripts
python test_demo.py
```

---

## Deployment

### Docker Compose (Recommended)

```bash
docker-compose up -d
```

### Nebius Serverless (Optional)

Deploy backend to Nebius Serverless Endpoint for production inference.

---

## Security

- Environment-based secrets (`.env` ignored by Git)
- Backend-only API keys (never exposed to browser)
- Command allowlist for sandbox execution
- Execution timeouts
- Audit logging
- Model output validation
- No unrestricted shell access

See [SECURITY.md](docs/SECURITY.md) for details.

---

## Limitations

- Requires Nebius Token Factory access for Nemotron 3 Ultra
- Requires Tavily API key for web research
- Docker required for sandbox verification
- Demo scenario is deterministic; real incidents vary in complexity
- Model routing (Nemotron Nano/Super/Ultra) not yet implemented

---

## Future Roadmap

- [ ] Model routing (Nemotron Nano/Super/Ultra)
- [ ] Incident memory with similarity search
- [ ] Evidence graph visualization
- [ ] Patch/diff viewer
- [ ] Cost & latency dashboards
- [ ] Multiple incident scenarios
- [ ] Asynchronous job processing
- [ ] Report export (PDF, Markdown)

---

## Hackathon Track

**Nebius x NVIDIA Global AI Hackathon 2026**  
**Track**: Best Apps and Agents

COSKA demonstrates:
- ✅ Nebius Token Factory integration
- ✅ NVIDIA Nemotron 3 Ultra as central model
- ✅ Meaningful multi-step agentic behavior
- ✅ Tavily as runtime research tool
- ✅ Sandbox execution with verification
- ✅ Working demo with deterministic scenario
- ✅ Public-ready repository with MIT license

---

## License

MIT License — see [LICENSE](LICENSE)

---

**COSKA — Autonomous Incident Intelligence & Verified Recovery**

*Investigate. Resolve. Verify.*