"""
Test script for container_stats.py
"""

import asyncio
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import podman
import pytest
from podman.models.containers import Container

from podmanmcp.tools.containers.container_stats import (
    BlockIOStats,
    ContainerStats,
    ContainerStatsParams,
    ContainerStatsResponse,
    CPUStats,
    MemoryStats,
    NetworkStats,
    get_container_stats,
)

# Fixtures


@pytest.fixture
def mock_podman_container():
    """Create a mock Podman container."""
    container = MagicMock(spec=Container)
    container.id = "test-container-id"
    container.name = "test-container"
    return container


@pytest.fixture
def mock_podman_client(mock_podman_container):
    """Create a mock Podman client."""
    client = MagicMock()
    client.containers.get.return_value = mock_podman_container
    return client


# Test data
SAMPLE_STATS = {
    "cpu_stats": {
        "cpu_usage": {"total_usage": 1000000000, "usage_in_kernelmode": 100000000, "usage_in_usermode": 900000000},
        "system_cpu_usage": 5000000000,
        "online_cpus": 4,
        "throttling_data": {"periods": 0, "throttled_periods": 0, "throttled_time": 0},
    },
    "precpu_stats": {
        "cpu_usage": {"total_usage": 900000000, "usage_in_kernelmode": 90000000, "usage_in_usermode": 810000000},
        "system_cpu_usage": 4500000000,
    },
    "memory_stats": {
        "usage": 100000000,
        "max_usage": 200000000,
        "limit": 1000000000,
        "stats": {"cache": 10000000, "rss": 90000000, "swap": 0},
    },
    "networks": {
        "eth0": {
            "rx_bytes": 1000,
            "rx_packets": 10,
            "rx_errors": 0,
            "rx_dropped": 0,
            "tx_bytes": 2000,
            "tx_packets": 20,
            "tx_errors": 0,
            "tx_dropped": 0,
        }
    },
    "blkio_stats": {
        "io_service_bytes_recursive": [{"op": "Read", "value": 1000000}, {"op": "Write", "value": 500000}],
        "io_serviced_recursive": [{"op": "Read", "value": 100}, {"op": "Write", "value": 50}],
    },
    "pids_stats": {"current": 5},
}

# Tests


@pytest.mark.asyncio
async def test_get_container_stats_one_shot(mock_podman_container, mock_podman_client):
    """Test getting a single stats snapshot."""
    # Mock the container stats
    mock_podman_container.stats.return_value = SAMPLE_STATS

    # Create test params
    params = ContainerStatsParams(container_id="test-container", one_shot=True)

    # Patch podman client
    with patch("podman.from_env", return_value=mock_podman_client):
        response = await get_container_stats(params)

    # Convert to dict if it's a Pydantic model
    if hasattr(response, "model_dump"):
        result = response.model_dump()
    else:
        result = response

    # Verify results
    assert result["status"] == "success"
    assert result["container_id"] == "test-container-id"
    assert "stats" in result
    assert result["stats"]["name"] == "test-container"
    assert result["stats"]["pids"] == 5


@pytest.mark.asyncio
async def test_get_container_stats_stream(mock_podman_container, mock_podman_client):
    """Test streaming stats."""
    # Mock the container stats
    mock_podman_container.stats.return_value = SAMPLE_STATS

    # Create test params
    params = ContainerStatsParams(container_id="test-container", stream=True, interval=0.1, timeout=0.3)

    # Create a mock for the async generator
    async def mock_stats_generator():
        for _ in range(3):
            yield {"cpu": {"percent_usage": 10.5}, "memory": {"usage": 100000000}}
            await asyncio.sleep(0.1)

    # Patch the _stream_stats function to return our mock generator
    with (
        patch("podman.from_env", return_value=mock_podman_client),
        patch(
            "podmanmcp.tools.containers.container_stats._stream_stats", return_value=mock_stats_generator()
        ) as mock_stream,
    ):
        # Call the function
        response = await get_container_stats(params)

        # Convert to dict if it's a Pydantic model
        if hasattr(response, "model_dump"):
            response = response.model_dump()

        # Verify the response structure
        assert response["status"] == "success"
        assert response["container_id"] == "test-container-id"
        assert "stream" in response

        # Test the stream
        count = 0
        async for stats in response["stream"]:
            assert "cpu" in stats
            assert "memory" in stats
            count += 1

        # Should have received exactly 3 stats updates
        assert count == 3

        # Verify the mock was called with correct parameters
        mock_stream.assert_called_once_with(mock_podman_container, interval=0.1, timeout=0.3)


@pytest.mark.asyncio
async def test_get_container_stats_not_found():
    """Test error handling when container is not found."""
    # Create a mock client that raises NotFound
    mock_client = MagicMock()
    mock_client.containers.get.side_effect = podman.errors.NotFound("Container not found")

    # Create test params
    params = ContainerStatsParams(container_id="nonexistent-container")

    # Patch podman client
    with patch("podman.from_env", return_value=mock_client):
        response = await get_container_stats(params)

    # Convert to dict if it's a Pydantic model
    if hasattr(response, "model_dump"):
        result = response.model_dump()
    else:
        result = response

    # Verify error response
    assert result["status"] == "error"
    assert "not found" in result["error"].lower()


def test_container_stats_model():
    """Test ContainerStats model validation."""
    # Create a valid stats model
    stats = ContainerStats(
        container_id="test-container-id",
        name="test-container",
        timestamp=datetime.now(UTC).isoformat(),
        cpu=CPUStats(
            total_usage=1000000000,
            system_cpu_usage=5000000000,
            online_cpus=4,
            usage_in_kernelmode=100000000,
            usage_in_usermode=900000000,
            throttling_periods=0,
            throttled_time=0,
            percent_usage=20.0,
        ),
        memory=MemoryStats(
            usage=100000000,
            max_usage=200000000,
            limit=1000000000,
            percent_usage=10.0,
            cache=10000000,
            rss=90000000,
            swap=0,
        ),
        network={
            "eth0": NetworkStats(
                rx_bytes=1000,
                rx_packets=10,
                rx_errors=0,
                rx_dropped=0,
                tx_bytes=2000,
                tx_packets=20,
                tx_errors=0,
                tx_dropped=0,
            )
        },
        block_io=BlockIOStats(read_bytes=1000000, write_bytes=500000, read_ops=100, write_ops=50),
        pids=5,
        error=None,
    )

    # Convert to dict and back to validate serialization
    stats_dict = stats.model_dump()
    assert ContainerStats.model_validate(stats_dict) == stats

    # Test response model with stats
    response = ContainerStatsResponse(
        status="success", container_id="test-container-id", stats=stats_dict, stream=None, error=None
    )
    assert response.status == "success"
    assert response.container_id == "test-container-id"
    assert response.stats == stats_dict
    assert response.stream is None
    assert response.error is None
