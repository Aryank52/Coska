"""Nebius Token Factory client for Nemotron model inference."""
import os
import json
from typing import Any, Dict, List, Optional
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger()


class NebiusClient:
    """Client for Nebius Token Factory API (OpenAI-compatible)."""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.nebius_base_url.rstrip("/")
        self.api_key = self.settings.nebius_api_key
        self.model = self.settings.nebius_model
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(120.0, connect=10.0),
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Send chat completion request to Nemotron."""
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
    
    async def health_check(self) -> bool:
        """Check if Nebius API is accessible."""
        try:
            # Try a simple completion
            result = await self.chat_completion(
                messages=[{"role": "user", "content": "Say 'OK' if you can hear me."}],
                max_tokens=10,
                temperature=0
            )
            return bool(result.get("choices"))
        except Exception as e:
            logger.error("nebius_health_check_failed", error=str(e))
            return False
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection with a simple prompt."""
        try:
            result = await self.chat_completion(
                messages=[
                    {"role": "system", "content": "You are COSKA, an autonomous incident intelligence system."},
                    {"role": "user", "content": "Explain what COSKA does in one sentence."}
                ],
                max_tokens=100,
                temperature=0.3
            )
            return {
                "success": True,
                "model": self.model,
                "response": result["choices"][0]["message"]["content"] if result.get("choices") else None,
                "usage": result.get("usage")
            }
        except Exception as e:
            logger.error("nebius_test_connection_failed", error=str(e))
            return {"success": False, "error": str(e)}


# Dependency injection
_nebius_client: Optional[NebiusClient] = None


def get_nebius_client() -> NebiusClient:
    global _nebius_client
    if _nebius_client is None:
        _nebius_client = NebiusClient()
    return _nebius_client