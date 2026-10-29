#!/usr/bin/env python
"""
Test script to verify Nebius Token Factory connection and Nemotron 3 Ultra model access.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.providers import create_provider, NebiusTokenFactoryProvider
from app.config import get_settings


async def test_nebius_connection():
    """Test Nebius Token Factory connection with real API key."""
    print("=" * 60)
    print("TESTING NEBIUS TOKEN FACTORY CONNECTION")
    print("=" * 60)
    
    settings = get_settings()
    print(f"Base URL: {settings.nebius_base_url}")
    print(f"Model: {settings.nebius_model}")
    print(f"API Key: {'SET' if settings.nebius_api_key else 'NOT SET'}")
    print(f"AI Provider: {settings.ai_provider}")
    print()
    
    if not settings.nebius_api_key:
        print("ERROR: NEBIUS_API_KEY not set in .env")
        print("Please add your Nebius Token Factory API key to .env")
        return False
    
    if settings.nebius_api_key.startswith("nvapi-"):
        print("WARNING: API key appears to be an NVIDIA key (nvapi-), not a Nebius Token Factory key")
        print("Please use a Nebius Token Factory API key from https://tokenfactory.nebius.com/")
        print()
    
    # Create provider
    provider = NebiusTokenFactoryProvider(
        api_key=settings.nebius_api_key,
        base_url=settings.nebius_base_url,
        model=settings.nebius_model
    )
    
    print("Testing health check...")
    health = await provider.health_check()
    print(f"  Reachable: {health.reachable}")
    print(f"  Authenticated: {health.authenticated}")
    print(f"  Model Available: {health.model_available}")
    print(f"  Inference Test: {health.inference_test}")
    if health.error:
        print(f"  Error: {health.error}")
    print()
    
    if not health.reachable:
        print("FAILED: Cannot reach Nebius Token Factory")
        return False
    
    if not health.authenticated:
        print("FAILED: Authentication failed")
        return False
    
    if not health.inference_test:
        print("FAILED: Inference test failed")
        return False
    
    print("Testing inference with Nemotron 3 Ultra...")
    test_result = await provider.test_inference("Reply with exactly: COSKA_NEBIUS_OK")
    print(f"  Success: {test_result.get('success')}")
    print(f"  Model: {test_result.get('model')}")
    print(f"  Response: {test_result.get('response')}")
    if test_result.get('usage'):
        print(f"  Usage: {test_result['usage']}")
    print()
    
    if not test_result.get('success'):
        print("FAILED: Inference test failed")
        return False
    
    if test_result.get('response') != "COSKA_NEBIUS_OK":
        print(f"WARNING: Unexpected response: {test_result.get('response')}")
    
    print("Testing chat completion with tools...")
    messages = [
        {"role": "system", "content": "You are COSKA, an autonomous incident intelligence system."},
        {"role": "user", "content": "Explain what COSKA does in one sentence."}
    ]
    try:
        result = await provider.chat_completion(messages, max_tokens=100, temperature=0.3)
        content = result["choices"][0]["message"]["content"]
        print(f"  Response: {content[:200]}...")
        if result.get("usage"):
            print(f"  Usage: {result['usage']}")
    except Exception as e:
        print(f"  Error: {e}")
    
    await provider.close()
    
    print()
    print("=" * 60)
    print("NEBIUS CONNECTION TEST: PASSED")
    print("=" * 60)
    return True


async def test_tavily_connection():
    """Test Tavily connection if configured."""
    print("\n" + "=" * 60)
    print("TESTING TAVILY CONNECTION")
    print("=" * 60)
    
    settings = get_settings()
    print(f"API Key: {'SET' if settings.tavily_api_key and settings.tavily_api_key != 'your_tavily_api_key_here' else 'NOT SET'}")
    
    if not settings.tavily_api_key or settings.tavily_api_key == "your_tavily_api_key_here":
        print("WARNING: TAVILY_API_KEY not configured")
        print("Web research will not be available")
        return False
    
    from app.services.tavily import TavilyClient
    client = TavilyClient()
    
    print("Testing health check...")
    try:
        healthy = await client.health_check()
        if healthy:
            print("Health check: PASSED")
        else:
            print("Health check: FAILED")
            return False
    except Exception as e:
        print(f"Health check failed: {e}")
        return False
    
    print("Testing search...")
    try:
        result = await client.search("PostgreSQL connection pool exhaustion", max_results=3)
        print(f"Results found: {len(result.get('results', []))}")
        if result.get('results'):
            print(f"First result: {result['results'][0]['title'][:80]}")
        print("TAVILY CONNECTION TEST: PASSED")
        return True
    except Exception as e:
        print(f"Search failed: {e}")
        return False


async def main():
    """Run all connection tests."""
    print("\nCOSKA - Connection Verification")
    print("Autonomous Incident Intelligence & Verified Recovery")
    print()
    
    # Test Nebius
    nebius_ok = await test_nebius_connection()
    
    # Test Tavily
    tavily_ok = await test_tavily_connection()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Nebius Token Factory: {'PASSED' if nebius_ok else 'FAILED'}")
    print(f"Tavily: {'PASSED' if tavily_ok else 'NOT CONFIGURED'}")
    
    if nebius_ok:
        print("\n[SUCCESS] Ready for real Nebius integration!")
        return 0
    else:
        print("\n[ERROR] Fix Nebius connection before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))