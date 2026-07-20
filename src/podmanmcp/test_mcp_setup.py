"""
Test script to verify FastMCP setup and tool registration.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from podmanmcp.logging_config import configure_logging, logger  # noqa: E402
from podmanmcp.mcp_instance import get_mcp  # noqa: E402

# Configure logging
configure_logging(level="INFO")


def test_mcp_setup():
    """Test that the MCP instance is properly set up and tools are registered."""
    try:
        # Get the MCP instance
        mcp = get_mcp()

        # Get registered tools
        tools = mcp.get_tools()

        # Print tool information
        logger.info(f"Found {len(tools)} registered tools:")
        for tool in tools:
            logger.info(f"- {tool['name']}: {tool.get('description', 'No description')}")

        return True
    except Exception as e:
        logger.error(f"Error testing MCP setup: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    if test_mcp_setup():
        logger.info("✅ MCP setup test completed successfully")
    else:
        logger.error("❌ MCP setup test failed")
