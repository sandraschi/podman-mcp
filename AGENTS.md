# podman-mcp — AGENTS.md

## Quick Reference

| | |
|---|---|
| **Ports** | Backend 11113 · Frontend 11112 · MCP /mcp |
| **Stack** | FastMCP 3.5 · Python 3.12+ · uv · React 19 · Vite · Tailwind |
| **Start** | `.\web_sota\start.ps1` |
| **Tests** | `uv run pytest` |
| **Lint** | `npx tsc --noEmit` (web_sota) |
| **Build NSIS** | `just build-native` |
| **CUA smoke** | `just cua-nsis-test` |

## Tool Pattern

All tools follow the portmanteau pattern — one function per domain with `operation: Literal[...]` discriminator. Tools auto-register via `@mcp.tool()` decorator on import.

| Tool | Module | Operations |
|------|--------|-----------|
| `manage_containers` | `tools/containers.py` | list, inspect, start, stop, restart, delete, create, logs, stats, exec, files, resources |
| `manage_pods` | `tools/pods.py` | list, inspect, create, start, stop, delete |
| `manage_images` | `tools/images.py` | list, inspect, pull, delete, build, search |
| `manage_system` | `tools/system.py` | status, info, machine_list/init/start/stop, prune, generate_systemd, volume_*, network_* |
| `manage_compose` | `tools/compose.py` | up, down, ps, logs, build, config, debug |
| `manage_backup` | `tools/backup.py` | save_image, load_image, export_container, import_container, save/load_volume, save_compose, list_backups |
| `manage_migrate` | `tools/migrate.py` | docker_compose_to_podman, podman_compose_to_docker, scan_docker_artifacts, migrate_image, compatibility_check, dockerfile_to_containerfile, export_for_docker |
| `manage_agentic` | `tools/agentic.py` | deploy_compose, cleanup, diagnose, rollback, health_sweep |
| `manage_health` | `tools/health.py` | container_analyze, system_overview, recommendations |

## Key Files

| File | Purpose |
|------|---------|
| `src/server.py` | FastAPI app + CORS + lifespan + web UI mount |
| `src/podmanmcp/mcp_instance.py` | FastMCP singleton, tool registration trigger |
| `src/podmanmcp/tool_registration.py` | Imports all tool modules (decorators fire on import) |
| `src/podmanmcp/podman_context.py` | Podman CLI resolution (native/WSL2), `run_podman_command()`, `check_podman_available` decorator |
| `src/podman_mcp/web.py` | All REST endpoints: dashboard, health, chat, diagnostics, compose REST bridge |
| `web_sota/src/App.tsx` | React router (13 routes) |
| `web_sota/src/lib/api.ts` | API_BASE constant |
| `web_sota/src/store/connection.ts` | Zustand store for backend connection state |

## Add a Tool

1. Create `src/podmanmcp/tools/yourname.py` with `@mcp.tool()` + `@check_podman_available`
2. Add import to `src/podmanmcp/tool_registration.py`
3. Import auto-registers at server start — no other changes needed
