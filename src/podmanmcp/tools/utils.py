"""Shared utilities for Podman MCP tools."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("podmanmcp")


def _error_response(
    error: str,
    error_type: str = "general",
    suggestions: list[str] | None = None,
    **kwargs: Any
) -> dict[str, Any]:
    """Auto-logging error response generator.
    
    Captures active exception traceback and logs it to warning/error log
    before returning a structured JSON response to the agent.
    """
    logger.exception("Tool error: %s [%s]", error, error_type)
    
    resp: dict[str, Any] = {
        "success": False,
        "error": error,
        "error_type": error_type,
    }
    if suggestions:
        resp["suggestions"] = suggestions
    else:
        # Provide default general suggestions if none specified
        resp["suggestions"] = [
            "Check that Podman is running and accessible.",
            "Verify your command parameters and try again.",
        ]
        
    resp.update(kwargs)
    return resp
