"""Incidents API endpoints."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid
import structlog

from app.models import Incident, Severity, IncidentStatus
from app.services.storage import get_storage
from app.api.dependencies import get_orchestrator

logger = structlog.get_logger()
router = APIRouter()


class IncidentCreate(BaseModel):
    service: str = Field(..., min_length=1, max_length=100)
    severity: Severity
    description: str = Field(..., min_length=1, max_length=5000)
    logs: Optional[str] = None
    deployment: Optional[str] = None
    repository: Optional[str] = None
    metadata: Optional[dict] = {}


class IncidentResponse(BaseModel):
    id: str
    service: str
    severity: Severity
    description: str
    logs: Optional[str]
    deployment: Optional[str]
    repository: Optional[str]
    metadata: dict
    status: IncidentStatus
    created_at: datetime
    updated_at: datetime


class InvestigateRequest(BaseModel):
    auto_approve: bool = False


@router.post("/incidents", response_model=IncidentResponse, status_code=201)
async def create_incident(incident: IncidentCreate):
    """Create a new incident."""
    storage = get_storage()
    
    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()
    
    incident_data = Incident(
        id=incident_id,
        service=incident.service,
        severity=incident.severity,
        description=incident.description,
        logs=incident.logs,
        deployment=incident.deployment,
        repository=incident.repository,
        metadata=incident.metadata or {},
        status=IncidentStatus.RECEIVED,
        created_at=now,
        updated_at=now,
    )
    
    storage.save_incident(incident_data)
    logger.info("incident_created", incident_id=incident_id, service=incident.service)
    
    return IncidentResponse(
        id=incident_data.id,
        service=incident_data.service,
        severity=incident_data.severity,
        description=incident_data.description,
        logs=incident_data.logs,
        deployment=incident_data.deployment,
        repository=incident_data.repository,
        metadata=incident_data.metadata,
        status=incident_data.status,
        created_at=incident_data.created_at,
        updated_at=incident_data.updated_at,
    )


@router.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents():
    """List all incidents."""
    storage = get_storage()
    incidents = storage.list_incidents()
    return [
        IncidentResponse(
            id=i.id, service=i.service, severity=i.severity, description=i.description,
            logs=i.logs, deployment=i.deployment, repository=i.repository,
            metadata=i.metadata, status=i.status, created_at=i.created_at, updated_at=i.updated_at
        )
        for i in incidents
    ]


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(incident_id: str):
    """Get incident by ID."""
    storage = get_storage()
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    return IncidentResponse(
        id=incident.id, service=incident.service, severity=incident.severity,
        description=incident.description, logs=incident.logs,
        deployment=incident.deployment, repository=incident.repository,
        metadata=incident.metadata, status=incident.status,
        created_at=incident.created_at, updated_at=incident.updated_at
    )


@router.post("/incidents/{incident_id}/investigate")
async def investigate_incident(
    incident_id: str, 
    request: InvestigateRequest,
    background_tasks: BackgroundTasks
):
    """Start investigation for an incident."""
    storage = get_storage()
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    orchestrator = get_orchestrator()
    
    # Run investigation in background
    background_tasks.add_task(orchestrator.investigate, incident, request.auto_approve)
    
    return {"incident_id": incident_id, "status": "started", "message": "Investigation started in background"}


@router.get("/incidents/{incident_id}/timeline")
async def get_incident_timeline(incident_id: str):
    """Get incident timeline."""
    orchestrator = get_orchestrator()
    state = orchestrator.get_investigation(incident_id)
    if not state:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return {"incident_id": incident_id, "timeline": state.timeline}


@router.get("/incidents/{incident_id}/evidence")
async def get_incident_evidence(incident_id: str):
    """Get incident evidence."""
    storage = get_storage()
    evidence = storage.get_evidence(incident_id)
    return {"incident_id": incident_id, "evidence": [e.dict() for e in evidence]}


@router.get("/incidents/{incident_id}/hypotheses")
async def get_incident_hypotheses(incident_id: str):
    """Get incident hypotheses."""
    storage = get_storage()
    hypotheses = storage.get_hypotheses(incident_id)
    return {"incident_id": incident_id, "hypotheses": [h.dict() for h in hypotheses]}


@router.get("/incidents/{incident_id}/actions")
async def get_incident_actions(incident_id: str):
    """Get agent actions for an incident."""
    orchestrator = get_orchestrator()
    actions = orchestrator.get_actions(incident_id)
    return {"incident_id": incident_id, "actions": [a.dict() for a in actions]}


@router.get("/incidents/{incident_id}/root-cause")
async def get_incident_root_cause(incident_id: str):
    """Get root cause analysis."""
    orchestrator = get_orchestrator()
    state = orchestrator.get_investigation(incident_id)
    if not state or not state.root_cause:
        raise HTTPException(status_code=404, detail="Root cause not available")
    return {"incident_id": incident_id, "root_cause": state.root_cause}


@router.get("/incidents/{incident_id}/remediation")
async def get_incident_remediation(incident_id: str):
    """Get remediation plan."""
    storage = get_storage()
    remediation = storage.get_remediation(incident_id)
    if not remediation:
        raise HTTPException(status_code=404, detail="Remediation not available")
    return {"incident_id": incident_id, "remediation": remediation.dict()}


@router.post("/incidents/{incident_id}/simulate-fix")
async def simulate_fix(incident_id: str):
    """Simulate a fix in sandbox (dry run)."""
    storage = get_storage()
    remediation = storage.get_remediation(incident_id)
    if not remediation:
        raise HTTPException(status_code=404, detail="No remediation to simulate")
    
    return {
        "incident_id": incident_id,
        "status": "simulated",
        "remediation": remediation.exact_change,
        "message": "Fix simulation completed (dry run)"
    }


@router.post("/incidents/{incident_id}/apply-fix")
async def apply_fix(incident_id: str, background_tasks: BackgroundTasks):
    """Apply fix to sandbox and run verification."""
    storage = get_storage()
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    orchestrator = get_orchestrator()
    
    # Run full investigation with auto-approve for verification
    background_tasks.add_task(orchestrator.investigate, incident, True)
    
    return {"incident_id": incident_id, "status": "verification_started", "message": "Fix application and verification started"}