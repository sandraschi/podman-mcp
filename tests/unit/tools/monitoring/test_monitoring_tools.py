"""Unit tests for monitoring tools."""

import json
import sys
from pathlib import Path
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

# Import the modules after setting up mocks
from podmanmcp.tools.monitoring import get_monitoring_status, start_monitoring
from podmanmcp.tools.monitoring.alerts import add_alert_rule, list_alert_rules
from podmanmcp.tools.monitoring.backup import create_backup
from podmanmcp.tools.monitoring.web_interfaces import open_grafana

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
async def test_get_monitoring_status(mock_podman):
    """Test getting monitoring stack status."""
    mock_container = MagicMock()
    mock_container.name = "prometheus"
    mock_container.status = "running"
    mock_container.ports = ["0.0.0.0:9091->9090/tcp"]

    mock_podman.return_value.containers.list.return_value = [mock_container]
    result = await get_monitoring_status()

    assert result["status"] == "success"
    assert len(result.get("containers", [])) > 0
    assert any(c.get("name") == "prometheus" for c in result["containers"])


@pytest.mark.asyncio
async def test_add_alert_rule(tmp_path):
    """Test adding an alert rule."""
    test_rule = TEST_ALERT_RULE.copy()

    with patch("pathlib.Path.write_text") as mock_write, patch("pathlib.Path.mkdir") as mock_mkdir:
        result = await add_alert_rule(
            name=test_rule["name"],
            condition=test_rule["condition"],
            duration=test_rule["duration"],
            severity=test_rule["severity"],
        )

        assert result["status"] == "success"
        assert "added" in result["message"].lower()
        mock_write.assert_called_once()


@pytest.mark.asyncio
async def test_list_alert_rules():
    """Test listing alert rules."""
    test_rule = {"name": "test_rule", "condition": "up == 0", "severity": "critical"}

    with patch("pathlib.Path.glob") as mock_glob, patch("pathlib.Path.read_text") as mock_read:
        mock_glob.return_value = [Path("/path/to/rule1.json")]
        mock_read.return_value = json.dumps(test_rule)

        result = await list_alert_rules()

        assert result["status"] == "success"
        assert len(result.get("rules", [])) > 0
        assert result["rules"][0]["name"] == "test_rule"


@pytest.mark.asyncio
async def test_create_backup():
    """Test creating a backup of monitoring data."""
    with patch("tarfile.open") as mock_tar, patch("pathlib.Path.mkdir"), patch("datetime.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = "20230912_123456"
        mock_tar.return_value.__enter__.return_value = MagicMock()

        result = await create_backup()

        assert result["status"] == "success"
        assert "backup" in result
        assert "20230912_123456" in result["backup"]


@pytest.mark.asyncio
async def test_open_grafana():
    """Test opening Grafana in browser."""
    with patch("webbrowser.open") as mock_browser:
        result = await open_grafana()

        assert result["status"] == "success"
        assert "grafana" in result["url"]
        assert ":3001" in result["url"]
        mock_browser.assert_called_once()
