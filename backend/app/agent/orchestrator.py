"""Main orchestrator for COSKA autonomous investigation workflow.

Implements the 8-phase investigation lifecycle with state persistence,
safety limits (MAX_AGENT_STEPS, MAX_TOOL_CALLS, MAX_RETRIES, MAX_INVESTIGATION_TIME),
and deterministic causal verification.
"""
import asyncio
from datetime import datetime, timezone
import os
import time
from typing import Dict, Any, List, Optional
import uuid
import structlog

from app.models import (
    Incident, IncidentStatus, Evidence, Hypothesis, 
    Remediation, VerificationResult, Verdict, AgentAction, SourceType,
    InvestigationPhase
)
from app.agent.evidence import EvidenceEngine
from app.agent.timeline import TimelineBuilder, format_timeline_for_display
from app.agent.hypotheses import HypothesisEngine
from app.agent.root_cause import RootCauseEngine
from app.agent.remediation import RemediationEngine
from app.agent.verifier import Verifier, VerificationReport
from app.tools.sandbox import SandboxEngine, SandboxResult
from app.tools.registry import get_tool_registry
from app.tools.investigation import register_all_tools
from app.services.storage import get_storage
from app.config import get_settings

logger = structlog.get_logger()


class InvestigationState:
    """Complete, serializable investigation state for an incident."""

    def __init__(self, incident: Incident, run_id: Optional[str] = None):
        self.run_id: str = run_id or f"RUN-{uuid.uuid4().hex[:8].upper()}"
        self.incident_id: str = incident.id
        self.current_phase: InvestigationPhase = InvestigationPhase.INCIDENT_INTAKE
        self.incident: Incident = incident
        self.timeline: List[Dict[str, Any]] = []
        self.evidence: List[Evidence] = []
        self.hypotheses: List[Hypothesis] = []
        self.tool_calls: List[Dict[str, Any]] = []
        self.tool_results: List[Dict[str, Any]] = []
        self.web_sources: List[Dict[str, Any]] = []
        self.knowledge_docs: List[Dict[str, Any]] = []
        self.root_cause: Optional[Dict[str, Any]] = None
        self.remediation: Optional[Remediation] = None
        self.sandbox_result: Optional[Dict[str, Any]] = None
        self.test_results: Optional[Dict[str, Any]] = None
        self.verification: Optional[VerificationReport] = None
        self.verification_result: Optional[VerificationResult] = None
        self.errors: List[str] = []
        self.actions: List[AgentAction] = []
        self.original_config: str = ""
        self.config_file: str = ".env"
        self.created_at: datetime = datetime.now(timezone.utc)
        self.updated_at: datetime = datetime.now(timezone.utc)

        # Safety limit counters
        self.step_count: int = 0
        self.tool_call_count: int = 0
        self.retry_count: int = 0
        self.start_time: float = time.time()

    def add_action(self, step: str, tool: str, summary: str, status: str = "COMPLETED", **kwargs):
        """Record an agent action."""
        self.step_count += 1
        action = AgentAction(
            incident_id=self.incident_id,
            step=step,
            tool=tool,
            summary=summary,
            status=status,
            **kwargs
        )
        self.actions.append(action)
        self.updated_at = datetime.now(timezone.utc)
        logger.info("agent_action", incident_id=self.incident_id, step=step, tool=tool, summary=summary)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete investigation state to dictionary."""
        return {
            "run_id": self.run_id,
            "incident_id": self.incident_id,
            "current_phase": self.current_phase.value,
            "incident": self.incident.model_dump(mode='json'),
            "timeline": self.timeline,
            "evidence": [e.model_dump(mode='json') for e in self.evidence],
            "hypotheses": [h.model_dump(mode='json') for h in self.hypotheses],
            "tool_calls": self.tool_calls,
            "tool_results": self.tool_results,
            "web_sources": self.web_sources,
            "knowledge_docs": self.knowledge_docs,
            "root_cause": self.root_cause,
            "remediation": self.remediation.model_dump(mode='json') if self.remediation else None,
            "sandbox_result": self.sandbox_result,
            "test_results": self.test_results,
            "verification_result": self.verification_result.model_dump(mode='json') if self.verification_result else None,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Orchestrator:
    """Main orchestrator for the COSKA 8-phase investigation workflow."""

    def __init__(self, repo_path: str = "./demo/payment-api"):
        self.repo_path = repo_path
        self.settings = get_settings()

        # Initialize core engines
        self.evidence_engine = EvidenceEngine()
        self.timeline_builder = TimelineBuilder()
        self.hypothesis_engine = HypothesisEngine()
        self.root_cause_engine = RootCauseEngine()
        self.remediation_engine = RemediationEngine()
        self.sandbox = SandboxEngine(
            timeout=self.settings.sandbox_timeout,
            memory_limit=self.settings.sandbox_memory_limit,
            cpu_limit=self.settings.sandbox_cpu_limit,
            provider_mode=self.settings.sandbox_mode
        )
        self.verifier = Verifier(self.sandbox, repo_path, self.settings.nebius_model)

        # Register tools
        register_all_tools()
        self.tool_registry = get_tool_registry()

        # Offline RAG Knowledge Engine
        from app.services.rag import get_rag_engine
        self.rag_engine = get_rag_engine()

        # Storage and active investigations map
        self.storage = get_storage()
        self.investigations: Dict[str, InvestigationState] = {}

    def _check_safety_limits(self, state: InvestigationState) -> Optional[str]:
        """Check if any investigation safety limit has been exceeded."""
        elapsed = time.time() - state.start_time
        if elapsed > self.settings.max_investigation_time:
            return f"MAX_INVESTIGATION_TIME exceeded ({elapsed:.1f}s > {self.settings.max_investigation_time}s)"
        if state.step_count > self.settings.max_agent_steps:
            return f"MAX_AGENT_STEPS exceeded ({state.step_count} > {self.settings.max_agent_steps})"
        if state.tool_call_count > self.settings.max_tool_calls:
            return f"MAX_TOOL_CALLS exceeded ({state.tool_call_count} > {self.settings.max_tool_calls})"
        if state.retry_count > self.settings.max_retries:
            return f"MAX_RETRIES exceeded ({state.retry_count} > {self.settings.max_retries})"
        return None

    def _persist_state(self, state: InvestigationState):
        """Persist current investigation state to SQLite storage."""
        try:
            self.storage.save_investigation(
                incident_id=state.incident_id,
                current_phase=state.current_phase.value,
                state_data=state.to_dict(),
                run_id=state.run_id
            )
            self.storage.save_incident(state.incident)
            if state.evidence:
                self.storage.save_evidence(state.evidence)
            if state.hypotheses:
                self.storage.save_hypotheses(state.hypotheses)
            if state.remediation:
                self.storage.save_remediation(state.remediation)
            if state.actions:
                self.storage.save_actions(state.actions)
            if state.verification_result:
                self.storage.save_verification(state.verification_result)
        except Exception as e:
            logger.warning("persist_state_warning", error=str(e), incident_id=state.incident_id)

    async def investigate(self, incident: Incident, auto_approve: bool = False) -> InvestigationState:
        """Run complete 8-phase autonomous investigation workflow."""
        state = InvestigationState(incident)
        self.investigations[incident.id] = state

        # PHASE 1: INCIDENT_INTAKE
        state.current_phase = InvestigationPhase.INCIDENT_INTAKE
        incident.status = IncidentStatus.TRIAGING
        incident.updated_at = datetime.now(timezone.utc)
        state.add_action("INCIDENT_INTAKE", "orchestrator", f"Ingested incident {incident.id} for service {incident.service}")

        # Check incident memory for previous verified incident patterns
        try:
            previous = self.storage.search_incident_memory(incident.service, incident.description[:50])
            if previous:
                state.add_action("INCIDENT_MEMORY", "storage", f"Found {len(previous)} previous incident memories for {incident.service}")
        except Exception:
            pass

        # Offline RAG Knowledge Retrieval
        try:
            query = f"{incident.service} {incident.description}"
            rag_result = self.rag_engine.search(query, top_k=3)
            rag_docs = rag_result.documents if hasattr(rag_result, 'documents') else rag_result
            state.knowledge_docs = [d.model_dump() for d in rag_docs]
            if rag_docs:
                top = rag_docs[0]
                rag_ev = Evidence(
                    incident_id=incident.id,
                    source_type=SourceType.RAG,
                    claim=f"Runbook guidance from {top.title}: {top.summary}",
                    reference=top.source,
                    confidence=top.relevance_score,
                    related_component=top.category,
                    raw_data={"doc_id": top.id, "snippet": top.snippet, "relevance": top.relevance_score}
                )
                state.evidence.append(rag_ev)
                state.add_action(
                    "KNOWLEDGE_RETRIEVAL",
                    "rag_engine",
                    f"Retrieved {len(rag_docs)} runbooks; Top source: {top.title}",
                    output_data={"query": query, "results_count": len(rag_docs), "top_source": top.title, "snippet": top.snippet}
                )
        except Exception as e:
            logger.warning("rag_retrieval_failed", error=str(e))

        self._persist_state(state)

        phases = [
            (InvestigationPhase.EVIDENCE_COLLECTION, self._phase_collect_evidence),
            (InvestigationPhase.TIMELINE_BUILD, self._phase_build_timeline),
            (InvestigationPhase.HYPOTHESIS_GENERATION, self._phase_generate_hypotheses),
            (InvestigationPhase.INVESTIGATION, self._phase_investigate),
            (InvestigationPhase.ROOT_CAUSE, self._phase_root_cause),
            (InvestigationPhase.REMEDIATION, self._phase_remediation),
        ]

        try:
            for phase_enum, phase_handler in phases:
                limit_violation = self._check_safety_limits(state)
                if limit_violation:
                    state.errors.append(f"INVESTIGATION_LIMIT_REACHED: {limit_violation}")
                    incident.status = IncidentStatus.INVESTIGATION_BLOCKED
                    state.add_action("LIMIT_CHECK", "orchestrator", f"INVESTIGATION_LIMIT_REACHED: {limit_violation}", status="FAILED")
                    self._persist_state(state)
                    return state

                state.current_phase = phase_enum
                phase_start = time.time()
                await phase_handler(state)
                duration_ms = int((time.time() - phase_start) * 1000)
                state.add_action(phase_enum.value, "orchestrator", f"Phase {phase_enum.value} completed", duration_ms=duration_ms)
                self._persist_state(state)

            # Verification phase
            if auto_approve or state.remediation:
                state.current_phase = InvestigationPhase.VERIFICATION
                v_start = time.time()
                await self._phase_verify(state)
                v_duration = int((time.time() - v_start) * 1000)
                state.add_action("VERIFICATION", "orchestrator", "Phase VERIFICATION completed", duration_ms=v_duration)

            # Final status update
            if state.verification and state.verification.verdict == Verdict.VERIFIED:
                incident.status = IncidentStatus.RESOLVED
                # Record in incident memory for verified recoveries
                try:
                    self.storage.save_incident_memory(
                        service=incident.service,
                        symptoms=incident.description,
                        root_cause=state.root_cause.get("root_cause", "") if state.root_cause else "",
                        evidence=[e.dict() for e in state.evidence[:5]],
                        remediation=state.remediation.dict() if state.remediation else {},
                        verification=state.verification.details
                    )
                except Exception:
                    pass
            else:
                incident.status = IncidentStatus.VERIFICATION_FAILED

            incident.updated_at = datetime.now(timezone.utc)
            self._persist_state(state)

        except Exception as e:
            logger.error("investigation_failed", incident_id=incident.id, error=str(e))
            state.errors.append(str(e))
            incident.status = IncidentStatus.INVESTIGATION_BLOCKED
            incident.updated_at = datetime.now(timezone.utc)
            state.add_action("ERROR", "orchestrator", f"Investigation failed: {str(e)}", status="FAILED")
            self._persist_state(state)

        return state

    async def _phase_collect_evidence(self, state: InvestigationState):
        """Phase 2: Collect evidence from all local sources."""
        incident = state.incident
        incident.status = IncidentStatus.COLLECTING_EVIDENCE
        incident.updated_at = datetime.now(timezone.utc)

        state.add_action("COLLECT_EVIDENCE", "evidence_engine", "Starting evidence collection")
        state.evidence = self.evidence_engine.collect_evidence(incident)

        # Store original config for verification rollback
        config_path = os.path.join(self.repo_path, state.config_file)
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                state.original_config = f.read()

        state.add_action(
            "COLLECT_EVIDENCE",
            "evidence_engine",
            f"Collected {len(state.evidence)} evidence items",
            output_data={"evidence_count": len(state.evidence)}
        )

    async def _phase_build_timeline(self, state: InvestigationState):
        """Phase 3: Construct chronological incident timeline."""
        incident = state.incident
        incident.status = IncidentStatus.BUILDING_TIMELINE
        incident.updated_at = datetime.now(timezone.utc)

        state.add_action("BUILD_TIMELINE", "timeline_builder", "Building incident timeline")
        events = self.timeline_builder.build(incident, state.evidence)
        state.timeline = format_timeline_for_display(events)

        state.add_action(
            "BUILD_TIMELINE",
            "timeline_builder",
            f"Built timeline with {len(state.timeline)} events",
            output_data={"event_count": len(state.timeline)}
        )

    async def _phase_generate_hypotheses(self, state: InvestigationState):
        """Phase 4: Generate competing hypotheses."""
        incident = state.incident
        incident.status = IncidentStatus.GENERATING_HYPOTHESES
        incident.updated_at = datetime.now(timezone.utc)

        state.add_action("GENERATE_HYPOTHESES", "hypothesis_engine", "Generating initial hypotheses")
        state.hypotheses = self.hypothesis_engine.generate_initial_hypotheses(incident, state.evidence)

        # Refine hypotheses with Nemotron
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
        """Phase 5: Investigate hypotheses with structured tools and research."""
        incident = state.incident
        incident.status = IncidentStatus.INVESTIGATING
        incident.updated_at = datetime.now(timezone.utc)

        state.add_action("INVESTIGATE", "investigator", "Investigating hypotheses with tools")

        # Run investigation actions for active hypotheses
        for hypothesis in state.hypotheses:
            if state.tool_call_count >= self.settings.max_tool_calls:
                break
            if hypothesis.status.value in ["ACTIVE", "SUPPORTED"] and hypothesis.next_investigation_action:
                action = hypothesis.next_investigation_action
                state.add_action(
                    "INVESTIGATE",
                    action,
                    f"Investigating {hypothesis.title}: {action}",
                    input_data={"hypothesis_id": hypothesis.id}
                )

                new_evidence = await self._execute_investigation_action(action, incident, hypothesis, state)
                if new_evidence:
                    state.evidence.extend(new_evidence)
                    state.add_action(
                        "INVESTIGATE",
                        action,
                        f"Found {len(new_evidence)} new evidence items",
                        output_data={"new_evidence": len(new_evidence)}
                    )

        # External research via Tavily tool
        await self._phase_research_external(state)

        # Update hypotheses with all evidence
        state.hypotheses = self.hypothesis_engine.update_hypotheses_with_evidence(
            state.hypotheses, state.evidence
        )

    async def _execute_investigation_action(
        self, 
        action: str, 
        incident: Incident, 
        hypothesis: Hypothesis,
        state: InvestigationState
    ) -> List[Evidence]:
        """Execute a specific investigation action using registered tools."""
        evidence: List[Evidence] = []
        state.tool_call_count += 1

        parts = action.split(":", 1)
        tool_name = parts[0]
        param = parts[1] if len(parts) > 1 else None

        tool_input = {"incident_id": incident.id}
        if param:
            if tool_name == "inspect_configuration":
                tool_input["config_keys"] = [param]
            elif tool_name == "inspect_logs":
                tool_input["pattern"] = param
            elif tool_name == "search_web":
                tool_input["query"] = param

        state.tool_calls.append({"tool": tool_name, "input": tool_input, "timestamp": datetime.now(timezone.utc).isoformat()})
        state.add_action(
            "TOOL_CALL",
            tool_name,
            f"Calling {tool_name} with input: {tool_input}",
            input_data=tool_input
        )

        result = await self.tool_registry.execute(tool_name, tool_input)
        state.tool_results.append({"tool": tool_name, "success": result.success, "data": result.data})

        state.add_action(
            "TOOL_RESULT",
            tool_name,
            f"Tool {tool_name} returned: {'success' if result.success else 'failed'}",
            output_data={"success": result.success, "metadata": result.metadata}
        )

        if result.success and result.data:
            for ev_data in result.data.get("evidence", []):
                evidence.append(Evidence(
                    incident_id=incident.id,
                    source_type=SourceType(ev_data.get("source_type", "RUNTIME")),
                    claim=ev_data.get("claim", ""),
                    reference=ev_data.get("reference", ""),
                    confidence=ev_data.get("confidence", 0.5),
                    related_component=ev_data.get("related_component"),
                    raw_data=ev_data.get("raw_data")
                ))

        return evidence

    async def _phase_research_external(self, state: InvestigationState):
        """Execute external technical web research using Tavily."""
        incident = state.incident
        state.add_action("RESEARCH_EXTERNAL", "tavily", "Researching external technical information")

        web_evidence_count = 0
        for hypothesis in state.hypotheses[:2]:
            if state.tool_call_count >= self.settings.max_tool_calls:
                break
            if hypothesis.status.value in ["ACTIVE", "SUPPORTED"]:
                query = f"{hypothesis.title} troubleshooting"
                state.add_action("RESEARCH_EXTERNAL", "tavily", f"Searching: {query}", input_data={"query": query})
                state.tool_call_count += 1

                result = await self.tool_registry.execute(
                    "search_web",
                    {"incident_id": incident.id, "query": query, "max_results": 5}
                )

                if result.success and result.data:
                    state.web_sources.append({"query": query, "results": result.data.get("results", [])})
                    for ev_data in result.data.get("evidence", []):
                        ev = Evidence(
                            incident_id=incident.id,
                            source_type=SourceType.WEB,
                            claim=ev_data.get("claim", ""),
                            reference=ev_data.get("reference", ""),
                            confidence=ev_data.get("confidence", 0.5),
                            related_component=ev_data.get("related_component"),
                            raw_data=ev_data.get("raw_data")
                        )
                        state.evidence.append(ev)
                        web_evidence_count += 1

        state.add_action(
            "RESEARCH_EXTERNAL",
            "tavily",
            f"Completed external research, added {web_evidence_count} web evidence items",
            output_data={"web_evidence_added": web_evidence_count}
        )

    async def _phase_root_cause(self, state: InvestigationState):
        """Phase 6: Identify root cause reasoning over all evidence."""
        incident = state.incident
        incident.status = IncidentStatus.ROOT_CAUSE_IDENTIFIED
        incident.updated_at = datetime.now(timezone.utc)

        state.add_action("ROOT_CAUSE", "nemotron", "Identifying root cause with Nemotron")
        state.root_cause = await self.root_cause_engine.identify_root_cause(
            incident, state.timeline, state.evidence, state.hypotheses
        )

        cause_text = state.root_cause.get("root_cause", "Unknown") if state.root_cause else "Unknown"
        conf = state.root_cause.get("confidence", 0) if state.root_cause else 0
        state.add_action(
            "ROOT_CAUSE",
            "nemotron",
            f"Root cause identified: {cause_text} (confidence: {conf:.0%})",
            output_data=state.root_cause or {}
        )

    async def _phase_remediation(self, state: InvestigationState):
        """Phase 7: Generate and validate remediation plan."""
        incident = state.incident
        incident.status = IncidentStatus.REMEDIATION_PROPOSED
        incident.updated_at = datetime.now(timezone.utc)

        state.add_action("REMEDIATION", "remediation_engine", "Generating remediation plan")
        state.remediation = await self.remediation_engine.generate_remediation_with_nemotron(
            incident, state.root_cause, state.evidence
        )

        if state.hypotheses:
            state.remediation.hypothesis_id = state.hypotheses[0].id

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
        """Phase 8: Execute deterministic 3-stage verification in sandbox."""
        incident = state.incident
        incident.status = IncidentStatus.VERIFYING
        incident.updated_at = datetime.now(timezone.utc)

        if not state.remediation:
            state.add_action("VERIFY", "verifier", "No remediation to verify", status="SKIPPED")
            return

        state.add_action("VERIFY", "verifier", f"Starting three-stage verification in {self.sandbox.provider_name} sandbox")

        state.verification = await self.verifier.verify(
            incident=incident,
            remediation=state.remediation,
            evidence=state.evidence,
            original_config=state.original_config,
            config_file=state.config_file
        )

        # Build persistent VerificationResult model
        state.verification_result = VerificationResult(
            incident_id=incident.id,
            remediation_id=state.remediation.id,
            baseline_test="PASSED" if state.verification.baseline_test.success else "FAILED",
            post_fix_tests="PASSED" if state.verification.post_fix_tests.success else "FAILED",
            health_check="PASSED" if state.verification.health_check.success else "FAILED",
            control_test="PASSED" if state.verification.control_test.success else "FAILED",
            verdict=state.verification.verdict,
            evidence_count=len(state.evidence),
            model=state.verification.model,
            details={
                **state.verification.details,
                "sandbox_provider": self.sandbox.provider_name
            }
        )

        state.add_action(
            "VERIFY",
            "verifier",
            f"Verification complete: {state.verification.verdict.value}",
            output_data={
                "verdict": state.verification.verdict.value,
                "sandbox_provider": self.sandbox.provider_name,
                "baseline": state.verification.baseline_test.success,
                "post_fix": state.verification.post_fix_tests.success,
                "health": state.verification.health_check.success,
                "control": state.verification.control_test.success
            }
        )

    def get_investigation(self, incident_id: str) -> Optional[InvestigationState]:
        """Get live or stored investigation state."""
        if incident_id in self.investigations:
            return self.investigations[incident_id]
        return None

    def get_actions(self, incident_id: str) -> List[AgentAction]:
        """Get agent actions for an incident."""
        state = self.investigations.get(incident_id)
        if state:
            return state.actions
        return self.storage.get_actions(incident_id)
