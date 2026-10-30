"""AI Provider abstraction for COSKA runtime.

Provides a unified interface for model reasoning via Nebius Token Factory
(NVIDIA Nemotron models) and deterministic MockAIProvider for local testing.
"""
from abc import ABC, abstractmethod
import asyncio
import json
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import structlog

from app.config import get_settings

logger = structlog.get_logger()


# =============================================================================
# Explicit Provider Error States
# =============================================================================

class ProviderError(Exception):
    """Base class for all AI provider errors."""
    def __init__(self, message: str, status: str = "PROVIDER_ERROR", status_code: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.status_code = status_code


class ProviderNotConfiguredError(ProviderError):
    def __init__(self, message: str = "AI Provider is not configured"):
        super().__init__(message, status="PROVIDER_NOT_CONFIGURED", status_code=500)


class ProviderUnauthorizedError(ProviderError):
    def __init__(self, message: str = "Invalid credentials for AI provider"):
        super().__init__(message, status="PROVIDER_UNAUTHORIZED", status_code=401)


class ProviderRateLimitedError(ProviderError):
    def __init__(self, message: str = "Rate limit exceeded (HTTP 429)"):
        super().__init__(message, status="PROVIDER_RATE_LIMITED", status_code=429)


class ProviderUnavailableError(ProviderError):
    def __init__(self, message: str = "AI provider service is unavailable", status_code: Optional[int] = 503):
        super().__init__(message, status="PROVIDER_UNAVAILABLE", status_code=status_code)


class ModelUnavailableError(ProviderError):
    def __init__(self, message: str = "Requested model is unavailable"):
        super().__init__(message, status="MODEL_UNAVAILABLE", status_code=404)


class ProviderInvalidResponseError(ProviderError):
    def __init__(self, message: str = "Malformed or empty response from AI provider"):
        super().__init__(message, status="PROVIDER_INVALID_RESPONSE", status_code=502)


# =============================================================================
# Provider Models & Interface
# =============================================================================

@dataclass
class ProviderInfo:
    """Provider metadata and health information."""
    name: str
    model: str
    base_url: str
    display_name: str = ""
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


# =============================================================================
# Mock Provider Implementation
# =============================================================================

class MockAIProvider(AIProvider):
    """Deterministic mock provider supporting the full COSKA workflow."""

    def __init__(self, model: str = "nvidia/nemotron-3-ultra-550b-a55b"):
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
        """Return deterministic mock responses based on message content."""
        self.call_count += 1
        self.last_messages = messages

        system_msg = ""
        for m in messages:
            if m.get("role") == "system":
                system_msg = m.get("content", "").lower()
                break
        last_msg = messages[-1].get("content", "").lower() if messages else ""
        all_text = " ".join([m.get("content", "") for m in messages]).lower()

        # 1. Remediation planner: system message indicates remediation OR prompt specifically requests remediation plan
        if "remediation" in system_msg or "generating a remediation plan" in last_msg or "generate a specific, validated remediation" in last_msg:
            return self._mock_remediation(all_text)

        # 2. Hypothesis generation: system message indicates hypotheses OR prompt requests competing hypotheses
        if "hypothes" in system_msg or "competing root cause hypotheses" in last_msg or "current hypotheses:" in last_msg or "return as json array" in last_msg:
            return self._mock_hypotheses(all_text)

        # 3. Root cause reasoning: system message indicates root cause OR prompt tasks root cause determination
        if "root cause analyst" in system_msg or "performing root cause analysis" in last_msg or "determine the root cause" in last_msg or "root_cause" in last_msg or "root cause" in last_msg:
            return self._mock_root_cause(all_text)

        # Default structured response
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({"status": "acknowledged", "model": self.model}),
                    "role": "assistant"
                }
            }],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        }

    def _mock_hypotheses(self, context: str) -> Dict[str, Any]:
        """Generate competing hypotheses tailored to scenario context."""
        if "retry" in context or "504" in context or "gateway" in context:
            hypotheses = [
                {
                    "title": "Upstream timeout and excessive retry storm",
                    "description": "High retry count (RETRY_COUNT=10) combined with short timeout (5s) causes cascading worker exhaustion during upstream latency spikes.",
                    "supporting_evidence_ids": ["E-1", "E-2"],
                    "contradicting_evidence_ids": [],
                    "confidence": 0.88,
                    "next_investigation_action": "inspect_configuration:RETRY_COUNT",
                    "status": "SUPPORTED"
                },
                {
                    "title": "Database connection pool exhaustion",
                    "description": "Worker threads locked waiting for DB connections under concurrent retry load",
                    "supporting_evidence_ids": [],
                    "contradicting_evidence_ids": ["E-1"],
                    "confidence": 0.15,
                    "next_investigation_action": "inspect_configuration:DB_POOL_SIZE",
                    "status": "WEAKENED"
                },
                {
                    "title": "Network partition with payment gateway",
                    "description": "Total network disconnect between service and upstream payment processor",
                    "supporting_evidence_ids": [],
                    "contradicting_evidence_ids": ["E-2"],
                    "confidence": 0.05,
                    "next_investigation_action": "inspect_runtime:network_status",
                    "status": "WEAKENED"
                },
                {
                    "title": "Application memory leak",
                    "description": "Garbage collection pauses triggering connection timeouts",
                    "supporting_evidence_ids": [],
                    "contradicting_evidence_ids": ["E-1", "E-2"],
                    "confidence": 0.02,
                    "next_investigation_action": "inspect_runtime:memory_usage",
                    "status": "REJECTED"
                }
            ]
        else:
            # Default payment-api pool exhaustion scenario
            hypotheses = [
                {
                    "title": "Database connection pool exhaustion",
                    "description": "Application cannot acquire database connections due to undersized pool configuration (DB_POOL_SIZE=5)",
                    "supporting_evidence_ids": ["E-1", "E-2", "E-3"],
                    "contradicting_evidence_ids": [],
                    "confidence": 0.91,
                    "next_investigation_action": "inspect_configuration:DB_POOL_SIZE",
                    "status": "SUPPORTED"
                },
                {
                    "title": "Database server saturation",
                    "description": "Database server CPU/memory/disk saturated causing slow responses and timeouts",
                    "supporting_evidence_ids": [],
                    "contradicting_evidence_ids": ["E-1", "E-2"],
                    "confidence": 0.08,
                    "next_investigation_action": "inspect_runtime:database_metrics",
                    "status": "WEAKENED"
                },
                {
                    "title": "Network instability",
                    "description": "Network packet loss between application and database causing connection failures",
                    "supporting_evidence_ids": [],
                    "contradicting_evidence_ids": ["E-1"],
                    "confidence": 0.05,
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

    def _mock_root_cause(self, context: str) -> Dict[str, Any]:
        """Generate structured root cause analysis."""
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
        return {
            "choices": [{
                "message": {"content": json.dumps(root_cause, separators=(',', ':')), "role": "assistant"}
            }],
            "usage": {"prompt_tokens": 300, "completion_tokens": 400, "total_tokens": 700}
        }

    def _mock_remediation(self, context: str) -> Dict[str, Any]:
        """Generate structured remediation plan."""
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
            model="coska-deterministic-mock",
            display_name="Deterministic Mock Provider",
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


# =============================================================================
# Nebius Token Factory Provider Implementation
# =============================================================================

class NebiusTokenFactoryProvider(AIProvider):
    """Production-ready Nebius Token Factory provider with bounded retry and error states."""

    MAX_RETRIES = 2
    RETRY_BACKOFFS = [1.0, 2.0]

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
            if not self.api_key or self.api_key == "your_nebius_token_factory_api_key_here":
                raise ProviderNotConfiguredError("NEBIUS_API_KEY is not configured or is a placeholder")
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
        """Send chat completion request with bounded 429 retries and explicit error handling."""
        import httpx

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

        retries = 0
        while True:
            try:
                response = await self.client.post("/chat/completions", json=payload)

                # HTTP 429: Bounded retry
                if response.status_code == 429:
                    if retries < self.MAX_RETRIES:
                        backoff = self.RETRY_BACKOFFS[retries]
                        logger.warning("nebius_rate_limited_retrying", retry=retries + 1, backoff=backoff)
                        await asyncio.sleep(backoff)
                        retries += 1
                        continue
                    else:
                        raise ProviderRateLimitedError("Rate limit exceeded on Nebius Token Factory after bounded retries")

                # HTTP 401 / 403: Unauthorized
                if response.status_code in (401, 403):
                    raise ProviderUnauthorizedError(f"Nebius authentication failed: HTTP {response.status_code}")

                # HTTP 404: Model not found
                if response.status_code == 404:
                    raise ModelUnavailableError(f"Model {self.model} not available on endpoint")

                # HTTP 5xx: Service unavailable
                if response.status_code >= 500:
                    raise ProviderUnavailableError(f"Nebius service unavailable: HTTP {response.status_code}", status_code=response.status_code)

                response.raise_for_status()

                try:
                    result = response.json()
                except Exception as e:
                    raise ProviderInvalidResponseError(f"Failed to parse JSON response: {e}")

                if not result or not result.get("choices"):
                    raise ProviderInvalidResponseError("Empty choices returned from model")

                logger.debug("nebius_response_received", model=self.model)
                return result

            except httpx.ConnectError as e:
                raise ProviderUnavailableError(f"Cannot connect to Nebius Token Factory: {e}")
            except httpx.TimeoutException as e:
                raise ProviderUnavailableError(f"Nebius Token Factory request timed out: {e}")
            except ProviderError:
                raise
            except Exception as e:
                raise ProviderError(f"Unexpected Nebius error: {e}")

    async def health_check(self) -> ProviderInfo:
        info = ProviderInfo(
            name="nebius",
            model=self.model,
            display_name="NVIDIA Nemotron via Nebius Token Factory",
            base_url=self.base_url
        )

        if not self.api_key or self.api_key == "your_nebius_token_factory_api_key_here":
            info.error = "PROVIDER_NOT_CONFIGURED"
            self._health_info = info
            return info

        try:
            await self.client.get("/models", timeout=5.0)
            info.reachable = True
        except Exception as e:
            info.error = f"PROVIDER_UNAVAILABLE: {e}"
            self._health_info = info
            return info

        try:
            test_result = await self.test_inference()
            info.authenticated = test_result.get("success", False)
            info.inference_test = test_result.get("success", False)
            info.model_available = True
            if not info.authenticated:
                info.error = test_result.get("error", "PROVIDER_UNAUTHORIZED")
        except Exception as e:
            info.error = str(e)

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


# =============================================================================
# Factory and Registry
# =============================================================================

def create_provider(provider_type: str = "auto", **kwargs) -> AIProvider:
    """Factory function to create AI provider based on configuration."""
    model = kwargs.get("model") or get_settings().nebius_model

    if provider_type == "mock":
        return MockAIProvider(model=model)

    if provider_type == "nebius":
        api_key = kwargs.get("api_key")
        if not api_key or api_key == "your_nebius_token_factory_api_key_here":
            logger.warning("nebius_api_key_missing_falling_back_to_mock")
            return MockAIProvider(model=model)
        return NebiusTokenFactoryProvider(
            api_key=api_key,
            base_url=kwargs.get("base_url") or get_settings().nebius_base_url,
            model=model
        )

    # Auto-detect: if valid api key present, use nebius, else fallback to mock
    if provider_type == "auto":
        api_key = kwargs.get("api_key") or kwargs.get("nebius_api_key") or get_settings().nebius_api_key
        if api_key and api_key != "your_nebius_token_factory_api_key_here":
            return NebiusTokenFactoryProvider(
                api_key=api_key,
                base_url=kwargs.get("base_url") or get_settings().nebius_base_url,
                model=model
            )
        return MockAIProvider(model=model)

    raise ValueError(f"Unknown provider type: {provider_type}")


_provider_instance: Optional[AIProvider] = None


def get_provider(provider_type: Optional[str] = None, **kwargs) -> AIProvider:
    """Get or create singleton provider instance based on settings."""
    global _provider_instance

    if _provider_instance is not None and provider_type is None:
        return _provider_instance

    settings = get_settings()
    active_type = provider_type or settings.ai_provider

    provider_kwargs = {
        "api_key": kwargs.get("api_key", settings.nebius_api_key),
        "base_url": kwargs.get("base_url", settings.nebius_base_url),
        "model": kwargs.get("model", settings.nebius_model),
    }

    instance = create_provider(active_type, **provider_kwargs)
    if provider_type is None:
        _provider_instance = instance
    return instance
