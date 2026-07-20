"""
FastAPI routes for Podman MCP webapp
"""

import logging
import os

import podman
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI app with Podman endpoints"""

    app = FastAPI(title="Podman MCP API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:10807",
            "http://localhost:10807",
            "http://goliath:10807",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize Podman client
    try:
        client = podman.from_env()
    except Exception as e:
        logger.error(f"Failed to connect to Podman: {e}")
        client = None

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    # Dashboard endpoint
    @app.get("/api/dashboard")
    async def get_dashboard():
        """Get dashboard overview with system info and container status"""
        if not client:
            raise HTTPException(status_code=503, detail="Podman not available")

        try:
            # Get system info
            info = client.info()
            version = client.version()

            # Get containers
            containers = client.containers.list(all=True)
            running = len([c for c in containers if c.status == "running"])

            # Get images
            images = client.images.list()

            # Calculate disk usage
            disk_info = client.df()
            total_size = sum(i.get("Size", 0) for i in disk_info.get("Images", []))

            return {
                "system_info": {
                    "podman_version": version.get("Version"),
                    "containers": {
                        "total": len(containers),
                        "running": running,
                        "paused": len([c for c in containers if c.status == "paused"]),
                        "stopped": len(containers) - running,
                    },
                    "images": {
                        "total": len(images),
                    },
                    "memory": {
                        "total": info.get("MemTotal", 0),
                        "total_formatted": f"{info.get('MemTotal', 0) / (1024**3):.1f}GB",
                    },
                    "cpu": {
                        "cores": info.get("NCPU", 0),
                    },
                },
                "containers": [
                    {
                        "id": c.id[:12],
                        "name": c.name,
                        "status": c.status,
                        "image": c.image.tags[0] if c.image.tags else c.image.id[:12],
                        "state": "running" if c.status == "running" else "stopped",
                    }
                    for c in containers[:10]
                ],
                "containers_status": "success",
                "containers_message": f"Total: {len(containers)} containers",
                "disk_summary": {
                    "total_containers_size": sum(c.get("SizeRw", 0) for c in disk_info.get("Containers", [])),
                    "total_images_size": sum(i.get("Size", 0) for i in disk_info.get("Images", [])),
                    "total_volumes_size": sum(
                        v.get("UsageData", {}).get("Size", 0) for v in disk_info.get("Volumes", [])
                    ),
                    "total_size": total_size,
                },
                "images": [
                    {
                        "id": img.id[:12],
                        "repo_tags": img.tags or ["<none>"],
                        "size": img.attrs.get("Size", 0),
                        "created": img.attrs.get("Created"),
                    }
                    for img in images[:10]
                ],
                "images_count": len(images),
                "images_status": "success",
                "system_status": "success",
            }
        except Exception as e:
            logger.error(f"Error getting dashboard: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    # Containers endpoint
    @app.get("/api/containers")
    async def get_containers():
        """Get list of all containers"""
        if not client:
            raise HTTPException(status_code=503, detail="Podman not available")

        try:
            containers = client.containers.list(all=True)
            return {
                "containers": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "status": c.status,
                        "image": c.image.tags[0] if c.image.tags else c.image.id[:12],
                        "state": "running" if c.status == "running" else "stopped",
                        "created": c.attrs.get("Created"),
                    }
                    for c in containers
                ],
                "status": "success",
            }
        except Exception as e:
            logger.error(f"Error getting containers: {e}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    # Tools endpoint
    @app.get("/api/tools")
    async def get_tools():
        """Get list of available MCP tools"""
        podman_desktop_tools = [
            "podman_desktop_status",
            "podman_daemon_recover",
            "podman_daemon_restart",
            "podman_desktop_update",
        ]

        container_tools = [
            "list_containers",
            "start_container",
            "stop_container",
            "restart_container",
            "remove_container",
            "get_container_logs",
        ]

        return {
            "tools": podman_desktop_tools + container_tools,
            "podman_desktop_tools": podman_desktop_tools,
            "container_tools": container_tools,
        }

    @app.get("/api/v1/diagnostics")
    async def diagnostics():
        try:
            import psutil

            cpu = psutil.cpu_percent()
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").percent
        except ImportError:
            cpu = mem = disk = None
        return {
            "success": True,
            "backend": {"port": 10807, "status": "running"},
            "system": {"cpu_percent": cpu, "memory_percent": mem, "disk_percent": disk},
            "tools": {"total": 0},
            "cua_status": {"tesseract_available": False, "window_found": False},
        }

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    host = os.environ.get("HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=10807)
