#!/usr/bin/env python
"""
COSKA Doctor - System Diagnostics

Diagnoses system environment, services, providers, database, and sandbox.
Outputs truthful states: PASS, WARN, FAIL.
"""
import asyncio
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import get_settings
from app.tools.sandbox import SandboxEngine


async def check_python() -> Tuple[str, str]:
    """Check Python version (3.12+)."""
    v = sys.version_info
    version_str = f"{v.major}.{v.minor}.{v.micro}"
    if v >= (3, 12):
        return "PASS", f"Python {version_str} [OK]"
    elif v >= (3, 11):
        return "WARN", f"Python {version_str} (3.12+ recommended)"
    return "FAIL", f"Python {version_str} (3.12+ required)"


async def check_node() -> Tuple[str, str]:
    """Check Node.js version."""
    try:
        use_shell = os.name == 'nt'
        result = subprocess.run(["node", "-v"], capture_output=True, text=True, timeout=10, shell=use_shell)
        if result.returncode == 0:
            version = result.stdout.strip()
            return "PASS", f"Node.js {version} [OK]"
        return "FAIL", "Node.js not working properly"
    except Exception as e:
        return "FAIL", f"Node.js not installed: {e}"


async def check_docker() -> Tuple[str, str]:
    """Check Docker availability."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return "PASS", "Docker daemon running [OK]"
    except Exception as e:
        return "WARN", f"Docker not running (Local safe sandbox active as fallback): {str(e)[:60]}"


async def check_backend() -> Tuple[str, str]:
    """Check backend API health."""
    import httpx
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.vite_api_url}/api/health")
            if resp.status_code == 200:
                return "PASS", f"Backend API [OK] ({settings.vite_api_url})"
            return "FAIL", f"Backend API returned status {resp.status_code}"
    except Exception as e:
        return "FAIL", f"Backend API unreachable: {e}"


async def check_frontend_build() -> Tuple[str, str]:
    """Check frontend build artifact."""
    dist_index = Path(__file__).parent.parent / "frontend" / "dist" / "index.html"
    if dist_index.exists():
        return "PASS", "Frontend build [OK] (dist/index.html exists)"
    return "WARN", "Frontend build missing. Run 'npm run build' in frontend/"


async def check_database() -> Tuple[str, str]:
    """Check SQLite database connectivity."""
    try:
        from app.services.storage import get_storage
        storage = get_storage()
        incidents = storage.list_incidents()
        return "PASS", f"Database (SQLite) [OK] ({len(incidents)} incidents recorded)"
    except Exception as e:
        return "FAIL", f"Database error: {e}"


async def check_provider() -> Tuple[str, str]:
    """Check AI provider abstraction."""
    settings = get_settings()
    from app.services.providers import get_provider
    try:
        provider = get_provider()
        info = await provider.health_check()
        if info.reachable and info.authenticated:
            return "PASS", f"AI Provider: {info.name} ({info.model}) [OK]"
        return "WARN", f"AI Provider: {info.name} degraded ({info.error})"
    except Exception as e:
        return "FAIL", f"AI Provider error: {e}"


async def check_nebius_config() -> Tuple[str, str]:
    """Check Nebius Token Factory configuration."""
    settings = get_settings()
    if not settings.nebius_api_key or settings.nebius_api_key.startswith("your_"):
        return "WARN", "Nebius Token Factory: unconfigured (Ready for real key, currently using mock)"
    return "PASS", f"Nebius Token Factory: configured ({settings.nebius_model})"


async def check_tavily() -> Tuple[str, str]:
    """Check Tavily web research client."""
    from app.services.tavily import get_tavily_client
    client = get_tavily_client()
    if not client.is_configured:
        return "WARN", "Tavily: not configured (optional)"
    try:
        healthy = await client.health_check()
        if healthy:
            return "PASS", "Tavily Web Research [OK]"
        return "WARN", "Tavily connection degraded"
    except Exception as e:
        return "WARN", f"Tavily check error: {e}"


async def check_sandbox() -> Tuple[str, str]:
    """Check sandbox engine capability."""
    sandbox = SandboxEngine()
    if sandbox.is_available():
        return "PASS", f"Sandbox ({sandbox.provider_name}) operational [OK]"
    return "FAIL", f"Sandbox ({sandbox.provider_name}) unavailable"


async def check_demo_fixtures() -> Tuple[str, str]:
    """Check payment-api demo fixture."""
    fixture = Path(__file__).parent.parent / "demo" / "incidents" / "payment-api-incident.json"
    demo_app = Path(__file__).parent.parent / "demo" / "payment-api" / "app" / "main.py"
    if fixture.exists() and demo_app.exists():
        return "PASS", "Demo fixtures & payment-api service [OK]"
    return "FAIL", "Demo fixtures missing"


async def main():
    """Run all COSKA Doctor diagnostics."""
    print("COSKA Doctor - System Diagnostics")
    print("=" * 60)

    checks = [
        ("Python", check_python()),
        ("Node.js", check_node()),
        ("Backend API", check_backend()),
        ("Frontend Build", check_frontend_build()),
        ("Database", check_database()),
        ("AI Provider", check_provider()),
        ("Nebius Configuration", check_nebius_config()),
        ("Tavily", check_tavily()),
        ("Sandbox", check_sandbox()),
        ("Docker", check_docker()),
        ("Demo Fixtures", check_demo_fixtures()),
    ]

    results = []
    fail_count = 0
    warn_count = 0
    pass_count = 0

    for name, coro in checks:
        try:
            status, msg = await coro
            results.append((name, status, msg))
            if status == "PASS":
                pass_count += 1
                badge = "[PASS]"
            elif status == "WARN":
                warn_count += 1
                badge = "[WARN]"
            else:
                fail_count += 1
                badge = "[FAIL]"
            print(f"  {badge} {name}: {msg}")
        except Exception as e:
            fail_count += 1
            print(f"  [FAIL] {name}: Diagnostic error: {e}")

    print("\n" + "=" * 60)
    print(f"Summary: {pass_count} passed, {warn_count} warnings, {fail_count} failed ({len(results)} total checks)")

    if fail_count == 0:
        print("[SUCCESS] All required COSKA systems are operational!")
        return 0
    else:
        print(f"[FAIL] {fail_count} critical checks failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
