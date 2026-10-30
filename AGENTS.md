# AGENTS.md - COSKA Agent Context

## PROJECT
**COSKA** — Autonomous Incident Intelligence & Verified Recovery

## PURPOSE
Autonomous incident investigation + safe remediation + deterministic causal verification.

## CORE PRINCIPLE
```
LLM REASONS
TOOLS ACT
VERIFIER DECIDES
```

## REPOSITORY MAP
```
COSKA/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agent/          # Core agent engines
│   │   │   ├── orchestrator.py      # 8-phase investigation workflow
│   │   │   ├── evidence.py          # Log/config/deployment analysis
│   │   │   ├── hypotheses.py        # Competing hypothesis generation
│   │   │   ├── root_cause.py        # Root cause analysis
│   │   │   ├── remediation.py       # Remediation generation
│   │   │   ├── verifier.py          # 3-stage causal verification
│   │   │   └── timeline.py          # Timeline construction
│   │   ├── api/            # REST endpoints
│   │   │   ├── incidents.py         # Incident CRUD
│   │   │   ├── investigations.py    # Investigation control
│   │   │   ├── verification.py      # Verification results
│   │   │   ├── health.py            # Health checks
│   │   │   ├── demo.py              # Demo/Judge mode
│   │   │   └── enhanced.py          # Enhanced API endpoints
│   │   ├── models/         # Pydantic models
│   │   │   └── __init__.py          # Incident, Evidence, Hypothesis, etc.
│   │   ├── services/       # Business logic services
│   │   │   ├── planner.py           # Agentic planner
│   │   │   ├── rag.py               # BM25 RAG engine
│   │   │   ├── incident_intelligence.py # NLP extraction
│   │   │   ├── evidence_graph.py    # Evidence relationships
│   │   │   ├── service_map.py       # Service topology
│   │   │   ├── demo_scenarios.py    # 6 canonical scenarios
│   │   │   ├── providers.py         # AI provider abstraction
│   │   │   ├── storage.py           # SQLite persistence
│   │   │   ├── tavily.py            # Web research
│   │   │   ├── nebius.py            # Nebius provider
│   │   │   └── sandbox.py           # Execution sandbox
│   │   ├── tools/          # Tool registry & implementations
│   │   │   ├── registry.py          # Tool registry
│   │   │   ├── investigation.py     # Inspect tools
│   │   │   └── sandbox.py           # Sandbox tool
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
│   ├── run_demo.py         # End-to-end demo
│   ├── evaluate_coska.py   # Evaluation harness
│   ├── healthcheck.py      # System health
│   ├── coska_doctor.py     # Diagnostics
│   ├── security_check.py   # Security audit
│   └── seed_demo_data.py   # Seed demo data
├── docs/                   # Documentation
└── README.md
```

## KEY FILES FOR AGENTS
| Task | Files to Read |
|------|--------------|
| Incident flow | `backend/app/agent/orchestrator.py` |
| Evidence | `backend/app/agent/evidence.py` |
| Hypotheses | `backend/app/agent/hypotheses.py` |
| Root cause | `backend/app/agent/root_cause.py` |
| Verification | `backend/app/agent/verifier.py` |
| Planner | `backend/app/services/planner.py` |
| RAG | `backend/app/services/rag.py` |
| Providers | `backend/app/services/providers.py` |
| Storage | `backend/app/services/storage.py` |
| Demo | `backend/app/services/demo_scenarios.py` |
| API | `backend/app/api/` |
| Frontend | `frontend/src/pages/`, `frontend/src/services/api.ts` |

## SAFE MODIFICATIONS
- Add new API endpoints in `backend/app/api/`
- Add new services in `backend/app/services/`
- Add new pages in `frontend/src/pages/`
- Add new tools in `backend/app/tools/`
- Extend models in `backend/app/models/__init__.py`

## HIGH-RISK FILES (Require Care)
- `backend/app/agent/orchestrator.py` - Core workflow
- `backend/app/agent/verifier.py` - Causal verification logic
- `backend/app/services/providers.py` - AI provider abstraction
- `backend/app/services/storage.py` - Database operations
- `backend/app/tools/sandbox.py` - Code execution

## TESTS
- Run: `python -m pytest -q` (43 tests)
- Evaluation: `python scripts/evaluate_coska.py` (24 checks)

## COMMANDS
```bash
# Backend tests
python -m pytest -q

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

# Demo
python scripts/run_demo.py
```

## ENVIRONMENT
- `AI_PROVIDER=mock` (default) - No API keys needed
- `TAVILY_ENABLED=false` (default) - No Tavily calls
- `NEBIUS_API_KEY` - Only for live integration
- `TAVILY_API_KEY` - Only for live integration

## CURRENT PROVIDER STRATEGY
- **MockAIProvider**: Default, deterministic, no network
- **NebiusTokenFactoryProvider**: Live, requires NEBIUS_API_KEY
- **TavilyClient**: Live, requires TAVILY_API_KEY

## SECURITY RULES
- No secrets in code, logs, or responses
- No arbitrary shell execution
- No unrestricted file writes
- No fake verification
- No false provider claims
- No infinite agent loops
- No uncontrolled external API use
- Path containment in sandbox
- Command allowlist enforcement

## DEMO SCENARIOS (6 Canonical)
1. `payment_pool_exhaustion` - DB pool exhaustion
2. `external_api_retry_misconfiguration` - Retry storm
3. `bad_deployment_config_regression` - Bad config
4. `cache_stampede` - Cache stampede
5. `memory_leak` - Memory leak
6. `database_saturation` - DB saturation

## VERIFICATION LOGIC (Immutable)
```
VERIFIED IFF:
  Baseline FAIL
+ Post-Fix PASS
+ Health PASS
+ Control FAIL
```