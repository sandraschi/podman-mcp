import shutil

"""
Tests for Podman network tools.

This module contains tests for the network management functionality in the Podman MCP.
"""

import os
import sys
from collections.abc import Callable
from typing import Any
from unittest.mock import Mock, patch

import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


# Mock FastMCP components
class ToolError(Exception):
    """Mock ToolError for testing."""

    pass


# Mock the Tool decorator
def Tool(name: str, description: str, parameters: dict[str, Any], returns: dict[str, Any], **kwargs) -> Callable:
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


# Mock the network tools module
sys.modules["fastmcp"] = Mock()
sys.modules["fastmcp.exceptions"] = Mock(ToolError=ToolError)
sys.modules["fastmcp.tools"] = Mock(Tool=Tool)

# Now import the tools to test
with patch("fastmcp.tools.Tool", Tool):
    from podmanmcp.tools.networks.network_tools import (
        connect_container_to_network,
        create_network,
        disconnect_container_from_network,
        get_network_stats,
        inspect_network,
        list_networks,
        prune_networks,
        remove_network,
    )

# Test data
TEST_NETWORK_ID = "7d86d31b1478e7cc9a2c8b8c4b982a5eafc70b5349d0d5a5875a855d0f2d2b3d"
TEST_NETWORK_NAME = "test-network"
TEST_CONTAINER_ID = "c8a8e6d5f7g9h1j2k3l4m5n6o7p8q9r0"


# Fixtures
@pytest.fixture
def mock_run_podman_command():
    """Mock the run_podman_command function."""
    with patch("podmanmcp.tools.networks.network_tools.run_podman_command") as mock:
        mock.side_effect = mock_run_podman_command
        yield mock


# Test classes
class TestPruneNetworks:
    """Tests for the prune_networks function."""

    @pytest.mark.asyncio
    async def test_prune_networks_success(self, mock_run_podman_command):
        """Test successful network pruning."""
        # Mock the Podman command response
        mock_response = {"NetworksDeleted": ["network1", "network2"], "SpaceReclaimed": 1024}
        mock_run_podman_command.return_value = mock_response

        # Call the function with a valid filter
        result = await prune_networks(filters={"until": "24h"}, force=True, timeout=30)

        # Verify the result
        assert result["success"] is True
        assert len(result["networks_deleted"]) == 2
        assert result["space_reclaimed"] == 1024
        assert "Successfully pruned 2 networks" in result["message"]

        # Verify the Podman command was called correctly
        mock_run_podman_command.assert_awaited_once()
        args, kwargs = mock_run_podman_command.await_args
        assert "network" in args[1]
        assert "prune" in args[1]
        assert "--force" in args[1]
        assert "--filter" in args[1]
        assert "until=24h" in args[1]

    @pytest.mark.asyncio
    async def test_prune_networks_no_networks(self, mock_run_podman_command):
        """Test pruning when no networks are found."""
        # Mock the Podman command response for no networks
        mock_run_podman_command.return_value = {"NetworksDeleted": None, "SpaceReclaimed": 0}

        # Call the function
        result = await prune_networks()

        # Verify the result
        assert result["success"] is True
        assert len(result["networks_deleted"]) == 0
        assert result["space_reclaimed"] == 0
        assert "No networks were pruned" in result["message"]

    @pytest.mark.asyncio
    async def test_prune_networks_timeout(self, mock_run_podman_command):
        """Test network pruning with a timeout."""
        # Mock a timeout error
        mock_run_podman_command.side_effect = TimeoutError("Operation timed out")

        # Call the function and expect an exception
        with pytest.raises(ToolError) as exc_info:
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


# Add more test classes for other network tools
class TestListNetworks:
    """Tests for the list_networks function."""

    @pytest.mark.asyncio
    async def test_list_networks_success(self, mock_run_podman_command):
        """Test successful network listing."""
        # Mock the Podman command response
        mock_response = [{"Id": TEST_NETWORK_ID, "Name": TEST_NETWORK_NAME, "Driver": "bridge", "Scope": "local"}]
        mock_run_podman_command.return_value = mock_response

        # Call the function
        result = await list_networks(verbose=True)

        # Verify the result
        assert "networks" in result
        assert len(result["networks"]) == 1
        assert result["networks"][0]["Name"] == TEST_NETWORK_NAME
        assert result["success"] is True

        # Verify the Podman command was called correctly
        mock_run_podman_command.assert_awaited_once()


class TestCreateNetwork:
    """Tests for the create_network function."""

    @pytest.mark.asyncio
    async def test_create_network_success(self, mock_run_podman_command):
        """Test successful network creation."""
        # Mock the Podman command response
        mock_response = {"Id": TEST_NETWORK_ID, "Warning": ""}
        mock_run_podman_command.return_value = mock_response

        # Call the function
        result = await create_network(name=TEST_NETWORK_NAME, driver="bridge", enable_ipv6=False)

        # Verify the result
        assert result["success"] is True
        assert "id" in result
        assert result["id"] == TEST_NETWORK_ID

        # Verify the Podman command was called correctly
        mock_run_podman_command.assert_awaited_once()


class TestRemoveNetwork:
    """Tests for the remove_network function."""

    @pytest.mark.asyncio
    async def test_remove_network_success(self, mock_run_podman_command):
        """Test successful network removal."""
        # Mock the Podman command response
        mock_run_podman_command.return_value = None  # No output on success

        # Call the function
        result = await remove_network(network_id=TEST_NETWORK_ID, force=True, timeout=30)

        # Verify the result
        assert result["success"] is True
        assert "successfully removed" in result["message"].lower()

        # Verify the Podman command was called correctly
        mock_run_podman_command.assert_awaited_once()


class TestConnectContainerToNetwork:
    """Tests for the connect_container_to_network function."""

    @pytest.mark.asyncio
    async def test_connect_container_success(self, mock_run_podman_command):
        """Test successful container connection to network."""
        # Mock the Podman command response
        mock_run_podman_command.return_value = None  # No output on success

        # Call the function
        result = await connect_container_to_network(
            container_id=TEST_CONTAINER_ID,
            network_id=TEST_NETWORK_ID,
            ipv4_address="172.20.0.2",
            aliases=["test-alias"],
            timeout=30,
        )

        # Verify the result
        assert result["success"] is True
        assert "connected" in result["message"].lower()

        # Verify the Podman command was called correctly
        mock_run_podman_command.assert_awaited_once()


class TestDisconnectContainerFromNetwork:
    """Tests for the disconnect_container_from_network function."""

    @pytest.mark.asyncio
    async def test_disconnect_container_success(self, mock_run_podman_command):
        """Test successful container disconnection from network."""
        # Mock the Podman command response
        mock_run_podman_command.return_value = None  # No output on success

        # Call the function
        result = await disconnect_container_from_network(
            container_id=TEST_CONTAINER_ID, network_id=TEST_NETWORK_ID, force=True, timeout=30
        )

        # Verify the result
        assert result["success"] is True
        assert "disconnected" in result["message"].lower()

        # Verify the Podman command was called correctly
        mock_run_podman_command.assert_awaited_once()


class TestGetNetworkStats:
    """Tests for the get_network_stats function."""

    @pytest.mark.asyncio
    async def test_get_network_stats_success(self, mock_run_podman_command):
        """Test successful retrieval of network statistics."""
        # Mock the Podman command responses
        mock_inspect_response = [
            {
                "Id": TEST_NETWORK_ID,
                "Name": TEST_NETWORK_NAME,
                "Driver": "bridge",
                "IPAM": {"Driver": "default", "Config": [{"Subnet": "172.20.0.0/16"}]},
                "Containers": {
                    TEST_CONTAINER_ID: {
                        "Name": "test-container",
                        "EndpointID": "abc123",
                        "MacAddress": "02:42:ac:14:00:02",
                        "IPv4Address": "172.20.0.2/16",
                        "IPv6Address": "",
                    }
                },
            }
        ]

        mock_stats_response = {
            "networks": {"eth0": {"rx_bytes": 1024, "rx_packets": 10, "tx_bytes": 512, "tx_packets": 5}}
        }

        # Configure the mock to return different values on subsequent calls
        mock_run_podman_command.side_effect = [
            mock_inspect_response,  # network inspect
            mock_stats_response,  # container stats
        ]

        # Call the function
        result = await get_network_stats(network_id=TEST_NETWORK_ID, verbose=True, timeout=30)

        # Verify the result
        assert result["success"] is True
        assert result["network_id"] == TEST_NETWORK_ID
        assert result["network_name"] == TEST_NETWORK_NAME
        assert len(result["containers"]) == 1
        assert "stats" in result["containers"][0]

        # Verify the Podman commands were called correctly
        assert mock_run_podman_command.await_count == 2


class TestInspectNetwork:
    """Tests for the inspect_network function."""

    @pytest.mark.asyncio
    async def test_inspect_network_success(self, mock_run_podman_command):
        """Test successful network inspection."""
        # Mock the Podman command response
        mock_response = [
            {
                "Id": TEST_NETWORK_ID,
                "Name": TEST_NETWORK_NAME,
                "Driver": "bridge",
                "IPAM": {"Driver": "default", "Config": [{"Subnet": "172.20.0.0/16"}]},
                "Containers": {},
                "Options": {},
            }
        ]
        mock_run_podman_command.return_value = mock_response

        # Call the function
        result = await inspect_network(network_id=TEST_NETWORK_ID, verbose=True)

        # Verify the result
        assert result["success"] is True
        assert result["id"] == TEST_NETWORK_ID
        assert result["name"] == TEST_NETWORK_NAME
        assert "ipam" in result

        # Verify the Podman command was called correctly
        mock_run_podman_command.assert_awaited_once()


# Helper functions for testing
def validate_network_response(response: dict[str, Any]) -> None:
    """
    Validate the structure of a network response.

    Args:
        response: The response dictionary to validate

    Raises:
        AssertionError: If the response structure is invalid
    """
    assert isinstance(response, dict), "Response must be a dictionary"
    assert "success" in response, "Response must contain 'success' key"
    assert "message" in response, "Response must contain 'message' key"
    assert isinstance(response["message"], str), "Message must be a string"

    if response["success"]:
        assert "id" in response or "networks" in response, "Successful response must contain 'id' or 'networks' key"
    else:
        assert "error" in response, "Error response must contain 'error' key"


# Skip tests if Podman is not available
pytestmark = pytest.mark.skipif(not shutil.which("podman"), reason="Podman is not available")


# Mock the run_podman_command function
def mock_run_podman_command(*args, **kwargs):
    """Mock function for run_podman_command."""
    if "network" in args[1] and "prune" in args[1]:
        return {"NetworksDeleted": ["network1", "network2"], "SpaceReclaimed": 1024}
    elif "network" in args[1] and "ls" in args[1]:
        return [{"Id": TEST_NETWORK_ID, "Name": TEST_NETWORK_NAME, "Driver": "bridge", "Scope": "local"}]
    elif "network" in args[1] and "inspect" in args[1]:
        return [
            {
                "Id": TEST_NETWORK_ID,
                "Name": TEST_NETWORK_NAME,
                "Driver": "bridge",
                "IPAM": {"Driver": "default", "Config": [{"Subnet": "172.20.0.0/16"}]},
                "Containers": {},
                "Options": {},
            }
        ]
    return None


# Ensure test output directory exists
test_output_dir = os.path.join(os.path.dirname(__file__), "test_output")
os.makedirs(test_output_dir, exist_ok=True)

# Run the tests
if __name__ == "__main__":
    output_file = os.path.join(test_output_dir, "test_network_tools.log")
    print(f"Running tests. Output will be saved to: {os.path.abspath(output_file)}")
    pytest.main(["-v", __file__, f"--log-file={output_file}", "--log-file-level=INFO"])
