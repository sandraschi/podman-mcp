"""Pod management tools for Podman MCP."""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, Literal
from pydantic import Field

from podmanmcp.mcp_instance import mcp
from podmanmcp.podman_context import check_podman_available, run_podman_command
from podmanmcp.tools.utils import _error_response

logger = logging.getLogger("podmanmcp")


@mcp.tool()
@check_podman_available
async def manage_pods(
    operation: Annotated[
        Literal["list", "inspect", "create", "start", "stop", "delete"],
        Field(description="The pod management operation to perform"),
    ],
    pod_id: Annotated[
        str | None,
        Field(
            description="Target Pod ID or Name. Required for inspect, start, stop, and delete operations."
        ),
    ] = None,
    pod_name: Annotated[
        str | None,
        Field(description="Optional name to assign to the new pod during 'create' operation."),
    ] = None,
    ports: Annotated[
        str | None,
        Field(description="Optional port mappings (e.g. '8080:80') to publish for the new pod during 'create'."),
    ] = None,
) -> dict[str, Any]:
    """
    Manage Podman Pods (groups of one or more shared-namespace containers).

    [RATIONALE]
    Pods are a primary feature of Podman, allowing developers to group containers 
    that share localhost network namespaces (mimicking Kubernetes Pods). 
    This tool groups all pod operations to make them easily discoverable.

    Operations:
    - list: List all pods running on the host.
    - inspect: Fetch detailed JSON metadata about a pod (requires 'pod_id').
    - create: Create a empty pod namespace shell (requires 'pod_name').
    - start: Start all containers grouped inside the pod (requires 'pod_id').
    - stop: Stop all containers grouped inside the pod (requires 'pod_id').
    - delete: Remove the pod and its containers (requires 'pod_id').

    ## Return Format
    Returns a structured dictionary with:
    - success (bool): Indication of command status.
    - message (str): Conversational summary of the action.
    - data (dict | list | None): Structured details returned by the command.

    ## Examples
    >>> await manage_pods(operation="list")
    >>> await manage_pods(operation="create", pod_name="backend-stack", ports="8080:80")
    >>> await manage_pods(operation="start", pod_id="backend-stack")
    """
    try:
        # 1. Operation validation checks
        if operation in ["inspect", "start", "stop", "delete"] and not pod_id:
            return _error_response(
                f"Operation '{operation}' requires a 'pod_id' parameter.", "validation_failed"
            )

        # 2. Execute operations
        if operation == "list":
            res = await run_podman_command(["pod", "ps", "--format", "json"])
            if not res["success"]:
                return _error_response(f"Failed to list pods: {res.get('stderr')}", "list_failed")
            
            pods = []
            if res["stdout"].strip():
                try:
                    pods = json.loads(res["stdout"])
                except Exception as parse_err:
                    logger.warning("Failed to parse pods JSON", error=str(parse_err))
                    
            return {
                "success": True,
                "message": f"Found {len(pods)} pods.",
                "pods": pods,  # Kept at top level for dashboard compatibility
                "data": {"pods": pods},
            }

        elif operation == "inspect":
            res = await run_podman_command(["pod", "inspect", pod_id])
            if not res["success"]:
                return _error_response(f"Failed to inspect pod '{pod_id}': {res.get('stderr')}", "inspect_failed")
            
            inspect_data = {}
            if res["stdout"].strip():
                try:
                    inspect_list = json.loads(res["stdout"])
                    if inspect_list:
                        inspect_data = inspect_list
                except Exception:
                    pass
            return {
                "success": True,
                "message": f"Successfully inspected pod '{pod_id}'.",
                "data": inspect_data,
            }

        elif operation == "create":
            if not pod_name:
                return _error_response("Operation 'create' requires a 'pod_name' parameter.", "validation_failed")
            
            run_args = ["pod", "create", "--name", pod_name]
            if ports:
                run_args += ["-p", ports]
                
            res = await run_podman_command(run_args)
            if not res["success"]:
                return _error_response(f"Failed to create pod '{pod_name}': {res.get('stderr')}", "create_failed")
                
            pod_id_created = res["stdout"].strip()
            return {
                "success": True,
                "message": f"Pod '{pod_name}' created successfully. ID: {pod_id_created[:12]}",
                "data": {"pod_id": pod_id_created, "name": pod_name, "ports": ports},
            }

        elif operation == "start":
            res = await run_podman_command(["pod", "start", pod_id])
            if not res["success"]:
                return _error_response(f"Failed to start pod '{pod_id}': {res.get('stderr')}", "start_failed")
            return {
                "success": True,
                "message": f"Pod '{pod_id}' started successfully.",
                "data": {"stdout": res["stdout"].strip()},
            }

        elif operation == "stop":
            res = await run_podman_command(["pod", "stop", pod_id])
            if not res["success"]:
                return _error_response(f"Failed to stop pod '{pod_id}': {res.get('stderr')}", "stop_failed")
            return {
                "success": True,
                "message": f"Pod '{pod_id}' stopped successfully.",
                "data": {"stdout": res["stdout"].strip()},
            }

        elif operation == "delete":
            res = await run_podman_command(["pod", "rm", "-f", pod_id])
            if not res["success"]:
                return _error_response(f"Failed to delete pod '{pod_id}': {res.get('stderr')}", "delete_failed")
            return {
                "success": True,
                "message": f"Pod '{pod_id}' force-deleted successfully.",
                "data": {"stdout": res["stdout"].strip()},
            }

        else:
            return _error_response(f"Unsupported operation: {operation}", "unsupported_operation")

    except Exception as e:
        return _error_response(f"Pod operation failed: {e!s}", "runtime_error")
