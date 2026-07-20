"""
Podman MCP Server - Main entry point.

This module initializes and runs the Podman MCP server with enhanced error handling,
logging, and system signal handling for graceful shutdowns.
"""

from __future__ import annotations

import asyncio
import atexit
import logging
import os
import signal
import sys
import time
from pathlib import Path

from podmanmcp.logging_config import configure_logging, logger
from podmanmcp.mcp_instance import get_mcp

# Add the parent directory to the Python path
src_dir = str(Path(__file__).parent.absolute())
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Configure logging with JSON format and proper stream handling
# Disable JSON for RPC logs to prevent parsing issues
configure_logging(
    enable_console=True, json_format=True, log_file=str(Path("logs/podmanmcp.log")), disable_json_for_rpc=True
)

# Global flag to control the main event loop
should_exit = False


class PodmanMCPServer:
    """Main server class for Podman MCP."""

    def __init__(self):
        """Initialize the server with default settings."""
        self.logger = logger.bind(component="podman_mcp")
        self.should_exit = False
        self.startup_time = time.time()
        self._shutdown_handlers = []

        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self.handle_exit_signal)
        signal.signal(signal.SIGTERM, self.handle_exit_signal)

    def add_shutdown_handler(self, handler: callable) -> None:
        """Register a function to be called during shutdown."""
        self._shutdown_handlers.append(handler)

    async def startup(self) -> None:
        """Initialize the server components."""
        self.logger.info("Starting Podman MCP server...")

        try:
            # Import the MCP instance first to ensure it's created

            # Import API endpoints to register them
            try:
                from podmanmcp.api import containers as _containers

                self.logger.debug("Successfully imported API endpoints")
            except ImportError as e:
                self.logger.warning(f"Failed to import API endpoints: {e}")
                # Fallback for direct script execution
                try:
                    from api import containers as _containers  # noqa: F401

                    self.logger.debug("Successfully imported API endpoints (fallback)")
                except ImportError:
                    self.logger.warning("Failed to import API endpoints (fallback)")

            # Import tools to ensure they're registered with the MCP instance
            try:
                from podmanmcp import tools as _tools  # noqa: F401

                self.logger.info("Successfully imported tools")
            except ImportError as e:
                self.logger.error(f"Failed to import tools: {e}", exc_info=True)
                raise

            self.logger.info("Podman MCP server started successfully")

        except Exception as e:
            self.logger.critical(
                "Failed to start Podman MCP server",
                exc_info=True,
                extra={"error": str(e)},
            )
            raise

    async def shutdown(self) -> None:
        """Clean up resources and shut down the server gracefully."""
        if self.should_exit:
            return

        self.should_exit = True
        self.logger.info("Shutting down Podman MCP server...")

        # Call all registered shutdown handlers in reverse order
        for handler in reversed(self._shutdown_handlers):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                self.logger.error(
                    f"Error in shutdown handler: {e}",
                    exc_info=True,
                    extra={"handler": handler.__name__ if hasattr(handler, "__name__") else str(handler)},
                )

        self.logger.info("Podman MCP server shut down successfully")

    def handle_exit_signal(self, signum: int, frame) -> None:
        """Handle system signals for graceful shutdown."""
        self.logger.info(f"Received signal {signal.Signals(signum).name}, shutting down...")
        self.should_exit = True

        # Schedule the shutdown in the event loop
        if asyncio.get_running_loop().is_running():
            self._shutdown_task = asyncio.ensure_future(self.shutdown())

    def cleanup(self) -> None:
        """Clean up resources during application exit."""
        self.logger.debug("Cleaning up resources...")
        # Add any cleanup code here

    def log_system_info(self) -> None:
        """Log system information for debugging."""
        import platform

        system_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "executable": sys.executable,
            "cwd": os.getcwd(),
            "pid": os.getpid(),
            "uid": os.getuid() if hasattr(os, "getuid") else None,
            "gid": os.getgid() if hasattr(os, "getgid") else None,
        }

        self.logger.info("System information", **system_info)


def handle_exception(exc_type: type[BaseException], exc_value: BaseException, exc_traceback) -> None:
    """Global exception handler for uncaught exceptions."""
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log keyboard interrupts
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logger.critical(
        "Uncaught exception",
        exc_info=(exc_type, exc_value, exc_traceback),
        extra={
            "exception_type": exc_type.__name__,
            "exception_message": str(exc_value),
        },
    )


async def run_server() -> None:
    """Run the Podman MCP server."""
    server = PodmanMCPServer()

    try:
        # Log system information
        server.log_system_info()

        # Initialize the server
        await server.startup()

        # Keep the server running until shutdown is requested
        while not server.should_exit:
            await asyncio.sleep(0.1)

    except asyncio.CancelledError:
        server.logger.info("Server task was cancelled")
    except Exception as e:
        server.logger.critical(
            "Fatal error in server",
            exc_info=True,
            extra={"error": str(e)},
        )
        raise
    finally:
        # Ensure clean shutdown
        await server.shutdown()


def main() -> int:
    """Entry point for the Podman MCP server."""
    # Set up global exception handler
    sys.excepthook = handle_exception

    # Configure root logger to be silent
    logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[logging.NullHandler()])

    # Silence common noisy loggers
    for logger_name in [
        "fastmcp",
        "mcp",
        "uvicorn",
        "httpx",
        "httpcore",
        "h11",
        "asyncio",
        "watchfiles",
        "uvicorn.error",
        "podman",
        "urllib3",
        "websockets",
        "aiohttp",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

    # Run the server
    try:
        logger.info("=== Podman MCP Server Starting ===")
        logger.info(f"Python Path: {sys.path}")

        # Get the singleton instance
        logger.info("Initializing FastMCP instance...")
        get_mcp()

        # Run the server in the event loop
        logger.info("Starting event loop...")
        asyncio.run(run_server())

        return 0

    except Exception as e:
        logger.critical(
            "Fatal error in main process",
            exc_info=True,
            extra={"error": str(e)},
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
