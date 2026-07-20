"""PodmanMCP - FastMCP 3.4+ server for Podman operations."""

__version__ = "3.5.0"

from .podman_context import (
    check_podman_available,
    podman_available,
    podman_error,
    get_podman_status,
    initialize_podman_connection,
    run_podman_command,
)


def __getattr__(name: str):
    if name == "mcp":
        from .mcp_instance import get_mcp
        return get_mcp()
    if name == "get_mcp":
        from .mcp_instance import get_mcp
        return get_mcp
    if name == "register_tools":
        from .tool_registration import register_all_tools
        return register_all_tools
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "__version__",
    "check_podman_available",
    "podman_available",
    "podman_error",
    "get_podman_status",
    "initialize_podman_connection",
    "run_podman_command",
    "mcp",
    "register_tools",
]
