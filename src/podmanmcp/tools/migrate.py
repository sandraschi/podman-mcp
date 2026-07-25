"""Docker-to-Podman and Podman-to-Docker migration tools."""

from __future__ import annotations

import json
import logging
import os
import shutil
from typing import Annotated, Any, Literal
from pydantic import Field

from podmanmcp.mcp_instance import mcp
from podmanmcp.podman_context import check_podman_available, run_podman_command
from podmanmcp.tools.utils import _error_response

logger = logging.getLogger("podmanmcp")


@mcp.tool()
@check_podman_available
async def manage_migrate(
    operation: Annotated[
        Literal[
            "docker_compose_to_podman",
            "podman_compose_to_docker",
            "scan_docker_artifacts",
            "migrate_image",
            "compatibility_check",
            "dockerfile_to_containerfile",
            "export_for_docker",
        ],
        Field(description="The migration operation to perform"),
    ],
    source_path: Annotated[
        str | None,
        Field(description="Path to a docker-compose.yml file, Dockerfile, or project directory."),
    ] = None,
    output_path: Annotated[
        str | None,
        Field(description="Path to write the converted file. Defaults to source directory with new name."),
    ] = None,
    image_name: Annotated[
        str | None,
        Field(description="Docker image name to migrate (e.g. 'nginx:latest')."),
    ] = None,
    new_name: Annotated[
        str | None,
        Field(description="New image tag after migration (e.g. 'nginx:podman')."),
    ] = None,
) -> dict[str, Any]:
    """
    Migrate between Docker and Podman: compose files, Dockerfiles, images, and artifacts.

    [RATIONALE]
    Podman is designed as a drop-in Docker replacement. This tool automates the common
    migration tasks: converting compose files, importing Docker images, exporting for
    Docker consumption, and checking compatibility of Docker artifacts with Podman.

    Operations:
    - docker_compose_to_podman: Convert docker-compose.yml to podman-compose.yml.
    - podman_compose_to_docker: Convert podman-compose.yml to docker-compose.yml.
    - scan_docker_artifacts: Scan for Docker Desktop artifacts suitable for migration.
    - migrate_image: Pull a Docker Hub image and re-tag for Podman use.
    - compatibility_check: Check if a compose file uses features incompatible with Podman.
    - dockerfile_to_containerfile: Rename Dockerfile to Containerfile (Podman convention).
    - export_for_docker: Export a Podman container/image for Docker consumption.

    ## Return Format
    Returns a structured dictionary with:
    - success (bool): Indication of command status.
    - message (str): Conversational summary of the action.
    - data (dict | None): Structured details including converted content or scan results.

    ## Examples
    >>> await manage_migrate(operation="docker_compose_to_podman", source_path="C:\\projects\\docker-compose.yml")
    >>> await manage_migrate(operation="migrate_image", image_name="nginx:latest", new_name="nginx:podman")
    >>> await manage_migrate(operation="compatibility_check", source_path="C:\\projects\\docker-compose.yml")
    """
    try:
        if operation in ["docker_compose_to_podman", "podman_compose_to_docker", "compatibility_check",
                          "dockerfile_to_containerfile"] and not source_path:
            return _error_response(f"Operation '{operation}' requires 'source_path'.", "validation_failed")
        if operation == "migrate_image" and not image_name:
            return _error_response("Operation 'migrate_image' requires 'image_name'.", "validation_failed")

        if operation == "docker_compose_to_podman":
            if not os.path.isfile(source_path):
                return _error_response(f"Source file not found: {source_path}", "validation_failed")
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()
            changes = []
            converted = content
            if "version:" in converted:
                converted = converted.replace('version: "3"', '# version: "3"  # podman ignores version; kept for reference')
                converted = converted.replace('version: "3.8"', '# version: "3.8"')
                changes.append("commented out version field (podman ignores it)")
            if "deploy:" in converted and "replicas:" in converted:
                changes.append("deploy.replicas may need adjustment: podman-compose uses scale instead of replicas")
            if "dockerfile:" in converted.lower():
                converted = converted.replace("dockerfile:", "dockerfile:")  # no change needed — podman-compose reads dockerfile key
            dest = output_path or source_path.replace(".yml", "-podman.yml").replace(".yaml", "-podman.yaml")
            with open(dest, "w", encoding="utf-8") as f:
                f.write(converted)
            return {
                "success": True,
                "message": f"Converted docker-compose.yml → podman-compose. Written to {dest}.",
                "data": {"output": dest, "changes": changes, "warnings": [c for c in changes if "may need" in c.lower()]},
                "podman_compose_content": converted,
            }

        elif operation == "podman_compose_to_docker":
            if not os.path.isfile(source_path):
                return _error_response(f"Source file not found: {source_path}", "validation_failed")
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()
            dest = output_path or source_path.replace("-podman.yml", ".yml").replace("-podman.yaml", ".yaml")
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
            return {
                "success": True,
                "message": f"Podman compose file copied to Docker-compatible format: {dest}.",
                "data": {"output": dest},
            }

        elif operation == "scan_docker_artifacts":
            findings = {"compose_files": [], "dockerfiles": [], "images": []}
            scan_dirs = [source_path] if source_path and os.path.isdir(source_path) else [
                os.path.expanduser("~"), os.getcwd()
            ]
            for scan_dir in scan_dirs:
                for root, _, files in os.walk(scan_dir):
                    if ".git" in root or "node_modules" in root or ".venv" in root or "__pycache__" in root:
                        continue
                    for f in files:
                        fp = os.path.join(root, f)
                        if "docker-compose" in f.lower() and (f.endswith(".yml") or f.endswith(".yaml")):
                            sz = os.path.getsize(fp)
                            if sz < 100_000:
                                findings["compose_files"].append({"path": fp, "size": sz})
                        if f.lower() == "dockerfile" or f.startswith("Dockerfile."):
                            findings["dockerfiles"].append(fp)
                    if len(str(root)) > 200:
                        break
            res = await run_podman_command(["images", "--format", "json"])
            if res["success"] and res["stdout"].strip():
                try:
                    images = json.loads(res["stdout"])
                    for img in images:
                        findings["images"].append(img.get("Names", img.get("Id", "unknown")))
                except Exception:
                    pass
            return {
                "success": True,
                "message": f"Scanned: {len(findings['compose_files'])} compose files, {len(findings['dockerfiles'])} Dockerfiles, {len(findings['images'])} images.",
                "data": findings,
            }

        elif operation == "migrate_image":
            pull_res = await run_podman_command(["pull", image_name], timeout=180.0)
            if not pull_res["success"]:
                return _error_response(f"Failed to pull image '{image_name}': {pull_res.get('stderr')}", "migrate_pull_failed")
            tag = new_name or image_name.replace("docker.io/", "").replace("library/", "")
            if tag != image_name:
                tag_res = await run_podman_command(["tag", image_name, tag])
            return {
                "success": True,
                "message": f"Image '{image_name}' migrated to Podman as '{tag}'. Run with: podman run {tag}",
                "data": {"from": image_name, "to": tag},
            }

        elif operation == "compatibility_check":
            if not os.path.isfile(source_path):
                return _error_response(f"File not found: {source_path}", "validation_failed")
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()
            issues = []
            docker_only = [
                ("deploy:", "deploy configuration (Swarm mode) is not supported by podman-compose; use 'scale' or pod-level replication"),
                ("secrets:", "Docker secrets are not supported by podman-compose; use volumes or env vars"),
                ("configs:", "Docker configs are not supported by podman-compose"),
                ("external_links:", "external_links is deprecated; not supported by podman-compose"),
                ("cgroup_parent:", "cgroup_parent may not work in rootless Podman without cgroups v2"),
            ]
            for pattern, explanation in docker_only:
                if pattern.lower() in content.lower():
                    issues.append({"pattern": pattern, "severity": "warning" if "may" in explanation else "error", "explanation": explanation})
            has_version = any(line.strip().startswith("version:") for line in content.splitlines())
            if has_version:
                issues.append({"pattern": "version:", "severity": "info", "explanation": "version field is ignored by podman-compose (safe to keep)"})
            if "depends_on:" in content and "condition: service_healthy" in content:
                issues.append({"pattern": "depends_on condition", "severity": "warning", "explanation": "service_healthy condition may not work; podman-compose polling is simpler"})
            ok = not any(i["severity"] == "error" for i in issues)
            return {
                "success": True,
                "message": f"Compatibility check: {'PASSED' if ok else 'FAILED'} — {len(issues)} issues found.",
                "data": {"compatible": ok, "issues": issues, "total": len(issues)},
            }

        elif operation == "dockerfile_to_containerfile":
            if os.path.isfile(source_path) and source_path.lower().endswith("dockerfile"):
                dest = output_path or os.path.join(os.path.dirname(source_path), "Containerfile")
                shutil.copy2(source_path, dest)
                return {"success": True, "message": f"Dockerfile copied to Containerfile at {dest}.", "data": {"from": source_path, "to": dest}}
            elif os.path.isdir(source_path):
                dockerfile = os.path.join(source_path, "Dockerfile")
                if not os.path.isfile(dockerfile):
                    return _error_response(f"No Dockerfile found in {source_path}", "validation_failed")
                dest = output_path or os.path.join(source_path, "Containerfile")
                shutil.copy2(dockerfile, dest)
                return {"success": True, "message": f"Dockerfile copied to Containerfile at {dest}.", "data": {"from": dockerfile, "to": dest}}
            else:
                return _error_response("source_path must be a Dockerfile or a directory containing one", "validation_failed")

        elif operation == "export_for_docker":
            if not image_name:
                return _error_response("Operation 'export_for_docker' requires 'image_name'.", "validation_failed")
            dest = output_path or f"{image_name.replace(':', '_').replace('/', '_')}-docker.tar"
            res = await run_podman_command(["save", "--format", "docker-archive", "-o", dest, image_name], timeout=180.0)
            if not res["success"]:
                return _error_response(f"Failed to export image '{image_name}' for Docker: {res.get('stderr')}", "export_failed")
            sz = os.path.getsize(dest) if os.path.isfile(dest) else 0
            return {
                "success": True,
                "message": f"Image '{image_name}' exported for Docker. Load with: docker load -i {dest}",
                "data": {"path": dest, "size_mb": round(sz / 1024 / 1024, 1), "docker_load_cmd": f"docker load -i {dest}"},
            }

        else:
            return _error_response(f"Unsupported operation: {operation}", "unsupported_operation")

    except Exception as e:
        return _error_response(f"Migration operation failed: {e!s}", "runtime_error")
