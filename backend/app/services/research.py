"""Research Provider abstraction for COSKA runtime.

Provides a unified interface for external web research via multiple providers:
- MockResearchProvider: Deterministic mock provider for development/testing
- LocalKnowledgeResearchProvider: Local knowledge base retrieval (offline)
- ExternalResearchProvider: External web search (Tavily, SerpAPI, etc.)

The core application must never require external web search.
Default: RESEARCH_PROVIDER=local
"""
from abc import ABC, abstractmethod
import asyncio
import httpx
import structlog
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.config import get_settings

logger = structlog.get_logger()


# =============================================================================
# Research Provider Models & Interface
# =============================================================================

@dataclass
class ResearchResult:
    """Single research result item."""
    title: str
    url: str
    snippet: str
    score: Optional[float] = None
    source: str = "web"


@dataclass
class ResearchResponse:
    """Response from research provider."""
    query: str
    results: List[ResearchResult]
    answer: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None
    status: str = "OK"
    error: Optional[str] = None


class ResearchProvider(ABC):
    """Abstract base class for research providers."""
    
    @abstractmethod
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> ResearchResponse:
        """Search the web or knowledge base."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if research provider is accessible."""
        pass
    
    @abstractmethod
    async def close(self):
        """Close provider connections."""
        pass


# =============================================================================
# Mock Research Provider (Default - No External Dependencies)
# =============================================================================

class MockResearchProvider(ResearchProvider):
    """Deterministic mock research provider for development/testing.
    
    Returns realistic mock results based on query keywords.
    Works fully offline - no external dependencies.
    """
    
    # Pre-defined mock results for common incident scenarios
    MOCK_RESULTS: Dict[str, List[Dict[str, Any]]] = {
        "connection pool": [
            {
                "title": "PostgreSQL Connection Pool Exhaustion Runbook",
                "url": "https://docs.example.com/runbooks/postgres-pool-exhaustion",
                "snippet": "Under high request concurrency, undersized connection pools cause queue starvation and HTTP 500 timeouts. Fix: Increase pool size.",
                "score": 0.94,
                "source": "runbook"
            },
            {
                "title": "PostgreSQL Connection Pool Exhaustion - Causes and Fixes",
                "url": "https://docs.example.com/guides/postgres-pool-sizing",
                "snippet": "Connection pool exhaustion occurs when all connections are in use. Configure pool size based on concurrent workers.",
                "score": 0.88,
                "source": "guide"
            },
        ],
        "retry storm": [
            {
                "title": "Upstream Timeout and Retry Storm Mitigation",
                "url": "https://docs.example.com/runbooks/retry-storm",
                "snippet": "Excessive retries without backoff create thundering herd. Implement exponential backoff with jitter and circuit breaker.",
                "score": 0.93,
                "source": "runbook"
            },
        ],
        "cache stampede": [
            {
                "title": "Cache Stampede Prevention Guide",
                "url": "https://docs.example.com/guides/cache-stampede",
                "snippet": "Thundering herd occurs when hot keys expire simultaneously. Use TTL jitter, mutex locks, or probabilistic early expiration.",
                "score": 0.91,
                "source": "guide"
            },
        ],
        "memory leak": [
            {
                "title": "Application Memory Leak Detection Guide",
                "url": "https://docs.example.com/guides/memory-leak",
                "snippet": "Unbounded caches and event listeners cause memory growth. Use LRU caches with TTL and weak references for callbacks.",
                "score": 0.89,
                "source": "guide"
            },
        ],
        "database saturation": [
            {
                "title": "Database Write Contention & Lock Runbook",
                "url": "https://docs.example.com/runbooks/db-write-locks",
                "snippet": "Undersized write pools cause transaction lock queues. Increase MAX_CONNECTIONS and reduce statement timeout.",
                "score": 0.93,
                "source": "runbook"
            },
        ],
        "deployment": [
            {
                "title": "Deployment Rollback Standard Operating Procedure",
                "url": "https://docs.example.com/runbooks/rollback-sop",
                "snippet": "Emergency procedures for config regressions and schema mismatches introduced during continuous delivery.",
                "score": 0.94,
                "source": "runbook"
            },
        ],
        "deployment config": [
            {
                "title": "Bad Deployment Configuration Regression Runbook",
                "url": "https://docs.example.com/runbooks/deployment-config-rollback",
                "snippet": "Post-deployment config regressions cause immediate failures. Verify config diffs and validate before promote.",
                "score": 0.92,
                "source": "runbook"
            },
        ],
        "default": [
            {
                "title": "General Troubleshooting Guide",
                "url": "https://docs.example.com/guides/troubleshooting",
                "snippet": "General incident troubleshooting methodology: observe, hypothesize, test, verify.",
                "score": 0.75,
                "source": "guide"
            },
        ]
    }
    
    def __init__(self):
        self.call_count = 0
    
    def _match_query(self, query: str) -> List[Dict[str, Any]]:
        """Match query to best mock results based on keywords."""
        query_lower = query.lower()
        
        # Check for specific keywords
        for keyword, results in self.MOCK_RESULTS.items():
            if keyword in query_lower:
                return results
        
        # Default fallback
        return self.MOCK_RESULTS["default"]
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> ResearchResponse:
        """Search the mock knowledge base."""
        self.call_count += 1
        
        logger.debug("mock_research_search", query=query, max_results=max_results)
        
        # Simulate small delay for realism
        await asyncio.sleep(0.05)
        
        matched = self._match_query(query)
        results = []
        
        for item in matched[:max_results]:
            results.append(ResearchResult(
                title=item["title"],
                url=item["url"],
                snippet=item["snippet"],
                score=item.get("score"),
                source=item.get("source", "knowledge_base")
            ))
        
        # Generate a mock answer
        answer = f"Based on {len(results)} retrieved documents, the most relevant information suggests: {results[0]['snippet'][:200]}..." if results else "No relevant information found."
        
        return ResearchResponse(
            query=query,
            results=results,
            answer=answer,
            usage={"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
            status="OK"
        )
    
    async def health_check(self) -> bool:
        """Mock provider is always healthy."""
        return True
    
    async def close(self):
        pass


# =============================================================================
# Local Knowledge Research Provider (Offline Knowledge Base)
# =============================================================================

class LocalKnowledgeResearchProvider(ResearchProvider):
    """Local knowledge base research provider (offline).
    
    Searches a local knowledge base of runbooks, postmortems, and guides.
    Uses BM25 or simple keyword matching for retrieval.
    """
    
    def __init__(self, knowledge_base_path: Optional[str] = None):
        self.knowledge_base_path = knowledge_base_path
        self.documents: List[Dict[str, Any]] = []
        self._load_knowledge_base()
    
    def _load_knowledge_base(self):
        """Load knowledge base from local files."""
        # This would load from local files in production
        # For now, use the same mock data as fallback
        self.documents = []
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> ResearchResponse:
        """Search local knowledge base."""
        # For now, delegate to mock provider
        mock = MockResearchProvider()
        return await mock.search(query, max_results, search_depth, include_domains, exclude_domains)
    
    async def health_check(self) -> bool:
        return True
    
    async def close(self):
        pass


# =============================================================================
# External Research Provider (Tavily, SerpAPI, etc.)
# =============================================================================

class ExternalResearchProvider(ResearchProvider):
    """External web research provider (Tavily, SerpAPI, etc.).
    
    This provider makes actual HTTP calls to external search APIs.
    Should be used only when explicitly enabled.
    """
    
    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.tavily.com",
        provider: str = "tavily"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.provider = provider
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
    
    async def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
    ) -> ResearchResponse:
        if not self.is_configured:
            return ResearchResponse(
                query=query,
                results=[],
                status="NOT_CONFIGURED",
                error="External research provider not configured"
            )
        
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
        
        logger.debug("external_research_search", query=query, max_results=max_results, provider=self.provider)
        
        try:
            response = await self.client.post("/search", json=payload)
            response.raise_for_status()
            result = response.json()
            
            results = []
            for item in result.get("results", [])[:5]:
                results.append(ResearchResult(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    snippet=item.get("content", "")[:300],
                    score=item.get("score"),
                    source=item.get("source", "web")
                ))
            
            return ResearchResponse(
                query=query,
                results=results,
                answer=result.get("answer"),
                usage=result.get("usage"),
                status="OK"
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403):
                return ResearchResponse(
                    query=query,
                    results=[],
                    status="UNAUTHORIZED",
                    error=str(e)
                )
            raise
    
    async def health_check(self) -> bool:
        if not self.is_configured:
            return False
        try:
            result = await self.search("test", max_results=1)
            return result.status == "OK"
        except Exception as e:
            logger.warning("external_research_health_check_failed", error=str(e))
            return False


# =============================================================================
# Factory and Registry
# =============================================================================

_research_provider: Optional[ResearchProvider] = None


def create_research_provider(provider_type: str = "auto", **kwargs) -> ResearchProvider:
    """Factory function to create research provider based on configuration."""
    
    if provider_type == "mock":
        return MockResearchProvider()
    
    if provider_type == "local":
        return LocalKnowledgeResearchProvider(
            knowledge_base_path=kwargs.get("knowledge_base_path")
        )
    
    if provider_type == "external":
        return ExternalResearchProvider(
            api_key=kwargs.get("api_key") or get_settings().tavily_api_key,
            base_url=kwargs.get("base_url") or "https://api.tavily.com",
            provider="tavily"
        )
    
    # Auto-detect
    if provider_type == "auto":
        settings = get_settings()
        if settings.tavily_enabled and settings.tavily_api_key:
            return ExternalResearchProvider(
                api_key=settings.tavily_api_key,
                provider="tavily"
            )
        return MockResearchProvider()
    
    raise ValueError(f"Unknown research provider type: {provider_type}")


_research_provider: Optional[ResearchProvider] = None


def get_research_provider(provider_type: Optional[str] = None, **kwargs) -> ResearchProvider:
    """Get or create singleton research provider instance based on settings."""
    global _research_provider
    
    if _research_provider is not None and provider_type is None:
        return _research_provider
    
    settings = get_settings()
    active_type = provider_type or getattr(settings, 'research_provider', 'mock')
    
    provider_kwargs = {
        "api_key": kwargs.get("api_key", getattr(settings, 'tavily_api_key', '')),
        "base_url": kwargs.get("base_url", "https://api.tavily.com"),
    }
    
    instance = create_research_provider(active_type, **provider_kwargs)
    if provider_type is None:
        _research_provider = instance
    return instance