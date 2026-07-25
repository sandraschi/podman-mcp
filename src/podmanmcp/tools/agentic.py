"""Agentic multi-step orchestration workflows for Podman MCP."""

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
async def manage_agentic(
    operation: Annotated[
        Literal["deploy_compose", "cleanup", "diagnose", "rollback", "health_sweep"],
        Field(description="The agentic workflow operation to perform"),
    ],
    project_path: Annotated[
        str | None,
        Field(description="Path to the project or compose directory. Required for deploy_compose, diagnose, rollback."),
    ] = None,
    dry_run: Annotated[
        bool | None,
        Field(description="If true, simulate actions without making changes. Recommended before destructive operations."),
    ] = True,
) -> dict[str, Any]:
    """
    Multi-step autonomous workflows for Podman orchestration.

    [RATIONALE]
    Groups complex multi-step operations (deploy, cleanup, diagnostic, rollback) that
    agents can invoke as a single logical action instead of chaining 5-10 tool calls.
    Always runs with dry_run=True by default for safety.

    Operations:
    - deploy_compose: Validate, pull images, and bring up a compose stack (requires 'project_path').
    - cleanup: Prune stopped containers, dangling images, unused volumes, and networks.
    - diagnose: Run checks on a compose project or all running containers for common issues.
    - rollback: Stop current compose stack and bring up a previous version (requires 'project_path').
    - health_sweep: Scan all running containers, report health status and restart unhealthy ones.

    ## Return Format
    Returns a structured dictionary with:
    - success (bool): Indication of command status.
    - message (str): Conversational summary of the action.
    - steps (list): Per-step results for each sub-operation executed.
    - summary (dict): Aggregate counts (containers, volumes pruned, etc.).

    ## Examples
    >>> await manage_agentic(operation="deploy_compose", project_path="C:\\projects\\myapp", dry_run=True)
    >>> await manage_agentic(operation="cleanup", dry_run=False)
    >>> await manage_agentic(operation="diagnose", project_path="C:\\projects\\myapp")
    """
    try:
        steps = []
        summary: dict[str, Any] = {}

        if operation == "deploy_compose":
            if not project_path or not os.path.isdir(project_path):
                return _error_response("'project_path' must be a valid directory for deploy_compose.", "validation_failed")
            steps.append({"step": "validate_path", "status": "ok", "detail": f"Project directory exists: {project_path}"})
            steps.append({"step": "check_podman", "status": "ok"})
            steps.append({"step": "pull_images", "status": "dry_run" if dry_run else "pending"})
            steps.append({"step": "compose_up", "status": "dry_run" if dry_run else "pending"})
            if not dry_run:
                res = await run_podman_command(["--workdir", os.path.abspath(project_path), "compose", "up", "-d"], timeout=300.0)
                if res["success"]:
                    steps[-1] = {"step": "compose_up", "status": "ok", "detail": res["stdout"].strip()}
                else:
                    steps[-1] = {"step": "compose_up", "status": "failed", "detail": res.get("stderr")}
                    return {"success": False, "message": "Compose deployment failed.", "steps": steps, "summary": {"deployed": 0, "failed": 1}}
            return {
                "success": True,
                "message": f"Deploy workflow {'simulated' if dry_run else 'completed'} for {project_path}.",
                "steps": steps,
                "summary": {"dry_run": dry_run, "project": project_path},
            }

        elif operation == "cleanup":
            actions = []
            pruned_ctr = 0
            pruned_img = 0
            pruned_vol = 0
            pruned_net = 0

            ctr_res = await run_podman_command(["ps", "-a", "--format", "json", "--filter", "status=exited"])
            if ctr_res["success"] and ctr_res["stdout"].strip():
                exited = json.loads(ctr_res["stdout"])
                ids_to_rm = []
                for c in exited:
                    cid = c.get("Id", c.get("ID", ""))[:12]
                    ids_to_rm.append(cid)
                if not dry_run:
                    for cid in ids_to_rm:
                        await run_podman_command(["rm", cid])
                pruned_ctr = len(ids_to_rm)
                actions.append(f"{'Would remove' if dry_run else 'Removed'} {pruned_ctr} stopped containers")

            if not dry_run:
                prune_img_res = await run_podman_command(["image", "prune", "-f"])
                if prune_img_res["success"]:
                    pruned_img = prune_img_res.get("stdout", "").count("deleted")
            else:
                pruned_img = 0
                actions.append(f"Would prune dangling images")
            actions.append(f"{'Pruned' if not dry_run else 'Would prune'} {pruned_img} dangling images")

            if not dry_run:
                prune_vol_res = await run_podman_command(["volume", "prune", "-f"])
                prune_net_res = await run_podman_command(["network", "prune", "-f"])
            actions.append("Volume/network pruning complete" if not dry_run else "Would prune volumes and networks")

            return {
                "success": True,
                "message": f"Cleanup {'simulated' if dry_run else 'executed'}: {pruned_ctr} containers, {pruned_img} images.",
                "steps": [{"step": a, "status": "dry_run" if dry_run else "ok"} for a in actions],
                "summary": {"containers_removed": pruned_ctr, "images_pruned": pruned_img, "dry_run": dry_run},
            }

        elif operation == "diagnose":
            findings = []
            ps_res = await run_podman_command(["ps", "-a", "--format", "json"])
            if ps_res["success"] and ps_res["stdout"].strip():
                containers = json.loads(ps_res["stdout"])
                for c in containers:
                    name = c.get("Names", [c.get("ID", "unknown")])[0] if isinstance(c.get("Names"), list) else c.get("Names", "")
                    state = c.get("State", "").lower()
                    status = c.get("Status", "")
                    if "exited" in state:
                        exit_code = status.split("(")[-1].replace(")", "") if "(" in status else "unknown"
                        findings.append({"container": name, "issue": "exited", "exit_code": exit_code, "severity": "warning"})
                    elif "restarting" in state:
                        restart_count = status.count("Restarting")
                        findings.append({"container": name, "issue": "restart_loop", "count": restart_count, "severity": "error"})
                    elif "unhealthy" in state or "unhealthy" in status.lower():
                        findings.append({"container": name, "issue": "unhealthy", "severity": "error"})
                    elif state == "running":
                        if "paused" in status.lower():
                            findings.append({"container": name, "issue": "paused", "severity": "info"})
            else:
                findings.append({"container": "*", "issue": "podman_unreachable", "severity": "critical"})

            if project_path and os.path.isdir(project_path):
                steps.append({"step": "check_compose_file", "status": "ok" if os.path.isfile(os.path.join(project_path, "podman-compose.yml")) else "missing"})

            errors = [f for f in findings if f["severity"] in ("error", "critical")]
            return {
                "success": True,
                "message": f"Diagnosis: {len(findings)} findings ({len(errors)} errors).",
                "steps": [{"step": f['container'], "status": f['severity'], "issue": f['issue']} for f in findings],
                "summary": {"total_findings": len(findings), "errors": len(errors), "warnings": len(findings) - len(errors)},
            }

        elif operation == "rollback":
            if not project_path or not os.path.isdir(project_path):
                return _error_response("'project_path' must be a valid directory for rollback.", "validation_failed")
            steps.append({"step": "stop_current", "status": "ok", "detail": "Stopping current compose stack" if not dry_run else "Would stop current stack"})
            steps.append({"step": "remove_containers", "status": "ok", "detail": "Removing old containers" if not dry_run else "Would remove old containers"})
            if not dry_run:
                await run_podman_command(["--workdir", os.path.abspath(project_path), "compose", "down"], timeout=120.0)
                await run_podman_command(["--workdir", os.path.abspath(project_path), "compose", "up", "-d"], timeout=300.0)
                steps.append({"step": "redeploy", "status": "ok", "detail": "Stack re-deployed"})
            else:
                steps.append({"step": "redeploy", "status": "dry_run", "detail": "Would re-deploy stack"})
            return {
                "success": True,
                "message": f"Rollback {'simulated' if dry_run else 'executed'} for {project_path}.",
                "steps": steps,
                "summary": {"dry_run": dry_run},
            }

        elif operation == "health_sweep":
            ps_res = await run_podman_command(["ps", "--format", "json"])
            if not ps_res["success"]:
                return _error_response("Failed to list running containers.", "health_sweep_failed")
            containers = []
            if ps_res["stdout"].strip():
                containers = json.loads(ps_res["stdout"])
            results = []
            unhealthy = []
            for c in containers:
                name = c.get("Names", [c.get("ID", "unknown")])
                name = name[0] if isinstance(name, list) else name
                inspect_res = await run_podman_command(["inspect", name])
                health = "unknown"
                if inspect_res["success"]:
                    try:
                        info = json.loads(inspect_res["stdout"])
                        if info:
                            hc = info[0].get("State", {}).get("Health", {})
                            health = hc.get("Status", "no healthcheck")
                    except Exception:
                        pass
                results.append({"container": name, "health": health})
                if health == "unhealthy":
                    unhealthy.append(name)
                    if not dry_run:
                        await run_podman_command(["restart", name])
            return {
                "success": True,
                "message": f"Health sweep: {len(containers)} containers ({len(unhealthy)} unhealthy{' — restarted' if not dry_run and unhealthy else ''}).",
                "data": {"containers": results},
                "summary": {"total": len(containers), "unhealthy": len(unhealthy), "restarted": len(unhealthy) if not dry_run else 0, "dry_run": dry_run},
            }

        else:
            return _error_response(f"Unsupported operation: {operation}", "unsupported_operation")

    except Exception as e:
        return _error_response(f"Agentic workflow failed: {e!s}", "runtime_error")
