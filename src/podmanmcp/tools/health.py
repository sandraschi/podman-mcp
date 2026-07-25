"""Container health analysis and recommendations for Podman MCP."""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any, Literal
from pydantic import Field

from podmanmcp.mcp_instance import mcp
from podmanmcp.podman_context import check_podman_available, run_podman_command
from podmanmcp.tools.utils import _error_response

logger = logging.getLogger("podmanmcp")
_READ_ONLY = {"readonly": True}


@mcp.tool(annotations=_READ_ONLY)
@check_podman_available
async def manage_health(
    operation: Annotated[
        Literal["container_analyze", "system_overview", "recommendations"],
        Field(description="The health analysis operation to perform"),
    ],
    container_id: Annotated[
        str | None,
        Field(description="Target container name or ID for container_analyze."),
    ] = None,
) -> dict[str, Any]:
    """
    Analyze container and system health with actionable recommendations.

    [RATIONALE]
    Proactive health monitoring catches restart loops, OOM kills, disk pressure,
    and stale resources before they cause outages. Agents can invoke this tool
    autonomously to assess cluster health.

    Operations:
    - container_analyze: Deep analysis of a single container (requires 'container_id').
    - system_overview: Fleet-wide health scan of all containers and resources.
    - recommendations: Generate prioritized fix suggestions based on health data.

    ## Return Format
    Returns a structured dictionary with:
    - success (bool): Indication of command status.
    - message (str): Conversational summary of findings.
    - data (dict): Detailed health metrics and recommendations.

    ## Examples
    >>> await manage_health(operation="container_analyze", container_id="my-web-app")
    >>> await manage_health(operation="system_overview")
    >>> await manage_health(operation="recommendations")
    """
    try:
        if operation == "container_analyze":
            if not container_id:
                return _error_response("Operation 'container_analyze' requires 'container_id'.", "validation_failed")

            inspect_res = await run_podman_command(["inspect", container_id])
            if not inspect_res["success"]:
                return _error_response(f"Failed to inspect container: {inspect_res.get('stderr')}", "inspect_failed")

            info = {}
            try:
                data = json.loads(inspect_res["stdout"])
                if data and isinstance(data, list):
                    info = data[0]
            except Exception:
                pass

            state_info = info.get("State", {})
            host_config = info.get("HostConfig", {})
            config = info.get("Config", {})

            restart_count = state_info.get("RestartCount", 0)
            oom_killed = state_info.get("OOMKilled", False)
            exit_code = state_info.get("ExitCode", 0)
            started_at = state_info.get("StartedAt", "")
            finished_at = state_info.get("FinishedAt", "")
            health = state_info.get("Health", {})
            mem_used = state_info.get("Memory", {}).get("Usage", 0) if isinstance(state_info.get("Memory"), dict) else 0

            issues = []
            if restart_count > 3:
                issues.append({"severity": "error", "detail": f"Restarted {restart_count} times — possible crash loop"})
            elif restart_count > 0:
                issues.append({"severity": "warning", "detail": f"Restarted {restart_count} times"})
            if oom_killed:
                issues.append({"severity": "error", "detail": "OOM killed — increase memory limit or reduce workload"})
            if exit_code != 0:
                issues.append({"severity": "warning", "detail": f"Last exit code: {exit_code}"})
            logs_res = await run_podman_command(["logs", "--tail", "50", container_id])
            error_lines = 0
            if logs_res["success"]:
                for line in (logs_res["stdout"] + logs_res["stderr"]).splitlines():
                    lower = line.lower()
                    if any(kw in lower for kw in ["error", "fatal", "panic", "exception", "traceback", "refused", "timeout"]):
                        error_lines += 1
            if error_lines > 10:
                issues.append({"severity": "error", "detail": f"{error_lines} error lines in recent logs"})
            elif error_lines > 0:
                issues.append({"severity": "info", "detail": f"{error_lines} error lines in recent logs"})

            mem_limit = host_config.get("Memory", 0)
            if mem_limit > 0 and mem_used > mem_limit * 0.9:
                issues.append({"severity": "warning", "detail": f"Memory usage near limit ({mem_used / mem_limit:.0%})"})

            status = "healthy" if not any(i["severity"] == "error" for i in issues) else "unhealthy"
            return {
                "success": True,
                "message": f"Container '{container_id}': {status} ({len(issues)} issues).",
                "data": {
                    "container": container_id,
                    "status": status,
                    "restart_count": restart_count,
                    "oom_killed": oom_killed,
                    "exit_code": exit_code,
                    "healthcheck": health.get("Status", "none"),
                    "error_log_lines": error_lines,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "issues": issues,
                },
            }

        elif operation == "system_overview":
            ps_res = await run_podman_command(["ps", "-a", "--format", "json"])
            containers = []
            if ps_res["success"] and ps_res["stdout"].strip():
                containers = json.loads(ps_res["stdout"])

            running = sum(1 for c in containers if c.get("State", "").lower() == "running")
            exited = sum(1 for c in containers if "exit" in c.get("State", "").lower())
            restarting = sum(1 for c in containers if "restart" in c.get("State", "").lower())

            images_res = await run_podman_command(["images", "--format", "json"])
            image_count = 0
            if images_res["success"] and images_res["stdout"].strip():
                image_count = len(json.loads(images_res["stdout"]))

            disk_res = await run_podman_command(["system", "df", "--format", "json"])
            disk_data = {}
            if disk_res["success"] and disk_res["stdout"].strip():
                try:
                    disk_data = json.loads(disk_res["stdout"])
                except Exception:
                    pass

            alerts = []
            if restarting > 0:
                alerts.append({"severity": "error", "detail": f"{restarting} container(s) in restart loop"})
            if exited > 20:
                alerts.append({"severity": "warning", "detail": f"{exited} stopped containers — consider cleanup"})

            return {
                "success": True,
                "message": f"System overview: {len(containers)} containers ({running} running, {exited} exited, {restarting} restarting), {image_count} images.",
                "data": {
                    "containers": {"total": len(containers), "running": running, "exited": exited, "restarting": restarting},
                    "images": {"total": image_count},
                    "disk": disk_data,
                    "alerts": alerts,
                },
            }

        elif operation == "recommendations":
            recs = []
            ps_res = await run_podman_command(["ps", "-a", "--format", "json"])
            containers = []
            if ps_res["success"] and ps_res["stdout"].strip():
                containers = json.loads(ps_res["stdout"])

            exited = sum(1 for c in containers if "exit" in c.get("State", "").lower())
            if exited > 10:
                recs.append({"priority": "medium", "action": "prune", "detail": f"Remove {exited} stopped containers: podman container prune"})

            images_res = await run_podman_command(["images", "--format", "json"])
            dangling = 0
            if images_res["success"] and images_res["stdout"].strip():
                images = json.loads(images_res["stdout"])
                dangling = sum(1 for i in images if "<none>" in str(i.get("Names", i.get("Repository", ""))))
                if dangling > 5:
                    recs.append({"priority": "low", "action": "prune_images", "detail": f"Remove {dangling} dangling images: podman image prune"})

            for c in containers:
                state = c.get("State", "").lower()
                if "restart" in state:
                    name = c.get("Names", [c.get("ID", "unknown")])
                    name = name[0] if isinstance(name, list) else name
                    recs.append({"priority": "high", "action": "investigate_restart", "detail": f"Inspect '{name}': check logs and restart count"})

            if not recs:
                recs.append({"priority": "info", "action": "none", "detail": "System looks healthy — no recommendations needed."})

            return {
                "success": True,
                "message": f"Generated {len(recs)} recommendations.",
                "data": {"recommendations": sorted(recs, key=lambda r: {"high": 0, "medium": 1, "low": 2, "info": 3}.get(r["priority"], 4))},
            }

        else:
            return _error_response(f"Unsupported operation: {operation}", "unsupported_operation")

    except Exception as e:
        return _error_response(f"Health analysis failed: {e!s}", "runtime_error")
