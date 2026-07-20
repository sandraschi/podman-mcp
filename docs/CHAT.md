# AI Chat & Agentic Workflows

## Chat UI

The `/chat` page provides a conversational interface to Podman.

### Personas

| Persona | Style |
|---------|-------|
| **Podman Expert** | Senior SRE, concise with commands and best practices |
| **SRE** | Reliability-focused: monitoring, resource limits, failure modes |
| **Beginner** | Friendly tutor, explains concepts simply, no jargon |

### Provider Auto-Discovery

On settings panel open, the backend probes:
- **Ollama**: `GET http://127.0.0.1:11434/api/tags`
- **LM Studio**: `GET http://127.0.0.1:1234/v1/models`

Discovered providers show a green (reachable) or red (offline) dot. Model dropdown auto-populates from the selected provider. Manual refresh button forces re-discovery.

### Agentic Tool Mode

Toggle the `Cpu` button in the chat header to enable tool execution mode. The backend:

1. Matches the user query to a Podman tool via keyword patterns
2. Executes the tool (e.g. `list_containers`, `list_images`, `get_system_info`)
3. Streams structured SSE events:
   - `tool_call` — tool name + display name
   - `tool_result` — success/fail, params, result, timing (ms)
   - `text` — LLM response with tool context
   - `done` — stream complete

The frontend renders expandable cards for each tool call with:
- Green checkmark / red X status
- Tool name, parameters, timing
- Result preview (first 1000 chars)

## Agentic Workflows (MCP Tool)

`agentic_workflow` provides four multi-step operations:

### deploy_compose
1. Run `podman compose up` (optionally with `--build`)
2. Wait 3s for services to stabilize
3. Health check each container's state
4. Return healthy/unhealthy counts + rollback suggestion

### cleanup
1. Prune dangling images (`podman image prune -f`)
2. Prune unused volumes (`podman volume prune -f`)
3. Prune unused networks (`podman network prune -f`)

Uses the Podman SDK directly, not CLI subprocess.

### diagnose
1. List all project containers with states
2. Health check each container
3. Fetch last 30 lines of logs
4. Report system resources (CPU, memory, disk via psutil)
5. Return issues list + suggestions

### rollback
1. `podman compose down -v` (stops + removes volumes)
2. Confirm success

## SEP-1577 Sampling

`agentic_container_workflow` uses FastMCP 3.4 `ctx.sample()` for autonomous multi-step orchestration. The LLM plans and executes tool calls without client round-trips. Falls back to structured guidance when sampling is unavailable (no Ollama/LM Studio configured).
