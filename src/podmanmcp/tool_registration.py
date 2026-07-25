"""Register MCP tools and fleet surface after FastMCP singleton exists."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_registered = False


def register_all_tools(mcp=None) -> None:
    """Import tool modules (decorators) and fleet prompts/prefabs."""
    global _registered
    if _registered:
        return

    from podmanmcp.fleet_surface import register_fleet_surface

    if mcp is None:
        from podmanmcp.mcp_instance import get_mcp
        mcp = get_mcp()

    # Import the Portmanteau tool modules (they register themselves via decorators)
    import podmanmcp.tools.system as _system
    import podmanmcp.tools.containers as _containers
    import podmanmcp.tools.pods as _pods
    import podmanmcp.tools.images as _images
    import podmanmcp.tools.compose as _compose
    import podmanmcp.tools.backup as _backup
    import podmanmcp.tools.migrate as _migrate
    import podmanmcp.tools.agentic as _agentic
    import podmanmcp.tools.health as _health

    # Hold references to prevent garbage collection
    _ = [_system, _containers, _pods, _images, _compose, _backup, _migrate, _agentic, _health]

    # Register the fleet prompts, resources, and cards
    register_fleet_surface(mcp)
    
    _registered = True
    logger.info("Podman MCP tools and fleet surface registered successfully")
