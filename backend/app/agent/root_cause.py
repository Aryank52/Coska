"""Root cause analysis engine using Nemotron."""
from typing import List, Dict, Any, Optional
import json
import structlog

from app.models import Incident, Evidence, Hypothesis
from app.services.nebius import get_nebius_client

logger = structlog.get_logger()


class RootCauseEngine:
    """Identifies root cause using Nemotron reasoning over all evidence."""
    
    def __init__(self):
        self.client = get_nebius_client()
    
    async def identify_root_cause(
        self,
        incident: Incident,
        timeline: List[Dict[str, Any]],
        evidence: List[Evidence],
        hypotheses: List[Hypothesis]
    ) -> Dict[str, Any]:
        """Use Nemotron to identify the root cause."""
        
        # Prepare comprehensive context
        evidence_summary = "\n".join([
            f"  {e.id} [{e.source_type.value}] (conf: {e.confidence:.0%}): {e.claim}"
            for e in evidence
        ])
        
        timeline_summary = "\n".join([
            f"  {e['timestamp']} [{e['event_type']}] {e['title']}: {e['description']}"
            for e in timeline
        ])
        
        hypotheses_summary = "\n".join([
            f"  {h.id}: {h.title} (conf: {h.confidence:.0%}, status: {h.status.value})"
            for h in hypotheses
        ])
        
        prompt = f"""You are COSKA, an autonomous incident intelligence system performing root cause analysis.

INCIDENT:
  ID: {incident.id}
  Service: {incident.service}
  Severity: {incident.severity}
  Description: {incident.description}

TIMELINE:
{timeline_summary}

EVIDENCE ({len(evidence)} items):
{evidence_summary}

HYPOTHESES ({len(hypotheses)}):
{hypotheses_summary}

TASK: Determine the root cause based on ALL evidence. You must:
1. Identify the single strongest root cause explanation
2. List supporting evidence IDs
3. List contradicting evidence IDs
4. List rejected hypotheses with reasoning
5. Assign confidence (0.0-1.0)
6. Note any remaining uncertainty
7. Recommend a specific remediation

CRITICAL RULES:
- If evidence is insufficient for a confident conclusion, set confidence < 0.5 and uncertainty = "INSUFFICIENT_EVIDENCE"
- Do not hallucinate. Only use provided evidence.
- The root cause must be traceable to specific evidence IDs.
- Distinguish between correlation and causation.

Return ONLY valid JSON with this exact structure:
{{
  "root_cause": "string",
  "confidence": 0.0,
  "supporting_evidence_ids": ["E-XXX"],
  "contradicting_evidence_ids": ["E-XXX"],
  "rejected_hypotheses": [
    {{"id": "H-XXX", "reason": "string"}}
  ],
  "uncertainty": "string or null",
  "recommended_remediation": {{
    "description": "string",
    "exact_change": "string",
    "expected_effect": "string",
    "risk": "LOW|MEDIUM|HIGH",
    "blast_radius": "string",
    "rollback_plan": "string"
  }}
}}"""
        
        try:
            result = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are COSKA, an expert root cause analyst. Return only valid JSON. Be precise and evidence-driven."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            content = result["choices"][0]["message"]["content"]
            
            # Extract JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                root_cause_data = json.loads(content[start:end])
                logger.info("root_cause_identified", incident_id=incident.id, cause=root_cause_data.get("root_cause"))
                return root_cause_data
            
        except Exception as e:
            logger.error("root_cause_analysis_failed", error=str(e))
        
        # Fallback
        return {
            "root_cause": "Unable to determine - insufficient evidence",
            "confidence": 0.0,
            "supporting_evidence_ids": [],
            "contradicting_evidence_ids": [],
            "rejected_hypotheses": [],
            "uncertainty": "INSUFFICIENT_EVIDENCE",
            "recommended_remediation": {
                "description": "Collect more evidence",
                "exact_change": "N/A",
                "expected_effect": "N/A",
                "risk": "LOW",
                "blast_radius": "N/A",
                "rollback_plan": "N/A"
            }
        }