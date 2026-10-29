#!/usr/bin/env python
"""Test script to run payment-api load test and generate incident."""
import asyncio
import httpx
import random
import sys
from pathlib import Path

# Add payment-api to path
sys.path.insert(0, str(Path(__file__).parent / "demo" / "payment-api"))


async def run_load_test():
    """Run load test against payment-api."""
    base_url = "http://localhost:8001"
    
    print("=" * 60)
    print("PAYMENT-API LOAD TEST")
    print("=" * 60)
    print(f"Target: {base_url}")
    print()
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Health check first
        try:
            health = await client.get(f"{base_url}/health")
            print(f"Health check: {health.status_code} - {health.json()}")
        except Exception as e:
            print(f"Health check failed: {e}")
            print("Make sure payment-api is running on port 8001")
            return
        
        # Run load test
        print("\nRunning load test (100 requests, 20 concurrent)...")
        try:
            resp = await client.post(
                f"{base_url}/load-test",
                json={"requests": 100, "concurrency": 20},
                timeout=30.0
            )
            result = resp.json()
            print(f"Results: {result}")
            print(f"Error rate: {result['error_rate']:.1%}")
            
            if result['error_rate'] > 0.1:
                print("\n⚠️  HIGH ERROR RATE DETECTED - Incident conditions met!")
                print("This simulates the incident scenario for COSKA.")
        except Exception as e:
            print(f"Load test failed: {e}")


if __name__ == "__main__":
    asyncio.run(run_load_test())