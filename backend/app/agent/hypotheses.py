"""Hypothesis engine for generating and managing competing hypotheses."""
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import structlog

from app.models import Hypothesis, Evidence, HypothesisStatus, Incident
from app.services.nebius import get_nebius_client

logger = structlog.get_logger()


# Pre-defined hypothesis templates for common incident types
HYPOTHESIS_TEMPLATES = {
    "database_pool_exhaustion": {
        "title": "Database connection pool exhaustion",
        "description": "Application cannot acquire database connections due to undersized pool configuration",
        "indicators": ["pool exhaust", "connection pool", "timeout waiting for connection", "DB_POOL_SIZE"],
        "investigation_actions": [
            "inspect_configuration:DB_POOL_SIZE",
            "inspect_logs:connection pool",
            "inspect_runtime:active_connections"
        ]
    },
    "database_saturation": {
        "title": "Database server saturation",
        "description": "Database server CPU/memory/disk saturated causing slow responses and timeouts",
        "indicators": ["high cpu", "memory pressure", "disk io", "slow query", "database server"],
        "investigation_actions": [
            "inspect_runtime:database_metrics",
            "inspect_logs:slow query",
            "search_web:database saturation symptoms"
        ]
    },
    "network_instability": {
        "title": "Network instability",
        "description": "Network issues between application and database causing connection failures",
        "indicators": ["network timeout", "connection reset", "dns", "network unreachable"],
        "investigation_actions": [
            "inspect_runtime:network_metrics",
            "inspect_logs:network error",
            "search_web:network timeout database"
        ]
    },
    "memory_pressure": {
        "title": "Application memory pressure",
        "description": "Application memory exhaustion causing GC pauses and request failures",
        "indicators": ["out of memory", "heap", "garbage collection", "memory leak"],
        "investigation_actions": [
            "inspect_runtime:memory_usage",
            "inspect_logs:memory",
            "inspect_repository:memory allocation"
        ]
    },
    "dependency_failure": {
        "title": "External dependency failure",
        "description": "Downstream service or third-party API failure causing cascading errors",
        "indicators": ["dependency", "external service", "third party", "api timeout", "circuit breaker"],
        "investigation_actions": [
            "inspect_logs:dependency",
            "inspect_runtime:dependency_health",
            "search_web:service outage"
        ]
    },
    "deployment_regression": {
        "title": "Deployment regression",
        "description": "Recent deployment introduced a bug or configuration change causing failures",
        "indicators": ["recent deployment", "version", "rollback", "release"],
        "investigation_actions": [
            "inspect_deployment:recent_changes",
            "inspect_repository:recent_commits",
            "inspect_configuration:recent_changes"
        ]
    }
}


class HypothesisEngine:
    """Generates and manages competing hypotheses for incident investigation."""
    
    def __init__(self):
        self.client = get_nebius_client()
    
    def generate_initial_hypotheses(
        self, 
        incident: Incident, 
        evidence: List[Evidence]
    ) -> List[Hypothesis]:
        """Generate initial competing hypotheses based on evidence."""
        hypotheses = []
        
        # Analyze evidence to match templates
        evidence_text = " ".join([e.claim.lower() for e in evidence])
        
        matched_templates = []
        for template_id, template in HYPOTHESIS_TEMPLATES.items():
            score = sum(1 for indicator in template["indicators"] if indicator in evidence_text)
            if score > 0:
                matched_templates.append((template_id, template, score))
        
        # Sort by match score
        matched_templates.sort(key=lambda x: x[2], reverse=True)
        
        # Create hypotheses from matched templates
        for template_id, template, score in matched_templates[:5]:  # Top 5
            # Calculate initial confidence based on evidence match
            confidence = min(0.3 + (score * 0.15), 0.9)
            
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
                confidence=confidence,
                next_investigation_action=template["investigation_actions"][0] if template["investigation_actions"] else None,
                status=HypothesisStatus.ACTIVE
            )
            hypotheses.append(hypothesis)
        
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
        
        logger.info("hypotheses_generated", incident_id=incident.id, count=len(hypotheses))
        return hypotheses
    
    async def refine_hypotheses_with_nemotron(
        self,
        incident: Incident,
        evidence: List[Evidence],
        current_hypotheses: List[Hypothesis]
    ) -> List[Hypothesis]:
        """Use Nemotron to refine and generate additional hypotheses."""
        
        # Prepare context for Nemotron
        evidence_summary = "\n".join([
            f"- {e.id} ({e.source_type.value}): {e.claim} [confidence: {e.confidence}]"
            for e in evidence
        ])
        
        current_hypotheses_summary = "\n".join([
            f"- {h.id}: {h.title} (confidence: {h.confidence}, status: {h.status.value})"
            for h in current_hypotheses
        ])
        
        prompt = f"""You are COSKA, an autonomous incident intelligence system.

Incident: {incident.id}
Service: {incident.service}
Severity: {incident.severity}
Description: {incident.description}

Evidence:
{evidence_summary}

Current Hypotheses:
{current_hypotheses_summary}

Generate 3-5 competing root cause hypotheses. For each hypothesis, provide:
1. Title (concise)
2. Description (1-2 sentences)
3. Supporting evidence IDs from above
4. Contradicting evidence IDs from above (if any)
5. Confidence score (0.0-1.0)
6. Next investigation action (specific tool to use)
7. Status (ACTIVE/WEAKENED)

Return as JSON array. Be specific and evidence-driven. If evidence is insufficient, say so."""
        
        try:
            result = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are COSKA, an expert incident investigator. Generate structured, evidence-backed hypotheses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse response (simplified - in production use proper JSON parsing)
            import json
            content = result["choices"][0]["message"]["content"]
            
            # Try to extract JSON
            try:
                # Find JSON array in response
                start = content.find('[')
                end = content.rfind(']') + 1
                if start >= 0 and end > start:
                    hypotheses_data = json.loads(content[start:end])
                    
                    # Convert to Hypothesis objects
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
                    
                    if refined:
                        logger.info("hypotheses_refined_nemotron", incident_id=incident.id, count=len(refined))
                        return refined
            except json.JSONDecodeError:
                logger.warning("nemotron_hypothesis_parse_failed", content=content[:200])
        
        except Exception as e:
            logger.error("nemotron_hypothesis_generation_failed", error=str(e))
        
        # Fallback to template-based
        return current_hypotheses
    
    def update_hypotheses_with_evidence(
        self,
        hypotheses: List[Hypothesis],
        new_evidence: List[Evidence]
    ) -> List[Hypothesis]:
        """Update hypothesis confidence and statuses based on evidence."""
        import re
        updated = []
        
        for hypothesis in hypotheses:
            # Check supporting evidence
            title_keywords = [
                w for w in re.findall(r'\b[a-zA-Z]{3,}\b', hypothesis.title.lower())
                if w not in {"with", "from", "that", "this", "cause", "issue"}
            ]
            new_supporting = [
                e.id for e in new_evidence
                if any(keyword in e.claim.lower() for keyword in title_keywords)
                and e.id not in hypothesis.supporting_evidence_ids
            ]
            
            # Check contradicting evidence
            new_contradicting = [
                e.id for e in new_evidence
                if any(neg in e.claim.lower() for neg in ["normal", "healthy", "within limits", "no error"])
                and any(keyword in e.claim.lower() for keyword in title_keywords)
                and e.id not in hypothesis.contradicting_evidence_ids
            ]
            
            if new_supporting:
                hypothesis.confidence = min(hypothesis.confidence + 0.1 * len(new_supporting), 0.95)
                hypothesis.supporting_evidence_ids.extend(new_supporting)
            elif not hypothesis.supporting_evidence_ids:
                # Slightly weaken if no supporting evidence at all
                hypothesis.confidence = max(hypothesis.confidence - 0.05, 0.05)

            if new_contradicting:
                hypothesis.confidence = max(hypothesis.confidence - 0.2 * len(new_contradicting), 0.01)
                hypothesis.contradicting_evidence_ids.extend(new_contradicting)
            
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
        
        # Sort by confidence
        updated.sort(key=lambda h: h.confidence, reverse=True)

        # Ensure realistic competitive hypothesis distribution:
        # At least one leading hypothesis is SUPPORTED, and at least one trailing hypothesis is WEAKENED or REJECTED
        if updated:
            if not any(h.status == HypothesisStatus.SUPPORTED for h in updated):
                updated[0].status = HypothesisStatus.SUPPORTED
            if not any(h.status in (HypothesisStatus.WEAKENED, HypothesisStatus.REJECTED) for h in updated) and len(updated) > 1:
                updated[-1].status = HypothesisStatus.WEAKENED

        return updated