"""Tool orchestrator for agentic chat — matches NL queries to Podman tools and executes them."""

import time
import re
from typing import Any

from podmanmcp.mcp_instance import get_mcp

TOOL_PATTERNS: dict[str, list[str]] = {
    "manage_containers": ["list container", "running container", "show container", "all container", "what.*container"],
    "manage_pods": ["list pod", "running pod", "show pod", "what.*pod"],
    "manage_images": ["list image", "show image", "available image", "what image"],
    "manage_system": ["podman info", "system info", "daemon info", "engine info", "podman version", "status", "volume", "network"],
    "manage_compose": ["compose", "podman-compose", "podman compose"],
}


def _match_query(query: str) -> str | None:
    q = query.lower()
    for tool, patterns in TOOL_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, q):
                return tool
    return None


async def execute_tool(tool_name: str, query: str) -> dict[str, Any]:
    """Execute an MCP tool by name, passing heuristically derived params."""
    mcp = get_mcp()
    params: dict[str, Any] = {}
    start = time.monotonic()
    q = query.lower()

    if tool_name == "manage_containers":
        if "inspect" in q or "detail" in q:
            params = {"operation": "inspect"}
        elif "start" in q:
            params = {"operation": "start"}
        elif "stop" in q:
            params = {"operation": "stop"}
        elif "delete" in q or "remove" in q:
            params = {"operation": "delete"}
        elif "run" in q or "create" in q:
            params = {"operation": "create"}
        elif "log" in q:
            params = {"operation": "logs"}
        elif "stat" in q:
            params = {"operation": "stats"}
        else:
            params = {"operation": "list"}
            
    elif tool_name == "manage_pods":
        if "inspect" in q or "detail" in q:
            params = {"operation": "inspect"}
        elif "create" in q or "new" in q:
            params = {"operation": "create"}
        elif "start" in q:
            params = {"operation": "start"}
        elif "stop" in q:
            params = {"operation": "stop"}
        elif "delete" in q or "remove" in q:
            params = {"operation": "delete"}
        else:
            params = {"operation": "list"}
            
    elif tool_name == "manage_images":
        if "inspect" in q:
            params = {"operation": "inspect"}
        elif "pull" in q or "download" in q:
            params = {"operation": "pull"}
        elif "delete" in q or "remove" in q:
            params = {"operation": "delete"}
        elif "build" in q:
            params = {"operation": "build"}
        elif "search" in q:
            params = {"operation": "search"}
        else:
            params = {"operation": "list"}
            
    elif tool_name == "manage_system":
        if "info" in q:
            params = {"operation": "info"}
        elif "prune" in q or "clean" in q:
            params = {"operation": "prune"}
        elif "volume" in q:
            params = {"operation": "volume_list"}
        elif "network" in q:
            params = {"operation": "network_list"}
        else:
            params = {"operation": "status"}
            
    elif tool_name == "manage_compose":
        if "down" in q or "stop" in q:
            params = {"operation": "down", "project_path": "."}
        elif "ps" in q:
            params = {"operation": "ps", "project_path": "."}
        elif "log" in q:
            params = {"operation": "logs", "project_path": "."}
        else:
            params = {"operation": "up", "project_path": "."}

    tool = next((t for t in (await mcp.list_tools()) if t.name == tool_name), None)
    if not tool:
        return {"success": False, "error": f"Tool '{tool_name}' not found"}

    try:
        result = await mcp.call_tool(tool_name, params)
        elapsed = time.monotonic() - start
        
        # Format result to string if it's not a primitive
        result_str = str(result)
        if hasattr(result, "model_dump_json"):
            result_str = result.model_dump_json()
        elif isinstance(result, (dict, list)):
            result_str = json.dumps(result)
            
        return {
            "success": True,
            "tool": tool_name,
            "params": params,
            "result": result_str,
            "timing_ms": round(elapsed * 1000),
        }
    except Exception as e:
        elapsed = time.monotonic() - start
        return {
            "success": False,
            "tool": tool_name,
            "params": params,
            "error": str(e),
            "timing_ms": round(elapsed * 1000),
        }


def tool_to_nl_name(tool: str) -> str:
    """Pretty name for a tool."""
    names = {
        "manage_containers": "Manage Containers",
        "manage_pods": "Manage Pods",
        "manage_images": "Manage Images",
        "manage_system": "Manage System",
        "manage_compose": "Manage Compose",
    }
    return names.get(tool, tool.replace("_", " ").title())
