"""COSKA data models."""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentStatus(str, Enum):
    RECEIVED = "RECEIVED"
    TRIAGING = "TRIAGING"
    COLLECTING_EVIDENCE = "COLLECTING_EVIDENCE"
    BUILDING_TIMELINE = "BUILDING_TIMELINE"
    GENERATING_HYPOTHESES = "GENERATING_HYPOTHESES"
    INVESTIGATING = "INVESTIGATING"
    RESEARCHING = "RESEARCHING"
    ROOT_CAUSE_IDENTIFIED = "ROOT_CAUSE_IDENTIFIED"
    REMEDIATION_PROPOSED = "REMEDIATION_PROPOSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPLYING_FIX = "APPLYING_FIX"
    VERIFYING = "VERIFYING"
    RESOLVED = "RESOLVED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INVESTIGATION_BLOCKED = "INVESTIGATION_BLOCKED"
    REMEDIATION_FAILED = "REMEDIATION_FAILED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class SourceType(str, Enum):
    LOG = "LOG"
    REPOSITORY = "REPOSITORY"
    CONFIG = "CONFIG"
    DEPLOYMENT = "DEPLOYMENT"
    RUNTIME = "RUNTIME"
    WEB = "WEB"
    TEST = "TEST"
    RAG = "RAG"


class HypothesisStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WEAKENED = "WEAKENED"
    REJECTED = "REJECTED"
    SUPPORTED = "SUPPORTED"


class Verdict(str, Enum):
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    UNVERIFIED = "UNVERIFIED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: f"INC-{uuid.uuid4().hex[:8].upper()}")
    service: str
    severity: Severity
    description: str
    logs: Optional[str] = None
    deployment: Optional[str] = None
    repository: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: IncidentStatus = IncidentStatus.RECEIVED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: f"E-{uuid.uuid4().hex[:6].upper()}")
    incident_id: str
    source_type: SourceType
    claim: str
    reference: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    related_component: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class Hypothesis(BaseModel):
    id: str = Field(default_factory=lambda: f"H-{uuid.uuid4().hex[:6].upper()}")
    incident_id: str
    title: str
    description: str
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradicting_evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    next_investigation_action: Optional[str] = None
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RemediationType(str, Enum):
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    CODE_CHANGE = "CODE_CHANGE"
    DEPENDENCY_CHANGE = "DEPENDENCY_CHANGE"
    SAFE_ROLLBACK = "SAFE_ROLLBACK"
    FEATURE_FLAG_CHANGE = "FEATURE_FLAG_CHANGE"


class Remediation(BaseModel):
    id: str = Field(default_factory=lambda: f"R-{uuid.uuid4().hex[:6].upper()}")
    incident_id: str
    hypothesis_id: str
    type: RemediationType
    description: str
    exact_change: str
    expected_effect: str
    risk: str = "LOW"
    blast_radius: str = "SANDBOX_ONLY"
    rollback_plan: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VerificationStage(str, Enum):
    BASELINE = "BASELINE"
    POST_FIX = "POST_FIX"
    CONTROL = "CONTROL"


class VerificationResult(BaseModel):
    id: str = Field(default_factory=lambda: f"V-{uuid.uuid4().hex[:6].upper()}")
    incident_id: str
    remediation_id: str
    baseline_test: str = "NOT_RUN"
    post_fix_tests: str = "NOT_RUN"
    health_check: str = "NOT_RUN"
    control_test: str = "NOT_RUN"
    verdict: Verdict = Verdict.UNVERIFIED
    evidence_count: int = 0
    model: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentAction(BaseModel):
    id: str = Field(default_factory=lambda: f"A-{uuid.uuid4().hex[:6].upper()}")
    incident_id: str
    step: str
    tool: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: int = 0
    status: str = "STARTED"
    summary: str = ""
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class InvestigationPhase(str, Enum):
    INCIDENT_INTAKE = "INCIDENT_INTAKE"
    EVIDENCE_COLLECTION = "EVIDENCE_COLLECTION"
    TIMELINE_BUILD = "TIMELINE_BUILD"
    HYPOTHESIS_GENERATION = "HYPOTHESIS_GENERATION"
    INVESTIGATION = "INVESTIGATION"
    ROOT_CAUSE = "ROOT_CAUSE"
    REMEDIATION = "REMEDIATION"
    VERIFICATION = "VERIFICATION"


class InvestigationStateModel(BaseModel):
    run_id: str = Field(default_factory=lambda: f"RUN-{uuid.uuid4().hex[:8].upper()}")
    incident_id: str
    current_phase: InvestigationPhase = InvestigationPhase.INCIDENT_INTAKE
    incident: Incident
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    web_sources: List[Dict[str, Any]] = Field(default_factory=list)
    knowledge_docs: List[Dict[str, Any]] = Field(default_factory=list)
    root_cause: Optional[Dict[str, Any]] = None
    remediation: Optional[Remediation] = None
    sandbox_result: Optional[Dict[str, Any]] = None
    test_results: Optional[Dict[str, Any]] = None
    verification_result: Optional[VerificationResult] = None
    errors: List[str] = Field(default_factory=list)
    actions: List[AgentAction] = Field(default_factory=list)
    original_config: str = ""
    config_file: str = ".env"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
