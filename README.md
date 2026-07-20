# 🦭 Podman MCP (podman-mcp)

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.5-purple.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://github.com/jlowin/fastmcp)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20WSL2-cyan.svg?style=for-the-badge&logo=windows&logoColor=white)](#requirements)
[![UI](https://img.shields.io/badge/UI-React%2019%20%2B%20Vite-blueviolet.svg?style=for-the-badge&logo=react&logoColor=white)](#webapp)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)

> A premium, daemon-less FastMCP 3.5 control plane for **Podman** container engines on Windows and WSL2 — featuring container management, native Pod orchestration, compose stacks, system analytics, and a glassmorphism React web dashboard.

---

### ❓ What is Podman?

**Podman (Pod Manager)** is a lightweight, open-source container engine designed as a modern alternative to Docker. 

While Docker relies on a monolithic background service (the Docker Daemon, `dockerd`) which can occasionally lock up or consume high idle resources on Windows, Podman operates on a **daemon-less** and **rootless-first** architecture:

*   **Zero Idle Overhead**: Since there is no background daemon running 24/7, Podman consumes virtually no memory or CPU when your containers are stopped.
*   **Fork-Exec Process Model**: Every container runs as a direct child process of your shell session, avoiding single-point-of-failure engine crashes.
*   **Native Kubernetes Pods**: Podman allows you to group multiple containers into a single shared namespace (a **Pod**), making local development match Kubernetes production environments.
*   **Docker-CLI Compatible**: Podman matches the Docker CLI commands. You can simply alias `docker` to `podman` and keep using your existing scripts.

---

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

Opens the web dashboard on `http://127.0.0.1:10806` (API bridge runs on `10807`).

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
