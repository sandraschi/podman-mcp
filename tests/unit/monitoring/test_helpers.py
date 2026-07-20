"""Test helpers for monitoring stack tests."""

from typing import Any
from unittest.mock import MagicMock

import pytest


def mock_podman_client():
    """Create a mock Podman client for testing."""
    mock_client = MagicMock()

    # Mock containers
    mock_container = MagicMock()
    mock_container.status = "running"
    mock_container.labels = {"com.podman.compose.service": "prometheus"}
    mock_container.ports = {"9090/tcp": [{"HostIp": "0.0.0.0", "HostPort": "9091"}]}

    mock_client.containers.list.return_value = [mock_container]
    return mock_client


@pytest.fixture
def monitoring_config() -> dict[str, Any]:
    """Return a sample monitoring configuration."""
    return {
        "services": {
            "prometheus": {"ports": ["9091:9090"]},
            "grafana": {"ports": ["3001:3000"]},
            "loki": {"ports": ["3101:3100"]},
            "cadvisor": {"ports": ["8082:8080"]},
            "node-exporter": {"ports": ["9100:9100"]},
            "promtail": {},
            "redis": {"ports": ["6379:6379"]},
        }
    }
