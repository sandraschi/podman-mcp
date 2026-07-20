"""
Completely isolated test for the inspect_container function.
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Create a mock for the podman module
mock_podman = MagicMock()
sys.modules["podman"] = mock_podman

# Now import the module we want to test
from podmanmcp.tools.containers.container_inspect import inspect_container


async def test_inspect_container():
    """Test the inspect_container function with a mock Podman client."""
    # Create a mock container
    mock_container = MagicMock()
    mock_container.attrs = {
        "Id": "test123",
        "Name": "test-container",
        "State": {"Status": "running"},
        "Config": {"Image": "test-image"},
    }

    # Configure the mock Podman client
    mock_podman.from_env.return_value.containers.get.return_value = mock_container

    # Call the function directly
    result = await inspect_container(container_id="test123")

    # Verify the result
    assert "container_id" in result
    assert result["status"] == "success"
    assert "data" in result
    assert result["data"]["id"] == "test123"
    assert result["data"]["name"] == "test-container"

    print("✅ Test passed: inspect_container")
    return True


if __name__ == "__main__":
    asyncio.run(test_inspect_container())
