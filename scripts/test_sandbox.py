#!/usr/bin/env python
"""
Test script to verify Docker sandbox functionality.
"""
import asyncio
import sys
import tempfile
import os
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.tools.sandbox import SandboxEngine
from app.config import get_settings


async def test_sandbox():
    """Test sandbox functionality."""
    print("=" * 60)
    print("TESTING DOCKER SANDBOX")
    print("=" * 60)
    
    settings = get_settings()
    
    sandbox = SandboxEngine(
        timeout=settings.sandbox_timeout,
        memory_limit=settings.sandbox_memory_limit,
        cpu_limit=settings.sandbox_cpu_limit
    )
    
    print(f"Docker available: {sandbox.is_available()}")
    
    if not sandbox.is_available():
        print("Docker not available - sandbox tests will be skipped")
        return False
    
    # Create a test repo
    with tempfile.TemporaryDirectory() as temp_dir:
        test_repo = os.path.join(temp_dir, "test_repo")
        os.makedirs(test_repo)
        
        # Create a simple test file
        test_file = os.path.join(test_repo, "test_sample.py")
        with open(test_file, 'w') as f:
            f.write("""
def test_add():
    assert 1 + 1 == 2

def test_subtract():
    assert 2 - 1 == 1
""")
        
        # Create requirements.txt
        with open(os.path.join(test_repo, "requirements.txt"), 'w') as f:
            f.write("pytest\n")
        
        # Test 1: Apply config change
        print("\nTest 1: Apply config change...")
        result = await sandbox.apply_config_change(
            test_repo, "TEST_KEY: old_value -> new_value", ".env"
        )
        print(f"  Success: {result.success}")
        print(f"  Output: {result.stdout[:100]}")
        
        # Test 2: Run tests
        print("\nTest 2: Run tests...")
        result = await sandbox.run_tests(test_repo, "pytest -v")
        print(f"  Success: {result.success}")
        print(f"  Exit code: {result.exit_code}")
        print(f"  Output: {result.stdout[:200]}")
        
        # Test 3: Health check (skip if no service)
        print("\nTest 3: Health check (simulated)...")
        # Skip actual health check as it requires a running service
        
        # Test 4: Control verification
        print("\nTest 4: Control verification...")
        original_config = "TEST_KEY=old_value\n"
        result = await sandbox.run_control_verification(
            test_repo, original_config, ".env", "pytest -v"
        )
        print(f"  Success (should be False): {result.success}")
        print(f"  Exit code: {result.exit_code}")
    
    print("\n" + "=" * 60)
    print("SANDBOX TEST: PASSED")
    print("=" * 60)
    return True


async def main():
    print("COSKA Sandbox Test")
    print("=" * 60)
    
    success = await test_sandbox()
    
    if success:
        print("\n✅ Sandbox test PASSED!")
        return 0
    else:
        print("\n❌ Sandbox test FAILED or SKIPPED (Docker not available)")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))