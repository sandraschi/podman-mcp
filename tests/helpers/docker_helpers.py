"""Helper functions for Podman-related tests."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import aiopodman
import podman

logger = logging.getLogger(__name__)


class PodmanTestHelper:
    """Helper class for Podman-related test operations."""

    def __init__(self, test_config):
        self.test_config = test_config
        self.podman_client = podman.from_env()
        self.async_podman = None
        self._test_containers = []
        self._test_networks = []
        self._test_volumes = []

    async def __aenter__(self):
        self.async_podman = aiopodman.Podman()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        if self.async_podman:
            await self.async_podman.close()
            self.async_podman = None
        self.podman_client.close()

    async def ensure_image_exists(self, image_name: str) -> None:
        """Ensure the specified Podman image exists, pull if needed."""
        try:
            await self.async_podman.images.get(image_name)
            logger.info(f"Image {image_name} already exists")
        except aiopodman.PodmanError:
            logger.info(f"Pulling image {image_name}...")
            await self.async_podman.images.pull(image_name)

    @asynccontextmanager
    async def temporary_container(
        self,
        image: str,
        command: str = "sleep 3600",
        environment: dict[str, str] | None = None,
        network: str | None = None,
        **kwargs,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Create a temporary container that's automatically removed after the test."""
        await self.ensure_image_exists(image)

        container = await self.async_podman.containers.create_or_replace(
            name=f"{self.test_config.TEST_CONTAINER_PREFIX}{self._random_suffix()}",
            config={
                "Image": image,
                "Cmd": ["/bin/sh", "-c", command],
                "Env": [f"{k}={v}" for k, v in (environment or {}).items()],
                "NetworkMode": network if network else "bridge",
                "HostConfig": {
                    "AutoRemove": True,
                },
                **kwargs,
            },
        )

        self._test_containers.append(container.id)

        try:
            await container.start()
            container_info = await container.show()
            yield container_info
        finally:
            try:
                await container.delete(force=True)
            except Exception as e:
                logger.warning(f"Failed to remove container {container.id}: {e}")

    async def create_test_network(self) -> str:
        """Create a test network and return its ID."""
        network_name = f"{self.test_config.TEST_NETWORK_NAME}_{self._random_suffix()}"
        network = await self.async_podman.networks.create(
            {
                "Name": network_name,
                "CheckDuplicate": True,
                "Driver": "bridge",
            }
        )
        self._test_networks.append(network.id)
        return network.id

    async def cleanup(self) -> None:
        """Clean up all test resources."""
        errors = []

        # Clean up containers
        for container_id in self._test_containers[:]:
            try:
                container = self.podman_client.containers.get(container_id)
                container.remove(force=True)
                self._test_containers.remove(container_id)
            except Exception as e:
                errors.append(f"Failed to remove container {container_id}: {e}")

        # Clean up networks
        for network_id in self._test_networks[:]:
            try:
                network = self.podman_client.networks.get(network_id)
                network.remove()
                self._test_networks.remove(network_id)
            except Exception as e:
                errors.append(f"Failed to remove network {network_id}: {e}")

        if errors:
            logger.warning("Errors during cleanup:\n" + "\n".join(errors))

    @staticmethod
    def _random_suffix() -> str:
        """Generate a random suffix for resource names."""
        import random
        import string

        return "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
