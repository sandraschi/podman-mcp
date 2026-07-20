"""
Test suite for container execution tools.

This module contains tests for executing commands inside containers.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import podman
from podmanmcp.tools.containers.container_models import ContainerExecRequest
from fastmcp.exceptions import ToolError
from pydantic import ValidationError

# Import the tools we want to test
from podmanmcp.tools.containers.container_exec import execute_in_container


class TestContainerExec(unittest.TestCase):
    """Test cases for container execution tools."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock Podman client
        self.podman_client = MagicMock(spec=podman.PodmanClient)
        self.mock_container = MagicMock()
        self.podman_client.containers.get.return_value = self.mock_container

        # Mock exec_create and exec_start
        self.mock_exec = MagicMock()
        self.mock_exec_output = b"Command output\nMultiple lines\n"
        self.mock_exec.start = AsyncMock(return_value=self.mock_exec_output)
        self.mock_container.exec_run.return_value = self.mock_exec

        # Mock for streaming
        self.mock_stream = [b"stdout output\n", b"stderr output\n", b"final output\n"]
        self.mock_container.exec_run.return_value.output = self.mock_stream

        # Patch the Podman client
        self.podman_patcher = patch("podman.from_env", return_value=self.podman_client)
        self.mock_podman = self.podman_patcher.start()

    def tearDown(self):
        """Clean up after each test."""
        self.podman_patcher.stop()

    async def test_execute_command(self):
        """Test executing a command in a container."""
        # Setup
        request = ContainerExecRequest(
            container_id="test-container",
            command="ls -la",
            workdir="/app",
            environment={"VAR1": "value1", "VAR2": "value2"},
            user="user",
            privileged=False,
            tty=False,
        )

        # Execute
        response = await execute_in_container(request)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertEqual(response["exit_code"], 0)
        self.assertEqual(response["stdout"], "Command output\nMultiple lines")
        self.assertEqual(response["stderr"], "")

        # Verify exec_run was called with correct parameters
        self.mock_container.exec_run.assert_called_once()
        args, kwargs = self.mock_container.exec_run.call_args
        self.assertEqual(args[0], "ls -la")
        self.assertEqual(kwargs["workdir"], "/app")
        self.assertEqual(kwargs["user"], "user")
        self.assertFalse(kwargs["privileged"])
        self.assertFalse(kwargs["tty"])
        self.assertIn("VAR1=value1", kwargs["environment"])
        self.assertIn("VAR2=value2", kwargs["environment"])

    async def test_execute_command_with_streaming(self):
        """Test executing a command with streaming output."""
        # Setup
        request = ContainerExecRequest(
            container_id="test-container", command="tail -f /var/log/app.log", stream=True, stream_timeout=5
        )

        # Mock the generator for streaming
        async def mock_stream():
            for chunk in self.mock_stream:
                yield chunk

        self.mock_container.exec_run.return_value.output = mock_stream()

        # Execute and collect output
        response = await execute_in_container(request)

        # Assert
        self.assertIsInstance(response, dict)
        self.assertEqual(response["exit_code"], 0)
        self.assertTrue(response["streaming"])
        self.assertIsNotNone(response["stream_id"])

    async def test_execute_command_with_error(self):
        """Test handling of command execution errors."""
        # Setup
        self.mock_container.exec_run.side_effect = podman.errors.APIError("Command failed")

        request = ContainerExecRequest(container_id="test-container", command="invalid-command")

        # Execute and assert
        with self.assertRaises(ToolError) as context:
            await execute_in_container(request)

        self.assertIn("failed to execute command", str(context.exception).lower())

    async def test_container_not_found(self):
        """Test handling of non-existent container."""
        # Setup
        self.podman_client.containers.get.side_effect = podman.errors.NotFound("Container not found")
        request = ContainerExecRequest(container_id="nonexistent-container", command="echo test")

        # Execute and assert
        with self.assertRaises(ToolError) as context:
            await execute_in_container(request)

        self.assertIn("not found", str(context.exception).lower())

    def test_request_validation(self):
        """Test validation of request parameters."""
        # Test missing required field
        with self.assertRaises(ValidationError):
            ContainerExecRequest(
                container_id="test-container"
                # Missing command
            )

        # Test invalid command type
        with self.assertRaises(ValidationError):
            ContainerExecRequest(
                container_id="test-container",
                command=["ls", "-la"],  # Should be a string
            )

        # Test valid request
        request = ContainerExecRequest(
            container_id="test-container", command="echo hello", environment={"TEST": "value"}, workdir="/app"
        )
        self.assertEqual(request.command, "echo hello")
        self.assertEqual(request.environment["TEST"], "value")
        self.assertEqual(request.workdir, "/app")


# Helper function to run async tests
if __name__ == "__main__":
    unittest.main()
