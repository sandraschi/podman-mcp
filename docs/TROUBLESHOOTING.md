# Troubleshooting

## Web dashboard: HTTP 500

1. Confirm the API bridge is running on **11113** (backend PowerShell window from `start.ps1`).
2. Check `customization.server` exports `app` (`from server import web_app as app`).
3. `curl http://127.0.0.1:11113/api/health` should return `healthy`.

## MCPB install fails

- Rebuild from repo root: `just mcpb-pack` (fleet shim → `dist/podman-mcp.mcpb` + `install.ps1`).
- Pack root is `mcpb/` (`mcpb/manifest.json`, staged `mcpb/src/`); prompts sync from `assets/prompts/`.
- Ensure `fastmcp>=3.4.4,<4` in your environment matches `manifest.json`.

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

## Playwright e2e fails in its own loader (ERR_MODULE_NOT_FOUND)

- Observed with Playwright 1.51 + Node 24: the failure is inside
  `playwright/lib/transform/esmLoader.js`, not in repo code. CI pins Node 22
  (`setup-node@v4`), where the suite runs. Locally, either use Node 22 or
  wait for the Playwright bump. `tsc --noEmit` + `biome ci` still gate the
  spec file statically.
