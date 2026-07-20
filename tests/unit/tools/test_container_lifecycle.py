"""
Test suite for container lifecycle management tools.

This module contains tests for container lifecycle operations like create, start, stop, etc.
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from fastmcp.exceptions import ToolError
from pydantic import ValidationError

# Import the tools we want to test
try:
    # Import the module to patch the implementation
    from podmanmcp.tools.containers import container_lifecycle
    from podmanmcp.tools.containers.container_lifecycle import (
        ContainerAction,
        ContainerLifecycleRequest,
        ContainerLifecycleResponse,
        _manage_container_lifecycle_impl,  # The actual implementation function
    )

    # Create a reference to the actual implementation for use in tests
    original_impl = _manage_container_lifecycle_impl

except ImportError as e:
    print(f"Error importing modules: {e}")
    raise

# Test constants
TEST_CONTAINER_ID = "test-container-id"
TEST_CONTAINER_NAME = "test-container"
TEST_IMAGE = "test-image:latest"


class TestContainerLifecycle(unittest.IsolatedAsyncioTestCase):
    """Test cases for container lifecycle management tools."""

    async def asyncSetUp(self):
        """Set up test fixtures."""
        # Create a mock Podman client
        self.podman_client = MagicMock()
        self.mock_container = MagicMock()
        self.mock_container.id = TEST_CONTAINER_ID
        self.mock_container.name = TEST_CONTAINER_NAME
        self.mock_container.status = "running"

        # Configure the container mock
        self.mock_container.attrs = {
            "Id": TEST_CONTAINER_ID,
            "Name": TEST_CONTAINER_NAME,
            "State": {
                "Status": "running",
                "Running": True,
                "Paused": False,
                "Restarting": False,
                "OOMKilled": False,
                "Dead": False,
                "Pid": 12345,
                "ExitCode": 0,
                "Error": "",
                "StartedAt": "2023-01-01T00:00:00Z",
                "FinishedAt": "0001-01-01T00:00:00Z",
            },
            "Config": {"Image": TEST_IMAGE, "Labels": {}, "Env": []},
            "Image": "sha256:test123",
        }

        # Add reload method to the mock container
        def reload_mock():
            # Update the status based on the last operation
            if hasattr(self.mock_container, "paused") and self.mock_container.paused:
                self.mock_container.status = "paused"
                self.mock_container.attrs["State"]["Paused"] = True
                self.mock_container.attrs["State"]["Running"] = True
            elif hasattr(self.mock_container, "stopped") and self.mock_container.stopped:
                self.mock_container.status = "exited"
                self.mock_container.attrs["State"]["Running"] = False
            else:
                self.mock_container.status = "running"
                self.mock_container.attrs["State"]["Running"] = True
                self.mock_container.attrs["State"]["Paused"] = False

        self.mock_container.reload = MagicMock(side_effect=reload_mock)

        # Patch the Podman client
        self.podman_patcher = patch("podman.from_env", return_value=self.podman_client)
        self.mock_podman = self.podman_patcher.start()

        # Set up the mock to return our test container
        self.podman_client.containers.get.return_value = self.mock_container

        # Patch the _manage_container_lifecycle_impl function
        self.original_impl = container_lifecycle._manage_container_lifecycle_impl

        # Create a wrapper to track calls to the implementation
        async def wrapped_impl(params):
            # Update the mock container state based on the action
            if params.action == "start":
                self.mock_container.stopped = False
                self.mock_container.paused = False
            elif params.action == "stop":
                self.mock_container.stopped = True
            elif params.action == "pause":
                self.mock_container.paused = True
            elif params.action == "unpause":
                self.mock_container.paused = False

            # Call the original implementation
            return await self.original_impl(params)

        # Apply the patch
        container_lifecycle._manage_container_lifecycle_impl = wrapped_impl

    async def asyncTearDown(self):
        """Clean up after each test."""
        # Restore the original implementation
        container_lifecycle._manage_container_lifecycle_impl = self.original_impl

        # Stop the Podman client patch
        self.podman_patcher.stop()

        # Reset the container state
        self.mock_container.attrs = {
            "Id": TEST_CONTAINER_ID,
            "Name": TEST_CONTAINER_NAME,
            "State": {
                "Status": "running",
                "Running": True,
                "Paused": False,
                "Restarting": False,
                "OOMKilled": False,
                "Dead": False,
                "Pid": 12345,
                "ExitCode": 0,
                "Error": "",
                "StartedAt": "2023-01-01T00:00:00Z",
                "FinishedAt": "0001-01-01T00:00:00Z",
            },
            "Config": {"Image": TEST_IMAGE, "Labels": {}, "Env": []},
            "Image": "sha256:test123",
        }

        # Reset any custom attributes
        if hasattr(self.mock_container, "paused"):
            delattr(self.mock_container, "paused")
        if hasattr(self.mock_container, "stopped"):
            delattr(self.mock_container, "stopped")

        # Set up the Podman client mock
        self.podman_client.containers.get.return_value = self.mock_container

        # Patch the Podman client
        self.podman_patcher = patch("podman.from_env", return_value=self.podman_client)
        self.mock_podman = self.podman_patcher.start()

        # Import the module after patching
        global manage_container_lifecycle, ContainerLifecycleRequest, ContainerAction
        from podmanmcp.tools.containers.container_lifecycle import (
            ContainerAction,
            ContainerLifecycleRequest,
            manage_container_lifecycle,
        )

    def tearDown(self):
        """Clean up after each test."""
        self.podman_patcher.stop()

    async def test_start_container(self):
        """Test starting a container."""
        # Set initial state: container is stopped
        self.mock_container.attrs["State"]["Running"] = False
        self.mock_container.status = "exited"

        # Create the request
        request = ContainerLifecycleRequest(container_id=TEST_CONTAINER_ID, action=ContainerAction.START)

        # Call the implementation directly for testing
        response = await container_lifecycle._manage_container_lifecycle_impl(request)

        # Verify the response
        self.assertIsInstance(response, dict)
        self.assertEqual(response["action"], "start")
        self.assertEqual(response["container_id"], TEST_CONTAINER_ID)
        self.assertTrue(response["success"])

        # Verify the container was started
        self.mock_container.start.assert_called_once()

        # Verify the container state was updated
        self.assertTrue(self.mock_container.attrs["State"]["Running"])
        self.podman_client.containers.get.assert_called_once_with(TEST_CONTAINER_ID)

        # Test 2: Start already running container
        self.mock_container.start.reset_mock()
        self.mock_container.attrs["State"]["Running"] = True

        response = await manage_container_lifecycle(request)
        self.assertTrue(response["success"])
        self.mock_container.start.assert_not_called()

        # Test 3: Start with custom timeout
        self.mock_container.start.reset_mock()
        self.mock_container.attrs["State"]["Running"] = False

        request = ContainerLifecycleRequest(container_id=TEST_CONTAINER_ID, action=ContainerAction.START, timeout=30)

        await manage_container_lifecycle(request)
        self.mock_container.start.assert_called_once()

    async def test_stop_container(self):
        """Test stopping a container."""
        # Set initial state: container is running
        self.mock_container.attrs["State"]["Running"] = True
        self.mock_container.status = "running"

        # Create the request with a custom timeout
        request = ContainerLifecycleRequest(container_id=TEST_CONTAINER_ID, action=ContainerAction.STOP, timeout=10)

        # Execute - use the implementation directly for testing
        response = await container_lifecycle._manage_container_lifecycle_impl(request)

        # Verify the response
        self.assertIsInstance(response, dict)
        self.assertEqual(response["action"], "stop")
        self.assertTrue(response["success"])

        # Verify the container was stopped with the correct timeout
        self.mock_container.stop.assert_called_once_with(timeout=10)

        # Test stopping an already stopped container
        self.mock_container.stop.reset_mock()
        self.mock_container.attrs["State"]["Running"] = False

        response = await container_lifecycle._manage_container_lifecycle_impl(request)
        self.assertTrue(response["success"])
        self.mock_container.stop.assert_not_called()

    async def test_restart_container(self):
        """Test restarting a container."""
        # Set initial state: container is running
        self.mock_container.attrs["State"]["Running"] = True
        self.mock_container.status = "running"

        # Create the request with a custom timeout
        request = ContainerLifecycleRequest(container_id=TEST_CONTAINER_ID, action=ContainerAction.RESTART, timeout=5)

        # Execute - use the implementation directly for testing
        response = await container_lifecycle._manage_container_lifecycle_impl(request)

        # Verify the response
        self.assertIsInstance(response, dict)
        self.assertEqual(response["action"], "restart")
        self.assertTrue(response["success"])

        # Verify the container was restarted with the correct timeout
        self.mock_container.restart.assert_called_once_with(timeout=5)

        # Test restarting a stopped container
        self.mock_container.restart.reset_mock()
        self.mock_container.attrs["State"]["Running"] = False

        response = await container_lifecycle._manage_container_lifecycle_impl(request)
        self.assertTrue(response["success"])
        self.mock_container.restart.assert_called_once()  # Should still call restart even if container is stopped

    async def test_remove_container(self):
        """Test removing a container."""
        # Set initial state: container is stopped
        self.mock_container.attrs["State"]["Running"] = False
        self.mock_container.status = "exited"

        # Test force remove on stopped container
        request = ContainerLifecycleRequest(
            container_id=TEST_CONTAINER_ID, action=ContainerAction.REMOVE, force=True, remove_volumes=True
        )

        # Execute - use the implementation directly for testing
        response = await container_lifecycle._manage_container_lifecycle_impl(request)

        # Verify the response
        self.assertIsInstance(response, dict)
        self.assertEqual(response["action"], "remove")
        self.assertTrue(response["success"])

        # Verify the container was removed with force and volume removal
        self.mock_container.remove.assert_called_once_with(force=True, v=True)

    async def test_container_in_abnormal_state(self):
        """Test handling of containers in various abnormal states."""
        # Test with paused container
        self.mock_container.paused = True
        self.mock_container.attrs["State"]["Paused"] = True
        self.mock_container.attrs["State"]["Running"] = True
        self.mock_container.status = "paused"

        request = ContainerLifecycleRequest(container_id=TEST_CONTAINER_ID, action=ContainerAction.START)

        response = await container_lifecycle._manage_container_lifecycle_impl(request)
        self.assertTrue(response["success"])
        self.mock_container.unpause.assert_called_once()
        self.assertFalse(hasattr(self.mock_container, "paused"))  # Should be removed by the wrapper

        # Test with dead container
        self.mock_container.attrs["State"]["Dead"] = True
        self.mock_container.attrs["State"]["Running"] = False
        self.mock_container.status = "dead"

        with self.assertRaises(ToolError) as context:
            await container_lifecycle._manage_container_lifecycle_impl(request)
        self.assertIn("dead", str(context.exception).lower())

    async def test_force_remove_container(self):
        """Test force removal of a running container."""
        # Test force remove on running container
        self.mock_container.attrs["State"]["Running"] = True
        self.mock_container.status = "running"

        request = ContainerLifecycleRequest(container_id=TEST_CONTAINER_ID, action=ContainerAction.REMOVE, force=True)

        response = await container_lifecycle._manage_container_lifecycle_impl(request)
        self.assertTrue(response["success"])
        self.mock_container.remove.assert_called_once_with(force=True, v=False)

    async def test_restart_policies(self):
        """Test container restart with different policies."""
        # Test with default policy (no restart)
        request = ContainerLifecycleRequest(container_id=TEST_CONTAINER_ID, action=ContainerAction.RESTART)

        # Call the implementation directly for testing
        response = await container_lifecycle._manage_container_lifecycle_impl(request)
        self.assertTrue(response["success"])
        self.mock_container.restart.assert_called_once_with(timeout=10)  # Default timeout

        # Test with custom timeout
        self.mock_container.restart.reset_mock()

        request = ContainerLifecycleRequest(container_id=TEST_CONTAINER_ID, action=ContainerAction.RESTART, timeout=5)

        # Call the implementation directly for testing
        response = await container_lifecycle._manage_container_lifecycle_impl(request)
        self.assertTrue(response["success"])
        self.mock_container.restart.assert_called_once_with(timeout=5)

    async def test_invalid_parameters(self):
        """Test validation of request parameters."""
        # Test invalid action
        with self.assertRaises(ValidationError):
            ContainerLifecycleRequest(container_id="test-container", action="invalid_action")

        # Test missing container_id
        with self.assertRaises(ValidationError):
            ContainerLifecycleRequest(action=ContainerAction.START)

        # Test invalid timeout (should be ge 0)
        with self.assertRaises(ValidationError):
            ContainerLifecycleRequest(
                container_id="test-container",
                action=ContainerAction.START,
                timeout=-1,  # Invalid timeout
            )

    async def test_concurrent_operations(self):
        """Test handling of concurrent operations on the same container."""

        # Simulate a slow operation
        async def slow_start():
            await asyncio.sleep(0.1)
            return {"status": "started"}

        # Configure the mock to simulate a slow start
        self.mock_container.start = AsyncMock(side_effect=slow_start)

        # Create a lock to simulate the container being locked during operations
        operation_lock = asyncio.Lock()

        async def run_operation():
            # Simulate acquiring a lock on the container
            async with operation_lock:
                request = ContainerLifecycleRequest(container_id=TEST_CONTAINER_ID, action=ContainerAction.START)
                return await container_lifecycle._manage_container_lifecycle_impl(request)

        # Start multiple operations concurrently
        tasks = [run_operation() for _ in range(3)]
        responses = await asyncio.gather(*tasks)

        # Verify all operations completed successfully
        self.assertEqual(len(responses), 3)
        for response in responses:
            self.assertTrue(response["success"])
            self.assertEqual(response["container_id"], TEST_CONTAINER_ID)

        # Verify the container was started once for each operation
        # (In a real scenario, you might want to implement operation deduplication)
        self.assertEqual(self.mock_container.start.call_count, 3)


# Helper function to run async tests
if __name__ == "__main__":
    unittest.main()
