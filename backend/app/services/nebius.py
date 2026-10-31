"""AI Provider wrapper for backward compatibility.

This module provides a backward-compatible wrapper around the AI provider abstraction.
"""
import structlog
from typing import Any, Dict, List, Optional

from app.services.providers import get_provider, AIProvider
from app.config import get_settings

logger = structlog.get_logger()


class AIClient:
    """Backward-compatible wrapper around the AI provider abstraction."""
    
    def __init__(self):
        self.settings = get_settings()
        self._provider: Optional[AIProvider] = None
    
    @property
    def provider(self) -> AIProvider:
        if self._provider is None:
            self._provider = get_provider(
                provider_type=self.settings.ai_provider,
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_base_url,
                model=self.settings.ai_model
            )
        return self._provider
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Send chat completion request via provider."""
        return await self.provider.chat_completion(
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    async def health_check(self) -> bool:
        """Check if provider is healthy."""
        info = await self.provider.health_check()
        return info.reachable and info.authenticated and info.model_available and info.inference_test
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection with a simple prompt."""
        return await self.provider.test_inference()
    
    async def close(self):
        await self.provider.close()


# Backward-compatible singleton
_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client


# Backward compatibility aliases
NebiusClient = AIClient
get_nebius_client = get_ai_client