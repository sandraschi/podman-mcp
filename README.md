# podman-mcp

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.5-purple.svg)](https://github.com/jlowin/fastmcp)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/sandraschi/podman-mcp/pulls)

FastMCP 3.5 control plane for Podman — containers, images, volumes, networks, Compose, daemon recovery, **AI chat**, **backup/restore**, **image comparison**, **container analysis**, and a React web dashboard.

## Install

| Method | Command |
|--------|---------|
| **Claude Desktop** | `just mcpb-pack` → drag `.mcpb` onto Claude |
| **Windows (NSIS)** | `just build-native` → run `*-setup.exe` |
| **Dev (any OS)** | `uv sync && .\start.ps1` → `localhost:10806` |

## Quick Start

```powershell
git clone https://github.com/sandraschi/podman-mcp
cd podman-mcp
uv sync
.\start.ps1
```

Opens `http://127.0.0.1:10806` (API bridge on `10807`).

## What You Can Do

- "List all running containers and show resource usage."
- "Deploy my compose stack and verify every service is healthy."
- "Compare nginx:1.25 and nginx:1.26 — what changed?"
- "Analyze container my-app — why is it restarting?"
- "Back up my database volume before the upgrade."

## Feature Overview

| Area | Highlights |
|------|------------|
| **Containers** | CRUD, logs, stats, exec, inspect, health analysis |
| **Images** | List, pull, build, tag, push, prune, search, compare |
| **Compose** | Projects, up/down, logs, config, YAML file analysis |
| **Backup/Restore** | `save/load image`, `backup/restore volume`, `export compose` |
| **Podman Machine** | Status, hang detection, triple-kill recovery, restart |
| **AI Chat** | SSE streaming, tool execution cards, LLM provider discovery |
| **Agentic** | Deploy, cleanup, diagnose, rollback workflows |
| **Prefab Cards** | Containers, images, daemon status, system info |

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/TOOLS.md](docs/TOOLS.md) | Full MCP tool reference |
| [docs/COMPOSE.md](docs/COMPOSE.md) | Compose management & file analysis |
| [docs/BACKUP.md](docs/BACKUP.md) | Podman backup & restore guide |
| [docs/CHAT.md](docs/CHAT.md) | AI chat & agentic workflows |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Stack, transport, REST API |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Environment variables |
| [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) | Build, just recipes, testing |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues |

## Requirements

Python 3.12+, Podman Engine 20.10+, Node.js 20+ (dev). Rust 1.70+ (Tauri build only).

## License

MIT
