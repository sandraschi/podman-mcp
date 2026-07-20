# Troubleshooting

## Web dashboard: HTTP 500

1. Confirm the API bridge is running on **10807** (backend PowerShell window from `start.ps1`).
2. Check `customization.server` exports `app` (`from server import web_app as app`).
3. `curl http://127.0.0.1:10807/api/health` should return `healthy`.

## MCPB install fails

- Rebuild from repo root: `just mcpb-pack` or `npx @anthropic-ai/mcpb pack . dist/podman-mcp-v3.3.0.mcpb`.
- Use root `manifest.json` and `assets/prompts/` (there is no `mcpb/` subfolder).
- Ensure `fastmcp>=3.3` in your environment matches `manifest.json`.

## Sampling / agentic workflow unavailable

- Start **Ollama** (11434) or **LM Studio** (1234).
- Set `PODMAN_MCP_SAMPLING_BASE_URL` if not using default Ollama.
- Use a client that supports MCP sampling (Cursor, Claude Desktop).

## Tauri build

- Run `native/ensure-sidecar-stub.ps1` before `cargo check` if sidecar is missing.
- Full release: `just build-native` (requires Rust toolchain).
- Webapp for Tauri must be built with `VITE_API_BASE=http://127.0.0.1:10807`.

## Podman CLI errors

- Verify Podman Machine is running: `podman ps` in a terminal.
- On Windows, socket default: `//./pipe/podman_engine`.
