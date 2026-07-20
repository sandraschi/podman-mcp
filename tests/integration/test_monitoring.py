"""Integration tests for monitoring stack."""

import time
from typing import Any

import pytest
import requests

# Test configuration
SERVICES = [
    {"name": "prometheus", "port": 9091, "path": "/-/healthy"},
    {"name": "grafana", "port": 3001, "path": "/api/health"},
    {"name": "loki", "port": 3101, "path": "/ready"},
    {"name": "cadvisor", "port": 8082, "path": "/healthz"},
    {"name": "node-exporter", "port": 9100, "path": ""},
    {"name": "redis", "port": 6379, "path": ""},
]


def is_service_healthy(url: str, timeout: int = 5) -> bool:
    """Check if a service is healthy by making an HTTP request."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code in (200, 204)
    except (requests.RequestException, ConnectionError):
        return False


@pytest.mark.integration
class TestMonitoringStack:
    """Integration tests for the monitoring stack."""

    @pytest.mark.parametrize("service", SERVICES)
    def test_service_running(self, service: dict[str, Any]):
        """Test that each monitoring service is running and accessible."""
        # Skip path check for services that don't have a health endpoint
        if not service["path"]:
            return

        url = f"http://localhost:{service['port']}{service['path']}"
        assert is_service_healthy(url), f"{service['name']} is not accessible at {url}"

    def test_prometheus_targets(self):
        """Test that Prometheus is scraping all configured targets."""
        url = "http://localhost:9091/api/v1/targets"

        # Give Prometheus time to discover targets
        time.sleep(5)

        response = requests.get(url)
        assert response.status_code == 200, "Failed to fetch Prometheus targets"

        data = response.json()
        assert data["status"] == "success", "Prometheus API returned error status"

        # Check that we have active targets
        active_targets = [t for t in data["data"]["activeTargets"] if t["health"] == "up"]
        assert len(active_targets) > 0, "No active Prometheus targets found"

    def test_grafana_datasources(self):
        """Test that Grafana has the expected datasources configured."""
        url = "http://admin:admin@localhost:3001/api/datasources"

        response = requests.get(url)
        assert response.status_code == 200, "Failed to fetch Grafana datasources"

        datasources = response.json()
        expected_datasources = ["Prometheus", "Loki"]

        for ds in expected_datasources:
            assert any(d["type"] == ds.lower() for d in datasources), f"{ds} datasource not found in Grafana"

    def test_loki_logs(self):
        """Test that Loki is receiving logs from Promtail."""
        # This is a basic test - in a real scenario, you'd want to verify
        # that logs are actually being ingested
        url = "http://localhost:3101/loki/api/v1/labels"

        response = requests.get(url)
        assert response.status_code == 200, "Failed to fetch Loki labels"

        data = response.json()
        assert data["status"] == "success", "Loki API returned error status"
        assert "values" in data["data"], "No labels found in Loki"


@pytest.mark.integration
class TestMonitoringTools:
    """Integration tests for monitoring tools."""

    def test_alert_rule_management(self):
        """Test adding and listing alert rules."""
        import asyncio

        from podmanmcp.tools.monitoring.alerts import add_alert_rule, list_alert_rules

        # Test adding a rule
        add_result = asyncio.run(
            add_alert_rule(name="TestRule", condition="up == 0", duration="1m", severity="warning")
        )

        assert add_result["status"] == "success", "Failed to add alert rule"

        # Test listing rules
        list_result = asyncio.run(list_alert_rules())
        assert list_result["status"] == "success", "Failed to list alert rules"
        assert any(r["name"] == "TestRule" for r in list_result["rules"]), "Added rule not found in list"

    def test_backup_restore(self):
        """Test backup and restore functionality."""
        import asyncio
        import os

        from podmanmcp.tools.monitoring.backup import create_backup, restore_backup

        # Create a backup
        backup_result = asyncio.run(create_backup())
        assert backup_result["status"] == "success", "Failed to create backup"
        assert os.path.exists(backup_result["backup"]), "Backup file not created"

        # Test restore (just verify the function runs, actual restore would need more setup)
        restore_result = asyncio.run(restore_backup(backup_result["backup"]))
        assert restore_result["status"] == "success", "Failed to restore backup"

        # Cleanup
        if os.path.exists(backup_result["backup"]):
            os.remove(backup_result["backup"])
