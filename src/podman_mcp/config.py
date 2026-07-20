"""Fleet configuration for sampling and web bridge."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class SamplingConfig:
    base_url: str
    model: str
    api_key: str | None


def get_sampling_config() -> SamplingConfig:
    base = os.getenv("PODMAN_MCP_SAMPLING_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
    if not base.endswith("/v1"):
        base = f"{base}/v1" if "://" in base else "http://127.0.0.1:11434/v1"
    return SamplingConfig(
        base_url=base,
        model=os.getenv("PODMAN_MCP_SAMPLING_MODEL", "llama3.2"),
        api_key=os.getenv("PODMAN_MCP_SAMPLING_API_KEY") or None,
    )
