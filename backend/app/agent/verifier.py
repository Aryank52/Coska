"""Verifier for three-stage verification."""
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import structlog

from app.models import Verdict, Incident, Remediation, Evidence
from app.tools.sandbox import SandboxEngine, SandboxResult

logger = structlog.get_logger()


@dataclass
class VerificationReport:
    """Complete verification report."""
    incident_id: str
    remediation_id: str
    baseline_test: SandboxResult
    post_fix_tests: SandboxResult
    health_check: SandboxResult
    control_test: SandboxResult
    verdict: Verdict
    evidence_count: int
    model: str
    details: Dict[str, Any]


class Verifier:
    """Three-stage verification engine."""
    
    def __init__(self, sandbox: SandboxEngine, repo_path: str, model: str):
        self.sandbox = sandbox
        self.repo_path = repo_path
        self.model = model
    
    async def verify(
        self,
        incident: Incident,
        remediation: Remediation,
        evidence: List[Evidence],
        original_config: str = "",
        config_file: str = ".env",
        test_command: str = "pytest -v",
        health_command: str = "python -c \"import httpx; httpx.get('http://localhost:8000/health', timeout=5)\""
    ) -> VerificationReport:
        """Run complete three-stage verification."""
        
        logger.info("verification_started", incident_id=incident.id, remediation_id=remediation.id)
        
        # STAGE 1: BASELINE - Run with original config (should FAIL)
        logger.info("stage1_baseline_started", incident_id=incident.id)
        if original_config:
            # Temporarily revert to original config
            config_path = os.path.join(self.repo_path, config_file)
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    current_config = f.read()
                with open(config_path, 'w') as f:
                    f.write(original_config)
                
                baseline = await self.sandbox.run_tests(self.repo_path, test_command)
                
                # Restore current config
                with open(config_path, 'w') as f:
                    f.write(current_config)
            else:
                baseline = SandboxResult(
                    success=False,
                    stdout="",
                    stderr="Config file not found for baseline",
                    exit_code=-1,
                    duration_ms=0,
                    files_changed=[]
                )
        else:
            baseline = await self.sandbox.run_tests(self.repo_path, test_command)
        
        logger.info("stage1_baseline_complete", incident_id=incident.id, passed=baseline.success)
        
        # STAGE 2: POST-FIX - Apply remediation and test (should PASS)
        logger.info("stage2_post_fix_started", incident_id=incident.id)
        
        # Apply remediation
        if remediation.type.value == "CONFIGURATION_CHANGE":
            apply_result = await self.sandbox.apply_config_change(
                self.repo_path, remediation.exact_change, config_file
            )
            if not apply_result.success:
                logger.error("remediation_apply_failed", incident_id=incident.id)
                return VerificationReport(
                    incident_id=incident.id,
                    remediation_id=remediation.id,
                    baseline_test=baseline,
                    post_fix_tests=apply_result,
                    health_check=SandboxResult(False, "", "Remediation apply failed", -1, 0, []),
                    control_test=SandboxResult(False, "", "Remediation apply failed", -1, 0, []),
                    verdict=Verdict.FAILED,
                    evidence_count=len(evidence),
                    model=self.model,
                    details={"error": "Failed to apply remediation"}
                )
        
        # Run tests
        post_fix = await self.sandbox.run_tests(self.repo_path, test_command)
        
        # Run health check
        health = await self.sandbox.run_health_check(self.repo_path, health_command)
        
        logger.info("stage2_post_fix_complete", incident_id=incident.id, tests_passed=post_fix.success, health_passed=health.success)
        
        # STAGE 3: CONTROL - Revert and verify failure returns
        logger.info("stage3_control_started", incident_id=incident.id)
        
        if original_config:
            control = await self.sandbox.run_control_verification(
                self.repo_path, original_config, config_file, test_command
            )
        else:
            # Without original config, we can't do proper control
            control = SandboxResult(
                success=True,  # Control "passes" (failure to fail) = inconclusive
                stdout="",
                stderr="No original config for control test",
                exit_code=0,
                duration_ms=0,
                files_changed=[]
            )
        
        logger.info("stage3_control_complete", incident_id=incident.id, control_failed=not control.success)
        
        # Determine verdict
        verdict = self._determine_verdict(baseline, post_fix, health, control)
        
        report = VerificationReport(
            incident_id=incident.id,
            remediation_id=remediation.id,
            baseline_test=baseline,
            post_fix_tests=post_fix,
            health_check=health,
            control_test=control,
            verdict=verdict,
            evidence_count=len(evidence),
            model=self.model,
            details={
                "baseline_passed": baseline.success,
                "post_fix_tests_passed": post_fix.success,
                "health_check_passed": health.success,
                "control_test_failed": not control.success,
                "baseline_exit_code": baseline.exit_code,
                "post_fix_exit_code": post_fix.exit_code,
                "health_exit_code": health.exit_code,
                "control_exit_code": control.exit_code
            }
        )
        
        logger.info("verification_complete", incident_id=incident.id, verdict=verdict.value)
        return report
    
    def _determine_verdict(
        self,
        baseline: Optional[SandboxResult],
        post_fix: Optional[SandboxResult],
        health: Optional[SandboxResult],
        control: Optional[SandboxResult]
    ) -> Verdict:
        """Determine final verdict from three stages.
        
        Matrix:
        - Missing baseline -> INSUFFICIENT_EVIDENCE
        - Baseline FAIL, Post-fix PASS, Health PASS, Control FAIL -> VERIFIED
        - Baseline FAIL, Post-fix FAIL -> FAILED
        - Baseline FAIL, Health FAIL -> FAILED
        - Baseline FAIL, Post-fix PASS, Control PASS -> UNVERIFIED
        - Baseline PASS -> UNVERIFIED
        """
        if baseline is None:
            return Verdict.INSUFFICIENT_EVIDENCE

        if post_fix is None or health is None or control is None:
            return Verdict.INSUFFICIENT_EVIDENCE
        
        baseline_failed = not baseline.success
        post_fix_passed = post_fix.success
        health_passed = health.success
        control_failed = not control.success

        if baseline_failed and post_fix_passed and health_passed and control_failed:
            return Verdict.VERIFIED
        elif not baseline_failed:
            return Verdict.UNVERIFIED
        elif not post_fix_passed or not health_passed:
            return Verdict.FAILED
        elif not control_failed:
            return Verdict.UNVERIFIED
        else:
            return Verdict.UNVERIFIED


import os  # Added for config file operations