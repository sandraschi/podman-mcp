# ADN-004: Podman MCP v3.5.0 — Release Status & Complete Gap Closure

*   **Status**: Approved
*   **Deciders**: Sandra Schimanovich, LLM Agent
*   **Date**: 2026-07-26

---

## 1. Context

Podman MCP was forked from docker-mcp with only port changes (10806/10807 → 11112/11113) but the tool surface and dashboard did not reflect Podman's unique capabilities. The dashboard showed a generic "Failed to fetch" error with no actionable instructions, and 34 stale port references across the codebase broke the health polling in dev mode.

---

## 2. Changes Made

### 2.1 Port Correction
All 34 instances of docker-mcp ports (10806/10807) corrected to podman-mcp registered ports (11112/11113) across 14 files. Root cause: health poller in app-layout.tsx hit port 10807 → connection store stayed offline → dashboard showed error state.

### 2.2 Dashboard Error UX — 4 Categorized States

| State | Trigger | Instructions |
|-------|---------|-------------|
| `backend_down` | fetch fails entirely | Run `.\start.ps1` |
| `podman_missing` | CLI not found | `winget install RedHat.Podman` + machine init/start |
| `podman_not_started` | machine stopped | `podman machine start` + restart button |
| `podman_error` | other tool failure | Troubleshooting checklist |

### 2.3 Rootless Mode Detection
Auto-detected from `podman info --format json` → `host.security.rootless`. Shown as green "Rootless" or amber "Rootful" badge in dashboard hero. Daemonless and "Pods native" badges also added.

### 2.4 New Tool Surface (4 tools added, 3 extended)

| Operation | Tool | Value |
|-----------|------|-------|
| `manage_migrate` | New tool | Docker↔Podman porting (compose conversion, image migration, compatibility check, export for Docker) |
| `manage_backup` | New tool | Save/load images, containers, volumes, compose snapshots |
| `manage_agentic` | New tool | Multi-step workflows with dry-run safety |
| `manage_health` | New tool | Restart/OOM detection, log error analysis, recommendations |
| `exec`, `files`, `resources` | Added to containers | In-container command execution, file I/O, CPU/memory limits |
| `generate_systemd` | Added to system | Container→systemd unit generation (Podman-unique) |
| `build`, `config`, `debug` | Added to compose | Compose build, config validation, debug diagnostics |

### 2.5 Documentation (all created/rewritten)

- `CHANGELOG.md`, `PRD.md`, `AGENTS.md`, `.env.example` — created
- `llms-full.txt` — rewritten (was 5000 lines of GitHub setup guides from advanced-memory-mcp)
- `llms.txt`, `glama.json`, `README.md` — updated
- MCD project page (`projects/podman-mcp/README.md`) — updated with architecture diagram
- Fleet index entry added

---

## 3. Compliance Gaps (Open Items)

| Gap | Priority | Impact |
|-----|----------|--------|
| Tauri native directory not present | Medium | No NSIS installer for non-dev users |
| CUA smoke test not configured | Medium | Can't certify NSIS builds |
| `.cursorrules` missing | Low | No session context injection for Cursor |
| `data-testid` on KPI cards missing | Low | CUA tests can't target KPIs by testid |
| `prefab-ui` dependency not in pyproject.toml | Low | Prefab cards not usable |
| Stale ADN file `SEP-1577-in-Docker-MCP...` | Low | Cleanup from docker-mcp fork |
| GitHub release not created | Low | v3.5.0 tag exists in pyproject only |

---

## 4. Next Steps

1. Address remaining gaps in priority order
2. Create native/ Tauri directory for NSIS builds
3. Add `.cursorrules` for session context injection
4. Remove stale ADN file carried over from docker-mcp fork
