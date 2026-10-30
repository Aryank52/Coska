# BRAIN.md - COSKA System Intelligence

## What the LLM Does

The LLM (via AI Provider abstraction) performs **reasoning-only** tasks:

### Phase 4: Hypothesis Generation
- Analyzes evidence to generate 3-5 competing root cause hypotheses
- Assigns confidence scores (0.0-1.0)
- Recommends next investigation actions
- Output: Structured JSON array

### Phase 6: Root Cause Analysis
- Synthesizes ALL evidence (logs, config, deployment, RAG, web research)
- Identifies single strongest root cause
- Lists supporting/contradicting evidence IDs
- Rejects alternative hypotheses with reasoning
- Assigns confidence (0.0-1.0)
- Recommends specific remediation
- Output: Structured JSON with root_cause, confidence, evidence_ids, rejected_hypotheses, recommended_remediation

### Phase 7: Remediation Planning
- Takes root cause + evidence
- Generates specific, validated remediation plan
- Includes: exact_change, expected_effect, risk, blast_radius, rollback_plan
- Output: Structured JSON

### RAG Enhancement
- When RAG documents retrieved, LLM uses them as context for hypothesis/root cause
- Documents are NOT treated as instructions - only as reference knowledge
- Retrieval reason logged for traceability

## What Tools Do

Tools perform **deterministic actions** - no LLM involved:

| Tool | Action | Deterministic |
|------|--------|---------------|
| `inspect_logs` | Regex pattern matching on incident logs | Yes |
| `inspect_configuration` | Parse .env/config for key values | Yes |
| `inspect_deployment` | Extract version, timestamp, changes | Yes |
| `inspect_runtime` | Return simulated metrics (CPU, memory, connections) | Yes |
| `inspect_repository` | Read repo files, return previews | Yes |
| `search_web` | Tavily API call, return structured results | Yes (API call) |
| `sandbox` | Execute remediation in isolated env | Yes |

**Tools never:** Execute arbitrary shell commands, access filesystem outside workspace, make LLM calls.

## What Is Deterministic (No LLM)

### Evidence Collection (Phase 2)
- Log analysis: regex patterns → structured Evidence objects
- Config analysis: regex patterns → Evidence objects
- Deployment analysis: regex patterns → Evidence objects
- **All evidence IDs, claims, confidence scores are deterministic**

### Timeline Building (Phase 3)
- Chronological ordering of events from evidence
- **Fully deterministic**

### Hypothesis Updates (Phase 5)
- Confidence updates based on evidence keyword matching
- Status transitions: ACTIVE → SUPPORTED/WEAKENED/REJECTED
- **Deterministic confidence math**

### Verification (Phase 8) - CORE DIFFERENTIATOR
```
VERIFIED IFF:
  Baseline FAIL     (incident reproduced without fix)
+ Post-Fix PASS     (tests pass with fix applied)
+ Health PASS       (service healthy with fix)
+ Control FAIL      (failure returns when fix reverted)
```
- **Zero LLM involvement**
- Sandbox executes actual code
- Deterministic pass/fail per stage
- Control test proves causality

### Incident Memory
- Similarity search: token overlap (Jaccard)
- **Deterministic similarity scoring**

### RAG Retrieval
- BM25 scoring (deterministic)
- Tokenization, scoring, ranking
- **Fully deterministic - no embeddings, no vector DB**

## What the Verifier Controls

The `Verifier` class (`backend/app/agent/verifier.py`) is the **authority** on verification:

1. **Controls sandbox execution** - applies fix, runs tests, reverts
2. **Determines verdict** - VERIFIED/FAILED/UNVERIFIED/INSUFFICIENT_EVIDENCE
3. **No LLM can override** - verdict is final
4. **Receipt generation** - creates auditable verification receipt

## What the Agent CANNOT Do

| Cannot Do | Enforced By |
|-----------|-------------|
| Execute arbitrary shell commands | Tool allowlist, command validation |
| Access files outside workspace | Path containment in sandbox |
| Declare "VERIFIED" without proof | Verifier controls verdict |
| Bypass safety limits | MAX_AGENT_STEPS, MAX_TOOL_CALLS, MAX_RETRIES, MAX_INVESTIGATION_TIME |
| Call external APIs without allowlist | Tool registry only |
| Modify production systems | Sandbox isolation (local_safe/Docker) |
| Store/reveal API keys | Provider abstraction, no key logging |
| Run infinite loops | Step/tool/time budgets enforced |
| Invent tools | Fixed tool registry |

## Agent Loop (Explicit)

```
GOAL: "Determine root cause and safely verify recovery"
  ↓
PLAN: Create investigation plan (steps, tools, dependencies, budgets)
  ↓
SELECT TOOL: Choose from allowlisted tools based on current hypothesis
  ↓
EXECUTE TOOL: Run deterministic tool with validated input
  ↓
OBSERVE: Receive structured tool result (success, evidence, metadata)
  ↓
UPDATE EVIDENCE: Add new evidence to investigation state
  ↓
UPDATE HYPOTHESES: Recalculate confidence, status based on new evidence
  ↓
REPLAN: If evidence contradicts, or tool fails, or budget allows → new plan
  ↓
STOP CONDITIONS:
  - Root cause identified with confidence ≥ 0.8
  - All hypotheses REJECTED/WEAKENED except one SUPPORTED
  - MAX_AGENT_STEPS reached
  - MAX_TOOL_CALLS reached
  - MAX_INVESTIGATION_TIME reached
  - Error limit exceeded
  ↓
VERIFY: If remediation exists → deterministic 3-stage verification
```

## Safety Budgets (Configurable)

| Limit | Default | Purpose |
|-------|---------|---------|
| `MAX_AGENT_STEPS` | 40 | Prevent infinite reasoning loops |
| `MAX_TOOL_CALLS` | 25 | Limit tool executions |
| `MAX_RETRIES` | 3 | Bound retry attempts |
| `MAX_INVESTIGATION_TIME` | 300s | Wall-clock timeout |

## Provider Abstraction

```python
AIProvider (ABC)
    ├── MockAIProvider          # Default, deterministic, offline
    └── NebiusTokenFactoryProvider  # Live, requires NEBIUS_API_KEY
```

**Switching:** `AI_PROVIDER=mock|nebius|auto` (env var only)

**Mock never claims to be Nemotron.** Returns `provider: "mock"`.

## RAG Security Model

Retrieved documents are **untrusted input**:
- Placed in `KNOWLEDGE` context section only
- Never in `SYSTEM` or `USER` instruction sections
- Marked with `source: "rag"` in evidence
- Prompt injection patterns detected and flagged
- Retrieval reason logged for audit

## Verification Receipt (Immutable)

```json
{
  "incident_id": "INC-...",
  "root_cause": "...",
  "remediation": { "exact_change": "DB_POOL_SIZE: 5 -> 30" },
  "baseline_test": "FAIL",
  "post_fix_tests": "PASS",
  "health_check": "PASS",
  "control_test": "FAIL",
  "verdict": "VERIFIED",
  "evidence_count": 18,
  "sandbox_provider": "local_safe",
  "ai_provider": "mock",
  "knowledge_sources": ["KB-RUNBOOK-001", ...],
  "web_research": [...],
  "timestamp": "2026-...",
  "receipt_id": "REC-...",
  "hash": "sha256(...)"
}
```