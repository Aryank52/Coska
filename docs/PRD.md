# PRD - Product Requirements Document

## Problem

**Production incidents are resolved too slowly and unsafely.**

- **Mean Time to Resolution (MTTR):** Hours to days for complex incidents
- **Root Cause Analysis:** Manual, error-prone, relies on tribal knowledge
- **Remediation Risk:** Fixes applied without verification cause regressions
- **Knowledge Loss:** Incident patterns not captured for future reference
- **Verification Gap:** No causal proof that fix actually resolved the incident

**Target Users:**
- SRE/Platform Engineers (primary)
- Incident Commanders
- Engineering Managers
- On-call Engineers

**User Pain:**
- "I spend 80% of incident time gathering logs/config, 20% reasoning"
- "I've applied fixes that made things worse because I couldn't verify safely"
- "We keep hitting the same issues - no organizational memory"
- "Management asks 'how do you know it's fixed?' - I can't prove it"

---

## Product Promise

**COSKA autonomously investigates incidents, proposes safe remediations, and causally verifies recovery.**

> **Investigate. Resolve. Verify.**

---

## Core Features

### 1. Autonomous Investigation (8 Phases)
| Phase | Description |
|-------|-------------|
| 1. Incident Intake | Ingest incident, extract structured intelligence |
| 2. Evidence Collection | Logs, config, deployment, runtime, repo analysis |
| 3. Timeline Building | Chronological event reconstruction |
| 4. Hypothesis Generation | 3-5 competing root cause hypotheses |
| 5. Investigation | Tool-driven evidence gathering per hypothesis |
| 6. Root Cause Analysis | Evidence synthesis → single root cause + confidence |
| 7. Remediation Planning | Specific fix + risk + rollback + validation criteria |
| 8. Deterministic Verification | 3-stage causal proof in sandbox |

### 2. Offline RAG Knowledge Base
- 20+ incident runbooks (PostgreSQL, retry storms, deployments, cache, memory, K8s, etc.)
- BM25 retrieval (deterministic, offline, no embeddings)
- Retrieval reason logged for traceability
- Postmortem & incident memory retrieval

### 3. Incident Memory
- Stores every verified incident
- Similarity search for new incidents
- Shows: previous root cause, fix, verification outcome

### 4. Evidence Graph
- Nodes: incident, evidence, hypotheses, root cause, remediation, verification
- Edges: supports, contradicts, caused_by, derived_from, verified_by
- Cytoscape.js visualization

### 5. Service Map & Blast Radius
- 12-service topology (client → gateway → APIs → DB/cache/external)
- Dependency types: critical/degraded/optional
- Blast radius calculation with error impact estimation

### 6. Judge Mode (Canonical Demo)
- One-click: "RUN SCENARIO"
- Payment Pool Exhaustion (canonical path)
- Visible agent trace with timestamps
- Verification receipt export

### 7. Secure Multi-Tenant Architecture
- Optional authentication (Argon2, HttpOnly cookies)
- User isolation on all tables
- Rate limiting, input validation, audit logging

---

## Impact

| Metric | Current | Target |
|--------|---------|--------|
| MTTR (complex incidents) | 2-8 hours | < 15 minutes |
| Root Cause Accuracy | ~60% (manual) | > 90% (autonomous) |
| Verification Confidence | Subjective | Causal proof (deterministic) |
| Knowledge Retention | Tribal | Institutional (incident memory) |
| Remediation Safety | Hope-based | Causal proof + rollback |

---

## Success Metrics (Hackathon Submission)

- ✅ 43/43 backend tests passing
- ✅ 24/24 evaluation harness checks passing
- ✅ Frontend TypeScript clean + production build
- ✅ 8/8 health checks passing
- ✅ Security scan clean (no secrets in code)
- ✅ Judge Mode: Payment Pool Exhaustion → VERIFIED
- ✅ 6 canonical scenarios all VERIFIED
- ✅ Offline RAG + deterministic verification working

---

## Non-Goals (Explicitly Out of Scope)

| Non-Goal | Reason |
|----------|--------|
| Microservices architecture | Hackathon scope; single deployable |
| Kubernetes deployment | Over-engineering for demo |
| Paid voice/TTS services | Browser-native Web Speech API only |
| Real TEE/hardware attestation | Abstraction only; no fake claims |
| Multi-model LLM routing (live) | Mock-compatible abstraction only |
| Vector database / embeddings | BM25 sufficient, deterministic, offline |
| Full auth system (production) | Optional; demo works without |
| Mobile app | Not in scope |
| Real-time collaboration | Single-user investigation model |
| Alerting/on-call integration | Post-hackathon |
| Fine-tuning models | Not needed; reasoning via prompts |
| Chat interface | Not a chatbot; structured investigation UI |