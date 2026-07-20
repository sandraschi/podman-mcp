"""System, machine, volume, and network management tools for Podman MCP."""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, Literal
from pydantic import Field

from podmanmcp.mcp_instance import mcp
from podmanmcp.podman_context import check_podman_available, run_podman_command, get_podman_status
from podmanmcp.tools.utils import _error_response

logger = logging.getLogger("podmanmcp")

# FastMCP annotations
_READ_ONLY = {"readonly": True}
_MUTATING = {}
_DESTRUCTIVE = {"destructive": True}


@mcp.tool()
@check_podman_available
async def manage_system(
    operation: Annotated[
        Literal[
            "status",
            "info",
            "machine_list",
            "machine_init",
            "machine_start",
            "machine_stop",
            "prune",
            "volume_list",
            "volume_create",
            "volume_delete",
            "network_list",
            "network_create",
            "network_delete",
        ],
        Field(description="The system/machine/volume/network operation to perform"),
    ],
    name: Annotated[
        str | None,
        Field(
            description="The name of the target volume or network. Required for create/delete operations."
        ),
    ] = None,
) -> dict[str, Any]:
    """
    Manage system configuration, virtual machines, volumes, and networks in Podman.

    [RATIONALE]
    Consolidates low-level environment, machine virtualization, volume storage, and bridge 
    networking operations under a single portmanteau to prevent tool catalog explosion 
    and maintain clean context bounds.

    Operations:
    - status: Probe CLI accessibility and machine state.
    - info: Retrieve engine and system hardware configuration.
    - machine_list: List local virtual machine environments.
    - machine_init: Scaffolds a new default virtual machine.
    - machine_start: Starts the virtual machine runner.
    - machine_stop: Halts the running virtual machine.
    - prune: Prunes unused system resources (containers, networks, images).
    - volume_list: Lists all local storage volumes.
    - volume_create: Creates a new named storage volume (requires 'name').
    - volume_delete: Deletes a named storage volume (requires 'name').
    - network_list: Lists all container networks.
    - network_create: Creates a new container bridge network (requires 'name').
    - network_delete: Deletes a container network (requires 'name').

    ## Return Format
    Returns a structured dictionary with:
    - success (bool): Indication of command status.
    - message (str): Conversational summary of the action.
    - data (dict | list | None): Structured details returned by the command.

    ## Examples
    >>> await manage_system(operation="status")
    >>> await manage_system(operation="volume_create", name="my_vol")
    """
    try:
        # 1. Read-only operations
        if operation == "status":
            ctx_status = get_podman_status()
            res = await run_podman_command(["machine", "list", "--format", "json"])
            machines = []
            if res["success"] and res["stdout"].strip():
                try:
                    machines = json.loads(res["stdout"])
                except Exception:
                    pass
            
            # Count local resources
            containers_res = await run_podman_command(["ps", "-a", "--format", "json"])
            images_res = await run_podman_command(["images", "--format", "json"])
            
            containers_count = 0
            if containers_res["success"] and containers_res["stdout"].strip():
                try:
                    containers_count = len(json.loads(containers_res["stdout"]))
                except Exception:
                    pass
                    
            images_count = 0
            if images_res["success"] and images_res["stdout"].strip():
                try:
                    images_count = len(json.loads(images_res["stdout"]))
                except Exception:
                    pass

            data = {
                "podman_available": True,
                "version": ctx_status.get("version"),
                "server_version": ctx_status.get("server_version"),
                "platform": ctx_status.get("platform"),
                "machines": machines,
                "containers_count": containers_count,
                "images_count": images_count,
            }
            return {
                "success": True,
                "message": f"Podman CLI is responsive. Active machines: {len(machines)}. Running on platform: {ctx_status.get('platform')}.",
                "data": data,
            }

        elif operation == "info":
            res = await run_podman_command(["info", "--format", "json"])
            if not res["success"]:
                return _error_response(f"Failed to get system info: {res.get('stderr')}", "info_failed")
            
            info_data = {}
            if res["stdout"].strip():
                info_data = json.loads(res["stdout"])
                
            return {
                "success": True,
                "message": "Successfully retrieved system configuration details.",
                "data": info_data,
            }

        elif operation == "machine_list":
            res = await run_podman_command(["machine", "list", "--format", "json"])
            if not res["success"]:
                return _error_response(f"Failed to list machines: {res.get('stderr')}", "machine_list_failed")
            
            machines = []
            if res["stdout"].strip():
                machines = json.loads(res["stdout"])
                
            return {
                "success": True,
                "message": f"Found {len(machines)} Podman machines.",
                "data": {"machines": machines},
            }

        # 2. Machine Lifecycle operations
        elif operation == "machine_init":
            res = await run_podman_command(["machine", "init"])
            if not res["success"]:
                return _error_response(f"Failed to initialize machine: {res.get('stderr')}", "machine_init_failed")
            return {
                "success": True,
                "message": "Podman machine initialized successfully. Start it using 'machine_start'.",
                "data": {"stdout": res["stdout"]},
            }

        elif operation == "machine_start":
            res = await run_podman_command(["machine", "start"])
            if not res["success"]:
                # Check if it was already running
                if "already running" in res.get("stderr", "").lower():
                    return {
                        "success": True,
                        "message": "Podman machine is already running.",
                        "data": {"stdout": res["stdout"]},
                    }
                return _error_response(f"Failed to start machine: {res.get('stderr')}", "machine_start_failed")
            return {
                "success": True,
                "message": "Podman machine started successfully.",
                "data": {"stdout": res["stdout"]},
            }

        elif operation == "machine_stop":
            res = await run_podman_command(["machine", "stop"])
            if not res["success"]:
                return _error_response(f"Failed to stop machine: {res.get('stderr')}", "machine_stop_failed")
            return {
                "success": True,
                "message": "Podman machine stopped successfully.",
                "data": {"stdout": res["stdout"]},
            }

        elif operation == "prune":
            res = await run_podman_command(["system", "prune", "-f"])
            if not res["success"]:
                return _error_response(f"Prune failed: {res.get('stderr')}", "prune_failed")
            return {
                "success": True,
                "message": "Pruned unused system storage and processes.",
                "data": {"stdout": res["stdout"]},
            }

        # 3. Volume operations
        elif operation == "volume_list":
            res = await run_podman_command(["volume", "ls", "--format", "json"])
            if not res["success"]:
                return _error_response(f"Failed to list volumes: {res.get('stderr')}", "volume_list_failed")
            
            volumes = []
            if res["stdout"].strip():
                volumes = json.loads(res["stdout"])
                
            return {
                "success": True,
                "message": f"Found {len(volumes)} volumes.",
                "data": {"volumes": volumes},
            }

        elif operation == "volume_create":
            if not name:
                return _error_response("Operation 'volume_create' requires a 'name' parameter", "validation_failed")
            res = await run_podman_command(["volume", "create", name])
            if not res["success"]:
                return _error_response(f"Failed to create volume: {res.get('stderr')}", "volume_create_failed")
            return {
                "success": True,
                "message": f"Volume '{name}' created successfully.",
                "data": {"name": name, "stdout": res["stdout"].strip()},
            }

        elif operation == "volume_delete":
            if not name:
                return _error_response("Operation 'volume_delete' requires a 'name' parameter", "validation_failed")
            res = await run_podman_command(["volume", "rm", "-f", name])
            if not res["success"]:
                return _error_response(f"Failed to delete volume: {res.get('stderr')}", "volume_delete_failed")
            return {
                "success": True,
                "message": f"Volume '{name}' deleted successfully.",
                "data": {"name": name, "stdout": res["stdout"].strip()},
            }

        # 4. Network operations
        elif operation == "network_list":
            res = await run_podman_command(["network", "ls", "--format", "json"])
            if not res["success"]:
                return _error_response(f"Failed to list networks: {res.get('stderr')}", "network_list_failed")
            
            networks = []
            if res["stdout"].strip():
                networks = json.loads(res["stdout"])
                
            return {
                "success": True,
                "message": f"Found {len(networks)} networks.",
                "data": {"networks": networks},
            }

        elif operation == "network_create":
            if not name:
                return _error_response("Operation 'network_create' requires a 'name' parameter", "validation_failed")
            res = await run_podman_command(["network", "create", name])
            if not res["success"]:
                return _error_response(f"Failed to create network: {res.get('stderr')}", "network_create_failed")
            return {
                "success": True,
                "message": f"Network '{name}' created successfully.",
                "data": {"name": name, "stdout": res["stdout"].strip()},
            }

        elif operation == "network_delete":
            if not name:
                return _error_response("Operation 'network_delete' requires a 'name' parameter", "validation_failed")
            res = await run_podman_command(["network", "rm", "-f", name])
            if not res["success"]:
                return _error_response(f"Failed to delete network: {res.get('stderr')}", "network_delete_failed")
            return {
                "success": True,
                "message": f"Network '{name}' deleted successfully.",
                "data": {"name": name, "stdout": res["stdout"].strip()},
            }

        else:
            return _error_response(f"Unsupported operation: {operation}", "unsupported_operation")

    except Exception as e:
        return _error_response(f"System operation failed: {e!s}", "runtime_error")
