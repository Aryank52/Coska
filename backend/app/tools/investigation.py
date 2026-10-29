"""Investigation tools for COSKA agent."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import structlog
import re

from app.tools.registry import BaseTool, ToolInput, ToolOutput, ToolResult, get_tool_registry
from app.models import Evidence, SourceType, Incident
from app.services.tavily import get_tavily_client
from app.config import get_settings

logger = structlog.get_logger()


# =============================================================================
# Input/Output Models
# =============================================================================

class InspectLogsInput(ToolInput):
    incident_id: str
    pattern: Optional[str] = None
    max_lines: int = 1000


class InspectLogsOutput(ToolOutput):
    evidence: List[Dict[str, Any]]


class InspectConfigurationInput(ToolInput):
    incident_id: str
    config_keys: Optional[List[str]] = None


class InspectConfigurationOutput(ToolOutput):
    evidence: List[Dict[str, Any]]


class InspectDeploymentInput(ToolInput):
    incident_id: str


class InspectDeploymentOutput(ToolOutput):
    evidence: List[Dict[str, Any]]


class SearchWebInput(ToolInput):
    query: str
    max_results: int = 5


class SearchWebOutput(ToolOutput):
    evidence: List[Dict[str, Any]]


class InspectRuntimeInput(ToolInput):
    incident_id: str
    metrics: Optional[List[str]] = None


class InspectRuntimeOutput(ToolOutput):
    evidence: List[Dict[str, Any]]


class InspectRepositoryInput(ToolInput):
    incident_id: str
    paths: Optional[List[str]] = None


class InspectRepositoryOutput(ToolOutput):
    evidence: List[Dict[str, Any]]


# =============================================================================
# Tool Implementations
# =============================================================================

class InspectLogsTool(BaseTool):
    """Inspect incident logs for patterns and errors."""
    
    name = "inspect_logs"
    description = "Analyze incident logs for error patterns, timeouts, stack traces, and anomalies"
    input_model = InspectLogsInput
    output_model = InspectLogsOutput
    
    async def execute(self, input_data: InspectLogsInput) -> ToolResult:
        # Get incident from storage (simplified - in production use storage service)
        # For now, we'll extract from the incident context
        evidence = []
        
        # This would typically fetch logs from a logging system
        # For the demo, we simulate based on the incident
        from app.agent.evidence import LogAnalyzer
        from app.services.storage import get_storage
        
        storage = get_storage()
        incident = storage.get_incident(input_data.incident_id)
        
        if incident and incident.logs:
            analyzer = LogAnalyzer()
            evidence = analyzer.analyze(incident.logs, input_data.incident_id)
        
        return ToolResult(
            success=True,
            data={"evidence": [e.dict() for e in evidence]},
            metadata={"evidence_count": len(evidence)}
        )


class InspectConfigurationTool(BaseTool):
    """Inspect configuration for relevant settings."""
    
    name = "inspect_configuration"
    description = "Extract and analyze configuration parameters from incident metadata"
    input_model = InspectConfigurationInput
    output_model = InspectConfigurationOutput
    
    async def execute(self, input_data: InspectConfigurationInput) -> ToolResult:
        from app.agent.evidence import ConfigAnalyzer
        from app.services.storage import get_storage
        
        storage = get_storage()
        incident = storage.get_incident(input_data.incident_id)
        
        evidence = []
        if incident:
            config = incident.metadata.get('configuration', '')
            if config:
                analyzer = ConfigAnalyzer()
                evidence = analyzer.analyze(config, input_data.incident_id)
        
        return ToolResult(
            success=True,
            data={"evidence": [e.dict() for e in evidence]},
            metadata={"evidence_count": len(evidence)}
        )


class InspectDeploymentTool(BaseTool):
    """Inspect deployment information."""
    
    name = "inspect_deployment"
    description = "Analyze deployment metadata for version, timing, and changes"
    input_model = InspectDeploymentInput
    output_model = InspectDeploymentOutput
    
    async def execute(self, input_data: InspectDeploymentInput) -> ToolResult:
        from app.agent.evidence import DeploymentAnalyzer
        from app.services.storage import get_storage
        
        storage = get_storage()
        incident = storage.get_incident(input_data.incident_id)
        
        evidence = []
        if incident and incident.deployment:
            analyzer = DeploymentAnalyzer()
            evidence = analyzer.analyze(incident.deployment, input_data.incident_id)
        
        return ToolResult(
            success=True,
            data={"evidence": [e.dict() for e in evidence]},
            metadata={"evidence_count": len(evidence)}
        )


class SearchWebTool(BaseTool):
    """Search the web for technical information."""
    
    name = "search_web"
    description = "Search external technical documentation, error patterns, and best practices"
    input_model = SearchWebInput
    output_model = SearchWebOutput
    
    async def execute(self, input_data: SearchWebInput) -> ToolResult:
        client = get_tavily_client()
        
        # Check if API key is available
        settings = get_settings()
        if not settings.tavily_api_key or settings.tavily_api_key == "your_tavily_api_key_here":
            return ToolResult(
                success=False,
                error="Tavily API key not configured",
                metadata={"tool": "search_web"}
            )
        
        try:
            result = await client.search(input_data.query, max_results=input_data.max_results)
            
            # Convert Tavily results to evidence format
            evidence = []
            for idx, item in enumerate(result.get("results", [])):
                evidence.append({
                    "id": f"WEB-{input_data.query[:4].upper()}-{idx}",
                    "source_type": "WEB",
                    "claim": f"External research: {item.get('title', '')} - {item.get('content', '')[:200]}",
                    "reference": item.get("url", ""),
                    "confidence": 0.75,
                    "related_component": "external_research",
                    "raw_data": {
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "snippet": item.get("content", "")[:500]
                    }
                })
            
            return ToolResult(
                success=True,
                data={"evidence": evidence},
                metadata={"query": input_data.query, "results_count": len(evidence)}
            )
        except Exception as e:
            logger.error("tavily_search_failed", error=str(e))
            return ToolResult(
                success=False,
                error=f"Web search failed: {str(e)}",
                metadata={"query": input_data.query}
            )


class InspectRuntimeTool(BaseTool):
    """Inspect runtime metrics."""
    
    name = "inspect_runtime"
    description = "Check runtime metrics like CPU, memory, connections, network"
    input_model = InspectRuntimeInput
    output_model = InspectRuntimeOutput
    
    async def execute(self, input_data: InspectRuntimeInput) -> ToolResult:
        # In a real implementation, this would connect to monitoring systems
        # For demo, return simulated metrics
        evidence = [{
            "id": f"RUNTIME-{input_data.incident_id[:8]}",
            "source_type": "RUNTIME",
            "claim": "Runtime metrics: active_db_connections=45, cpu_usage=23%, memory_usage=67%, network_latency=2ms",
            "reference": "Runtime monitoring system",
            "confidence": 0.7,
            "related_component": "runtime_monitoring",
            "raw_data": {
                "active_connections": 45,
                "cpu_percent": 23,
                "memory_percent": 67,
                "network_latency_ms": 2
            }
        }]
        
        return ToolResult(
            success=True,
            data={"evidence": evidence},
            metadata={"evidence_count": len(evidence)}
        )


class InspectRepositoryTool(BaseTool):
    """Inspect repository files."""
    
    name = "inspect_repository"
    description = "Analyze source code, configuration files, and dependencies"
    input_model = InspectRepositoryInput
    output_model = InspectRepositoryOutput
    
    async def execute(self, input_data: InspectRepositoryInput) -> ToolResult:
        from app.services.storage import get_storage
        import os
        
        storage = get_storage()
        incident = storage.get_incident(input_data.incident_id)
        
        evidence = []
        if incident and incident.repository:
            # For demo, read the local payment-api repo
            repo_path = "./demo/payment-api"
            if os.path.exists(repo_path):
                # Check key files
                key_files = ["app/config.py", "app/main.py", "requirements.txt"]
                for kf in key_files:
                    full_path = os.path.join(repo_path, kf)
                    if os.path.exists(full_path):
                        with open(full_path, 'r') as f:
                            content = f.read()
                        evidence.append({
                            "id": f"REPO-{kf.replace('/', '-').replace('.', '-')}",
                            "source_type": "REPOSITORY",
                            "claim": f"Repository file {kf}: {len(content)} chars",
                            "reference": f"Repository: {kf}",
                            "confidence": 0.8,
                            "related_component": "source_code",
                            "raw_data": {"file": kf, "size": len(content), "preview": content[:200]}
                        })
        
        return ToolResult(
            success=True,
            data={"evidence": evidence},
            metadata={"evidence_count": len(evidence)}
        )


# =============================================================================
# Tool Registration
# =============================================================================

def register_all_tools() -> None:
    """Register all investigation tools in the global registry."""
    registry = get_tool_registry()
    
    registry.register(InspectLogsTool())
    registry.register(InspectConfigurationTool())
    registry.register(InspectDeploymentTool())
    registry.register(SearchWebTool())
    registry.register(InspectRuntimeTool())
    registry.register(InspectRepositoryTool())
    
    logger.info("all_tools_registered", count=len(registry._tools))