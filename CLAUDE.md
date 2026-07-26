# podman-mcp — Claude / agent context

Podman control plane. Ports **11112** (frontend) / **11113** (backend).

## Do

- Prefer portmanteau tools (`manage_containers`, `manage_compose`, …)
- Check Podman machine health before heavy compose/up
- Follow `docs/ONBOARDING.md` when Podman is missing or hung

## Don't

- Assume Docker Desktop is the engine
- Collide with docker-mcp ports (10806/10807)
- Commit `.env` or live compose secrets

## Commands

```powershell
.\start.ps1
uv run pytest
just mcpb-pack
```

See AGENTS.md, README.md, llms-full.txt.
