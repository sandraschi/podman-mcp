"""
Pydantic models for request/response validation.

This package contains all data models used for API request/response validation.
"""

from typing import Any

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool
    message: str
    error: str | None = None


class ContainerInfo(BaseModel):
    """Container information model."""

    id: str
    name: str
    status: str
    image: str
    created: str
    ports: dict[str, Any] | None = None
    labels: dict[str, str] | None = None


class ImageInfo(BaseModel):
    """Image information model."""

    id: str
    tags: list[str]
    created: str
    size: int
    virtual_size: int


class NetworkInfo(BaseModel):
    """Network information model."""

    id: str
    name: str
    driver: str
    scope: str
    ipam: dict[str, Any]
    containers: list[dict[str, str]] | None = None
    created: str | None = None
    labels: dict[str, str] | None = None


class VolumeInfo(BaseModel):
    """Volume information model."""

    name: str
    driver: str
    mountpoint: str
    created: str | None = None
    scope: str | None = None
    labels: dict[str, str] | None = None
    options: dict[str, str] | None = None
    usage_data: dict[str, Any] | None = None


class SystemInfo(BaseModel):
    """System information model."""

    containers: int
    containers_running: int
    containers_paused: int
    containers_stopped: int
    images: int
    driver: str
    os: str
    architecture: str
    cpus: int
    memory: int
    podman_root_dir: str
