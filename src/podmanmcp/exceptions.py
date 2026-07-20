"""
Custom exceptions for the Podman MCP application.

This module defines custom exceptions that are used throughout the application.
"""


class PodmanMCPError(Exception):
    """Base exception for all Podman MCP errors."""

    pass


class ToolError(PodmanMCPError):
    """Raised when a tool encounters an error during execution."""

    pass


class PodmanOperationError(PodmanMCPError):
    """Raised when a Podman operation fails."""

    pass


class ContainerError(PodmanMCPError):
    """Raised when a container operation fails."""

    pass


class ImageError(PodmanMCPError):
    """Raised when an image operation fails."""

    pass


class NetworkError(PodmanMCPError):
    """Raised when a network operation fails."""

    pass


class VolumeError(PodmanMCPError):
    """Raised when a volume operation fails."""

    pass


class ValidationError(PodmanMCPError):
    """Raised when input validation fails."""

    pass


class ConfigurationError(PodmanMCPError):
    """Raised when there is a configuration error."""

    pass


class NotFoundError(PodmanMCPError):
    """Raised when a resource is not found."""

    pass


class UnauthorizedError(PodmanMCPError):
    """Raised when authentication or authorization fails."""

    pass


class TimeoutError(PodmanMCPError):
    """Raised when an operation times out."""

    pass


# For backward compatibility
ToolError = ToolError
