# Podman MCP — Improvement Plan

## 1. Podman Compose CRUD + Debug

| Feature | Description |
|---------|-------------|
| `compose_list` | List all compose projects (detect from labels, working dirs) |
| `compose_up/down` | Start/stop compose stacks by project name |
| `compose_logs` | Tail logs for a compose service |
| `compose_config` | Validate and render compose YAML |
| `compose_build` | Rebuild images for a compose service |
| `compose_debug` | Inspect container state within compose context (exit codes, restart policy violations, port conflicts) |

**Implementation:** New module `src/podmanmcp/tools/compose.py`. Uses Podman Compose v2 CLI (`podman compose --project-name ...`). Returns parsed output.

## 2. Image Operations

| Feature | Description |
|---------|-------------|
| `image_rebuild` | Rebuild an image with —no-cache option, show build log streaming |
| `image_history` | Show layer history for an image (size, command, created) |
| `image_inspect` | Deep inspect: env vars, labels, entrypoint, exposed ports, volumes |
| `image_vulnerabilities` | Scan image for known CVEs (Podman Scout or Trivy integration) |
| `image_compare` | Diff two images: layers, env vars, entrypoint differences |

## 3. Container Analysis

| Feature | Description |
|---------|-------------|
| `container_analyze` | Deep container analysis: resource usage trends, restart count, last exit code, log error patterns |
| `container_diagnostics` | Network connectivity test (ping inside container), DNS resolution, port binding check |
| `container_recommend` | Suggest resource limits based on observed memory/cpu usage |
| `container_exec_web` | Web terminal for exec into container (WebSocket) |

## 4. Agentic Workflows (Existing)

Already have `agentic_container_workflow` tool. Enhance:

- **Multi-step compose deploy**: natural language → parse compose → up → health check → rollback on failure
- **Cleanup workflow**: "clean up unused resources" → prune images/volumes/networks in dependency order
- **Diagnose workflow**: "why is my container failing?" → check logs → check exit code → check resources → suggest fix

## 5. Podman-Expert Skill

Create `skills/podman-expert/SKILL.md` with:
- Podman architecture overview (images, containers, volumes, networks, compose)
- Common troubleshooting patterns (OOM, port conflicts, volume permissions)
- Podman Machine on Windows specific notes (named pipes, WSL2, triple kill)
- Example tool sequences for common tasks
- Glossary

Register via FastMCP `SkillsDirectoryProvider`.

## 6. MCPB Packaging

- `manifest.json` at repo root (exists but needs update for 3.3.1)
- `assets/prompts/system.md`, `user.md`, `examples.json` — curated prompts
- `assets/icon.png` — 256x256 Podman-themed icon
- `mcpb pack . dist/podman-mcp.mcpb`
- `.mcpbignore` excludes native/, node_modules/, .venv/, target/

## 7. Chat Page (Full-featured)

| Component | Requirement |
|-----------|-------------|
| **Personalities** | Pre-set personas (Podman Expert, SRE, Beginner) + custom system prompt editor. Switchable mid-conversation. |
| **Prompt refinement** | "Polish prompt" button that prepends Podman context to user queries. Suggested prompts on empty chat. |
| **Memory** | Store conversation history in localStorage + optional export. Context-aware follow-ups. |
| **Export** | Export conversation as Markdown, JSON, or plain text. |
| **Tool call display** | Show MCP tool calls inline with expandable details (params, response, timing). |
| **Streaming** | Stream AI responses token by token. |

## 8. Provider & Model Selection

| Feature | Description |
|---------|-------------|
| **Auto-discovery** | Proper glom: probe Ollama (11434), LM Studio (1234), list models |
| **Provider config** | UI to add/remove/edit providers (base URL, API key, models list) |
| **Model fallback** | If primary model fails, fall back to next available |
| **Per-conversation model** | Pick model per chat message (not just global setting) |
| **Status indicators** | Show online/offline per provider, response time per model |

## Priority Matrix

| Feature | Effort | Impact | Priority |
|---------|--------|--------|----------|
| Chat page (personalities, streaming) | High | High | P1 |
| Provider/model selection | Medium | High | P1 |
| Container compose CRUD | Medium | Medium | P2 |
| Image rebuild + inspect | Low | Medium | P2 |
| Container analysis | Medium | Medium | P2 |
| Podman-expert skill | Low | Medium | P3 |
| Agentic workflow enhancements | Medium | High | P1 |
| MCPB packaging | Low | Low | P3 |

## Implementation Order

1. **Chat page** — full personality + streaming + memory + export
2. **Provider/model selection** — proper glom + model picker per message
3. **Agentic workflow enhancements** — compose deploy, cleanup, diagnose
4. **Compose CRUD** — list, up, down, logs, build, debug
5. **Image rebuild + inspect** — rebuild, history, deep inspect, compare
6. **Container analysis** — analyze, diagnostics, recommend
7. **Podman-expert skill** — SKILL.md + SkillsDirectoryProvider
8. **MCPB packaging** — manifest, prompts, icon, pack
