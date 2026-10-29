"""Sandbox execution engine for safe remediation testing."""
import asyncio
import docker
import tempfile
import os
import shutil
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class SandboxResult:
    """Result of sandbox execution."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    files_changed: List[str]


class SandboxEngine:
    """Executes remediation in isolated Docker sandbox."""
    
    def __init__(self, timeout: int = 300, memory_limit: str = "512m", cpu_limit: float = 1.0):
        self.timeout = timeout
        self.memory_limit = memory_limit
        self.cpu_limit = cpu_limit
        self.client = None
        self._network_name = f"coska-sandbox-{uuid.uuid4().hex[:8]}"
        self._init_docker()
    
    def _init_docker(self):
        """Initialize Docker client and create sandbox network."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            # Create isolated network for sandbox containers
            try:
                self.client.networks.create(self._network_name, driver="bridge", internal=False)
                logger.info("docker_network_created", network=self._network_name)
            except Exception as e:
                logger.warning("docker_network_create_failed", network=self._network_name, error=str(e))
            logger.info("docker_client_initialized")
        except Exception as e:
            logger.warning("docker_not_available", error=str(e))
            self.client = None
    
    def _cleanup_network(self):
        """Clean up the sandbox network."""
        if self.client:
            try:
                network = self.client.networks.get(self._network_name)
                network.remove()
                logger.info("docker_network_removed", network=self._network_name)
            except Exception:
                pass
    
    def is_available(self) -> bool:
        """Check if Docker is available."""
        return self.client is not None
    
    async def apply_config_change(
        self,
        repo_path: str,
        config_change: str,
        config_file: str = ".env"
    ) -> SandboxResult:
        """Apply configuration change in sandbox."""
        
        if not self.is_available():
            return SandboxResult(
                success=False,
                stdout="",
                stderr="Docker not available",
                exit_code=-1,
                duration_ms=0,
                files_changed=[]
            )
        
        # Create temporary directory with repo copy
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy repo to temp dir
            sandbox_repo = os.path.join(temp_dir, "repo")
            shutil.copytree(repo_path, sandbox_repo)
            
            # Parse config change: "KEY: old -> new"
            try:
                key_part, new_value = config_change.split("->")
                key = key_part.split(":")[0].strip()
                new_value = new_value.strip()
            except ValueError:
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr=f"Invalid config change format: {config_change}",
                    exit_code=-1,
                    duration_ms=0,
                    files_changed=[]
                )
            
            # Apply change
            config_path = os.path.join(sandbox_repo, config_file)
            if not os.path.exists(config_path):
                # Try common config files
                for alt in [".env", "config.yaml", "config.yml", "settings.py", "application.properties"]:
                    alt_path = os.path.join(sandbox_repo, alt)
                    if os.path.exists(alt_path):
                        config_path = alt_path
                        break
            
            if not os.path.exists(config_path):
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr=f"Config file not found: {config_file}",
                    exit_code=-1,
                    duration_ms=0,
                    files_changed=[]
                )
            
            # Read and modify
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Replace or add
            import re
            pattern = rf'^{re.escape(key)}[:\s=]+.*$'
            replacement = f"{key}={new_value}"
            
            if re.search(pattern, content, re.MULTILINE):
                new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            else:
                new_content = content.rstrip() + f"\n{replacement}\n"
            
            with open(config_path, 'w') as f:
                f.write(new_content)
            
            return SandboxResult(
                success=True,
                stdout=f"Applied {config_change} to {config_path}",
                stderr="",
                exit_code=0,
                duration_ms=0,
                files_changed=[config_path]
            )
    
    async def run_tests(
        self,
        repo_path: str,
        test_command: str = "pytest -v"
    ) -> SandboxResult:
        """Run tests in sandbox."""
        
        if not self.is_available():
            return SandboxResult(
                success=False,
                stdout="",
                stderr="Docker not available",
                exit_code=-1,
                duration_ms=0,
                files_changed=[]
            )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox_repo = os.path.join(temp_dir, "repo")
            shutil.copytree(repo_path, sandbox_repo)
            
            try:
                # Create Dockerfile for test environment
                dockerfile = """
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e . 2>/dev/null || pip install -r requirements.txt 2>/dev/null || true
CMD ["pytest", "-v"]
"""
                dockerfile_path = os.path.join(sandbox_repo, "Dockerfile.test")
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile)
                
                # Build image
                image, _ = self.client.images.build(
                    path=sandbox_repo,
                    dockerfile="Dockerfile.test",
                    tag="coska-test:latest",
                    rm=True
                )
                
                # Run tests in the sandbox network
                container = self.client.containers.run(
                    image.id,
                    command=test_command,
                    mem_limit=self.memory_limit,
                    cpu_quota=int(self.cpu_limit * 100000),
                    cpu_period=100000,
                    network=self._network_name,
                    detach=True,
                    remove=False
                )
                
                # Wait with timeout
                try:
                    result = container.wait(timeout=self.timeout)
                    exit_code = result.get('StatusCode', -1)
                    logs = container.logs(stdout=True, stderr=True).decode('utf-8')
                    
                    container.remove()
                    
                    return SandboxResult(
                        success=exit_code == 0,
                        stdout=logs,
                        stderr="",
                        exit_code=exit_code,
                        duration_ms=0,
                        files_changed=[]
                    )
                except Exception as e:
                    container.kill()
                    container.remove()
                    raise
                    
            except Exception as e:
                logger.error("sandbox_test_failed", error=str(e))
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr=str(e),
                    exit_code=-1,
                    duration_ms=0,
                    files_changed=[]
                )
    
    async def run_health_check(
        self,
        repo_path: str,
        health_command: str = "python -c \"import httpx; httpx.get('http://localhost:8000/health', timeout=5)\""
    ) -> SandboxResult:
        """Run health check in sandbox using the same network."""
        
        if not self.is_available():
            return SandboxResult(
                success=False,
                stdout="",
                stderr="Docker not available",
                exit_code=-1,
                duration_ms=0,
                files_changed=[]
            )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox_repo = os.path.join(temp_dir, "repo")
            shutil.copytree(repo_path, sandbox_repo)
            
            try:
                # Build service image
                dockerfile = """
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -e . 2>/dev/null || pip install -r requirements.txt 2>/dev/null || true
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
                dockerfile_path = os.path.join(sandbox_repo, "Dockerfile.service")
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile)
                
                image, _ = self.client.images.build(
                    path=sandbox_repo,
                    dockerfile="Dockerfile.service",
                    tag="coska-service:latest",
                    rm=True
                )
                
                # Start service container in sandbox network
                service_container = self.client.containers.run(
                    image.id,
                    detach=True,
                    network=self._network_name,
                    network_aliases=["service"],
                    mem_limit=self.memory_limit,
                    cpu_quota=int(self.cpu_limit * 100000),
                    cpu_period=100000,
                    remove=False
                )
                
                # Wait for service to start
                await asyncio.sleep(5)
                
                # Run health check from a container in the same network
                check_container = self.client.containers.run(
                    "python:3.12-slim",
                    command=health_command.replace("localhost", "service"),
                    network=self._network_name,
                    remove=True
                )
                
                exit_code = 0 if check_container == 0 else 1
                logs = check_container.decode('utf-8') if isinstance(check_container, bytes) else str(check_container)
                
                # Cleanup
                service_container.stop()
                service_container.remove()
                
                return SandboxResult(
                    success=exit_code == 0,
                    stdout=logs,
                    stderr="",
                    exit_code=exit_code,
                    duration_ms=0,
                    files_changed=[]
                )
                
            except Exception as e:
                logger.error("sandbox_health_check_failed", error=str(e))
                # Attempt cleanup
                try:
                    if 'service_container' in locals():
                        service_container.stop()
                        service_container.remove()
                except Exception:
                    pass
                return SandboxResult(
                    success=False,
                    stdout="",
                    stderr=str(e),
                    exit_code=-1,
                    duration_ms=0,
                    files_changed=[]
                )
    
    async def run_control_verification(
        self,
        repo_path: str,
        original_config: str,
        config_file: str = ".env",
        test_command: str = "pytest -v"
    ) -> SandboxResult:
        """Run control test: revert fix and verify failure returns."""
        
        if not self.is_available():
            return SandboxResult(
                success=False,
                stdout="",
                stderr="Docker not available",
                exit_code=-1,
                duration_ms=0,
                files_changed=[]
            )
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox_repo = os.path.join(temp_dir, "repo")
            shutil.copytree(repo_path, sandbox_repo)
            
            # Revert to original config
            config_path = os.path.join(sandbox_repo, config_file)
            if os.path.exists(config_path):
                with open(config_path, 'w') as f:
                    f.write(original_config)
            
            # Run tests - should FAIL
            return await self.run_tests(sandbox_repo, test_command)
    
    def cleanup(self):
        """Clean up sandbox resources."""
        self._cleanup_network()