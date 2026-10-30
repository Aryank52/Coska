# COSKA Architecture

## Overview

COSKA (Autonomous Incident Intelligence & Verified Recovery) is a multi-component system that transforms incident investigation into an autonomous, evidence-driven workflow with verified recovery.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + TypeScript)                   │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐  │
│  │  Dashboard  │ │ Investigation│ │ Evidence │ │Hypotheses │ │Root Cause │  │
│  └─────────────┘ └──────────────┘ └──────────┘ └───────────┘ └───────────┘  │
│  ┌─────────────┐ ┌──────────────┐                                           │
│  │ Remediation │ │ Verification │                                           │
│  └─────────────┘ └──────────────┘                                           │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ REST API / WebSocket
┌─────────────────────────────────▼───────────────────────────────────────────┐
│                           BACKEND (FastAPI + Python)                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                        AGENT ORCHESTRATOR                                │ │
│  │  ┌──────────┐ ┌──────────────┐ ┌────────────┐ ┌──────────┐ ┌────────┐  │ │
│  │  │ Planner  │ │ Investigator │ │Root Cause  │ │Remediat'n│ │Verifier│  │ │
│  │  └──────────┘ └──────────────┘ └────────────┘ └──────────┘ └────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Evidence │ │Hypothesis│ │Timeline  │ │Remediat'n│ │Sandbox   │          │
│  │ Engine   │ │ Engine   │ │ Builder  │ │ Engine   │ │ Engine   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────────────────┐ ┌──────────────────────┐ ┌────────────────────┐  │
│  │     NEBIUS SERVICE   │ │      TAVILY SERVICE  │ │   STORAGE SERVICE  │  │
│  │  (Nemotron 3 Ultra)  │ │   (Web Research)     │ │    (SQLite)        │  │
│  └──────────────────────┘ └──────────────────────┘ └────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
            ┌───────────────┐           ┌───────────────┐
            │  SANDBOX      │           │  DEMO APP     │
            │  (Docker)     │           │  (Payment API)│
            └───────────────┘           └───────────────┘
```

## Component Details

### Frontend (React 18 + TypeScript + Vite)

**Pages:**
- **Dashboard** - Overview of active/critical/resolved incidents
- **Investigation** - Main incident view with progress tracking
- **Evidence** - Structured evidence grouped by source type
- **Hypotheses** - Competing hypotheses with confidence scores
- **Root Cause** - Evidence-backed root cause analysis
- **Remediation** - Fix proposal with risk assessment
- **Verification** - Three-stage verification results

**Design System:**
- Dark command-center aesthetic
- JetBrains Mono for technical data
- Inter for UI text
- Status colors: Critical (red), High (amber), Medium (blue), Low (green), Verified (green)

### Backend (FastAPI + Python 3.12)

**Core Modules:**

1. **Agent Orchestrator** (`app/agent/orchestrator.py`)
   - Coordinates the 8-phase investigation workflow
   - Manages investigation state per incident
   - Records all agent actions for audit trail

2. **Evidence Engine** (`app/agent/evidence.py`)
   - `LogAnalyzer` - Deterministic log pattern extraction
   - `ConfigAnalyzer` - Configuration parameter extraction
   - `DeploymentAnalyzer` - Deployment metadata extraction
   - Produces structured `Evidence` objects with source types

3. **Timeline Builder** (`app/agent/timeline.py`)
   - Constructs chronological incident timeline
   - Events: Deployment → Config Change → First Anomaly → Escalation → Current

4. **Hypothesis Engine** (`app/agent/hypotheses.py`)
   - Template-based initial hypothesis generation
   - Nemotron refinement for competing explanations
   - Evidence-based confidence updating

5. **Root Cause Engine** (`app/agent/root_cause.py`)
   - Nemotron 3 Ultra reasoning over all evidence
   - Structured output: root cause, confidence, supporting/contradicting evidence
   - Rejected hypotheses with reasoning

6. **Remediation Engine** (`app/agent/remediation.py`)
   - Nemotron-generated specific, reversible fixes
   - Validation against allowlisted configuration keys
   - Risk assessment and rollback planning

6. **Sandbox Engine** (`app/tools/sandbox.py`)
   - Dual-mode architecture via `SandboxProvider` ABC:
     - `DockerSandboxProvider` - Isolated container execution, memory/CPU quotas, bridge network, automatic container cleanup.
     - `LocalSafeSandboxProvider` - Deterministic host fallback (Windows/macOS/Linux) with strict path traversal prevention, command allowlisting, environment credential sanitization, timeout enforcement, and automatic file rollback.
   - Truthful reporting: accurately reports `docker` or `local_safe` without mislabeling local execution.

7. **Verifier** (`app/agent/verifier.py`)
   - Three-stage causal verification: Baseline → Post-Fix → Control
   - Exact Deterministic Verdict Matrix:
     - Baseline FAIL + Post-Fix PASS + Health PASS + Control FAIL → `VERIFIED`
     - Baseline FAIL + Post-Fix FAIL → `FAILED`
     - Baseline FAIL + Post-Fix PASS + Control PASS (inconclusive fix) → `UNVERIFIED`
     - Missing Baseline / No reproduce → `INSUFFICIENT_EVIDENCE`

8. **AI Provider Abstraction** (`app/services/providers.py`)
   - `MockAIProvider` - Deterministic mock provider producing typed schemas for all 8 phases.
   - `NebiusTokenFactoryProvider` - Production-ready client for NVIDIA Nemotron 3 Ultra (`nvidia/nemotron-3-ultra-550b-a55b`) via Nebius Token Factory with bounded exponential-backoff 429 retries.
   - Centralized error states: `PROVIDER_NOT_CONFIGURED`, `PROVIDER_UNAUTHORIZED`, `PROVIDER_RATE_LIMITED`, `PROVIDER_UNAVAILABLE`, `MODEL_UNAVAILABLE`, `PROVIDER_INVALID_RESPONSE`.

9. **Services & Persistence**
   - `TavilyClient` (`app/services/tavily.py`) - Real-time technical web research with graceful fallback if unconfigured.
   - `StorageService` (`app/services/storage.py`) - SQLite persistence with dedicated schemas for `incidents`, `evidence`, `hypotheses`, `remediations`, `verification_results`, `agent_actions`, `investigations`, and `incident_memory`.

**API Endpoints:**
- `GET /api/health` - Basic health
- `GET /api/health/ai` - AI provider health
- `POST /api/incidents` - Create incident
- `GET /api/incidents` - List incidents
- `GET /api/incidents/{id}` - Get incident
- `POST /api/incidents/{id}/investigate` - Start investigation
- `GET /api/incidents/{id}/timeline` - Get timeline
- `GET /api/incidents/{id}/evidence` - Get evidence
- `GET /api/incidents/{id}/hypotheses` - Get hypotheses
- `GET /api/incidents/{id}/root-cause` - Get root cause
- `GET /api/incidents/{id}/remediation` - Get remediation
- `POST /api/incidents/{id}/apply-fix` - Apply fix & verify
- `POST /api/incidents/{id}/verify` - Run verification
- `GET /api/incidents/{id}/report` - Verification report

### AI Model Integration

**NVIDIA Nemotron 3 Ultra 550B-A55B**
- Endpoint: Nebius Token Factory (`https://api.tokenfactory.us-central1.nebius.com/v1/`)
- Model ID: `nvidia/nemotron-3-ultra-550b-a55b`
- Used for: Root cause reasoning, hypothesis generation, remediation planning, verification reasoning
- Temperature: 0.1 (deterministic reasoning)
- Max tokens: 4096

**Tavily Search**
- Real-time technical web research
- Queries: Error patterns, configuration guidance, documentation
- Results converted to WEB-type evidence

### Data Flow

```
Incident Input
      │
      ▼
┌─────────────┐
│  TRIAGE     │ ──► Severity classification, initial signal extraction
└─────────────┘
      │
      ▼
┌─────────────┐
│ COLLECT     │ ──► Logs, Config, Deployment, Repository, Runtime
│  EVIDENCE   │
└─────────────┘
      │
      ▼
┌─────────────┐
│  BUILD      │ ──► Last Healthy → Deployment → First Anomaly → Escalation
│  TIMELINE   │
└─────────────┘
      │
      ▼
┌─────────────┐
│  GENERATE   │ ──► Template-based + Nemotron refinement
│ HYPOTHESES  │     3-5 competing explanations
└─────────────┘
      │
      ▼
┌─────────────┐
│ INVESTIGATE │ ──► Tool-driven: inspect_logs, inspect_config, search_web
│             │     Updates hypotheses with new evidence
└─────────────┘
      │
      ▼
┌─────────────┐
│  RESEARCH   │ ──► Tavily searches for external technical validation
│  EXTERNAL   │
└─────────────┘
      │
      ▼
┌─────────────┐
│  ROOT CAUSE │ ──► Nemotron reasons over ALL evidence
│  IDENTIFIED │     Single strongest explanation with traceability
└─────────────┘
      │
      ▼
┌─────────────┐
│ REMEDIATION │ ──► Specific, validated, reversible fix
│  PROPOSED   │     Risk assessment + rollback plan
└─────────────┘
      │
      ▼
┌─────────────┐
│   SANDBOX   │ ──► Docker: Apply fix → Run tests → Health check
│  EXECUTION  │
└─────────────┘
      │
      ▼
┌─────────────┐
│ VERIFICATION│ ──► Stage 1: Baseline (FAIL)
│  (3-STAGE)  │     Stage 2: Post-Fix (PASS)
└─────────────┘     Stage 3: Control (FAIL without fix)
      │                Verdict: VERIFIED only if all align
      ▼
┌─────────────┐
│  RECEIPT    │ ──► Auditable JSON report with verdict
└─────────────┘
```

### Security Model

- **Secrets**: Environment variables only (`.env` gitignored)
- **API Keys**: Backend-only, never exposed to frontend
- **Sandbox**: Docker isolation, no host access, no production credentials
- **Commands**: Allowlisted only, no arbitrary shell execution
- **Validation**: All model outputs validated before execution
- **Audit**: Every action logged with timestamp, tool, result

### Deployment

**Development:**
```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend  
cd frontend && npm run dev

# Demo app
cd demo/payment-api && uvicorn app.main:app --port 8001
```

**Production (Docker Compose):**
```bash
docker-compose up -d
```

**Nebius Serverless** (Optional):
- Backend deployed as Nebius Serverless Endpoint
- Jobs for async verification/report generation

## Data Models

Key entities: `Incident`, `Evidence`, `Hypothesis`, `Remediation`, `VerificationResult`, `AgentAction`, `IncidentMemory`

All stored in SQLite with JSON columns for flexible metadata.

## Demo Application

**Payment API** (FastAPI + SQLite)
- Intentional fault: `DB_POOL_SIZE=5` (undersized)
- Load test generates connection pool exhaustion
- HTTP 500 error rate increases from ~1% to ~38%
- COSKA identifies root cause, proposes `DB_POOL_SIZE: 5 → 30`
- Verification proves causal relationship