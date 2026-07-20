"""
Test suite for container inspection tools.

This module contains tests for container inspection and monitoring functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

import podman
from fastmcp.exceptions import ToolError

# Import the tools we want to test
from podmanmcp.tools.containers.container_inspect import (
    inspect_container,
)


class TestContainerInspect(unittest.TestCase):
    """Test cases for container inspection tools."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock Podman client
        self.podman_client = MagicMock(spec=podman.PodmanClient)
        self.mock_container = MagicMock()
        self.podman_client.containers.get.return_value = self.mock_container

        # Set up return values for container inspection
        self.mock_container.attrs = {
            "Id": "a1b2c3d4e5f6",
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
            "Image": "sha256:testimage123",
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

        # Mock stats generator
        self.mock_stats = iter(
            [
                {
                    "cpu_stats": {
                        "cpu_usage": {
                            "total_usage": 1000000000,
                            "usage_in_kernelmode": 200000000,
                            "usage_in_usermode": 800000000,
                        },
                        "system_cpu_usage": 5000000000,
                        "online_cpus": 4,
                        "throttling_data": {"periods": 0, "throttled_periods": 0, "throttled_time": 0},
                    },
                    "memory_stats": {
                        "usage": 10000000,
                        "max_usage": 20000000,
                        "stats": {
                            "cache": 1000000,
                            "rss": 8000000,
                            "mapped_file": 1000000,
                            "swap": 0,
                            "pgpgin": 1000,
                            "pgpgout": 900,
                            "pgfault": 100,
                            "pgmajfault": 1,
                        },
                        "limit": 2000000000,
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
                }
            ]
        )

        # Set up the stats method to return the mock stats
        self.mock_container.stats.return_value = self.mock_stats

        # Patch the Podman client
        self.podman_patcher = patch("podman.from_env", return_value=self.podman_client)
        self.mock_podman = self.podman_patcher.start()

    def tearDown(self):
        """Clean up after each test."""
        self.podman_patcher.stop()

    async def test_inspect_container_basic(self):
        """Test basic container inspection."""
        # Execute
        response = await inspect_container(container_id="test-container", show_stats=False, show_logs=False)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertEqual(response["id"], "a1b2c3d4e5f6")
        self.assertEqual(response["name"], "test-container")
        self.assertEqual(response["status"], "running")
        self.assertIsNone(response.get("stats"))
        self.assertIsNone(response.get("logs"))

    async def test_inspect_container_with_stats(self):
        """Test container inspection with stats."""
        # Execute
        response = await inspect_container(container_id="test-container", show_stats=True, show_logs=False)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIsNotNone(response.get("stats"))
        self.assertIn("cpu_percent", response["stats"])
        self.assertIn("memory_usage", response["stats"])
        self.assertIn("network_io", response["stats"])

    async def test_inspect_container_with_logs(self):
        """Test container inspection with logs."""
        # Setup
        self.mock_container.logs.return_value = b"Log line 1\nLog line 2\n"

        # Execute
        response = await inspect_container(container_id="test-container", show_stats=False, show_logs=True, log_tail=10)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertIsNotNone(response.get("logs"))
        self.assertEqual(len(response["logs"]), 2)
        self.mock_container.logs.assert_called_once_with(tail=10, timestamps=False)

    async def test_container_not_found(self):
        """Test handling of non-existent container."""
        # Setup
        self.podman_client.containers.get.side_effect = podman.errors.NotFound("Container not found")

        # Execute and assert
        with self.assertRaises(ToolError) as context:
            await inspect_container(mock_request)

        self.assertIn("not found", str(context.exception).lower())


# Helper function to run async tests
if __name__ == "__main__":
    unittest.main()
