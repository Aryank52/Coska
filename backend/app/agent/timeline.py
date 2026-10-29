"""Timeline builder for incident timeline construction."""
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import structlog

from app.models import Incident, Evidence, SourceType

logger = structlog.get_logger()


@dataclass
class TimelineEvent:
    """A single event in the incident timeline."""
    timestamp: datetime
    event_type: str
    title: str
    description: str
    source_type: SourceType
    evidence_ids: List[str] = field(default_factory=list)
    severity: str = "INFO"


class TimelineBuilder:
    """Builds incident timeline from evidence and metadata."""
    
    def build(self, incident: Incident, evidence: List[Evidence]) -> List[TimelineEvent]:
        """Build chronological timeline from incident and evidence."""
        events = []
        
        # Last healthy state (estimated from incident creation - some buffer)
        if incident.created_at:
            events.append(TimelineEvent(
                timestamp=incident.created_at,
                event_type="INCIDENT_REPORTED",
                title="Incident Reported",
                description=incident.description,
                source_type=SourceType.RUNTIME,
                severity="HIGH"
            ))
        
        # Deployment events
        deployment_evidence = [e for e in evidence if e.source_type == SourceType.DEPLOYMENT]
        for ev in deployment_evidence:
            if 'version' in ev.raw_data:
                events.append(TimelineEvent(
                    timestamp=ev.timestamp,
                    event_type="DEPLOYMENT",
                    title=f"Deployment {ev.raw_data.get('version', 'unknown')}",
                    description=ev.claim,
                    source_type=SourceType.DEPLOYMENT,
                    evidence_ids=[ev.id],
                    severity="MEDIUM"
                ))
        
        # Configuration changes
        config_evidence = [e for e in evidence if e.source_type == SourceType.CONFIG]
        for ev in config_evidence:
            events.append(TimelineEvent(
                timestamp=ev.timestamp,
                event_type="CONFIG_CHANGE",
                title="Configuration Change Detected",
                description=ev.claim,
                source_type=SourceType.CONFIG,
                evidence_ids=[ev.id],
                severity="MEDIUM"
            ))
        
        # First anomalies from logs
        log_evidence = [e for e in evidence if e.source_type == SourceType.LOG]
        for ev in log_evidence:
            if 'pool' in ev.claim.lower() or 'timeout' in ev.claim.lower() or 'error' in ev.claim.lower():
                events.append(TimelineEvent(
                    timestamp=ev.timestamp,
                    event_type="FIRST_ANOMALY",
                    title="First Anomaly Detected",
                    description=ev.claim,
                    source_type=SourceType.LOG,
                    evidence_ids=[ev.id],
                    severity="HIGH"
                ))
                break  # Only first anomaly
        
        # Error escalation
        for ev in log_evidence:
            if 'exhaust' in ev.claim.lower() or '5xx' in ev.claim or 'pool' in ev.claim.lower():
                events.append(TimelineEvent(
                    timestamp=ev.timestamp,
                    event_type="ERROR_ESCALATION",
                    title="Error Escalation",
                    description=ev.claim,
                    source_type=SourceType.LOG,
                    evidence_ids=[ev.id],
                    severity="CRITICAL"
                ))
        
        # Current incident state
        events.append(TimelineEvent(
            timestamp=datetime.utcnow(),
            event_type="CURRENT_STATE",
            title="Current Incident State",
            description=f"Incident {incident.id} under investigation",
            source_type=SourceType.RUNTIME,
            severity="INFO"
        ))
        
        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)
        
        logger.info("timeline_built", incident_id=incident.id, events=len(events))
        return events


def format_timeline_for_display(events: List[TimelineEvent]) -> List[Dict[str, Any]]:
    """Format timeline events for UI display."""
    return [
        {
            "timestamp": e.timestamp.isoformat(),
            "event_type": e.event_type,
            "title": e.title,
            "description": e.description,
            "source_type": e.source_type.value,
            "evidence_ids": e.evidence_ids,
            "severity": e.severity
        }
        for e in events
    ]