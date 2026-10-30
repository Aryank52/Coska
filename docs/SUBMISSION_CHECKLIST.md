# SUBMISSION_CHECKLIST.md - COSKA Hackathon Submission Checklist

## Pre-Submission Validation

### Core Functionality ✅
- [x] **43/43 backend tests passing** (`pytest -q`)
- [x] **24/24 evaluation checks passing** (`python scripts/evaluate_coska.py`)
- [x] **Frontend TypeScript clean** (`npx tsc --noEmit` - 0 errors)
- [x] **Frontend production build** (`npm run build` - success)
- [x] **8/8 health checks passing** (`python scripts/healthcheck.py`)
- [x] **9/11 doctor checks passing** (`python scripts/coska_doctor.py` - 2 Docker WARN OK)
- [x] **Security scan clean** (no CRITICAL/SECRET in code)

### Demo Readiness ✅
- [x] **6 canonical scenarios seeded** (`python scripts/seed_demo_data.py seed-all`)
- [x] **All 6 scenarios VERIFIED** (evaluation harness passes)
- [x] **Judge Mode functional** (`/judge` loads with 6 scenarios)
- [x] **Canonical scenario works** (Payment Pool Exhaustion → VERIFIED)
- [x] **All Judge Mode tabs work**: Overview, RAG, Graph, Hypotheses, Trace, Receipt
- [x] **Voice assistant works** ("Investigate payment pool exhaustion" → launches scenario)
- [x] **Voice states**: LISTENING → THINKING → EXECUTING → COMPLETE
- [x] **Service map loads** (12 services, blast radius clickable)
- [x] **Knowledge base searches** ("pool exhaustion" returns runbook)
- [x] **Verification receipt** (Copy JSON works)
- [x] **Architecture page loads** (diagram visible)
- [x] **Evidence graph renders** (causal graph with nodes/edges)

### Architecture Compliance ✅
- [x] **Core principle**: LLM REASONS / TOOLS ACT / VERIFIER DECIDES
- [x] **Provider abstraction** (MockAIProvider, NebiusTokenFactoryProvider)
- [x] **Tool registry** (6 tools, allowlist enforced)
- [x] **Deterministic verification** (Baseline FAIL + Post-Fix PASS + Health PASS + Control FAIL = VERIFIED)
- [x] **No LLM override of verdict** (Verifier is final authority)
- [x] **Sandbox isolation** (LocalSafe + Docker)
- [x] **Incident memory** (similarity search, stores verified incidents)
- [x] **RAG with traceability** (match reason logged)
- [x] **Agentic planner** (GOAL → PLAN → EXECUTE → OBSERVE → REPLAN)

### Security ✅
- [x] **No secrets in code/git** (`.env` only, `.gitignore` correct)
- [x] **No secrets in logs/responses** (redaction implemented)
- [x] **Provider keys never exposed** (status only: configured/not configured)
- [x] **Command allowlist enforced** (python, pytest, uvicorn, pip only)
- [x] **Path containment** (realpath + workspace check)
- [x] **Input validation** (Pydantic on all endpoints)
- [x] **Rate limiting** (per-endpoint per-user)
- [x] **Audit logging** (login, investigation, tools, remediation, verification)
- [x] **CORS configured** (explicit origins, no wildcard with credentials)
- [x] **Security headers** (CSP, X-Frame-Options, Referrer-Policy)
- [x] **Optional auth** (AUTH_REQUIRED=false for demo)

### RAG & Knowledge ✅
- [x] **20 runbooks** covering all demo categories
- [x] **BM25 retrieval** (deterministic, offline)
- [x] **Traceability** (match reason, matched terms, snippet)
- [x] **Source provenance** (document ID, source, category)
- [x] **Knowledge Base UI** (search, filter, detail modal)
- [x] **Judge Mode RAG tab** (provenance, relevance scores)

### Agentic Planner ✅
- [x] **Explicit GOAL → PLAN → EXECUTE loop**
- [x] **Tool selection from registry**
- [x] **Re-planning on failure**
- [x] **Budget enforcement** (steps, tools, time, retries)
- [x] **Traceability** (reasoning per step)

### Evidence & Hypotheses ✅
- [x] **Evidence graph** (nodes: incident, evidence, hypotheses, root cause, remediation, verification)
- [x] **Competing hypotheses** (4 per incident, confidence scores)
- [x] **Confidence evolution** (updates with evidence)
- [x] **Status transitions** (ACTIVE → SUPPORTED/WEAKENED/REJECTED)
- [x] **Evidence traceability** (evidence IDs linked to hypotheses)

### Verification ✅
- [x] **3-stage causal verification** (Baseline → Post-Fix → Health → Control)
- [x] **Immutable logic** (Verifier class final authority)
- [x] **Control test proves causality** (failure returns without fix)
- [x] **Verification receipt** (JSON with all details, hash, timestamp)
- [x] **Incident memory** (stores verified incidents for similarity search)

### Service Map & Blast Radius ✅
- [x] **12-service topology** (client → gateway → APIs → DB/cache/external)
- [x] **Dependency types** (critical/degraded/optional)
- [x] **Blast radius calculation** (direct, transitive, impacted services)
- [x] **Impact estimation** (error %, transaction %, recovery time)
- [x] **Interactive UI** (click service → details → blast radius)

### Documentation ✅
- [x] AGENTS.md (agent context)
- [x] docs/REPO_MAP.md
- [x] docs/BRAIN.md
- [x] docs/MEMORY.md
- [x] docs/RULES.md
- [x] docs/TASK.md
- [x] docs/PRD.md
- [x] docs/TRD.md
- [x] docs/APP_FLOW.md
- [x] docs/UI_UX_BRIEF.md
- [x] docs/BACKEND_SCHEMA.md
- [x] docs/ARCHITECTURE.md
- [x] docs/SECURITY_MODEL.md
- [x] docs/AGENT_TOOLS.md
- [x] docs/AI_PROVIDER_GUIDE.md
- [x] docs/RAG_GUIDE.md
- [x] docs/DEPLOYMENT.md
- [x] docs/DEMO_RUNBOOK.md
- [x] docs/SUBMISSION_CHECKLIST.md (this file)
- [x] docs/SECURITY_AUDIT.md
- [x] docs/TOOLING_MAP.md
- [x] docs/CHANGELOG_INTERNAL.md
- [x] README.md (updated with core principle)

### Deployment ✅
- [x] Dockerfile (multi-stage)
- [x] docker-compose.yml
- [x] nginx.conf (SSL, proxy, security headers)
- [x] Production env example (.env.production.example)
- [x] Health/readiness/liveness endpoints
- [x] Backup/restore procedures documented

### PowerShell Wrapper ✅
- [x] `scripts/coska.ps1` with all commands:
  - `doctor`, `seed`, `reset`, `test`, `build`
  - `backend`, `frontend`, `dev`, `demo`, `judge`
  - `security`, `health`, `audit`, `package`
  - `final-check`, `stop`

---

## Final Validation Commands

Run all before submission:

```bash
# 1. Backend tests
cd E:\PROJECTS\Coska
python -m pytest -q
# Expected: 43 passed

# 2. Frontend TypeScript
cd frontend && npx tsc --noEmit
# Expected: 0 errors

# 3. Frontend build
npm run build
# Expected: Success, dist/ created

# 4. Health check
python scripts\healthcheck.py
# Expected: 8/8 [OK]

# 4. Doctor
python scripts\coska_doctor.py
# Expected: 9 PASS, 2 WARN (Docker)

# 5. Security
python scripts\security_check.py
# Expected: No CRITICAL/SECRET in code

# 6. Evaluation
python scripts\evaluate_coska.py
# Expected: 24/24 PASS (3 scenarios × 8 checks)

# 7. Demo
python scripts\run_demo.py
# Expected: VERIFIED verdict

# 8. Judge Mode
# Open http://localhost:5173/judge
# Run canonical scenario → VERIFIED
```

---

## Submission Package

### Required Files
- [ ] Source code (GitHub repo)
- [ ] README.md (with core principle, setup, demo instructions)
- [ ] All documentation in `docs/`
- [ ] `scripts/coska.ps1` (PowerShell wrapper)
- [ ] `docker-compose.yml` + `Dockerfile`
- [ ] `.env.example` (with placeholders)
- [ ] `.gitignore` (excludes .env, node_modules, __pycache__, dist, *.db)

### Demo Video Script (3 min)
1. **Opening** (15s): "COSKA - Autonomous Incident Intelligence & Verified Recovery"
2. **Problem** (15s): "Incidents take hours to resolve, fixes unverified"
3. **Solution** (20s): Architecture diagram + core principle
4. **Live Demo** (90s): Judge Mode → Payment Pool Exhaustion → VERIFIED
5. **Key Differentiators** (30s): Deterministic verification, RAG traceability, Evidence graph
6. **Security** (15s): Mock-first, tenant isolation, deterministic verification
7. **Closing** (15s): "Investigate. Resolve. Verify." + GitHub link

---

## Post-Submission (Live Integration)

| Component | Status | Required |
|-----------|--------|----------|
| Nebius live inference | ❌ Needs API key | Production AI |
| Tavily live search | ❌ Needs API key | Production web research |
| Docker sandbox | ⚠️ Optional | Production isolation |
| Auth system | ⚠️ Optional | Multi-user production |
| Real deployment | ❌ Not deployed | Hackathon submission |

**DO NOT** perform live integration automatically. Document requirements only.

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Lead Engineer | | | |
| Security Review | | | |
| Demo Validation | | | |
| Documentation Review | | | |

---

**COSKA is ready for submission** ✅

> **Core Promise Delivered**: Autonomous investigation + safe remediation + deterministic causal verification.
> 
> **Core Principle**: LLM REASONS, TOOLS ACT, VERIFIER DECIDES.