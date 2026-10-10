#!/usr/bin/env python3
"""
Podman MCP Server - HTTP/web bridge entry point.

Serves the FastAPI app (REST + web UI mount) for the webapp/launcher path.
MCP stdio transport lives in podmanmcp.server (``python -m podmanmcp``).
"""

import logging
import sys
import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from podman_mcp.web import setup_webapp
from podmanmcp.logging_config import LOG_FILE, configure_logging
from podmanmcp.mcp_instance import get_mcp

# Initialize MCP + tools before web routes import podmanmcp tool modules
mcp = get_mcp()

# Suppress all warnings
warnings.filterwarnings("ignore")

# Configure root logger to be silent
logging.basicConfig(level=logging.CRITICAL, force=True, handlers=[logging.NullHandler()])

# Silence common noisy loggers
for logger_name in ["fastmcp", "mcp", "uvicorn", "httpx", "httpcore", "h11", "asyncio"]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# Configure our specific logging
configure_logging(
    enable_console=True,
    json_format=False,
    log_file=str(LOG_FILE),
    level="WARNING",
)


@asynccontextmanager
async def _web_lifespan(_app: FastAPI):
    from podman_mcp.activity_log import install_log_handler, log_activity
    from podman_mcp.llm.manager import get_llm_manager

    install_log_handler()
    log_activity("system", "Podman MCP web bridge starting")
    await get_llm_manager().glom_local_providers_if_up()
    log_activity("system", "Podman MCP web bridge ready")
    yield


# FastAPI Bridge - auth only on /api/chat so dashboard/containers work without login
web_app = FastAPI(title="Podman Management Web Bridge", lifespan=_web_lifespan)

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:11112",
        "http://localhost:11112",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup webapp bridge with the tool-loaded MCP instance
setup_webapp(web_app, mcp_app=mcp)


def _mount_web_ui(app: FastAPI) -> None:
    """Serve built web_sota for Tauri / single-port installs."""
    from pathlib import Path

    from fastapi.staticfiles import StaticFiles

    dist = Path(__file__).resolve().parent.parent / "web_sota" / "dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=str(dist), html=True), name="web-ui")


_mount_web_ui(web_app)


if __name__ == "__main__":
    sys.exit("Use the fleet launcher (start.ps1) or uvicorn customization.server:app for HTTP.")
