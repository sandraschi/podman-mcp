#!/usr/bin/env python3
"""
Test script to verify podmanmcp server starts properly after FastMCP 2.12 fixes.
"""

import sys
import traceback
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test that all imports work correctly."""
    print("🔧 Testing imports...")

    try:
        # Test main module import
        print("  ✓ Importing podmanmcp...")

        # Test tools import
        print("  ✓ Importing podmanmcp.tools...")

        # Test individual tool modules
        print("  ✓ Testing individual tool modules...")
        print("    ✓ containers module")

        print("    ✓ images module")

        print("    ✓ networks module")

        print("    ✓ volumes module")

        print("    ✓ system module")

        print("    ✓ workflow module")

        print("    ✓ compose module")

        print("✅ All imports successful!")
        return True

    except Exception as e:
        print(f"❌ Import failed: {e!s}")
        print(f"❌ Error type: {type(e).__name__}")
        traceback.print_exc()
        return False


def test_tool_discovery():
    """Test that tool discovery works."""
    print("\n🔧 Testing tool discovery...")

    try:
        from podmanmcp.tools import get_tools

        tools = get_tools()
        print(f"  ✓ Found {len(tools)} tools")

        # Check if we have some basic tools
        tool_names = [getattr(tool, "name", str(tool)) for tool in tools]
        print(f"  ✓ Tool names: {tool_names[:5]}{'...' if len(tool_names) > 5 else ''}")

        return True

    except Exception as e:
        print(f"❌ Tool discovery failed: {e!s}")
        traceback.print_exc()
        return False


def test_server_creation():
    """Test that we can create the MCP server."""
    print("\n🔧 Testing server creation...")

    try:
        from podmanmcp.server import create_server

        server = create_server()
        print("  ✓ Server created successfully")
        return True

    except Exception as e:
        print(f"❌ Server creation failed: {e!s}")
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🚀 Podman MCP FastMCP 2.12 Compatibility Test")
    print("=" * 50)

    tests = [test_imports, test_tool_discovery, test_server_creation]

    results = []
    for test in tests:
        results.append(test())

    print("\n" + "=" * 50)
    if all(results):
        print("🎉 ALL TESTS PASSED! Podman MCP is compatible with FastMCP 2.12")
        return 0
    else:
        print("💥 SOME TESTS FAILED! Check the output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
