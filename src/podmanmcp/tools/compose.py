"""Compose project management tools for Podman MCP."""

from __future__ import annotations

import json
import logging
import os
from typing import Annotated, Any, Literal
from pydantic import Field

from podmanmcp.mcp_instance import mcp
from podmanmcp.podman_context import check_podman_available, run_podman_command
from podmanmcp.tools.utils import _error_response

logger = logging.getLogger("podmanmcp")


@mcp.tool()
@check_podman_available
async def manage_compose(
    operation: Annotated[
        Literal["up", "down", "ps", "logs"],
        Field(description="The compose management operation to perform"),
    ],
    project_path: Annotated[
        str,
        Field(
            description="The filesystem directory path containing the podman-compose.yml file."
        ),
    ],
    file_name: Annotated[
        str | None,
        Field(description="Optional custom compose file name (e.g. 'podman-compose.prod.yml') if different from default."),
    ] = None,
    volumes: Annotated[
        bool | None,
        Field(description="Remove named volumes declared in the volumes section of the compose file. Applicable to 'down' operation."),
    ] = False,
) -> dict[str, Any]:
    """
    Manage multi-container stack deployments using Podman Compose.

    [RATIONALE]
    Groups all multi-container operations (compose up/down orchestration, service listing, 
    and log aggregations) under a single tool. Podman Compose manages multi-container 
    applications inside a unified project directory, which this tool exposes.

    Operations:
    - up: Builds, (re)creates, starts, and attaches to containers for a service.
    - down: Stops containers and removes containers, networks, volumes, and images created by 'up'.
    - ps: Lists containers inside the compose project scope.
    - logs: View aggregated stdout/stderr logs from the stack.

    ## Return Format
    Returns a structured dictionary with:
    - success (bool): Indication of command status.
    - message (str): Conversational summary of the action.
    - data (dict | list | None): Structured details returned by the command.

    ## Examples
    >>> await manage_compose(operation="up", project_path="d:/Dev/projects/web-stack")
    >>> await manage_compose(operation="down", project_path="d:/Dev/projects/web-stack", volumes=True)
    """
    try:
        # 1. Parameter check and path validation
        if not project_path:
            return _error_response("Parameter 'project_path' is required.", "validation_failed")

        # Resolve path
        abs_path = os.path.abspath(project_path)
        if not os.path.isdir(abs_path):
            return _error_response(
                f"Project path '{project_path}' does not exist or is not a directory. Resolved to: '{abs_path}'",
                "validation_failed",
            )

        # 2. Build base compose command
        compose_args = ["compose"]
        if file_name:
            compose_args += ["-f", file_name]

        # 3. Execute operations
        if operation == "up":
            # Run in project directory
            # timeout set to 180s for download & build
            cmd_args = compose_args + ["up", "-d"]
            
            # We must specify Cwd when running the command, but since run_podman_command runs it 
            # we can inject -C path or run it relative.
            # Podman CLI supports global option -C / --workdir to change directory!
            # Let's check: podman compose -C /path/to/project up -d
            # Yes! podman --workdir /path/to/project compose up -d is standard.
            # Wait, let's prepend --workdir to the command!
            # If we add ["--workdir", abs_path] at the very beginning of args, then it runs in that dir!
            # Wait, is --workdir a global option?
            # Yes, podman --workdir <dir> ... is a global option for podman.
            # Or we can just let it run. Let's use --workdir to make sure it's directory-independent!
            
            run_args = ["--workdir", abs_path] + cmd_args
            res = await run_podman_command(run_args, timeout=180.0)
            
            if not res["success"]:
                return _error_response(
                    f"Compose up failed: {res.get('stderr')}. Command executed: {res.get('command')}",
                    "compose_up_failed",
                )
                
            return {
                "success": True,
                "message": f"Compose stack started successfully in background for project: {abs_path}",
                "data": {"stdout": res["stdout"].strip()},
            }

        elif operation == "down":
            cmd_args = compose_args + ["down"]
            if volumes:
                cmd_args.append("-v")
                
            run_args = ["--workdir", abs_path] + cmd_args
            res = await run_podman_command(run_args, timeout=60.0)
            
            if not res["success"]:
                return _error_response(
                    f"Compose down failed: {res.get('stderr')}",
                    "compose_down_failed",
                )
                
            return {
                "success": True,
                "message": f"Compose stack stopped and cleaned up successfully for project: {abs_path}",
                "data": {"stdout": res["stdout"].strip()},
            }

        elif operation == "ps":
            cmd_args = compose_args + ["ps", "--format", "json"]
            run_args = ["--workdir", abs_path] + cmd_args
            res = await run_podman_command(run_args)
            
            if not res["success"]:
                return _error_response(
                    f"Failed to list compose status: {res.get('stderr')}",
                    "compose_ps_failed",
                )
                
            services = []
            if res["stdout"].strip():
                try:
                    services = json.loads(res["stdout"])
                except Exception:
                    pass
                    
            return {
                "success": True,
                "message": f"Found {len(services)} services in compose stack.",
                "data": {"services": services},
            }

        elif operation == "logs":
            cmd_args = compose_args + ["logs", "--tail", "100"]
            run_args = ["--workdir", abs_path] + cmd_args
            res = await run_podman_command(run_args)
            
            if not res["success"]:
                return _error_response(
                    f"Failed to get compose logs: {res.get('stderr')}",
                    "compose_logs_failed",
                )
                
            return {
                "success": True,
                "message": "Retrieved last 100 log lines from compose stack.",
                "data": {"logs": res["stdout"] + res["stderr"]},
            }

        else:
            return _error_response(f"Unsupported operation: {operation}", "unsupported_operation")

    except Exception as e:
        return _error_response(f"Compose operation failed: {e!s}", "runtime_error")
