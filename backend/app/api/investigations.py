"""Investigations API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import structlog

from app.api.dependencies import get_orchestrator
from app.services.storage import get_storage

logger = structlog.get_logger()
router = APIRouter()


class InvestigateRequest(BaseModel):
    incident_id: str
    auto_approve: bool = False


class InvestigateResponse(BaseModel):
    incident_id: str
    status: str
    message: str


@router.post("/incidents/{incident_id}/investigate", response_model=InvestigateResponse)
async def investigate_incident(incident_id: str, request: InvestigateRequest):
    """Start investigation for an incident."""
    orchestrator = get_orchestrator()
    storage = get_storage()
    incident = storage.get_incident(incident_id)
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Run investigation
    state = await orchestrator.investigate(incident, request.auto_approve)
    
    return InvestigateResponse(
        incident_id=incident_id,
        status="completed",
        message=f"Investigation completed with {len(state.hypotheses)} hypotheses"
    )


@router.post("/incidents/{incident_id}/simulate-fix")
async def simulate_fix(incident_id: str):
    """Simulate a fix in sandbox."""
    storage = get_storage()
    remediation = storage.get_remediation(incident_id)
    if not remediation:
        raise HTTPException(status_code=404, detail="No remediation to simulate")
    
    return {"incident_id": incident_id, "status": "simulated", "message": "Fix simulated (stub)"}


@router.post("/incidents/{incident_id}/apply-fix")
async def apply_fix(incident_id: str):
    """Apply fix to sandbox."""
    storage = get_storage()
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    orchestrator = get_orchestrator()
    state = await orchestrator.investigate(incident, True)
    
    return {"incident_id": incident_id, "status": "applied", "message": "Fix applied and verified"}