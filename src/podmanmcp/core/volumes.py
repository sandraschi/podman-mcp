"""
Volume management operations.

This module provides functions for managing Podman volumes including
creation, inspection, and removal.
"""

import asyncio
import logging
from typing import Any

from ..logging_config import ContextLogger

logger = ContextLogger(logging.getLogger(f"podmanmcp.core.{__name__}"), {})

# TODO: Move volume operations from podman_ops/volumes.py to here


class VolumeManager:
    """Manager for volume operations."""

    def __init__(self, podman_client):
        """Initialize with a Podman client."""
        self.client = podman_client

    async def list_volumes(self) -> list[dict[str, Any]]:
        """List all Podman volumes."""
        try:
            volumes = await asyncio.get_event_loop().run_in_executor(None, lambda: self.client.volumes.list())
            return [
                {
                    "name": vol.name,
                    "driver": vol.attrs["Driver"],
                    "mountpoint": vol.attrs["Mountpoint"],
                    "labels": vol.attrs.get("Labels", {}),
                }
                for vol in volumes["Volumes"]
            ]
        except Exception as e:
            logger.error(f"Error listing volumes: {e!s}")
            raise

    # Add other volume operations here...
