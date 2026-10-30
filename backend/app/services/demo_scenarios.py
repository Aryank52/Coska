"""Demo Scenario Library for COSKA - 6 realistic synthetic incidents with deterministic data."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import json


class DemoScenario(BaseModel):
    """Complete demo scenario definition."""
    id: str
    name: str
    description: str
    category: str  # pool_exhaustion, retry_storm, bad_deployment, cache_stampede, memory_leak, db_saturation
    
    # Incident data
    incident: Dict[str, Any]
    
    # Expected investigation results
    expected_root_cause: str
    expected_remediation: Dict[str, Any]
    expected_verification: Dict[str, Any]
    
    # Demo metadata
    difficulty: str = "medium"  # easy, medium, hard
    estimated_duration_seconds: int = 30
    tags: List[str] = Field(default_factory=list)


# Scenario 1: Payment API DB Pool Exhaustion
SCENARIO_POOL_EXHAUSTION = DemoScenario(
    id="payment_pool_exhaustion",
    name="Payment API DB Pool Exhaustion",
    description="Database connection pool exhaustion due to undersized pool configuration during traffic spike",
    category="pool_exhaustion",
    incident={
        "service": "payment-api",
        "severity": "CRITICAL",
        "description": "HTTP 500 error rate increased from 1.2% to 38%. Users experiencing payment failures.",
        "logs": (
            "2026-10-29T10:15:23.456Z ERROR payment-api: connection pool exhausted\n"
            "2026-10-29T10:15:24.123Z ERROR payment-api: timeout waiting for database connection\n"
            "2026-10-29T10:15:24.789Z ERROR payment-api: connection pool exhausted\n"
            "2026-10-29T10:15:25.001Z ERROR payment-api: timeout waiting for database connection\n"
            "2026-10-29T10:15:25.555Z ERROR payment-api: connection pool exhausted\n"
            "2026-10-29T10:15:26.234Z ERROR payment-api: HTTP 500 - Database connection timeout\n"
            "2026-10-29T10:15:26.890Z ERROR payment-api: connection pool exhausted\n"
            "2026-10-29T10:15:27.111Z ERROR payment-api: timeout waiting for database connection\n"
            "2026-10-29T10:15:27.666Z ERROR payment-api: connection pool exhausted\n"
            "2026-10-29T10:15:28.000Z ERROR payment-api: HTTP 500 - Database connection timeout\n"
            "2026-10-29T10:15:28.555Z ERROR payment-api: connection pool exhausted\n"
            "2026-10-29T10:15:29.123Z ERROR payment-api: timeout waiting for database connection\n"
            "2026-10-29T10:15:29.777Z ERROR payment-api: connection pool exhausted\n"
            "2026-10-29T10:15:30.001Z ERROR payment-api: HTTP 500 - Database connection timeout\n"
            "... (17 total pool exhaustion events in 90 seconds)"
        ),
        "deployment": "payment-api v1.8.2 deployed at 2026-10-29T10:10:00Z",
        "repository": "https://github.com/coska/payment-api",
        "metadata": {
            "configuration": "DB_POOL_SIZE=5\nDB_POOL_TIMEOUT=5\nDATABASE_URL=sqlite+aiosqlite:///./payments.db"
        }
    },
    expected_root_cause="Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)",
    expected_remediation={
        "type": "CONFIGURATION_CHANGE",
        "description": "Increase database connection pool size from 5 to 30 to handle concurrent request load",
        "exact_change": "DB_POOL_SIZE: 5 -> 30",
        "expected_effect": "Eliminate connection pool exhaustion and reduce HTTP 500 error rate to baseline",
        "risk": "LOW",
        "blast_radius": "SANDBOX_ONLY",
        "rollback_plan": "Revert DB_POOL_SIZE to 5 in configuration"
    },
    expected_verification={
        "baseline_test": "FAILED",
        "post_fix_tests": "PASSED",
        "health_check": "PASSED",
        "control_test": "FAILED",
        "verdict": "VERIFIED"
    },
    difficulty="easy",
    estimated_duration_seconds=25,
    tags=["database", "pool", "connection", "postgres", "500", "configuration"]
)


# Scenario 2: External API Retry Storm
SCENARIO_RETRY_STORM = DemoScenario(
    id="retry_storm",
    name="External API Retry Storm",
    description="Cascading 504 Gateway Timeouts caused by unjittered excessive retries to upstream payment provider",
    category="retry_storm",
    incident={
        "service": "checkout-api",
        "severity": "CRITICAL",
        "description": "Cascading HTTP 504 Gateway Timeouts. Queue buildup causing complete checkout failure.",
        "logs": (
            "2026-10-28T14:22:10.123Z WARN checkout-api: upstream timeout calling payment-api (5s)\n"
            "2026-10-28T14:22:10.456Z WARN checkout-api: retry 1/10 for request req-abc123\n"
            "2026-10-28T14:22:10.789Z WARN checkout-api: retry 2/10 for request req-abc123\n"
            "2026-10-28T14:22:11.234Z WARN checkout-api: retry 3/10 for request req-abc123\n"
            "2026-10-28T14:22:11.567Z WARN checkout-api: retry 4/10 for request req-abc123\n"
            "2026-10-28T14:22:12.001Z ERROR checkout-api: all 10 retries exhausted for req-abc123\n"
            "2026-10-28T14:22:12.100Z WARN checkout-api: upstream timeout calling payment-api (5s)\n"
            "2026-10-28T14:22:12.200Z WARN checkout-api: retry 1/10 for request req-def456\n"
            "2026-10-28T14:22:12.300Z WARN checkout-api: retry 2/10 for request req-def456\n"
            "... (127 similar retry storms in 5 minutes)"
        ),
        "deployment": "checkout-api v2.3.1 deployed at 2026-10-28T14:20:00Z",
        "repository": "https://github.com/coska/checkout-api",
        "metadata": {
            "configuration": "RETRY_COUNT=10\nRETRY_BACKOFF=0\nTIMEOUT=5\nPAYMENT_API_URL=https://payments.internal"
        }
    },
    expected_root_cause="Upstream timeout and cascading retry storm caused by excessive RETRY_COUNT=10 with no backoff or jitter",
    expected_remediation={
        "type": "CONFIGURATION_CHANGE",
        "description": "Reduce retry count from 10 to 3, add exponential backoff with full jitter, enable circuit breaker",
        "exact_change": "RETRY_COUNT: 10 -> 3, RETRY_BACKOFF: 0 -> exponential_jitter, CIRCUIT_BREAKER_THRESHOLD: 0 -> 50",
        "expected_effect": "Prevent thundering herd, allow upstream recovery, reduce cascade failures by 95%",
        "risk": "LOW",
        "blast_radius": "SANDBOX_ONLY",
        "rollback_plan": "Revert RETRY_COUNT to 10, disable circuit breaker"
    },
    expected_verification={
        "baseline_test": "FAILED",
        "post_fix_tests": "PASSED",
        "health_check": "PASSED",
        "control_test": "FAILED",
        "verdict": "VERIFIED"
    },
    difficulty="medium",
    estimated_duration_seconds=35,
    tags=["retry", "timeout", "504", "gateway", "circuit breaker", "upstream", "backoff", "thundering herd"]
)


# Scenario 3: Bad Deployment Configuration
SCENARIO_BAD_DEPLOYMENT = DemoScenario(
    id="bad_deployment",
    name="Bad Deployment Configuration",
    description="Post-release configuration mismatch causing immediate 100% failure rate",
    category="bad_deployment",
    incident={
        "service": "inventory-api",
        "severity": "CRITICAL",
        "description": "Immediate 100% HTTP 500 failure rate immediately following v3.0.0 deployment. All requests failing.",
        "logs": (
            "2026-10-27T09:00:01.000Z ERROR inventory-api: FATAL: database authentication failed for user 'prod_user'\n"
            "2026-10-27T09:00:01.100Z ERROR inventory-api: FATAL: database authentication failed for user 'prod_user'\n"
            "2026-10-27T09:00:01.200Z ERROR inventory-api: FATAL: database authentication failed for user 'prod_user'\n"
            "2026-10-27T09:00:01.300Z ERROR inventory-api: FATAL: database authentication failed for user 'prod_user'\n"
            "2026-10-27T09:00:01.400Z ERROR inventory-api: FATAL: database authentication failed for user 'prod_user'\n"
        ),
        "deployment": "inventory-api v3.0.0 deployed at 2026-10-27T09:00:00Z",
        "repository": "https://github.com/coska/inventory-api",
        "metadata": {
            "configuration": "DB_USER=prod_user\nDB_PASSWORD=old_password\nDB_HOST=db-prod.internal\nDB_PORT=5432\nDATABASE_URL=postgresql://prod_user:old_password@db-prod.internal:5432/inventory"
        }
    },
    expected_root_cause="Bad deployment configuration: DB_PASSWORD not updated in deployment, using stale credentials",
    expected_remediation={
        "type": "CONFIGURATION_CHANGE",
        "description": "Update DB_PASSWORD in deployment configuration to match current production credentials",
        "exact_change": "DB_PASSWORD: old_password -> current_prod_password_2026",
        "expected_effect": "Restore database connectivity and eliminate authentication failures",
        "risk": "LOW",
        "blast_radius": "SANDBOX_ONLY",
        "rollback_plan": "Rollback to inventory-api v2.9.1 deployment artifact"
    },
    expected_verification={
        "baseline_test": "FAILED",
        "post_fix_tests": "PASSED",
        "health_check": "PASSED",
        "control_test": "FAILED",
        "verdict": "VERIFIED"
    },
    difficulty="easy",
    estimated_duration_seconds=20,
    tags=["deployment", "regression", "auth", "config", "rollback", "credentials", "500"]
)


# Scenario 4: Cache Stampede
SCENARIO_CACHE_STAMPEDE = DemoScenario(
    id="cache_stampede",
    name="Redis Cache Stampede",
    description="Thundering herd on cache expiration causing database saturation and cascade failure",
    category="cache_stampede",
    incident={
        "service": "catalog-api",
        "severity": "HIGH",
        "description": "Database CPU spike to 100% after hot cache key expiration. Query latency increased from 5ms to 5000ms.",
        "logs": (
            "2026-10-26T16:45:00.000Z INFO catalog-api: cache miss for key 'product_catalog_v2'\n"
            "2026-10-26T16:45:00.001Z INFO catalog-api: cache miss for key 'product_catalog_v2'\n"
            "2026-10-26T16:45:00.002Z INFO catalog-api: cache miss for key 'product_catalog_v2'\n"
            "2026-10-26T16:45:00.003Z INFO catalog-api: cache miss for key 'product_catalog_v2'\n"
            "2026-10-26T16:45:00.004Z INFO catalog-api: cache miss for key 'product_catalog_v2'\n"
            "2026-10-26T16:45:00.005Z ERROR catalog-api: database query timeout (30s) for catalog rebuild\n"
            "2026-10-26T16:45:01.000Z ERROR catalog-api: database CPU 98%, connection pool exhausted\n"
            "2026-10-26T16:45:02.000Z WARN catalog-api: 234 concurrent requests rebuilding same cache key\n"
        ),
        "deployment": "catalog-api v1.5.0 deployed at 2026-10-26T16:00:00Z (no config changes)",
        "repository": "https://github.com/coska/catalog-api",
        "metadata": {
            "configuration": "CACHE_TTL=300\nCACHE_BACKEND=redis\nREDIS_URL=redis://cache.internal:6379\nDB_POOL_SIZE=20"
        }
    },
    expected_root_cause="Cache stampede (thundering herd) where 200+ concurrent requests simultaneously recomputed expired catalog cache key",
    expected_remediation={
        "type": "CODE_CHANGE",
        "description": "Implement singleflight/mutex pattern for cache recomputation to prevent thundering herd",
        "exact_change": "Add mutex lock around cache rebuild: singleflight.Do(key, rebuild_fn) in catalog service",
        "expected_effect": "Only 1 request recomputes cache, others wait for result. Eliminates stampede.",
        "risk": "MEDIUM",
        "blast_radius": "SANDBOX_ONLY",
        "rollback_plan": "Revert catalog-api to v1.4.9 without singleflight"
    },
    expected_verification={
        "baseline_test": "FAILED",
        "post_fix_tests": "PASSED",
        "health_check": "PASSED",
        "control_test": "FAILED",
        "verdict": "VERIFIED"
    },
    difficulty="hard",
    estimated_duration_seconds=40,
    tags=["cache", "redis", "stampede", "thundering herd", "saturation", "singleflight", "mutex"]
)


# Scenario 5: Memory Leak
SCENARIO_MEMORY_LEAK = DemoScenario(
    id="memory_leak",
    name="Application Memory Leak",
    description="Gradual memory leak causing GC pauses, health check timeouts, and eventual OOM kills",
    category="memory_leak",
    incident={
        "service": "notification-api",
        "severity": "HIGH",
        "description": "Gradually increasing memory usage over 6 hours. Periodic 15-30s latency spikes. 3 OOM kills in last hour.",
        "logs": (
            "2026-10-25T10:00:00.000Z INFO notification-api: RSS memory: 450MB\n"
            "2026-10-25T12:00:00.000Z INFO notification-api: RSS memory: 680MB\n"
            "2026-10-25T14:00:00.000Z INFO notification-api: RSS memory: 920MB\n"
            "2026-10-25T15:30:00.000Z WARN notification-api: GC pause 12.3s, health check timeout\n"
            "2026-10-25T15:45:00.000Z ERROR notification-api: OOM kill, container restarted\n"
            "2026-10-25T15:50:00.000Z INFO notification-api: RSS memory: 520MB (after restart)\n"
            "2026-10-25T16:00:00.000Z INFO notification-api: RSS memory: 750MB\n"
            "2026-10-25T16:15:00.000Z WARN notification-api: GC pause 18.7s, health check timeout\n"
            "2026-10-25T16:20:00.000Z ERROR notification-api: OOM kill, container restarted\n"
        ),
        "deployment": "notification-api v2.1.0 deployed at 2026-10-25T08:00:00Z",
        "repository": "https://github.com/coska/notification-api",
        "metadata": {
            "configuration": "MEMORY_LIMIT=1024m\nWEB_CONCURRENCY=4\nEVENT_BUFFER_SIZE=unbounded\n"
        }
    },
    expected_root_cause="Application memory leak: unbounded EVENT_BUFFER_SIZE global list accumulating event objects without eviction",
    expected_remediation={
        "type": "CODE_CHANGE",
        "description": "Replace unbounded global event buffer with bounded LRU cache with TTL",
        "exact_change": "EVENT_BUFFER_SIZE: unbounded -> 10000 with TTL 300s, use functools.lru_cache or cachetools.LRUCache",
        "expected_effect": "Memory ceiling remains flat, GC pauses eliminated, no OOM kills",
        "risk": "MEDIUM",
        "blast_radius": "SANDBOX_ONLY",
        "rollback_plan": "Revert notification-api to v2.0.5 with original buffer implementation"
    },
    expected_verification={
        "baseline_test": "FAILED",
        "post_fix_tests": "PASSED",
        "health_check": "PASSED",
        "control_test": "FAILED",
        "verdict": "VERIFIED"
    },
    difficulty="hard",
    estimated_duration_seconds=45,
    tags=["memory", "leak", "oom", "garbage collection", "gc", "heap", "rss", "lru", "eviction"]
)


# Scenario 6: Database Saturation
SCENARIO_DB_SATURATION = DemoScenario(
    id="db_saturation",
    name="Database Saturation - Missing Index",
    description="Sequential full-table scans on large orders table causing 100% database CPU saturation",
    category="db_saturation",
    incident={
        "service": "order-api",
        "severity": "CRITICAL",
        "description": "Database CPU at 100%, all queries timing out. Order creation latency >30s. Complete service degradation.",
        "logs": (
            "2026-10-24T11:00:00.000Z ERROR order-api: query timeout (30s) SELECT * FROM orders WHERE user_id=? AND status=?\n"
            "2026-10-24T11:00:01.000Z ERROR order-api: query timeout (30s) SELECT * FROM orders WHERE user_id=?\n"
            "2026-10-24T11:00:02.000Z ERROR order-api: query timeout (30s) SELECT * FROM orders WHERE user_id=? AND status=?\n"
            "2026-10-24T11:00:03.000Z WARN order-api: database CPU 99%, active connections 95/100\n"
            "2026-10-24T11:00:04.000Z ERROR order-api: query timeout (30s) SELECT * FROM orders WHERE user_id=?\n"
            "2026-10-24T11:00:05.000Z WARN order-api: pg_stat_statements shows Seq Scan on orders (4.2M rows)\n"
            "2026-10-24T11:00:06.000Z ERROR order-api: query timeout (30s) SELECT * FROM orders WHERE user_id=? AND status=?\n"
        ),
        "deployment": "order-api v4.2.0 deployed at 2026-10-24T10:30:00Z (added new order filtering feature)",
        "repository": "https://github.com/coska/order-api",
        "metadata": {
            "configuration": "DB_POOL_SIZE=50\nDB_POOL_TIMEOUT=10\nWORK_MEM=4MB\n"
        }
    },
    expected_root_cause="Database saturation: missing composite index on orders(user_id, status) causing sequential scans on 4.2M row table",
    expected_remediation={
        "type": "CODE_CHANGE",
        "description": "Add missing composite index to support order filtering queries",
        "exact_change": "CREATE INDEX CONCURRENTLY idx_orders_user_status ON orders(user_id, status) WHERE status IN ('pending', 'processing')",
        "expected_effect": "Query execution changes from Seq Scan to Index Scan, latency drops from 30s+ to <10ms",
        "risk": "LOW",
        "blast_radius": "SANDBOX_ONLY",
        "rollback_plan": "DROP INDEX CONCURRENTLY idx_orders_user_status"
    },
    expected_verification={
        "baseline_test": "FAILED",
        "post_fix_tests": "PASSED",
        "health_check": "PASSED",
        "control_test": "FAILED",
        "verdict": "VERIFIED"
    },
    difficulty="medium",
    estimated_duration_seconds=35,
    tags=["database", "cpu", "saturation", "slow query", "index", "disk", "iops", "full table scan", "postgres"]
)


# All scenarios registry
ALL_SCENARIOS: Dict[str, DemoScenario] = {
    SCENARIO_POOL_EXHAUSTION.id: SCENARIO_POOL_EXHAUSTION,
    SCENARIO_RETRY_STORM.id: SCENARIO_RETRY_STORM,
    SCENARIO_BAD_DEPLOYMENT.id: SCENARIO_BAD_DEPLOYMENT,
    SCENARIO_CACHE_STAMPEDE.id: SCENARIO_CACHE_STAMPEDE,
    SCENARIO_MEMORY_LEAK.id: SCENARIO_MEMORY_LEAK,
    SCENARIO_DB_SATURATION.id: SCENARIO_DB_SATURATION,
}


def get_scenario(scenario_id: str) -> Optional[DemoScenario]:
    """Get a demo scenario by ID."""
    return ALL_SCENARIOS.get(scenario_id)


def list_scenarios() -> List[Dict[str, Any]]:
    """List all available demo scenarios."""
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "category": s.category,
            "difficulty": s.difficulty,
            "estimated_duration_seconds": s.estimated_duration_seconds,
            "tags": s.tags
        }
        for s in ALL_SCENARIOS.values()
    ]


def create_incident_from_scenario(scenario_id: str) -> Dict[str, Any]:
    """Create incident data from scenario for API submission."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"Unknown scenario: {scenario_id}")
    return scenario.incident