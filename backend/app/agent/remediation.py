"""Remediation engine for generating and validating fixes."""
from typing import Dict, Any, List, Optional
import structlog

from app.models import Remediation, RemediationType, Incident, Hypothesis, Evidence
from app.services.nebius import get_nebius_client

logger = structlog.get_logger()


class RemediationEngine:
    """Generates and validates remediation plans."""
    
    def __init__(self):
        self.client = get_nebius_client()
    
    # Allowed remediation patterns (security)
    ALLOWED_CONFIG_CHANGES = {
        "DB_POOL_SIZE": {"type": "int", "min": 1, "max": 100},
        "MAX_CONNECTIONS": {"type": "int", "min": 1, "max": 500},
        "TIMEOUT": {"type": "int", "min": 1, "max": 300},
        "POOL_TIMEOUT": {"type": "int", "min": 1, "max": 60},
    }
    
    def generate_remediation(
        self,
        incident: Incident,
        root_cause: Dict[str, Any],
        evidence: List[Evidence]
    ) -> Remediation:
        """Generate remediation from root cause analysis."""
        
        rec = root_cause.get("recommended_remediation", {})
        
        # Determine remediation type
        remediation_type = RemediationType.CONFIGURATION_CHANGE
        if "code" in rec.get("description", "").lower():
            remediation_type = RemediationType.CODE_CHANGE
        elif "dependency" in rec.get("description", "").lower():
            remediation_type = RemediationType.DEPENDENCY_CHANGE
        elif "rollback" in rec.get("description", "").lower():
            remediation_type = RemediationType.SAFE_ROLLBACK
        elif "feature flag" in rec.get("description", "").lower():
            remediation_type = RemediationType.FEATURE_FLAG_CHANGE
        
        remediation = Remediation(
            incident_id=incident.id,
            hypothesis_id="",  # Will be set by orchestrator
            type=remediation_type,
            description=rec.get("description", "Apply configuration fix"),
            exact_change=rec.get("exact_change", ""),
            expected_effect=rec.get("expected_effect", ""),
            risk=rec.get("risk", "LOW"),
            blast_radius=rec.get("blast_radius", "SANDBOX_ONLY"),
            rollback_plan=rec.get("rollback_plan", "Revert configuration change")
        )
        
        return remediation
    
    def validate_remediation(self, remediation: Remediation) -> Dict[str, Any]:
        """Validate remediation for safety and correctness."""
        errors = []
        warnings = []
        
        # Check exact_change format for config changes
        if remediation.type == RemediationType.CONFIGURATION_CHANGE:
            # Expected format: "KEY: old_value -> new_value"
            if "->" not in remediation.exact_change:
                errors.append("Configuration change must be in format 'KEY: old -> new'")
            else:
                parts = remediation.exact_change.split("->")
                if len(parts) == 2:
                    key_part = parts[0].strip()
                    key = key_part.split(":")[0].strip() if ":" in key_part else key_part
                    
                    if key not in self.ALLOWED_CONFIG_CHANGES:
                        warnings.append(f"Configuration key '{key}' not in allowlist")
                    else:
                        # Validate new value
                        try:
                            new_value = parts[1].strip()
                            spec = self.ALLOWED_CONFIG_CHANGES[key]
                            if spec["type"] == "int":
                                val = int(new_value)
                                if val < spec["min"] or val > spec["max"]:
                                    errors.append(f"Value {val} outside allowed range [{spec['min']}, {spec['max']}]")
                        except ValueError:
                            errors.append(f"Invalid value format for {key}")
        
        # Risk validation
        if remediation.risk == "HIGH" and remediation.blast_radius != "SANDBOX_ONLY":
            errors.append("HIGH risk remediation must have blast_radius=SANDBOX_ONLY")
        
        # Rollback plan required
        if not remediation.rollback_plan or remediation.rollback_plan.strip() == "":
            errors.append("Rollback plan is required")
        
        is_valid = len(errors) == 0
        
        return {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings
        }
    
    async def generate_remediation_with_nemotron(
        self,
        incident: Incident,
        root_cause: Dict[str, Any],
        evidence: List[Evidence]
    ) -> Remediation:
        """Use Nemotron to generate detailed remediation."""
        
        evidence_summary = "\n".join([
            f"  {e.id} [{e.source_type.value}]: {e.claim}"
            for e in evidence
        ])
        
        prompt = f"""You are COSKA generating a remediation plan.

Incident: {incident.id} ({incident.service})
Root Cause: {root_cause.get('root_cause', 'Unknown')}
Confidence: {root_cause.get('confidence', 0):.0%}

Evidence:
{evidence_summary}

Generate a SPECIFIC, VALIDATED remediation. The fix must be:
1. Configurable (not code changes unless absolutely necessary)
2. Reversible with clear rollback plan
3. Low blast radius (sandbox only)
4. Precisely specified

Return JSON:
{{
  "type": "CONFIGURATION_CHANGE|CODE_CHANGE|DEPENDENCY_CHANGE|SAFE_ROLLBACK|FEATURE_FLAG_CHANGE",
  "description": "Human-readable description",
  "exact_change": "Precise change (e.g., 'DB_POOL_SIZE: 5 -> 30')",
  "expected_effect": "What this fixes",
  "risk": "LOW|MEDIUM|HIGH",
  "blast_radius": "SANDBOX_ONLY",
  "rollback_plan": "Exact steps to revert"
}}"""
        
        try:
            result = await self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "You are COSKA remediation planner. Generate precise, safe, reversible fixes. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = result["choices"][0]["message"]["content"]
            import json
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                rec = json.loads(content[start:end])
                
                remediation = Remediation(
                    incident_id=incident.id,
                    hypothesis_id="",
                    type=RemediationType(rec.get("type", "CONFIGURATION_CHANGE")),
                    description=rec.get("description", ""),
                    exact_change=rec.get("exact_change", ""),
                    expected_effect=rec.get("expected_effect", ""),
                    risk=rec.get("risk", "LOW"),
                    blast_radius=rec.get("blast_radius", "SANDBOX_ONLY"),
                    rollback_plan=rec.get("rollback_plan", "")
                )
                
                logger.info("remediation_generated_nemotron", incident_id=incident.id)
                return remediation
                
        except Exception as e:
            logger.error("nemotron_remediation_failed", error=str(e))
        
        # Fallback to root cause recommendation
        return self.generate_remediation(incident, root_cause, evidence)