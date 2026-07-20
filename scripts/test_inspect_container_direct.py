"""
Direct test for the inspect_container function without loading the entire application.
"""

import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import only what we need
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

    # Create a mock Podman client
    mock_podman = MagicMock()
    mock_podman.containers.get.return_value = mock_container

    # Patch the podman module to return our mock client
    with patch("podmanmcp.tools.containers.container_inspect.podman") as mock_podman_module:
        mock_podman_module.from_env.return_value = mock_podman

        # Call the function
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
