# IMPLEMENTATION_PLAN.md - COSKA Implementation Roadmap

## Current Baseline (Verified)
- ✅ 43/43 backend tests passing
- ✅ 24/24 evaluation checks passing (3 scenarios × 8 checks)
- ✅ Frontend TypeScript clean + production build
- ✅ 8/8 health checks passing
- ✅ Security scan clean
- ✅ Judge Mode: Payment Pool Exhaustion → VERIFIED
- ✅ All 6 canonical scenarios working
- ✅ Mock provider fully functional
- ✅ Nebius/Tavily providers integrated
- ✅ Offline RAG + deterministic verification

---

## Phase 0: Documentation (Week 0) ✅ COMPLETE
- [x] AGENTS.md - Agent context file
- [x] docs/REPO_MAP.md - Repository map
- [x] docs/BRAIN.md - System intelligence model
- [x] docs/MEMORY.md - Architectural decisions
- [x] docs/RULES.md - Engineering rules
- [x] docs/TASK.md - Task breakdown
- [x] docs/PRD.md - Product requirements
- [x] docs/TRD.md - Technical reference
- [x] docs/APP_FLOW.md - Application flows
- [x] docs/UI_UX_BRIEF.md - Design system
- [x] docs/BACKEND_SCHEMA.md - Schema & API contracts

### Remaining Documentation (Week 0-1)
- [ ] docs/ARCHITECTURE.md - Architecture diagram & decisions
- [ ] docs/SECURITY_MODEL.md - Security architecture
- [ ] docs/AGENT_TOOLS.md - Tool registry guide
- [ ] docs/AI_PROVIDER_GUIDE.md - Provider integration
- [ ] docs/RAG_GUIDE.md - RAG usage & extension
- [ ] docs/DEPLOYMENT.md - Deployment guide
- [ ] docs/DEMO_RUNBOOK.md - Demo scenarios guide
- [ ] docs/SUBMISSION_CHECKLIST.md - Hackathon submission
- [ ] docs/SECURITY_AUDIT.md - Security audit report
- [ ] docs/TOOLING_MAP.md - Installed tools map
- [ ] docs/CHANGELOG_INTERNAL.md - Internal changelog

---

## Phase 1: Security Foundation (Week 1)

### P0-1: Secure Authentication
```python
# Files to create/modify:
- backend/app/api/auth.py (NEW)
- backend/app/models/__init__.py (add User, Session)
- backend/app/services/auth.py (NEW - Argon2, JWT)
- backend/app/services/storage.py (add user_id to all tables)
- frontend/src/pages/Login.tsx (NEW)
- frontend/src/services/api.ts (add auth endpoints)
- frontend/src/App.tsx (add /login route, auth guard)

# Implementation:
1. User model with Argon2id password hashing
2. JWT tokens in HttpOnly Secure cookies
3. POST /api/auth/register, POST /api/auth/login, POST /api/auth/logout, GET /api/auth/me
4. AUTH_REQUIRED=false for demo, true for production
5. Polished login screen with validation
6. Session expiration (24h) + revocation
```

### P0-2: Multi-User Tenant Isolation
```python
# Files to modify:
- backend/app/services/storage.py (add user_id to ALL tables)
- backend/app/api/dependencies.py (add get_current_user)
- backend/app/api/*.py (scope queries to user_id)
- backend/app/models/__init__.py (add user_id to all models)

# Implementation:
1. Add user_id column to: incidents, evidence, hypotheses, remediations, verifications, actions, investigations, memory, audit
2. Create get_current_user dependency
3. Scope ALL queries to authenticated user_id
4. Return 404 for cross-user access (no info leak)
5. Add cross-user access tests
```

### P0-3: Rate Limiting
```python
# Files to create/modify:
- backend/app/middleware/rate_limit.py (NEW)
- backend/app/main.py (add middleware)

# Implementation:
1. Token bucket per endpoint per user
2. Limits: login(5/min), register(3/min), investigate(10/min), tools(30/min), rag(20/min), tavily(5/min)
3. 429 response with Retry-After header
4. Request ID on all responses
```

### P0-4: Input Validation Hardening
```python
# Files to modify:
- backend/app/api/*.py (audit all endpoints)
- backend/app/models/__init__.py (add validators)

# Implementation:
1. String max lengths on all fields
2. Enum validation on all enum fields
3. UUID format validation
4. URL validation with allowlist
5. Pagination limits (max 100)
6. Reject oversized requests (>1MB)
7. SSRF prevention on search endpoints
```

### P0-5: Tool Security Hardening
```python
# Files to modify:
- backend/app/tools/sandbox.py (add tests)
- backend/app/tools/registry.py (verify allowlist)

# Implementation:
1. Command injection tests
2. Path traversal tests
3. Symlink escape tests
4. Secret/environment leakage tests
5. Verify command allowlist enforcement
```

### P0-6: Safe File Writes
```python
# Files to modify:
- backend/app/tools/sandbox.py
- backend/app/services/storage.py

# Implementation:
1. Canonical path resolution (os.path.realpath)
2. Workspace containment verification
3. Traversal rejection
4. Atomic writes (temp + rename)
5. Backup before overwrite
```

### P0-7: Error Handling Standardization
```python
# Files to create/modify:
- backend/app/middleware/error_handling.py (NEW)
- backend/app/api/*.py (use structured errors)

# Implementation:
1. Structured error: request_id, error_code, message, timestamp
2. No stack traces in responses
3. No internal paths/secrets/SQL in responses
4. Server logs detailed diagnostics (redacted)
```

### P0-8: API Key Security
```python
# Files to modify:
- backend/app/config.py (verify no defaults)
- backend/app/services/providers.py (verify no logging)
- backend/app/services/tavily.py (verify no logging)
- frontend/src/services/api.ts (verify no keys)

# Implementation:
1. NEBIUS_API_KEY, TAVILY_API_KEY only in .env/deployment
2. Never in code, logs, database, responses, git
3. Status endpoints: "configured" / "not configured" only
```

### P0-9: CORS / CSRF / Security Headers
```python
# Files to modify:
- backend/app/main.py (CORS, middleware)

# Implementation:
1. Strict CORS (explicit origins, no wildcard with credentials)
2. Secure cookies in production
3. CSRF protection via SameSite=Strict
4. Security headers:
   - Content-Security-Policy
   - X-Content-Type-Options: nosniff
   - Referrer-Policy: strict-origin-when-cross-origin
   - X-Frame-Options: DENY
```

### P0-10: Audit Logging
```python
# Files to modify:
- backend/app/services/storage.py (add audit_events table)
- backend/app/api/*.py (log events)

# Implementation:
1. Log: login, logout, investigation_start, tool_execute, remediation_propose, remediation_approve, verification_complete, provider_failure, security_rejection
2. Never log secrets
3. Include: user_id, action, resource, details, ip, user_agent
```

### P0-11: Privacy Controls
```python
# Files to modify:
- backend/app/services/storage.py (add delete endpoints)
- backend/app/api/incidents.py (add delete)
- backend/app/services/redaction.py (NEW)

# Implementation:
1. PII redaction in logs/errors
2. Secret redaction in logs/errors
3. Minimal retention policy
4. DELETE /api/incidents/{id} endpoint
5. Clear memory endpoint
6. Only relevant context to external models
```

---

## Phase 2: AI/RAG/Voice/TEE (Week 2)

### P1-1: Model Routing Abstraction
```python
# Files to create/modify:
- backend/app/services/model_router.py (NEW)
- backend/app/services/providers.py (extend)

# Implementation:
1. Fast model: classification, summarization, metadata extraction
2. Deep model: hypotheses, root cause, remediation
3. Internal routing layer (mock-compatible)
4. No live multi-model requirement
```

### P1-2: RAG 2.0 Enhancements
```python
# Files to modify:
- backend/app/services/rag.py

# Implementation:
1. Query normalization (stemming, synonyms)
2. Metadata filtering (category, tags, date range)
3. Top-k configuration
4. Relevance scoring with source type
3. Retrieval reason logging
4. Incident-memory retrieval
5. Runbook/postmortem/config retrieval
6. Only snippets to model context
```

### P1-3: RAG Security
```python
# Files to modify:
- backend/app/services/rag.py (add security layer)

# Implementation:
1. Prompt injection detection in retrieved content
2. Flag suspicious material
3. Strict separation: SYSTEM/USER/TOOLS/EVIDENCE/RETRIEVED_KNOWLEDGE
4. Test cases: ignore instructions, reveal secrets, run shell, modify files, bypass verification
```

### P1-4: Incident NLP Intelligence
```python
# Files to modify:
- backend/app/services/incident_intelligence.py

# Implementation:
1. Deterministic extraction: service, severity, environment, symptoms, components, dependencies, error patterns, timestamps, business impact, technical entities
2. Optional AI enhancement
3. No AI dependency for basic functionality
```

### P1-5: Hypothesis Engine Enhancements
```python
# Files to modify:
- backend/app/agent/hypotheses.py

# Implementation:
1. Confidence evolution tracking (history)
2. UI shows confidence changes over time
3. LLM cannot declare final verification
```

### P1-6: Root Cause Enhancements
```python
# Files to modify:
- backend/app/agent/root_cause.py

# Implementation:
1. Candidate + confidence + supporting/contradicting evidence + reason + alternatives + validation requirement
2. Must reference evidence IDs
```

### P1-7: Remediation Engine Enhancements
```python
# Files to modify:
- backend/app/agent/remediation.py

# Implementation:
1. Configuration diff display
2. Risk levels: LOW/MEDIUM/HIGH
3. Approval requirement: LOW auto, MEDIUM/HIGH human approval
4. Validation criteria per remediation
```

### P1-8: Incident Memory Expansion
```python
# Files to modify:
- backend/app/services/storage.py
- backend/app/api/enhanced.py

# Implementation:
1. Persist: user_id, service, incident, symptoms, evidence, root cause, remediation, verification, knowledge sources, research, timestamps
2. Similar incident search with similarity score
3. Show: similarity, previous root cause, previous fix, previous verification
```

### P1-9: Voice Assistant
```python
# Files to create/modify:
- frontend/src/components/VoiceAssistant.tsx (NEW)
- frontend/src/hooks/useVoice.ts (NEW)
- frontend/src/pages/*.tsx (integrate)

# Implementation:
1. Web Speech API + SpeechSynthesis (browser-native)
2. Deterministic intent parsing first
3. Optional LLM interpretation when live
4. Allowlisted commands only
5. UI states: LISTENING, THINKING, EXECUTING, COMPLETE
6. Microphone NOT always-on
```

### P1-10: Voice → Agent Integration
```python
# Files to modify:
- frontend/src/components/VoiceAssistant.tsx
- backend/app/api/enhanced.py (voice endpoint)

# Implementation:
1. "Investigate payment pool exhaustion" → launches scenario
2. Voice cannot bypass safety
```

### P1-11: TEE / Trusted Execution Abstraction
```python
# Files to create/modify:
- backend/app/services/tee.py (NEW)
- frontend/src/components/TEEStatus.tsx (NEW)

# Implementation:
1. TrustedExecutionProvider interface
2. LocalSafeTrustedExecutionProvider implementation
3. AttestedTEEProvider stub
4. UI: "Execution Trust: Local Safe" / "Attestation: UNAVAILABLE"
5. Only show "TEE VERIFIED" with actual attestation evidence
```

---

## Phase 3: Deployment & Polish (Week 3)

### P2-1: Deployment Artifacts
```dockerfile
# Files to create:
- Dockerfile (multi-stage)
- docker-compose.yml
- .env.production.example
```

### P2-2: PowerShell Wrapper
```powershell
# File to create:
# scripts/coska.ps1

# Commands:
# .\scripts\coska.ps1 doctor
# .\scripts\coska.ps1 seed
# .\scripts\coska.ps1 reset
# .\scripts\coska.ps1 test
# .\scripts\coska.ps1 build
# .\scripts\coska.ps1 backend
# .\scripts\coska.ps1 frontend
# .\scripts\coska.ps1 dev
# .\scripts\coska.ps1 demo
# .\scripts\coska.ps1 judge
# .\scripts\coska.ps1 security
# .\scripts\coska.ps1 health
# .\scripts\coska.ps1 audit
# .\scripts\coska.ps1 package
# .\scripts\coska.ps1 final-check
# .\scripts\coska.ps1 stop
```

### P2-3: Documentation Completion
```markdown
# Files to create:
- docs/ARCHITECTURE.md
- docs/SECURITY_MODEL.md
- docs/AGENT_TOOLS.md
- docs/AI_PROVIDER_GUIDE.md
- docs/RAG_GUIDE.md
- docs/DEPLOYMENT.md
- docs/DEMO_RUNBOOK.md
- docs/SUBMISSION_CHECKLIST.md
- docs/SECURITY_AUDIT.md
- docs/TOOLING_MAP.md
- docs/CHANGELOG_INTERNAL.md

# README.md update with:
- Problem, Solution, Agentic workflow
- RAG, Incident Memory, Evidence Graph
- NVIDIA Nemotron, Nebius Token Factory, Tavily
- Sandbox, Deterministic Verification, Security
- Setup, Judge Mode, Deployment
- Core: LLM REASONS / TOOLS ACT / VERIFIER DECIDES
```

### P2-4: Dependency Audit
```bash
# Commands:
cd backend && pip-audit
cd frontend && npm audit
# Fix compatible high-value vulnerabilities only
```

### P2-5: Additional Tests
```python
# Files to create:
- backend/tests/test_auth.py
- backend/tests/test_sessions.py
- backend/tests/test_tenant_isolation.py
- backend/tests/test_rate_limiting.py
- backend/tests/test_validation.py
- backend/tests/test_ssrf.py
- backend/tests/test_prompt_injection.py
- backend/tests/test_voice_commands.py
- backend/tests/test_tee_status.py
- backend/tests/test_rag.py
- backend/tests/test_planner.py
- backend/tests/test_verification.py
- backend/tests/test_secret_redaction.py
- backend/tests/test_path_traversal.py
```

---

## Phase 4: Final Validation (Week 3 End)

### Final Validation Checklist
```bash
# Run all:
pytest -q                                    # 43+ tests
cd frontend && npx tsc --noEmit              # TypeScript clean
cd frontend && npm run build                 # Production build
python scripts/healthcheck.py                # 8/8 checks
python scripts/coska_doctor.py               # 9/11 checks
python scripts/security_check.py             # Clean
python scripts/evaluate_coska.py             # 24/24 checks
python scripts/run_demo.py                   # VERIFIED
# Dependency audit
```

### Canonical Demo Target
```
Payment Pool Exhaustion Scenario:
Incident → NLP → RAG → Planner → Evidence → Hypotheses → Root Cause → Remediation → Sandbox → Verification → VERIFIED
```

---

## Remaining Live Integration Work (Post-Submission)

| Component | Status | Required For |
|-----------|--------|--------------|
| Nebius live inference | ❌ Needs API key | Production AI reasoning |
| Tavily live search | ❌ Needs API key | Production web research |
| Docker sandbox | ⚠️ Optional | Production isolation |
| Auth system | ⚠️ Optional | Multi-user production |
| Real deployment | ❌ Not deployed | Hackathon submission |

**DO NOT PERFORM LIVE INTEGRATION AUTOMATICALLY**