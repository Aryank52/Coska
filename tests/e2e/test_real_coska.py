#!/usr/bin/env python
"""
End-to-end test for COSKA real integration.
Requires:
- AI_PROVIDER=nebius
- Real NEBIUS_API_KEY in .env
- Docker running for sandbox
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from app.agent.orchestrator import Orchestrator
from app.models import Incident, Severity
from app.services.storage import get_storage
from app.config import get_settings


async def test_real_coska_workflow():
    """Run full COSKA investigation with real AI provider."""
    print("=" * 60)
    print("COSKA REAL INTEGRATION E2E TEST")
    print("=" * 60)
    
    settings = get_settings()
    
    # Verify we're using real provider
    if settings.ai_provider != "nebius":
        print(f"ERROR: AI_PROVIDER is '{settings.ai_provider}', must be 'nebius' for real test")
        return False
    
    if not settings.nebius_api_key or settings.nebius_api_key.startswith("nvapi-"):
        print("ERROR: NEBIUS_API_KEY not properly configured")
        return False
    
    print(f"AI Provider: {settings.ai_provider}")
    print(f"Model: {settings.nebius_model}")
    print()
    
    # Create test incident
    storage = get_storage()
    incident = Incident(
        service="payment-api",
        severity=Severity.CRITICAL,
        description="HTTP 500 error rate increased from 1.2% to 38%. Users experiencing payment failures.",
        logs="""2026-10-29T10:15:23.456Z ERROR payment-api: connection pool exhausted
2026-10-29T10:15:24.123Z ERROR payment-api: timeout waiting for database connection
2026-10-29T10:15:24.789Z ERROR payment-api: connection pool exhausted
2026-10-29T10:15:25.001Z ERROR payment-api: timeout waiting for database connection
2026-10-29T10:15:25.555Z ERROR payment-api: connection pool exhausted
2026-10-29T10:15:26.234Z ERROR payment-api: HTTP 500 - Database connection timeout
2026-10-29T10:15:26.890Z ERROR payment-api: connection pool exhausted
2026-10-29T10:15:27.111Z ERROR payment-api: timeout waiting for database connection
2026-10-29T10:15:27.666Z ERROR payment-api: connection pool exhausted
2026-10-29T10:15:28.000Z ERROR payment-api: HTTP 500 - Database connection timeout
2026-10-29T10:15:28.555Z ERROR payment-api: connection pool exhausted
2026-10-29T10:15:29.123Z ERROR payment-api: timeout waiting for database connection
2026-10-29T10:15:29.777Z ERROR payment-api: connection pool exhausted
2026-10-29T10:15:30.001Z ERROR payment-api: HTTP 500 - Database connection timeout
... (17 total pool exhaustion events in 90 seconds)""",
        deployment="payment-api v1.8.2 deployed at 2026-10-29T10:10:00Z",
        repository="https://github.com/coska/payment-api",
        metadata={
            "configuration": "DB_POOL_SIZE=5\nDB_POOL_TIMEOUT=5\nDATABASE_URL=sqlite+aiosqlite:///./payments.db"
        }
    )
    
    storage = get_storage()
    storage.save_incident(incident)
    print(f"Created incident: {incident.id}")
    print()
    
    # Run investigation
    print("Starting investigation...")
    start_time = time.time()
    
    orchestrator = Orchestrator()
    state = await orchestrator.investigate(incident, auto_approve=True)
    
    duration = time.time() - start_time
    
    # Verify results
    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)
    
    success_checks = []
    
    # Check 1: Evidence collected
    evidence_ok = len(state.evidence) >= 5
    success_checks.append(("Evidence collected", evidence_ok, f"{len(state.evidence)} items"))
    
    # Check 2: Hypotheses generated
    hypotheses_ok = len(state.hypotheses) >= 3
    success_checks.append(("Hypotheses generated", hypotheses_ok, f"{len(state.hypotheses)} hypotheses"))
    
    # Check 3: Root cause identified
    root_cause_ok = state.root_cause is not None and "pool exhaustion" in state.root_cause.get("root_cause", "").lower()
    success_checks.append(("Root cause identified", root_cause_ok, state.root_cause.get('root_cause') if state.root_cause else "NONE"))
    
    # Check 4: Remediation generated
    remediation_ok = state.remediation is not None and "DB_POOL_SIZE" in state.remediation.exact_change
    success_checks.append(("Remediation generated", remediation_ok, state.remediation.exact_change if state.remediation else "NONE"))
    
    # Check 5: Verification attempted
    verification_ok = state.verification is not None
    success_checks.append(("Verification attempted", verification_ok, state.verification.verdict.value if state.verification else "NONE"))
    
    # Print results
    all_passed = True
    for name, passed, detail in success_checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {name}: {detail}")
        if not passed:
            all_passed = False
    
    # Summary
    passed_count = sum(1 for _, passed, _ in success_checks if passed)
    total_count = len(success_checks)
    
    print(f"\n{'=' * 60}")
    print(f"E2E TEST: {'PASSED' if all_passed else 'FAILED'} ({passed_count}/{total_count} checks passed)")
    print(f"Duration: {duration:.1f}s")
    print("=" * 60)
    
    return all_passed


async def main():
    print("COSKA End-to-End Real Integration Test")
    print("=" * 60)
    print(f"Python: {sys.version.split()[0]}")
    print()
    
    settings = get_settings()
    print(f"AI Provider: {settings.ai_provider}")
    print(f"Model: {settings.nebius_model}")
    print(f"Docker: {'Available' if settings.ai_provider == 'nebius' else 'N/A'}")
    print()
    
    if settings.ai_provider != "nebius":
        print("ERROR: AI_PROVIDER must be 'nebius' for real integration test")
        print("Set AI_PROVIDER=nebius in .env")
        return 1
    
    success = await test_real_coska_workflow()
    
    if success:
        print("\n✅ E2E TEST PASSED - COSKA real integration working!")
        return 0
    else:
        print("\n❌ E2E TEST FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))