"""Demo and Judge Mode API endpoints."""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from app.demo.scenarios import get_all_scenarios, get_scenario_by_id, DemoScenario
from app.models import Incident, Severity, IncidentStatus
from app.services.storage import get_storage
from app.services.rag import get_rag_engine
from app.api.dependencies import get_orchestrator

router = APIRouter()


class RunDemoRequest(BaseModel):
    scenario_id: str = "payment_pool_exhaustion"
    auto_approve: bool = True


@router.get("/demo/scenarios", response_model=List[DemoScenario])
async def list_demo_scenarios():
    """List all pre-configured Judge Mode demo scenarios."""
    return get_all_scenarios()


@router.post("/demo/run")
async def run_demo_scenario(request: RunDemoRequest):
    """Execute complete autonomous investigation and verification for a selected demo scenario."""
    scenario = get_scenario_by_id(request.scenario_id)
    storage = get_storage()
    orchestrator = get_orchestrator()

    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()

    incident = Incident(
        id=incident_id,
        service=scenario.service,
        severity=Severity(scenario.severity),
        description=scenario.description,
        logs=scenario.logs,
        deployment=scenario.deployment,
        repository=scenario.repository,
        metadata={"configuration": scenario.config, "metrics": scenario.metrics},
        status=IncidentStatus.RECEIVED,
        created_at=now,
        updated_at=now,
    )
    storage.save_incident(incident)

    # Execute investigation synchronously so the judge UI receives instant completed state
    state = await orchestrator.investigate(incident, auto_approve=request.auto_approve)
    return state.to_dict()


@router.get("/rag/search")
async def search_rag_knowledge(q: str = Query(..., description="Query for technical runbooks")):
    """Offline Knowledge Retrieval (RAG) search endpoint."""
    rag = get_rag_engine()
    results = rag.search(q, top_k=3)
    return {
        "query": q,
        "results_count": len(results),
        "top_source": results[0].title if results else None,
        "documents": [d.model_dump() for d in results]
    }


@router.get("/incidents/{incident_id}/graph")
async def get_incident_graph(incident_id: str):
    """Generate structured Evidence & Causal Graph linking incident, evidence, hypotheses, root cause, remediation, and verification."""
    storage = get_storage()
    orchestrator = get_orchestrator()

    state = orchestrator.get_investigation(incident_id)
    state_dict = state.to_dict() if state else storage.get_investigation_state(incident_id)

    if not state_dict:
        # Fallback to incident if not yet investigated
        inc = storage.get_incident(incident_id)
        if not inc:
            raise HTTPException(status_code=404, detail="Incident not found")
        return {
            "nodes": [{"id": inc.id, "label": inc.service, "type": "incident", "severity": inc.severity}],
            "edges": []
        }

    nodes = []
    edges = []

    # 1. Incident node
    inc_id = state_dict.get("incident_id", incident_id)
    nodes.append({
        "id": inc_id,
        "label": f"Incident: {state_dict.get('incident', {}).get('service', 'Service')}",
        "type": "incident",
        "status": state_dict.get("current_phase", "INTAKE")
    })

    # 2. Evidence nodes
    evidence_list = state_dict.get("evidence", [])
    for ev in evidence_list[:12]:  # Limit for visual clarity
        ev_id = ev.get("id", "E-?")
        nodes.append({
            "id": ev_id,
            "label": f"[{ev.get('source_type')}] {ev.get('claim', '')[:35]}...",
            "type": "evidence",
            "source_type": ev.get("source_type"),
            "confidence": ev.get("confidence")
        })
        edges.append({
            "source": inc_id,
            "target": ev_id,
            "label": "yielded"
        })

    # 3. Hypothesis nodes
    hypotheses = state_dict.get("hypotheses", [])
    for idx, hyp in enumerate(hypotheses):
        h_id = hyp.get("id", f"H-{idx+1}")
        nodes.append({
            "id": h_id,
            "label": hyp.get("title", "Hypothesis"),
            "type": "hypothesis",
            "status": hyp.get("status", "ACTIVE"),
            "confidence": hyp.get("confidence", 0.5)
        })
        # Link from supporting evidence
        for sup_ev in hyp.get("supporting_evidence_ids", []):
            if any(n["id"] == sup_ev for n in nodes):
                edges.append({
                    "source": sup_ev,
                    "target": h_id,
                    "label": "supports"
                })
        if not hyp.get("supporting_evidence_ids"):
            edges.append({
                "source": inc_id,
                "target": h_id,
                "label": "considered"
            })

    # 4. Root cause node
    root_cause = state_dict.get("root_cause")
    if root_cause and root_cause.get("root_cause"):
        rc_id = "RC-1"
        nodes.append({
            "id": rc_id,
            "label": f"Root Cause: {root_cause.get('root_cause', '')[:40]}...",
            "type": "root_cause",
            "confidence": root_cause.get("confidence", 0.9)
        })
        # Connect winning hypotheses or supporting evidence
        for sup_ev in root_cause.get("supporting_evidence_ids", []):
            if any(n["id"] == sup_ev for n in nodes):
                edges.append({
                    "source": sup_ev,
                    "target": rc_id,
                    "label": "proves"
                })
        # Link supported hypothesis to root cause
        for hyp in hypotheses:
            if hyp.get("status") == "SUPPORTED":
                edges.append({
                    "source": hyp.get("id", "H-1"),
                    "target": rc_id,
                    "label": "explains"
                })

        # 5. Remediation node
        remediation = state_dict.get("remediation")
        if remediation and remediation.get("exact_change"):
            rem_id = "REM-1"
            nodes.append({
                "id": rem_id,
                "label": f"Fix: {remediation.get('exact_change')}",
                "type": "remediation",
                "risk": remediation.get("risk", "LOW")
            })
            edges.append({
                "source": rc_id,
                "target": rem_id,
                "label": "resolves"
            })

            # 6. Verification node
            verif = state_dict.get("verification_result")
            if verif:
                ver_id = "VER-1"
                verdict = verif.get("verdict", "VERIFIED")
                nodes.append({
                    "id": ver_id,
                    "label": f"Verification: {verdict}",
                    "type": "verification",
                    "verdict": verdict
                })
                edges.append({
                    "source": rem_id,
                    "target": ver_id,
                    "label": "verified_by"
                })

    return {
        "incident_id": incident_id,
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges)
    }

