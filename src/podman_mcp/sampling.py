"""OpenAI-compatible sampling handler (FastMCP 3.3 fleet pattern)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from podman_mcp.config import SamplingConfig

logger = logging.getLogger(__name__)

try:
    from fastmcp import Context
except ImportError:
    from fastmcp.server.context import Context  # type: ignore[attr-defined]


class PodmanSamplingHandler:
    """Route MCP sampling to Ollama / LM Studio OpenAI-compatible APIs."""

    def __init__(self, config: SamplingConfig) -> None:
        self.config = config

    async def __call__(
        self,
        context: Context,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        del context
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools

        headers: dict[str, str] = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        async with httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=headers,
            timeout=120.0,
        ) as client:
            response = await client.post("/chat/completions", json=payload)
            response.raise_for_status()
            return response.json()
