# Changelog

## v3.5.2 — 2026-10-10

- **Gates green**: `pyright src/` 0 errors (was 435), `ruff check`/`format` clean with S110/S112 + T20 enforced, pytest 21 passed, `tsc` clean, `biome ci` clean (config migrated 1.9 → 2.5), coverage floor `--cov-fail-under=20`.
- **Critical entrypoint fix**: `python -m podmanmcp` (the MCPB stdio entry) called `asyncio.run()` on a sync runner → instant exit 1; now calls `run_server()` directly. Proven live: stdio initialize + tools/list returns 15/15 tools.
- **Crash-path fixes**: structlog-style `error=` kwargs on stdlib loggers (TypeError on every JSON-parse failure) in containers/images/pods; 18 silent `try/except: pass` JSON fallbacks now log at debug.
- **Shutdown surface**: new `podman_shutdown` MCP tool (confirm-gated) + `POST /api/shutdown`; proven live (backend exits ~500 ms after POST).
- **REST discovery**: added `GET /api/skills`, `GET /api/status`, `GET /api/llm/discover|models|onboarding`, `POST /api/llm/chat` (alias); all probed 200 live.
- **Frontend**: same-origin API base with Tauri gate (no more hardcoded `127.0.0.1:11113` outside Tauri); Chat gains Operator + Custom personalities; 5 `text-xs`/contrast and a11y/keys/hooks-deps findings fixed.
- **Hygiene**: removed dead `workflow_intel/` + `podmanmcp/core/` (zero importers, 280 type errors), moved stray `src/test_*.py` to `scripts/legacy/`, sampling config/handler relocated into `podmanmcp/` so the MCPB bundle is self-contained (clean-room verified: 15/15 tools from bundle files only).
- **CI**: new `.github/workflows/ci.yml` (ruff, format, pyright, pytest, node 22, npm ci, biome, tsc); session channels added (Claude Code, Cursor, Windsurf, Copilot, OpenCode, Antigravity).
- **Packaging**: fleet `scripts/mcpb-pack.ps1` shim + `mcpb/manifest.json`; `dist/podman-mcp-v3.5.2.mcpb` (+ stable + `install.ps1`) built and clean-room verified (15/15 tools from bundle files only).
- **Deferred round**: `GET /api/events` (engine event feed with graceful engine-down) + unit tests; new **Inbox** (event stream, auto-refresh, engine banner) and **Skills** (prompt/tool catalog with copy) pages + nav; `skills/podman-mcp/SKILL.md`; Zustand `store/llm.ts` (providers, model, personality, GPU probe) with Chat migrated; Chat skill chips, 6 example prompts, `chat-controls`/`chat-messages`/`chat-llm-status` testids; every page now carries 3+ `data-testid`s; npm-over-bun decision documented in `docs/DEVELOPMENT.md`.

## v3.5.1 — 2026-09-13

- **Dashboard**: fix false "Podman is not installed" when the CLI works but the engine/machine is down (empty `message` + misleading fallback text).
- **Backend**: classify Podman failures (`podman_missing` vs `podman_not_started` vs `podman_error`); expose `podman_error_kind` and `podman_context` on `/api/dashboard`.
- **Windows**: discover `podman.exe` under `%LOCALAPPDATA%\Programs\Podman` when not on PATH; fleet start sets `PODMAN_CMD` in `fleet-start.config.ps1`.
- **Tools**: error responses now include `message` for web/API consumers.

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
