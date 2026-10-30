#!/usr/bin/env python
"""
COSKA Doctor - System health diagnostics

Checks all system components and reports status.
"""
import asyncio
import sys
import subprocess
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import get_settings
from app.services.providers import get_provider
from app.services.tavily import get_tavily_client
from app.tools.sandbox import SandboxEngine
from app.config import get_settings as get_backend_settings


async def check_python() -> tuple[bool, str]:
    """Check Python version."""
    import sys
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 12):
        return True, f"Python {version} [OK]"
    return False, f"Python {version} [FAIL] (requires 3.12+)"


async def check_node() -> tuple[bool, str]:
    """Check Node.js version."""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        version = result.stdout.strip()
        return True, f"Node.js {version} [OK]"
    except Exception:
        return False, "Node.js not found [FAIL]"


async def check_docker() -> tuple[bool, str]:
    """Check Docker availability."""
    try:
        import docker
        client = docker.from_env()
        client.ping()
        return True, "Docker [OK]"
    except Exception as e:
        return False, f"Docker not available [WARN] (required for sandbox verification): {str(e)[:100]}"


async def check_backend() -> tuple[bool, str]:
    """Check backend API health."""
    import httpx
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.vite_api_url}/api/health")
            if resp.status_code == 200:
                return True, f"Backend API [OK] ({settings.vite_api_url})"
            return False, f"Backend API returned {resp.status_code}"
    except Exception as e:
        return False, f"Backend API unreachable: {e}"


async def check_ai_provider() -> tuple[bool, str]:
    """Check AI provider connectivity."""
    settings = get_settings()
    from app.services.providers import get_provider
    
    provider = get_provider(
        provider_type=settings.ai_provider,
        api_key=settings.nebius_api_key,
        base_url=settings.nebius_base_url,
        model=settings.nebius_model
    )
    
    info = await provider.health_check()
    await provider.close()
    
    if info.reachable and info.authenticated and info.model_available and info.inference_test:
        return True, f"AI Provider: {info.name} ({info.model}) [OK]"
    elif info.reachable and info.authenticated:
        return True, f"AI Provider: {info.name} (model unavailable) [WARN]"
    elif info.reachable:
        return False, f"AI Provider: {info.name} (auth failed: {info.error}) [FAIL]"
    else:
        return False, f"AI Provider unreachable: {info.error} [FAIL]"


async def check_tavily() -> tuple[bool, str]:
    """Check Tavily connectivity."""
    settings = get_settings()
    if not settings.tavily_api_key or settings.tavily_api_key == "your_tavily_api_key_here":
        return True, "Tavily: not configured [WARN] (optional)"
    
    from app.services.tavily import get_tavily_client
    client = get_tavily_client()
    try:
        healthy = await client.health_check()
        await client.close()
        if healthy:
            return True, "Tavily [OK]"
        return False, "Tavily API error [FAIL]"
    except Exception as e:
        return False, f"Tavily error: {e} [FAIL]"


async def check_sandbox() -> tuple[bool, str]:
    """Check sandbox capability."""
    sandbox = SandboxEngine()
    if sandbox.is_available():
        return True, "Sandbox (Docker) [OK]"
    return False, "Sandbox (Docker) not available [WARN]"


async def check_frontend_build() -> tuple[bool, str]:
    """Check frontend build."""
    try:
        use_shell = os.name == 'nt'  # Use shell on Windows to find npm in PATH
        result = subprocess.run(["npm", "run", "build"], 
                              cwd=Path(__file__).parent.parent / "frontend",
                              capture_output=True, text=True, timeout=120,
                              shell=use_shell)
        if result.returncode == 0:
            return True, "Frontend build [OK]"
        return False, f"Frontend build failed: {result.stderr[:200]}"
    except Exception as e:
        return False, f"Frontend build error: {e}"


async def check_mock_provider() -> tuple[bool, str]:
    """Check mock provider works."""
    try:
        from app.services.providers import MockAIProvider
        provider = MockAIProvider("test-model")
        info = await provider.health_check()
        if info.reachable and info.authenticated and info.model_available and info.inference_test:
            return True, "Mock Provider [OK]"
        return False, "Mock Provider [FAIL]"
    except Exception as e:
        return False, f"Mock Provider error: {e} [FAIL]"


async def check_demo_fixtures() -> tuple[bool, str]:
    """Check demo fixtures exist."""
    try:
        fixtures_path = Path(__file__).parent.parent / "demo" / "incidents" / "payment-api-incident.json"
        if fixtures_path.exists():
            return True, "Demo fixtures [OK]"
        return False, "Demo fixtures not found [FAIL]"
    except Exception as e:
        return False, f"Demo fixtures check error: {e} [FAIL]"


async def check_database() -> tuple[bool, str]:
    """Check database connectivity."""
    try:
        from app.services.storage import get_storage
        storage = get_storage()
        # Try to list incidents (will create empty table if needed)
        incidents = storage.list_incidents()
        return True, f"Database [OK] ({len(incidents)} incidents)"
    except Exception as e:
        return False, f"Database error: {e} [FAIL]"


async def main():
    """Run all health checks."""
    print("COSKA Doctor - System Diagnostics")
    print("=" * 50)
    
    checks = [
        ("Python", check_python()),
        ("Node.js", check_node()),
        ("Docker", check_docker()),
        ("Backend API", check_backend()),
        ("AI Provider", check_ai_provider()),
        ("Tavily", check_tavily()),
        ("Sandbox", check_sandbox()),
        ("Frontend Build", check_frontend_build()),
        ("Mock Provider", check_mock_provider()),
        ("Demo Fixtures", check_demo_fixtures()),
        ("Database", check_database()),
    ]
    
    results = []
    for name, coro in checks:
        try:
            ok, msg = await coro
            results.append((name, ok, msg))
            status = "[OK]" if ok else "[FAIL]"
            print(f"  {status} {name}: {msg}")
        except Exception as e:
            results.append((name, False, f"Check failed: {e}"))
            print(f"  [FAIL] {name}: Check failed: {e}")
    
    print("\n" + "=" * 50)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"Summary: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n[SUCCESS] All systems operational!")
        return 0
    else:
        print("\n[WARNING] Some checks failed - see details above")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))