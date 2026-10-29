"""AI Provider abstraction for COSKA runtime."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import structlog

from app.config import get_settings

logger = structlog.get_logger()


@dataclass
class ProviderInfo:
    """Provider metadata and health information."""
    name: str
    model: str
    base_url: str
    reachable: bool = False
    authenticated: bool = False
    model_available: bool = False
    inference_test: bool = False
    error: Optional[str] = None


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Send chat completion request."""
        pass
    
    @abstractmethod
    async def health_check(self) -> ProviderInfo:
        """Check provider health and model availability."""
        pass
    
    @abstractmethod
    async def test_inference(self, prompt: str = "Reply with exactly: COSKA_NEBIUS_OK") -> Dict[str, Any]:
        """Test inference with a simple prompt."""
        pass
    
    @abstractmethod
    async def close(self):
        """Close provider connections."""
        pass


class MockAIProvider(AIProvider):
    """Mock provider for development and testing."""
    
    def __init__(self, model: str = "mock-model"):
        self.model = model
        self.call_count = 0
        self.last_messages: List[Dict] = []
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Return mock responses based on message content."""
        self.call_count += 1
        self.last_messages = messages
        
        # Analyze the last user message to provide contextual mock response
        last_msg = messages[-1]["content"] if messages else ""
        last_msg_lower = last_msg.lower()
        
        # Hypothesis generation mock (check for specific hypothesis generation prompt)
        if "Generate 3-5 competing" in last_msg:
            return self._mock_hypotheses()
        
        # Remediation mock (check for remediation planner prompt specifically)
        if "Generate a SPECIFIC, VALIDATED remediation" in last_msg:
            return self._mock_remediation()
        
        # Root cause analysis mock
        if "root cause" in last_msg_lower or "root_cause" in last_msg_lower:
            return self._mock_root_cause()
        
        # Generic hypothesis generation mock
        if "hypothes" in last_msg_lower:
            return self._mock_hypotheses()
        
        # Generic mock
        return {
            "choices": [{
                "message": {
                    "content": "Mock AI response for development.",
                    "role": "assistant"
                }
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        }
    
    def _mock_hypotheses(self) -> Dict[str, Any]:
        import json
        hypotheses = [
            {
                "title": "Database connection pool exhaustion",
                "description": "Application cannot acquire database connections due to undersized pool configuration (DB_POOL_SIZE=5)",
                "supporting_evidence_ids": ["E-1", "E-2", "E-3"],
                "contradicting_evidence_ids": [],
                "confidence": 0.91,
                "next_investigation_action": "inspect_configuration:DB_POOL_SIZE",
                "status": "ACTIVE"
            },
            {
                "title": "Database server saturation",
                "description": "Database server CPU/memory/disk saturated causing slow responses and timeouts",
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": ["E-1", "E-2"],
                "confidence": 0.05,
                "next_investigation_action": "inspect_runtime:database_metrics",
                "status": "WEAKENED"
            },
            {
                "title": "Network instability",
                "description": "Network issues between application and database causing connection failures",
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": ["E-1"],
                "confidence": 0.03,
                "next_investigation_action": "inspect_runtime:network_metrics",
                "status": "WEAKENED"
            },
            {
                "title": "Application memory pressure",
                "description": "Application memory exhaustion causing GC pauses and request failures",
                "supporting_evidence_ids": [],
                "contradicting_evidence_ids": ["E-1", "E-2", "E-3"],
                "confidence": 0.01,
                "next_investigation_action": "inspect_runtime:memory_usage",
                "status": "REJECTED"
            }
        ]
        return {
            "choices": [{
                "message": {"content": json.dumps(hypotheses), "role": "assistant"}
            }],
            "usage": {"prompt_tokens": 200, "completion_tokens": 300, "total_tokens": 500}
        }
    
    def _mock_root_cause(self) -> Dict[str, Any]:
        import json
        root_cause = {
            "root_cause": "Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)",
            "confidence": 0.92,
            "supporting_evidence_ids": ["E-1", "E-2", "E-3", "E-4"],
            "contradicting_evidence_ids": [],
            "rejected_hypotheses": [
                {"id": "H-2", "reason": "No evidence of database CPU/memory saturation"},
                {"id": "H-3", "reason": "No network timeout patterns in logs"},
                {"id": "H-4", "reason": "No memory pressure indicators in logs"}
            ],
            "uncertainty": None,
            "recommended_remediation": {
                "description": "Increase database connection pool size from 5 to 30 to handle concurrent request load",
                "exact_change": "DB_POOL_SIZE: 5 -> 30",
                "expected_effect": "Eliminate connection pool exhaustion and reduce HTTP 500 error rate to baseline",
                "risk": "LOW",
                "blast_radius": "SANDBOX_ONLY",
                "rollback_plan": "Revert DB_POOL_SIZE to 5 in configuration"
            }
        }
        # Return just the JSON without extra wrapper
        return {
            "choices": [{
                "message": {"content": json.dumps(root_cause), "role": "assistant"}
            }],
            "usage": {"prompt_tokens": 300, "completion_tokens": 400, "total_tokens": 700}
        }
    
    def _mock_remediation(self) -> Dict[str, Any]:
        import json
        remediation = {
            "type": "CONFIGURATION_CHANGE",
            "description": "Increase database connection pool size from 5 to 30 to handle concurrent request load",
            "exact_change": "DB_POOL_SIZE: 5 -> 30",
            "expected_effect": "Eliminate connection pool exhaustion and reduce HTTP 500 error rate to baseline",
            "risk": "LOW",
            "blast_radius": "SANDBOX_ONLY",
            "rollback_plan": "Revert DB_POOL_SIZE to 5 in configuration"
        }
        return {
            "choices": [{
                "message": {"content": json.dumps(remediation), "role": "assistant"}
            }],
            "usage": {"prompt_tokens": 200, "completion_tokens": 200, "total_tokens": 400}
        }
    
    async def health_check(self) -> ProviderInfo:
        return ProviderInfo(
            name="mock",
            model=self.model,
            base_url="mock://localhost",
            reachable=True,
            authenticated=True,
            model_available=True,
            inference_test=True
        )
    
    async def test_inference(self, prompt: str = "Reply with exactly: COSKA_NEBIUS_OK") -> Dict[str, Any]:
        if "COSKA_NEBIUS_OK" in prompt:
            return {
                "success": True,
                "model": self.model,
                "response": "COSKA_NEBIUS_OK",
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
            }
        return {
            "success": True,
            "model": self.model,
            "response": "Mock response",
            "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
        }
    
    async def close(self):
        pass


class NebiusTokenFactoryProvider(AIProvider):
    """Nebius Token Factory provider for Nemotron models."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.tokenfactory.us-central1.nebius.com/v1/",
        model: str = "nvidia/nemotron-3-ultra-550b-a55b"
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = None
        self._health_info: Optional[ProviderInfo] = None
    
    @property
    def client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(120.0, connect=10.0),
            )
        return self._client
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice or "auto"
        
        logger.debug("nebius_request", model=self.model, message_count=len(messages))
        
        response = await self.client.post("/chat/completions", json=payload)
        response.raise_for_status()
        
        result = response.json()
        logger.debug("nebius_response", model=self.model)
        return result
    
    async def health_check(self) -> ProviderInfo:
        info = ProviderInfo(
            name="nebius",
            model=self.model,
            base_url=self.base_url
        )
        
        # Test reachability
        try:
            await self.client.get("/models", timeout=10.0)
            info.reachable = True
        except Exception as e:
            info.error = f"Provider unreachable: {e}"
            self._health_info = info
            return info
        
        # Test authentication
        try:
            result = await self.chat_completion(
                messages=[{"role": "user", "content": "OK"}],
                max_tokens=5,
                temperature=0
            )
            info.authenticated = True
        except Exception as e:
            info.error = f"Authentication failed: {e}"
            self._health_info = info
            return info
        
        # Test model availability
        try:
            models_resp = await self.client.get("/models")
            models_data = models_resp.json()
            model_ids = [m.get("id", "") for m in models_data.get("data", [])]
            info.model_available = self.model in model_ids or any(self.model in m for m in model_ids)
        except Exception:
            # Some endpoints may not support /models
            info.model_available = True  # Assume available if auth works
        
        # Test inference
        try:
            test_result = await self.test_inference()
            info.inference_test = test_result.get("success", False)
            if not info.inference_test:
                info.error = test_result.get("error", "Inference test failed")
        except Exception as e:
            info.error = f"Inference test error: {e}"
        
        self._health_info = info
        return info
    
    async def test_inference(self, prompt: str = "Reply with exactly: COSKA_NEBIUS_OK") -> Dict[str, Any]:
        try:
            result = await self.chat_completion(
                messages=[
                    {"role": "system", "content": "You are COSKA, an autonomous incident intelligence system."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0
            )
            return {
                "success": True,
                "model": self.model,
                "response": result["choices"][0]["message"]["content"] if result.get("choices") else None,
                "usage": result.get("usage")
            }
        except Exception as e:
            logger.error("nebius_test_inference_failed", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None


def create_provider(provider_type: str = "auto", **kwargs) -> AIProvider:
    """Factory function to create AI provider based on configuration."""
    if provider_type == "mock":
        return MockAIProvider(kwargs.get("model", "mock-model"))
    
    if provider_type == "nebius":
        api_key = kwargs.get("api_key")
        if not api_key:
            logger.warning("nebius_api_key_missing_falling_back_to_mock")
            return MockAIProvider()
        return NebiusTokenFactoryProvider(
            api_key=api_key,
            base_url=kwargs.get("base_url", "https://api.tokenfactory.us-central1.nebius.com/v1/"),
            model=kwargs.get("model", "nvidia/nemotron-3-ultra-550b-a55b")
        )
    
    # Auto-detect: try nebius if key available, else mock
    if provider_type == "auto":
        api_key = kwargs.get("api_key") or kwargs.get("nebius_api_key")
        if api_key:
            return NebiusTokenFactoryProvider(
                api_key=api_key,
                base_url=kwargs.get("base_url", "https://api.tokenfactory.us-central1.nebius.com/v1/"),
                model=kwargs.get("model", "nvidia/nemotron-3-ultra-550b-a55b")
            )
        return MockAIProvider()
    
    raise ValueError(f"Unknown provider type: {provider_type}")


# Provider singleton for dependency injection
_provider_instance: Optional[AIProvider] = None


def get_provider(provider_type: Optional[str] = None, **kwargs) -> AIProvider:
    """Get or create provider instance based on settings."""
    global _provider_instance
    
    if _provider_instance is not None:
        return _provider_instance
    
    settings = get_settings()
    
    # Determine provider type
    if provider_type is None:
        provider_type = settings.ai_provider
    
    # Build kwargs from settings and overrides
    provider_kwargs = {
        "api_key": kwargs.get("api_key", settings.nebius_api_key),
        "base_url": kwargs.get("base_url", settings.nebius_base_url),
        "model": kwargs.get("model", settings.nebius_model),
    }
    
    _provider_instance = create_provider(provider_type, **provider_kwargs)
    return _provider_instance