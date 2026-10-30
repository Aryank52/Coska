# COSKA Security

## Security Principles

COSKA is designed with security as a foundational concern. As an autonomous incident investigation system that executes remediations, it must never pose a risk to production systems.

## Secret Management

### Environment Variables
All secrets are stored in `.env` file (gitignored):
- `NEBIUS_API_KEY` - Nebius Token Factory authentication
- `TAVILY_API_KEY` - Tavily web research authentication
- `DATABASE_URL` - SQLite database path

### Frontend Isolation
- Frontend communicates **only** with backend API
- No API keys exposed to browser
- No direct AI provider calls from frontend
- CORS restricted to known origins

## Sandbox Execution Security

### Dual Sandbox Architecture
COSKA supports two isolated execution providers via `SandboxProvider`:

1. **Docker Sandbox (`DockerSandboxProvider`)**:
   - Remediation execution occurs in ephemeral Docker containers
   - Containers have:
     - No host network access (`network_mode: none` or isolated bridge)
     - No host filesystem access (bind-mounted temp directory only)
     - Memory limit: 512MB (configurable)
     - CPU limit: 1 core (configurable)
     - Execution timeout: 300 seconds (configurable)
     - No production credentials or environment variables
     - Guaranteed container cleanup on completion or failure

2. **Local Safe Sandbox (`LocalSafeSandboxProvider`)**:
   - Host fallback for environments where Docker Desktop is not present
   - Strict path traversal prevention: rejects all paths traversing outside repo root (`..`, absolute paths, symlinks)
   - Strict command allowlisting: permits only approved test/build runners (`pytest`, `python -m unittest`, `npm test`)
   - Environment sanitization: clears credentials (`*_KEY`, `*_SECRET`, `*_PASSWORD`, `*_TOKEN`, `AWS_*`, `GOOGLE_*`)
   - Enforced process timeouts
   - Guaranteed file rollback to capture clean state before and after execution

### Agent Safety Bounds
To prevent runaway execution and infinite loops:
- `MAX_AGENT_STEPS`: Max orchestrator steps (default: 20)
- `MAX_TOOL_CALLS`: Max tool executions per investigation (default: 15)
- `MAX_RETRIES`: Bounded retries for external providers (default: 2)
- `MAX_INVESTIGATION_TIME`: Wall-clock timeout (default: 180 seconds)
- When any bound is breached, the investigation terminates gracefully with status `INVESTIGATION_LIMIT_REACHED`.

### Command Allowlisting
Only these operations are permitted in sandbox:
1. Configuration file modifications (`.env`, `config.yaml`, etc.)
2. Test execution (`pytest`, `npm test`)
3. Health check HTTP requests
4. Application startup for verification

**Explicitly forbidden:**
- Arbitrary shell commands
- Package installation from untrusted sources
- Network access to external systems
- Filesystem access outside sandbox directory
- Process execution outside container

### Model Output Validation
All AI-generated remediations pass through validation:
```python
def validate_remediation(remediation):
    # 1. Check type is allowed
    # 2. Validate exact_change format
    # 3. Verify config key in allowlist
    # 4. Validate value ranges
    # 5. Require rollback_plan
    # 6. Enforce blast_radius = "SANDBOX_ONLY" for HIGH risk
```

### Allowlisted Configuration Keys
Only these configuration parameters can be modified:
- `DB_POOL_SIZE` (1-100)
- `MAX_CONNECTIONS` (1-500)
- `TIMEOUT` (1-300 seconds)
- `POOL_TIMEOUT` (1-60 seconds)

## API Security

### Authentication
- Development: No authentication (local only)
- Production: JWT/API key authentication recommended
- Rate limiting on investigation endpoints

### Input Validation
- All API inputs validated via Pydantic models
- SQL injection prevention via SQLAlchemy ORM
- XSS prevention via React's built-in escaping

### Error Handling
- Structured error responses (no stack traces in production)
- Logging without sensitive data
- Graceful degradation when AI providers unavailable

## Data Protection

### Incident Data
- Stored in local SQLite database
- No automatic cloud sync
- Incident memory stores only verified patterns (opt-in)

### Audit Logging
Every action recorded:
```json
{
  "run_id": "uuid",
  "incident_id": "INC-XXX",
  "step": "VERIFYING",
  "tool": "sandbox",
  "timestamp": "2026-10-29T...",
  "duration_ms": 1234,
  "status": "COMPLETED",
  "summary": "Applied fix and ran verification"
}
```

## Threat Model

### Threats Mitigated
| Threat | Mitigation |
|--------|------------|
| AI hallucination causing harmful action | Validation + sandbox + human approval gate |
| Prompt injection | Structured prompts, output validation |
| Sandbox escape | Docker isolation, no privileges |
| Secret leakage | Environment-only, gitignored, backend-only |
| Unauthorized API access | CORS, rate limiting, auth (prod) |
| Data exfiltration | No outbound network from sandbox |

### Residual Risks
1. **Model reasoning errors** - Mitigated by evidence traceability and verification
2. **Configuration drift** - Sandbox uses repo copy, not production
3. **Denial of service** - Timeouts and resource limits on all operations

## Compliance

- No PII processed (incidents are technical only)
- No data sent to third parties except AI providers (Nebius/NVIDIA, Tavily)
- Audit trail supports SOC 2 / ISO 27001 evidence requirements

## Incident Response

If a security issue is discovered:
1. Report via GitHub Security Advisories
2. Immediate patch for sandbox/validation bypasses
3. Rotate affected API keys
4. Audit recent investigations for anomalies