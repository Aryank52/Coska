# AGENT_TOOLS.md - COSKA Tool Registry Guide

## Tool Registry Overview

The tool registry is the **single source of truth** for all agent capabilities. The LLM CANNOT invent tools - it must select from this allowlist.

```python
# backend/app/tools/registry.py
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        return [tool.get_schema() for tool in self._tools.values()]
    
    async def execute(self, name: str, input_data: Dict[str, Any]) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(success=False, error=f"Tool '{name}' not found")
        validated = tool.validate_input(input_data)
        return await tool.execute(validated)
```

---

## Registered Tools (6 Total)

### 1. inspect_logs
**Purpose**: Analyze incident logs for error patterns, timeouts, stack traces, anomalies

```python
class InspectLogsTool(BaseTool):
    name = "inspect_logs"
    description = "Analyze incident logs for error patterns, timeouts, stack traces, and anomalies"
    
    class Input(ToolInput):
        incident_id: str
        pattern: Optional[str] = None
        max_lines: int = 1000

    class Output(ToolOutput):
        evidence: List[Dict[str, Any]]

# Input Example:
{
    "incident_id": "INC-A1B2C3D4",
    "pattern": "connection pool",
    "max_lines": 500
}

# Output Example:
{
    "success": true,
    "data": {
        "evidence": [
            {
                "id": "E-LOG-001",
                "source_type": "LOG",
                "claim": "Found 14 timestamped log entries spanning from 2026-10-29T10:15:23.456Z to 2026-10-29T10:15:30.001Z",
                "reference": "Log lines 1-14",
                "confidence": 0.9,
                "related_component": "logging",
                "raw_data": {"timestamp_count": 14, "first": "...", "last": "..."}
            },
            {
                "id": "E-LOG-002",
                "source_type": "LOG",
                "claim": "Error frequency analysis: ERROR (14), timeout (7)",
                "reference": "Log error pattern matching",
                "confidence": 0.85,
                "related_component": "error_handling",
                "raw_data": {"error_counts": {"ERROR": 14, "timeout": 7}}
            },
            {
                "id": "E-LOG-003",
                "source_type": "LOG",
                "claim": "Database connection pool exhaustion detected: 8 pool-related errors",
                "reference": "Database pool error pattern matching",
                "confidence": 0.95,
                "related_component": "database_connection_pool",
                "raw_data": {"pool_error_count": 8}
            }
        ]
    }
}
```

**Deterministic Patterns Extracted**:
- Timestamps (ISO 8601)
- Error types (ERROR, FATAL, CRITICAL, Exception, Timeout)
- Stack trace frames
- Service/component names
- Request/trace IDs
- Database pool exhaustion patterns
- HTTP status codes (5xx, 4xx)
- Repeated log lines (>3 occurrences)

---

### 2. inspect_configuration
**Purpose**: Extract and analyze configuration parameters from incident metadata

```python
class InspectConfigurationTool(BaseTool):
    name = "inspect_configuration"
    description = "Extract and analyze configuration parameters from incident metadata"
    
    class Input(ToolInput):
        incident_id: str
        config_keys: Optional[List[str]] = None

    class Output(ToolOutput):
        evidence: List[Dict[str, Any]]

# Input Example:
{
    "incident_id": "INC-A1B2C3D4",
    "config_keys": ["DB_POOL_SIZE", "DB_POOL_TIMEOUT"]
}

# Output Example:
{
    "success": true,
    "data": {
        "evidence": [
            {
                "id": "E-CFG-001",
                "source_type": "CONFIG",
                "claim": "Database connection pool size configured as 5",
                "reference": "DB_POOL_SIZE configuration",
                "confidence": 1.0,
                "related_component": "database_connection_pool",
                "raw_data": {"pool_size": 5}
            },
            {
                "id": "E-CFG-002",
                "source_type": "CONFIG",
                "claim": "Timeout configured as 5 seconds",
                "reference": "DB_POOL_TIMEOUT configuration",
                "confidence": 1.0,
                "related_component": "timeout_settings",
                "raw_data": {"timeout_seconds": 5}
            },
            {
                "id": "E-CFG-003",
                "source_type": "CONFIG",
                "claim": "Found 3 configuration parameters",
                "reference": "Configuration parameter extraction",
                "confidence": 0.7,
                "related_component": "configuration",
                "raw_data": {"parameters": {"DB_POOL_SIZE": "5", "DB_POOL_TIMEOUT": "5", "DATABASE_URL": "..."}}
            }
        ]
    }
}
```

**Extracted Patterns**:
- `DB_POOL_SIZE=5` → pool_size evidence
- `MAX_CONNECTIONS=100` → max_connections evidence
- `TIMEOUT=5` → timeout evidence
- All key=value pairs as raw data

---

### 3. inspect_deployment
**Purpose**: Analyze deployment metadata for version, timing, changes

```python
class InspectDeploymentTool(BaseTool):
    name = "inspect_deployment"
    description = "Analyze deployment metadata for version, timing, and changes"
    
    class Input(ToolInput):
        incident_id: str

    class Output(ToolOutput):
        evidence: List[Dict[str, Any]]

# Input Example:
{
    "incident_id": "INC-A1B2C3D4"
}

# Output Example:
{
    "success": true,
    "data": {
        "evidence": [
            {
                "id": "E-DEP-001",
                "source_type": "DEPLOYMENT",
                "claim": "Recent deployment version: 1.8.2",
                "reference": "Deployment version extraction",
                "confidence": 0.9,
                "related_component": "deployment",
                "raw_data": {"version": "1.8.2"}
            },
            {
                "id": "E-DEP-002",
                "source_type": "DEPLOYMENT",
                "claim": "Deployment occurred at 2026-10-29T10:10:00Z",
                "reference": "Deployment timestamp extraction",
                "confidence": 0.8,
                "related_component": "deployment",
                "raw_data": {"timestamp": "2026-10-29T10:10:00Z"}
            }
        ]
    }
}
```

**Extracted Patterns**:
- Version: `v1.8.2` or `1.8.2`
- Timestamps: `deployed at 2026-10-29T10:10:00Z`
- Changed components: `changed payment-api`

---

### 4. inspect_runtime
**Purpose**: Check runtime metrics (simulated for demo)

```python
class InspectRuntimeTool(BaseTool):
    name = "inspect_runtime"
    description = "Check runtime metrics like CPU, memory, connections, network"
    
    class Input(ToolInput):
        incident_id: str
        metrics: Optional[List[str]] = None

    class Output(ToolOutput):
        evidence: List[Dict[str, Any]]

# Input Example:
{
    "incident_id": "INC-A1B2C3D4",
    "metrics": ["active_connections", "cpu_usage"]
}

# Output Example:
{
    "success": true,
    "data": {
        "evidence": [
            {
                "id": "RUNTIME-INC-A1B2C3D4",
                "source_type": "RUNTIME",
                "claim": "Runtime metrics: active_db_connections=45, cpu_usage=23%, memory_usage=67%, network_latency=2ms",
                "reference": "Runtime monitoring system",
                "confidence": 0.7,
                "related_component": "runtime_monitoring",
                "raw_data": {
                    "active_connections": 45,
                    "cpu_percent": 23,
                    "memory_percent": 67,
                    "network_latency_ms": 2
                }
            }
        ]
    }
}
```

**Note**: Returns simulated metrics for demo. Production would connect to monitoring systems.

---

### 5. inspect_repository
**Purpose**: Analyze source code, configuration files, dependencies

```python
class InspectRepositoryTool(BaseTool):
    name = "inspect_repository"
    description = "Analyze source code, configuration files, and dependencies"
    
    class Input(ToolInput):
        incident_id: str
        paths: Optional[List[str]] = None

    class Output(ToolOutput):
        evidence: List[Dict[str, Any]]

# Input Example:
{
    "incident_id": "INC-A1B2C3D4",
    "paths": ["app/config.py", "app/main.py"]
}

# Output Example:
{
    "success": true,
    "data": {
        "evidence": [
            {
                "id": "REPO-app-config-py",
                "source_type": "REPOSITORY",
                "claim": "Repository file app/config.py: 245 chars",
                "reference": "Repository: app/config.py",
                "confidence": 0.8,
                "related_component": "source_code",
                "raw_data": {"file": "app/config.py", "size": 245, "preview": "DB_POOL_SIZE = 5\n..."}
            }
        ]
    }
}
```

**Default Paths Checked** (demo):
- `app/config.py`
- `app/main.py`
- `requirements.txt`

---

### 6. search_web (Tavily)
**Purpose**: Search external technical documentation, error patterns, best practices

```python
class SearchWebTool(BaseTool):
    name = "search_web"
    description = "Search external technical documentation, error patterns, and best practices"
    
    class Input(ToolInput):
        query: str
        max_results: int = 5

    class Output(ToolOutput):
        evidence: List[Dict[str, Any]]

# Input Example:
{
    "query": "PostgreSQL connection pool exhaustion troubleshooting",
    "max_results": 5
}

# Output Example:
{
    "success": true,
    "data": {
        "evidence": [
            {
                "id": "WEB-POST-001",
                "source_type": "WEB",
                "claim": "External research: Connection Pool Exhaustion: The Silent Killer | Database Performance - Connection pool exhaustion occurs when...",
                "reference": "https://example.com/pool-exhaustion",
                "confidence": 0.75,
                "related_component": "external_research",
                "raw_data": {
                    "title": "Connection Pool Exhaustion: The Silent Killer",
                    "url": "https://example.com/pool-exhaustion",
                    "snippet": "Connection pool exhaustion occurs when all connections..."
                }
            }
        ],
        "metadata": {"query": "PostgreSQL connection pool exhaustion troubleshooting", "results_count": 5}
    }
}
```

**Configuration**:
- `TAVILY_ENABLED=false` by default (mock mode)
- `TAVILY_API_KEY` required for live
- `search_depth=basic`, `max_results=3`, `include_usage=true` by default

---

## Tool Schemas (OpenAI Compatible)

```json
{
  "type": "function",
  "function": {
    "name": "inspect_logs",
    "description": "Analyze incident logs for error patterns, timeouts, stack traces, and anomalies",
    "parameters": {
      "type": "object",
      "properties": {
        "incident_id": {"type": "string"},
        "pattern": {"type": "string"},
        "max_lines": {"type": "integer", "default": 1000}
      },
      "required": ["incident_id"]
    }
  }
}
```

---

## Adding New Tools

### 1. Create Tool Class
```python
# backend/app/tools/investigation.py
class NewTool(BaseTool):
    name = "new_tool"
    description = "Description of what this tool does"
    
    class Input(ToolInput):
        incident_id: str
        param: str
    
    class Output(ToolOutput):
        evidence: List[Dict[str, Any]]
    
    async def execute(self, input_data: Input) -> ToolResult:
        # Deterministic logic here
        evidence = [...]
        return ToolResult(success=True, data={"evidence": evidence})
```

### 2. Register Tool
```python
# backend/app/tools/investigation.py
def register_all_tools() -> None:
    registry = get_tool_registry()
    # ... existing tools ...
    registry.register(NewTool())
```

### 3. Add to Planner Allowlist
The planner automatically discovers tools via `tool_registry.list_tools()`.

### 4. Add Tests
```python
# tests/test_tools.py
async def test_new_tool():
    tool = NewTool()
    result = await tool.execute(NewTool.Input(incident_id="INC-1", param="test"))
    assert result.success
    assert len(result.data["evidence"]) > 0
```

---

## Tool Execution Flow

```
1. Planner selects tool → tool_name + tool_input
    │
    ▼
2. Orchestrator._execute_investigation_action()
    │
    ▼
3. ToolRegistry.execute(tool_name, tool_input)
    │
    ▼
4. Tool.validate_input() → Pydantic validation
    │
    ▼
5. Tool.execute() → Deterministic execution
    │
    ▼
6. ToolResult(success, data, error, metadata)
    │
    ▼
7. Convert evidence dicts → Evidence objects
    │
    ▼
8. Add to investigation state
```

---

## Best Practices

| Principle | Implementation |
|-----------|----------------|
| **Deterministic** | Same input → same output (no randomness) |
| **Idempotent** | Multiple calls = same result |
| **Fast** | < 500ms typical execution |
| **Structured Output** | Evidence objects with IDs, types, confidence |
| **Error Handling** | ToolResult with success/error, never exceptions |
| **Validation** | Pydantic Input/Output models |
| **Timeouts** | Per-tool timeouts (default 30s) |
| **Logging** | Structured: `tool_executed`, `tool_execution_failed` |

---

## Testing Tools

```bash
# Run tool tests
python -m pytest tests/test_core.py::TestToolRegistry -v

# Manual test
python -c "
import asyncio
from app.tools.registry import get_tool_registry
from app.tools.investigation import register_all_tools

async def test():
    register_all_tools()
    registry = get_tool_registry()
    result = await registry.execute('inspect_logs', {'incident_id': 'INC-TEST'})
    print(result)

asyncio.run(test())
"
```

---

## Tool Metrics (Tracked)

| Metric | Purpose |
|--------|---------|
| `tool_executed` | Success/failure count per tool |
| `tool_call_count` | Per-investigation budget tracking |
| `duration_ms` | Performance monitoring |
| `evidence_count` | Evidence yield per tool |

---

## Security Checklist for New Tools

- [ ] Input validation via Pydantic
- [ ] No arbitrary shell commands
- [ ] Path containment if filesystem access
- [ ] No secret leakage in output
- [ ] Timeout enforcement
- [ ] Resource limits (memory/CPU)
- [ ] Structured logging
- [ ] Unit tests with mock data
- [ ] Integration test in evaluation harness