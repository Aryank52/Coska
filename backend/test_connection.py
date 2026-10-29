#!/usr/bin/env python
"""Test script to verify Nebius Token Factory connection and Nemotron 3 Ultra."""
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Load environment FIRST before importing config
from dotenv import load_dotenv
load_dotenv(backend_path.parent / ".env")

# Clear any cached settings
import app.config
app.config.get_settings.cache_clear()

from app.services.nebius import NebiusClient
from app.services.tavily import TavilyClient
from app.config import get_settings


async def test_nebius_connection():
    """Test Nebius Token Factory connection."""
    print("=" * 60)
    print("TESTING NEBIUS TOKEN FACTORY CONNECTION")
    print("=" * 60)
    
    settings = get_settings()
    print(f"Base URL: {settings.nebius_base_url}")
    print(f"Model: {settings.nebius_model}")
    print(f"API Key: {'SET' if settings.nebius_api_key else 'NOT SET'}")
    print()
    
    if not settings.nebius_api_key:
        print("ERROR: NEBIUS_API_KEY not set in .env")
        print("Please add your Nebius Token Factory API key to .env")
        return False
    
    client = NebiusClient()
    
    print("Testing health check...")
    health_ok = await client.health_check()
    print(f"Health check: {'PASSED' if health_ok else 'FAILED'}")
    
    if not health_ok:
        print("ERROR: Could not connect to Nebius Token Factory")
        await client.close()
        return False
    
    print("\nTesting model completion...")
    result = await client.test_connection()
    
    if result["success"]:
        print(f"Model: {result['model']}")
        print(f"Response: {result['response']}")
        if result.get("usage"):
            print(f"Usage: {result['usage']}")
        print("\n[OK] NEBIUS CONNECTION VERIFIED")
        print("[OK] NEMOTRON 3 ULTRA ACCESSIBLE")
        await client.close()
        return True
    else:
        print(f"ERROR: {result.get('error')}")
        await client.close()
        return False


async def test_tavily_connection():
    """Test Tavily connection."""
    print("\n" + "=" * 60)
    print("TESTING TAVILY CONNECTION")
    print("=" * 60)
    
    settings = get_settings()
    print(f"API Key: {'SET' if settings.tavily_api_key else 'NOT SET'}")
    
    if not settings.tavily_api_key or settings.tavily_api_key == "your_tavily_api_key_here":
        print("WARNING: TAVILY_API_KEY not set in .env")
        print("Web research will not be available")
        return False
    
    client = TavilyClient()
    
    print("Testing health check...")
    health_ok = await client.health_check()
    print(f"Health check: {'PASSED' if health_ok else 'FAILED'}")
    
    if health_ok:
        print("\nTesting search...")
        try:
            result = await client.search("PostgreSQL connection pool exhaustion", max_results=3)
            print(f"Results found: {len(result.get('results', []))}")
            if result.get('results'):
                print(f"First result: {result['results'][0]['title']}")
            print("\n[OK] TAVILY CONNECTION VERIFIED")
        except Exception as e:
            print(f"Search failed: {e}")
            health_ok = False
    
    await client.close()
    return health_ok


async def main():
    """Run all connection tests."""
    print("\nCOSKA - Connection Verification")
    print("Autonomous Incident Intelligence & Verified Recovery")
    print()
    
    nebius_ok = await test_nebius_connection()
    tavily_ok = await test_tavily_connection()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Nebius Token Factory: {'[OK] CONNECTED' if nebius_ok else '[FAIL] FAILED'}")
    print(f"Tavily: {'[OK] CONNECTED' if tavily_ok else '[FAIL] NOT CONFIGURED'}")
    
    if nebius_ok:
        print("\n[SUCCESS] Ready to build COSKA!")
        return 0
    else:
        print("\n[ERROR] Fix Nebius connection before proceeding")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))