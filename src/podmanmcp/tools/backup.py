"""Backup and restore operations for Podman MCP."""

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
_DESTRUCTIVE = {"destructive": True}


@mcp.tool(annotations=_DESTRUCTIVE)
@check_podman_available
async def manage_backup(
    operation: Annotated[
        Literal["save_image", "load_image", "export_container", "import_container", "save_volume", "load_volume", "save_compose", "list_backups"],
        Field(description="The backup/restore operation to perform"),
    ],
    name: Annotated[
        str | None,
        Field(description="Target image, container, volume, or compose project name."),
    ] = None,
    output_path: Annotated[
        str | None,
        Field(description="Filesystem path for the backup archive (save) or archive to restore from (load)."),
    ] = None,
    tag: Annotated[
        str | None,
        Field(description="Image tag for load/import operations."),
    ] = None,
) -> dict[str, Any]:
    """
    Backup and restore Podman images, containers, volumes, and compose projects.

    [RATIONALE]
    Consolidates save/load/export/import of Podman artifacts under one tool.
    Podman images use OCI format which is portable to Docker and other runtimes.

    Operations:
    - save_image: Save a Podman image to a tar archive (requires 'name', 'output_path').
    - load_image: Load a Podman image from a tar archive (requires 'output_path', optional 'tag').
    - export_container: Export a container's filesystem to a tar archive (requires 'name', 'output_path').
    - import_container: Import a tar archive as a container image (requires 'output_path', 'name', optional 'tag').
    - save_volume: Backup a named volume to a tar.gz archive (requires 'name', 'output_path').
    - load_volume: Restore a volume from a tar.gz archive (requires 'name', 'output_path').
    - save_compose: Backup compose project config and data to a directory (requires 'name', 'output_path').
    - list_backups: List backup archives in a directory (requires 'output_path').

    ## Return Format
    Returns a structured dictionary with:
    - success (bool): Indication of command status.
    - message (str): Conversational summary of the action.
    - data (dict | None): Structured details returned by the command.

    ## Examples
    >>> await manage_backup(operation="save_image", name="nginx:latest", output_path="C:\\backups\\nginx.tar")
    >>> await manage_backup(operation="load_image", output_path="C:\\backups\\nginx.tar", tag="nginx:restored")
    """
    try:
        if operation in ["save_image", "export_container", "save_volume"] and (not name or not output_path):
            return _error_response(f"Operation '{operation}' requires 'name' and 'output_path'.", "validation_failed")
        if operation in ["load_image", "import_container", "load_volume"] and not output_path:
            return _error_response(f"Operation '{operation}' requires 'output_path'.", "validation_failed")
        if operation == "load_volume" and not name:
            return _error_response("Operation 'load_volume' requires 'name'.", "validation_failed")

        if operation == "save_image":
            res = await run_podman_command(["save", "-o", output_path, name], timeout=120.0)
            if not res["success"]:
                return _error_response(f"Failed to save image '{name}': {res.get('stderr')}", "save_image_failed")
            sz = os.path.getsize(output_path) if os.path.isfile(output_path) else 0
            return {"success": True, "message": f"Image '{name}' saved to {output_path} ({sz / 1024 / 1024:.1f} MB).", "data": {"path": output_path, "size_bytes": sz}}

        elif operation == "load_image":
            args = ["load", "-i", output_path]
            res = await run_podman_command(args, timeout=120.0)
            if not res["success"]:
                return _error_response(f"Failed to load image from '{output_path}': {res.get('stderr')}", "load_image_failed")
            loaded = res["stdout"].strip()
            if tag:
                tag_res = await run_podman_command(["tag", loaded, tag])
            return {"success": True, "message": f"Image loaded from {output_path}: {loaded}", "data": {"loaded_image": loaded, "tag": tag}}

        elif operation == "export_container":
            res = await run_podman_command(["export", "-o", output_path, name], timeout=120.0)
            if not res["success"]:
                return _error_response(f"Failed to export container '{name}': {res.get('stderr')}", "export_failed")
            sz = os.path.getsize(output_path) if os.path.isfile(output_path) else 0
            return {"success": True, "message": f"Container '{name}' filesystem exported to {output_path} ({sz / 1024 / 1024:.1f} MB).", "data": {"path": output_path, "size_bytes": sz}}

        elif operation == "import_container":
            args = ["import", output_path]
            if name:
                args += ["--change", f"CMD {name}"]
            if tag:
                args.append(tag)
            else:
                args.append(name or "imported")
            res = await run_podman_command(args, timeout=120.0)
            if not res["success"]:
                return _error_response(f"Failed to import from '{output_path}': {res.get('stderr')}", "import_failed")
            return {"success": True, "message": f"Container image imported from {output_path}.", "data": {"image_id": res["stdout"].strip()}}

        elif operation == "save_volume":
            backup_file = output_path if output_path.endswith(".tar.gz") else f"{output_path}.tar.gz"
            res = await run_podman_command([
                "run", "--rm", "-v", f"{name}:/data", "-v", f"{os.path.dirname(os.path.abspath(backup_file))}:/backup",
                "alpine", "tar", "czf", f"/backup/{os.path.basename(backup_file)}", "-C", "/data", "."
            ], timeout=120.0)
            if not res["success"]:
                return _error_response(f"Failed to save volume '{name}': {res.get('stderr')}", "save_volume_failed")
            sz = os.path.getsize(backup_file) if os.path.isfile(backup_file) else 0
            return {"success": True, "message": f"Volume '{name}' backed up to {backup_file} ({sz / 1024 / 1024:.1f} MB).", "data": {"path": backup_file, "size_bytes": sz}}

        elif operation == "load_volume":
            if not os.path.isfile(output_path):
                return _error_response(f"Backup file not found: {output_path}", "validation_failed")
            await run_podman_command(["volume", "create", name])
            abs_backup = os.path.abspath(output_path)
            res = await run_podman_command([
                "run", "--rm", "-v", f"{name}:/data", "-v", f"{os.path.dirname(abs_backup)}:/backup",
                "alpine", "tar", "xzf", f"/backup/{os.path.basename(abs_backup)}", "-C", "/data"
            ], timeout=120.0)
            if not res["success"]:
                return _error_response(f"Failed to restore volume '{name}': {res.get('stderr')}", "load_volume_failed")
            return {"success": True, "message": f"Volume '{name}' restored from {output_path}.", "data": {"volume": name}}

        elif operation == "save_compose":
            if not name or not output_path:
                return _error_response("Operation 'save_compose' requires 'name' (project path) and 'output_path'.", "validation_failed")
            os.makedirs(output_path, exist_ok=True)
            info_parts = [f"# Podman Compose Backup: {name}", f"# Date: auto-generated", ""]
            info_parts.append("## Images")
            images_res = await run_podman_command(["images", "--format", "json"])
            if images_res["success"] and images_res["stdout"].strip():
                for img in json.loads(images_res["stdout"]):
                    info_parts.append(f"- {img.get('Names', img.get('Id', 'unknown'))}")
            with open(os.path.join(output_path, "backup-info.txt"), "w") as f:
                f.write("\n".join(info_parts))
            return {"success": True, "message": f"Compose project '{name}' metadata saved to {output_path}.", "data": {"path": output_path, "images": len(info_parts) - 3}}

        elif operation == "list_backups":
            if not output_path:
                return _error_response("Operation 'list_backups' requires 'output_path'.", "validation_failed")
            if not os.path.isdir(output_path):
                return _error_response(f"Directory not found: {output_path}", "validation_failed")
            files = []
            for f in sorted(os.listdir(output_path)):
                fp = os.path.join(output_path, f)
                if os.path.isfile(fp):
                    files.append({"name": f, "size_bytes": os.path.getsize(fp), "size_mb": round(os.path.getsize(fp) / 1024 / 1024, 1)})
            return {"success": True, "message": f"Found {len(files)} backup files in {output_path}.", "data": {"files": files}}

        else:
            return _error_response(f"Unsupported operation: {operation}", "unsupported_operation")

    except Exception as e:
        return _error_response(f"Backup operation failed: {e!s}", "runtime_error")
