"""Tavily client for web research."""
import httpx
import structlog
from typing import Dict, Any, List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings

logger = structlog.get_logger()


class TavilyClient:
    """Client for Tavily Search API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.tavily_api_key
        self.base_url = "https://api.tavily.com"
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Content-Type": "application/json"},
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None
    
    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
    )
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search the web using Tavily."""
        payload = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": True,
            "include_raw_content": False,
        }
        
        if include_domains:
            payload["include_domains"] = include_domains
        if exclude_domains:
            payload["exclude_domains"] = exclude_domains
        
        logger.debug("tavily_search", query=query, max_results=max_results)
        
        response = await self.client.post("/search", json=payload)
        response.raise_for_status()
        
        result = response.json()
        logger.debug("tavily_search_complete", query=query, result_count=len(result.get("results", [])))
        return result
    
    async def health_check(self) -> bool:
        """Check if Tavily API is accessible."""
        try:
            if not self.api_key:
                return False
            result = await self.search("test", max_results=1)
            return bool(result.get("results"))
        except Exception as e:
            logger.error("tavily_health_check_failed", error=str(e))
            return False


_tavily_client: Optional[TavilyClient] = None


def get_tavily_client() -> TavilyClient:
    global _tavily_client
    if _tavily_client is None:
        _tavily_client = TavilyClient()
    return _tavily_client