"""
Test suite for container logs tools.

This module contains tests for container log retrieval and streaming.
"""

import unittest
from unittest.mock import MagicMock, patch

import podman
from podmanmcp.tools.containers.container_models import ContainerLogsRequest
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

# Import the tools we want to test
from podmanmcp.tools.containers.container_logs import _parse_log_entry, get_container_logs, stream_container_logs


class TestContainerLogs(unittest.TestCase):
    """Test cases for container logs tools."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock Podman client
        self.podman_client = MagicMock(spec=podman.PodmanClient)
        self.mock_container = MagicMock()
        self.podman_client.containers.get.return_value = self.mock_container

        # Mock log data
        self.mock_logs = b"2023-01-01T00:00:00Z Log line 1\n2023-01-01T00:00:01Z Log line 2\n"
        self.mock_container.logs.return_value = self.mock_logs

        # Mock for streaming
        self.mock_stream = [
            b"2023-01-01T00:00:00Z Log line 1\n",
            b"2023-01-01T00:00:01Z Log line 2\n",
            b"2023-01-01T00:00:02Z Log line 3\n",
        ]

        # Patch the Podman client
        self.podman_patcher = patch("podman.from_env", return_value=self.podman_client)
        self.mock_podman = self.podman_patcher.start()

    def tearDown(self):
        """Clean up after each test."""
        self.podman_patcher.stop()

    async def test_get_container_logs(self):
        """Test retrieving container logs."""
        # Setup
        request = ContainerLogsRequest(
            container_id="test-container", tail=100, since="1h", until="now", timestamps=True, follow=False
        )

        # Execute
        response = await get_container_logs(request)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertEqual(len(response["logs"]), 2)
        self.assertEqual(response["container_id"], "test-container")
        self.mock_container.logs.assert_called_once_with(
            tail=100, since="1h", until="now", timestamps=True, follow=False, stream=False
        )

    async def test_stream_container_logs(self):
        """Test streaming container logs."""

        # Setup mock for streaming
        async def mock_stream():
            for chunk in self.mock_stream:
                yield chunk

        self.mock_container.logs.return_value = mock_stream()

        request = ContainerLogsRequest(container_id="test-container", follow=True, tail=10)

        # Collect all log entries
        logs = []
        async for log_entry in stream_container_logs(request):
            logs.append(log_entry)

        # Assert
        self.assertEqual(len(logs), 3)
        self.assertIn("Log line 1", logs[0]["message"])
        self.assertIn("Log line 2", logs[1]["message"])
        self.mock_container.logs.assert_called_once_with(
            tail=10, since=None, until=None, timestamps=True, follow=True, stream=True
        )

    async def test_log_parsing(self):
        """Test parsing of log entries with different formats."""
        # Test with timestamps

        # Test Podman log format with timestamp
        timestamp, message = _parse_log_entry(b"2023-01-01T00:00:00.123456Z This is a log message\n")
        self.assertEqual(timestamp, "2023-01-01T00:00:00.123456Z")
        self.assertEqual(message, "This is a log message")

        # Test without timestamp
        timestamp, message = _parse_log_entry(b"This is a log message without timestamp\n")
        self.assertIsNotNone(timestamp)  # Should use current time
        self.assertEqual(message, "This is a log message without timestamp")

    async def test_container_not_found(self):
        """Test handling of non-existent container."""
        # Setup
        self.podman_client.containers.get.side_effect = podman.errors.NotFound("Container not found")

        request = ContainerLogsRequest(container_id="nonexistent-container")

        # Execute and assert
        with self.assertRaises(ToolError) as context:
            await get_container_logs(request)

        self.assertIn("not found", str(context.exception).lower())

    def test_request_validation(self):
        """Test validation of request parameters."""
        # Test missing required field
        with self.assertRaises(ValidationError):
            ContainerLogsRequest(
                # Missing container_id
                tail=100
            )

        # Test invalid tail value
        with self.assertRaises(ValidationError):
            ContainerLogsRequest(
                container_id="test-container",
                tail=-1,  # Must be >= 0
            )

        # Test valid request
        request = ContainerLogsRequest(container_id="test-container", tail=50, since="2h", until="now", timestamps=True)
        self.assertEqual(request.container_id, "test-container")
        self.assertEqual(request.tail, 50)
        self.assertEqual(request.since, "2h")
        self.assertEqual(request.until, "now")
        self.assertTrue(request.timestamps)


# Helper function to run async tests
if __name__ == "__main__":
    unittest.main()
