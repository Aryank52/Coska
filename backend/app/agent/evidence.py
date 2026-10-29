"""Evidence engine for structured evidence extraction."""
import re
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter

from app.models import Evidence, SourceType, Incident
import structlog

logger = structlog.get_logger()


class LogAnalyzer:
    """Deterministic log analyzer for structured finding extraction."""
    
    # Common patterns
    TIMESTAMP_PATTERN = re.compile(
        r'(\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)'
    )
    ERROR_PATTERN = re.compile(r'(ERROR|FATAL|CRITICAL|Exception|Error|Timeout|timeout)', re.IGNORECASE)
    STACK_TRACE_PATTERN = re.compile(r'(at\s+\w+\(|File\s+".*?",\s+line\s+\d+|^\s+at\s+)', re.MULTILINE)
    SERVICE_PATTERN = re.compile(r'(service|component|module)[:\s]+(\w+)', re.IGNORECASE)
    REQUEST_ID_PATTERN = re.compile(r'(request[_-]?id|trace[_-]?id|correlation[_-]?id)[:\s]+([a-zA-Z0-9\-_]+)', re.IGNORECASE)
    DB_POOL_PATTERN = re.compile(r'(connection pool|pool).*?(exhaust|timeout|full|wait)', re.IGNORECASE)
    HTTP_ERROR_PATTERN = re.compile(r'HTTP\s+(\d{3})', re.IGNORECASE)
    
    def analyze(self, logs: str, incident_id: str) -> List[Evidence]:
        """Analyze logs and extract structured evidence."""
        evidence = []
        
        if not logs:
            return evidence
        
        lines = logs.strip().split('\n')
        
        # Extract timestamps
        timestamps = self.TIMESTAMP_PATTERN.findall(logs)
        if timestamps:
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.LOG,
                claim=f"Found {len(timestamps)} timestamped log entries spanning from {timestamps[0]} to {timestamps[-1]}",
                reference=f"Log lines 1-{len(lines)}",
                confidence=0.9,
                related_component="logging",
                raw_data={"timestamp_count": len(timestamps), "first": timestamps[0], "last": timestamps[-1]}
            ))
        
        # Count error types
        error_matches = self.ERROR_PATTERN.findall(logs)
        error_counts = Counter(error_matches)
        if error_counts:
            top_errors = error_counts.most_common(5)
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.LOG,
                claim=f"Error frequency analysis: {', '.join([f'{e} ({c})' for e, c in top_errors])}",
                reference="Log error pattern matching",
                confidence=0.85,
                related_component="error_handling",
                raw_data={"error_counts": dict(error_counts)}
            ))
        
        # Check for stack traces
        stack_traces = self.STACK_TRACE_PATTERN.findall(logs)
        if stack_traces:
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.LOG,
                claim=f"Found {len(stack_traces)} stack trace frames indicating code-level failures",
                reference="Stack trace pattern matching",
                confidence=0.8,
                related_component="application_code",
                raw_data={"stack_frame_count": len(stack_traces)}
            ))
        
        # Extract service/component names
        services = self.SERVICE_PATTERN.findall(logs)
        if services:
            service_names = list(set([s[1] for s in services]))
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.LOG,
                claim=f"Identified services/components in logs: {', '.join(service_names)}",
                reference="Service pattern extraction",
                confidence=0.7,
                related_component="service_discovery",
                raw_data={"services": service_names}
            ))
        
        # Extract request IDs
        request_ids = self.REQUEST_ID_PATTERN.findall(logs)
        if request_ids:
            unique_ids = list(set([r[1] for r in request_ids]))
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.LOG,
                claim=f"Found {len(unique_ids)} unique request/trace IDs for correlation",
                reference="Request ID pattern extraction",
                confidence=0.75,
                related_component="distributed_tracing",
                raw_data={"request_ids": unique_ids[:10]}
            ))
        
        # Database connection pool issues
        pool_matches = self.DB_POOL_PATTERN.findall(logs)
        if pool_matches:
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.LOG,
                claim=f"Database connection pool exhaustion detected: {len(pool_matches)} pool-related errors",
                reference="Database pool error pattern matching",
                confidence=0.95,
                related_component="database_connection_pool",
                raw_data={"pool_error_count": len(pool_matches)}
            ))
        
        # HTTP error rates
        http_errors = self.HTTP_ERROR_PATTERN.findall(logs)
        if http_errors:
            error_5xx = [e for e in http_errors if e.startswith('5')]
            error_4xx = [e for e in http_errors if e.startswith('4')]
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.LOG,
                claim=f"HTTP errors: {len(error_5xx)} 5xx, {len(error_4xx)} 4xx out of {len(http_errors)} total",
                reference="HTTP status code extraction",
                confidence=0.9,
                related_component="http_layer",
                raw_data={"5xx": len(error_5xx), "4xx": len(error_4xx), "total": len(http_errors)}
            ))
        
        # Repeated patterns (lines that appear multiple times)
        line_counts = Counter(lines)
        repeated = [(line, count) for line, count in line_counts.items() if count > 3]
        if repeated:
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.LOG,
                claim=f"Found {len(repeated)} repeated log patterns (occurring >3 times)",
                reference="Log line frequency analysis",
                confidence=0.8,
                related_component="pattern_detection",
                raw_data={"repeated_patterns": repeated[:5]}
            ))
        
        logger.info("log_analysis_complete", incident_id=incident_id, evidence_count=len(evidence))
        return evidence


class ConfigAnalyzer:
    """Analyze configuration for evidence."""
    
    def analyze(self, config: str, incident_id: str) -> List[Evidence]:
        """Analyze configuration and extract evidence."""
        evidence = []
        
        if not config:
            return evidence
        
        # Common config patterns
        pool_size_match = re.search(r'DB_POOL_SIZE[:\s=]+(\d+)', config, re.IGNORECASE)
        if pool_size_match:
            pool_size = int(pool_size_match.group(1))
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.CONFIG,
                claim=f"Database connection pool size configured as {pool_size}",
                reference="DB_POOL_SIZE configuration",
                confidence=1.0,
                related_component="database_connection_pool",
                raw_data={"pool_size": pool_size}
            ))
        
        max_connections_match = re.search(r'MAX_CONNECTIONS[:\s=]+(\d+)', config, re.IGNORECASE)
        if max_connections_match:
            max_conn = int(max_connections_match.group(1))
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.CONFIG,
                claim=f"Database max connections configured as {max_conn}",
                reference="MAX_CONNECTIONS configuration",
                confidence=1.0,
                related_component="database_connection_pool",
                raw_data={"max_connections": max_conn}
            ))
        
        timeout_match = re.search(r'(TIMEOUT|timeout)[:\s=]+(\d+)', config, re.IGNORECASE)
        if timeout_match:
            timeout = int(timeout_match.group(2))
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.CONFIG,
                claim=f"Timeout configured as {timeout} seconds",
                reference=f"{timeout_match.group(1)} configuration",
                confidence=1.0,
                related_component="timeout_settings",
                raw_data={"timeout_seconds": timeout}
            ))
        
        # Detect environment variables
        env_vars = re.findall(r'(\w+)[:\s=]+([^\s\n]+)', config)
        if env_vars:
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.CONFIG,
                claim=f"Found {len(env_vars)} configuration parameters",
                reference="Configuration parameter extraction",
                confidence=0.7,
                related_component="configuration",
                raw_data={"parameters": dict(env_vars[:20])}
            ))
        
        return evidence


class DeploymentAnalyzer:
    """Analyze deployment information for evidence."""
    
    def analyze(self, deployment: str, incident_id: str) -> List[Evidence]:
        """Analyze deployment info and extract evidence."""
        evidence = []
        
        if not deployment:
            return evidence
        
        # Version pattern
        version_match = re.search(r'v?(\d+\.\d+\.\d+)', deployment)
        if version_match:
            version = version_match.group(1)
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.DEPLOYMENT,
                claim=f"Recent deployment version: {version}",
                reference="Deployment version extraction",
                confidence=0.9,
                related_component="deployment",
                raw_data={"version": version}
            ))
        
        # Time-based patterns
        time_match = re.search(r'(deployed|released|updated).*?(?:at|on)\s+([\d\-T:]+)', deployment, re.IGNORECASE)
        if time_match:
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.DEPLOYMENT,
                claim=f"Deployment occurred at {time_match.group(2)}",
                reference="Deployment timestamp extraction",
                confidence=0.8,
                related_component="deployment",
                raw_data={"timestamp": time_match.group(2)}
            ))
        
        # Changed components
        changed = re.findall(r'(changed|updated|modified|added).*?(\w+)', deployment, re.IGNORECASE)
        if changed:
            components = list(set([c[1] for c in changed]))
            evidence.append(Evidence(
                incident_id=incident_id,
                source_type=SourceType.DEPLOYMENT,
                claim=f"Deployment changed components: {', '.join(components)}",
                reference="Deployment change extraction",
                confidence=0.7,
                related_component="deployment",
                raw_data={"changed_components": components}
            ))
        
        return evidence


class EvidenceEngine:
    """Main evidence engine coordinating all analyzers."""
    
    def __init__(self):
        self.log_analyzer = LogAnalyzer()
        self.config_analyzer = ConfigAnalyzer()
        self.deployment_analyzer = DeploymentAnalyzer()
    
    def collect_evidence(self, incident: Incident) -> List[Evidence]:
        """Collect all evidence for an incident."""
        all_evidence = []
        
        # Analyze logs
        if incident.logs:
            all_evidence.extend(self.log_analyzer.analyze(incident.logs, incident.id))
        
        # Analyze configuration
        config = incident.metadata.get('configuration', '') or incident.repository or ''
        if config:
            all_evidence.extend(self.config_analyzer.analyze(config, incident.id))
        
        # Analyze deployment
        if incident.deployment:
            all_evidence.extend(self.deployment_analyzer.analyze(incident.deployment, incident.id))
        
        # Add repository evidence if available
        if incident.repository:
            all_evidence.append(Evidence(
                incident_id=incident.id,
                source_type=SourceType.REPOSITORY,
                claim=f"Repository reference: {incident.repository}",
                reference="Incident metadata",
                confidence=0.6,
                related_component="source_code",
                raw_data={"repository": incident.repository}
            ))
        
        logger.info("evidence_collection_complete", incident_id=incident.id, total=len(all_evidence))
        return all_evidence