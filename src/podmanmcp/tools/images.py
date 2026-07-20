"""Image management tools for Podman MCP."""

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
async def manage_images(
    operation: Annotated[
        Literal["list", "inspect", "pull", "delete", "build", "search"],
        Field(description="The image management operation to perform"),
    ],
    image_name: Annotated[
        str | None,
        Field(
            description="Target image reference, tag, or ID. Required for inspect, pull, and delete operations."
        ),
    ] = None,
    search_term: Annotated[
        str | None,
        Field(description="Term or name to search on remote registries. Required for 'search' operation."),
    ] = None,
    build_tag: Annotated[
        str | None,
        Field(description="Optional tag (e.g. 'my-app:v1') to apply to the image built during 'build'."),
    ] = None,
    build_path: Annotated[
        str | None,
        Field(description="Optional path to the build context directory (defaults to '.') for 'build'."),
    ] = ".",
) -> dict[str, Any]:
    """
    Manage local and remote container images in Podman.

    [RATIONALE]
    Consolidates image registry search, downloads (pull), listing local inventory, 
    deleting images, inspecting manifest metadata, and building new images 
    from local Podmanfiles/Containerfiles.

    Operations:
    - list: List all local images cached in Podman storage.
    - inspect: Get low-level JSON layer information of an image (requires 'image_name').
    - pull: Download a remote image from configured registries (requires 'image_name').
    - delete: Remove a local image cache entry (requires 'image_name').
    - build: Build a new image from a build context directory path.
    - search: Find images in registry search indexes (requires 'search_term').

    ## Return Format
    Returns a structured dictionary with:
    - success (bool): Indication of command status.
    - message (str): Conversational summary of the action.
    - data (dict | list | None): Structured details returned by the command.

    ## Examples
    >>> await manage_images(operation="list")
    >>> await manage_images(operation="pull", image_name="podman.io/library/alpine:latest")
    >>> await manage_images(operation="search", search_term="postgres")
    """
    try:
        # 1. Parameter validation
        if operation in ["inspect", "pull", "delete"] and not image_name:
            return _error_response(
                f"Operation '{operation}' requires an 'image_name' parameter.", "validation_failed"
            )
        if operation == "search" and not search_term:
            return _error_response(
                "Operation 'search' requires a 'search_term' parameter.", "validation_failed"
            )

        # 2. Execute operations
        if operation == "list":
            res = await run_podman_command(["images", "--format", "json"])
            if not res["success"]:
                return _error_response(f"Failed to list images: {res.get('stderr')}", "list_failed")
            
            images = []
            if res["stdout"].strip():
                try:
                    images = json.loads(res["stdout"])
                except Exception as parse_err:
                    logger.warning("Failed to parse images JSON", error=str(parse_err))
                    
            # Map fields for compatibility
            mapped_images = []
            for img in images:
                # Podman list image fields can be lowercase or title case
                repo_tags = img.get("Names") or img.get("names") or []
                if isinstance(repo_tags, str):
                    repo_tags = [repo_tags]
                    
                mapped_images.append({
                    "id": img.get("Id", img.get("id", ""))[:19],
                    "repo_tags": repo_tags,
                    "size": int(img.get("Size", img.get("size", 0))),
                    "created": img.get("Created", img.get("created", "")),
                })
                
            return {
                "success": True,
                "message": f"Found {len(mapped_images)} local images.",
                "images": mapped_images,  # Keep top-level keys for webapp compatibility
                "data": {"images": mapped_images},
            }

        elif operation == "inspect":
            res = await run_podman_command(["inspect", image_name])
            if not res["success"]:
                return _error_response(f"Failed to inspect image '{image_name}': {res.get('stderr')}", "inspect_failed")
            
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
                "message": f"Successfully inspected image '{image_name}'.",
                "data": inspect_data,
            }

        elif operation == "pull":
            # Pulling is a mutating operation that can take time, timeout is set to 120s here
            res = await run_podman_command(["pull", image_name], timeout=120.0)
            if not res["success"]:
                return _error_response(f"Failed to pull image '{image_name}': {res.get('stderr')}", "pull_failed")
            return {
                "success": True,
                "message": f"Successfully pulled image '{image_name}' to host registry cache.",
                "data": {"stdout": res["stdout"].strip()},
            }

        elif operation == "delete":
            res = await run_podman_command(["rmi", "-f", image_name])
            if not res["success"]:
                return _error_response(f"Failed to delete image '{image_name}': {res.get('stderr')}", "delete_failed")
            return {
                "success": True,
                "message": f"Successfully deleted local image '{image_name}'.",
                "data": {"stdout": res["stdout"].strip()},
            }

        elif operation == "build":
            build_args = ["build"]
            if build_tag:
                build_args += ["-t", build_tag]
            build_args.append(build_path or ".")
            
            # Build can take time, timeout set to 180s
            res = await run_podman_command(build_args, timeout=180.0)
            if not res["success"]:
                return _error_response(f"Failed to build image: {res.get('stderr')}", "build_failed")
            return {
                "success": True,
                "message": f"Successfully built image. Tag: {build_tag or 'untagged'}",
                "data": {"stdout": res["stdout"].strip(), "tag": build_tag},
            }

        elif operation == "search":
            res = await run_podman_command(["search", "--format", "json", search_term])
            if not res["success"]:
                return _error_response(f"Registry search failed for '{search_term}': {res.get('stderr')}", "search_failed")
            
            results = []
            if res["stdout"].strip():
                try:
                    results = json.loads(res["stdout"])
                except Exception:
                    pass
            return {
                "success": True,
                "message": f"Found {len(results)} registry matches for '{search_term}'.",
                "data": {"results": results},
            }

        else:
            return _error_response(f"Unsupported operation: {operation}", "unsupported_operation")

    except Exception as e:
        return _error_response(f"Image operation failed: {e!s}", "runtime_error")
