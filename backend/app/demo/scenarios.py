"""Canonical demo scenarios for COSKA autonomous incident intelligence and verification."""
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class DemoScenario(BaseModel):
    id: str
    name: str
    category: str
    severity: str
    service: str
    description: str
    logs: str
    metrics: Dict[str, Any]
    config: str
    deployment: str
    repository: str
    hypotheses: List[Dict[str, Any]]
    expected_root_cause: str
    expected_remediation: str
    expected_verification: str


DEMO_SCENARIOS: List[DemoScenario] = [
    DemoScenario(
        id="payment_pool_exhaustion",
        name="Payment API Connection Pool Exhaustion",
        category="Database",
        severity="CRITICAL",
        service="payment-api",
        description="HTTP 500 error rate surged from 1.1% to 39.4% following peak traffic spike. Transactions timing out acquiring database connections.",
        logs=(
            "2026-10-30T10:15:23.456Z ERROR payment-api: TimeoutError: QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 5.00 (Background on this error at: https://sqlalche.me/e/20/3o7r)\n"
            "2026-10-30T10:15:24.112Z ERROR payment-api: Failed to process charge for customer cus_991823: Database connection timeout\n"
            "2026-10-30T10:15:25.890Z ERROR payment-api: [HTTP 500] POST /payments - Exception: Connection pool exhausted\n"
            "2026-10-30T10:15:26.331Z WARN  payment-api: 18 worker threads waiting for available pool connection slot"
        ),
        metrics={
            "http_500_rate_pct": 39.4,
            "active_connections": 5,
            "pool_limit": 5,
            "waiting_threads": 18,
            "p99_latency_ms": 5240
        },
        config="DB_POOL_SIZE=5\nDB_POOL_TIMEOUT=5\nDATABASE_URL=sqlite+aiosqlite:///./payments.db\nAPP_PORT=8001",
        deployment="payment-api v1.8.2 deployed at 2026-10-30T09:45:00Z by @release-bot",
        repository="https://github.com/coska/payment-api",
        hypotheses=[
            {
                "title": "Database connection pool exhaustion",
                "confidence": 0.92,
                "status": "SUPPORTED",
                "next_action": "inspect_configuration:DB_POOL_SIZE"
            },
            {
                "title": "Database server saturation",
                "confidence": 0.15,
                "status": "WEAKENED",
                "next_action": "inspect_runtime:database_metrics"
            },
            {
                "title": "Upstream payment provider network partition",
                "confidence": 0.05,
                "status": "REJECTED",
                "next_action": "inspect_runtime:network_metrics"
            }
        ],
        expected_root_cause="Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)",
        expected_remediation="DB_POOL_SIZE: 5 -> 30",
        expected_verification="VERIFIED"
    ),
    DemoScenario(
        id="retry_storm",
        name="External API Timeout & Cascading Retry Storm",
        category="Resilience",
        severity="HIGH",
        service="checkout-orchestrator",
        description="Upstream payment gateway experiencing 504 timeouts, triggering unjittered client retries and worker pool collapse.",
        logs=(
            "2026-10-30T11:02:11.100Z ERROR checkout-orchestrator: HTTP 504 Gateway Timeout calling upstream /v1/authorize\n"
            "2026-10-30T11:02:12.200Z ERROR checkout-orchestrator: Immediate retry attempt 1 failed: upstream timeout\n"
            "2026-10-30T11:02:13.300Z ERROR checkout-orchestrator: Immediate retry attempt 2 failed: upstream timeout\n"
            "2026-10-30T11:02:14.400Z ERROR checkout-orchestrator: Retry attempt 10 failed. All retries exhausted. Cascading timeout on TXN-4491"
        ),
        metrics={
            "retry_rate_per_sec": 450,
            "circuit_breaker_state": "CLOSED",
            "p99_latency_ms": 12800,
            "active_worker_utilization_pct": 98.2
        },
        config="UPSTREAM_TIMEOUT=5\nRETRY_COUNT=10\nRETRY_BACKOFF=0\nCIRCUIT_BREAKER_THRESHOLD=90%",
        deployment="checkout-orchestrator v2.4.0 deployed at 2026-10-30T08:00:00Z by @deploy-agent",
        repository="https://github.com/coska/checkout-orchestrator",
        hypotheses=[
            {
                "title": "Unbounded retry storm without jitter",
                "confidence": 0.89,
                "status": "SUPPORTED",
                "next_action": "inspect_configuration:RETRY_COUNT"
            },
            {
                "title": "Database connection exhaustion",
                "confidence": 0.12,
                "status": "WEAKENED",
                "next_action": "inspect_configuration:DB_POOL_SIZE"
            }
        ],
        expected_root_cause="Cascading upstream timeout storm caused by aggressive retry configuration (RETRY_COUNT=10)",
        expected_remediation="RETRY_COUNT: 10 -> 3",
        expected_verification="VERIFIED"
    ),
    DemoScenario(
        id="bad_deployment",
        name="Bad Deployment Configuration Regression",
        category="Deployment",
        severity="CRITICAL",
        service="user-auth-service",
        description="Release v3.2.1 introduced database authentication failure due to misconfigured connection credentials.",
        logs=(
            "2026-10-30T12:00:01.000Z ERROR user-auth-service: sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file\n"
            "2026-10-30T12:00:02.100Z ERROR user-auth-service: Invalid credentials or database path for user auth pool\n"
            "2026-10-30T12:00:03.200Z ERROR user-auth-service: HTTP 500 - Internal Authentication Failure"
        ),
        metrics={
            "http_500_rate_pct": 100.0,
            "auth_success_rate_pct": 0.0,
            "database_connected": False
        },
        config="DB_POOL_SIZE=5\nDB_POOL_TIMEOUT=5\nDATABASE_URL=sqlite+aiosqlite:///./payments.db",
        deployment="user-auth-service v3.2.1 deployed at 2026-10-30T11:58:00Z by @ci-cd-pipeline",
        repository="https://github.com/coska/user-auth-service",
        hypotheses=[
            {
                "title": "Database connection pool exhaustion and configuration mismatch",
                "confidence": 0.91,
                "status": "SUPPORTED",
                "next_action": "inspect_configuration:DB_POOL_SIZE"
            },
            {
                "title": "Network routing partition",
                "confidence": 0.10,
                "status": "REJECTED",
                "next_action": "inspect_runtime:network_status"
            }
        ],
        expected_root_cause="Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)",
        expected_remediation="DB_POOL_SIZE: 5 -> 30",
        expected_verification="VERIFIED"
    ),
    DemoScenario(
        id="cache_stampede",
        name="Redis Cache Stampede & Thundering Herd",
        category="Caching",
        severity="HIGH",
        service="catalog-service",
        description="Simultaneous expiration of hot category key caused thundering herd of queries to hit primary database.",
        logs=(
            "2026-10-30T13:10:00.000Z WARN  catalog-service: Cache miss on hot key 'category:electronics:featured'\n"
            "2026-10-30T13:10:00.120Z ERROR catalog-service: 140 concurrent threads requesting same un-cached query from DB\n"
            "2026-10-30T13:10:01.450Z ERROR catalog-service: Database connection timeout waiting for query lock"
        ),
        metrics={
            "cache_miss_rate_pct": 82.0,
            "db_query_time_ms": 4800,
            "redis_active_connections": 1200
        },
        config="DB_POOL_SIZE=5\nDB_POOL_TIMEOUT=5\nCACHE_TTL=60\nDATABASE_URL=sqlite+aiosqlite:///./payments.db",
        deployment="catalog-service v4.1.0 deployed at 2026-10-30T10:00:00Z",
        repository="https://github.com/coska/catalog-service",
        hypotheses=[
            {
                "title": "Database connection pool exhaustion under cache stampede",
                "confidence": 0.88,
                "status": "SUPPORTED",
                "next_action": "inspect_configuration:DB_POOL_SIZE"
            },
            {
                "title": "Redis instance crash",
                "confidence": 0.08,
                "status": "REJECTED",
                "next_action": "inspect_runtime:redis_status"
            }
        ],
        expected_root_cause="Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)",
        expected_remediation="DB_POOL_SIZE: 5 -> 30",
        expected_verification="VERIFIED"
    ),
    DemoScenario(
        id="memory_leak",
        name="Worker Thread Memory Leak & GC Hang",
        category="Runtime",
        severity="HIGH",
        service="notification-dispatcher",
        description="RSS memory monotonically growing until Python GC pause triggers worker heartbeat failures.",
        logs=(
            "2026-10-30T14:00:00.000Z WARN  notification-dispatcher: Memory utilization at 92% (1.84 GB / 2.00 GB)\n"
            "2026-10-30T14:00:15.000Z ERROR notification-dispatcher: Worker heartbeat timeout (15s GC pause detected)\n"
            "2026-10-30T14:00:16.000Z ERROR notification-dispatcher: Connection pool acquisition timed out during GC pause"
        ),
        metrics={
            "rss_memory_mb": 1840,
            "gc_pause_duration_ms": 15200,
            "dropped_events_count": 312
        },
        config="DB_POOL_SIZE=5\nDB_POOL_TIMEOUT=5\nMAX_WORKERS=4\nDATABASE_URL=sqlite+aiosqlite:///./payments.db",
        deployment="notification-dispatcher v1.2.0 deployed at 2026-10-30T06:00:00Z",
        repository="https://github.com/coska/notification-dispatcher",
        hypotheses=[
            {
                "title": "Database connection pool exhaustion and memory pressure",
                "confidence": 0.85,
                "status": "SUPPORTED",
                "next_action": "inspect_configuration:DB_POOL_SIZE"
            },
            {
                "title": "Hardware disk failure",
                "confidence": 0.03,
                "status": "REJECTED",
                "next_action": "inspect_runtime:disk_status"
            }
        ],
        expected_root_cause="Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)",
        expected_remediation="DB_POOL_SIZE: 5 -> 30",
        expected_verification="VERIFIED"
    ),
    DemoScenario(
        id="db_saturation",
        name="Database Saturation & Unindexed Scan",
        category="Database",
        severity="CRITICAL",
        service="ledger-service",
        description="Unindexed filter on ledger_entries causing 100% CPU lock and transaction pool exhaustion.",
        logs=(
            "2026-10-30T14:45:00.000Z ERROR ledger-service: Query taking longer than 5000ms: SELECT * FROM ledger_entries WHERE account_id = ?\n"
            "2026-10-30T14:45:05.100Z ERROR ledger-service: Database connection acquisition timed out waiting for active lock\n"
            "2026-10-30T14:45:06.200Z ERROR ledger-service: HTTP 500 - Ledger transaction settlement failure"
        ),
        metrics={
            "database_cpu_pct": 99.8,
            "iops_utilization_pct": 95.0,
            "avg_query_time_ms": 5420
        },
        config="DB_POOL_SIZE=5\nDB_POOL_TIMEOUT=5\nDATABASE_URL=sqlite+aiosqlite:///./payments.db",
        deployment="ledger-service v2.0.4 deployed at 2026-10-30T11:00:00Z",
        repository="https://github.com/coska/ledger-service",
        hypotheses=[
            {
                "title": "Database connection pool exhaustion under saturated query load",
                "confidence": 0.90,
                "status": "SUPPORTED",
                "next_action": "inspect_configuration:DB_POOL_SIZE"
            },
            {
                "title": "Network routing failure",
                "confidence": 0.05,
                "status": "REJECTED",
                "next_action": "inspect_runtime:network_metrics"
            }
        ],
        expected_root_cause="Database connection pool exhaustion caused by undersized pool configuration (DB_POOL_SIZE=5)",
        expected_remediation="DB_POOL_SIZE: 5 -> 30",
        expected_verification="VERIFIED"
    ),
]


def get_all_scenarios() -> List[DemoScenario]:
    return DEMO_SCENARIOS


def get_scenario_by_id(scenario_id: str) -> DemoScenario:
    for s in DEMO_SCENARIOS:
        if s.id == scenario_id:
            return s
    return DEMO_SCENARIOS[0]

