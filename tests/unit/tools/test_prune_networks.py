"""
Tests for the prune_networks function.

This module contains tests specifically for the prune_networks function.
"""

import os
import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# Mock the Tool decorator
def Tool(name: str, description: str, parameters: dict[str, Any], returns: dict[str, Any], **kwargs):
    """Mock Tool decorator for testing."""

    def decorator(func):
        func.tool_metadata = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "returns": returns,
            **kwargs,
        }
        return func

    return decorator


# Mock the FastMCP components
sys.modules["fastmcp"] = MagicMock()
sys.modules["fastmcp.exceptions"] = MagicMock()
sys.modules["fastmcp.exceptions"].ToolError = Exception
sys.modules["fastmcp.tools"] = MagicMock()
sys.modules["fastmcp.tools"].Tool = Tool

# Mock the network tools module
with patch("fastmcp.tools.Tool", Tool):
    from podmanmcp.tools.networks.network_tools import prune_networks

# Test data
TEST_NETWORK_ID = "7d86d31b1478e7cc9a2c8b8c4b982a5eafc70b5349d0d5a5875a855d0f2d2b3d"


# Mock function for run_podman_command
def mock_run_podman_command(*args, **kwargs):
    """Mock function for run_podman_command."""
    if "network" in args[1] and "prune" in args[1]:
        return {"NetworksDeleted": ["network1", "network2"], "SpaceReclaimed": 1024}
    return None


# Test class for prune_networks
class TestPruneNetworks:
    """Tests for the prune_networks function."""

    @pytest.mark.asyncio
    @patch("podmanmcp.tools.networks.network_tools.run_podman_command", side_effect=mock_run_podman_command)
    async def test_prune_networks_success(self, mock_run_podman):
        """Test successful network pruning."""
        # Call the function
        result = await prune_networks(filters={"until": "24h"}, force=True, timeout=30)

        # Verify the result
        assert result["success"] is True
        assert len(result["networks_deleted"]) == 2
        assert result["space_reclaimed"] == 1024
        assert "Successfully pruned 2 networks" in result["message"]

        # Verify the Podman command was called correctly
        mock_run_podman.assert_called_once()
        args, kwargs = mock_run_podman.call_args
        assert "network" in args[1]
        assert "prune" in args[1]
        assert "--force" in args[1]
        assert "--filter" in args[1]
        assert "until=24h" in args[1]

    @pytest.mark.asyncio
    @patch(
        "podmanmcp.tools.networks.network_tools.run_podman_command",
        return_value={"NetworksDeleted": None, "SpaceReclaimed": 0},
    )
    async def test_prune_networks_no_networks(self, mock_run_podman):
        """Test pruning when no networks are found."""
        # Call the function
        result = await prune_networks()

        # Verify the result
        assert result["success"] is True
        assert len(result["networks_deleted"]) == 0
        assert result["space_reclaimed"] == 0
        assert "No networks were pruned" in result["message"]

    @pytest.mark.asyncio
    @patch("podmanmcp.tools.networks.network_tools.run_podman_command", side_effect=TimeoutError("Operation timed out"))
    async def test_prune_networks_timeout(self, mock_run_podman):
        """Test network pruning with a timeout."""
        # Call the function and expect an exception
        with pytest.raises(Exception) as exc_info:
            await prune_networks(timeout=5)

        # Verify the error message
        assert "timed out" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_timeout", [-1, 0, 301])
    @pytest.mark.asyncio
    async def test_prune_networks_invalid_timeout(self, invalid_timeout):
        """Test network pruning with invalid timeout values."""
        with pytest.raises(ValueError):
            await prune_networks(timeout=invalid_timeout)

    @pytest.mark.asyncio
    async def test_prune_networks_invalid_timeout_type(self):
        """Test network pruning with invalid timeout type."""
        with pytest.raises(TypeError):
            await prune_networks(timeout="not_an_int")

    @pytest.mark.asyncio
    async def test_prune_networks_invalid_filters_type(self):
        """Test network pruning with invalid filters type."""
        with pytest.raises(TypeError):
            await prune_networks(filters="not_a_dict")

    @pytest.mark.asyncio
    async def test_prune_networks_invalid_filter_values(self):
        """Test network pruning with invalid filter values."""
        with pytest.raises(ValueError):
            await prune_networks(filters={"invalid_filter": 123})


# Ensure test output directory exists
test_output_dir = os.path.join(os.path.dirname(__file__), "test_output")
os.makedirs(test_output_dir, exist_ok=True)

# Run the tests
if __name__ == "__main__":
    output_file = os.path.join(test_output_dir, "test_prune_networks.log")
    print(f"Running tests. Output will be saved to: {os.path.abspath(output_file)}")
    pytest.main(["-v", __file__, f"--log-file={output_file}", "--log-file-level=INFO"])
