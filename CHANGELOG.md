# Changelog

## v3.5.0 — 2026-07-26

- **Dashboard overhaul**: rootless mode detection badge, daemonless architecture highlights, 4 categorized error states with step-by-step fix instructions (backend down, Podman missing, machine not started, generic error)
- **New tool: `manage_migrate`** — Docker↔Podman porting (compose file conversion, image migration, compatibility check, Dockerfile→Containerfile, export for Docker)
- **New tool: `manage_backup`** — save/load images, export/import containers, backup/restore volumes, compose project snapshots
- **New tool: `manage_agentic`** — multi-step orchestrations with dry-run safety (deploy_compose, cleanup, diagnose, rollback, health_sweep)
- **New tool: `manage_health`** — container restart loops, OOM detection, log error analysis, system overview, prioritized recommendations
- **Extended `manage_containers`**: added exec (run commands), files (list/read/write in-container), resources (get/set CPU & memory limits)
- **Extended `manage_system`**: added generate_systemd (container→systemd unit)
- **Extended `manage_compose`**: added build, config, debug operations
- **New webapp page**: `/migrate` — Docker↔Podman migration UI with tool call examples and CLI cheat sheet
- **Port fix**: all 34 instances corrected from docker-mcp origin (10806/10807) to podman-mcp registered ports (11112/11113)
- **Rootless mode**: auto-detected from `podman info` and displayed in hero badge

## v3.4.0 — 2026-07-22

- Portmanteau tool consolidation: pods, volumes, networks, compose operations
- Webapp: pods page, volumes page, networks page, compose page
- Sidebar expanded to 12 navigation items
- FastMCP 3.4+ sampling support
- MCPB packaging support

## v3.0.0 — 2026-07-20

- Initial fleet registration: ports 11112/11113
- 5 portmanteau tools (41 operations)
- React/Vite webapp with glassmorphism dark theme
- FastMCP 3.2 dual-transport (stdio + HTTP)
- Podman machine lifecycle (init/start/stop/list)
