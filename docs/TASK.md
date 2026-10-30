# TASK.md - COSKA Implementation Tasks

## P0 - Critical (Must Complete for Submission)

### P0-1: Secure Authentication (Optional)
- [ ] Argon2/bcrypt password hashing
- [ ] Secure session tokens with HttpOnly cookies
- [ ] Session expiration & revocation
- [ ] POST /api/auth/register, POST /api/auth/login, POST /api/auth/logout, GET /api/auth/me
- [ ] Polished login screen
- [ ] AUTH_REQUIRED=false for Judge Mode demo
- [ ] Tests for auth flow

### P0-2: Multi-User Tenant Isolation
- [ ] Add `user_id` to all tables: users, sessions, incidents, investigations, evidence, hypotheses, remediations, verification_receipts, incident_memory, audit_events
- [ ] Scope all queries to authenticated user
- [ ] 404/403 for cross-user access (no info leakage)
- [ ] Cross-user access tests

### P0-3: Rate Limiting / Abuse Protection
- [ ] Rate limits on: login, register, investigation creation, agent execution, RAG search, Tavily calls, Nebius inference
- [ ] 429 responses (safe, no stack traces)
- [ ] Request IDs on all responses

### P0-4: Input Validation Hardening
- [ ] Audit all API endpoints for validation
- [ ] String lengths, enums, IDs, URLs, pagination, JSON bodies
- [ ] Reject oversized requests
- [ ] Prevent SSRF (search endpoints not arbitrary URL fetchers)
- [ ] Prevent malformed payload abuse

### P0-5: Tool Security Hardening
- [ ] Command injection tests
- [ ] Path traversal tests
- [ ] Symlink escape tests
- [ ] Secret/environment leakage tests
- [ ] Verify command allowlist enforcement

### P0-6: Safe File Writes
- [ ] Canonical path resolution
- [ ] Workspace containment verification
- [ ] Traversal rejection
- [ ] Atomic writes with backup
- [ ] No arbitrary filesystem access

### P0-7: Error Handling Standardization
- [ ] Structured error: request_id, error_code, message, timestamp
- [ ] No stack traces in responses
- [ ] No internal paths/secrets/SQL in responses
- [ ] Server logs detailed diagnostics (redacted)

### P0-8: API Key Security
- [ ] NEBIUS_API_KEY, TAVILY_API_KEY never in frontend/db/logs/reports
- [ ] .env / deployment secret storage only
- [ ] Status endpoints: "configured" / "not configured" only

### P0-7: CORS / CSRF / Security Headers
- [ ] Strict CORS (no credentialed wildcard origins)
- [ ] Secure cookies in production
- [ ] CSRF protection where needed
- [ ] Security headers: CSP, X-Content-Type-Options, Referrer-Policy, frame-ancestors

### P0-8: Audit Logging
- [ ] Log: login, logout, investigation, tool execution, remediation, approval, verification, provider failure, security rejection
- [ ] Never log secrets

### P0-9: Privacy Controls
- [ ] PII redaction
- [ ] Secret redaction
- [ ] Minimal retention
- [ ] Delete incident endpoint
- [ ] Clear memory endpoint
- [ ] Audit access log
- [ ] Only relevant context to external models

---

## P1 - Important (Should Complete)

### P1-1: Model Routing Abstraction
- [ ] Fast reasoning model (classification, summarization, metadata extraction)
- [ ] Deep reasoning model (hypotheses, root cause, remediation)
- [ ] Internal routing layer (mock-compatible)
- [ ] No live multi-model requirement

### P1-2: RAG 2.0 Enhancements
- [ ] Query normalization
- [ ] Metadata filtering
- [ ] Top-k configuration
- [ ] Relevance scoring with source type
- [ ] Retrieval reason logging
- [ ] Incident-memory retrieval
- [ ] Runbook/postmortem/config retrieval
- [ ] Only snippets to model context (not full docs)

### P1-3: RAG Security
- [ ] Prompt injection detection in retrieved content
- [ ] Flag suspicious material
- [ ] Strict separation: SYSTEM/USER/TOOLS/EVIDENCE/RETRIEVED_KNOWLEDGE
- [ ] Test cases: ignore instructions, reveal secrets, run shell, modify files, bypass verification

### P1-4: Incident NLP Intelligence
- [ ] Deterministic extraction: service, severity, environment, symptoms, components, dependencies, error patterns, timestamps, business impact, technical entities
- [ ] Optional AI enhancement
- [ ] No AI dependency for basic functionality

### P1-5: Hypothesis Engine Enhancements
- [ ] Confidence evolution tracking (history)
- [ ] UI shows confidence changes over time
- [ ] LLM cannot declare final verification

### P1-6: Root Cause Enhancements
- [ ] Candidate + confidence + supporting/contradicting evidence + reason + alternatives + validation requirement
- [ ] Must reference evidence IDs

### P1-7: Remediation Engine Enhancements
- [ ] Configuration diff display
- [ ] Risk levels: LOW/MEDIUM/HIGH
- [ ] Approval requirement: LOW auto, MEDIUM/HIGH human approval
- [ ] Validation criteria per remediation

### P1-8: Incident Memory Expansion
- [ ] Persist: user_id, service, incident, symptoms, evidence, root cause, remediation, verification, knowledge sources, research, timestamps
- [ ] Similar incident search with similarity score
- [ ] Show: similarity, previous root cause, previous fix, previous verification

### P1-9: Voice Assistant
- [ ] Web Speech API + SpeechSynthesis (browser-native)
- [ ] Deterministic intent parsing first
- [ ] Optional LLM interpretation when live
- [ ] Allowlisted commands only
- [ ] UI states: LISTENING, THINKING, EXECUTING, COMPLETE
- [ ] Microphone NOT always-on

### P1-10: Voice → Agent Integration
- [ ] "Investigate payment pool exhaustion" → launches full scenario
- [ ] Voice cannot bypass safety

### P1-10: TEE / Trusted Execution Abstraction
- [ ] TrustedExecutionProvider interface
- [ ] LocalSafeTrustedExecutionProvider implementation
- [ ] AttestedTEEProvider stub
- [ ] UI: "Execution Trust: Local Safe" / "Attestation: UNAVAILABLE"
- [ ] Only show "TEE VERIFIED" with actual attestation evidence

### P1-11: Cost / Latency Tracking
- [ ] Track: provider, model, latency, tokens, estimated cost, Tavily calls, cache hits/misses
- [ ] Never show credentials

---

## P2 - Nice to Have

### P2-1: Deployment Artifacts
- [ ] Dockerfile (FastAPI + built frontend)
- [ ] docker-compose.yml
- [ ] Production env example
- [ ] Health/readiness/liveness endpoints

### P2-2: PowerShell Wrapper
- [ ] `scripts/coska.ps1` with commands: doctor, seed, reset, test, build, backend, frontend, dev, demo, judge, security, health, audit, package, final-check, stop

### P2-3: Documentation Completion
- [ ] README with: Problem, Solution, Agentic workflow, RAG, Incident Memory, Evidence Graph, NVIDIA Nemotron, Nebius, Tavily, Sandbox, Deterministic Verification, Security, Setup, Judge Mode, Deployment
- [ ] All docs/ files complete
- [ ] Core explanation: LLM REASONS / TOOLS ACT / VERIFIER DECIDES

### P2-4: Dependency Audit
- [ ] pip-audit
- [ ] npm audit
- [ ] Fix compatible high-value vulnerabilities only

### P2-5: Additional Tests
- [ ] Auth tests
- [ ] Session tests
- [ ] Tenant isolation tests
- [ ] Rate limiting tests
- [ ] Validation tests
- [ ] SSRF tests
- [ ] Prompt injection tests
- [ ] Voice command parsing tests
- [ ] TEE status abstraction tests
- [ ] RAG tests
- [ ] Planner tests
- [ ] Verification tests
- [ ] Secret redaction tests
- [ ] Path traversal tests

---

## Completed (Baseline)

- [x] 43/43 backend tests passing
- [x] 24/24 evaluation checks passing
- [x] Frontend TypeScript clean
- [x] Frontend production build
- [x] 8/8 health checks passing
- [x] 9/11 doctor checks passing (2 Docker WARN)
- [x] Security scan (no CRITICAL in code)
- [x] Mock provider working
- [x] Nebius/Tavily providers integrated
- [x] 6 demo scenarios working
- [x] Judge Mode functional
- [x] Verification receipt
- [x] Evidence graph
- [x] Service map / blast radius
- [x] Agentic planner
- [x] Incident intelligence
- [x] BM25 RAG with 20 runbooks
- [x] LocalSafe + Docker sandbox
- [x] Security scanner

---

## Current Sprint Focus

**Week 1:** P0-1 through P0-9 (Security & Auth Foundation)
**Week 2:** P1-1 through P1-11 (AI/RAG/Voice/TEE)
**Week 3:** P2-1 through P2-5 (Deployment & Polish)
**Week 3 End:** Final validation & submission