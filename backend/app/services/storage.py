"""Storage service for persisting incidents and investigations."""
import json
import sqlite3
from typing import List, Optional, Dict, Any
from pathlib import Path
from contextlib import contextmanager
import structlog

from app.models import Incident, Evidence, Hypothesis, Remediation, VerificationResult, AgentAction
from app.config import get_settings

logger = structlog.get_logger()


class StorageService:
    """SQLite-based storage for COSKA data."""
    
    def __init__(self):
        self.settings = get_settings()
        self.db_path = self.settings.database_url.replace("sqlite:///", "")
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    service TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    logs TEXT,
                    deployment TEXT,
                    repository TEXT,
                    metadata TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    reference TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    related_component TEXT,
                    raw_data TEXT,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                );
                
                CREATE TABLE IF NOT EXISTS hypotheses (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    supporting_evidence_ids TEXT NOT NULL,
                    contradicting_evidence_ids TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    next_investigation_action TEXT,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                );
                
                CREATE TABLE IF NOT EXISTS remediations (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    hypothesis_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    exact_change TEXT NOT NULL,
                    expected_effect TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    blast_radius TEXT NOT NULL,
                    rollback_plan TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                );
                
                CREATE TABLE IF NOT EXISTS verification_runs (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    remediation_id TEXT NOT NULL,
                    baseline_test TEXT NOT NULL,
                    post_fix_tests TEXT NOT NULL,
                    health_check TEXT NOT NULL,
                    control_test TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    evidence_count INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                );
                
                CREATE TABLE IF NOT EXISTS agent_actions (
                    id TEXT PRIMARY KEY,
                    incident_id TEXT NOT NULL,
                    step TEXT NOT NULL,
                    tool TEXT,
                    timestamp TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    input_data TEXT,
                    output_data TEXT,
                    error TEXT,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                );
                
                CREATE TABLE IF NOT EXISTS incident_memory (
                    id TEXT PRIMARY KEY,
                    service TEXT NOT NULL,
                    symptoms TEXT NOT NULL,
                    root_cause TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    remediation TEXT NOT NULL,
                    verification_result TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                
                CREATE INDEX IF NOT EXISTS idx_evidence_incident ON evidence(incident_id);
                CREATE INDEX IF NOT EXISTS idx_hypotheses_incident ON hypotheses(incident_id);
                CREATE INDEX IF NOT EXISTS idx_actions_incident ON agent_actions(incident_id);
            """)
    
    @contextmanager
    def _conn(self):
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    # Incident operations
    def save_incident(self, incident: Incident) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO incidents 
                (id, service, severity, description, logs, deployment, repository, metadata, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident.id, incident.service, incident.severity.value,
                incident.description, incident.logs, incident.deployment,
                incident.repository, json.dumps(incident.metadata),
                incident.status.value, incident.created_at.isoformat(),
                incident.updated_at.isoformat()
            ))
    
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if not row:
                return None
            return Incident(
                id=row["id"],
                service=row["service"],
                severity=row["severity"],
                description=row["description"],
                logs=row["logs"],
                deployment=row["deployment"],
                repository=row["repository"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                status=row["status"],
                created_at=row["created_at"],
                updated_at=row["updated_at"]
            )
    
    def list_incidents(self) -> List[Incident]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()
            return [Incident(
                id=r["id"], service=r["service"], severity=r["severity"],
                description=r["description"], logs=r["logs"],
                deployment=r["deployment"], repository=r["repository"],
                metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                status=r["status"], created_at=r["created_at"], updated_at=r["updated_at"]
            ) for r in rows]
    
    # Evidence operations
    def save_evidence(self, evidence: List[Evidence]) -> None:
        with self._conn() as conn:
            for e in evidence:
                conn.execute("""
                    INSERT OR REPLACE INTO evidence
                    (id, incident_id, source_type, claim, reference, timestamp, confidence, related_component, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    e.id, e.incident_id, e.source_type.value, e.claim, e.reference,
                    e.timestamp.isoformat(), e.confidence, e.related_component,
                    json.dumps(e.raw_data) if e.raw_data else None
                ))
    
    def get_evidence(self, incident_id: str) -> List[Evidence]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM evidence WHERE incident_id = ?", (incident_id,)).fetchall()
            return [Evidence(
                id=r["id"], incident_id=r["incident_id"], source_type=r["source_type"],
                claim=r["claim"], reference=r["reference"], timestamp=r["timestamp"],
                confidence=r["confidence"], related_component=r["related_component"],
                raw_data=json.loads(r["raw_data"]) if r["raw_data"] else None
            ) for r in rows]
    
    # Hypothesis operations
    def save_hypotheses(self, hypotheses: List[Hypothesis]) -> None:
        with self._conn() as conn:
            for h in hypotheses:
                conn.execute("""
                    INSERT OR REPLACE INTO hypotheses
                    (id, incident_id, title, description, supporting_evidence_ids, contradicting_evidence_ids,
                     confidence, next_investigation_action, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    h.id, h.incident_id, h.title, h.description,
                    json.dumps(h.supporting_evidence_ids), json.dumps(h.contradicting_evidence_ids),
                    h.confidence, h.next_investigation_action, h.status.value,
                    h.created_at.isoformat(), h.updated_at.isoformat()
                ))
    
    def get_hypotheses(self, incident_id: str) -> List[Hypothesis]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM hypotheses WHERE incident_id = ?", (incident_id,)).fetchall()
            return [Hypothesis(
                id=r["id"], incident_id=r["incident_id"], title=r["title"],
                description=r["description"],
                supporting_evidence_ids=json.loads(r["supporting_evidence_ids"]),
                contradicting_evidence_ids=json.loads(r["contradicting_evidence_ids"]),
                confidence=r["confidence"], next_investigation_action=r["next_investigation_action"],
                status=r["status"], created_at=r["created_at"], updated_at=r["updated_at"]
            ) for r in rows]
    
    # Remediation operations
    def save_remediation(self, remediation: Remediation) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO remediations
                (id, incident_id, hypothesis_id, type, description, exact_change,
                 expected_effect, risk, blast_radius, rollback_plan, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                remediation.id, remediation.incident_id, remediation.hypothesis_id,
                remediation.type.value, remediation.description, remediation.exact_change,
                remediation.expected_effect, remediation.risk, remediation.blast_radius,
                remediation.rollback_plan, remediation.created_at.isoformat()
            ))
    
    def get_remediation(self, incident_id: str) -> Optional[Remediation]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM remediations WHERE incident_id = ?", (incident_id,)).fetchone()
            if not row:
                return None
            return Remediation(
                id=row["id"], incident_id=row["incident_id"], hypothesis_id=row["hypothesis_id"],
                type=row["type"], description=row["description"], exact_change=row["exact_change"],
                expected_effect=row["expected_effect"], risk=row["risk"],
                blast_radius=row["blast_radius"], rollback_plan=row["rollback_plan"],
                created_at=row["created_at"]
            )
    
    # Verification operations
    def save_verification(self, verification: VerificationResult) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO verification_runs
                (id, incident_id, remediation_id, baseline_test, post_fix_tests,
                 health_check, control_test, verdict, evidence_count, model, details, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                verification.id, verification.incident_id, verification.remediation_id,
                verification.baseline_test, verification.post_fix_tests,
                verification.health_check, verification.control_test,
                verification.verdict.value, verification.evidence_count,
                verification.model, json.dumps(verification.details),
                verification.created_at.isoformat()
            ))
    
    def get_verification(self, incident_id: str) -> Optional[VerificationResult]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM verification_runs WHERE incident_id = ? ORDER BY created_at DESC LIMIT 1", (incident_id,)).fetchone()
            if not row:
                return None
            return VerificationResult(
                id=row["id"], incident_id=row["incident_id"], remediation_id=row["remediation_id"],
                baseline_test=row["baseline_test"], post_fix_tests=row["post_fix_tests"],
                health_check=row["health_check"], control_test=row["control_test"],
                verdict=row["verdict"], evidence_count=row["evidence_count"],
                model=row["model"], details=json.loads(row["details"]),
                created_at=row["created_at"]
            )
    
    # Agent action operations
    def save_actions(self, actions: List[AgentAction]) -> None:
        with self._conn() as conn:
            for a in actions:
                conn.execute("""
                    INSERT OR REPLACE INTO agent_actions
                    (id, incident_id, step, tool, timestamp, duration_ms, status,
                     summary, input_data, output_data, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    a.id, a.incident_id, a.step, a.tool, a.timestamp.isoformat(),
                    a.duration_ms, a.status, a.summary,
                    json.dumps(a.input_data), json.dumps(a.output_data), a.error
                ))
    
    def get_actions(self, incident_id: str) -> List[AgentAction]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM agent_actions WHERE incident_id = ? ORDER BY timestamp", (incident_id,)).fetchall()
            return [AgentAction(
                id=r["id"], incident_id=r["incident_id"], step=r["step"], tool=r["tool"],
                timestamp=r["timestamp"], duration_ms=r["duration_ms"], status=r["status"],
                summary=r["summary"], input_data=json.loads(r["input_data"]),
                output_data=json.loads(r["output_data"]), error=r["error"]
            ) for r in rows]
    
    # Incident memory
    def save_incident_memory(
        self, service: str, symptoms: str, root_cause: str,
        evidence: List[Dict], remediation: Dict, verification: Dict
    ) -> None:
        with self._conn() as conn:
            conn.execute("""
                INSERT INTO incident_memory
                (id, service, symptoms, root_cause, evidence, remediation, verification_result, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"MEM-{__import__('uuid').uuid4().hex[:8].upper()}",
                service, symptoms, root_cause,
                json.dumps(evidence), json.dumps(remediation), json.dumps(verification),
                __import__('datetime').datetime.utcnow().isoformat()
            ))
    
    def search_incident_memory(self, service: str, symptoms: str) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute("""
                SELECT * FROM incident_memory 
                WHERE service = ? AND symptoms LIKE ?
                ORDER BY created_at DESC LIMIT 5
            """, (service, f"%{symptoms}%")).fetchall()
            return [dict(r) for r in rows]


# Singleton
_storage: Optional[StorageService] = None


def get_storage() -> StorageService:
    global _storage
    if _storage is None:
        _storage = StorageService()
    return _storage