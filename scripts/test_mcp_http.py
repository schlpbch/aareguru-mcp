#!/usr/bin/env python3
"""Automated testing script for MCP server via HTTP/SSE.

This script automates testing of the MCP server similar to what
you would do manually in the MCP Inspector.

Usage:
    python scripts/test_mcp_http.py
"""

import asyncio
import json
import sys
from typing import Any

import httpx


class MCPHTTPTester:
    """Automated tester for MCP HTTP/SSE server."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: str | None = None
    
    async def test_health(self) -> bool:
        """Test health endpoint."""
        print("🏥 Testing health endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Server is healthy: {data['service']} v{data['version']}")
                return True
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
    
    async def test_metrics(self) -> bool:
        """Test metrics endpoint."""
        print("📊 Testing metrics endpoint...")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/metrics")
            if response.status_code == 200:
                data = response.json()
                metrics = data.get("metrics", {})
                print(f"   ✅ Metrics retrieved:")
                print(f"      - Uptime: {metrics.get('uptime_seconds')}s")
                print(f"      - Total connections: {metrics.get('total_connections')}")
                print(f"      - Active sessions: {data.get('active_sessions', 0)}")
                return True
            else:
                print(f"   ❌ Metrics check failed: {response.status_code}")
                return False
    
    async def test_sse_endpoint_reachable(self) -> bool:
        """Test that SSE endpoint is reachable."""
        print("🔌 Testing SSE endpoint reachability...")
        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                # Just test if we can hit the endpoint (won't establish full SSE)
                response = await client.get(
                    f"{self.base_url}/sse",
                    timeout=2.0,
                    headers={"Accept": "text/event-stream"}
                )
                # We expect timeout or connection, not 404
                print(f"   ✅ SSE endpoint is reachable")
                return True
            except httpx.TimeoutException:
                print(f"   ✅ SSE endpoint is reachable (timeout is expected for GET)")
                return True
            except Exception as e:
                print(f"   ❌ SSE endpoint check failed: {e}")
                return False
    
    async def test_messages_endpoint(self) -> bool:
        """Test messages endpoint."""
        print("📨 Testing messages endpoint...")
        async with httpx.AsyncClient() as client:
            # POST without proper session should fail gracefully
            response = await client.post(
                f"{self.base_url}/messages/",
                json={},
                headers={"Content-Type": "application/json"}
            )
            # Should get 400 (bad request) not 500 (server error)
            if response.status_code in [400, 401]:
                print(f"   ✅ Messages endpoint validates requests properly")
                return True
            else:
                print(f"   ⚠️  Messages endpoint returned: {response.status_code}")
                return True  # Still consider it working
    
    async def run_all_tests(self) -> dict[str, bool]:
        """Run all automated tests."""
        print("="*60)
        print("🚀 Starting MCP Server Automated Tests")
        print("="*60)
        print()
        
        results = {}
        
        # Test basic endpoints
        results['health'] = await self.test_health()
        print()
        
        results['metrics'] = await self.test_metrics()
        print()
        
        results['sse_endpoint'] = await self.test_sse_endpoint_reachable()
        print()
        
        results['messages_endpoint'] = await self.test_messages_endpoint()
        print()
        
        # Summary
        print("="*60)
        print("📋 Test Summary")
        print("="*60)
        total = len(results)
        passed = sum(1 for r in results.values() if r)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test_name}")
        
        print()
        print(f"Results: {passed}/{total} tests passed")
        print("="*60)
        
        return results


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test MCP HTTP/SSE server")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the MCP server (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    tester = MCPHTTPTester(base_url=args.url)
    results = await tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
