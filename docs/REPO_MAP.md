# Repository Map - COSKA

## Directory Structure

```
COSKA/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agent/          # Core agent engines
│   │   ├── api/            # REST endpoints
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic services
│   │   ├── tools/          # Tool registry & implementations
│   │   ├── config.py       # Configuration
│   │   └── main.py         # FastAPI app entry
│   ├── demo/               # Demo payment-api service
│   ├── tests/              # Test suite (43 tests)
│   └── requirements.txt
├── frontend/               # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/     # Layout, shared UI
│   │   ├── pages/          # Dashboard, Investigation, Judge, etc.
│   │   ├── services/       # API client, demo scenarios
│   │   ├── types/          # TypeScript types
│   │   └── App.tsx         # Routes
│   └── package.json
├── scripts/                # Operational scripts
├── docs/                   # Documentation
└── README.md
```

## Backend - Key Modules

### Agent Engines (`backend/app/agent/`)
| File | Purpose | Entry Point |
|------|---------|-------------|
| `orchestrator.py` | 8-phase investigation workflow | `Orchestrator.investigate()` |
| `evidence.py` | Log/config/deployment analysis | `EvidenceEngine.collect_evidence()` |
| `hypotheses.py` | Competing hypothesis generation | `HypothesisEngine.generate_initial_hypotheses()` |
| `root_cause.py` | Root cause analysis | `RootCauseEngine.identify_root_cause()` |
| `remediation.py` | Remediation generation | `RemediationEngine.generate_remediation_with_nemotron()` |
| `verifier.py` | 3-stage causal verification | `Verifier.verify()` |
| `timeline.py` | Timeline construction | `TimelineBuilder.build()` |

### API Endpoints (`backend/app/api/`)
| File | Purpose |
|------|---------|
| `incidents.py` | Incident CRUD, investigation trigger |
| `investigations.py` | Investigation state, evidence, hypotheses |
| `verification.py` | Verification results, receipts |
| `health.py` | Health checks (AI, Tavily, Sandbox) |
| `demo.py` | Demo scenarios, Judge Mode, RAG search |
| `enhanced.py` | Intelligence, RAG, Graph, Planner, Service Map |

### Services (`backend/app/services/`)
| File | Purpose |
|------|---------|
| `planner.py` | Agentic planner with GOAL→PLAN→EXECUTE loop |
| `rag.py` | BM25 offline RAG engine |
| `incident_intelligence.py` | NLP extraction from incidents |
| `evidence_graph.py` | Evidence relationship graph |
| `service_map.py` | Service topology & blast radius |
| `demo_scenarios.py` | 6 canonical demo scenarios |
| `providers.py` | AI provider abstraction (Mock, Nebius) |
| `storage.py` | SQLite persistence |
| `tavily.py` | Web research client |
| `nebius.py` | Nebius provider wrapper |
| `sandbox.py` | LocalSafe & Docker sandbox |

### Tools (`backend/app/tools/`)
| File | Purpose |
|------|---------|
| `registry.py` | Tool registry with validation |
| `investigation.py` | Inspect logs, config, deployment, runtime, repo, web search |
| `sandbox.py` | Sandbox execution tool |

### Models (`backend/app/models/__init__.py`)
Core Pydantic models: `Incident`, `Evidence`, `Hypothesis`, `Remediation`, `VerificationResult`, `AgentAction`, `IncidentStatus`, `SourceType`, `HypothesisStatus`, `Verdict`, `Severity`, `InvestigationPhase`, `RemediationType`

---

## Frontend - Key Modules

### Pages (`frontend/src/pages/`)
| File | Route | Purpose |
|------|-------|---------|
| `Dashboard.tsx` | `/` | Command center with KPIs, incidents, infra status |
| `IncidentDetail.tsx` | `/incidents/:id` | Incident shell with tabs |
| `Investigation.tsx` | `/incidents/:id` | Progress, status, next actions |
| `Evidence.tsx` | `/incidents/:id/evidence` | Evidence by source type |
| `EvidenceGraph.tsx` | `/incidents/:id/graph` | Causal graph visualization |
| `Hypotheses.tsx` | `/incidents/:id/hypotheses` | Competing hypotheses with confidence |
| `RootCause.tsx` | `/incidents/:id/root-cause` | Root cause with evidence chain |
| `Remediation.tsx` | `/incidents/:id/remediation` | Remediation plan, risk, rollback |
| `Verification.tsx` | `/incidents/:id/verification` | 3-stage verification, receipt |
| `IncidentIntelligence.tsx` | `/intelligence` | NLP incident analysis |
| `KnowledgeBase.tsx` | `/knowledge` | RAG runbook search |
| `ServiceMap.tsx` | `/services` | Service topology & blast radius |
| `Judge.tsx` | `/judge` | Judge Mode - canonical demo |
| `JudgeMode.tsx` | `/judge` | Legacy Judge Mode |
| `Architecture.tsx` | `/architecture` | Architecture diagram |
| `WhyCoska.tsx` | `/why` | Why COSKA page |

### Services (`frontend/src/services/`)
| File | Purpose |
|------|---------|
| `api.ts` | Axios client, all API endpoints |
| `demoScenarios.ts` | 6 canonical demo scenarios |

### Types (`frontend/src/types/incident.ts`)
TypeScript interfaces matching backend models.

---

## Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `run_demo.py` | End-to-end demo execution |
| `evaluate_coska.py` | 3-scenario evaluation harness (24 checks) |
| `healthcheck.py` | 8-system health check |
| `coska_doctor.py` | 11-point diagnostic |
| `security_check.py` | 6-phase security audit |
| `seed_demo_data.py` | Seed demo scenarios |
| `test_nebius.py` | Nebius integration test |
| `test_sandbox.py` | Sandbox test |

---

## Tests (`backend/tests/`)

| File | Tests |
|------|-------|
| `test_core.py` | 24 core tests (models, engines) |
| `test_advanced.py` | 15 advanced tests (verification, security, providers) |
| `test_rag_and_scenarios.py` | 4 RAG/scenario tests |
| `e2e/test_real_coska.py` | 1 E2E integration test |

---

## Demo Fixtures

| Path | Purpose |
|------|---------|
| `demo/incidents/payment-api-incident.json` | Canonical incident |
| `demo/payment-api/` | FastAPI demo service with .env |
| `backend/app/demo/scenarios.py` | Backend demo scenarios |
| `frontend/src/services/demoScenarios.ts` | Frontend demo scenarios |

---

## Configuration

| File | Purpose |
|------|---------|
| `backend/app/config.py` | Settings via Pydantic Settings |
| `frontend/vite.config.ts` | Vite config |
| `frontend/tsconfig.json` | TypeScript config |
| `.env` | Environment variables |

---

## Safe Modifications by Area

| Area | Safe Files | High-Risk Files |
|------|------------|-----------------|
| API | `backend/app/api/enhanced.py`, new files in `api/` | `incidents.py`, `investigations.py` |
| Agent | `backend/app/services/planner.py`, new agent files | `orchestrator.py`, `verifier.py` |
| RAG | `backend/app/services/rag.py` | Core retrieval logic |
| Storage | `backend/app/services/storage.py` (new methods) | Schema changes, migrations |
| Frontend | New pages in `pages/`, new components | `App.tsx`, `Layout.tsx`, `api.ts` |
| Tools | New tools in `tools/investigation.py` | `registry.py`, `sandbox.py` |
| Models | Extend models in `models/__init__.py` | Core model structure |

---

## Test Commands

```bash
# All tests
python -m pytest -q

# Specific test file
python -m pytest tests/test_core.py -v

# Frontend TypeScript
cd frontend && npx tsc --noEmit

# Frontend build
cd frontend && npm run build

# Health check
python scripts/healthcheck.py

# Doctor
python scripts/coska_doctor.py

# Security
python scripts/security_check.py

# Evaluation
python scripts/evaluate_coska.py
```