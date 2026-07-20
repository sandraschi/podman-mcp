"""
Minimal test for the inspect_container function.
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import only the specific module we need
from podmanmcp.tools.containers import container_inspect

# Mock the podman module at the module level
container_inspect.podman = MagicMock()


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
    container_inspect.podman.from_env.return_value.containers.get.return_value = mock_container

    # Call the function directly
    result = await container_inspect.inspect_container(container_id="test123")

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
