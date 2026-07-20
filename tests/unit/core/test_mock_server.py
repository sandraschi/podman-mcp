"""Tests for the mock MCP server."""

import pytest
import requests

from tests.mocks.mock_mcp_server import MockMCPServer


def test_mock_server_basic():
    """Test basic functionality of the mock MCP server."""
    with MockMCPServer(port=8001) as server:
        # Test health check
        response = requests.get("http://localhost:8001/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "version": "1.0.0"}

        # Test listing containers (should be empty initially)
        response = requests.get("http://localhost:8001/containers")
        assert response.status_code == 200
        assert response.json() == []


def test_container_lifecycle():
    """Test container lifecycle operations."""
    with MockMCPServer(port=8001) as server:
        # Add a test container
        container_id = "test-container-1"
        server.server.RequestHandlerClass.containers[container_id] = {
            "Id": container_id,
            "Name": "/test-container",
            "Image": "alpine:latest",
            "State": {"Status": "created", "Running": False},
        }

        # Test getting container logs
        response = requests.get(f"http://localhost:8001/containers/{container_id}/logs")
        assert response.status_code == 200
        assert response.text == f"Mock logs for container {container_id}\n"

        # Test starting the container
        response = requests.post(f"http://localhost:8001/containers/{container_id}/start")
        assert response.status_code == 204

        # Verify container is running
        response = requests.get(f"http://localhost:8001/containers/{container_id}")
        assert response.status_code == 200
        container = response.json()
        assert container["State"]["Status"] == "running"
        assert container["State"]["Running"] is True


def test_image_operations():
    """Test image operations."""
    with MockMCPServer(port=8001) as server:
        # Test listing images
        response = requests.get("http://localhost:8001/images")
        assert response.status_code == 200
        initial_image_count = len(response.json())

        # Test pulling an image
        response = requests.post("http://localhost:8001/images/pull", json={"fromImage": "nginx:latest"})
        assert response.status_code == 200

        # Verify the image was added
        response = requests.get("http://localhost:8001/images")
        assert len(response.json()) == initial_image_count + 1
        assert any("nginx:latest" in img["RepoTags"][0] for img in response.json())


if __name__ == "__main__":
    # Run the tests
    import sys

    import pytest

    sys.exit(pytest.main([__file__] + sys.argv[1:]))
