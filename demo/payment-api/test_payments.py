"""Integration & recovery verification test suite for payment-api."""
import os
import pytest
from pathlib import Path


def _get_pool_size() -> int:
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        content = env_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("DB_POOL_SIZE="):
                try:
                    return int(line.split("=")[1].strip())
                except ValueError:
                    pass
    return int(os.getenv("DB_POOL_SIZE", "5"))


def test_service_configuration():
    """Verify payment-api environment configuration exists."""
    env_file = Path(__file__).parent / ".env"
    assert env_file.exists(), ".env configuration must exist"


def test_database_pool_capacity():
    """Verify connection pool capacity under simulated concurrent load.
    
    Under production load (20 concurrent workers), a pool size of 5 will exhaust
    and trigger HTTP 500 errors. A pool size of >= 15 is required to prevent timeout.
    """
    pool_size = _get_pool_size()
    assert pool_size >= 15, (
        f"Database connection pool size {pool_size} is undersized for concurrent load "
        f"(requires >= 15). Connection pool exhaustion will occur."
    )


def test_health_metrics():
    """Verify health metrics status."""
    pool_size = _get_pool_size()
    # Health metric is healthy when pool size is safely scaled
    assert pool_size >= 15, f"Service health degraded: pool_size={pool_size}"

