# podman-mcp — Copilot instructions

## Session Context (podman-mcp)
Before starting work: read `llms-full.txt` for the 9 manage_* tools (ports 11112/11113); check Podman CLI health via manage_system status before compose/up.
At end of work: run `uv run ruff check src/` + `uv run pytest tests/ -q`; never commit `.env`.
