"""
Test script to verify Podman MCP behavior when Podman is not running.

This script tests the error handling and graceful degradation features
when the Podman CLI is not available.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from podmanmcp.tools.containers.container_tools import list_containers

from podmanmcp import get_podman_status
from podmanmcp.tools.podman_reconnect import podman_reconnect
from podmanmcp.tools.podman_status import podman_status

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_podman_status():
    """Test the podman_status tool when Podman is down."""
    logger.info("Testing podman_status tool...")
    status = await podman_status()
    print("\n=== podman_status output ===")
    print(json.dumps(status, indent=2))
    print("=" * 30 + "\n")

    # Verify the status shows Podman as not available
    assert isinstance(status, dict), "podman_status should return a dictionary"
    assert "podman_available" in status, "Status should include podman_available flag"
    assert not status["podman_available"], "podman_available should be False when Podman is down"
    assert "error" in status, "Status should include error information"

    logger.info("✅ podman_status test passed")


async def test_list_containers():
    """Test list_containers when Podman is down."""
    logger.info("Testing list_containers tool...")
    from podmanmcp.tools.containers.container_models import ListContainersRequest

    # Create a simple request
    request = ListContainersRequest(all=True)
    result = await list_containers(request)

    print("\n=== list_containers output ===")
    print(json.dumps(result, indent=2))
    print("=" * 30 + "\n")

    # Should return empty list when Podman is down
    assert isinstance(result, list), "list_containers should return a list"
    assert len(result) == 0, "Should return empty list when Podman is down"

    logger.info("✅ list_containers test passed")


async def test_podman_reconnect():
    """Test the podman_reconnect tool when Podman is down."""
    logger.info("Testing podman_reconnect tool...")

    # First verify Podman is not available
    initial_status = get_podman_status()
    assert not initial_status["podman_available"], "Podman should not be available initially"

    # Try to reconnect
    result = await podman_reconnect()

    print("\n=== podman_reconnect output ===")
    print(json.dumps(result, indent=2))
    print("=" * 30 + "\n")

    # Should indicate reconnection failed
    assert isinstance(result, dict), "podman_reconnect should return a dictionary"
    assert "success" in result, "Result should include success flag"

    # Reconnection should fail since we haven't started Podman
    assert not result.get("success"), "Reconnection should fail when Podman is not running"

    logger.info("✅ podman_reconnect test passed")


async def run_tests():
    """Run all Podman down tests."""
    logger.info("Starting Podman down tests...")

    try:
        await test_podman_status()
        await test_list_containers()
        await test_podman_reconnect()

        logger.info("\n✅ All Podman down tests passed!")
        return True
    except AssertionError as e:
        logger.error(f"❌ Test failed: {e!s}", exc_info=True)
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e!s}", exc_info=True)
        return False


if __name__ == "__main__":
    # Print initial Podman status
    status = get_podman_status()
    print("\n=== Initial Podman Status ===")
    print(f"Podman Available: {status.get('podman_available', False)}")
    print(f"Error: {status.get('error', 'None')}")

    # Ensure Podman is not running before tests
    if status.get("podman_available", False):
        print("\n❌ ERROR: Podman is running. Please stop Podman Machine before running these tests.")
        sys.exit(1)

    # Run tests
    success = asyncio.run(run_tests())

    # Exit with appropriate status code
    sys.exit(0 if success else 1)
