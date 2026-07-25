"""Container lifecycle and status management tools for Podman MCP."""

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
async def manage_containers(
    operation: Annotated[
        Literal["list", "inspect", "start", "stop", "restart", "delete", "create", "logs", "stats", "exec", "files", "resources"],
        Field(description="The container management operation to perform"),
    ],
    container_id: Annotated[
        str | None,
        Field(
            description="Target container ID or Name. Required for inspect, start, stop, restart, delete, logs, and stats operations."
        ),
    ] = None,
    image: Annotated[
        str | None,
        Field(description="Container image reference (e.g. 'nginx:latest'). Required for 'create' operation."),
    ] = None,
    container_name: Annotated[
        str | None,
        Field(description="Optional name to assign to the new container during 'create' operation."),
    ] = None,
    ports: Annotated[
        str | None,
        Field(description="Optional port mappings (e.g. '8080:80') to publish during 'create' operation."),
    ] = None,
    volumes: Annotated[
        list[str] | None,
        Field(description="Optional storage volumes (e.g. ['my_vol:/data']) to bind during 'create' operation."),
    ] = None,
    env: Annotated[
        dict[str, str] | None,
        Field(description="Optional environment variables as key-value pairs during 'create' operation."),
    ] = None,
    cmd_args: Annotated[
        list[str] | None,
        Field(description="Optional command and arguments to pass to the container on execution during 'create'."),
    ] = None,
    tail_lines: Annotated[
        int | None,
        Field(description="Number of log lines to retrieve from the end (defaults to 100) for 'logs' operation."),
    ] = 100,
    exec_cmd: Annotated[
        list[str] | None,
        Field(description="Command and arguments to execute inside the container for 'exec' operation."),
    ] = None,
    file_op: Annotated[
        Literal["list", "read", "write"] | None,
        Field(description="File operation sub-type for 'files' operation."),
    ] = None,
    container_path: Annotated[
        str | None,
        Field(description="Path inside the container for 'files' operation."),
    ] = None,
    file_content: Annotated[
        str | None,
        Field(description="Content to write to the file for 'files' write operation."),
    ] = None,
    cpu_limit: Annotated[
        str | None,
        Field(description="CPU limit (e.g. '1.5' for 1.5 cores, or '0.5' for half a core) for 'resources' set operation."),
    ] = None,
    memory_limit: Annotated[
        str | None,
        Field(description="Memory limit (e.g. '512m', '1g') for 'resources' set operation."),
    ] = None,
    resource_op: Annotated[
        Literal["get", "set"] | None,
        Field(description="Resource operation sub-type: 'get' reads current limits, 'set' applies new limits."),
    ] = None,
) -> dict[str, Any]:
    """
    Perform CRUD and lifecycle management on Podman containers.

    [RATIONALE]
    Groups all container actions (retrieval, control, inspection, telemetry) in a single
    discriminator-based entry point. This limits context pollution for LLMs and lets them discover
    all available container features through a single schema.

    Operations:
    - list: List all containers on the host (both running and stopped).
    - inspect: Get low-level configuration of a container (requires 'container_id').
    - start: Start a stopped container (requires 'container_id').
    - stop: Stop a running container (requires 'container_id').
    - restart: Restart a running container (requires 'container_id').
    - delete: Force-delete a container (requires 'container_id').
    - create: Run a new background container (requires 'image').
    - logs: Get recent stdout/stderr output from a container (requires 'container_id').
    - stats: Fetch instant resource metrics (requires 'container_id').

    ## Return Format
    Returns a structured dictionary with:
    - success (bool): Indication of command status.
    - message (str): Conversational summary of the action.
    - data (dict | list | None): Structured details returned by the command.

    ## Examples
    >>> await manage_containers(operation="list")
    >>> await manage_containers(operation="start", container_id="my-web-app")
    >>> await manage_containers(operation="create", image="nginx:alpine", container_name="web", ports="8080:80")
    """
    try:
        # 1. Operation validation checks
        if operation in ["inspect", "start", "stop", "restart", "delete", "logs", "stats", "exec", "files", "resources"] and not container_id:
            return _error_response(
                f"Operation '{operation}' requires a 'container_id' parameter.", "validation_failed"
            )

        # 2. Execute operations
        if operation == "list":
            res = await run_podman_command(["ps", "-a", "--format", "json"])
            if not res["success"]:
                return _error_response(f"Failed to list containers: {res.get('stderr')}", "list_failed")
            
            containers = []
            if res["stdout"].strip():
                try:
                    containers = json.loads(res["stdout"])
                except Exception as parse_err:
                    logger.warning("Failed to parse containers JSON, trying fallback", error=str(parse_err))
                    
            # Map Podman JSON fields to standard representation
            mapped_containers = []
            for c in containers:
                mapped_containers.append({
                    "id": c.get("Id", c.get("ID", ""))[:12],
                    "name": c.get("Names", c.get("Name", [""]))[0] if isinstance(c.get("Names"), list) else c.get("Names", ""),
                    "image": c.get("Image", ""),
                    "status": c.get("Status", c.get("State", "")),
                    "state": c.get("State", "").lower() or c.get("Status", "").split()[0].lower(),
                    "ports": c.get("Ports", ""),
                    "created": c.get("Created", c.get("CreatedAt", "")),
                    "size": c.get("Size", ""),
                })
                
            return {
                "success": True,
                "message": f"Found {len(mapped_containers)} containers.",
                "containers": mapped_containers,  # Keep top-level keys for webapp compatibility
                "data": {"containers": mapped_containers},
            }

        elif operation == "inspect":
            res = await run_podman_command(["inspect", container_id])
            if not res["success"]:
                return _error_response(f"Failed to inspect container '{container_id}': {res.get('stderr')}", "inspect_failed")
            
            inspect_data = {}
            if res["stdout"].strip():
                try:
                    inspect_list = json.loads(res["stdout"])
                    if inspect_list:
                        inspect_data = inspect_list[0]
                except Exception:
                    pass
                    
            return {
                "success": True,
                "message": f"Successfully inspected container '{container_id}'.",
                "data": inspect_data,
            }

        elif operation == "start":
            res = await run_podman_command(["start", container_id])
            if not res["success"]:
                return _error_response(f"Failed to start container '{container_id}': {res.get('stderr')}", "start_failed")
            return {
                "success": True,
                "message": f"Container '{container_id}' started successfully.",
                "data": {"stdout": res["stdout"].strip()},
            }

        elif operation == "stop":
            res = await run_podman_command(["stop", container_id])
            if not res["success"]:
                return _error_response(f"Failed to stop container '{container_id}': {res.get('stderr')}", "stop_failed")
            return {
                "success": True,
                "message": f"Container '{container_id}' stopped successfully.",
                "data": {"stdout": res["stdout"].strip()},
            }

        elif operation == "restart":
            res = await run_podman_command(["restart", container_id])
            if not res["success"]:
                return _error_response(f"Failed to restart container '{container_id}': {res.get('stderr')}", "restart_failed")
            return {
                "success": True,
                "message": f"Container '{container_id}' restarted successfully.",
                "data": {"stdout": res["stdout"].strip()},
            }

        elif operation == "delete":
            res = await run_podman_command(["rm", "-f", container_id])
            if not res["success"]:
                return _error_response(f"Failed to delete container '{container_id}': {res.get('stderr')}", "delete_failed")
            return {
                "success": True,
                "message": f"Container '{container_id}' force-deleted successfully.",
                "data": {"stdout": res["stdout"].strip()},
            }

        elif operation == "create":
            if not image:
                return _error_response("Operation 'create' requires an 'image' parameter.", "validation_failed")
            
            run_args = ["run", "-d"]
            
            if container_name:
                run_args += ["--name", container_name]
            if ports:
                run_args += ["-p", ports]
            if volumes:
                for v in volumes:
                    run_args += ["-v", v]
            if env:
                for k, v in env.items():
                    run_args += ["-e", f"{k}={v}"]
            
            run_args.append(image)
            
            if cmd_args:
                run_args += cmd_args
                
            res = await run_podman_command(run_args)
            if not res["success"]:
                return _error_response(f"Failed to run container with image '{image}': {res.get('stderr')}", "create_failed")
                
            new_id = res["stdout"].strip()
            return {
                "success": True,
                "message": f"Container created and started in background. ID: {new_id[:12]} (Name: {container_name or 'unnamed'})",
                "data": {"container_id": new_id, "name": container_name, "image": image},
            }

        elif operation == "logs":
            log_args = ["logs"]
            if tail_lines:
                log_args += ["--tail", str(tail_lines)]
            log_args.append(container_id)
            
            res = await run_podman_command(log_args)
            if not res["success"]:
                return _error_response(f"Failed to get logs for container '{container_id}': {res.get('stderr')}", "logs_failed")
            
            # Combine stdout/stderr if separated
            logs_content = res["stdout"] + res["stderr"]
            return {
                "success": True,
                "message": f"Retrieved last {tail_lines} lines of logs for container '{container_id}'.",
                "data": {"logs": logs_content},
            }

        elif operation == "stats":
            res = await run_podman_command(["stats", "--no-stream", "--format", "json", container_id])
            if not res["success"]:
                return _error_response(f"Failed to get stats for container '{container_id}': {res.get('stderr')}", "stats_failed")
            
            stats_data = {}
            if res["stdout"].strip():
                try:
                    stats_json = json.loads(res["stdout"])
                    if isinstance(stats_json, list) and stats_json:
                        stats_data = stats_json[0]
                    else:
                        stats_data = stats_json
                except Exception:
                    pass
            return {
                "success": True,
                "message": f"Retrieved runtime metrics for container '{container_id}'.",
                "data": stats_data,
            }

        elif operation == "exec":
            if not exec_cmd:
                return _error_response("Operation 'exec' requires 'exec_cmd' parameter.", "validation_failed")
            cmd = exec_cmd
            res = await run_podman_command(["exec", container_id] + cmd, timeout=60.0)
            if not res["success"]:
                return _error_response(f"Exec failed in container '{container_id}': {res.get('stderr')}", "exec_failed")
            return {
                "success": True,
                "message": f"Command executed in container '{container_id}'.",
                "data": {"stdout": res["stdout"], "stderr": res["stderr"], "exit_code": res["returncode"]},
                "stdout": res["stdout"],
                "stderr": res["stderr"],
            }

        elif operation == "files":
            if not file_op:
                return _error_response("Operation 'files' requires 'file_op' parameter (list/read/write).", "validation_failed")
            if file_op == "list":
                target = container_path or "/"
                res = await run_podman_command(["exec", container_id, "ls", "-la", target])
                if not res["success"]:
                    return _error_response(f"Failed to list files in container '{container_id}': {res.get('stderr')}", "files_list_failed")
                return {
                    "success": True,
                    "message": f"Directory listing for '{target}' in container '{container_id}'.",
                    "data": {"path": target, "listing": res["stdout"]},
                }
            elif file_op == "read":
                if not container_path:
                    return _error_response("Operation 'files read' requires 'container_path' parameter.", "validation_failed")
                res = await run_podman_command(["exec", container_id, "cat", container_path])
                if not res["success"]:
                    return _error_response(f"Failed to read file '{container_path}' in container '{container_id}': {res.get('stderr')}", "files_read_failed")
                return {
                    "success": True,
                    "message": f"File '{container_path}' read from container '{container_id}'.",
                    "data": {"path": container_path, "content": res["stdout"]},
                }
            elif file_op == "write":
                if not container_path or file_content is None:
                    return _error_response("Operation 'files write' requires 'container_path' and 'file_content'.", "validation_failed")
                escaped = file_content.replace("\\", "\\\\").replace('"', '\\"')
                res = await run_podman_command(["exec", container_id, "sh", "-c", f'echo "{escaped}" > {container_path}'])
                if not res["success"]:
                    return _error_response(f"Failed to write file in container '{container_id}': {res.get('stderr')}", "files_write_failed")
                return {
                    "success": True,
                    "message": f"Content written to '{container_path}' in container '{container_id}'.",
                    "data": {"path": container_path},
                }
            else:
                return _error_response(f"Unsupported file operation: {file_op}", "unsupported_operation")

        elif operation == "resources":
            if not resource_op:
                return _error_response("Operation 'resources' requires 'resource_op' parameter (get/set).", "validation_failed")
            if resource_op == "get":
                res = await run_podman_command(["inspect", container_id])
                if not res["success"]:
                    return _error_response(f"Failed to inspect container '{container_id}' for resources: {res.get('stderr')}", "resources_get_failed")
                limits = {}
                try:
                    info = json.loads(res["stdout"])
                    if info and isinstance(info, list):
                        hc = info[0].get("HostConfig", {})
                        limits["cpu_shares"] = hc.get("CpuShares", 0)
                        limits["memory"] = hc.get("Memory", 0)
                        limits["memory_swap"] = hc.get("MemorySwap", 0)
                        limits["nano_cpus"] = hc.get("NanoCpus", 0)
                        si = info[0].get("State", {})
                        limits["restart_count"] = si.get("RestartCount", 0)
                        limits["oom_killed"] = si.get("OOMKilled", False)
                except Exception:
                    pass
                return {
                    "success": True,
                    "message": f"Resource limits retrieved for container '{container_id}'.",
                    "data": limits,
                }
            elif resource_op == "set":
                if not cpu_limit and not memory_limit:
                    return _error_response("Operation 'resources set' requires at least 'cpu_limit' or 'memory_limit'.", "validation_failed")
                update_args = ["update"]
                if cpu_limit:
                    update_args += ["--cpus", cpu_limit]
                if memory_limit:
                    update_args += ["--memory", memory_limit]
                update_args.append(container_id)
                res = await run_podman_command(update_args)
                if not res["success"]:
                    return _error_response(f"Failed to set resource limits on container '{container_id}': {res.get('stderr')}", "resources_set_failed")
                return {
                    "success": True,
                    "message": f"Resource limits applied to container '{container_id}'.",
                    "data": {"cpu_limit": cpu_limit, "memory_limit": memory_limit},
                }
            else:
                return _error_response(f"Unsupported resource operation: {resource_op}", "unsupported_operation")

        else:
            return _error_response(f"Unsupported operation: {operation}", "unsupported_operation")

    except Exception as e:
        return _error_response(f"Container operation failed: {e!s}", "runtime_error")
