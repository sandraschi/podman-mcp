# Podman MCP — Product Requirements Document

**Version**: 3.5.0  
**Status**: Active development  
**Last Updated**: 2026-07-26

## Purpose

Podman MCP is an AI-agent control plane for Podman container engines on Windows and WSL2. It exposes Podman's full CLI surface as MCP tools consumable by LLM agents (Claude Desktop, Cursor, opencode) and provides a React web dashboard for manual management.

## Architecture

```
LLM Agent (Claude / Cursor / opencode)
     │
     ├── stdio JSON-RPC ──► FastMCP (podman-mcp singleton)
     │                          │
     │                      [Portmanteau Tools]
     │                      manage_containers, manage_pods, manage_images,
     │                      manage_system, manage_compose, manage_backup,
     │                      manage_migrate, manage_agentic, manage_health
     │                          │
     └── HTTP REST ────────► FastAPI Bridge (127.0.0.1:11113)
                                │
                            podman CLI (native / WSL2)
                                │
                            Podman Machine (WSL2 VM)
```

```
React Webapp (:11112)  ──►  FastAPI (:11113)  ──►  podman CLI  ──►  Podman Machine
```

## Shipped Features (v3.5.0)

### Tool Surface — 9 portmanteau tools (70+ operations)

| Tool | Domain |
|------|--------|
| `manage_containers` | CRUD, logs, stats, exec, files (in-container I/O), resource limits |
| `manage_pods` | Kubernetes-style pod lifecycle |
| `manage_images` | Pull, build, search, inspect, delete |
| `manage_system` | Machine lifecycle, generate systemd, volumes, networks, prune |
| `manage_compose` | Up/down/ps/logs/build/config/debug with --workdir |
| `manage_backup` | Image/container/volume/compose save and restore |
| `manage_migrate` | Docker↔Podman porting: compose conversion, image migration, compatibility check |
| `manage_agentic` | Multi-step workflows with dry-run safety |
| `manage_health` | Container analysis, restart detection, OOM, recommendations |

### Webapp — 13 pages

Dashboard, Containers, Pods, Images, Volumes, Networks, Compose, Migrate (Docker↔Podman), AI Command (chat), MCP Tools, Event Logs, Help, Settings

### Dashboard

- Rootless mode detection (from `podman info`)
- Daemonless badge, Pods native badge
- 4 error states with step-by-step instructions (backend down, Podman missing, machine not started, generic)
- 5 KPI cards (Containers, Pods, CPU, Memory, Storage)
- Status log + images preview panel

### Docker↔Podman Migration

- docker-compose.yml ↔ podman-compose.yml conversion
- Docker Hub image pull for Podman
- Compose compatibility checker
- Dockerfile→Containerfile copy
- Podman→Docker OCI archive export
- CLI cheat sheet on `/migrate` page

## Stack

- **Backend**: FastMCP 3.5 · Python 3.12+ · uv · FastAPI
- **Frontend**: React 19 · Vite · Tailwind CSS · Zustand · Lucide Icons
- **Dev**: just · tsc · Ruff
- **Dist**: MCPB (Claude Desktop) · Tauri NSIS (native installer)

## Ports

| Port | Service |
|------|---------|
| 11112 | Frontend (Vite React) |
| 11113 | Backend (FastAPI + FastMCP HTTP `/mcp`) |

## Non-Goals

- Docker Desktop GUI parity (Podman is CLI-first)
- Docker Swarm / Docker Compose v2 plugin features
- Kubernetes cluster orchestration (Pods only, not clusters)
- Buildah as a separate tool surface (buildah is used internally by `podman build`)
- Monitoring stack (Grafana/Prometheus) — separate concern, see monitoring-mcp
