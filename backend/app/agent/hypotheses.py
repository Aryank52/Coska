"""Enhanced Hypothesis Engine for COSKA - Competing hypotheses with evidence tracking and AI explanations."""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json
import structlog
import re
from pydantic import BaseModel, Field

from app.models import Hypothesis, Evidence, HypothesisStatus, Incident
from app.services.providers import get_provider

logger = structlog.get_logger()


class HypothesisDecision(BaseModel):
    """Tracks AI decision for hypothesis generation/update."""
    hypothesis_id: str
    decision_type: str  # generated, confidence_update, status_change, rejected
    confidence_before: float
    confidence_after: float
    evidence_considered: List[str]
    reasoning: str
    alternative_considered: Optional[str] = None
    next_validation_step: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# Extended hypothesis templates covering all demo scenarios
HYPOTHESIS_TEMPLATES = {
    "database_pool_exhaustion": {
        "title": "Database connection pool exhaustion",
        "description": "Application cannot acquire database connections due to undersized pool configuration (DB_POOL_SIZE too low)",
        "indicators": ["pool exhaust", "connection pool", "timeout waiting for connection", "db_pool_size", "queuepool", "overflow"],
        "investigation_actions": [
            "inspect_configuration:DB_POOL_SIZE",
            "inspect_logs:connection pool",
            "inspect_runtime:active_connections"
        ],
        "confidence_base": 0.7,
        "confidence_per_match": 0.1
    },
    "database_saturation": {
        "title": "Database server saturation",
        "description": "Database server CPU/memory/disk saturated causing slow responses and connection timeouts",
        "indicators": ["high cpu", "memory pressure", "disk io", "slow query", "database server", "saturation", "iops"],
        "investigation_actions": [
            "inspect_runtime:database_metrics",
            "inspect_logs:slow query",
            "search_web:database saturation symptoms"
        ],
        "confidence_base": 0.3,
        "confidence_per_match": 0.1
    },
    "network_instability": {
        "title": "Network instability",
        "description": "Network issues between application and database causing connection failures and timeouts",
        "indicators": ["network timeout", "connection reset", "dns", "network unreachable", "packet loss"],
        "investigation_actions": [
            "inspect_runtime:network_metrics",
            "inspect_logs:network error",
            "search_web:network timeout database"
        ],
        "confidence_base": 0.2,
        "confidence_per_match": 0.1
    },
    "memory_pressure": {
        "title": "Application memory pressure",
        "description": "Application memory exhaustion causing GC pauses, health check timeouts, and request failures",
        "indicators": ["out of memory", "oom", "heap", "garbage collection", "memory leak", "gc pause", "rss"],
        "investigation_actions": [
            "inspect_runtime:memory_usage",
            "inspect_logs:memory",
            "inspect_repository:memory allocation"
        ],
        "confidence_base": 0.15,
        "confidence_per_match": 0.1
    },
    "dependency_failure": {
        "title": "External dependency failure",
        "description": "Downstream service or third-party API failure causing cascading errors and timeouts",
        "indicators": ["dependency", "external service", "third party", "api timeout", "circuit breaker", "upstream", "stripe", "payment"],
        "investigation_actions": [
            "inspect_logs:dependency",
            "inspect_runtime:dependency_health",
            "search_web:service outage"
        ],
        "confidence_base": 0.25,
        "confidence_per_match": 0.1
    },
    "deployment_regression": {
        "title": "Deployment regression",
        "description": "Recent deployment introduced a bug or configuration change causing immediate failures",
        "indicators": ["recent deployment", "version", "rollback", "release", "deployed", "v1.", "v2."],
        "investigation_actions": [
            "inspect_deployment:recent_changes",
            "inspect_repository:recent_commits",
            "inspect_configuration:recent_changes"
        ],
        "confidence_base": 0.4,
        "confidence_per_match": 0.15
    },
    "retry_storm": {
        "title": "Upstream timeout and cascading retry storm",
        "description": "Excessive client retries without exponential backoff or jitter creates thundering herd overwhelming upstream",
        "indicators": ["retry", "504", "gateway timeout", "retry_count", "backoff", "thundering herd", "cascading"],
        "investigation_actions": [
            "inspect_configuration:RETRY_COUNT",
            "inspect_logs:retry",
            "search_web:retry storm mitigation"
        ],
        "confidence_base": 0.6,
        "confidence_per_match": 0.15
    },
    "cache_stampede": {
        "title": "Cache stampede / thundering herd",
        "description": "Simultaneous cache expiration causes massive concurrent recomputation overwhelming backend",
        "indicators": ["cache", "stampede", "thundering herd", "ttl", "expiration", "miss spike", "redis"],
        "investigation_actions": [
            "inspect_configuration:CACHE_TTL",
            "inspect_runtime:cache_metrics",
            "search_web:cache stampede prevention"
        ],
        "confidence_base": 0.3,
        "confidence_per_match": 0.1
    },
    "bad_config": {
        "title": "Bad deployment configuration",
        "description": "Misconfigured environment variables or configuration mismatch causing authentication or connection failures",
        "indicators": ["config", "environment", "credential", "auth", "password", "username", "host", "port", "mismatch"],
        "investigation_actions": [
            "inspect_configuration:all",
            "inspect_deployment:config_changes",
            "inspect_repository:config_files"
        ],
        "confidence_base": 0.5,
        "confidence_per_match": 0.1
    },
}


class EnhancedHypothesisEngine:
    """Enhanced hypothesis engine with AI explanations and decision tracking."""
    
    def __init__(self):
        self.provider = get_provider()
        self.decision_history: List[HypothesisDecision] = []
    
    def generate_initial_hypotheses(
        self, 
        incident: Incident, 
        evidence: List[Evidence],
        intelligence: Optional[Any] = None
    ) -> List[Hypothesis]:
        """Generate initial competing hypotheses with explanations."""
        hypotheses = []
        
        # Analyze evidence to match templates
        evidence_text = " ".join([e.claim.lower() for e in evidence])
        
        # Also use intelligence if available
        if intelligence:
            evidence_text += " " + " ".join(intelligence.symptoms + intelligence.probable_causes + intelligence.error_types)
        
        matched_templates = []
        for template_id, template in HYPOTHESIS_TEMPLATES.items():
            matches = [indicator for indicator in template["indicators"] if indicator in evidence_text]
            score = len(matches)
            if score > 0:
                matched_templates.append((template_id, template, score, matches))
        
        # Sort by match score
        matched_templates.sort(key=lambda x: x[2], reverse=True)
        
        # Create hypotheses from matched templates
        for template_id, template, score, matches in matched_templates[:5]:
            confidence = min(template["confidence_base"] + (score * template["confidence_per_match"]), 0.9)
            
            # Find supporting evidence
            supporting = []
            for ev in evidence:
                if any(indicator in ev.claim.lower() for indicator in template["indicators"]):
                    supporting.append(ev.id)
            
            hypothesis = Hypothesis(
                incident_id=incident.id,
                title=template["title"],
                description=template["description"],
                supporting_evidence_ids=supporting,
                contradicting_evidence_ids=[],
                confidence=confidence,
                next_investigation_action=template["investigation_actions"][0] if template["investigation_actions"] else None,
                status=HypothesisStatus.ACTIVE
            )
            hypotheses.append(hypothesis)
            
            # Record decision
            self.decision_history.append(HypothesisDecision(
                hypothesis_id=hypothesis.id,
                decision_type="generated",
                confidence_before=0.0,
                confidence_after=confidence,
                evidence_considered=supporting + matches,
                reasoning=f"Template '{template_id}' matched {score} indicators: {', '.join(matches)}. Base confidence {template['confidence_base']} + {score} matches * {template['confidence_per_match']} = {confidence:.2f}",
                next_validation_step=template["investigation_actions"][0] if template["investigation_actions"] else None
            ))
        
        # If no templates matched, create a generic hypothesis
        if not hypotheses:
            hypothesis = Hypothesis(
                incident_id=incident.id,
                title="Unknown root cause",
                description="Insufficient evidence to generate specific hypotheses",
                confidence=0.1,
                next_investigation_action="collect_more_evidence",
                status=HypothesisStatus.ACTIVE
            )
            hypotheses.append(hypothesis)
            
            self.decision_history.append(HypothesisDecision(
                hypothesis_id=hypothesis.id,
                decision_type="generated",
                confidence_before=0.0,
                confidence_after=0.1,
                evidence_considered=[],
                reasoning="No hypothesis templates matched the available evidence. Generic hypothesis created as placeholder.",
                next_validation_step="collect_more_evidence"
            ))
        
        logger.info("hypotheses_generated", incident_id=incident.id, count=len(hypotheses))
        return hypotheses
    
    async def refine_hypotheses_with_ai(
        self,
        incident: Incident,
        evidence: List[Evidence],
        current_hypotheses: List[Hypothesis],
        rag_results: Optional[List[Dict[str, Any]]] = None
    ) -> List[Hypothesis]:
        """Use AI to refine and generate additional hypotheses with explanations."""
        
        evidence_summary = "\n".join([
            f"- {e.id} ({e.source_type.value}, conf: {e.confidence:.0%}): {e.claim}"
            for e in evidence
        ])
        
        current_hypotheses_summary = "\n".join([
            f"- {h.id}: {h.title} (conf: {h.confidence:.0%}, status: {h.status.value}, "
            f"supporting: {h.supporting_evidence_ids}, contradicting: {h.contradicting_evidence_ids})"
            for h in current_hypotheses
        ])
        
        rag_context = ""
        if rag_results:
            rag_context = "\nRELEVANT RUNBOOKS:\n" + "\n".join([
                f"- {d.get('title', '')}: {d.get('snippet', '')[:200]}"
                for d in rag_results
            ])
        
        prompt = f"""You are COSKA, an autonomous incident intelligence system.

Incident: {incident.id}
Service: {incident.service}
Severity: {incident.severity}
Description: {incident.description}

Evidence ({len(evidence)} items):
{evidence_summary}

Current Hypotheses ({len(current_hypotheses)}):
{current_hypotheses_summary}
{rag_context}

TASK: Refine hypotheses and generate 3-5 competing root cause hypotheses.
For EACH hypothesis, provide a detailed decision explanation.

Return JSON array with this exact structure for each hypothesis:
{{
  "title": "string",
  "description": "string (1-2 sentences)",
  "supporting_evidence_ids": ["E-XXX"],
  "contradicting_evidence_ids": ["E-XXX"],
  "confidence": 0.0,
  "next_investigation_action": "specific_tool:parameter",
  "status": "ACTIVE|WEAKENED|SUPPORTED|REJECTED",
  "decision_explanation": {{
    "reasoning": "Why this hypothesis at this confidence",
    "evidence_used": ["E-XXX"],
    "runbooks_consulted": ["KB-RUNBOOK-XXX"],
    "alternative_considered": "Alternative hypothesis and why rejected",
    "next_validation": "Specific next action to validate/refute"
  }}
}}"""
        
        try:
            result = await self.provider.chat_completion(
                messages=[
                    {"role": "system", "content": "You are COSKA, an expert incident investigator. Generate structured, evidence-backed hypotheses with detailed decision explanations. Return only valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=3000
            )
            
            content = result["choices"][0]["message"]["content"]
            
            # Extract JSON array
            start = content.find('[')
            end = content.rfind(']') + 1
            if start >= 0 and end > start:
                hypotheses_data = json.loads(content[start:end])
                
                refined = []
                for h_data in hypotheses_data:
                    hypothesis = Hypothesis(
                        incident_id=incident.id,
                        title=h_data.get("title", "Unknown"),
                        description=h_data.get("description", ""),
                        supporting_evidence_ids=h_data.get("supporting_evidence_ids", []),
                        contradicting_evidence_ids=h_data.get("contradicting_evidence_ids", []),
                        confidence=h_data.get("confidence", 0.5),
                        next_investigation_action=h_data.get("next_investigation_action"),
                        status=HypothesisStatus(h_data.get("status", "ACTIVE"))
                    )
                    refined.append(hypothesis)
                    
                    # Record AI decision
                    decision_exp = h_data.get("decision_explanation", {})
                    self.decision_history.append(HypothesisDecision(
                        hypothesis_id=hypothesis.id,
                        decision_type="ai_refined",
                        confidence_before=0.0,
                        confidence_after=hypothesis.confidence,
                        evidence_considered=hypothesis.supporting_evidence_ids + hypothesis.contradicting_evidence_ids,
                        reasoning=decision_exp.get("reasoning", ""),
                        alternative_considered=decision_exp.get("alternative_considered"),
                        next_validation_step=decision_exp.get("next_validation")
                    ))
                
                if refined:
                    logger.info("hypotheses_refined_ai", incident_id=incident.id, count=len(refined))
                    return refined
                    
        except Exception as e:
            logger.error("ai_hypothesis_refinement_failed", error=str(e))
        
        # Fallback to template-based update
        return self.update_hypotheses_with_evidence(current_hypotheses, evidence)
    
    def update_hypotheses_with_evidence(
        self,
        hypotheses: List[Hypothesis],
        new_evidence: List[Evidence],
        intelligence: Optional[Any] = None
    ) -> List[Hypothesis]:
        """Update hypothesis confidence and statuses based on new evidence with detailed tracking."""
        updated = []
        
        for hypothesis in hypotheses:
            old_confidence = hypothesis.confidence
            old_status = hypothesis.status
            
            # Extract keywords from hypothesis title
            title_keywords = [
                w for w in re.findall(r'\b[a-zA-Z]{3,}\b', hypothesis.title.lower())
                if w not in {"with", "from", "that", "this", "cause", "issue", "the", "and", "for"}
            ]
            
            # Check supporting evidence
            new_supporting = [
                e.id for e in new_evidence
                if any(keyword in e.claim.lower() for keyword in title_keywords)
                and e.id not in hypothesis.supporting_evidence_ids
            ]
            
            # Check contradicting evidence
            neg_indicators = ["normal", "healthy", "within limits", "no error", "stable", "ok", "success", "passed"]
            new_contradicting = [
                e.id for e in new_evidence
                if any(neg in e.claim.lower() for neg in neg_indicators)
                and any(keyword in e.claim.lower() for keyword in title_keywords)
                and e.id not in hypothesis.contradicting_evidence_ids
            ]
            
            evidence_changes = []
            
            if new_supporting:
                hypothesis.confidence = min(hypothesis.confidence + 0.1 * len(new_supporting), 0.95)
                hypothesis.supporting_evidence_ids.extend(new_supporting)
                evidence_changes.append(f"added {len(new_supporting)} supporting evidence: {new_supporting}")
            elif not hypothesis.supporting_evidence_ids:
                # Slightly weaken if no supporting evidence at all
                hypothesis.confidence = max(hypothesis.confidence - 0.05, 0.05)
                evidence_changes.append("no supporting evidence, slight weaken")
            
            if new_contradicting:
                hypothesis.confidence = max(hypothesis.confidence - 0.2 * len(new_contradicting), 0.01)
                hypothesis.contradicting_evidence_ids.extend(new_contradicting)
                evidence_changes.append(f"added {len(new_contradicting)} contradicting evidence: {new_contradicting}")
            
            # Status resolution
            if hypothesis.confidence >= 0.6 or (hypothesis.supporting_evidence_ids and hypothesis.confidence >= 0.4):
                hypothesis.status = HypothesisStatus.SUPPORTED
            elif hypothesis.confidence < 0.1 or len(hypothesis.contradicting_evidence_ids) >= 2:
                hypothesis.status = HypothesisStatus.REJECTED
            elif hypothesis.confidence < 0.35:
                hypothesis.status = HypothesisStatus.WEAKENED
            else:
                hypothesis.status = HypothesisStatus.ACTIVE
            
            hypothesis.updated_at = datetime.utcnow()
            updated.append(hypothesis)
            
            # Record decision if confidence changed significantly
            if abs(hypothesis.confidence - old_confidence) > 0.05 or hypothesis.status != old_status:
                self.decision_history.append(HypothesisDecision(
                    hypothesis_id=hypothesis.id,
                    decision_type="confidence_update",
                    confidence_before=old_confidence,
                    confidence_after=hypothesis.confidence,
                    evidence_considered=new_supporting + new_contradicting,
                    reasoning=f"Confidence changed from {old_confidence:.2f} to {hypothesis.confidence:.2f}. "
                              f"Status: {old_status.value} -> {hypothesis.status.value}. "
                              f"Changes: {'; '.join(evidence_changes)}",
                    next_validation_step=hypothesis.next_investigation_action
                ))
        
        # Sort by confidence
        updated.sort(key=lambda h: h.confidence, reverse=True)
        
        # Ensure realistic competitive hypothesis distribution
        if updated:
            if not any(h.status == HypothesisStatus.SUPPORTED for h in updated):
                updated[0].status = HypothesisStatus.SUPPORTED
                self.decision_history.append(HypothesisDecision(
                    hypothesis_id=updated[0].id,
                    decision_type="status_change",
                    confidence_before=updated[0].confidence,
                    confidence_after=updated[0].confidence,
                    evidence_considered=updated[0].supporting_evidence_ids,
                    reasoning="Ensuring at least one SUPPORTED hypothesis for competitive analysis",
                    next_validation_step=updated[0].next_investigation_action
                ))
            if not any(h.status in (HypothesisStatus.WEAKENED, HypothesisStatus.REJECTED) for h in updated) and len(updated) > 1:
                updated[-1].status = HypothesisStatus.WEAKENED
                self.decision_history.append(HypothesisDecision(
                    hypothesis_id=updated[-1].id,
                    decision_type="status_change",
                    confidence_before=updated[-1].confidence,
                    confidence_after=updated[-1].confidence,
                    evidence_considered=updated[-1].supporting_evidence_ids + updated[-1].contradicting_evidence_ids,
                    reasoning="Ensuring at least one WEAKENED/REJECTED hypothesis for competitive analysis",
                    next_validation_step=updated[-1].next_investigation_action
                ))
        
        return updated
    
    def get_decision_history(self, hypothesis_id: Optional[str] = None) -> List[HypothesisDecision]:
        """Get decision history for a specific hypothesis or all."""
        if hypothesis_id:
            return [d for d in self.decision_history if d.hypothesis_id == hypothesis_id]
        return self.decision_history
    
    def clear_history(self):
        self.decision_history = []


# Backward compatibility
class HypothesisEngine:
    """Backward-compatible wrapper."""
    
    def __init__(self):
        self.enhanced = EnhancedHypothesisEngine()
    
    def generate_initial_hypotheses(self, incident: Incident, evidence: List[Evidence]) -> List[Hypothesis]:
        return self.enhanced.generate_initial_hypotheses(incident, evidence)
    
    async def refine_hypotheses_with_nemotron(
        self,
        incident: Incident,
        evidence: List[Evidence],
        current_hypotheses: List[Hypothesis]
    ) -> List[Hypothesis]:
        return await self.enhanced.refine_hypotheses_with_ai(incident, evidence, current_hypotheses)
    
    def update_hypotheses_with_evidence(
        self,
        hypotheses: List[Hypothesis],
        new_evidence: List[Evidence]
    ) -> List[Hypothesis]:
        return self.enhanced.update_hypotheses_with_evidence(hypotheses, new_evidence)