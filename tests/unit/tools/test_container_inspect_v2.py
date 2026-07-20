"""
Test script for the container inspection tools (v2).

This script tests the inspect_container function independently.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import only what we need for testing

# Import the tool we want to test
from podmanmcp.tools.containers.container_inspect_v2 import inspect_container


async def test_inspect_container(container_id: str):
    """Test the inspect_container function."""
    try:
        logger.info(f"Testing inspect_container with container: {container_id}")

        # Test basic inspection
        result = await inspect_container(container_id=container_id, include_stats=True, include_logs=True, log_tail=10)

        # Print results
        print("\nInspection Results:")
        print(json.dumps(result, indent=2, default=str))

        # Basic validation
        assert result["success"] is True, "Inspection failed"
        assert result["container_id"] == container_id, "Container ID mismatch"
        assert "name" in result, "Missing container name"
        assert "status" in result, "Missing container status"

        if result.get("stats"):
            logger.info("Stats included in response")
        if result.get("logs"):
            logger.info(f"Logs included in response ({len(result['logs'])} lines)")

        logger.info("Test passed successfully!")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_container_inspect_v2.py <container_id>")
        sys.exit(1)

    container_id = sys.argv[1]
    asyncio.run(test_inspect_container(container_id))
