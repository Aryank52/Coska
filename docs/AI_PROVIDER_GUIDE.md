# AI_PROVIDER_GUIDE.md - COSKA AI Provider Integration Guide

## Provider Abstraction

COSKA uses a clean provider abstraction - the agent code NEVER calls AI APIs directly.

```python
# backend/app/services/providers.py
class AIProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def health_check(self) -> ProviderInfo:
        pass
    
    @abstractmethod
    async def test_inference(self, prompt: str = "Reply with exactly: COSKA_NEBIUS_OK") -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def close(self):
        pass
```

---

## Providers

### 1. MockAIProvider (Default)

**Purpose**: Deterministic, offline, first-class implementation for development and testing

```python
class MockAIProvider(AIProvider):
    def __init__(self, model: str = "nvidia/nemotron-3-ultra-550b-a55b"):
        self.model = model
        self.call_count = 0
    
    async def chat_completion(self, messages, tools=None, tool_choice=None, temperature=0.1, max_tokens=4096):
        self.call_count += 1
        # Phase-aware deterministic responses
        system_msg = self._get_system_message(messages)
        last_msg = messages[-1]["content"].lower() if messages else ""
        all_text = " ".join([m["content"] for m in messages]).lower()
        
        # Phase 4: Hypothesis Generation
        if "hypothes" in system_msg or "competing root cause hypotheses" in last_msg:
            return self._mock_hypotheses(all_text)
        
        # Phase 6: Root Cause Analysis
        if "root cause analyst" in system_msg or "performing root cause analysis" in last_msg:
            return self._mock_root_cause(all_text)
        
        # Phase 7: Remediation Planning
        if "remediation" in system_msg or "generating a remediation plan" in last_msg:
            return self._mock_remediation(all_text)
        
        # Default
        return {
            "choices": [{"message": {"content": json.dumps({"status": "acknowledged"}), "role": "assistant"}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        }
```

#### Mock Response Patterns

| Phase | Trigger | Response |
|-------|---------|----------|
| Hypothesis Generation | "hypothes" in system OR "competing root cause hypotheses" in user | 4 structured hypotheses with confidence, evidence IDs, next actions |
| Root Cause | "root cause analyst" OR "performing root cause analysis" | Root cause JSON with confidence, evidence IDs, rejected hypotheses, remediation |
| Remediation | "remediation" in system OR "generating a remediation plan" | Remediation JSON with exact_change, risk, rollback_plan |

**Key Property**: Same input → Same output (deterministic)

---

### 2. NebiusTokenFactoryProvider (Live)

**Purpose**: Production AI via Nebius Token Factory (NVIDIA Nemotron models)

```python
class NebiusTokenFactoryProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.tokenfactory.us-central1.nebius.com/v1/",
        model: str = "nvidia/nemotron-3-ultra-550b-a55b"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            if not self.api_key or self.api_key == "your_nebius_token_factory_api_key_here":
                raise ProviderNotConfiguredError("NEBIUS_API_KEY not configured")
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout=httpx.Timeout(120.0, connect=10.0)
            )
        return self._client
    
    async def chat_completion(self, messages, tools=None, tool_choice=None, temperature=0.1, max_tokens=4096):
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"
        
        # Bounded retries on 429
        for attempt in range(3):
            response = await self.client.post("/chat/completions", json=payload)
            if response.status_code == 429:
                if attempt < 2:
                    await asyncio.sleep([1.0, 2.0][attempt])
                    continue
                raise ProviderRateLimitedError("Rate limit exceeded after retries")
            # ... handle other status codes
            return response.json()
```

#### Configuration
```bash
# Required for live integration
export NEBIUS_API_KEY=your_token_factory_key
export NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
export NEBIUS_MODEL=nvidia/nemotron-3-ultra-550b-a55b
export AI_PROVIDER=nebius
```

#### Model: NVIDIA Nemotron 3 Ultra (550B)
- **Parameters**: 550 billion
- **Context**: 4096 tokens (configurable)
- **Strengths**: Reasoning, code, structured output
- **Endpoint**: Nebius Token Factory (managed inference)

#### Error Handling
```python
class ProviderNotConfiguredError(ProviderError):      # NEBIUS_API_KEY missing
class ProviderUnauthorizedError(ProviderError):       # 401/403
class ProviderRateLimitedError(ProviderError):        # 429 after retries
class ProviderUnavailableError(ProviderError):        # 5xx / network
class ModelUnavailableError(ProviderError):           # 404 model
class ProviderInvalidResponseError(ProviderError):    # Malformed JSON
```

---

### 3. Factory & Singleton

```python
def create_provider(provider_type: str = "auto", **kwargs) -> AIProvider:
    if provider_type == "mock":
        return MockAIProvider(model=kwargs.get("model"))
    
    if provider_type == "nebius":
        return NebiusTokenFactoryProvider(
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url"),
            model=kwargs.get("model")
        )
    
    # Auto-detect
    if provider_type == "auto":
        api_key = kwargs.get("api_key") or get_settings().nebius_api_key
        if api_key and api_key != "your_nebius_token_factory_api_key_here":
            return NebiusTokenFactoryProvider(api_key=api_key, ...)
        return MockAIProvider(model=kwargs.get("model"))
    
    raise ValueError(f"Unknown provider type: {provider_type}")

# Singleton for app lifecycle
_provider_instance: Optional[AIProvider] = None

def get_provider(provider_type: Optional[str] = None, **kwargs) -> AIProvider:
    global _provider_instance
    if _provider_instance is not None and provider_type is None:
        return _provider_instance
    
    settings = get_settings()
    instance = create_provider(provider_type or settings.ai_provider, **{
        "api_key": kwargs.get("api_key", settings.nebius_api_key),
        "base_url": kwargs.get("base_url", settings.nebius_base_url),
        "model": kwargs.get("model", settings.nebius_model),
    })
    if provider_type is None:
        _provider_instance = instance
    return instance
```

---

## Backward Compatibility Layer

```python
# backend/app/services/nebius.py
class NebiusClient:
    """Backward-compatible wrapper around provider abstraction."""
    
    def __init__(self):
        self.settings = get_settings()
        self._provider: Optional[AIProvider] = None
    
    @property
    def provider(self) -> AIProvider:
        if self._provider is None:
            self._provider = get_provider(
                provider_type=self.settings.ai_provider,
                api_key=self.settings.nebius_api_key,
                base_url=self.settings.nebius_base_url,
                model=self.settings.nebius_model
            )
        return self._provider
    
    async def chat_completion(self, messages, tools=None, tool_choice=None, temperature=0.1, max_tokens=4096):
        return await self.provider.chat_completion(messages, tools, tool_choice, temperature, max_tokens)
    
    async def health_check(self) -> bool:
        info = await self.provider.health_check()
        return info.reachable and info.authenticated and info.model_available and info.inference_test
    
    async def test_connection(self) -> Dict[str, Any]:
        return await self.provider.test_inference()
    
    async def close(self):
        await self.provider.close()

# Singleton
_nebius_client: Optional[NebiusClient] = None
def get_nebius_client() -> NebiusClient:
    global _nebius_client
    if _nebius_client is None:
        _nebius_client = NebiusClient()
    return _nebius_client
```

---

## Usage in Agent Engines

```python
# backend/app/agent/hypotheses.py
class HypothesisEngine:
    def __init__(self):
        self.client = get_nebius_client()  # Uses provider abstraction
    
    async def refine_hypotheses_with_nemotron(self, incident, evidence, hypotheses):
        prompt = f"""You are COSKA...
        Evidence: {evidence_summary}
        Current Hypotheses: {hypotheses_summary}
        
        Generate 3-5 competing root cause hypotheses...
        Return as JSON array."""
        
        result = await self.client.chat_completion(
            messages=[
                {"role": "system", "content": "You are COSKA, an expert incident investigator..."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        # Parse JSON response...
```

---

## Switching Providers

### Development (Default)
```bash
# No configuration needed
AI_PROVIDER=mock
# Works immediately - no API keys needed
```

### Live Integration
```bash
# Set environment variables
export AI_PROVIDER=nebius
export NEBIUS_API_KEY=your_actual_token_factory_key
export NEBIUS_BASE_URL=https://api.tokenfactory.us-central1.nebius.com/v1/
export NEBIUS_MODEL=nvidia/nemotron-3-ultra-550b-a55b

# Run demo
python scripts/run_demo.py
```

### Auto-Detect
```bash
# AI_PROVIDER=auto (default in config)
# If NEBIUS_API_KEY is valid → Nebius
# Else → Mock
export AI_PROVIDER=auto
export NEBIUS_API_KEY=your_key
```

---

## Health Checks

```python
# GET /api/health/ai
{
    "status": "healthy",
    "provider": "mock",
    "model": "coska-deterministic-mock",
    "reachable": true,
    "authenticated": true,
    "model_available": true,
    "details": {
        "base_url": "mock://localhost",
        "inference_test": true,
        "error": null
    }
}

# Live:
{
    "status": "healthy",
    "provider": "nebius",
    "model": "nvidia/nemotron-3-ultra-550b-a55b",
    "reachable": true,
    "authenticated": true,
    "model_available": true,
    "details": {
        "base_url": "https://api.tokenfactory.us-central1.nebius.com/v1/",
        "inference_test": true,
        "error": null
    }
}
```

---

## Testing

### Mock Provider Tests (Offline)
```python
# tests/test_core.py
async def test_mock_provider_hypotheses():
    provider = MockAIProvider()
    result = await provider.chat_completion(
        messages=[{"role": "user", "content": "competing root cause hypotheses"}]
    )
    hypotheses = json.loads(result["choices"][0]["message"]["content"])
    assert len(hypotheses) >= 3
    assert all("confidence" in h for h in hypotheses)

async def test_mock_provider_deterministic():
    provider = MockAIProvider()
    r1 = await provider.chat_completion(messages=[{"role": "user", "content": "test"}])
    r2 = await provider.chat_completion(messages=[{"role": "user", "content": "test"}])
    assert r1 == r2  # Deterministic!
```

### Live Integration Tests (Manual)
```bash
# Requires NEBIUS_API_KEY
python scripts/test_nebius.py

# Tests:
# 1. Health check
# 2. Test inference (COSKA_NEBIUS_OK)
# 3. Chat completion
# 4. Rate limit handling
```

---

## Cost Tracking (Live Only)

```python
# In NebiusTokenFactoryProvider.chat_completion()
response = await self.client.post("/chat/completions", json=payload)
result = response.json()

# Extract usage
usage = result.get("usage", {})
logger.info("nebius_usage", 
    model=self.model,
    prompt_tokens=usage.get("prompt_tokens"),
    completion_tokens=usage.get("completion_tokens"),
    total_tokens=usage.get("total_tokens"),
    estimated_cost_usd=estimate_cost(usage)
)

def estimate_cost(usage: Dict) -> float:
    # Nebius Token Factory pricing (example)
    return (usage.get("prompt_tokens", 0) * 0.0001 + usage.get("completion_tokens", 0) * 0.0003) / 1000
```

---

## Best Practices

| Practice | Implementation |
|----------|---------------|
| **Mock First** | All development/testing uses MockAIProvider |
| **No Direct Calls** | All AI via `get_nebius_client()` → provider abstraction |
| **Structured Output** | Prompts request JSON, parse with validation |
| **Temperature Control** | 0.1 for reasoning, 0.3 for hypotheses |
| **Token Limits** | max_tokens=4096 for reasoning, 2000 for hypotheses |
| **Error Handling** | Explicit error types, bounded retries |
| **Cost Tracking** | Log usage per call, estimate cost |
| **Mock Parity** | Mock returns same structure as live |

---

## Troubleshooting

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| "Provider not configured" | NEBIUS_API_KEY missing or placeholder | Set valid key |
| "Rate limited" | 429 after 3 retries | Wait, check quota |
| "Model unavailable" | 404 on model | Check model name |
| "Invalid JSON" | Malformed response | Check prompt for structure |
| "Auth failed" | 401/403 | Verify API key |
| "Timeout" | >120s response | Increase timeout |