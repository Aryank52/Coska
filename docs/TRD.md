# TRD - Technical Reference Document

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        COSKA SYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React + TS + Vite)                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────┐ │
│  │ Dashboard   │ │ Investigation│ │ Judge Mode  │ │ Knowledge │ │
│  │ Service Map │ │ Evidence    │ │ Voice Asst  │ │ Evidence  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └───────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Backend (FastAPI)                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────┐ │
│  │ Orchestrator │ │ Agent Engines│ │ Services     │ │ Tools  │ │
│  │ (8 phases)   │ │ (Evidence,   │ │ (RAG, Planner│ │ (6     │ │
│  │              │ │  Hypotheses, │ │  Intelligence│ │  types)│ │
│  │              │ │  Root Cause, │ │  Service Map,│ │        │ │
│  │              │ │  Remediation,│ │  Incident    │ │        │ │
│  │              │ │  Verifier)   │ │  Memory)     │ │        │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Provider Abstraction                                           │
│  ┌─────────────────────┐ ┌─────────────────────────────────┐   │
│  │ MockAIProvider      │ │ NebiusTokenFactoryProvider      │   │
│  │ (default, offline)  │ │ (live, requires NEBIUS_API_KEY) │   │
│  └─────────────────────┘ └─────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Persistence (SQLite + SQLAlchemy)                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Incidents, Evidence, Hypotheses, Remediations,          │   │
│  │ Verifications, Actions, Memory, Audit Events            │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  Sandbox                                                        │
│  ┌──────────────────┐ ┌──────────────────┐                     │
│  │ LocalSafe        │ │ Docker           │                     │
│  │ (subprocess,     │ │ (container,      │                     │
│  │  allowlist)      │ │  isolated)       │                     │
│  └──────────────────┘ └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontend (React + TypeScript + Vite)

### Tech Stack
- **React 18** + **TypeScript 5** (strict mode)
- **Vite 5** for dev/build
- **React Router 6** for routing
- **Axios** for API client
- **Lucide React** for icons
- **date-fns** for date formatting
- **CSS Custom Properties** for theming

### Project Structure
```
frontend/
├── src/
│   ├── components/          # Shared UI components
│   │   └── Layout.tsx       # Header, navigation, outlet
│   ├── pages/               # Route components
│   │   ├── Dashboard.tsx    # Command center
│   │   ├── Investigation.tsx# Progress, status
│   │   ├── Evidence.tsx     # Evidence by source
│   │   ├── EvidenceGraph.tsx# Causal graph (canvas)
│   │   ├── Hypotheses.tsx   # Competing hypotheses
│   │   ├── RootCause.tsx    # Root cause + evidence chain
│   │   ├── Remediation.tsx  # Fix + risk + rollback
│   │   ├── Verification.tsx # 3-stage + receipt
│   │   ├── IncidentDetail.tsx# Incident shell
│   │   ├── IncidentIntelligence.tsx # NLP analysis
│   │   ├── KnowledgeBase.tsx# RAG search
│   │   ├── ServiceMap.tsx   # Topology + blast radius
│   │   ├── Judge.tsx        # Judge Mode (canonical)
│   │   ├── JudgeMode.tsx    # Legacy Judge Mode
│   │   ├── Architecture.tsx # Architecture diagram
│   │   └── WhyCoska.tsx     # Marketing page
│   ├── services/
│   │   ├── api.ts           # Axios client + typed endpoints
│   │   └── demoScenarios.ts # 6 canonical scenarios
│   ├── types/
│   │   └── incident.ts      # Shared TypeScript types
│   ├── App.tsx              # Routes
│   ├── main.tsx             # Entry point
│   └── index.css            # Design system
├── package.json
├── tsconfig.json
├── vite.config.ts
└── index.html
```

### Key Types (`src/types/incident.ts`)
```typescript
// Core models matching backend
interface Incident { id, service, severity, description, logs?, deployment?, repository?, metadata, status, created_at, updated_at }
interface Evidence { id, incident_id, source_type, claim, reference, timestamp, confidence, related_component?, raw_data? }
interface Hypothesis { id, incident_id, title, description, supporting_evidence_ids[], contradicting_evidence_ids[], confidence, next_investigation_action?, status, created_at, updated_at }
interface Remediation { id, incident_id, hypothesis_id, type, description, exact_change, expected_effect, risk, blast_radius, rollback_plan, created_at }
interface VerificationResult { id, incident_id, remediation_id, baseline_test, post_fix_tests, health_check, control_test, verdict, evidence_count, model, details, created_at }
interface AgentAction { id, incident_id, step, tool?, timestamp, duration_ms, status, summary, input_data, output_data, error? }
```

### API Client (`src/services/api.ts`)
```typescript
// All endpoints typed
export const getIncidents = () => api.get('/incidents').then(r => r.data)
export const investigateIncident = (id, autoApprove) => api.post(`/incidents/${id}/investigate`, { auto_approve: autoApprove })
export const getEvidenceGraph = (id) => api.get(`/incidents/${id}/evidence-graph`)
export const getServiceMap = () => api.get('/service-map')
export const getBlastRadius = (serviceId) => api.get(`/service-map/blast-radius/${serviceId}`)
export const searchKnowledgeBase = (query) => api.post('/rag/search', { query, top_k: 10 })
export const createInvestigationPlan = (data) => api.post('/planner/plan', data)
```

---

## Backend (FastAPI)

### Tech Stack
- **FastAPI 0.115** + **Python 3.12**
- **SQLAlchemy 2.0** (async) + **aiosqlite**
- **Pydantic 2** + **Pydantic Settings**
- **structlog** for structured logging
- **httpx** for HTTP clients
- **tenacity** for retries
- **pytest-asyncio** for testing

### Project Structure
```
backend/
├── app/
│   ├── agent/               # Core investigation engines
│   │   ├── orchestrator.py  # 8-phase workflow
│   │   ├── evidence.py      # Log/config/deployment analysis
│   │   ├── hypotheses.py    # Competing hypotheses
│   │   ├── root_cause.py    # Root cause synthesis
│   │   ├── remediation.py   # Remediation generation
│   │   ├── verifier.py      # 3-stage causal verification
│   │   └── timeline.py      # Timeline construction
│   ├── api/                 # REST endpoints
│   │   ├── incidents.py     # Incident CRUD + investigation
│   │   ├── investigations.py# State, evidence, hypotheses
│   │   ├── verification.py  # Verification results
│   │   ├── health.py        # AI/Tavily/Sandbox health
│   │   ├── demo.py          # Demo scenarios, Judge, RAG
│   │   └── enhanced.py      # Intelligence, RAG, Graph, Planner, Service Map
│   ├── models/              # Pydantic models
│   │   └── __init__.py      # All core models
│   ├── services/            # Business logic
│   │   ├── planner.py       # Agentic planner
│   │   ├── rag.py           # BM25 RAG engine
│   │   ├── incident_intelligence.py # NLP extraction
│   │   ├── evidence_graph.py# Evidence relationships
│   │   ├── service_map.py   # Topology + blast radius
│   │   ├── demo_scenarios.py# 6 canonical scenarios
│   │   ├── providers.py     # AI provider abstraction
│   │   ├── storage.py       # SQLite persistence
│   │   ├── tavily.py        # Web research
│   │   ├── nebius.py        # Nebius provider
│   │   └── sandbox.py       # LocalSafe + Docker
│   ├── tools/               # Tool registry
│   │   ├── registry.py      # Tool registration/validation
│   │   ├── investigation.py # 6 inspection tools
│   │   └── sandbox.py       # Sandbox tool
│   ├── config.py            # Settings (Pydantic Settings)
│   └── main.py              # FastAPI app + routers
├── demo/                    # Demo payment-api service
├── tests/                   # 43 tests
└── requirements.txt
```

### Core Models (`app/models/__init__.py`)
```python
# Enums
class Severity(str, Enum): LOW, MEDIUM, HIGH, CRITICAL
class IncidentStatus(str, Enum): RECEIVED, TRIAGING, ..., RESOLVED, VERIFICATION_FAILED
class SourceType(str, Enum): LOG, REPOSITORY, CONFIG, DEPLOYMENT, RUNTIME, WEB, TEST
class HypothesisStatus(str, Enum): ACTIVE, WEAKENED, REJECTED, SUPPORTED
class Verdict(str, Enum): VERIFIED, FAILED, UNVERIFIED, INSUFFICIENT_EVIDENCE
class InvestigationPhase(str, Enum): INCIDENT_INTAKE, EVIDENCE_COLLECTION, ..., VERIFICATION

# Core Models
class Incident(BaseModel): id, service, severity, description, logs?, deployment?, repository?, metadata, status, created_at, updated_at
class Evidence(BaseModel): id, incident_id, source_type, claim, reference, timestamp, confidence, related_component?, raw_data?
class Hypothesis(BaseModel): id, incident_id, title, description, supporting_evidence_ids[], contradicting_evidence_ids[], confidence, next_investigation_action?, status, created_at, updated_at
class Remediation(BaseModel): id, incident_id, hypothesis_id, type, description, exact_change, expected_effect, risk, blast_radius, rollback_plan, created_at
class VerificationResult(BaseModel): id, incident_id, remediation_id, baseline_test, post_fix_tests, health_check, control_test, verdict, evidence_count, model, details, created_at
class AgentAction(BaseModel): id, incident_id, step, tool?, timestamp, duration_ms, status, summary, input_data, output_data, error?
```

### Provider Abstraction (`app/services/providers.py`)
```python
class AIProvider(ABC):
    @abstractmethod
    async def chat_completion(messages, tools?, tool_choice?, temperature?, max_tokens?) -> Dict
    @abstractmethod
    async def health_check() -> ProviderInfo
    @abstractmethod
    async def test_inference(prompt) -> Dict
    @abstractmethod
    async def close()

class MockAIProvider(AIProvider):  # Deterministic, offline
    async def chat_completion(...) -> Dict  # Returns structured JSON per phase

class NebiusTokenFactoryProvider(AIProvider):  # Live
    def __init__(api_key, base_url, model): ...
    async def chat_completion(...) -> Dict  # HTTP to Nebius Token Factory
    # Bounded retries, explicit error states

def create_provider(provider_type: str, **kwargs) -> AIProvider
def get_provider(provider_type=None, **kwargs) -> AIProvider  # Singleton
```

### RAG Engine (`app/services/rag.py`)
```python
class RAGEngine:
    def __init__(runbooks?):  # 20 default runbooks
    def search(query: str, top_k: int=3) -> RAGSearchResult:
        # BM25 scoring
        # Returns: documents[], query, query_tokens, trace{}
    def get_document(doc_id) -> RAGDocument
    def list_categories() -> List[str]
    def list_documents() -> List[Dict]

class RAGSearchResult:
    documents: List[RAGDocument]
    query: str
    query_tokens: List[str]
    trace: {top_results: [{id, title, relevance_score, matched_terms, match_reason}]}

class RAGDocument:
    id, title, category, source, summary, content, tags[]
    relevance_score: float
    snippet: str
    matched_terms: List[str]
    match_reason: str  # "title matches query; tags match: pool, exhaustion"
```

### Planner (`app/services/planner.py`)
```python
class AgenticPlanner:
    def __init__():  # provider, tool_registry, rag_engine, intelligence_engine
    
    async def create_plan(incident, intelligence, evidence, hypotheses) -> InvestigationPlan:
        # LLM generates step-by-step plan with tool selection, reasoning
    
    async def execute_plan(plan, incident) -> PlanResult:
        # Executes steps respecting dependencies, budgets
        # Re-planning on failure
    
class InvestigationPlan:
    incident_id, goal, steps[PlannerStep], current_step_index, budgets...
    
class PlannerStep:
    step_id, type, description, tool_name?, tool_input?, rag_query?, reasoning, expected_outcome, depends_on[]
```

### Verification (`app/app/agent/verifier.py`)
```python
class Verifier:
    def __init__(sandbox, repo_path, model):
    
    async def verify(incident, remediation, evidence, original_config, config_file) -> VerificationReport:
        # Stage 1: BASELINE - Run tests with original config (must FAIL)
        # Stage 2: POST-FIX - Apply remediation, run tests (must PASS)
        # Stage 3: HEALTH - Service health checks (must PASS)
        # Stage 4: CONTROL - Revert config, run tests (must FAIL)
        # VERIFIED IFF: Baseline FAIL + Post-Fix PASS + Health PASS + Control FAIL
```

---

## AI Providers

### MockAIProvider (Default)
- **Deterministic** - Same input → same output
- **Offline** - No network calls
- **Phase-aware** - Returns structured JSON per investigation phase
- **Token counting** - Simulated usage
- **Health check** - Always healthy

### NebiusTokenFactoryProvider (Live)
- **Endpoint**: `https://api.tokenfactory.us-central1.nebius.com/v1/`
- **Model**: `nvidia/nemotron-3-ultra-550b-a55b`
- **Auth**: Bearer token (NEBIUS_API_KEY)
- **Retries**: 2 retries with exponential backoff (1s, 2s) on 429
- **Errors**: Explicit states (NOT_CONFIGURED, UNAUTHORIZED, RATE_LIMITED, UNAVAILABLE, MODEL_UNAVAILABLE, INVALID_RESPONSE)
- **Timeout**: 120s total, 10s connect

### TavilyClient (Live)
- **Endpoint**: `https://api.tavily.com/search`
- **Auth**: API key in payload
- **Defaults**: depth=basic, max_results=3, include_usage=true
- **Rate limiting**: Configurable max calls per investigation

---

## Sandbox

### LocalSafeSandbox (Default)
- **Execution**: `subprocess.run()` with allowlist
- **Allowlist**: `python`, `pytest`, `uvicorn`, `pip`
- **Path containment**: `os.path.realpath()` + workspace check
- **Environment**: Sanitized (no secrets)
- **Timeout**: Configurable (default 300s)
- **Resource limits**: Memory/CPU via subprocess (best effort)

### DockerSandbox (Optional)
- **Execution**: Docker container
- **Isolation**: Full container isolation
- **Requires**: Docker daemon
- **Fallback**: LocalSafe if Docker unavailable

---

## Persistence (SQLite)

### Schema
```sql
-- Incidents
CREATE TABLE incidents (id, service, severity, description, logs, deployment, repository, metadata, status, created_at, updated_at)

-- Evidence
CREATE TABLE evidence (id, incident_id, source_type, claim, reference, timestamp, confidence, related_component, raw_data)

-- Hypotheses
CREATE TABLE hypotheses (id, incident_id, title, description, supporting_evidence_ids, contradicting_evidence_ids, confidence, next_investigation_action, status, created_at, updated_at)

-- Remediations
CREATE TABLE remediations (id, incident_id, hypothesis_id, type, description, exact_change, expected_effect, risk, blast_radius, rollback_plan, created_at)

-- Verification Runs
CREATE TABLE verification_runs (id, incident_id, remediation_id, baseline_test, post_fix_tests, health_check, control_test, verdict, evidence_count, model, details, created_at)

-- Agent Actions
CREATE TABLE agent_actions (id, incident_id, step, tool, timestamp, duration_ms, status, summary, input_data, output_data, error)

-- Investigations (full state)
CREATE TABLE investigations (id, incident_id, current_phase, state_json, created_at, updated_at)

-- Incident Memory
CREATE TABLE incident_memory (id, service, symptoms, root_cause, evidence, remediation, verification_result, created_at)

-- Audit Events
CREATE TABLE audit_events (id, user_id, action, resource, details, timestamp)
```

---

## API Endpoints

### Incidents
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/incidents` | Create incident |
| GET | `/api/incidents` | List incidents |
| GET | `/api/incidents/{id}` | Get incident |
| POST | `/api/incidents/{id}/investigate` | Start investigation |
| GET | `/api/incidents/{id}/timeline` | Get timeline |
| GET | `/api/incidents/{id}/evidence` | Get evidence |
| GET | `/api/incidents/{id}/hypotheses` | Get hypotheses |
| GET | `/api/incidents/{id}/actions` | Get agent actions |
| GET | `/api/incidents/{id}/root-cause` | Get root cause |
| GET | `/api/incidents/{id}/remediation` | Get remediation |
| POST | `/api/incidents/{id}/simulate-fix` | Dry run |
| POST | `/api/incidents/{id}/apply-fix` | Apply + verify |

### Enhanced (New)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/incidents/{id}/intelligence` | Incident NLP intelligence |
| POST | `/api/rag/search` | RAG knowledge search |
| GET | `/api/rag/documents` | List runbooks |
| GET | `/api/incidents/{id}/evidence-graph` | Evidence graph |
| GET | `/api/service-map` | Service topology |
| GET | `/api/service-map/blast-radius/{service}` | Blast radius |
| POST | `/api/planner/plan` | Create investigation plan |
| POST | `/api/planner/execute` | Execute plan |
| GET | `/api/incidents/{id}/verification-receipt` | Verification receipt |
| GET | `/api/incidents/{id}/report` | Incident report (JSON/MD) |

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Basic health |
| GET | `/api/health/ai` | AI provider status |
| GET | `/api/health/tavily` | Tavily status |
| GET | `/api/health/sandbox` | Sandbox status |

---

## Configuration

### Environment Variables
```bash
# Required for live integration only
NEBIUS_API_KEY=                    # Nebius Token Factory key
NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
NEBIUS_MODEL=nvidia/nemotron-3-ultra-550b-a55b

TAVILY_API_KEY=                    # Tavily API key
TAVILY_ENABLED=false               # Enable Tavily

# Application
AI_PROVIDER=mock                   # mock | nebius | auto
DATABASE_URL=sqlite:///./coska.db
APP_ENV=development                # development | production
APP_HOST=0.0.0.0
APP_PORT=8000

# Frontend
VITE_API_URL=http://localhost:8000

# Sandbox
SANDBOX_MODE=local                 # local | docker | auto
SANDBOX_TIMEOUT=300
SANDBOX_MEMORY_LIMIT=512m
SANDBOX_CPU_LIMIT=1.0

# Safety Budgets
MAX_AGENT_STEPS=40
MAX_TOOL_CALLS=25
MAX_RETRIES=3
MAX_INVESTIGATION_TIME=300

# Auth
AUTH_REQUIRED=false
SESSION_SECRET=                    # For production
```

---

## Security Model

### Secrets Management
- `.env` for local development (gitignored)
- Deployment secrets via platform (Railway, Render, etc.)
- Never in code, logs, database, responses, git

### Authentication (Optional)
- `AUTH_REQUIRED=false` for demo
- Argon2id password hashing
- JWT in HttpOnly Secure cookies
- Session expiration: 24h
- CSRF protection via SameSite=Strict

### Authorization
- All tables have `user_id`
- Queries scoped to authenticated user
- 404 for cross-user access (no info leak)

### Rate Limiting
- Login: 5/min
- Register: 3/min
- Investigation: 10/min
- Tool execution: 30/min
- RAG search: 20/min
- Tavily: 5/min

### Input Validation
- Pydantic on all endpoints
- String max lengths
- Enum validation
- UUID format
- URL validation
- Pagination limits (max 100)

### Tool Security
- Command allowlist: `python`, `pytest`, `uvicorn`, `pip`
- Path containment: `realpath()` + workspace check
- Symlink rejection
- Environment sanitization
- Timeout enforcement

### File Safety
- Canonical path resolution
- Workspace boundary check
- Atomic writes (temp + rename)
- Backup before overwrite

### Error Handling
```json
{
  "request_id": "req-abc123",
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid incident ID format",
  "timestamp": "2026-10-30T18:00:00Z"
}
```
- No stack traces to client
- No internal paths/secrets in responses
- Server logs: detailed + redacted

### Audit Logging
| Event | Logged |
|-------|--------|
| Login/Logout | ✅ |
| Investigation started | ✅ |
| Tool executed | ✅ |
| Remediation proposed | ✅ |
| Remediation approved | ✅ |
| Verification completed | ✅ |
| Provider failure | ✅ |
| Security rejection | ✅ |

---

## Deployment

### Development
```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

### Production (Docker)
```dockerfile
# Dockerfile (multi-stage)
FROM python:3.12-slim AS builder
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --user -r requirements.txt

FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY backend/ .
COPY --from=frontend-builder /app/dist ./frontend/dist
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml
```yaml
services:
  api:
    build: .
    ports: ["8000:8000"]
    environment:
      - AI_PROVIDER=nebius
      - NEBIUS_API_KEY=${NEBIUS_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
      - AUTH_REQUIRED=true
      - SESSION_SECRET=${SESSION_SECRET}
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Monitoring & Observability

### Structured Logging (structlog)
```python
logger.info("agent_action", incident_id=..., step=..., tool=..., summary=...)
logger.info("tool_executed", tool=..., success=...)
logger.info("root_cause_identified", incident_id=..., cause=..., confidence=...)
logger.warning("rag_retrieval_failed", error=...)
logger.error("verification_failed", incident_id=..., error=...)
```

### Health Endpoints
- `/api/health` - Basic
- `/api/health/ai` - Provider status + model
- `/api/health/tavily` - Tavily connectivity
- `/api/health/sandbox` - Sandbox availability

### Metrics (Future)
- Investigation duration
- Evidence count per phase
- Hypothesis confidence evolution
- Verification verdict distribution
- Provider latency/tokens
- Tavily calls / cache hits