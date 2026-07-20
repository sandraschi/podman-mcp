"""Mock Podman API responses for testing."""

from typing import Any
from unittest.mock import AsyncMock


class MockPodmanClient:
    """Mock Podman client for testing without a Podman CLI."""

    def __init__(self):
        self.containers = MockContainers()
        self.images = MockImages()
        self.networks = MockNetworks()
        self.volumes = MockVolumes()
        self.api = MockPodmanAPI()
        self.events = AsyncMock()

    async def close(self):
        """Close the mock client."""
        pass


class MockContainers:
    """Mock Podman containers API."""

    def __init__(self):
        self._containers: dict[str, dict[str, Any]] = {}

    async def list(self, **kwargs) -> list[dict[str, Any]]:
        """List containers."""
        return list(self._containers.values())

    async def get(self, container_id: str) -> dict[str, Any]:
        """Get a container by ID."""
        if container_id not in self._containers:
            raise MockPodmanError("No such container", 404)
        return self._containers[container_id]

    async def create(self, config: dict[str, Any], **kwargs) -> dict[str, Any]:
        """Create a container."""
        container_id = f"mock_{len(self._containers) + 1}"
        container = {
            "Id": container_id,
            "Name": config.get("name") or f"{container_id[:12]}",
            "Image": config.get("Image"),
            "State": {"Status": "created"},
            "Config": config,
            "NetworkSettings": {"Networks": {}},
        }
        self._containers[container_id] = container
        return container

    async def start(self, container_id: str) -> None:
        """Start a container."""
        if container_id not in self._containers:
            raise MockPodmanError("No such container", 404)
        self._containers[container_id]["State"]["Status"] = "running"

    async def stop(self, container_id: str, **kwargs) -> None:
        """Stop a container."""
        if container_id not in self._containers:
            raise MockPodmanError("No such container", 404)
        self._containers[container_id]["State"]["Status"] = "exited"

    async def delete(self, container_id: str, **kwargs) -> None:
        """Delete a container."""
        if container_id not in self._containers:
            raise MockPodmanError("No such container", 404)
        del self._containers[container_id]


class MockImages:
    """Mock Podman images API."""

    def __init__(self):
        self._images: dict[str, dict[str, Any]] = {}

    async def list(self, **kwargs) -> list[dict[str, Any]]:
        """List images."""
        return list(self._images.values())

    async def get(self, image_id: str) -> dict[str, Any]:
        """Get an image by ID."""
        if image_id not in self._images:
            raise MockPodmanError("No such image", 404)
        return self._images[image_id]

    async def pull(self, repository: str, **kwargs) -> dict[str, Any]:
        """Pull an image."""
        image_id = f"sha256:{len(self._images) + 1:064x}"
        image = {
            "Id": image_id,
            "RepoTags": [repository],
            "Size": 1024 * 1024,  # 1MB
            "Labels": {},
            "Config": {"Cmd": ["/bin/sh"]},
        }
        self._images[image_id] = image
        return image


class MockNetworks:
    """Mock Podman networks API."""

    def __init__(self):
        self._networks: dict[str, dict[str, Any]] = {}

    async def list(self, **kwargs) -> list[dict[str, Any]]:
        """List networks."""
        return list(self._networks.values())

    async def create(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create a network."""
        network_id = f"mock_network_{len(self._networks) + 1}"
        network = {
            "Id": network_id,
            "Name": config.get("Name"),
            "Driver": config.get("Driver", "bridge"),
            "Containers": {},
        }
        self._networks[network_id] = network
        return network


class MockVolumes:
    """Mock Podman volumes API."""

    def __init__(self):
        self._volumes: dict[str, dict[str, Any]] = {}

    async def list(self) -> dict[str, list[dict[str, Any]]]:
        """List volumes."""
        return {"Volumes": list(self._volumes.values())}

    async def create(self, config: dict[str, Any]) -> dict[str, Any]:
        """Create a volume."""
        volume_name = config.get("Name") or f"mock_volume_{len(self._volumes) + 1}"
        volume = {
            "Name": volume_name,
            "Driver": config.get("Driver", "local"),
            "Mountpoint": f"/var/lib/podman/volumes/{volume_name}/_data",
            "Labels": config.get("Labels", {}),
        }
        self._volumes[volume_name] = volume
        return volume


class MockPodmanAPI:
    """Mock Podman API client."""

    def __init__(self):
        self._info = {
            "ServerVersion": "20.10.0",
            "OSType": "linux",
            "NCPU": 4,
            "MemTotal": 17179869184,  # 16GB
            "PodmanRootDir": "/var/lib/podman",
            "Name": "mock-podman-host",
        }

    async def version(self) -> dict[str, str]:
        """Get Podman version info."""
        return {
            "Version": "20.10.0",
            "ApiVersion": "1.41",
            "MinAPIVersion": "1.12",
            "GitCommit": "mock",
            "GoVersion": "go1.16.0",
            "Os": "linux",
            "Arch": "amd64",
            "KernelVersion": "5.10.0-0.bpo.5-amd64",
            "BuildTime": "2021-12-20T00:19:13.000000000+00:00",
        }

    async def info(self) -> dict[str, Any]:
        """Get Podman system info."""
        return self._info


class MockPodmanError(Exception):
    """Mock Podman API error."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def __str__(self) -> str:
        return f"{self.status_code} {self.message}"

    @property
    def explanation(self) -> str:
        """Get error explanation."""
        return self.message
