"""
Vienna-specific functionality for Podman MCP.
Provides tools specific to Sandra's Vienna environment.
"""

import json
import socket
from typing import Any

from podmanmcp.logging_config import logger
from podmanmcp.utils import run_podman_command

# Get a child logger for this module
logger = logger.getChild("vienna")


class ViennaEnvironment:
    """
    Provides Vienna-specific functionality for Podman management.
    """

    def get_environment_status(self) -> dict[str, Any]:
        """
        Get the status of the Vienna development environment.

        Returns:
            Dict containing environment status information
        """
        try:
            # Get host information
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)

            # Get Podman system info using the utility function
            podman_info = run_podman_command("system", ["info"])

            podman_data = {}
            if podman_info.returncode == 0:
                try:
                    podman_data = json.loads(podman_info.stdout)
                except json.JSONDecodeError:
                    pass

            # Get running containers using the utility function
            containers = run_podman_command("ps")

            running_containers = []
            if containers.returncode == 0:
                for line in containers.stdout.strip().split("\n"):
                    if line:
                        try:
                            running_containers.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue

            # Check for known Vienna stacks
            known_stacks = self._check_known_stacks()

            return {
                "success": True,
                "host": {"hostname": hostname, "ip_address": ip_address},
                "podman": {
                    "version": podman_data.get("ServerVersion", "unknown"),
                    "containers": {"running": len(running_containers), "total": podman_data.get("Containers", 0)},
                    "images": podman_data.get("Images", 0),
                    "storage_driver": podman_data.get("Driver", "unknown"),
                },
                "stacks": known_stacks,
                "status": "healthy" if all(s["healthy"] for s in known_stacks.values()) else "degraded",
            }

        except Exception as e:
            logger.error(f"Error getting environment status: {e!s}")
            return {"success": False, "error": f"Error getting environment status: {e!s}"}

    def _check_known_stacks(self) -> dict[str, dict[str, Any]]:
        """
        Check the status of known Vienna stacks.

        Returns:
            Dict containing status of known stacks
        """
        stacks = {
            "veogen": {"name": "Veogen", "healthy": False, "containers": []},
            "immich": {"name": "Immich", "healthy": False, "containers": []},
            "myai": {"name": "MyAI", "healthy": False, "containers": []},
        }

        try:
            # Get all containers using the utility function
            result = run_podman_command("ps", ["-a"])

            if result.returncode != 0:
                return stacks

            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        container = json.loads(line)
                        containers.append(container)

                        # Check for Veogen stack
                        if "veogen" in container["Names"].lower():
                            stacks["veogen"]["containers"].append(
                                {
                                    "id": container["ID"],
                                    "name": container["Names"],
                                    "status": container["Status"],
                                    "healthy": "Up" in container["Status"],
                                }
                            )

                        # Check for Immich stack
                        elif "immich" in container["Names"].lower():
                            stacks["immich"]["containers"].append(
                                {
                                    "id": container["ID"],
                                    "name": container["Names"],
                                    "status": container["Status"],
                                    "healthy": "Up" in container["Status"],
                                }
                            )

                        # Check for MyAI stack
                        elif any(x in container["Names"].lower() for x in ["myai", "bob", "alice"]):
                            stacks["myai"]["containers"].append(
                                {
                                    "id": container["ID"],
                                    "name": container["Names"],
                                    "status": container["Status"],
                                    "healthy": "Up" in container["Status"],
                                }
                            )

                    except (json.JSONDecodeError, KeyError):
                        continue

            # Determine stack health
            for stack in stacks.values():
                if stack["containers"]:
                    stack["healthy"] = all(c["healthy"] for c in stack["containers"])
                else:
                    stack["healthy"] = False

            return stacks

        except Exception as e:
            logger.error(f"Error checking known stacks: {e!s}")
            return stacks

    def check_veogen_stack(self) -> dict[str, Any]:
        """
        Check the status of the Veogen stack.

        Returns:
            Dict containing Veogen stack status
        """
        try:
            stacks = self._check_known_stacks()
            veogen = stacks.get("veogen", {"name": "Veogen", "healthy": False, "containers": []})

            # Additional Veogen-specific checks can be added here

            return {
                "success": True,
                "stack": "veogen",
                "healthy": veogen["healthy"],
                "containers": veogen["containers"],
                "checks": [
                    {"name": "Containers Running", "status": "ok" if veogen["containers"] else "error"},
                    {"name": "All Containers Healthy", "status": "ok" if veogen["healthy"] else "error"},
                ],
            }

        except Exception as e:
            logger.error(f"Error checking Veogen stack: {e!s}")
            return {"success": False, "error": f"Error checking Veogen stack: {e!s}"}

    def check_immich_stack(self) -> dict[str, Any]:
        """
        Check the status of the Immich stack.

        Returns:
            Dict containing Immich stack status
        """
        try:
            stacks = self._check_known_stacks()
            immich = stacks.get("immich", {"name": "Immich", "healthy": False, "containers": []})

            # Additional Immich-specific checks can be added here

            return {
                "success": True,
                "stack": "immich",
                "healthy": immich["healthy"],
                "containers": immich["containers"],
                "checks": [
                    {"name": "Containers Running", "status": "ok" if immich["containers"] else "error"},
                    {"name": "All Containers Healthy", "status": "ok" if immich["healthy"] else "error"},
                ],
            }

        except Exception as e:
            logger.error(f"Error checking Immich stack: {e!s}")
            return {"success": False, "error": f"Error checking Immich stack: {e!s}"}

    def check_myai_stack(self) -> dict[str, Any]:
        """
        Check the status of the MyAI stack.

        Returns:
            Dict containing MyAI stack status
        """
        try:
            stacks = self._check_known_stacks()
            myai = stacks.get("myai", {"name": "MyAI", "healthy": False, "containers": []})

            # Additional MyAI-specific checks can be added here

            return {
                "success": True,
                "stack": "myai",
                "healthy": myai["healthy"],
                "containers": myai["containers"],
                "checks": [
                    {"name": "Containers Running", "status": "ok" if myai["containers"] else "error"},
                    {"name": "All Containers Healthy", "status": "ok" if myai["healthy"] else "error"},
                ],
            }

        except Exception as e:
            logger.error(f"Error checking MyAI stack: {e!s}")
            return {"success": False, "error": f"Error checking MyAI stack: {e!s}"}
