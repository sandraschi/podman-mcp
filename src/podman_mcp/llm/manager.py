"""Fleet SOTA: auto-discover Ollama and LM Studio on startup."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class LLMManager:
    """Track reachable local inference endpoints."""

    def __init__(self) -> None:
        self.providers: dict[str, dict[str, Any]] = {}

    def register(self, provider_type: str, base_url: str, *, models: list[str] | None = None) -> None:
        self.providers[provider_type] = {
            "type": provider_type,
            "base_url": base_url,
            "models": models or [],
            "reachable": True,
        }
        logger.info("LLM glom: registered %s at %s", provider_type, base_url)

    def list_providers(self) -> list[dict[str, Any]]:
        return list(self.providers.values())

    async def glom_local_providers_if_up(self, *, force: bool = False) -> None:
        if os.getenv("PODMAN_MCP_LLM_GLOM", "1").strip().lower() in (
            "0",
            "false",
            "no",
            "off",
        ):
            return
        if force:
            self.providers.clear()

        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        lm_url = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234").rstrip("/")
        timeout = httpx.Timeout(2.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            if "ollama" not in self.providers:
                try:
                    response = await client.get(f"{ollama_url}/api/tags")
                    if response.status_code == 200:
                        payload = response.json()
                        models = [m.get("name", "") for m in payload.get("models", []) if m.get("name")]
                        self.register("ollama", ollama_url, models=models)
                except Exception:
                    logger.debug("LLM glom: Ollama not reachable", exc_info=True)
            if "lmstudio" not in self.providers:
                try:
                    response = await client.get(f"{lm_url}/v1/models")
                    if response.status_code == 200:
                        payload = response.json()
                        models = [m.get("id", "") for m in payload.get("data", []) if m.get("id")]
                        self.register("lmstudio", lm_url, models=models)
                except Exception:
                    logger.debug("LLM glom: LM Studio not reachable", exc_info=True)


_llm_manager: LLMManager | None = None


def get_llm_manager() -> LLMManager:
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
