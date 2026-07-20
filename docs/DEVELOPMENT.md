# Development

## Setup

```powershell
uv sync
cd web_sota
npm install
```

## Run

| Command | Purpose |
|---------|---------|
| `.\start.ps1` | Web UI (10806) + API (10807) |
| `just run` | MCP stdio server |
| `just webapp-dev` | Vite only |
| `just check` | Ruff + Biome |

## MCPB bundle

```powershell
npx @anthropic-ai/mcpb pack . dist/podman-mcp-v3.3.0.mcpb
```

Uses root `manifest.json` and `.mcpbignore` per [mcp-central-docs MCPB standards](https://github.com/sandraschi/mcp-central-docs).

## Tauri native (Windows)

```powershell
just build-native
```

Pipeline: `web_sota` build → PyInstaller sidecar → `npx tauri build`.

Outputs under `native/target/release/bundle/`:

- `nsis/Podman MCP_3.3.0_x64-setup.exe`
- `msi/Podman MCP_3.3.0_x64_en-US.msi`

Prerequisites: Rust (rustup), Node 20+, uv, PyInstaller (installed via uv).

## Fleet surface

Registered in `podmanmcp/fleet_surface.py`:

- MCP prompts: `podman_deploy_stack`, `podman_daemon_health_check`
- Resources: `resource://podman-mcp/skills`, `resource://podman-mcp/capabilities`
- Prefab tools: `podman_containers_card`, `podman_desktop_status_card`, `podman_system_info_card`
