"""
System-level Podman operations.

This module provides functions for system-wide Podman operations including
system information, disk usage, and cleanup.
"""

import asyncio
import logging
from typing import Any

from ..logging_config import ContextLogger

logger = ContextLogger(logging.getLogger(f"podmanmcp.core.{__name__}"), {})

# TODO: Move system operations from podman_ops/system.py to here


class SystemManager:
    """Manager for system-level Podman operations."""

    def __init__(self, podman_client):
        """Initialize with a Podman client."""
        self.client = podman_client

    async def get_system_info(self) -> dict[str, Any]:
        """Get Podman system information."""
        try:
            info = await asyncio.get_event_loop().run_in_executor(None, self.client.info)
            return {
                "containers": info["Containers"],
                "containers_running": info["ContainersRunning"],
                "containers_paused": info["ContainersPaused"],
                "containers_stopped": info["ContainersStopped"],
                "images": info["Images"],
                "driver": info["Driver"],
                "os": info["OperatingSystem"],
                "architecture": info["Architecture"],
                "cpus": info["NCPU"],
                "memory": info["MemTotal"],
                "podman_root_dir": info["PodmanRootDir"],
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e!s}")
            raise

    # Add other system operations here...
