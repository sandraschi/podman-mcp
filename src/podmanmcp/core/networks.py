"""
Network management operations.

This module provides functions for managing Podman networks including
creation, inspection, and removal.
"""

import asyncio
import logging
from typing import Any

from ..logging_config import ContextLogger

logger = ContextLogger(logging.getLogger(f"podmanmcp.core.{__name__}"), {})

# TODO: Move network operations from podman_ops/networks.py to here


class NetworkManager:
    """Manager for network operations."""

    def __init__(self, podman_client):
        """Initialize with a Podman client."""
        self.client = podman_client

    async def list_networks(self) -> list[dict[str, Any]]:
        """List all Podman networks."""
        try:
            networks = await asyncio.get_event_loop().run_in_executor(None, self.client.networks.list)
            return [
                {
                    "id": net.id,
                    "name": net.name,
                    "driver": net.attrs["Driver"],
                    "scope": net.attrs["Scope"],
                    "ipam": net.attrs.get("IPAM", {}),
                }
                for net in networks
            ]
        except Exception as e:
            logger.error(f"Error listing networks: {e!s}")
            raise

    # Add other network operations here...
