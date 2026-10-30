"""Timeline builder for incident timeline construction.

Handles missing timestamps, unsorted events, duplicate timestamps, and missing raw data.
Produces structured events representing:
healthy → change → anomaly → escalation → incident → investigation → recovery.
"""
from datetime import datetime, timedelta, timezone
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

    def build(self, incident: Optional[Incident], evidence: Optional[List[Evidence]]) -> List[TimelineEvent]:
        """Build chronological timeline with robustness against None/missing/unsorted data."""
        if incident is None:
            return []

        evidence = evidence or []
        events: List[TimelineEvent] = []

        now = datetime.now(timezone.utc)
        base_time = incident.created_at if incident.created_at else now
        if base_time.tzinfo is None:
            base_time = base_time.replace(tzinfo=timezone.utc)

        # 1. HEALTHY: Pre-incident healthy baseline (10 mins before incident or deploy)
        healthy_time = base_time - timedelta(minutes=10)
        events.append(TimelineEvent(
            timestamp=healthy_time,
            event_type="HEALTHY",
            title="System Operational (Baseline)",
            description=f"Service {incident.service} operating within normal thresholds prior to incident.",
            source_type=SourceType.RUNTIME,
            severity="LOW"
        ))

        # 2. CHANGE: Deployments
        deployment_evidence = [e for e in evidence if e and e.source_type == SourceType.DEPLOYMENT]
        for ev in deployment_evidence:
            raw_data = ev.raw_data or {}
            ev_time = ev.timestamp if ev.timestamp else (base_time - timedelta(minutes=5))
            if ev_time.tzinfo is None:
                ev_time = ev_time.replace(tzinfo=timezone.utc)
            events.append(TimelineEvent(
                timestamp=ev_time,
                event_type="DEPLOYMENT",
                title=f"Deployment {raw_data.get('version', 'new version')}",
                description=ev.claim or "Deployment detected",
                source_type=SourceType.DEPLOYMENT,
                evidence_ids=[ev.id] if ev.id else [],
                severity="MEDIUM"
            ))

        # 2b. CHANGE: Config Changes
        config_evidence = [e for e in evidence if e and e.source_type == SourceType.CONFIG]
        for ev in config_evidence:
            ev_time = ev.timestamp if ev.timestamp else (base_time - timedelta(minutes=4))
            if ev_time.tzinfo is None:
                ev_time = ev_time.replace(tzinfo=timezone.utc)
            events.append(TimelineEvent(
                timestamp=ev_time,
                event_type="CONFIG_CHANGE",
                title="Configuration Applied",
                description=ev.claim or "Configuration parameters recorded",
                source_type=SourceType.CONFIG,
                evidence_ids=[ev.id] if ev.id else [],
                severity="MEDIUM"
            ))

        # 3. ANOMALY: First anomalies from logs
        log_evidence = [e for e in evidence if e and e.source_type == SourceType.LOG]
        anomaly_seen = False
        for ev in log_evidence:
            claim_lower = (ev.claim or "").lower()
            if any(term in claim_lower for term in ("error", "timeout", "pool", "fail", "slow", "500")):
                ev_time = ev.timestamp if ev.timestamp else (base_time - timedelta(minutes=2))
                if ev_time.tzinfo is None:
                    ev_time = ev_time.replace(tzinfo=timezone.utc)
                events.append(TimelineEvent(
                    timestamp=ev_time,
                    event_type="FIRST_ANOMALY",
                    title="First Anomaly Detected",
                    description=ev.claim,
                    source_type=SourceType.LOG,
                    evidence_ids=[ev.id] if ev.id else [],
                    severity="HIGH"
                ))
                anomaly_seen = True
                break

        # 4. ESCALATION: Repeated failures / exhaustion
        for ev in log_evidence:
            claim_lower = (ev.claim or "").lower()
            if any(term in claim_lower for term in ("exhaust", "5xx", "saturation", "cascade")):
                ev_time = ev.timestamp if ev.timestamp else (base_time - timedelta(minutes=1))
                if ev_time.tzinfo is None:
                    ev_time = ev_time.replace(tzinfo=timezone.utc)
                events.append(TimelineEvent(
                    timestamp=ev_time,
                    event_type="ERROR_ESCALATION",
                    title="Error Rate Escalation",
                    description=ev.claim,
                    source_type=SourceType.LOG,
                    evidence_ids=[ev.id] if ev.id else [],
                    severity="CRITICAL"
                ))

        # 5. INCIDENT: Incident reported / intake
        events.append(TimelineEvent(
            timestamp=base_time,
            event_type="INCIDENT_REPORTED",
            title=f"Incident {incident.id} Declared",
            description=incident.description or "Incident reported",
            source_type=SourceType.RUNTIME,
            severity="HIGH"
        ))

        # 6. INVESTIGATION: Investigation initiated
        investigation_time = base_time + timedelta(seconds=15)
        events.append(TimelineEvent(
            timestamp=investigation_time,
            event_type="INVESTIGATION_STARTED",
            title="Autonomous Investigation Initiated",
            description="COSKA agent began evidence gathering and timeline correlation.",
            source_type=SourceType.RUNTIME,
            severity="INFO"
        ))

        # 7. CURRENT STATE / RECOVERY
        events.append(TimelineEvent(
            timestamp=now,
            event_type="CURRENT_STATE",
            title="Investigation & Recovery Phase",
            description=f"Status: {incident.status.value if hasattr(incident.status, 'value') else str(incident.status)}",
            source_type=SourceType.RUNTIME,
            severity="INFO"
        ))

        # De-duplicate timestamps by adding stable microsecond offsets
        # and sort chronologically
        events.sort(key=lambda e: (e.timestamp, e.event_type))
        for idx in range(1, len(events)):
            if events[idx].timestamp <= events[idx - 1].timestamp:
                events[idx].timestamp = events[idx - 1].timestamp + timedelta(microseconds=1000)

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
            "source_type": e.source_type.value if hasattr(e.source_type, "value") else str(e.source_type),
            "evidence_ids": e.evidence_ids,
            "severity": e.severity
        }
        for e in events
    ]
