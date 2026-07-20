"""
Problem detection functionality for Podman MCP.
Provides tools to detect and diagnose common Podman issues.
"""

import json
import re
from typing import Any

from podmanmcp.logging_config import logger
from podmanmcp.utils import run_podman_command

# Get a child logger for this module
logger = logger.getChild("problem_detection")


class ProblemDetector:
    """
    Detects and diagnoses common Podman problems.
    """

    def detect_common_issues(self) -> dict[str, Any]:
        """
        Detect common Podman issues across the system.

        Returns:
            Dict containing detected issues and recommendations
        """
        issues = []

        # Check for Podman CLI issues
        daemon_issues = self._check_daemon_issues()
        if daemon_issues:
            issues.extend(daemon_issues)

        # Check for container issues
        container_issues = self._check_container_issues()
        if container_issues:
            issues.extend(container_issues)

        # Check for image issues
        image_issues = self._check_image_issues()
        if image_issues:
            issues.extend(image_issues)

        # Check for network issues
        network_issues = self._check_network_issues()
        if network_issues:
            issues.extend(network_issues)

        # Check for volume issues
        volume_issues = self._check_volume_issues()
        if volume_issues:
            issues.extend(volume_issues)

        return {"success": True, "issues": issues, "issue_count": len(issues)}

    def _check_daemon_issues(self) -> list[dict[str, Any]]:
        """Check for Podman CLI related issues."""
        issues = []

        try:
            # Check if Podman is running using the utility function
            result = run_podman_command("info", format_json=False)

            if result.returncode != 0:
                issues.append(
                    {
                        "type": "daemon",
                        "severity": "critical",
                        "title": "Podman CLI not running",
                        "description": "The Podman CLI does not appear to be running.",
                        "recommendation": "Start the Podman service and try again.",
                    }
                )

            # Check for low disk space using the utility function
            df_result = run_podman_command("system", ["df"], format_json=True)

            if df_result.returncode == 0:
                try:
                    df_data = json.loads(f"[{df_result.stdout.replace('}\n{', '},{')}]")
                    for item in df_data:
                        if item.get("Type") == "Images" and item.get("Reclaimable", "0B") != "0B":
                            issues.append(
                                {
                                    "type": "resource",
                                    "severity": "warning",
                                    "title": "Reclaimable disk space in images",
                                    "description": f"{item.get('Reclaimable')} of disk space "
                                    "can be reclaimed from unused images.",
                                    "recommendation": 'Run "podman image prune -a" to clean up unused images.',
                                }
                            )
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            logger.error(f"Error checking daemon issues: {e!s}")

        return issues

    def _check_container_issues(self) -> list[dict[str, Any]]:
        """Check for container-related issues."""
        issues = []

        try:
            # Get all containers (including stopped ones) using the utility function
            result = run_podman_command("ps", ["-a"], format_json=True)

            if result.returncode != 0:
                return issues

            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        containers.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            # Check for exited containers
            for container in containers:
                status = container.get("Status", "")
                if "Exited" in status and "(0)" not in status:
                    exit_code = re.search(r"\(([0-9]+)\)", status)
                    exit_code = exit_code.group(1) if exit_code else "unknown"

                    # Get container logs for context using the utility function
                    log_result = run_podman_command("logs", ["--tail=20", container["ID"]], format_json=False)

                    logs = log_result.stderr or log_result.stdout or "No logs available"

                    issues.append(
                        {
                            "type": "container",
                            "severity": "error",
                            "container_id": container["ID"],
                            "container_name": container["Names"],
                            "title": f"Container {container['Names']} exited with code {exit_code}",
                            "description": f"Container exited unexpectedly with status: {status}",
                            "logs": logs.split("\n")[-10:],  # Last 10 log lines
                            "recommendation": "Check container logs and restart the container.",
                        }
                    )

            # Check for containers in restarting state
            for container in containers:
                status = container.get("Status", "")
                if "Restarting" in status:
                    issues.append(
                        {
                            "type": "container",
                            "severity": "error",
                            "container_id": container["ID"],
                            "container_name": container["Names"],
                            "title": f"Container {container['Names']} is in a restart loop",
                            "description": f"Container is constantly restarting: {status}",
                            "recommendation": "Investigate container logs and check for configuration issues.",
                        }
                    )

        except Exception as e:
            logger.error(f"Error checking container issues: {e!s}")

        return issues

    def _check_image_issues(self) -> list[dict[str, Any]]:
        """Check for image-related issues."""
        issues = []

        try:
            # Check for dangling images using the utility function
            result = run_podman_command("images", ["-f", "dangling=true", "--format", "{{.ID}}"], format_json=False)

            if result.returncode == 0 and result.stdout.strip():
                dangling_count = len([i for i in result.stdout.split("\n") if i.strip()])
                if dangling_count > 0:
                    issues.append(
                        {
                            "type": "image",
                            "severity": "warning",
                            "title": f"{dangling_count} dangling images found",
                            "description": "Dangling images are unused and taking up disk space.",
                            "recommendation": 'Run "podman image prune" to remove dangling images.',
                        }
                    )

            # Check for large images using the utility function
            result = run_podman_command(
                "images", ["--format", "{{.Size}}	{{.Repository}}:{{.Tag}}"], format_json=False
            )

            if result.returncode == 0:
                large_images = []
                for line in result.stdout.strip().split("\n"):
                    if not line.strip():
                        continue

                    try:
                        size_str, image = line.strip().split("\t", 1)
                        # Convert size to MB for comparison
                        if "GB" in size_str:
                            size_mb = float(size_str.replace("GB", "")) * 1024
                        elif "MB" in size_str:
                            size_mb = float(size_str.replace("MB", ""))
                        else:
                            continue

                        if size_mb > 500:  # Consider images > 500MB as large
                            large_images.append({"image": image, "size": size_str})
                    except (ValueError, IndexError):
                        continue

                if large_images:
                    issues.append(
                        {
                            "type": "image",
                            "severity": "info",
                            "title": f"{len(large_images)} large images found",
                            "description": "The following images are larger than 500MB "
                            "and may be using significant disk space.",
                            "details": large_images,
                            "recommendation": "Consider optimizing or removing unused large images.",
                        }
                    )

        except Exception as e:
            logger.error(f"Error checking image issues: {e!s}")

        return issues

    def _check_network_issues(self) -> list[dict[str, Any]]:
        """Check for network-related issues."""
        issues = []

        try:
            # Check for networks with no containers using the utility function
            result = run_podman_command("network", ["ls", "--format", "{{.Name}}"], format_json=False)

            if result.returncode != 0:
                return issues

            networks = [n for n in result.stdout.strip().split("\n") if n]

            for network in networks:
                if network in ["host", "none", "bridge"]:
                    continue

                # Check if network has any containers using the utility function
                containers_result = run_podman_command(
                    "network", ["inspect", "--format", "{{.Containers}}", network], format_json=False
                )

                if containers_result.returncode == 0 and not containers_result.stdout.strip():
                    issues.append(
                        {
                            "type": "network",
                            "severity": "info",
                            "title": f"Unused network: {network}",
                            "description": f'Network "{network}" has no containers attached to it.',
                            "recommendation": 'Consider removing unused networks with "podman network rm".',
                        }
                    )

        except Exception as e:
            logger.error(f"Error checking network issues: {e!s}")

        return issues

    def _check_volume_issues(self) -> list[dict[str, Any]]:
        """Check for volume-related issues."""
        issues = []

        try:
            # Check for volumes not used by any container using the utility function
            result = run_podman_command("volume", ["ls", "--format", "{{.Name}}"], format_json=False)

            if result.returncode != 0:
                return issues

            volumes = [v for v in result.stdout.strip().split("\n") if v]

            for volume in volumes:
                # Check if volume is in use using the utility function
                in_use_result = run_podman_command(
                    "ps", ["-a", "--filter", f"volume={volume}", "--format", "{{.ID}}"], format_json=False
                )

                if in_use_result.returncode == 0 and not in_use_result.stdout.strip():
                    issues.append(
                        {
                            "type": "volume",
                            "severity": "info",
                            "title": f"Unused volume: {volume}",
                            "description": f'Volume "{volume}" is not used by any container.',
                            "recommendation": 'Consider removing unused volumes with "podman volume rm".',
                        }
                    )

        except Exception as e:
            logger.error(f"Error checking volume issues: {e!s}")

        return issues
