"""
Image management operations.

This module provides functions for managing Podman images including
listing, pulling, and removing images.
"""

import asyncio
import logging
from typing import Any

from ..logging_config import ContextLogger

logger = ContextLogger(logging.getLogger(f"podmanmcp.core.{__name__}"), {})

# TODO: Move image operations from podman_ops/images.py to here


class ImageManager:
    """Manager for image operations."""

    def __init__(self, podman_client):
        """Initialize with a Podman client."""
        self.client = podman_client

    async def list_images(self, name: str | None = None) -> list[dict[str, Any]]:
        """List all images with optional filtering by name."""
        try:
            images = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.images.list(name=name) if name else self.client.images.list()
            )
            return [
                {
                    "id": img.id,
                    "tags": img.tags,
                    "created": img.attrs["Created"],
                    "size": img.attrs["Size"],
                    "virtual_size": img.attrs["VirtualSize"],
                }
                for img in images
            ]
        except Exception as e:
            logger.error(f"Error listing images: {e!s}")
            raise

    # Add other image operations here...
