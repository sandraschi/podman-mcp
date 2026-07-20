"""
Pytest configuration and fixtures for Podman MCP tests.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import podman
import pytest
import requests
from dotenv import load_dotenv

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default MCP server URL
DEFAULT_MCP_SERVER = "http://localhost:8000"


# Test configuration
class TestConfig:
    """Test configuration settings."""

    # Podman test settings
    TEST_CONTAINER_PREFIX = "test_podmanmcp_"
    TEST_NETWORK_NAME = "test_podmanmcp_network"
    TEST_IMAGE = "alpine:latest"  # Lightweight image for testing

    # Test timeouts (in seconds)
    CONTAINER_START_TIMEOUT = 30
    TEST_TIMEOUT = 60


# Environment variable helpers
def get_test_config() -> TestConfig:
    """Get test configuration with environment overrides."""
    config = TestConfig()

    # Allow environment overrides
    if "PODMAN_TEST_IMAGE" in os.environ:
        config.TEST_IMAGE = os.environ["PODMAN_TEST_IMAGE"]
    if "TEST_TIMEOUT" in os.environ:
        config.TEST_TIMEOUT = int(os.environ["TEST_TIMEOUT"])

    return config


# Session fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> TestConfig:
    """Provide test configuration to tests."""
    return get_test_config()


@pytest.fixture(scope="session")
def mcp_server_url():
    """Get the MCP server URL from environment or use default."""
    return os.environ.get("MCP_SERVER_URL", DEFAULT_MCP_SERVER)


def is_server_available(url):
    """Check if MCP server is available."""
    try:
        response = requests.get(f"{url}/health")
        return response.status_code == 200
    except requests.RequestException:
        return False


# Podman client fixtures
@pytest.fixture(scope="session")
def use_mock_podman() -> bool:
    """Determine whether to use mock Podman client."""
    return os.environ.get("SKIP_PODMAN_TESTS", "false").lower() == "true"


@pytest.fixture(scope="function")
async def podman_helper(test_config, use_mock_podman):
    """Fixture providing Podman test helper with automatic cleanup."""
    if use_mock_podman:
        from tests.helpers.mock_podman import MockPodmanClient

        async with MockPodmanClient() as mock_client:
            yield mock_client
    else:
        from tests.helpers.podman_helpers import PodmanTestHelper

        async with PodmanTestHelper(test_config) as helper:
            yield helper


# Mock mode fixtures
if os.environ.get("MOCK_MODE", "0") == "1" or os.environ.get("SKIP_PODMAN_TESTS", "false").lower() == "true":

    @pytest.fixture(autouse=True)
    def mock_podman():
        """Fixture to mock the Podman client when in mock mode."""
        with patch("podman.from_env") as mock_from_env, patch("aiopodman.Podman") as mock_async_podman:
            # Set up sync client mock
            mock_client = MagicMock(spec=podman.PodmanClient)
            mock_from_env.return_value = mock_client

            # Set up async client mock
            mock_async_client = AsyncMock()
            mock_async_podman.return_value = mock_async_client

            # Set up default mocks
            mock_container = MagicMock()
            mock_client.containers.get.return_value = mock_container

            # Configure container attributes
            mock_container.attrs = {
                "Id": "test-container-id",
                "Name": "test-container",
                "State": {
                    "Status": "running",
                    "Running": True,
                    "Paused": False,
                    "Restarting": False,
                    "OOMKilled": False,
                    "Dead": False,
                    "Pid": 1234,
                    "ExitCode": 0,
                    "Error": "",
                    "StartedAt": "2023-01-01T00:00:00Z",
                    "FinishedAt": "0001-01-01T00:00:00Z",
                },
                "Config": {
                    "Image": "test-image:latest",
                    "Cmd": ["/bin/sh"],
                    "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"],
                    "WorkingDir": "/app",
                    "Labels": {},
                },
                "NetworkSettings": {
                    "IPAddress": "172.17.0.2",
                    "Ports": {"80/tcp": [{"HostIp": "0.0.0.0", "HostPort": "8080"}]},
                    "Networks": {
                        "bridge": {
                            "IPAMConfig": None,
                            "Links": None,
                            "Aliases": None,
                            "NetworkID": "test-network",
                            "EndpointID": "test-endpoint",
                            "Gateway": "172.17.0.1",
                            "IPAddress": "172.17.0.2",
                            "IPPrefixLen": 16,
                            "IPv6Gateway": "",
                            "GlobalIPv6Address": "",
                            "GlobalIPv6PrefixLen": 0,
                            "MacAddress": "02:42:ac:11:00:02",
                        }
                    },
                },
            }

            # Mock container logs
            mock_container.logs.return_value = (
                b"2023-01-01T00:00:00Z Test log line 1\n2023-01-01T00:00:01Z Test log line 2\n"
            )

            # Mock exec_run
            mock_exec = MagicMock()
            mock_exec.output = [b"stdout output\n", b"stderr output\n"]
            mock_container.exec_run.return_value = mock_exec

            yield mock_client
else:

    @pytest.fixture(scope="session")
    def podman_client():
        """Fixture to provide a real Podman client."""
        client = podman.from_env()
        try:
            # Verify Podman is running
            client.ping()
            return client
        except Exception as e:
            pytest.skip(f"Podman is not available: {e}")

    @pytest.fixture(scope="session")
    def ensure_mcp_server(mcp_server_url):
        """Ensure MCP server is available before running tests."""
        if not is_server_available(mcp_server_url):
            pytest.skip(f"MCP server not available at {mcp_server_url}")
        return mcp_server_url
