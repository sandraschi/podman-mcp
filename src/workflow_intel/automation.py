"""
Automation functionality for Podman MCP.
Provides tools to automate common Podman operations.
"""

import json
import time
from typing import Any

from podmanmcp.logging_config import logger
from podmanmcp.utils import run_podman_command

# Get a child logger for this module
logger = logger.getChild("automation")


class AutomationManager:
    """
    Handles automation of common Podman operations.
    """

    def restart_failed_containers(self, max_attempts: int = 3) -> dict[str, Any]:
        """
        Automatically restart containers that have failed.

        Args:
            max_attempts: Maximum number of restart attempts (default: 3)

        Returns:
            Dict containing restart results
        """
        try:
            # Get all containers using the utility function
            result = run_podman_command("ps", ["-a"], format_json=True)

            if result.returncode != 0:
                return {"success": False, "error": f"Failed to list containers: {result.stderr}"}

            containers = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    try:
                        containers.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

            # Find failed containers
            failed_containers = []
            for container in containers:
                status = container.get("Status", "")
                if "Exited" in status and "(0)" not in status:
                    failed_containers.append(container)

            if not failed_containers:
                return {"success": True, "message": "No failed containers found", "restarted": []}

            # Restart failed containers
            restart_results = []
            for container in failed_containers:
                container_id = container.get("ID", "")
                container_name = container.get("Names", "")

                for attempt in range(1, max_attempts + 1):
                    # Try to restart the container using the utility function
                    restart_result = run_podman_command("restart", [container_id], format_json=False)

                    if restart_result.returncode == 0:
                        # Verify container is running
                        time.sleep(2)  # Give it a moment to start

                        # Check container status using the utility function
                        check_result = run_podman_command(
                            "inspect", ["--format", "{{.State.Running}}", container_id], format_json=False
                        )

                        is_running = check_result.stdout.strip() == "true"

                        rst_msg = restart_result.stderr or "Successfully restarted" if is_running else "Failed to start"
                        restart_results.append(
                            {
                                "container_id": container_id,
                                "container_name": container_name,
                                "status": "restarted" if is_running else "failed",
                                "attempts": attempt,
                                "message": rst_msg,
                            }
                        )
                        break

                    if attempt < max_attempts:
                        time.sleep(1)  # Wait before retry
                else:
                    # Max attempts reached
                    restart_results.append(
                        {
                            "container_id": container_id,
                            "container_name": container_name,
                            "status": "failed",
                            "attempts": max_attempts,
                            "message": f"Failed to restart after {max_attempts} attempts: {restart_result.stderr}",
                        }
                    )

            return {
                "success": True,
                "restarted": restart_results,
                "total_failed": len(failed_containers),
                "successfully_restarted": sum(1 for r in restart_results if r["status"] == "restarted"),
            }

        except Exception as e:
            logger.error(f"Error in restart_failed_containers: {e!s}")
            return {"success": False, "error": f"Error restarting containers: {e!s}"}

    def cleanup_unused_resources(self, prune_volumes: bool = False) -> dict[str, Any]:
        """
        Clean up unused Podman resources.

        Args:
            prune_volumes: Whether to also prune volumes (default: False)

        Returns:
            Dict containing cleanup results
        """
        try:
            # Prune containers using the utility function
            container_result = run_podman_command("container", ["prune", "-f"], format_json=False)

            # Prune networks using the utility function
            network_result = run_podman_command("network", ["prune", "-f"], format_json=False)

            # Prune images using the utility function
            image_result = run_podman_command("image", ["prune", "-a", "-f"], format_json=False)

            # Prune volumes if requested using the utility function
            volume_result = None
            if prune_volumes:
                volume_result = run_podman_command("volume", ["prune", "-f"], format_json=False)

            return {
                "success": True,
                "containers_pruned": container_result.stdout,
                "networks_pruned": network_result.stdout,
                "images_pruned": image_result.stdout,
                "volumes_pruned": volume_result.stdout if volume_result else "Volume pruning skipped",
                "warnings": {
                    "containers": container_result.stderr if container_result.stderr else None,
                    "networks": network_result.stderr if network_result.stderr else None,
                    "images": image_result.stderr if image_result.stderr else None,
                    "volumes": volume_result.stderr if volume_result and volume_result.stderr else None,
                },
            }

        except Exception as e:
            logger.error(f"Error in cleanup_unused_resources: {e!s}")
            return {"success": False, "error": f"Error cleaning up resources: {e!s}"}

    def update_containers(self, container_names: list[str] | None = None) -> dict[str, Any]:
        """
        Update containers by pulling the latest images and recreating them.

        Args:
            container_names: List of container names to update (None for all)

        Returns:
            Dict containing update results
        """
        try:
            # Get all containers if none specified using the utility function
            if not container_names:
                result = run_podman_command("ps", ["--format", "{{.Names}}"], format_json=False)

                if result.returncode != 0:
                    return {"success": False, "error": f"Failed to list containers: {result.stderr}"}

                container_names = [name for name in result.stdout.strip().split("\n") if name]

            update_results = []

            for container_name in container_names:
                # Get container info using the utility function
                inspect_result = run_podman_command("inspect", [container_name], format_json=True)

                if inspect_result.returncode != 0:
                    update_results.append(
                        {
                            "container": container_name,
                            "status": "failed",
                            "error": f"Failed to inspect container: {inspect_result.stderr}",
                        }
                    )
                    continue

                try:
                    container_info = json.loads(inspect_result.stdout)[0]
                    image_name = container_info["Config"]["Image"]

                    # Pull the latest image using the utility function
                    pull_result = run_podman_command("pull", [image_name], format_json=False)

                    if pull_result.returncode != 0:
                        update_results.append(
                            {
                                "container": container_name,
                                "status": "failed",
                                "error": f"Failed to pull image: {pull_result.stderr}",
                            }
                        )
                        continue

                    # Stop and remove the old container using the utility function
                    stop_result = run_podman_command("stop", [container_name], format_json=False)

                    if stop_result.returncode != 0:
                        update_results.append(
                            {
                                "container": container_name,
                                "status": "failed",
                                "error": f"Failed to stop container: {stop_result.stderr}",
                            }
                        )
                        continue

                    # Get the original container's configuration
                    original_config = container_info["Config"]
                    original_host_config = container_info["HostConfig"]

                    # Start a new container with the same configuration
                    create_cmd = [
                        "podman",
                        "run",
                        "-d",
                        "--name",
                        container_name,
                        "--restart",
                        original_host_config.get("RestartPolicy", {}).get("Name", "no"),
                    ]

                    # Add environment variables
                    for env in original_config.get("Env", []):
                        create_cmd.extend(["-e", env])

                    # Add volumes
                    for vol in original_host_config.get("Binds", []):
                        create_cmd.extend(["-v", vol])

                    # Add ports
                    port_bindings = original_host_config.get("PortBindings", {})
                    for container_port, host_ports in port_bindings.items():
                        if host_ports:
                            host_port = host_ports[0]["HostPort"]
                            create_cmd.extend(["-p", f"{host_port}:{container_port.split('/')[0]}"])

                    # Add the image name
                    create_cmd.append(image_name)

                    # Add the original command if it exists
                    if original_config.get("Cmd"):
                        create_cmd.extend(original_config["Cmd"])

                    # Create and start the new container using the utility function
                    create_result = run_podman_command(create_cmd[0], create_cmd[1:], format_json=False)

                    if create_result.returncode == 0:
                        update_results.append(
                            {
                                "container": container_name,
                                "status": "updated",
                                "new_container_id": create_result.stdout.strip(),
                                "image": image_name,
                            }
                        )
                    else:
                        update_results.append(
                            {
                                "container": container_name,
                                "status": "failed",
                                "error": f"Failed to create new container: {create_result.stderr}",
                            }
                        )

                except (json.JSONDecodeError, KeyError, IndexError) as e:
                    update_results.append(
                        {"container": container_name, "status": "failed", "error": f"Error processing container: {e!s}"}
                    )

            return {
                "success": True,
                "results": update_results,
                "total_containers": len(container_names),
                "successful_updates": sum(1 for r in update_results if r["status"] == "updated"),
                "failed_updates": sum(1 for r in update_results if r["status"] == "failed"),
            }

        except Exception as e:
            logger.error(f"Error in update_containers: {e!s}")
            return {"success": False, "error": f"Error updating containers: {e!s}"}
