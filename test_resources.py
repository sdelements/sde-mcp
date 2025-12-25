#!/usr/bin/env python3
"""
Test script for SD Elements MCP Resources

Tests the new resource endpoints added to the SD Elements MCP server.
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the server components
from src.sde_mcp_server.api_client import SDElementsAPIClient
from src.sde_mcp_server import resources

async def test_resources():
    """Test all resource endpoints"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║  SD Elements MCP Resources - Test Suite                     ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Initialize API client
    host = os.getenv("SDE_HOST")
    api_key = os.getenv("SDE_API_KEY")
    project_id = int(os.getenv("SDE_PROJECT_ID", "31445"))
    
    if not host or not api_key:
        print("❌ ERROR: SDE_HOST and SDE_API_KEY environment variables required")
        print("\nPlease set:")
        print("  export SDE_HOST=https://cd.sdelements.com")
        print("  export SDE_API_KEY=your-api-key")
        return
    
    print(f"Configuration:")
    print(f"  Host: {host}")
    print(f"  Project ID: {project_id}")
    print()
    
    # Set global API client
    resources.api_client = SDElementsAPIClient(host=host, api_key=api_key)
    
    # Mock context (FastMCP Context not needed for testing)
    class MockContext:
        pass
    
    ctx = MockContext()
    
    # Test 1: Get all rules
    print("=" * 70)
    print("TEST 1: Get All Security Rules")
    print("=" * 70)
    try:
        result = await resources.get_all_security_rules(ctx, project_id)
        print(f"✅ Success! Retrieved {len(result)} characters")
        print(f"\nPreview (first 500 chars):\n")
        print(result[:500] + "...\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test 2: Get specific task
    print("=" * 70)
    print("TEST 2: Get Specific Task (T76)")
    print("=" * 70)
    try:
        result = await resources.get_task_rule(ctx, project_id, "T76")
        print(f"✅ Success! Retrieved {len(result)} characters")
        print(f"\nPreview (first 500 chars):\n")
        print(result[:500] + "...\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test 3: Get authentication rules
    print("=" * 70)
    print("TEST 3: Get Authentication Rules")
    print("=" * 70)
    try:
        result = await resources.get_authentication_rules(ctx, project_id)
        print(f"✅ Success! Retrieved {len(result)} characters")
        print(f"\nPreview (first 500 chars):\n")
        print(result[:500] + "...\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test 4: Get cryptography rules
    print("=" * 70)
    print("TEST 4: Get Cryptography Rules")
    print("=" * 70)
    try:
        result = await resources.get_cryptography_rules(ctx, project_id)
        print(f"✅ Success! Retrieved {len(result)} characters")
        print(f"\nPreview (first 500 chars):\n")
        print(result[:500] + "...\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test 5: Get authorization rules
    print("=" * 70)
    print("TEST 5: Get Authorization Rules")
    print("=" * 70)
    try:
        result = await resources.get_authorization_rules(ctx, project_id)
        print(f"✅ Success! Retrieved {len(result)} characters")
        print(f"\nPreview (first 500 chars):\n")
        print(result[:500] + "...\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    # Test 6: Get container rules
    print("=" * 70)
    print("TEST 6: Get Container Security Rules")
    print("=" * 70)
    try:
        result = await resources.get_container_rules(ctx, project_id)
        print(f"✅ Success! Retrieved {len(result)} characters")
        print(f"\nPreview (first 500 chars):\n")
        print(result[:500] + "...\n")
    except Exception as e:
        print(f"❌ Error: {e}\n")
    
    print("=" * 70)
    print("✅ All Tests Completed!")
    print("=" * 70)
    print("""
Next Steps:
1. Start the MCP server: python -m sde_mcp_server
2. Configure your AI IDE to use the MCP server
3. Resources will be automatically available

Resource URIs:
  • sde://project/{project_id}/rules/all
  • sde://project/{project_id}/tasks/{task_id}
  • sde://project/{project_id}/rules/authentication
  • sde://project/{project_id}/rules/cryptography
  • sde://project/{project_id}/rules/authorization
  • sde://project/{project_id}/rules/container
  • sde://project/{project_id}/rules/cicd
  • sde://project/{project_id}/rules/input-validation
""")

if __name__ == "__main__":
    asyncio.run(test_resources())

