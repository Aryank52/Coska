"""Investigations API endpoints."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import structlog

from app.api.dependencies import get_orchestrator
from app.services.storage import get_storage

logger = structlog.get_logger()
router = APIRouter()


class InvestigateRequest(BaseModel):
    auto_approve: bool = False
    run_id: Optional[str] = None


class InvestigateResponse(BaseModel):
    incident_id: str
    status: str
    message: str
    run_id: Optional[str] = None


@router.get("/incidents/{incident_id}/investigation")
async def get_investigation_state(incident_id: str):
    """Get full investigation state including phase, timeline, and results."""
    orchestrator = get_orchestrator()
    storage = get_storage()
    
    state = orchestrator.get_investigation(incident_id)
    if state:
        return state.to_dict()
    
    persisted = storage.get_investigation_state(incident_id)
    if persisted:
        return persisted
    
    raise HTTPException(status_code=404, detail="Investigation not found for this incident")


@router.get("/incidents/{incident_id}/state")
async def get_investigation_summary(incident_id: str):
    """Get summary of current investigation progress."""
    orchestrator = get_orchestrator()
    state = orchestrator.get_investigation(incident_id)
    if not state:
        storage = get_storage()
        persisted = storage.get_investigation_state(incident_id)
        if persisted:
            return {
                "incident_id": incident_id,
                "current_phase": persisted.get("current_phase"),
                "hypotheses_count": len(persisted.get("hypotheses", [])),
                "evidence_count": len(persisted.get("evidence", [])),
                "has_root_cause": bool(persisted.get("root_cause")),
                "has_remediation": bool(persisted.get("remediation")),
                "verdict": persisted.get("verification_result", {}).get("verdict") if persisted.get("verification_result") else None
            }
        raise HTTPException(status_code=404, detail="Investigation state not found")

    return {
        "incident_id": incident_id,
        "run_id": state.run_id,
        "current_phase": state.current_phase.value,
        "step_count": state.step_count,
        "hypotheses_count": len(state.hypotheses),
        "evidence_count": len(state.evidence),
        "has_root_cause": bool(state.root_cause),
        "has_remediation": bool(state.remediation),
        "verdict": state.verification.verdict.value if state.verification else None,
        "errors": state.errors
    }
