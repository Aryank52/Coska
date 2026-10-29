#!/usr/bin/env python
"""
Unit tests for COSKA core components.
Run with: pytest tests/ -v
"""
import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Test models
from app.models import (
    Incident, Evidence, Hypothesis, Remediation, 
    VerificationResult, AgentAction, Severity, 
    IncidentStatus, SourceType, HypothesisStatus, 
    Verdict, RemediationType
)


class TestModels:
    """Test Pydantic models."""
    
    def test_incident_creation(self):
        """Test incident creation with all fields."""
        incident = Incident(
            service="payment-api",
            severity=Severity.CRITICAL,
            description="Test incident",
            logs="error logs",
            deployment="v1.0.0",
            repository="https://github.com/test/repo",
            metadata={"key": "value"}
        )
        
        assert incident.id.startswith("INC-")
        assert incident.service == "payment-api"
        assert incident.severity == Severity.CRITICAL
        assert incident.status == IncidentStatus.RECEIVED
        assert incident.metadata["key"] == "value"
    
    def test_evidence_creation(self):
        """Test evidence creation."""
        evidence = Evidence(
            incident_id="INC-123",
            source_type=SourceType.LOG,
            claim="Database connection timeout",
            reference="log line 42",
            confidence=0.9,
            related_component="database"
        )
        
        assert evidence.id.startswith("E-")
        assert evidence.source_type == SourceType.LOG
        assert evidence.confidence == 0.9
    
    def test_hypothesis_creation(self):
        """Test hypothesis creation."""
        hypothesis = Hypothesis(
            incident_id="INC-123",
            title="Database pool exhaustion",
            description="Pool size too small",
            supporting_evidence_ids=["E-1", "E-2"],
            confidence=0.85,
            status=HypothesisStatus.ACTIVE
        )
        
        assert hypothesis.id.startswith("H-")
        assert hypothesis.title == "Database pool exhaustion"
        assert hypothesis.confidence == 0.85
        assert hypothesis.status == HypothesisStatus.ACTIVE
    
    def test_remediation_creation(self):
        """Test remediation creation."""
        remediation = Remediation(
            incident_id="INC-123",
            hypothesis_id="H-1",
            type=RemediationType.CONFIGURATION_CHANGE,
            description="Increase pool size",
            exact_change="DB_POOL_SIZE: 5 -> 30",
            expected_effect="Fix pool exhaustion",
            risk="LOW",
            blast_radius="SANDBOX_ONLY",
            rollback_plan="Revert to 5"
        )
        
        assert remediation.id.startswith("R-")
        assert remediation.type == RemediationType.CONFIGURATION_CHANGE
        assert remediation.exact_change == "DB_POOL_SIZE: 5 -> 30"
    
    def test_verification_result_creation(self):
        """Test verification result creation."""
        vr = VerificationResult(
            incident_id="INC-123",
            remediation_id="R-1",
            baseline_test="FAILED",
            post_fix_tests="PASSED",
            health_check="PASSED",
            control_test="FAILED",
            verdict=Verdict.VERIFIED,
            evidence_count=5,
            model="nvidia/nemotron-3-ultra-550b-a55b"
        )
        
        assert vr.id.startswith("V-")
        assert vr.verdict == Verdict.VERIFIED
    
    def test_agent_action_creation(self):
        """Test agent action creation."""
        action = AgentAction(
            incident_id="INC-123",
            step="COLLECT_EVIDENCE",
            tool="evidence_engine",
            summary="Collected 5 evidence items",
            status="COMPLETED",
            duration_ms=1500
        )
        
        assert action.id.startswith("A-")
        assert action.step == "COLLECT_EVIDENCE"
        assert action.duration_ms == 1500
    
    def test_invalid_severity(self):
        """Test that invalid severity raises error."""
        with pytest.raises(ValidationError):
            Incident(
                service="test",
                severity="INVALID",
                description="test"
            )
    
    def test_confidence_bounds(self):
        """Test confidence must be between 0 and 1."""
        with pytest.raises(ValidationError):
            Evidence(
                incident_id="INC-123",
                source_type=SourceType.LOG,
                claim="test",
                reference="ref",
                confidence=1.5  # Invalid > 1
            )
        
        with pytest.raises(ValidationError):
            Evidence(
                incident_id="INC-123",
                source_type=SourceType.LOG,
                claim="test",
                reference="ref",
                confidence=-0.1  # Invalid < 0
            )


# Test evidence engine
from app.agent.evidence import LogAnalyzer, ConfigAnalyzer, DeploymentAnalyzer, EvidenceEngine
from app.models import Incident


class TestEvidenceEngine:
    """Test evidence extraction."""
    
    def test_log_analyzer(self):
        """Test log analysis."""
        logs = """2026-10-29T10:15:23.456Z ERROR payment-api: connection pool exhausted
2026-10-29T10:15:24.123Z ERROR payment-api: timeout waiting for database connection
2026-10-29T10:15:24.789Z ERROR payment-api: connection pool exhausted"""
        
        incident = Incident(
            id="TEST-1",
            service="payment-api",
            severity="CRITICAL",
            description="Test",
            logs=logs
        )
        
        analyzer = LogAnalyzer()
        evidence = analyzer.analyze(logs, "TEST-1")
        
        assert len(evidence) >= 3  # timestamps, errors, pool exhaustion
        pool_evidence = [e for e in evidence if "pool" in e.claim.lower()]
        assert len(pool_evidence) >= 1
    
    def test_config_analyzer(self):
        """Test configuration analysis."""
        config = "DB_POOL_SIZE=5\nMAX_CONNECTIONS=100\nTIMEOUT=30"
        
        incident = Incident(
            id="TEST-1",
            service="payment-api",
            severity="CRITICAL",
            description="Test",
            metadata={"configuration": config}
        )
        
        analyzer = ConfigAnalyzer()
        evidence = analyzer.analyze(config, "TEST-1")
        
        pool_evidence = [e for e in evidence if "pool" in e.claim.lower()]
        assert len(pool_evidence) == 1
        assert pool_evidence[0].raw_data["pool_size"] == 5
    
    def test_deployment_analyzer(self):
        """Test deployment analysis."""
        deployment = "payment-api v1.8.2 deployed at 2026-10-29T10:10:00Z"
        
        analyzer = DeploymentAnalyzer()
        evidence = analyzer.analyze(deployment, "TEST-1")
        
        version_evidence = [e for e in evidence if "version" in e.raw_data]
        assert len(version_evidence) == 1
        assert version_evidence[0].raw_data["version"] == "1.8.2"


# Test timeline builder
from app.agent.timeline import TimelineBuilder, format_timeline_for_display


class TestTimelineBuilder:
    """Test timeline construction."""
    
    def test_timeline_build(self):
        """Test timeline building."""
        incident = Incident(
            id="TEST-1",
            service="payment-api",
            severity="CRITICAL",
            description="Test incident",
            deployment="payment-api v1.8.2 deployed at 2026-10-29T10:10:00Z"
        )
        
        # Add deployment evidence to trigger deployment event
        from app.models import Evidence, SourceType
        evidence = [
            Evidence(
                incident_id="TEST-1",
                source_type=SourceType.DEPLOYMENT,
                claim="Deployment v1.8.2",
                reference="deployment metadata",
                confidence=0.9,
                raw_data={"version": "1.8.2"}
            )
        ]
        builder = TimelineBuilder()
        events = builder.build(incident, evidence)
        
        formatted = format_timeline_for_display(events)
        assert len(formatted) >= 3  # Incident reported, deployment, current state
        
        event_types = [e["event_type"] for e in formatted]
        assert "INCIDENT_REPORTED" in event_types
        assert "DEPLOYMENT" in event_types
        assert "CURRENT_STATE" in event_types


# Test hypothesis engine
from app.agent.hypotheses import HypothesisEngine


class TestHypothesisEngine:
    """Test hypothesis generation."""
    
    def test_initial_hypotheses(self):
        """Test initial hypothesis generation."""
        incident = Incident(
            id="TEST-1",
            service="payment-api",
            severity="CRITICAL",
            description="Database timeout errors",
            logs="connection pool exhausted timeout waiting for connection",
            metadata={"configuration": "DB_POOL_SIZE=5"}
        )
        
        # Add evidence that would be extracted by evidence engine
        from app.models import Evidence, SourceType
        evidence = [
            Evidence(
                incident_id="TEST-1",
                source_type=SourceType.LOG,
                claim="connection pool exhausted",
                reference="logs",
                confidence=0.9
            ),
            Evidence(
                incident_id="TEST-1",
                source_type=SourceType.CONFIG,
                claim="DB_POOL_SIZE=5",
                reference="config",
                confidence=1.0
            )
        ]
        
        engine = HypothesisEngine()
        hypotheses = engine.generate_initial_hypotheses(incident, evidence)
        
        assert len(hypotheses) >= 1
        # Should detect pool exhaustion
        pool_hyp = [h for h in hypotheses if "pool" in h.title.lower()]
        assert len(pool_hyp) >= 1


# Test remediation validation
from app.agent.remediation import RemediationEngine
from app.models import Remediation, RemediationType


class TestRemediationEngine:
    """Test remediation validation."""
    
    def test_valid_config_change(self):
        """Test valid configuration change validation."""
        engine = RemediationEngine()
        
        remediation = Remediation(
            incident_id="INC-1",
            hypothesis_id="H-1",
            type=RemediationType.CONFIGURATION_CHANGE,
            description="Increase pool size",
            exact_change="DB_POOL_SIZE: 5 -> 30",
            expected_effect="Fix pool exhaustion",
            risk="LOW",
            blast_radius="SANDBOX_ONLY",
            rollback_plan="Revert to 5"
        )
        
        validation = engine.validate_remediation(remediation)
        assert validation["valid"] == True
        assert len(validation["errors"]) == 0
    
    def test_invalid_format(self):
        """Test invalid change format."""
        engine = RemediationEngine()
        
        remediation = Remediation(
            incident_id="INC-1",
            hypothesis_id="H-1",
            type=RemediationType.CONFIGURATION_CHANGE,
            description="Bad format",
            exact_change="DB_POOL_SIZE 5 30",  # Missing colon and arrow
            expected_effect="Fix",
            risk="LOW",
            blast_radius="SANDBOX_ONLY",
            rollback_plan="Revert"
        )
        
        validation = engine.validate_remediation(remediation)
        assert validation["valid"] == False
        assert any("format" in e.lower() for e in validation["errors"])
    
    def test_out_of_range(self):
        """Test value out of allowed range."""
        engine = RemediationEngine()
        
        remediation = Remediation(
            incident_id="INC-1",
            hypothesis_id="H-1",
            type=RemediationType.CONFIGURATION_CHANGE,
            description="Too high",
            exact_change="DB_POOL_SIZE: 5 -> 200",  # Max is 100
            expected_effect="Fix",
            risk="LOW",
            blast_radius="SANDBOX_ONLY",
            rollback_plan="Revert"
        )
        
        validation = engine.validate_remediation(remediation)
        assert validation["valid"] == False
        assert any("range" in e.lower() for e in validation["errors"])


# Test verification logic
from app.agent.verifier import Verifier
from app.tools.sandbox import SandboxResult


class TestVerifier:
    """Test verification logic."""
    
    def test_verified(self):
        """Test VERIFIED verdict."""
        verifier = Verifier(None, "", "test-model")
        
        baseline = SandboxResult(False, "", "", 1, 0, [])
        post_fix = SandboxResult(True, "", "", 0, 0, [])
        health = SandboxResult(True, "", "", 0, 0, [])
        control = SandboxResult(False, "", "", 1, 0, [])
        
        verdict = verifier._determine_verdict(baseline, post_fix, health, control)
        assert verdict.value == "VERIFIED"
    
    def test_unverified_baseline_passed(self):
        """Test UNVERIFIED when baseline passes."""
        verifier = Verifier(None, "", "test-model")
        
        baseline = SandboxResult(True, "", "", 0, 0, [])
        post_fix = SandboxResult(True, "", "", 0, 0, [])
        health = SandboxResult(True, "", "", 0, 0, [])
        control = SandboxResult(False, "", "", 1, 0, [])
        
        verdict = verifier._determine_verdict(baseline, post_fix, health, control)
        assert verdict.value == "UNVERIFIED"
    
    def test_failed_fix(self):
        """Test FAILED when fix doesn't work."""
        verifier = Verifier(None, "", "test-model")
        
        baseline = SandboxResult(False, "", "", 1, 0, [])
        post_fix = SandboxResult(False, "", "", 1, 0, [])
        health = SandboxResult(True, "", "", 0, 0, [])
        control = SandboxResult(False, "", "", 1, 0, [])
        
        verdict = verifier._determine_verdict(baseline, post_fix, health, control)
        assert verdict.value == "FAILED"


# Test tool registry
from app.tools.registry import ToolRegistry, BaseTool, ToolInput, ToolOutput, ToolResult


class DummyTool(BaseTool):
    name = "dummy"
    description = "Dummy tool for testing"
    
    class DummyInput(ToolInput):
        value: str
    
    class DummyOutput(ToolOutput):
        result: str
    
    input_model = DummyInput
    output_model = DummyOutput
    
    async def execute(self, input_data: DummyInput) -> ToolResult:
        return ToolResult(success=True, data={"result": f"processed: {input_data.value}"})


class TestToolRegistry:
    """Test tool registry."""
    
    @pytest.mark.asyncio
    async def test_register_and_execute(self):
        registry = ToolRegistry()
        registry.register(DummyTool())
        
        assert "dummy" in registry._tools
        
        result = await registry.execute("dummy", {"value": "test"})
        assert result.success == True
        assert result.data["result"] == "processed: test"
    
    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        registry = ToolRegistry()
        result = await registry.execute("nonexistent", {})
        assert result.success == False
        assert "not found" in result.error


# Test sandbox result
from app.tools.sandbox import SandboxResult


class TestSandboxResult:
    """Test sandbox result dataclass."""
    
    def test_success_result(self):
        result = SandboxResult(
            success=True,
            stdout="tests passed",
            stderr="",
            exit_code=0,
            duration_ms=1000,
            files_changed=["test.py"]
        )
        
        assert result.success == True
        assert result.exit_code == 0
        assert "passed" in result.stdout
    
    def test_failure_result(self):
        result = SandboxResult(
            success=False,
            stdout="",
            stderr="test failed",
            exit_code=1,
            duration_ms=500,
            files_changed=[]
        )
        
        assert result.success == False
        assert result.exit_code == 1
        assert "failed" in result.stderr


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])