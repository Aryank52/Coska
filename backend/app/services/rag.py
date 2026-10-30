"""Offline RAG (Retrieval-Augmented Generation) knowledge engine for COSKA.

Provides deterministic runbook and post-mortem retrieval without external API dependencies.
Includes traceability features for evidence-backed reasoning.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import re
import math
from collections import Counter


class RAGDocument(BaseModel):
    id: str
    title: str
    category: str
    source: str
    summary: str
    content: str
    tags: List[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    snippet: str = ""
    # Traceability fields
    matched_terms: List[str] = Field(default_factory=list)
    match_reason: str = ""


class RAGSearchResult(BaseModel):
    """Result of a RAG search with traceability."""
    documents: List[RAGDocument]
    query: str
    query_tokens: List[str]
    trace: Dict[str, Any] = Field(default_factory=dict)

    def __len__(self):
        return len(self.documents)

    def __getitem__(self, idx):
        return self.documents[idx]

    def __iter__(self):
        return iter(self.documents)


# Expanded knowledge base with 20+ runbooks covering all demo scenarios
DEFAULT_RUNBOOKS: List[Dict[str, Any]] = [
    {
        "id": "KB-RUNBOOK-001",
        "title": "PostgreSQL Pool Exhaustion Runbook",
        "category": "database",
        "source": "docs/runbooks/database-pool-exhaustion.md",
        "summary": "Mitigation steps and diagnostics for SQLAlchemy/PostgreSQL connection pool exhaustion",
        "content": (
            "Symptoms: High HTTP 500 error rates, 'QueuePool limit of size 5 overflow 10 reached' errors, "
            "worker threads blocked on db connection acquisition, latency spikes after deployment. "
            "Root Cause: DB_POOL_SIZE undersized for concurrency spike or connection leaks. "
            "Verification: Check active connections vs pool limit. Inspect DB_POOL_SIZE in .env/config. "
            "Remediation: Increase DB_POOL_SIZE from 5 to 30. Tune POOL_TIMEOUT to 10s. "
            "Validation: Load test with 20+ concurrent workers. Verify 0 connection acquisition timeout errors."
        ),
        "tags": ["database", "postgres", "pool", "sqlalchemy", "db_pool_size", "connection pool", "500", "exhaustion"]
    },
    {
        "id": "KB-RUNBOOK-002",
        "title": "Upstream Timeout and Cascading Retry Storm Runbook",
        "category": "network",
        "source": "docs/runbooks/retry-storm-mitigation.md",
        "summary": "Mitigating cascading 504 gateway timeouts caused by unjittered exponential retries",
        "content": (
            "Symptoms: Cascading HTTP 504 Gateway Timeouts, queue buildup, upstream third-party service degradation. "
            "Root Cause: Excessive client retries (RETRY_COUNT >= 10) without exponential backoff or jitter creates a thundering herd. "
            "Verification: Inspect gateway logs for repeated requests for the same transaction ID within milliseconds. "
            "Remediation: Lower RETRY_COUNT from 10 to 3, add full jitter, and activate circuit breaker threshold at 50%. "
            "Validation: Simulate upstream latency spike; confirm circuit breaker trips and prevents cascading exhaustion."
        ),
        "tags": ["retry", "timeout", "504", "gateway", "circuit breaker", "upstream", "backoff", "retry_count", "thundering herd"]
    },
    {
        "id": "KB-RUNBOOK-003",
        "title": "Bad Deployment Configuration Regression Runbook",
        "category": "deployment",
        "source": "docs/runbooks/deployment-config-rollback.md",
        "summary": "Diagnosing post-release environment variable regressions and database authentication failures",
        "content": (
            "Symptoms: Immediate 100% or high 5xx failure rate immediately following a deployment or release tag. "
            "Root Cause: Misconfigured environment variables, invalid credentials, or changed database host port. "
            "Verification: Correlate deployment timestamp with first anomaly timestamp. Inspect deployment diff for .env changes. "
            "Remediation: Rollback to previous deployment artifact or correct invalid DB_USER/DB_PASSWORD credentials. "
            "Validation: Verify service health endpoint returns 200 OK and database ping succeeds."
        ),
        "tags": ["deployment", "regression", "auth", "config", "rollback", "credentials", "500", "environment"]
    },
    {
        "id": "KB-RUNBOOK-004",
        "title": "Redis Cache Stampede & Thundering Herd Runbook",
        "category": "cache",
        "source": "docs/runbooks/cache-stampede-prevention.md",
        "summary": "Preventing backend database saturation when high-traffic cache keys expire simultaneously",
        "content": (
            "Symptoms: Sudden spike in database CPU and IOPS when a hot cache key expires, high query response times. "
            "Root Cause: Cache stampede (thundering herd) where hundreds of concurrent requests simultaneously attempt to recompute the same key. "
            "Verification: Cache miss spike in metrics followed immediately by database slow query escalation. "
            "Remediation: Implement mutex locking / singleflight pattern or probabilistic early expiration (XFetch algorithm). "
            "Validation: Flush key under synthetic concurrent load and ensure only 1 recomputation query hits the database."
        ),
        "tags": ["cache", "redis", "stampede", "thundering herd", "saturation", "lock", "ttl", "singleflight"]
    },
    {
        "id": "KB-RUNBOOK-005",
        "title": "Application Memory Leak and GC Pause Runbook",
        "category": "runtime",
        "source": "docs/runbooks/memory-leak-gc.md",
        "summary": "Identifying uncollected heap allocations and garbage collection pauses causing health check timeouts",
        "content": (
            "Symptoms: Monotonically increasing RSS memory, periodic 10-30s latency spikes (GC stop-the-world), eventual OOM kill. "
            "Root Cause: Retained object references in global caches or event listeners without eviction. "
            "Verification: Inspect heap dump or memory metrics over time. Check dmesg for oom-killer invocations. "
            "Remediation: Apply bounded LRU cache with maxsize and TTL. Implement weak references for listener callbacks. "
            "Validation: Run soak test for 10,000 iterations; verify memory ceiling remains flat."
        ),
        "tags": ["memory", "leak", "oom", "garbage collection", "gc", "heap", "rss", "pause"]
    },
    {
        "id": "KB-RUNBOOK-006",
        "title": "Database Server Saturation & Missing Index Runbook",
        "category": "database",
        "source": "docs/runbooks/db-saturation-indexes.md",
        "summary": "Remediating sequential full-table scans causing 100% database CPU saturation",
        "content": (
            "Symptoms: Database CPU at 95-100%, disk IO queue depth elevated, queries taking >5s. "
            "Root Cause: Full table scan on large table due to missing composite index or unindexed foreign key column. "
            "Verification: Run EXPLAIN ANALYZE on top queries from pg_stat_statements. Look for 'Seq Scan'. "
            "Remediation: Add CREATE INDEX CONCURRENTLY on filtered columns. Increase work_mem temporarily. "
            "Validation: Re-run query with index; verify execution plan uses 'Index Scan' and latency drops below 10ms."
        ),
        "tags": ["database", "cpu", "saturation", "slow query", "index", "disk", "iops", "full table scan"]
    },
    {
        "id": "KB-RUNBOOK-007",
        "title": "Kubernetes Deployment Troubleshooting Guide",
        "category": "kubernetes",
        "source": "docs/runbooks/k8s-deployment-troubleshooting.md",
        "summary": "Diagnosing pod failures, CrashLoopBackOff, ImagePullBackOff, and resource quota issues",
        "content": (
            "Symptoms: Pods stuck in CrashLoopBackOff, ImagePullBackOff, Pending, or OOMKilled. "
            "Root Cause: Resource limits too low, missing secrets/configmaps, wrong image tag, or node resource exhaustion. "
            "Verification: kubectl describe pod, check events, inspect resource requests/limits, verify image pull secrets. "
            "Remediation: Increase memory/CPU limits, fix image tag, create missing secrets, or scale cluster. "
            "Validation: Pod reaches Running state, readiness/liveness probes pass, no restarts for 5 minutes."
        ),
        "tags": ["kubernetes", "k8s", "pod", "crashloop", "imagepull", "oomkilled", "pending", "resource quota"]
    },
    {
        "id": "KB-RUNBOOK-008",
        "title": "Database Connection Pool Saturation Guide",
        "category": "database",
        "source": "docs/runbooks/db-connection-pool-saturation.md",
        "summary": "Understanding and fixing connection pool saturation beyond basic exhaustion",
        "content": (
            "Symptoms: Increasing connection wait times, sporadic timeouts, pool statistics show near-max usage. "
            "Root Cause: Connection leaks (not returning to pool), long-running transactions, or genuine capacity need. "
            "Verification: Monitor pg_stat_activity for idle in transaction, check pool stats for checked_out vs available. "
            "Remediation: Fix connection leaks in code, add pool_recycle, set statement_timeout, or increase pool size. "
            "Validation: Pool utilization stays below 70% under peak load, zero connection wait timeouts."
        ),
        "tags": ["database", "pool", "saturation", "leak", "idle in transaction", "pool_recycle", "statement_timeout"]
    },
    {
        "id": "KB-RUNBOOK-009",
        "title": "Incident Response Checklist",
        "category": "process",
        "source": "docs/runbooks/incident-response-checklist.md",
        "summary": "Standardized incident response procedure for on-call engineers",
        "content": (
            "1. Acknowledge: Confirm incident, page team, start timeline. "
            "2. Triage: Assess severity, impact, affected services. "
            "3. Communicate: Update status page, notify stakeholders. "
            "4. Investigate: Check dashboards, logs, recent deployments. "
            "5. Mitigate: Apply workaround or rollback if needed. "
            "6. Resolve: Implement root cause fix, verify. "
            "7. Document: Write postmortem, action items, follow-ups. "
            "8. Review: Post-incident review meeting within 48 hours."
        ),
        "tags": ["incident", "response", "checklist", "oncall", "severity", "postmortem", "process"]
    },
    {
        "id": "KB-RUNBOOK-010",
        "title": "Rollback Procedure",
        "category": "process",
        "source": "docs/runbooks/rollback-procedure.md",
        "summary": "Safe and fast rollback procedure for failed deployments",
        "content": (
            "Preconditions: Previous version artifact available, database migrations are backward compatible. "
            "Procedure: 1) Stop new traffic to affected service. 2) Deploy previous artifact version. "
            "3) Run smoke tests on critical paths. 4) Restore traffic gradually. 5) Monitor error rates. "
            "6) If rollback fails, escalate to disaster recovery. "
            "Verification: Error rate returns to baseline, latency normalizes, health checks pass."
        ),
        "tags": ["rollback", "deployment", "artifact", "backward compatible", "smoke test", "disaster recovery"]
    },
    {
        "id": "KB-RUNBOOK-011",
        "title": "Health Check Procedure",
        "category": "process",
        "source": "docs/runbooks/health-check-procedure.md",
        "summary": "Comprehensive service health validation after remediation",
        "content": (
            "Levels: 1) Liveness: Process running, port listening. "
            "2) Readiness: Dependencies reachable, cache warm, DB pool healthy. "
            "3) Functional: Key API endpoints return 200, business logic executes. "
            "4) Performance: Latency p99 < SLO, error rate < threshold. "
            "Tools: curl health endpoint, synthetic transactions, load test script. "
            "Criteria: All levels pass for 5 consecutive minutes before declaring healthy."
        ),
        "tags": ["health", "check", "liveness", "readiness", "synthetic", "load test", "slo"]
    },
    {
        "id": "KB-RUNBOOK-012",
        "title": "Payment API Architecture Document",
        "category": "architecture",
        "source": "docs/architecture/payment-api.md",
        "summary": "Payment API service architecture, dependencies, and data flow",
        "content": (
            "Service: payment-api (Python/FastAPI). "
            "Dependencies: PostgreSQL (primary DB), Redis (cache), Stripe (external payment processor). "
            "Data Flow: Client -> API Gateway -> payment-api -> PostgreSQL (transactions) + Stripe (processing) -> Response. "
            "Configuration: DB_POOL_SIZE=5 (DEFAULT), RETRY_COUNT=10, TIMEOUT=5s, CACHE_TTL=300s. "
            "SLOs: p99 latency < 500ms, error rate < 0.1%, availability 99.9%. "
            "Known Weaknesses: Small connection pool, aggressive retries, no circuit breaker."
        ),
        "tags": ["architecture", "payment-api", "postgres", "redis", "stripe", "dependencies", "slo", "data flow"]
    },
    {
        "id": "KB-RUNBOOK-013",
        "title": "Service Dependency Document",
        "category": "architecture",
        "source": "docs/architecture/service-dependencies.md",
        "summary": "Service dependency graph and blast radius analysis",
        "content": (
            "Payment API depends on: PostgreSQL (critical), Redis (degraded mode OK), Stripe (critical for payments). "
            "Checkout Service depends on: Payment API (critical), Inventory API (degraded mode OK). "
            "Order Service depends on: Checkout Service (critical), Payment API (critical). "
            "Notification Service depends on: Message Queue (critical), Email/SMS providers (degraded). "
            "Blast Radius: Payment API failure impacts Checkout (100%), Orders (100%), Notifications (50%)."
        ),
        "tags": ["dependencies", "blast radius", "payment-api", "checkout", "orders", "notifications", "service graph"]
    },
    {
        "id": "KB-RUNBOOK-014",
        "title": "Previous Incident INC-1042: Payment API Pool Exhaustion",
        "category": "incident",
        "source": "docs/incidents/INC-1042.md",
        "summary": "Historical incident: Payment API database connection pool exhaustion during Black Friday",
        "content": (
            "Incident: INC-1042. Service: payment-api. Date: 2025-11-29. "
            "Symptoms: HTTP 500 rate 45%, 'connection pool exhausted' errors. "
            "Root Cause: DB_POOL_SIZE=5 insufficient for 50x traffic spike. "
            "Remediation: Increased DB_POOL_SIZE to 50, added pool monitoring. "
            "Verification: Load test 100 concurrent users, 0 pool errors. "
            "Lessons: Always load test pool config at expected peak traffic + 50% headroom."
        ),
        "tags": ["incident", "payment-api", "pool", "exhaustion", "black friday", "traffic spike", "lessons learned"]
    },
    {
        "id": "KB-RUNBOOK-015",
        "title": "Previous Incident INC-0987: Checkout API Connection Saturation",
        "category": "incident",
        "source": "docs/incidents/INC-0987.md",
        "summary": "Historical incident: Checkout API upstream connection saturation causing cascade",
        "content": (
            "Incident: INC-0987. Service: checkout-api. Date: 2025-10-15. "
            "Symptoms: 504 Gateway Timeout, retry storm to Payment API. "
            "Root Cause: RETRY_COUNT=12 with no backoff overwhelmed Payment API. "
            "Remediation: Reduced RETRY_COUNT to 3, added exponential backoff with jitter. "
            "Verification: Chaos test with Payment API latency injection, no cascade. "
            "Lessons: Always implement circuit breaker and jittered backoff for external calls."
        ),
        "tags": ["incident", "checkout-api", "retry", "storm", "cascade", "circuit breaker", "jitter", "backoff"]
    },
    {
        "id": "KB-RUNBOOK-016",
        "title": "Postmortem Template",
        "category": "process",
        "source": "docs/process/postmortem-template.md",
        "summary": "Standardized postmortem template for incident documentation",
        "content": (
            "Sections: 1) Executive Summary. 2) Timeline. 3) Root Cause. "
            "4) Impact Assessment. 5) Detection & Response. 6) Resolution. "
            "7) Action Items (P0/P1/P2). 8) Lessons Learned. 9) Prevention. "
            "Blameless culture: Focus on systems, not individuals."
        ),
        "tags": ["postmortem", "template", "blameless", "action items", "lessons learned", "prevention"]
    },
    {
        "id": "KB-RUNBOOK-017",
        "title": "Configuration Reference",
        "category": "reference",
        "source": "docs/reference/configuration.md",
        "summary": "Complete configuration reference for all COSKA-monitored services",
        "content": (
            "DB_POOL_SIZE: Default 5, Recommended 30, Max 100. "
            "DB_POOL_TIMEOUT: Default 5s, Recommended 10s, Max 30s. "
            "RETRY_COUNT: Default 10, Recommended 3, Max 5. "
            "TIMEOUT: Default 5s, Recommended 10s, Max 30s. "
            "CACHE_TTL: Default 300s, Recommended 600s, Max 3600s. "
            "CIRCUIT_BREAKER_THRESHOLD: Default 50%, Recommended 50%. "
            "MEMORY_LIMIT: Default 512m, Recommended 1g for high-traffic services."
        ),
        "tags": ["configuration", "reference", "db_pool_size", "retry_count", "timeout", "cache_ttl", "circuit_breaker"]
    },
    {
        "id": "KB-RUNBOOK-018",
        "title": "Monitoring Guide",
        "category": "reference",
        "source": "docs/reference/monitoring.md",
        "summary": "Key metrics and alerts for production service monitoring",
        "content": (
            "Golden Signals: Latency, Traffic, Errors, Saturation. "
            "Key Metrics: HTTP error rate (target <0.1%), p99 latency (target <500ms), "
            "DB pool utilization (target <70%), CPU (target <70%), Memory (target <80%). "
            "Alerts: Error rate >1% for 5m, p99 latency >1s for 5m, pool exhaustion >0, OOM kills."
        ),
        "tags": ["monitoring", "golden signals", "slo", "alerts", "error rate", "latency", "saturation"]
    },
    {
        "id": "KB-RUNBOOK-019",
        "title": "SLO/SLA Guide",
        "category": "reference",
        "source": "docs/reference/slo-sla.md",
        "summary": "Service Level Objectives and Agreements for critical services",
        "content": (
            "Payment API: Availability 99.9%, Latency p99 <500ms, Error rate <0.1%. "
            "Checkout API: Availability 99.95%, Latency p99 <800ms, Error rate <0.05%. "
            "Order API: Availability 99.99%, Latency p99 <300ms, Error rate <0.01%. "
            "Error Budget: Monthly error budget = (1 - SLO) * total requests. "
            "Burn Rate: Alert if burning >2% of error budget per hour."
        ),
        "tags": ["slo", "sla", "availability", "latency", "error budget", "burn rate", "payment-api", "checkout"]
    },
    {
        "id": "KB-RUNBOOK-020",
        "title": "Security Escalation Runbook",
        "category": "security",
        "source": "docs/runbooks/security-escalation.md",
        "summary": "Security incident escalation and response procedures",
        "content": (
            "Triggers: Suspected data breach, unauthorized access, vulnerability exploitation. "
            "Immediate: Isolate affected systems, preserve evidence, notify security team. "
            "Investigation: Check access logs, audit trails, vulnerability scans. "
            "Communication: Legal, PR, customer notification if PII exposed. "
            "Recovery: Rotate credentials, patch vulnerabilities, verify integrity. "
            "Post-incident: Full forensic analysis, update threat model."
        ),
        "tags": ["security", "escalation", "breach", "unauthorized", "vulnerability", "forensic", "threat model"]
    },
]


class RAGEngine:
    """Offline, deterministic BM25-based Knowledge Retrieval Engine with traceability."""
    
    def __init__(self, runbooks: Optional[List[Dict[str, Any]]] = None):
        self.documents: List[RAGDocument] = []
        raw_books = runbooks or DEFAULT_RUNBOOKS
        for r in raw_books:
            doc = RAGDocument(
                id=r["id"],
                title=r["title"],
                category=r.get("category", "general"),
                source=r.get("source", "docs/runbooks"),
                summary=r.get("summary", ""),
                content=r.get("content", ""),
                tags=r.get("tags", [])
            )
            self.documents.append(doc)
        
        # Precompute document frequencies for BM25
        self._doc_tokens = [self._tokenize(f"{d.title} {d.summary} {d.content} {' '.join(d.tags)}") for d in self.documents]
        self._doc_lens = [len(toks) for toks in self._doc_tokens]
        self._avg_doc_len = sum(self._doc_lens) / max(len(self._doc_lens), 1)
        self._df = Counter()
        for toks in self._doc_tokens:
            for term in set(toks):
                self._df[term] += 1
    
    def _tokenize(self, text: str) -> List[str]:
        """Lowercase alphanumeric tokenizer."""
        return re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
    
    def search(self, query: str, top_k: int = 3, include_trace: bool = True) -> RAGSearchResult:
        """Retrieve top-k most relevant knowledge documents with relevance scores, snippets, and traceability."""
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return RAGSearchResult(
                documents=self.documents[:top_k],
                query=query,
                query_tokens=q_tokens,
                trace={"note": "Empty query, returning default documents"}
            )
        
        k1 = 1.5
        b = 0.75
        N = len(self.documents)
        scored: List[tuple[float, RAGDocument, str, List[str]]] = []
        
        for idx, doc in enumerate(self.documents):
            score = 0.0
            doc_toks = self._doc_tokens[idx]
            doc_len = self._doc_lens[idx]
            tok_counts = Counter(doc_toks)
            matched_terms = []
            
            for qt in q_tokens:
                if qt not in self._df:
                    continue
                df = self._df[qt]
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                tf = tok_counts.get(qt, 0)
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (doc_len / max(self._avg_doc_len, 1)))
                score += idf * (numerator / max(denominator, 0.001))
                if tf > 0:
                    matched_terms.append(qt)
            
            # Boost tag and title matches
            for tag in doc.tags:
                if any(qt == tag.lower() for qt in q_tokens):
                    score += 2.5
                    matched_terms.append(tag)
            if any(qt in doc.title.lower() for qt in q_tokens):
                score += 1.5
                matched_terms.append("title_match")
            
            # Extract snippet containing query terms
            snippet = self._generate_snippet(doc.content, q_tokens)
            doc_copy = doc.model_copy()
            doc_copy.relevance_score = round(min(max(score / 15.0, 0.05), 0.99), 3)
            doc_copy.snippet = snippet
            doc_copy.matched_terms = list(set(matched_terms))
            doc_copy.match_reason = self._generate_match_reason(doc, q_tokens, matched_terms)
            scored.append((score, doc_copy, snippet, matched_terms))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item[1] for item in scored[:top_k]]
        
        trace = {
            "query": query,
            "query_tokens": q_tokens,
            "total_documents": N,
            "documents_evaluated": len(scored),
            "top_results": [
                {
                    "id": d.id,
                    "title": d.title,
                    "relevance_score": d.relevance_score,
                    "matched_terms": d.matched_terms,
                    "match_reason": d.match_reason
                }
                for d in results
            ]
        }
        
        return RAGSearchResult(
            documents=results,
            query=query,
            query_tokens=q_tokens,
            trace=trace
        )
    
    def _generate_match_reason(self, doc: RAGDocument, query_tokens: List[str], matched_terms: List[str]) -> str:
        """Generate human-readable explanation of why this document was retrieved."""
        reasons = []
        if "title_match" in matched_terms:
            reasons.append("title matches query")
        tag_matches = [t for t in matched_terms if t in doc.tags]
        if tag_matches:
            reasons.append(f"tags match: {', '.join(tag_matches)}")
        content_matches = [t for t in matched_terms if t not in doc.tags and t != "title_match"]
        if content_matches:
            reasons.append(f"content matches: {', '.join(content_matches[:5])}")
        return "; ".join(reasons) if reasons else "general relevance"
    
    def _generate_snippet(self, content: str, query_tokens: List[str]) -> str:
        """Extract surrounding text snippet highlighting matching terms."""
        sentences = content.split(". ")
        best_sentence = sentences[0] if sentences else content[:160]
        max_matches = -1
        
        for s in sentences:
            s_toks = set(self._tokenize(s))
            matches = sum(1 for qt in query_tokens if qt in s_toks)
            if matches > max_matches:
                max_matches = matches
                best_sentence = s
        
        return best_sentence.strip() + ("." if not best_sentence.endswith(".") else "")
    
    def get_document(self, doc_id: str) -> Optional[RAGDocument]:
        """Get a specific document by ID."""
        for doc in self.documents:
            if doc.id == doc_id:
                return doc
        return None
    
    def list_categories(self) -> List[str]:
        """List all unique categories."""
        return list(set(d.category for d in self.documents))
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents with metadata."""
        return [
            {
                "id": d.id,
                "title": d.title,
                "category": d.category,
                "source": d.source,
                "summary": d.summary,
                "tags": d.tags
            }
            for d in self.documents
        ]


# Global singleton
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine