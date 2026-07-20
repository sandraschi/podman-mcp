"""
Stack health checking functionality for Podman MCP.
Provides tools to monitor and report on the health of Podman stacks.
"""

import json
from typing import Any

from podmanmcp.logging_config import logger
from podmanmcp.utils import run_podman_command

# Get a child logger for this module
logger = logger.getChild("health")


class StackHealthChecker:
    """
    Provides stack health checking functionality for Podman environments.
    """

    def check_stack_health(self, stack_name: str) -> dict[str, Any]:
        """
        Check the health of a Podman stack.

        Args:
            stack_name: Name of the stack to check

        Returns:
            Dict containing health status and details
        """
        try:
            # Get stack services using the utility function
            result = run_podman_command("stack", ["ps", stack_name], format_json=True)

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to get stack services: {result.stderr}",
                    "stack": stack_name,
                }

            # Parse service information
            services = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    services.append(json.loads(line))

            if not services:
                return {"success": False, "error": f"No services found in stack: {stack_name}", "stack": stack_name}

            # Check service status
            unhealthy_services = []
            for service in services:
                if service.get("CurrentState") != "Running":
                    unhealthy_services.append(
                        {
                            "name": service.get("Name", "unknown"),
                            "state": service.get("CurrentState", "unknown"),
                            "error": service.get("Error", ""),
                        }
                    )

            is_healthy = len(unhealthy_services) == 0

            return {
                "success": True,
                "healthy": is_healthy,
                "stack": stack_name,
                "total_services": len(services),
                "unhealthy_services": unhealthy_services,
                "unhealthy_count": len(unhealthy_services),
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse stack health data: {e}")
            return {"success": False, "error": f"Failed to parse stack health data: {e}", "stack": stack_name}
        except Exception as e:
            logger.error(f"Error checking stack health: {e!s}")
            return {"success": False, "error": f"Error checking stack health: {e!s}", "stack": stack_name}

    def get_failed_containers(self, stack_name: str) -> dict[str, Any]:
        """
        Get a list of failed containers in a stack.

        Args:
            stack_name: Name of the stack to check

        Returns:
            Dict containing failed container information
        """
        try:
            # Get running stack services using the utility function
            result = run_podman_command(
                "stack", ["ps", "--filter", "desired-state=running", stack_name], format_json=True
            )

            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Failed to get stack services: {result.stderr}",
                    "stack": stack_name,
                }

            failed_containers = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                try:
                    service = json.loads(line)
                    if service.get("CurrentState") != "Running":
                        failed_containers.append(
                            {
                                "id": service.get("ID", ""),
                                "name": service.get("Name", ""),
                                "image": service.get("Image", ""),
                                "desired_state": service.get("DesiredState", ""),
                                "current_state": service.get("CurrentState", ""),
                                "error": service.get("Error", ""),
                                "ports": service.get("Ports", ""),
                            }
                        )
                except json.JSONDecodeError:
                    continue

            return {
                "success": True,
                "stack": stack_name,
                "failed_containers": failed_containers,
                "failed_count": len(failed_containers),
            }

        except Exception as e:
            logger.error(f"Error getting failed containers: {e!s}")
            return {"success": False, "error": f"Error getting failed containers: {e!s}", "stack": stack_name}
