"""
Utility functions for PodmanMCP.

This module provides helper functions used throughout the PodmanMCP application.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from podman import PodmanClient
from podman.errors import PodmanException

# Configure logger
logger = logging.getLogger(__name__)


def get_podman_client() -> PodmanClient:
    """Get a Podman client instance.

    Returns:
        PodmanClient: A Podman client instance.

    Raises:
        RuntimeError: If Podman is not installed or the Podman CLI is not running.
    """
    try:
        return PodmanClient.from_env()
    except PodmanException as e:
        logger.error("Failed to initialize Podman client: %s", e)
        raise RuntimeError(
            "Podman is not installed or the Podman CLI is not running. "
            "Please make sure Podman is installed and running."
        ) from e


def run_command(
    cmd: str | list[str],
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    capture_output: bool = True,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a shell command and return the result.

    Args:
        cmd: Command to run as a string or list of arguments.
        cwd: Working directory for the command.
        env: Environment variables to set for the command.
        capture_output: Whether to capture stdout and stderr.
        check: Whether to raise an exception if the command fails.

    Returns:
        subprocess.CompletedProcess: The result of the command execution.

    Raises:
        subprocess.CalledProcessError: If the command fails and check is True.
    """
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False
        cmd = [str(arg) for arg in cmd]

    try:
        return subprocess.run(  # noqa: S603
            cmd,
            cwd=str(cwd) if cwd else None,
            env=env,
            shell=shell,
            check=check,
            capture_output=capture_output,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        logger.error("Command failed with exit code %d: %s", e.returncode, e)
        if e.stderr:
            logger.error("Error output: %s", e.stderr.strip())
        raise
    except FileNotFoundError as e:
        logger.error("Command not found: %s", cmd)
        raise RuntimeError(f"Command not found: {cmd[0] if isinstance(cmd, list) else cmd}") from e


def parse_json_output(output: str) -> Any:
    """Parse JSON output from a command.

    Args:
        output: JSON string to parse.

    Returns:
        Parsed JSON data.

    Raises:
        ValueError: If the output is not valid JSON.
    """
    try:
        return json.loads(output)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON: %s", e)
        raise ValueError(f"Invalid JSON output: {e}") from e


def ensure_directory(path: str | Path) -> Path:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory.

    Returns:
        Path: The path to the directory.
    """
    path = Path(path).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def format_bytes(size: float) -> str:
    """Format a size in bytes to a human-readable string.

    Args:
        size: Size in bytes.

    Returns:
        Formatted string with appropriate unit (e.g., "1.5 MB").
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def format_size(size_bytes: int) -> str:
    """Format a size in bytes to a human-readable string.

    This is an alias for format_bytes for backward compatibility.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted string with appropriate unit (e.g., "1.5 MB").
    """
    return format_bytes(size_bytes)


def parse_size(size_str: str) -> int:
    """Parse a human-readable size string to bytes.

    Args:
        size_str: Size string (e.g., '1.5MB', '500K', '2G').

    Returns:
        Size in bytes.

    Raises:
        ValueError: If the size string is invalid.
    """
    size_str = size_str.strip().upper()
    if not size_str:
        raise ValueError("Empty size string")

    # Find the numeric part
    num_str = ""
    i = 0
    while i < len(size_str) and (size_str[i].isdigit() or size_str[i] == "."):
        num_str += size_str[i]
        i += 1

    if not num_str:
        raise ValueError(f"Invalid size format: {size_str}")

    try:
        num = float(num_str)
    except ValueError as e:
        raise ValueError(f"Invalid number in size: {num_str}") from e

    # Get the unit
    unit = size_str[i:] if i < len(size_str) else "B"

    # Convert to bytes
    units = {
        "B": 1,
        "K": 1024,
        "KB": 1024,
        "M": 1024**2,
        "MB": 1024**2,
        "G": 1024**3,
        "GB": 1024**3,
        "T": 1024**4,
        "TB": 1024**4,
    }

    if unit not in units:
        raise ValueError(f"Unknown size unit: {unit}")

    return int(num * units[unit])


def human_readable_to_bytes(size_str: str) -> int:
    """Convert a human-readable size string to bytes.

    This is an alias for parse_size for backward compatibility.

    Args:
        size_str: Human-readable size string (e.g., '1.5MB', '500K', '2G').

    Returns:
        Size in bytes.

    Raises:
        ValueError: If the size string is invalid.
    """
    return parse_size(size_str)


def is_podman_installed() -> bool:
    """Check if Podman is installed and running.

    Returns:
        bool: True if Podman is installed and running, False otherwise.
    """
    try:
        client = get_podman_client()
        client.ping()
        return True
    except Exception:
        return False


def get_environment_vars() -> dict[str, str]:
    """Get environment variables with sensitive values redacted.

    Returns:
        Dictionary of environment variables with sensitive values redacted.
    """
    sensitive_keys = {"PASSWORD", "SECRET", "TOKEN", "KEY", "CREDENTIALS"}
    env_vars = {}

    for key, value in os.environ.items():
        if any(sensitive in key.upper() for sensitive in sensitive_keys):
            env_vars[key] = "***REDACTED***"
        else:
            env_vars[key] = value

    return env_vars


def validate_file_exists(file_path: str | Path) -> Path:
    """Validate that a file exists and return its Path object.

    Args:
        file_path: Path to the file.

    Returns:
        Path: The resolved path to the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    return path


def validate_directory_exists(dir_path: str | Path) -> Path:
    """Validate that a directory exists and return its Path object.

    Args:
        dir_path: Path to the directory.

    Returns:
        Path: The resolved path to the directory.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    path = Path(dir_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {dir_path}")
    return path
