#!/usr/bin/env python3
"""
Podman MCP Server

Main entry point for the Podman MCP server using FastMCP 2.12 tool registration.
"""

import asyncio
import logging
import sys
import warnings
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from podman_mcp.web import setup_webapp
from podmanmcp.logging_config import configure_logging, logger
from podmanmcp.mcp_instance import get_mcp

# Initialize MCP + tools before web routes import podmanmcp tool modules
mcp = get_mcp()

# Suppress all warnings
warnings.filterwarnings("ignore")

# Configure root logger to be silent
logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[logging.NullHandler()])

# Silence common noisy loggers
for logger_name in ["fastmcp", "mcp", "uvicorn", "httpx", "httpcore", "h11", "asyncio"]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# Configure our specific logging
configure_logging(
    enable_console=True,
    json_format=False,
    log_file=str(Path("logs/podmanmcp.log")),
    level="WARNING",
)


@asynccontextmanager
async def _web_lifespan(_app: FastAPI):
    from podman_mcp.activity_log import install_log_handler, log_activity
    from podman_mcp.llm.manager import get_llm_manager

    install_log_handler()
    log_activity("system", "Podman MCP web bridge starting")
    await get_llm_manager().glom_local_providers_if_up()
    log_activity("system", "Podman MCP web bridge ready")
    yield


# FastAPI Bridge - auth only on /api/chat so dashboard/containers work without login
web_app = FastAPI(title="Podman Management Web Bridge", lifespan=_web_lifespan)

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:10807",
        "http://localhost:10807",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup webapp bridge with the tool-loaded MCP instance
setup_webapp(web_app, mcp_app=mcp)


def _mount_web_ui(app: FastAPI) -> None:
    """Serve built web_sota for Tauri / single-port installs."""
    from pathlib import Path

    from fastapi.staticfiles import StaticFiles

    dist = Path(__file__).resolve().parent.parent / "web_sota" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="web-ui")


_mount_web_ui(web_app)


def get_all_tools() -> list[callable]:
    """
    Discover all FastMCP 2.12+ tools by scanning for @Tool decorated functions.

    Returns:
        List of tool functions that have been decorated with @Tool
    """
    import importlib
    import pkgutil
    from inspect import getmembers, isfunction
    from pathlib import Path

    tools_dir = Path(__file__).parent / "podmanmcp" / "tools"
    tools = []

    # Skip __pycache__, __init__.py, and models
    modules = [
        name
        for _, name, is_pkg in pkgutil.iter_modules([str(tools_dir)])
        if not name.startswith("_") and not name == "models" and not name.startswith("test_")
    ]

    # Import all modules to register the tools
    for name in modules:
        try:
            module = importlib.import_module(f"podmanmcp.tools.{name}")
            logger.debug(f"Imported module: podmanmcp.tools.{name}")

            # Find all functions with _tool attribute (added by @Tool decorator)
            for _func_name, func in getmembers(module, isfunction):
                if hasattr(func, "_tool"):
                    tools.append(func)
                    logger.debug(f"Discovered tool: {name}.{func.__name__}")

        except ImportError as e:
            logger.warning(f"Failed to import module {name}: {e}")
        except Exception as e:
            logger.error(f"Error processing module {name}: {e}", exc_info=True)

    logger.info(f"Discovered {len(tools)} tools")
    return tools


async def run_mcp_server():
    """Run the FastMCP server with all tools."""
    mcp_instance = get_mcp()

    # Get all tools
    tools = get_all_tools()

    # Register all tools
    for tool in tools:
        mcp_instance.register_tool(tool)

    # Log startup information
    logger.info(f"Starting Podman MCP server with {len(tools)} tools")
    logger.info("Registered tools: " + ", ".join([t.__name__ for t in tools]))

    # Configure logging for FastMCP
    mcp_instance.logger.setLevel("CRITICAL")  # Only show critical errors

    # Run the server with stdio transport and proper logging config
    logger.info("Starting FastMCP server with stdio transport...")
    await mcp_instance.run_async(
        transport="stdio",
        log_level="CRITICAL",  # Ensure minimal logging
        json_response=True,  # Set JSON response formatting
    )


def main():
    """Initialize and run the Podman MCP server with all tools."""
    try:
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        # Create and run the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(run_mcp_server())
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        except Exception as e:
            logger.error(f"Error in MCP server: {e}", exc_info=True)
            return 1
        finally:
            # Cleanup
            loop.close()

    except Exception as e:
        logger.error(f"Error starting Podman MCP server: {e!s}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
