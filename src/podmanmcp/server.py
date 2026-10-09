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

# Suppress Pydantic deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")

# Import local modules
from podmanmcp.logging_config import LOG_FILE, configure_logging, logger
from podmanmcp.mcp_instance import get_mcp
from podmanmcp.tools.assorted_crap import SafeJSONEncoder, warn_with_log
from podmanmcp.transport import run_server

# Configure logging with JSON format and proper stream handling
# Disable JSON for RPC logs to prevent parsing issues
configure_logging(enable_console=True, json_format=True, log_file=str(LOG_FILE), disable_json_for_rpc=True)

# Get logger for this module
server_logger = logging.getLogger("podmanmcp.server")

# Redirect warnings to the logger
warnings.showwarning = warn_with_log

mcp = get_mcp()

# Override the default JSON encoder
mcp.json_encoder = SafeJSONEncoder()

# Log that we're using the singleton instance. Tools are registered inside
# get_mcp() via tool_registration.register_all_tools; the per-module imports
# copied from docker-mcp named modules podman never had (tools.desktop, ...).
logger.info("Using singleton FastMCP instance from mcp_instance.py")


def run_fastapi_server():
    """Run FastAPI server in a separate thread"""
    import uvicorn

    from podmanmcp.api.app import create_app

    app = create_app()
    logger.info("Starting FastAPI server on port 11113...")
    uvicorn.run(app, host="127.0.0.1", port=11113, log_level="warning")


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
