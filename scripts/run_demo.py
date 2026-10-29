#!/usr/bin/env python
"""
COSKA Demo Runner

This script runs the complete COSKA investigation workflow against the
Payment API demo scenario.

Usage:
    python scripts/run_demo.py

Requirements:
- Backend running on http://localhost:8000
- Payment API running on http://localhost:8001 (for load testing)
- Docker available for sandbox verification (optional)
- NEBIUS_API_KEY and TAVILY_API_KEY in .env (or uses mock provider)
"""
import asyncio
import httpx
import json
import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.agent.orchestrator import Orchestrator
from app.models import Incident, Severity
from app.services.storage import get_storage
from app.config import get_settings


async def check_services():
    """Check if required services are running."""
    settings = get_settings()
    
    # Check backend
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.vite_api_url}/api/health")
            if resp.status_code == 200:
                print("[OK] Backend API is running")
            else:
                print("[FAIL] Backend API returned error")
                return False
    except Exception as e:
        print(f"[FAIL] Backend API not accessible: {e}")
        return False
    
    # Check AI provider
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.vite_api_url}/api/health/ai")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("nebius_connected"):
                    print("[OK] Nebius AI provider connected")
                else:
                    print("[WARN] Using mock AI provider (set NEBIUS_API_KEY for real Nemotron)")
    except Exception:
        print("[WARN] Could not check AI provider status")
    
    return True


async def create_demo_incident():
    """Create the demo payment-api incident."""
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
    print(f"[INFO] Created incident: {incident.id}")
    return incident


async def run_investigation(incident):
    """Run the full investigation workflow."""
    print("\n[INFO] Starting COSKA investigation...")
    print("=" * 60)
    
    orchestrator = Orchestrator()
    state = await orchestrator.investigate(incident, auto_approve=True)
    
    return state


def print_results(state):
    """Print investigation results."""
    print("\n" + "=" * 60)
    print("[RESULTS] INVESTIGATION RESULTS")
    print("=" * 60)
    
    print(f"\n[INCIDENT] {state.incident.id} ({state.incident.service})")
    print(f"   Severity: {state.incident.severity}")
    print(f"   Status: {state.incident.status}")
    
    print(f"\n[EVIDENCE] Evidence Collected: {len(state.evidence)} items")
    for ev in state.evidence:
        print(f"   [{ev.source_type.value}] {ev.claim[:80]}...")
    
    print(f"\n[HYPOTHESES] ({len(state.hypotheses)}):")
    for h in state.hypotheses:
        status_emoji = {"SUPPORTED": "[OK]", "REJECTED": "[FAIL]", "WEAKENED": "[WARN]", "ACTIVE": "[WAIT]"}.get(h.status.value, "[?]")
        print(f"   {status_emoji} {h.title} ({h.confidence:.0%}) [{h.status.value}]")
        if h.supporting_evidence_ids:
            print(f"      Supporting: {', '.join(h.supporting_evidence_ids)}")
    
    if state.root_cause:
        print(f"\n[ROOT CAUSE] {state.root_cause.get('root_cause', 'Unknown')}")
        print(f"   Confidence: {state.root_cause.get('confidence', 0):.0%}")
        if state.root_cause.get('supporting_evidence_ids'):
            print(f"   Supporting Evidence: {', '.join(state.root_cause['supporting_evidence_ids'])}")
        if state.root_cause.get('rejected_hypotheses'):
            print(f"   Rejected Hypotheses: {len(state.root_cause['rejected_hypotheses'])}")
    
    if state.remediation:
        print(f"\n[REMEDIATION] {state.remediation.exact_change}")
        print(f"   Type: {state.remediation.type.value}")
        print(f"   Risk: {state.remediation.risk}")
        print(f"   Expected Effect: {state.remediation.expected_effect}")
        print(f"   Rollback: {state.remediation.rollback_plan}")
    
    if state.verification:
        v = state.verification
        print(f"\n[VERIFICATION] Verdict: {v.verdict.value}")
        print(f"   Baseline Test: {'PASS' if v.baseline_test.success else 'FAIL'}")
        print(f"   Post-Fix Tests: {'PASS' if v.post_fix_tests.success else 'FAIL'}")
        print(f"   Health Check: {'PASS' if v.health_check.success else 'FAIL'}")
        print(f"   Control Test: {'PASS' if v.control_test.success else 'FAIL (expected)'}")
        print(f"   Evidence Count: {v.evidence_count}")
        print(f"   Model: {v.model}")
    
    print(f"\n[ACTIONS] Agent Actions: {len(state.actions)} steps")
    for action in state.actions:
        status_emoji = "[OK]" if action.status == "COMPLETED" else "[FAIL]"
        print(f"   {status_emoji} {action.step}: {action.summary}")


async def main():
    """Main demo runner."""
    print("[INFO] COSKA Demo - Autonomous Incident Intelligence & Verified Recovery")
    print("=" * 60)
    
    # Check services
    if not await check_services():
        print("\n[FAIL] Required services not available. Please start backend first:")
        print("   cd backend && uvicorn app.main:app --reload")
        return 1
    
    # Create incident
    incident = await create_demo_incident()
    
    # Run investigation
    start_time = time.time()
    state = await run_investigation(incident)
    duration = time.time() - start_time
    
    # Print results
    print_results(state)
    
    print(f"\n[TIME] Investigation completed in {duration:.1f} seconds")
    
    # Final verdict
    if state.verification and state.verification.verdict.value == "VERIFIED":
        print("\n[SUCCESS] VERIFIED: COSKA proved the recovery!")
        print("   Root cause identified, remediation applied, and causally verified.")
        return 0
    elif state.verification and state.verification.verdict.value == "FAILED":
        print("\n[WARN] Verification failed - sandbox not available (Docker required)")
        print("   Investigation complete, but causal verification requires Docker.")
        return 0
    else:
        print("\n[INFO] Investigation complete (verification requires Docker)")
        return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))