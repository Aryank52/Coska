"""Incident NLP Intelligence - Lightweight incident understanding layer.

Extracts structured information from incident metadata using deterministic
parsing and AI reasoning where semantic interpretation adds value.
"""
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import structlog

from app.models import Incident, Severity
from app.services.providers import get_provider

logger = structlog.get_logger()


class IncidentIntelligence(BaseModel):
    """Structured incident intelligence output."""
    service: str
    severity: Severity
    symptoms: List[str] = Field(default_factory=list)
    components: List[str] = Field(default_factory=list)
    environment: str = "production"
    error_types: List[str] = Field(default_factory=list)
    probable_causes: List[str] = Field(default_factory=list)
    timestamps: List[str] = Field(default_factory=list)
    configuration_values: Dict[str, str] = Field(default_factory=dict)
    suspected_dependencies: List[str] = Field(default_factory=list)
    business_impact: str = ""
    keywords: List[str] = Field(default_factory=list)
    technical_entities: List[str] = Field(default_factory=list)
    extraction_method: str = "deterministic"  # or "ai_enhanced"


class IncidentIntelligenceEngine:
    """Lightweight incident understanding layer using deterministic extraction
    with optional AI enhancement for semantic interpretation.
    """
    
    # Deterministic patterns for common incident types
    SYMPTOM_PATTERNS = {
        "http_500_spike": [
            r"http\s+500",
            r"5xx",
            r"internal server error",
            r"error rate.*increased",
        ],
        "database_timeout": [
            r"timeout.*waiting.*for.*database.*connection",
            r"connection pool.*exhaust",
            r"pool.*timeout",
            r"queuepool.*limit",
            r"connection.*acquisition.*timeout",
        ],
        "connection_pool_exhaustion": [
            r"pool.*exhaust",
            r"connection pool.*full",
            r"cannot acquire connection",
            r"no connection available",
        ],
        "upstream_timeout": [
            r"upstream.*timeout",
            r"gateway.*timeout",
            r"504",
            r"request.*timeout",
        ],
        "memory_pressure": [
            r"out of memory",
            r"oom",
            r"heap.*exhaust",
            r"memory.*leak",
            r"garbage collection",
        ],
        "deployment_regression": [
            r"recent deployment",
            r"just deployed",
            r"after deployment",
            r"release.*caused",
        ],
        "cache_stampede": [
            r"cache.*miss.*spike",
            r"thundering herd",
            r"cache.*stampede",
        ],
        "network_instability": [
            r"network.*error",
            r"connection.*reset",
            r"dns.*fail",
            r"unreachable",
        ],
    }
    
    ERROR_TYPE_PATTERNS = {
        "database": [r"database", r"postgres", r"sql", r"pool", r"connection"],
        "network": [r"timeout", r"network", r"dns", r"unreachable", r"reset"],
        "memory": [r"memory", r"oom", r"heap", r"garbage collection", r"gc"],
        "application": [r"exception", r"error", r"null pointer", r"segmentation"],
        "deployment": [r"deployment", r"config", r"environment", r"credential"],
        "dependency": [r"upstream", r"downstream", r"third.?party", r"external"],
    }
    
    COMPONENT_PATTERNS = {
        "database": [r"postgres", r"mysql", r"database", r"db", r"pool"],
        "cache": [r"redis", r"memcache", r"cache"],
        "api_gateway": [r"gateway", r"nginx", r"proxy", r"ingress"],
        "application": [r"service", r"api", r"worker", r"app"],
        "message_queue": [r"kafka", r"rabbit", r"queue", r"message"],
        "external_service": [r"payment", r"stripe", r"provider", r"third.?party"],
    }
    
    CONFIG_PATTERNS = {
        "DB_POOL_SIZE": r"DB_POOL_SIZE[:\s=]+(\d+)",
        "DB_POOL_TIMEOUT": r"DB_POOL_TIMEOUT[:\s=]+(\d+)",
        "RETRY_COUNT": r"RETRY_COUNT[:\s=]+(\d+)",
        "TIMEOUT": r"TIMEOUT[:\s=]+(\d+)",
        "MAX_CONNECTIONS": r"MAX_CONNECTIONS[:\s=]+(\d+)",
        "CACHE_TTL": r"CACHE_TTL[:\s=]+(\d+)",
        "MEMORY_LIMIT": r"MEMORY_LIMIT[:\s=]+(\w+)",
    }

    def __init__(self):
        self.provider = get_provider()
    
    def extract_deterministic(self, incident: Incident) -> IncidentIntelligence:
        """Extract structured intelligence using deterministic pattern matching."""
        intelligence = IncidentIntelligence(
            service=incident.service,
            severity=incident.severity,
        )
        
        # Combine all text sources
        all_text = " ".join(filter(None, [
            incident.description,
            incident.logs,
            incident.deployment,
            incident.repository,
            str(incident.metadata.get("configuration", "")),
        ])).lower()
        
        # Extract symptoms
        for symptom, patterns in self.SYMPTOM_PATTERNS.items():
            if any(re.search(p, all_text, re.IGNORECASE) for p in patterns):
                intelligence.symptoms.append(symptom.replace("_", " ").title())
        
        # Extract error types
        for error_type, patterns in self.ERROR_TYPE_PATTERNS.items():
            if any(re.search(p, all_text, re.IGNORECASE) for p in patterns):
                intelligence.error_types.append(error_type)
        
        # Extract components
        for component, patterns in self.COMPONENT_PATTERNS.items():
            if any(re.search(p, all_text, re.IGNORECASE) for p in patterns):
                intelligence.components.append(component)
        
        # Extract configuration values
        config_text = str(incident.metadata.get("configuration", ""))
        for key, pattern in self.CONFIG_PATTERNS.items():
            match = re.search(pattern, config_text, re.IGNORECASE)
            if match:
                intelligence.configuration_values[key] = match.group(1)
        
        # Extract timestamps
        timestamp_matches = re.findall(
            r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?',
            str(incident.logs) + " " + str(incident.deployment)
        )
        intelligence.timestamps = timestamp_matches[:10]  # Limit
        
        # Extract suspected dependencies from logs and description
        dep_patterns = [
            r"(postgres|postgresql|mysql|mongodb)",
            r"(redis|memcached)",
            r"(kafka|rabbitmq)",
            r"(stripe|paypal|payment)",
            r"(aws|gcp|azure|cloud)",
            r"(kubernetes|k8s)",
        ]
        for pattern in dep_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            intelligence.suspected_dependencies.extend(matches)
        intelligence.suspected_dependencies = list(set(intelligence.suspected_dependencies))
        
        # Extract probable causes based on symptoms
        if "http_500_spike" in all_text and "database_timeout" in all_text:
            intelligence.probable_causes.append("Database connection pool exhaustion")
        if "connection_pool_exhaustion" in all_text:
            intelligence.probable_causes.append("Undersized connection pool configuration")
        if "upstream_timeout" in all_text:
            intelligence.probable_causes.append("Upstream service degradation with retry storm")
        if "deployment_regression" in all_text:
            intelligence.probable_causes.append("Bad deployment configuration")
        if "memory_pressure" in all_text:
            intelligence.probable_causes.append("Application memory leak or pressure")
        if "cache_stampede" in all_text:
            intelligence.probable_causes.append("Cache stampede / thundering herd")
        
        # Extract keywords (technical terms)
        intelligence.keywords = list(set(
            [kw for kw in re.findall(r'\b[a-zA-Z_]{3,}\b', all_text) 
             if kw.lower() not in {"the", "and", "for", "with", "from", "has", "have", "error", "service", "api"}]
        )[:20])
        
        # Business impact estimation
        if incident.severity == Severity.CRITICAL:
            intelligence.business_impact = "High - Customer-facing payment failures, revenue impact"
        elif incident.severity == Severity.HIGH:
            intelligence.business_impact = "Medium - Degraded user experience, potential revenue loss"
        else:
            intelligence.business_impact = "Low - Internal system degradation"
        
        return intelligence
    
    async def extract_with_ai(self, incident: Incident) -> IncidentIntelligence:
        """Enhance extraction with AI reasoning for semantic interpretation."""
        # First get deterministic extraction
        intelligence = self.extract_deterministic(incident)
        intelligence.extraction_method = "ai_enhanced"
        
        # Prepare context for AI
        context = f"""
Incident: {incident.id}
Service: {incident.service}
Severity: {incident.severity}
Description: {incident.description}

Logs:
{incident.logs[:2000] if incident.logs else 'N/A'}

Deployment:
{incident.deployment[:500] if incident.deployment else 'N/A'}

Configuration:
{incident.metadata.get('configuration', 'N/A')[:1000]}

Current Extraction:
- Symptoms: {intelligence.symptoms}
- Error Types: {intelligence.error_types}
- Components: {intelligence.components}
- Config Values: {intelligence.configuration_values}
- Probable Causes: {intelligence.probable_causes}
"""
        
        prompt = f"""You are COSKA's incident intelligence engine. Enhance the incident analysis.

{context}

Provide enhancements as JSON:
{{
  "enhanced_symptoms": ["additional symptom descriptions"],
  "enhanced_components": ["additional affected components"],
  "enhanced_probable_causes": ["additional probable root causes"],
  "business_impact_assessment": "Detailed business impact description",
  "technical_entities": ["specific technical entities mentioned (services, databases, APIs, etc.)"],
  "recommended_investigation_priority": ["ordered list of investigation actions"]
}}"""
        
        try:
            result = await self.provider.chat_completion(
                messages=[
                    {"role": "system", "content": "You are COSKA, an expert incident analyst. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            import json
            content = result["choices"][0]["message"]["content"]
            
            # Extract JSON
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                enhancements = json.loads(content[start:end])
                
                # Merge enhancements
                if enhancements.get("enhanced_symptoms"):
                    intelligence.symptoms.extend(enhancements["enhanced_symptoms"])
                if enhancements.get("enhanced_components"):
                    intelligence.components.extend(enhancements["enhanced_components"])
                if enhancements.get("enhanced_probable_causes"):
                    intelligence.probable_causes.extend(enhancements["enhanced_probable_causes"])
                if enhancements.get("business_impact_assessment"):
                    intelligence.business_impact = enhancements["business_impact_assessment"]
                if enhancements.get("technical_entities"):
                    intelligence.technical_entities = enhancements["technical_entities"]
                if enhancements.get("recommended_investigation_priority"):
                    intelligence.metadata = intelligence.metadata or {}
                    intelligence.metadata["investigation_priority"] = enhancements["recommended_investigation_priority"]
            
            logger.info("incident_intelligence_ai_enhanced", incident_id=incident.id)
            
        except Exception as e:
            logger.warning("incident_intelligence_ai_failed", error=str(e))
        
        # Deduplicate
        intelligence.symptoms = list(dict.fromkeys(intelligence.symptoms))
        intelligence.components = list(dict.fromkeys(intelligence.components))
        intelligence.error_types = list(dict.fromkeys(intelligence.error_types))
        intelligence.probable_causes = list(dict.fromkeys(intelligence.probable_causes))
        intelligence.suspected_dependencies = list(dict.fromkeys(intelligence.suspected_dependencies))
        
        return intelligence
    
    async def analyze(self, incident: Incident, use_ai: bool = False) -> IncidentIntelligence:
        """Main entry point for incident intelligence analysis."""
        if use_ai:
            return await self.extract_with_ai(incident)
        return self.extract_deterministic(incident)


# Singleton
_intelligence_engine: Optional[IncidentIntelligenceEngine] = None


def get_intelligence_engine() -> IncidentIntelligenceEngine:
    global _intelligence_engine
    if _intelligence_engine is None:
        _intelligence_engine = IncidentIntelligenceEngine()
    return _intelligence_engine