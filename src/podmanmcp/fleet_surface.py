"""Register fleet SOTA surface: prompts, prefab tools, MCP resources."""

from __future__ import annotations

import logging
import os
from typing import Annotated

from pydantic import Field

logger = logging.getLogger(__name__)

# Try to load the SKILL.md file if available, or fall back
_SKILL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "skills", "podman-mcp", "SKILL.md")
try:
    with open(_SKILL_PATH, encoding="utf-8") as _f:
        SKILLS_MD = _f.read()
except (FileNotFoundError, OSError):
    SKILLS_MD = (
        "# Podman-MCP\n"
        "Podman MCP is a FastMCP server designed to manage daemon-less container operations "
        "on Windows and WSL2 using the Podman CLI directly."
    )


def register_fleet_surface(mcp) -> None:
    """Attach prompts, prefab tools, and resources to the singleton MCP instance."""

    @mcp.prompt()
    def podman_deploy_stack(
        stack_name: Annotated[str, Field(description="Name of the stack to deploy")] = "app",
    ) -> str:
        """Prompt template for deploying a multi-container stack."""
        return (
            f"Deploy Podman stack '{stack_name}': list images, create networks/volumes as needed, "
            "start containers in dependency order, verify health, and summarize ports and status."
        )

    @mcp.prompt()
    def podman_machine_health_check() -> str:
        """Prompt template for Podman Machine diagnostics."""
        return (
            "Check Podman CLI health with podman_machine_status_card. If the machine is stopped or "
            "unavailable, use manage_system to start the local VM machine. Report recent containers and images."
        )

    @mcp.resource("resource://podman-mcp/skills")
    def podman_mcp_skills() -> str:
        return SKILLS_MD

    @mcp.resource("resource://podman-mcp/capabilities")
    def podman_mcp_capabilities() -> str:
        return (
            "podman-mcp: FastMCP 3.4+, sampling (Ollama/LM Studio), manage_containers, manage_pods, "
            "manage_images, manage_system, manage_compose, prefab cards, webapp /logs. Transports: stdio, HTTP."
        )

    @mcp.tool(annotations={"readonly": True})
    async def podman_containers_card(
        all_states: Annotated[bool, Field(description="Include stopped containers")] = True,
    ):
        """List containers as a Prefab card (fleet list/status surface)."""
        from podmanmcp.prefabs import build_containers_card
        from podmanmcp.tools.containers import manage_containers

        result = await manage_containers(operation="list")
        return build_containers_card(result)

    @mcp.tool(annotations={"readonly": True})
    async def podman_pods_card():
        """List Podman Pods as a Prefab card (fleet list/status surface)."""
        from podmanmcp.prefabs import build_pods_card
        from podmanmcp.tools.pods import manage_pods

        result = await manage_pods(operation="list")
        return build_pods_card(result)

    @mcp.tool(annotations={"readonly": True})
    async def podman_machine_status_card():
        """Podman Machine / CLI status as a Prefab card."""
        from podmanmcp.prefabs import build_machine_status_card
        from podmanmcp.tools.system import manage_system

        result = await manage_system(operation="status")
        payload = result.get("data") or result
        return build_machine_status_card(payload)

    @mcp.tool(annotations={"readonly": True})
    async def podman_images_card(
        limit: Annotated[int, Field(description="Max images in card")] = 12,
    ):
        """Image inventory as a Prefab card."""
        from podmanmcp.prefabs import build_images_card
        from podmanmcp.tools.images import manage_images

        result = await manage_images(operation="list")
        return build_images_card(result, limit=limit)

    @mcp.tool(annotations={"readonly": True})
    async def podman_system_info_card():
        """Engine system info as a Prefab card."""
        from podmanmcp.prefabs import build_system_info_card
        from podmanmcp.tools.system import manage_system

        result = await manage_system(operation="info")
        payload = result.get("data") or result
        return build_system_info_card(payload)

    logger.info("Fleet surface registered: prompts, resources, prefab tools")
