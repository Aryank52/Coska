# RAG_GUIDE.md - COSKA Retrieval-Augmented Generation Guide

## Overview

COSKA uses a **deterministic, offline BM25 RAG engine** for knowledge retrieval. No embeddings, no vector database, no external dependencies.

```
┌─────────────────────────────────────────────────────────────────┐
│                        COSKA RAG ENGINE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INCIDENT INTAKE                                                │
│       │                                                         │
│       ▼                                                         │
│  QUERY: service + description + symptoms + probable_causes     │
│       │                                                         │
│       ▼                                                         │
│  BM25 SEARCH (20 curated runbooks)                              │
│       │                                                         │
│       ▼                                                         │
│  TOP-K (default 3) WITH:                                        │
│  • Relevance score (0.05-0.99)                                  │
│  • Snippet with matched terms                                   │
│  • Matched terms list                                           │
│  • Match reason (traceability)                                  │
│       │                                                         │
│       ▼                                                         │
│  INJECT INTO: Hypothesis Gen + Root Cause Analysis              │
│       │                                                         │
│       ▼                                                         │
│  EVIDENCE: source_type=RAG with full provenance                 │
│       │                                                         │
│       ▼                                                         │
│  UI: Knowledge Base page + Judge Mode RAG tab                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture

### Components

| Component | File | Responsibility |
|-----------|------|----------------|
| `RAGEngine` | `backend/app/services/rag.py` | BM25 search, scoring, snippet extraction |
| `RAGDocument` | `backend/app/services/rag.py` | Pydantic model for runbook documents |
| `RAGSearchResult` | `backend/app/services/rag.py` | Search results with traceability |
| `get_rag_engine()` | `backend/app/services/rag.py` | Singleton accessor |

### Data Model

```python
class RAGDocument(BaseModel):
    id: str                           # KB-RUNBOOK-001
    title: str                        # "PostgreSQL Pool Exhaustion Runbook"
    category: str                     # database, network, deployment, cache, runtime, kubernetes, process, reference, security
    source: str                       # docs/runbooks/database-pool-exhaustion.md
    summary: str                      # One-line summary
    content: str                      # Full runbook content
    tags: List[str]                   # ["database", "postgres", "pool", "sqlalchemy", "db_pool_size"]
    relevance_score: float = 0.0      # BM25 score normalized 0.05-0.99
    snippet: str = ""                 # Best matching sentence
    matched_terms: List[str] = []     # ["pool", "exhaustion", "db_pool_size"]
    match_reason: str = ""            # "tags match: pool, exhaustion; title matches query"

class RAGSearchResult(BaseModel):
    documents: List[RAGDocument]
    query: str
    query_tokens: List[str]
    trace: Dict[str, Any]             # For traceability UI
```

---

## Knowledge Base (20 Runbooks)

| ID | Title | Category | Key Tags |
|----|-------|----------|----------|
| KB-RUNBOOK-001 | PostgreSQL Pool Exhaustion Runbook | database | postgres, pool, sqlalchemy, db_pool_size, 500 |
| KB-RUNBOOK-002 | Upstream Timeout and Retry Storm Runbook | network | retry, timeout, 504, gateway, circuit breaker, backoff |
| KB-RUNBOOK-003 | Bad Deployment Configuration Runbook | deployment | deployment, regression, auth, config, rollback, credentials |
| KB-RUNBOOK-004 | Redis Cache Stampede Runbook | cache | cache, redis, stampede, thundering herd, lock, ttl |
| KB-RUNBOOK-005 | Memory Leak & GC Pause Runbook | runtime | memory, leak, oom, garbage collection, gc, heap, rss |
| KB-RUNBOOK-006 | Database Saturation & Missing Index Runbook | database | database, cpu, saturation, slow query, index, disk, iops |
| KB-RUNBOOK-007 | Kubernetes Deployment Troubleshooting | kubernetes | kubernetes, k8s, pod, crashloop, imagepull, oomkilled |
| KB-RUNBOOK-008 | Database Connection Pool Saturation | database | database, pool, saturation, leak, idle in transaction |
| KB-RUNBOOK-009 | Incident Response Checklist | process | incident, response, checklist, oncall, postmortem |
| KB-RUNBOOK-010 | Rollback Procedure | process | rollback, deployment, artifact, backward compatible |
| KB-RUNBOOK-011 | Health Check Procedure | process | health, liveness, readiness, synthetic, load test, slo |
| KB-RUNBOOK-012 | Payment API Architecture | architecture | architecture, payment-api, postgres, redis, stripe, slo |
| KB-RUNBOOK-013 | Service Dependencies | architecture | dependencies, blast radius, payment-api, checkout, orders |
| KB-RUNBOOK-014 | Previous Incident INC-1042: Pool Exhaustion | incident | incident, payment-api, pool, exhaustion, black friday |
| KB-RUNBOOK-015 | Previous Incident INC-0987: Connection Saturation | incident | incident, checkout-api, retry, storm, cascade |
| KB-RUNBOOK-016 | Postmortem Template | process | postmortem, template, blameless, action items |
| KB-RUNBOOK-017 | Configuration Reference | reference | configuration, db_pool_size, retry_count, timeout |
| KB-RUNBOOK-018 | Monitoring Guide | reference | monitoring, golden signals, slo, alerts |
| KB-RUNBOOK-019 | SLO/SLA Guide | reference | slo, sla, availability, latency, error budget, burn rate |
| KB-RUNBOOK-020 | Security Escalation Runbook | security | security, escalation, breach, vulnerability, forensic |

---

## BM25 Scoring Algorithm

```python
def search(self, query: str, top_k: int = 3) -> RAGSearchResult:
    q_tokens = self._tokenize(query)
    
    k1 = 1.5      # Term frequency saturation
    b = 0.75      # Document length normalization
    N = len(self.documents)
    
    for idx, doc in enumerate(self.documents):
        score = 0.0
        doc_toks = self._doc_tokens[idx]
        doc_len = self._doc_lens[idx]
        tok_counts = Counter(doc_toks)
        
        for qt in q_tokens:
            if qt not in self._df:
                continue
            df = self._df[qt]
            idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
            tf = tok_counts.get(qt, 0)
            
            # BM25 formula
            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (1.0 - b + b * (doc_len / max(self._avg_doc_len, 1)))
            score += idf * (numerator / max(denominator, 0.001))
        
        # Boost for tag matches (+2.5) and title matches (+1.5)
        for tag in doc.tags:
            if any(qt == tag.lower() for qt in q_tokens):
                score += 2.5
        if any(qt in doc.title.lower() for qt in q_tokens):
            score += 1.5
        
        # Normalize to 0.05-0.99
        relevance = round(min(max(score / 15.0, 0.05), 0.99), 3)
```

### Tokenization
```python
def _tokenize(self, text: str) -> List[str]:
    return re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())
```
- Lowercase alphanumeric + underscore + hyphen
- Minimum 2 characters
- No stopword removal (handled by IDF)

---

## Integration Points

### 1. Incident Intake (Phase 1)
```python
# orchestrator.py - _phase_incident_intake()
query = f"{incident.service} {incident.description}"
rag_docs = self.rag_engine.search(query, top_k=3)
state.knowledge_docs = [d.model_dump() for d in rag_docs]

# Add top runbook as evidence
if rag_docs:
    top = rag_docs[0]
    rag_ev = Evidence(
        source_type=SourceType.RAG,
        claim=f"Runbook guidance from {top.title}: {top.summary}",
        reference=top.source,
        confidence=top.relevance_score,
        related_component=top.category,
        raw_data={"doc_id": top.id, "snippet": top.snippet, "relevance": top.relevance_score}
    )
    state.evidence.append(rag_ev)
```

### 2. Hypothesis Generation (Phase 4)
```python
# hypotheses.py - refine_hypotheses_with_nemotron()
rag_results = self.rag_engine.search(query, top_k=5)
# Pass to LLM as context:
rag_context = "\nRELEVANT RUNBOOKS:\n" + "\n".join([
    f"- {d.title}: {d.snippet[:200]}" for d in rag_results
])
```

### 3. Root Cause Analysis (Phase 6)
```python
# root_cause.py - identify_root_cause()
rag_results = self.rag_engine.search(query, top_k=3)
# Included in prompt context
```

---

## API Endpoints

### Search Knowledge Base
```http
POST /api/rag/search
Content-Type: application/json

{
  "query": "connection pool exhaustion",
  "top_k": 3,
  "include_trace": true
}

Response 200:
{
  "documents": [
    {
      "id": "KB-RUNBOOK-001",
      "title": "PostgreSQL Pool Exhaustion Runbook",
      "category": "database",
      "source": "docs/runbooks/database-pool-exhaustion.md",
      "summary": "Mitigation steps and diagnostics for SQLAlchemy/PostgreSQL connection pool exhaustion",
      "content": "Symptoms: High HTTP 500 error rates...",
      "tags": ["database", "postgres", "pool", "sqlalchemy", "db_pool_size", "connection pool", "500"],
      "relevance_score": 0.94,
      "snippet": "Root Cause: DB_POOL_SIZE undersized for concurrency spike or connection leaks.",
      "matched_terms": ["pool", "exhaustion", "connection", "db_pool_size"],
      "match_reason": "tags match: pool, exhaustion, connection, db_pool_size; title matches query"
    }
  ],
  "query": "connection pool exhaustion",
  "query_tokens": ["connection", "pool", "exhaustion"],
  "trace": {
    "total_documents": 20,
    "top_results": [
      {"id": "KB-RUNBOOK-001", "title": "...", "relevance_score": 0.94, "matched_terms": [...], "match_reason": "..."}
    ]
  }
}
```

### List Documents
```http
GET /api/rag/documents
Response: { "documents": [{ "id": "...", "title": "...", "category": "...", "summary": "...", "tags": [...] }, ...] }
```

### Get Document
```http
GET /api/rag/documents/KB-RUNBOOK-001
```

### List Categories
```http
GET /api/rag/categories
Response: { "categories": ["database", "network", "deployment", "cache", "runtime", "kubernetes", "process", "reference", "security", "incident", "architecture"] }
```

---

## Frontend Integration

### Knowledge Base Page (`/knowledge`)
```tsx
// Search with traceability
const handleSearch = async (e) => {
  e.preventDefault();
  setSearchLoading(true);
  const result = await searchKnowledgeBase({ query: searchQuery, top_k: 10, include_trace: true });
  setSearchResults(result);
  setViewMode('search');
};

// Results show:
// - Rank # + Relevance score (0-99%)
// - Title + Category badge
// - Snippet with matched terms
// - Match reason: "tags match: pool, exhaustion; title matches query"
// - Source provenance
```

### Judge Mode RAG Tab
```tsx
// Tab shows retrieved runbooks with provenance
{resultState.knowledge_docs.map((doc, idx) => (
  <div key={doc.id} style={{ border: idx === 0 ? '1px solid var(--accent-primary)' : '1px solid var(--border-color)' }}>
    {idx === 0 && <span style={{background: 'var(--accent-primary)', color: '#000', padding: '2px 6px', borderRadius: 4, fontWeight: 700, fontSize: 10}}>TOP SOURCE</span>}
    <h4>{doc.title}</h4>
    <span className="badge badge-medium">{doc.category}</span>
    <p>{doc.summary}</p>
    <div style={{padding: 10, background: 'rgba(0,0,0,0.25)', borderRadius: 6, fontSize: 12, borderLeft: '3px solid var(--accent-primary)'}}>
      <span style={{color: 'var(--fg-muted)', fontWeight: 600}}>Snippet: </span>
      <span style={{color: 'var(--fg-default)'}}>{doc.snippet || doc.content?.slice(0, 200)}</span>
    </div>
    <div style={{fontSize: 11, color: 'var(--fg-muted)'}}>Source Provenance: {doc.source}</div>
    <div style={{fontSize: 11, color: 'var(--accent-info)', marginTop: 4}}>Matched: {doc.matched_terms?.join(', ')}</div>
    <div style={{fontSize: 11, color: 'var(--accent-info)', marginTop: 4}}>Why: {doc.match_reason}</div>
  </div>
))}
```

---

## Traceability

Every RAG result includes traceability for audit:

```json
{
  "trace": {
    "query": "connection pool exhaustion",
    "query_tokens": ["connection", "pool", "exhaustion"],
    "total_documents": 20,
    "documents_evaluated": 20,
    "top_results": [
      {
        "id": "KB-RUNBOOK-001",
        "title": "PostgreSQL Pool Exhaustion Runbook",
        "relevance_score": 0.94,
        "matched_terms": ["pool", "exhaustion", "db_pool_size"],
        "match_reason": "tags match: pool, exhaustion, db_pool_size; title matches query"
      }
    ]
  }
}
```

**UI shows**: "Why this document was retrieved" → Match reason

---

## Adding Custom Runbooks

### 1. Add to DEFAULT_RUNBOOKS
```python
# backend/app/services/rag.py
DEFAULT_RUNBOOKS = [
    # ... existing ...
    {
        "id": "KB-RUNBOOK-021",
        "title": "Custom Service Runbook",
        "category": "custom",
        "source": "docs/runbooks/custom-service.md",
        "summary": "Brief summary",
        "content": "Full runbook content with symptoms, root cause, verification, remediation",
        "tags": ["custom", "service", "specific-tags"]
    }
]
```

### 2. Create Markdown File (Optional)
```markdown
# docs/runbooks/custom-service.md

## Symptoms
- Symptom 1
- Symptom 2

## Root Cause
- Root cause description

## Verification
- Verification steps

## Remediation
- Fix steps
```

### 3. Rebuild Index
```python
# Automatic on next search - no rebuild needed
# Or force rebuild:
rag_engine = RAGEngine()  # Re-initializes with new runbooks
```

---

## Testing

```python
# tests/test_rag_and_scenarios.py
def test_rag_retrieval():
    engine = get_rag_engine()
    result = engine.search("connection pool exhaustion", top_k=3)
    assert len(result.documents) == 3
    assert result.documents[0].relevance_score > 0.8
    assert "pool" in result.documents[0].matched_terms

def test_rag_traceability():
    engine = get_rag_engine()
    result = engine.search("pool exhaustion", top_k=1, include_trace=True)
    assert "trace" in result.trace
    assert "match_reason" in result.trace["top_results"][0]

def test_rag_categories():
    engine = get_rag_engine()
    cats = engine.list_categories()
    assert "database" in cats
    assert len(cats) >= 5
```

---

## Performance

| Metric | Value |
|--------|-------|
| Documents | 20 |
| Avg Search Time | < 5ms |
| Memory | ~500KB |
| Index Build | < 10ms (on init) |
| Max Top-K | 10 |

---

## Security

| Concern | Mitigation |
|---------|------------|
| Prompt Injection | Retrieved docs in KNOWLEDGE section only; injection patterns detected |
| Data Leakage | No secrets in runbooks; only public knowledge |
| Injection Detection | Patterns: "ignore previous instructions", "reveal secrets", "run shell", "modify files" |
| Traceability | Match reason logged for every retrieval |

---

## Extending RAG

### Add Metadata Filtering
```python
def search(self, query: str, top_k: int = 3, category: Optional[str] = None, tags: Optional[List[str]] = None):
    # Filter documents before scoring
    candidates = self.documents
    if category:
        candidates = [d for d in candidates if d.category == category]
    if tags:
        candidates = [d for d in candidates if any(t in d.tags for t in tags)]
    # ... BM25 on candidates
```

### Add Hybrid Search (Future)
```python
# Hybrid: BM25 + Embeddings
# 1. BM25 for exact match (current)
# 2. Embeddings for semantic similarity
# 3. Reciprocal rank fusion
```

---

## Monitoring

```python
# Logged per search
logger.debug("rag_search", 
    query=query, 
    top_k=top_k,
    result_count=len(result.documents),
    top_score=result.documents[0].relevance_score if result.documents else 0
)
```

**Metrics to Track**:
- Search latency (p50, p95, p99)
- Result count distribution
- Top category distribution
- Zero-result queries
- Traceability click-through