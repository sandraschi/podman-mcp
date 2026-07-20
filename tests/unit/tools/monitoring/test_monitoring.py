"""Unit tests for monitoring tools."""

import sys
from unittest.mock import MagicMock, patch

import pytest


# Mock the FastMCP Tool decorator
class MockTool:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, func):
        func._is_tool = True
        return func


# Apply the mock tool decorator
sys.modules["fastmcp"] = MagicMock()
sys.modules["fastmcp.tools"] = MagicMock()
sys.modules["fastmcp.tools.tool"] = MagicMock()
sys.modules["fastmcp.tools.tool"].Tool = MockTool

# Mock the podman module
sys.modules["podman"] = MagicMock()

# Now import the modules we want to test
from podmanmcp.tools.monitoring import MonitoringManager, start_monitoring
from podmanmcp.tools.monitoring import monitoring_status as get_monitoring_status

# Test data
TEST_ALERT_RULE = {"name": "HighCPUUsage", "condition": "avg(cpu_usage) > 80", "duration": "5m", "severity": "critical"}


@pytest.fixture
def mock_podman():
    """Fixture to mock podman client."""
    with patch("podman.from_env") as mock_podman:
        yield mock_podman


@pytest.fixture
def mock_subprocess():
    """Fixture to mock subprocess.run."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        yield mock_run


@pytest.fixture
def mock_path():
    """Fixture to mock path operations."""
    with patch("pathlib.Path") as mock_path:
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.is_file.return_value = True
        yield mock_path


@pytest.mark.asyncio
async def test_start_monitoring(mock_subprocess):
    """Test starting the monitoring stack."""
    result = await start_monitoring()

    assert result["status"] == "success"
    assert "started" in result["message"].lower()
    mock_subprocess.assert_called_once()
    assert "up -d" in " ".join(mock_subprocess.call_args[0][0])


@pytest.mark.asyncio
async def test_get_monitoring_status():
    """Test getting monitoring stack status."""
    # Mock the MonitoringManager.get_status method
    with patch.object(MonitoringManager, "get_status") as mock_get_status:
        # Setup the mock to return a successful response
        mock_get_status.return_value = {
            "status": "success",
            "stdout": "monitoring_prometheus_1|Up 5 minutes\nmonitoring_grafana_1|Up 5 minutes",
        }

        # Test the function
        result = await get_monitoring_status()

        # Assertions
        assert result["status"] == "success"
        assert len(result.get("services", [])) > 0

        # Check if the services are parsed correctly
        service_names = [s["name"] for s in result["services"] if isinstance(s, dict)]
        assert "monitoring_prometheus_1" in service_names
        assert "monitoring_grafana_1" in service_names

        # Check the status of one of the services
        prometheus = next(
            (s for s in result["services"] if isinstance(s, dict) and s.get("name") == "monitoring_prometheus_1"), None
        )
        assert prometheus is not None
        assert "status" in prometheus
        assert "Up" in prometheus["status"]


@pytest.mark.asyncio
async def test_monitoring_status_detailed():
    """Test getting detailed monitoring status."""
    # Mock the subprocess.run to return detailed container info
    with patch("subprocess.run") as mock_run:
        # Setup the mock to return a successful response with detailed info
        mock_run.return_value.stdout = "monitoring_grafana_1|Up 5 minutes (healthy)"
        mock_run.return_value.returncode = 0

        # Test the function with detailed=True
        result = await get_monitoring_status(detailed=True)

        # Assertions
        assert result["status"] == "success"
        assert len(result.get("services", [])) > 0

        # Check if the service info is in the result
        service_found = any(
            isinstance(s, dict) and "monitoring_grafana_1" in s.get("name", "") for s in result["services"]
        )
        assert service_found, "Grafana service not found in results"

        # Check if raw output is included
        assert "raw_output" in result
        assert result["raw_output"] is not None


# Add more test cases for error scenarios and edge cases

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
