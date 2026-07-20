#!/usr/bin/env python3
"""
Podman MCP Server - Main Entry Point

This module initializes and runs the Podman MCP server with FastMCP 3.1+ compatibility.
Includes both MCP stdio transport and FastAPI HTTP server for the webapp.
"""

import asyncio
import logging
import sys
import threading
import warnings
from pathlib import Path

# Suppress Pydantic deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Import local modules
from podmanmcp.logging_config import configure_logging, logger  # noqa: E402
from podmanmcp.mcp_instance import get_mcp  # noqa: E402
from podmanmcp.tools.assorted_crap import SafeJSONEncoder, warn_with_log  # noqa: E402
from podmanmcp.transport import run_server  # noqa: E402

# Configure logging with JSON format and proper stream handling
# Disable JSON for RPC logs to prevent parsing issues
configure_logging(
    enable_console=True, json_format=True, log_file=str(Path("logs/podmanmcp.log")), disable_json_for_rpc=True
)

# Get logger for this module
server_logger = logging.getLogger("podmanmcp.server")

# Redirect warnings to the logger
warnings.showwarning = warn_with_log

mcp = get_mcp()

# Override the default JSON encoder
mcp.json_encoder = SafeJSONEncoder()

# Log that we're using the singleton instance
logger.info("Using singleton FastMCP instance from mcp_instance.py")

# Import tool modules to register them with @mcp.tool decorators
try:
    # Import tool modules - these will be registered via @mcp.tool decorators
    from podmanmcp.tools import agentic_container_workflow as _aw  # noqa: F401
    from podmanmcp.tools.containers import list_containers as _lc  # noqa: F401

    # Import desktop tools
    from podmanmcp.tools.desktop import (  # noqa: F401
        podman_daemon_recover,
        podman_daemon_restart,
        podman_desktop_status,
        podman_desktop_update,
    )
    from podmanmcp.tools.networks import network_management as _nm  # noqa: F401
    from podmanmcp.tools.system import system_management as _sm  # noqa: F401
    from podmanmcp.tools.volumes import volume_management as _vm  # noqa: F401
    from podmanmcp.tools.workflows import workflow_management as _wm  # noqa: F401

    # Log successful imports
    logger.info("Successfully imported all tool modules including Podman Machine tools and SEP-1577 agentic workflows")

except ImportError as e:
    logger.error(f"Failed to import tool modules: {e}", exc_info=True)
    sys.exit(1)


def run_fastapi_server():
    """Run FastAPI server in a separate thread"""
    import uvicorn

    from podmanmcp.api.app import create_app

    app = create_app()
    logger.info("Starting FastAPI server on port 10807...")
    uvicorn.run(app, host="127.0.0.1", port=10807, log_level="warning")


def main() -> None:
    """Initialize and run the Podman MCP server with stdio transport and FastAPI HTTP."""
    try:
        # Start FastAPI server in a background thread
        fastapi_thread = threading.Thread(target=run_fastapi_server, daemon=True)
        fastapi_thread.start()
        logger.info("FastAPI server started in background thread")

        # Give FastAPI time to start
        import time

        time.sleep(2)

        # Start MCP stdio server
        logger.info("Starting Podman MCP server with stdio transport...")
        asyncio.run(run_server(mcp, server_name="podman-mcp"))
    except KeyboardInterrupt:
        logger.info("Shutting down Podman MCP server...")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
