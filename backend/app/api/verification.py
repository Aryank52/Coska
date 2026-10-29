"""Verification API endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import structlog

from app.services.storage import get_storage
from app.api.dependencies import get_orchestrator

logger = structlog.get_logger()
router = APIRouter()


class VerifyRequest(BaseModel):
    incident_id: str


class VerifyResponse(BaseModel):
    incident_id: str
    verdict: str
    baseline_test: str
    post_fix_tests: str
    health_check: str
    control_test: str
    details: dict


@router.post("/incidents/{incident_id}/verify", response_model=VerifyResponse)
async def verify_incident(incident_id: str, request: VerifyRequest):
    """Run verification for an incident."""
    storage = get_storage()
    orchestrator = get_orchestrator()
    
    state = orchestrator.get_investigation(incident_id)
    if not state or not state.verification:
        raise HTTPException(status_code=404, detail="Verification not available")
    
    v = state.verification
    return VerifyResponse(
        incident_id=incident_id,
        verdict=v.verdict.value,
        baseline_test="PASSED" if v.baseline_test.success else "FAILED",
        post_fix_tests="PASSED" if v.post_fix_tests.success else "FAILED",
        health_check="PASSED" if v.health_check.success else "FAILED",
        control_test="FAILED (as expected)" if not v.control_test.success else "PASSED (unexpected)",
        details=v.details
    )


@router.get("/incidents/{incident_id}/report")
async def get_verification_report(incident_id: str):
    """Get verification report for an incident."""
    storage = get_storage()
    verification = storage.get_verification(incident_id)
    if not verification:
        raise HTTPException(status_code=404, detail="Verification report not found")
    
    return {
        "incident_id": incident_id,
        "verdict": verification.verdict.value,
        "root_cause": "See root-cause endpoint",
        "remediation": "See remediation endpoint",
        "baseline_test": verification.baseline_test,
        "post_fix_tests": verification.post_fix_tests,
        "health_check": verification.health_check,
        "control_test": verification.control_test,
        "evidence_count": verification.evidence_count,
        "model": verification.model,
        "details": verification.details,
        "timestamp": verification.created_at
    }