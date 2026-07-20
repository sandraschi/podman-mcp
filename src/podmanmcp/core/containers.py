"""
Container management operations.

This module provides functions for managing Podman containers including
creation, starting, stopping, and inspection.
"""

import asyncio
import logging
from typing import Any

from ..logging_config import ContextLogger

logger = ContextLogger(logging.getLogger(f"podmanmcp.core.{__name__}"), {})

# TODO: Move container operations from podman_ops/containers.py to here
# This will be implemented after confirming the file move


class ContainerManager:
    """Manager for container operations."""

    def __init__(self, podman_client):
        """Initialize with a Podman client."""
        self.client = podman_client

    async def list_containers(self, all_containers: bool = True) -> list[dict[str, Any]]:
        """List all containers with their details."""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: [
                    {
                        "id": c.id,
                        "name": c.name,
                        "status": c.status,
                        "image": c.image.tags[0] if c.image.tags else c.image.id,
                        "created": c.attrs["Created"],
                    }
                    for c in self.client.containers.list(all=all_containers)
                ],
            )
        except Exception as e:
            logger.error(f"Error listing containers: {e!s}")
            raise

    # Add other container operations here...
