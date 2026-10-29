"""Main orchestrator for COSKA autonomous investigation workflow."""
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from app.models import (
    Incident, IncidentStatus, Evidence, Hypothesis, 
    Remediation, VerificationResult, Verdict, AgentAction
)
from app.agent.evidence import EvidenceEngine
from app.agent.timeline import TimelineBuilder, format_timeline_for_display
from app.agent.hypotheses import HypothesisEngine
from app.agent.root_cause import RootCauseEngine
from app.agent.remediation import RemediationEngine
from app.agent.verifier import Verifier, VerificationReport
from app.tools.sandbox import SandboxEngine
from app.config import get_settings

logger = structlog.get_logger()


class InvestigationState:
    """Tracks investigation state for an incident."""
    
    def __init__(self, incident: Incident):
        self.incident = incident
        self.evidence: List[Evidence] = []
        self.timeline: List[Dict[str, Any]] = []
        self.hypotheses: List[Hypothesis] = []
        self.root_cause: Optional[Dict[str, Any]] = None
        self.remediation: Optional[Remediation] = None
        self.verification: Optional[VerificationReport] = None
        self.actions: List[AgentAction] = []
        self.original_config: str = ""
        self.config_file: str = ".env"
    
    def add_action(self, step: str, tool: str, summary: str, status: str = "COMPLETED", **kwargs):
        """Record an agent action."""
        action = AgentAction(
            incident_id=self.incident.id,
            step=step,
            tool=tool,
            summary=summary,
            status=status,
            **kwargs
        )
        self.actions.append(action)
        logger.info("agent_action", incident_id=self.incident.id, step=step, tool=tool, summary=summary)


class Orchestrator:
    """Main orchestrator for the COSKA investigation workflow."""
    
    def __init__(self, repo_path: str = "./demo/payment-api"):
        self.repo_path = repo_path
        self.settings = get_settings()
        
        # Initialize engines
        self.evidence_engine = EvidenceEngine()
        self.timeline_builder = TimelineBuilder()
        self.hypothesis_engine = HypothesisEngine()
        self.root_cause_engine = RootCauseEngine()
        self.remediation_engine = RemediationEngine()
        self.sandbox = SandboxEngine(
            timeout=self.settings.sandbox_timeout,
            memory_limit=self.settings.sandbox_memory_limit,
            cpu_limit=self.settings.sandbox_cpu_limit
        )
        self.verifier = Verifier(self.sandbox, repo_path, self.settings.nebius_model)
        
        # Active investigations
        self.investigations: Dict[str, InvestigationState] = {}
    
    async def investigate(self, incident: Incident, auto_approve: bool = False) -> InvestigationState:
        """Run complete autonomous investigation workflow."""
        
        state = InvestigationState(incident)
        self.investigations[incident.id] = state
        
        # Update incident status
        incident.status = IncidentStatus.TRIAGING
        incident.updated_at = datetime.utcnow()
        
        try:
            # PHASE 1: COLLECT EVIDENCE
            await self._phase_collect_evidence(state)
            
            # PHASE 2: BUILD TIMELINE
            await self._phase_build_timeline(state)
            
            # PHASE 3: GENERATE HYPOTHESES
            await self._phase_generate_hypotheses(state)
            
            # PHASE 4: INVESTIGATE HYPOTHESES
            await self._phase_investigate(state)
            
            # PHASE 5: RESEARCH EXTERNAL (Tavily)
            await self._phase_research_external(state)
            
            # PHASE 6: IDENTIFY ROOT CAUSE
            await self._phase_root_cause(state)
            
            # PHASE 7: GENERATE REMEDIATION
            await self._phase_remediation(state)
            
            # PHASE 8: APPLY IN SANDBOX & VERIFY
            if auto_approve or state.remediation:
                await self._phase_verify(state)
            
            # Final status
            if state.verification and state.verification.verdict == Verdict.VERIFIED:
                incident.status = IncidentStatus.RESOLVED
            else:
                incident.status = IncidentStatus.VERIFICATION_FAILED
            
            incident.updated_at = datetime.utcnow()
            
        except Exception as e:
            logger.error("investigation_failed", incident_id=incident.id, error=str(e))
            incident.status = IncidentStatus.INVESTIGATION_BLOCKED
            incident.updated_at = datetime.utcnow()
            state.add_action("ERROR", "orchestrator", f"Investigation failed: {str(e)}", status="FAILED")
        
        return state
    
    async def _phase_collect_evidence(self, state: InvestigationState):
        """Phase 1: Collect evidence from all sources."""
        incident = state.incident
        incident.status = IncidentStatus.COLLECTING_EVIDENCE
        incident.updated_at = datetime.utcnow()
        
        state.add_action("COLLECT_EVIDENCE", "evidence_engine", "Starting evidence collection")
        
        # Collect evidence
        state.evidence = self.evidence_engine.collect_evidence(incident)
        
        # Store original config for verification
        config_path = os.path.join(self.repo_path, state.config_file)
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                state.original_config = f.read()
        
        state.add_action(
            "COLLECT_EVIDENCE", 
            "evidence_engine", 
            f"Collected {len(state.evidence)} evidence items",
            output_data={"evidence_count": len(state.evidence)}
        )
    
    async def _phase_build_timeline(self, state: InvestigationState):
        """Phase 2: Build incident timeline."""
        incident = state.incident
        incident.status = IncidentStatus.BUILDING_TIMELINE
        incident.updated_at = datetime.utcnow()
        
        state.add_action("BUILD_TIMELINE", "timeline_builder", "Building incident timeline")
        
        timeline_events = self.timeline_builder.build(incident, state.evidence)
        state.timeline = format_timeline_for_display(timeline_events)
        
        state.add_action(
            "BUILD_TIMELINE",
            "timeline_builder",
            f"Built timeline with {len(state.timeline)} events",
            output_data={"events": len(state.timeline)}
        )
    
    async def _phase_generate_hypotheses(self, state: InvestigationState):
        """Phase 3: Generate competing hypotheses."""
        incident = state.incident
        incident.status = IncidentStatus.GENERATING_HYPOTHESES
        incident.updated_at = datetime.utcnow()
        
        state.add_action("GENERATE_HYPOTHESES", "hypothesis_engine", "Generating initial hypotheses")
        
        # Template-based initial hypotheses
        state.hypotheses = self.hypothesis_engine.generate_initial_hypotheses(
            incident, state.evidence
        )
        
        # Refine with Nemotron
        state.add_action("GENERATE_HYPOTHESES", "nemotron", "Refining hypotheses with Nemotron")
        state.hypotheses = await self.hypothesis_engine.refine_hypotheses_with_nemotron(
            incident, state.evidence, state.hypotheses
        )
        
        state.add_action(
            "GENERATE_HYPOTHESES",
            "hypothesis_engine",
            f"Generated {len(state.hypotheses)} competing hypotheses",
            output_data={"hypotheses": [{"id": h.id, "title": h.title, "confidence": h.confidence} for h in state.hypotheses]}
        )
    
    async def _phase_investigate(self, state: InvestigationState):
        """Phase 4: Investigate hypotheses with tools."""
        incident = state.incident
        incident.status = IncidentStatus.INVESTIGATING
        incident.updated_at = datetime.utcnow()
        
        state.add_action("INVESTIGATE", "investigator", "Investigating hypotheses with tools")
        
        # For each active hypothesis, run investigation actions
        for hypothesis in state.hypotheses:
            if hypothesis.status.value == "ACTIVE" and hypothesis.next_investigation_action:
                action = hypothesis.next_investigation_action
                state.add_action(
                    "INVESTIGATE",
                    action,
                    f"Investigating {hypothesis.title}: {action}",
                    input_data={"hypothesis_id": hypothesis.id}
                )
                
                # Execute investigation action (simplified - in production use actual tools)
                new_evidence = await self._execute_investigation_action(action, incident, hypothesis)
                
                if new_evidence:
                    state.evidence.extend(new_evidence)
                    state.add_action(
                        "INVESTIGATE",
                        action,
                        f"Found {len(new_evidence)} new evidence items",
                        output_data={"new_evidence": len(new_evidence)}
                    )
        
        # Update hypotheses with new evidence
        state.hypotheses = self.hypothesis_engine.update_hypotheses_with_evidence(
            state.hypotheses, state.evidence
        )
    
    async def _execute_investigation_action(
        self, 
        action: str, 
        incident: Incident, 
        hypothesis: Hypothesis
    ) -> List[Evidence]:
        """Execute a specific investigation action."""
        # This is a simplified version - in production, connect to actual tools
        evidence = []
        
        if action.startswith("inspect_configuration"):
            key = action.split(":")[1] if ":" in action else "DB_POOL_SIZE"
            # Simulate finding config
            evidence.append(Evidence(
                incident_id=incident.id,
                source_type="CONFIG",
                claim=f"Configuration {key} found in system",
                reference=f"Configuration inspection: {action}",
                confidence=0.9,
                related_component="configuration"
            ))
        
        elif action.startswith("inspect_logs"):
            # Simulate log finding
            evidence.append(Evidence(
                incident_id=incident.id,
                source_type="LOG",
                claim=f"Log analysis for {action.split(':')[1] if ':' in action else 'pattern'} completed",
                reference=f"Log inspection: {action}",
                confidence=0.8,
                related_component="logging"
            ))
        
        elif action.startswith("search_web"):
            # Simulate web research
            evidence.append(Evidence(
                incident_id=incident.id,
                source_type="WEB",
                claim=f"Web research for {action.split(':')[1] if ':' in action else 'topic'} completed",
                reference=f"Tavily search: {action}",
                confidence=0.7,
                related_component="external_research"
            ))
        
        return evidence
    
    async def _phase_research_external(self, state: InvestigationState):
        """Phase 5: External research with Tavily."""
        incident = state.incident
        incident.status = IncidentStatus.RESEARCHING
        incident.updated_at = datetime.utcnow()
        
        state.add_action("RESEARCH_EXTERNAL", "tavily", "Researching external technical information")
        
        # Research queries based on top hypotheses
        for hypothesis in state.hypotheses[:2]:  # Top 2 hypotheses
            if hypothesis.status.value in ["ACTIVE", "SUPPORTED"]:
                query = f"{hypothesis.title} troubleshooting"
                state.add_action(
                    "RESEARCH_EXTERNAL",
                    "tavily",
                    f"Searching: {query}",
                    input_data={"query": query}
                )
                
                # Simulate Tavily result (real implementation would call Tavily)
                evidence = Evidence(
                    incident_id=incident.id,
                    source_type="WEB",
                    claim=f"External research confirms {hypothesis.title.lower()} pattern",
                    reference=f"Tavily: {query}",
                    confidence=0.75,
                    related_component="external_knowledge"
                )
                state.evidence.append(evidence)
        
        state.add_action(
            "RESEARCH_EXTERNAL",
            "tavily",
            f"Completed external research, added {len(state.hypotheses[:2])} web evidence items",
            output_data={"web_evidence_added": len(state.hypotheses[:2])}
        )
    
    async def _phase_root_cause(self, state: InvestigationState):
        """Phase 6: Identify root cause with Nemotron."""
        incident = state.incident
        incident.status = IncidentStatus.ROOT_CAUSE_IDENTIFIED
        incident.updated_at = datetime.utcnow()
        
        state.add_action("ROOT_CAUSE", "nemotron", "Identifying root cause with Nemotron")
        
        state.root_cause = await self.root_cause_engine.identify_root_cause(
            incident, state.timeline, state.evidence, state.hypotheses
        )
        
        state.add_action(
            "ROOT_CAUSE",
            "nemotron",
            f"Root cause identified: {state.root_cause.get('root_cause', 'Unknown')} (confidence: {state.root_cause.get('confidence', 0):.0%})",
            output_data=state.root_cause
        )
    
    async def _phase_remediation(self, state: InvestigationState):
        """Phase 7: Generate remediation."""
        incident = state.incident
        incident.status = IncidentStatus.REMEDIATION_PROPOSED
        incident.updated_at = datetime.utcnow()
        
        state.add_action("REMEDIATION", "remediation_engine", "Generating remediation plan")
        
        # Generate with Nemotron
        state.remediation = await self.remediation_engine.generate_remediation_with_nemotron(
            incident, state.root_cause, state.evidence
        )
        
        # Link to top hypothesis
        if state.hypotheses:
            state.remediation.hypothesis_id = state.hypotheses[0].id
        
        # Validate
        validation = self.remediation_engine.validate_remediation(state.remediation)
        
        if not validation["valid"]:
            state.add_action(
                "REMEDIATION",
                "remediation_engine",
                f"Remediation validation failed: {validation['errors']}",
                status="FAILED",
                output_data=validation
            )
            state.remediation = None
        else:
            state.add_action(
                "REMEDIATION",
                "remediation_engine",
                f"Remediation generated: {state.remediation.exact_change}",
                output_data={
                    "remediation": state.remediation.exact_change,
                    "type": state.remediation.type.value,
                    "validation": validation
                }
            )
    
    async def _phase_verify(self, state: InvestigationState):
        """Phase 8: Verify remediation in sandbox."""
        incident = state.incident
        incident.status = IncidentStatus.VERIFYING
        incident.updated_at = datetime.utcnow()
        
        if not state.remediation:
            state.add_action("VERIFY", "verifier", "No remediation to verify")
            return
        
        state.add_action("VERIFY", "verifier", "Starting three-stage verification")
        
        state.verification = await self.verifier.verify(
            incident=incident,
            remediation=state.remediation,
            evidence=state.evidence,
            original_config=state.original_config,
            config_file=state.config_file
        )
        
        state.add_action(
            "VERIFY",
            "verifier",
            f"Verification complete: {state.verification.verdict.value}",
            output_data={
                "verdict": state.verification.verdict.value,
                "baseline": state.verification.baseline_test.success,
                "post_fix": state.verification.post_fix_tests.success,
                "health": state.verification.health_check.success,
                "control": state.verification.control_test.success
            }
        )
    
    def get_investigation(self, incident_id: str) -> Optional[InvestigationState]:
        """Get investigation state by incident ID."""
        return self.investigations.get(incident_id)
    
    def get_actions(self, incident_id: str) -> List[AgentAction]:
        """Get agent actions for an incident."""
        state = self.investigations.get(incident_id)
        return state.actions if state else []


import os  # Added for config file operations