# RULES.md - COSKA Engineering Rules

## Absolute Rules (Never Violate)

### Security
1. **NO SECRETS** - Never commit API keys, passwords, tokens to git
2. **NO ARBITRARY SHELL** - Model cannot execute shell commands; only allowlisted tools
3. **NO UNRESTRICTED FILE WRITES** - All writes canonical-path checked, workspace-contained
4. **NO FAKE VERIFICATION** - VERIFIED only via deterministic 3-stage verification
5. **NO FALSE PROVIDER CLAIMS** - Mock never claims to be Nemotron/Nebius
6. **NO INFINITE AGENT LOOPS** - Safety budgets (steps, tools, time, retries) enforced
7. **NO UNCONTROLLED EXTERNAL API** - Only Tavily via search_web tool; Nebius via provider

### Verification
8. **VERIFIER IS FINAL** - No LLM override of verdict
9. **CONTROL TEST REQUIRED** - Failure must return when fix reverted
10. **BASELINE MUST FAIL** - Incident must reproduce before fix

### Architecture
11. **NO MICROSERVICES** - Single FastAPI + React deployment
12. **NO KUBERNETES** - Simple deployment (Docker Compose or single container)
13. **NO REWRITES** - Extend, don't replace existing working code

### Data
14. **USER ISOLATION** - All tables have user_id; queries scoped to authenticated user
15. **SECRET REDACTION** - Logs/errors/responses never contain secrets
16. **INPUT VALIDATION** - Pydantic on all endpoints; reject oversized/malformed

### Testing
17. **OFFLINE TESTS** - pytest never calls real Nebius/Tavily
18. **MOCK FIRST** - All features work with AI_PROVIDER=mock

---

## Coding Standards

### Python (Backend)
- Type hints on all functions
- Pydantic models for all data
- Structured logging with structlog
- Async/await throughout
- No global mutable state (use dependency injection)

### TypeScript (Frontend)
- Strict mode, no implicit any
- Shared types in `types/incident.ts`
- React hooks for state
- Axios for API with typed responses
- Lucide icons only

### Git
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- No direct commits to main (PRs preferred)
- No secrets in history

---

## Safe Modification Patterns

### Adding New API Endpoint
```python
# backend/app/api/new_feature.py
from fastapi import APIRouter
router = APIRouter(prefix="/api/new-feature", tags=["new-feature"])
# Add endpoints with Pydantic models
# Register in backend/app/main.py
```

### Adding New Service
```python
# backend/app/services/new_service.py
class NewService:
    def __init__(self):
        pass
    async def do_something(self) -> Result:
        pass

# backend/app/services/__init__.py - export
# Use via dependency injection
```

### Adding New Tool
```python
# backend/app/tools/investigation.py
class NewTool(BaseTool):
    name = "new_tool"
    description = "Description"
    class Input(ToolInput):
        param: str
    async def execute(self, input: Input) -> ToolResult:
        pass

# Register in register_all_tools()
```

### Adding Frontend Page
```tsx
// frontend/src/pages/NewPage.tsx
export function NewPage() {
  // Use api.ts for calls
  // Use types from types/incident.ts
}

// Add route in App.tsx
<Route path="new-page" element={<NewPage />} />
```

### Extending Models
```python
# backend/app/models/__init__.py
class NewModel(BaseModel):
    field: str = Field(...)
# Use in services, API, storage
```

---

## High-Risk Operations (Require Extra Review)

| Operation | Risk | Mitigation |
|-----------|------|------------|
| Modify `orchestrator.py` | Breaks investigation flow | Run full evaluation harness |
| Modify `verifier.py` | Breaks causal verification | Run evaluation harness + manual verify |
| Modify `providers.py` | Breaks AI abstraction | Test both mock and nebius |
| Modify `storage.py` schema | Data loss/migration | Backup DB, test migrations |
| Modify `sandbox.py` | Security bypass | Run security_check.py |
| Modify `registry.py` | Tool injection | Audit allowlist |
| Change safety budgets | Infinite loops | Run stress tests |
| Add external API call | Uncontrolled network | Add to allowlist, rate limit |

---

## Definition of Done (Per Feature)

- [ ] Backend tests pass (`pytest -q`)
- [ ] Frontend TypeScript clean (`npx tsc --noEmit`)
- [ ] Frontend builds (`npm run build`)
- [ ] Health checks pass (`python scripts/healthcheck.py`)
- [ ] Doctor passes (`python scripts/coska_doctor.py`)
- [ ] Security scan clean (`python scripts/security_check.py`)
- [ ] Evaluation harness passes (`python scripts/evaluate_coska.py`)
- [ ] Documentation updated (relevant .md files)
- [ ] No secrets in changes
- [ ] TypeScript types match backend models

---

## Environment Rules

| Variable | Default | Allowed Values |
|----------|---------|----------------|
| `AI_PROVIDER` | `mock` | `mock`, `nebius`, `auto` |
| `TAVILY_ENABLED` | `false` | `true`, `false` |
| `NEBIUS_API_KEY` | `""` | Valid Token Factory key |
| `TAVILY_API_KEY` | `""` | Valid Tavily key |
| `AUTH_REQUIRED` | `false` | `true`, `false` |
| `SANDBOX_MODE` | `local` | `local`, `docker`, `auto` |

---

## Demo Rules

1. **6 Canonical Scenarios Only** - No ad-hoc scenarios in evaluation
2. **Expected Outcomes Fixed** - VERIFIED with specific root cause/remediation
3. **Mock Provider Default** - Demo works without API keys
4. **Judge Mode = Canonical Path** - Payment Pool Exhaustion scenario
5. **No Live Calls in CI** - Evaluation uses mock provider