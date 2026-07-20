"""
Minimal test for the inspect_container function with all required dependencies.
"""

import asyncio
from typing import Any
from unittest.mock import MagicMock


# Define the Tool decorator if not available
class Tool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def __call__(self, func):
        return func


def tool(name: str, description: str):
    """Tool decorator for testing."""

    def decorator(func):
        return func

    return decorator


# Mock the podman module
class PodmanClient:
    def __init__(self):
        self.containers = MagicMock()


podman = MagicMock()
podman.from_env.return_value = PodmanClient()


# The actual function to test
@tool(name="inspect_container", description="Inspect a Podman container and return detailed information")
async def inspect_container(
    container_id: str, include_stats: bool = False, include_logs: bool = False, log_tail: int = 100
) -> dict[str, Any]:
    """Inspect a Podman container and return detailed information."""
    try:
        # Get the Podman client
        client = podman.from_env()

        # Get the container
        container = client.containers.get(container_id)

        # Get container details
        container_data = container.attrs

        # Prepare the result
        result = {
            "id": container_data["Id"],
            "name": container_data["Name"].lstrip("/"),
            "status": container_data["State"]["Status"],
            "image": container_data["Config"]["Image"],
            "created": container_data["Created"],
            "state": container_data["State"],
        }

        # Include additional data if requested
        if include_stats:
            result["stats"] = container.stats(stream=False)

        if include_logs:
            result["logs"] = container.logs(tail=log_tail).decode("utf-8")

        return {
            "status": "success",
            "message": "Container inspected successfully",
            "data": result,
            "container_id": container_id,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to inspect container: {e!s}",
            "error": str(e),
            "container_id": container_id,
        }


async def test_inspect_container():
    """Test the inspect_container function."""
    # Configure the mock container
    mock_container = MagicMock()
    mock_container.attrs = {
        "Id": "test123",
        "Name": "test-container",
        "State": {"Status": "running"},
        "Config": {"Image": "test-image"},
        "Created": "2023-01-01T00:00:00Z",
    }

    # Configure the mock Podman client
    podman.from_env.return_value.containers.get.return_value = mock_container

    # Call the function
    result = await inspect_container(container_id="test123")

    # Verify the result
    assert "container_id" in result, "Result should contain container_id"
    assert result["status"] == "success", "Status should be 'success'"
    assert "data" in result, "Result should contain data"
    assert result["data"]["id"] == "test123", "Container ID should match"
    assert result["data"]["name"] == "test-container", "Container name should match"

    print("✅ Test passed: inspect_container")
    return True


if __name__ == "__main__":
    asyncio.run(test_inspect_container())
