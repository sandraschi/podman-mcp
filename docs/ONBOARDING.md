# Onboarding — podman-mcp

## What this is for

Drive **Podman** (containers, pods, compose, images, backup) from agents and a React dashboard on Windows / WSL2. Prefer this when you want daemon-less / rootless containers instead of Docker Desktop.

## Cost / prerequisites

| Question | Answer |
|----------|--------|
| Podman installed? | Required — Podman Engine 20.10+ (Windows or WSL2) |
| Docker? | Optional; migrate tools can help move compose stacks |
| Cloud fees? | None for local Podman |

## Setup

```powershell
cd D:\Dev\repos\podman-mcp
uv sync
.\start.ps1
```

Fleet launcher: `mcp-central-docs\starts\podman-mcp-start.bat`

- Dashboard: http://127.0.0.1:11112  
- Backend / MCP: http://127.0.0.1:11113  

## Pitfalls

- Machine not running → `manage_system` machine_start / hang recovery
- Confusing with docker-mcp — different engine; ports **11112/11113**
- WSL2 vs native Podman path resolution — see `docs/TROUBLESHOOTING.md`
