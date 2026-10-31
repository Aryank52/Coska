"""Tavily client for web research - backward compatibility wrapper.

This module provides a backward-compatible wrapper around the ResearchProvider abstraction.
"""
import httpx
import structlog
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.services.research import get_research_provider, ResearchResponse

logger = structlog.get_logger()


class TavilyClient:
    """Backward-compatible wrapper around the ResearchProvider abstraction."""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.tavily_api_key
        self.base_url = "https://api.tavily.com"
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("your_"))

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Content-Type": "application/json"},
                timeout=httpx.Timeout(15.0, connect=5.0),
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=5),
        stop=stop_after_attempt(2),
        reraise=True
    )
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search the web using Tavily (backward compatibility)."""
        if not self.is_configured:
            return {
                "status": "TAVILY_NOT_CONFIGURED",
                "query": query,
                "results": [],
                "answer": None
            }
        
        # Use the research provider abstraction
        research_provider = get_research_provider("external" if self.is_configured else "mock")
        response = await research_provider.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_domains=include_domains,
            exclude_domains=exclude_domains,
        )
        
        # Convert ResearchResponse to legacy format
        return {
            "status": response.status,
            "query": response.query,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "content": r.snippet,
                    "score": r.score,
                    "source": r.source
                }
                for r in response.results
            ],
            "answer": response.answer,
            "usage": response.usage
        }
    
    async def health_check(self) -> bool:
        """Check if Tavily API is accessible."""
        try:
            if not self.is_configured:
                return False
            result = await self.search("test", max_results=1)
            return bool(result.get("results"))
        except Exception as e:
            logger.warning("tavily_health_check_failed", error=str(e))
            return False


# TavilyService alias for architecture consistency
TavilyService = TavilyClient


_tavily_client: Optional[TavilyClient] = None


def get_tavily_client() -> TavilyClient:
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient()
    return _tavily_client