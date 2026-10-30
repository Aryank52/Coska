"""Enhanced API endpoints for COSKA advanced features."""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from app.models import Incident, Severity, IncidentStatus
from app.services.storage import get_storage
from app.services.rag import get_rag_engine, RAGSearchResult
from app.services.incident_intelligence import get_intelligence_engine, IncidentIntelligence
from app.services.evidence_graph import build_evidence_graph, EvidenceGraph
from app.services.service_map import get_service_map_engine, BlastRadius
from app.services.demo_scenarios import get_scenario, list_scenarios, create_incident_from_scenario, ALL_SCENARIOS
from app.services.planner import get_planner, InvestigationPlan, PlanResult
from app.api.dependencies import get_orchestrator
from app.agent.orchestrator import Orchestrator

logger = structlog.get_logger()
router = APIRouter()


# =============================================================================
# Incident Intelligence
# =============================================================================

@router.get("/incidents/{incident_id}/intelligence", response_model=IncidentIntelligence)
async def get_incident_intelligence(
    incident_id: str,
    use_ai: bool = Query(False, description="Use AI enhancement for semantic interpretation")
):
    """Get structured incident intelligence analysis."""
    storage = get_storage()
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    intelligence_engine = get_intelligence_engine()
    intelligence = await intelligence_engine.analyze(incident, use_ai=use_ai)
    return intelligence


# =============================================================================
# RAG Knowledge Retrieval
# =============================================================================

class RAGSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(3, ge=1, le=10)
    include_trace: bool = True


@router.post("/rag/search", response_model=RAGSearchResult)
async def search_knowledge_base(request: RAGSearchRequest):
    """Search the offline knowledge base (runbooks, postmortems, architecture docs)."""
    rag_engine = get_rag_engine()
    result = rag_engine.search(request.query, top_k=request.top_k, include_trace=request.include_trace)
    return result


@router.get("/rag/documents")
async def list_knowledge_documents():
    """List all available knowledge documents."""
    rag_engine = get_rag_engine()
    return {"documents": rag_engine.list_documents()}


@router.get("/rag/documents/{doc_id}")
async def get_knowledge_document(doc_id: str):
    """Get a specific knowledge document by ID."""
    rag_engine = get_rag_engine()
    doc = rag_engine.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/rag/categories")
async def list_knowledge_categories():
    """List all knowledge categories."""
    rag_engine = get_rag_engine()
    return {"categories": rag_engine.list_categories()}


# =============================================================================
# Evidence Graph
# =============================================================================

@router.get("/incidents/{incident_id}/evidence-graph", response_model=EvidenceGraph)
async def get_evidence_graph(incident_id: str):
    """Get evidence graph for visualization."""
    storage = get_storage()
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    evidence = storage.get_evidence(incident_id)
    hypotheses = storage.get_hypotheses(incident_id)
    remediation = storage.get_remediation(incident_id)
    verification = storage.get_verification(incident_id)
    
    # Get root cause from investigation state
    orchestrator = get_orchestrator()
    state = orchestrator.get_investigation(incident_id)
    root_cause = state.root_cause if state else None
    
    # Get RAG documents
    rag_docs = []
    if state and state.knowledge_docs:
        rag_docs = state.knowledge_docs
    
    graph = build_evidence_graph(
        incident=incident,
        evidence=evidence,
        hypotheses=hypotheses,
        root_cause=root_cause,
        remediation=remediation.dict() if remediation else None,
        verification=verification.dict() if verification else None,
        rag_documents=rag_docs
    )
    
    return graph


@router.get("/incidents/{incident_id}/evidence-graph/cytoscape")
async def get_evidence_graph_cytoscape(incident_id: str):
    """Get evidence graph in Cytoscape.js format for frontend visualization."""
    graph = await get_evidence_graph(incident_id)
    builder = EvidenceGraphBuilder()
    # Rebuild to get elements
    from app.services.evidence_graph import EvidenceGraphBuilder
    builder = EvidenceGraphBuilder()
    builder.build(
        incident=Incident(**graph.incident_id),  # This needs fixing
        evidence=[],
        hypotheses=[]
    )
    # For now, return the graph data
    return {
        "elements": graph.nodes + graph.edges,  # Simplified
        "layout": graph.layout
    }


# =============================================================================
# Service Map & Blast Radius
# =============================================================================

@router.get("/service-map", response_model=Dict[str, Any])
async def get_service_map():
    """Get the complete service dependency map."""
    engine = get_service_map_engine()
    return engine.get_service_map().model_dump()


@router.get("/service-map/cytoscape")
async def get_service_map_cytoscape():
    """Get service map in Cytoscape.js format."""
    engine = get_service_map_engine()
    return {"elements": engine.to_cytoscape_elements()}


@router.get("/service-map/status")
async def get_service_status_overview():
    """Get overview of all service statuses."""
    engine = get_service_map_engine()
    return engine.get_service_status_overview()


@router.get("/service-map/blast-radius/{service_id}", response_model=BlastRadius)
async def get_blast_radius(service_id: str):
    """Calculate blast radius for a service failure."""
    engine = get_service_map_engine()
    return engine.calculate_blast_radius(service_id)


@router.post("/service-map/status/{service_id}")
async def update_service_status(service_id: str, status: str):
    """Update a service's status."""
    from app.services.service_map import ServiceStatus
    try:
        service_status = ServiceStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    engine = get_service_map_engine()
    engine.update_service_status(service_id, service_status)
    return {"service_id": service_id, "status": status}


# =============================================================================
# Demo Scenarios
# =============================================================================

@router.get("/demo/scenarios")
async def list_demo_scenarios():
    """List all available demo scenarios."""
    return {"scenarios": list_scenarios()}


@router.get("/demo/scenarios/{scenario_id}")
async def get_demo_scenario(scenario_id: str):
    """Get a specific demo scenario."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario.model_dump()


@router.post("/demo/scenarios/{scenario_id}/run")
async def run_demo_scenario(
    scenario_id: str,
    background_tasks: BackgroundTasks,
    auto_approve: bool = False
):
    """Run a demo scenario investigation."""
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Create incident from scenario
    incident_data = create_incident_from_scenario(scenario_id)
    
    storage = get_storage()
    incident = Incident(
        id=f"INC-DEMO-{scenario_id.upper()}-{datetime.utcnow().strftime('%H%M%S')}",
        service=incident_data["service"],
        severity=Severity(incident_data["severity"]),
        description=incident_data["description"],
        logs=incident_data["logs"],
        deployment=incident_data["deployment"],
        repository=incident_data["repository"],
        metadata=incident_data["metadata"],
        status=IncidentStatus.RECEIVED,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    storage.save_incident(incident)
    
    # Start investigation
    orchestrator = get_orchestrator()
    background_tasks.add_task(orchestrator.investigate, incident, auto_approve)
    
    return {
        "incident_id": incident.id,
        "scenario_id": scenario_id,
        "status": "started",
        "message": f"Demo scenario '{scenario.name}' investigation started"
    }


@router.post("/demo/reset")
async def reset_demo_data():
    """Reset demo data (clear incidents, keep runbooks)."""
    storage = get_storage()
    with storage._conn() as conn:
        conn.executescript("""
            DELETE FROM incidents;
            DELETE FROM evidence;
            DELETE FROM hypotheses;
            DELETE FROM remediations;
            DELETE FROM verification_runs;
            DELETE FROM agent_actions;
            DELETE FROM investigations;
            -- Keep incident_memory for demo continuity
        """)
    return {"status": "reset", "message": "Demo data cleared, runbooks preserved"}


# =============================================================================
# Agentic Planner
# =============================================================================

class PlanRequest(BaseModel):
    incident_id: str
    auto_execute: bool = False


@router.post("/planner/plan", response_model=InvestigationPlan)
async def create_investigation_plan(request: PlanRequest):
    """Create an investigation plan for an incident."""
    storage = get_storage()
    incident = storage.get_incident(request.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get existing evidence and hypotheses
    evidence = storage.get_evidence(request.incident_id)
    hypotheses = storage.get_hypotheses(request.incident_id)
    
    # Get intelligence
    intelligence_engine = get_intelligence_engine()
    intelligence = intelligence_engine.extract_deterministic(incident)
    
    # Create plan
    planner = get_planner()
    plan = await planner.create_plan(incident, intelligence, evidence, hypotheses)
    return plan


@router.post("/planner/execute", response_model=PlanResult)
async def execute_investigation_plan(request: PlanRequest, background_tasks: BackgroundTasks):
    """Create and execute an investigation plan."""
    storage = get_storage()
    incident = storage.get_incident(request.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    # Get existing evidence and hypotheses
    evidence = storage.get_evidence(request.incident_id)
    hypotheses = storage.get_hypotheses(request.incident_id)
    
    # Get intelligence
    intelligence_engine = get_intelligence_engine()
    intelligence = intelligence_engine.extract_deterministic(incident)
    
    # Create and execute plan
    planner = get_planner()
    plan = await planner.create_plan(incident, intelligence, evidence, hypotheses)
    
    if request.auto_execute:
        # Execute in background
        background_tasks.add_task(planner.execute_plan, plan, incident)
        return PlanResult(
            success=True,
            completed_steps=0,
            total_steps=len(plan.steps),
            final_state="executing",
            trace=[{"event": "plan_execution_started", "steps": len(plan.steps)}]
        )
    
    return PlanResult(
        success=True,
        completed_steps=0,
        total_steps=len(plan.steps),
        final_state="planned",
        trace=[{"event": "plan_created", "steps": len(plan.steps)}]
    )


# =============================================================================
# Hypothesis Decisions
# =============================================================================

@router.get("/incidents/{incident_id}/hypotheses/{hypothesis_id}/decisions")
async def get_hypothesis_decisions(incident_id: str, hypothesis_id: str):
    """Get AI decision explanations for a hypothesis."""
    from app.agent.hypotheses import get_hypothesis_engine
    engine = get_hypothesis_engine()
    if hasattr(engine, 'enhanced'):
        decisions = engine.enhanced.get_decision_history(hypothesis_id)
    else:
        decisions = []
    return {"hypothesis_id": hypothesis_id, "decisions": [d.model_dump() for d in decisions]}


# =============================================================================
# Verification Receipt
# =============================================================================

@router.get("/incidents/{incident_id}/verification-receipt")
async def get_verification_receipt(incident_id: str):
    """Get complete verification receipt for an incident."""
    storage = get_storage()
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    verification = storage.get_verification(incident_id)
    remediation = storage.get_remediation(incident_id)
    root_cause = None
    
    orchestrator = get_orchestrator()
    state = orchestrator.get_investigation(incident_id)
    if state:
        root_cause = state.root_cause
    
    # Build comprehensive receipt
    receipt = {
        "incident_id": incident_id,
        "service": incident.service,
        "timestamp": datetime.utcnow().isoformat(),
        "root_cause": root_cause.get("root_cause") if root_cause else None,
        "root_cause_confidence": root_cause.get("confidence") if root_cause else None,
        "remediation": remediation.dict() if remediation else None,
        "verification": verification.dict() if verification else None,
        "evidence_count": len(storage.get_evidence(incident_id)),
        "hypotheses_count": len(storage.get_hypotheses(incident_id)),
        "ai_provider": "mock",  # Would come from settings
        "knowledge_sources": state.knowledge_docs if state else [],
        "tavily_usage": "disabled",  # Would track actual usage
        "final_determination": verification.verdict.value if verification else "UNVERIFIED"
    }
    
    return receipt


# =============================================================================
# Incident Report
# =============================================================================

@router.get("/incidents/{incident_id}/report")
async def get_incident_report(incident_id: str, format: str = Query("json", regex="^(json|markdown)$")):
    """Generate comprehensive incident report."""
    storage = get_storage()
    incident = storage.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    evidence = storage.get_evidence(incident_id)
    hypotheses = storage.get_hypotheses(incident_id)
    remediation = storage.get_remediation(incident_id)
    verification = storage.get_verification(incident_id)
    actions = storage.get_actions(incident_id)
    
    orchestrator = get_orchestrator()
    state = orchestrator.get_investigation(incident_id)
    root_cause = state.root_cause if state else None
    knowledge_docs = state.knowledge_docs if state else []
    
    report = {
        "executive_summary": {
            "incident_id": incident_id,
            "service": incident.service,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "description": incident.description,
            "created_at": incident.created_at,
            "resolved_at": incident.updated_at if incident.status == IncidentStatus.RESOLVED else None
        },
        "incident_timeline": state.timeline if state else [],
        "affected_services": [incident.service],
        "evidence": [e.dict() for e in evidence],
        "competing_hypotheses": [h.dict() for h in hypotheses],
        "root_cause": root_cause,
        "remediation": remediation.dict() if remediation else None,
        "verification": verification.dict() if verification else None,
        "knowledge_sources": knowledge_docs,
        "external_research": state.web_sources if state else [],
        "lessons_learned": [],
        "recommended_prevention": []
    }
    
    if format == "markdown":
        # Generate markdown report
        md = f"""# Incident Report: {incident_id}

## Executive Summary
- **Incident ID**: {incident_id}
- **Service**: {incident.service}
- **Severity**: {incident.severity.value}
- **Status**: {incident.status.value}
- **Description**: {incident.description}
- **Created**: {incident.created_at}
- **Resolved**: {incident.updated_at if incident.status == IncidentStatus.RESOLVED else 'N/A'}

## Root Cause
{root_cause.get('root_cause', 'Not determined') if root_cause else 'Not determined'}
**Confidence**: {root_cause.get('confidence', 0):.0% if root_cause else 'N/A'}

## Remediation
{remediation.exact_change if remediation else 'None'}
**Description**: {remediation.description if remediation else 'N/A'}
**Risk**: {remediation.risk if remediation else 'N/A'}

## Verification
**Verdict**: {verification.verdict.value if verification else 'N/A'}
- Baseline: {'PASSED' if verification and verification.baseline_test == 'PASSED' else 'FAILED'}
- Post-Fix: {'PASSED' if verification and verification.post_fix_tests == 'PASSED' else 'FAILED'}
- Health: {'PASSED' if verification and verification.health_check == 'PASSED' else 'FAILED'}
- Control: {'PASSED' if verification and verification.control_test == 'PASSED' else 'FAILED'}

## Evidence ({len(evidence)} items)
"""
        for e in evidence:
            md += f"- **{e.id}** ({e.source_type.value}): {e.claim}\n"
        
        md += f"\n## Competing Hypotheses ({len(hypotheses)})\n"
        for h in hypotheses:
            md += f"- **{h.id}**: {h.title} ({h.confidence:.0%}) - {h.status.value}\n"
        
        return {"format": "markdown", "content": md}
    
    return report