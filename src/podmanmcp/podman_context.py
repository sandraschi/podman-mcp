"""Podman CLI connection state and execution helper (import-safe)."""

from __future__ import annotations

import asyncio
import os
import shlex
import shutil
import subprocess
import sys
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast
import structlog

# Setup structured logging
log = structlog.get_logger(__name__)

podman_available: bool = False
podman_error: str | None = None
podman_cmd_base: list[str] = ["podman"]

F = TypeVar("F", bound=Callable[..., Any])


def get_podman_command() -> list[str]:
    """Resolve the base command for running Podman."""
    # Check env var first
    env_cmd = os.getenv("PODMAN_CMD")
    if env_cmd:
        try:
            cmd = shlex.split(env_cmd)
            log.info("Using Podman command from PODMAN_CMD env", command=cmd)
            return cmd
        except Exception as e:
            log.warning("Failed to parse PODMAN_CMD env, falling back", error=str(e))

    # Check if native podman is in PATH
    if shutil.which("podman"):
        log.info("Found native Windows podman in PATH")
        return ["podman"]

    # Check if wsl is available and podman works inside it
    if shutil.which("wsl"):
        try:
            # Probe if wsl podman --version works
            res = subprocess.run(
                ["wsl", "podman", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            if res.returncode == 0:
                log.info("Found podman inside WSL")
                return ["wsl", "podman"]
        except Exception as e:
            log.debug("WSL probe failed or podman not in default WSL distro", error=str(e))

    log.warning("Podman executable not found in PATH or WSL. Defaulting to 'podman'")
    return ["podman"]


def initialize_podman_connection() -> bool:
    """Check if Podman is working and determine command base."""
    global podman_available, podman_error, podman_cmd_base

    try:
        podman_cmd_base = get_podman_command()
        log.info("Probing Podman system status...", cmd_base=podman_cmd_base)
        
        # Test command by running podman --version
        test_args = podman_cmd_base + ["--version"]
        res = subprocess.run(
            test_args,
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        if res.returncode == 0:
            podman_available = True
            podman_error = None
            log.info("Successfully verified Podman CLI connection", version=res.stdout.strip())
            return True
        else:
            podman_available = False
            podman_error = res.stderr.strip() or f"Exit code {res.returncode}"
            log.warning("Podman connection failed", error=podman_error)
            return False
    except FileNotFoundError as e:
        podman_available = False
        podman_error = f"Executable '{podman_cmd_base[0]}' not found: {e!s}"
        log.warning("Podman executable not found", command=podman_cmd_base[0], error=str(e))
        return False
    except Exception as e:
        podman_available = False
        podman_error = f"Probe failed: {e!s}"
        log.warning("Unexpected error probing Podman CLI", error=str(e))
        return False


async def run_podman_command(args: list[str], timeout: float = 30.0) -> dict[str, Any]:
    """Execute a Podman CLI command asynchronously.

    Args:
        args: Command arguments to append to podman (e.g. ['ps', '-a'])
        timeout: Timeout in seconds

    Returns:
        Dictionary containing success, stdout, stderr, returncode, and command.
    """
    cmd = podman_cmd_base + args
    log.debug("Running podman command", command=cmd)
    
    try:
        # Run subprocess asynchronously in a thread pool to avoid blocking the event loop
        def _run():
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )

        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, _run)

        return {
            "success": res.returncode == 0,
            "stdout": res.stdout,
            "stderr": res.stderr,
            "returncode": res.returncode,
            "command": " ".join(cmd),
        }
    except subprocess.TimeoutExpired:
        log.warning("Podman command timed out", command=cmd, timeout=timeout)
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds",
            "command": " ".join(cmd),
            "error_type": "TimeoutExpired",
        }
    except Exception as e:
        log.exception("Error executing Podman command", command=cmd)
        return {
            "success": False,
            "error": f"Failed to execute command: {e!s}",
            "command": " ".join(cmd),
            "error_type": type(e).__name__,
        }


def check_podman_available[F: Callable[..., Any]](func: F) -> F:
    """Decorator to check Podman availability before tool execution."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not podman_available:
            return {
                "success": False,
                "error": f"Podman CLI is not available: {podman_error}",
                "suggestions": [
                    "Ensure Podman is installed (winget install RedHat.Podman)",
                    "Initialize and start your Podman machine: 'podman machine init' followed by 'podman machine start'",
                    "If using WSL2, ensure Podman is installed and running inside your default WSL distro.",
                    "Verify 'podman --version' works in your shell.",
                ],
                "error_type": "PodmanUnavailable",
            }
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            return func(*args, **kwargs)
        except Exception as e:
            log.exception("Tool execution error", tool=func.__name__)
            return {
                "success": False,
                "error": f"Operation failed: {e!s}",
                "error_type": type(e).__name__,
            }

    return cast(F, wrapper)


def get_podman_status() -> dict[str, Any]:
    """Get status overview of the Podman system."""
    status = {
        "podman_available": podman_available,
        "error": podman_error,
        "cmd_base": podman_cmd_base,
        "platform": sys.platform,
    }
    
    if podman_available:
        try:
            # Get version info
            res = subprocess.run(
                podman_cmd_base + ["version", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            if res.returncode == 0:
                import json
                try:
                    version_data = json.loads(res.stdout)
                    # Extract version details safely
                    client_version = version_data.get("Client", {}).get("Version") or version_data.get("Version")
                    server_version = version_data.get("Server", {}).get("Version")
                    status.update({
                        "version": client_version,
                        "server_version": server_version or client_version,
                        "api_version": version_data.get("Client", {}).get("APIVersion"),
                    })
                except Exception:
                    # Fallback plain text parse
                    status["version_raw"] = res.stdout.strip()
        except Exception as e:
            log.warning("Failed to get detailed version", error=str(e))
            
    return status


# Perform initial connection check
initialize_podman_connection()
