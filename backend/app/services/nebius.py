"""Nebius Token Factory provider wrapper for backward compatibility."""
import structlog
from typing import Any, Dict, List, Optional

from app.services.providers import get_provider, AIProvider
from app.config import get_settings

logger = structlog.get_logger()


class NebiusClient:
    """Backward-compatible wrapper around the AI provider abstraction."""
    
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
_nebius_client: Optional[NebiusClient] = None


def get_nebius_client() -> NebiusClient:
    global _nebius_client
    if _nebius_client is None:
        _nebius_client = NebiusClient()
    return _nebius_client