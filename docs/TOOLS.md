# MCP Server

## Quick Config

### Claude Desktop

```json
{
  "mcpServers": {
    "podman-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "D:/Dev/repos/podman-mcp", "python", "-m", "podmanmcp"],
      "env": { "PYTHONPATH": "src" }
    }
  }
}
```

Or install the `.mcpb` bundle: `just mcpb-pack` → drag onto Claude Desktop.

### Cursor

Settings → MCP → Add server:
```
Name: podman-mcp
Type: stdio
Command: uv run --directory D:/Dev/repos/podman-mcp python -m podmanmcp
```

### HTTP (streamable)

```
URL: http://127.0.0.1:10807/mcp
Transport: streamable HTTP (SSE)
```

## Tool Catalog

### Compose

| Tool | Purpose |
|------|---------|
| `compose_operations` | CRUD: list, ps, up, down, logs, build, config, debug |
| `agentic_workflow("deploy_compose")` | Up + health check + rollback suggestion |
| `agentic_workflow("cleanup")` | Prune images/volumes/networks in order |
| `agentic_workflow("diagnose")` | States + logs + system resources + suggestions |
| `agentic_workflow("rollback")` | Down + remove volumes |

### Images

| Tool | Purpose |
|------|---------|
| `list_images` | All images with tags, sizes, OS, arch |
| `pull_image` | Pull from registry |
| `build_image` | Build from Podmanfile |
| `tag_image` | Tag an image |
| `push_image` | Push to registry |
| `prune_images` | Remove dangling (dry-run supported) |
| `search_images` | Podman Hub search |
| `get_image_history` | Layer history |
| `image_compare(a, b)` | Diff layers, env, entrypoint, cmd, ports, labels, workdir, user |

### Containers

| Tool | Purpose |
|------|---------|
| `list_containers` | All containers with states |
| `manage_container` | Create, start, stop, restart, remove |
| `get_container_logs` | Logs with tail/filters |
| `execute_in_container` | Run commands |
| `get_container_stats` | CPU, memory, network, block IO |
| `inspect_container` | Full container config |
| `container_analyze(id)` | Restart count, exit codes, log errors, recommendations |

### Networks, Volumes, System

| Tool | Purpose |
|------|---------|
| `list_networks` / `create_network` / `remove_network` | Network CRUD |
| `list_volumes` / `create_volume` / `remove_volume` / `prune_volumes` | Volume CRUD |
| `get_system_info` | Podman engine info |
| `get_disk_usage` | Podman disk usage |
| `get_container_resources` | Resource limits |

### Backup & Restore

| Tool | Purpose |
|------|---------|
| `podman_backup("save_image")` | Export image(s) to .tar |
| `podman_backup("load_image")` | Import images from .tar |
| `podman_backup("backup_volume")` | Volume data to .tar.gz |
| `podman_backup("restore_volume")` | Restore volume from .tar.gz |
| `podman_backup("export_compose")` | Full project: config + containers + images |

### Podman Machine

| Tool | Purpose |
|------|---------|
| `podman_desktop_status` | Health check + hang detection + auto-recovery |
| `podman_daemon_recover` | Triple-kill Podman Machine + backend + vpnkit |
| `podman_daemon_restart` | Graceful daemon restart |
| `podman_desktop_update` | Fix update elevation errors |

### Agentic / Sampling

| Tool | Purpose | Requires |
|------|---------|----------|
| `agentic_container_workflow` | Autonomous multi-step orchestration via `ctx.sample()` | Sampling-capable client + Ollama/LM Studio |
| `agentic_workflow` | Deterministic multi-step: deploy, cleanup, diagnose, rollback | Nothing (uses Podman SDK directly) |

### Prefab Cards (in-chat rich UI)

| Tool | Content |
|------|---------|
| `podman_containers_card` | Container inventory with total/running badges |
| `podman_images_card` | Image inventory with tagged/total badges |
| `podman_desktop_status_card` | Daemon health with autofix option |
| `podman_system_info_card` | Engine version, CPU cores, memory |

### Web API (REST)

The server also exposes a REST API at `http://127.0.0.1:10807/api` for the web dashboard.
See [ARCHITECTURE.md](ARCHITECTURE.md) for the full endpoint list.

## Prompts

| Prompt | Purpose |
|--------|---------|
| `podman_deploy_stack` | Deploy a multi-container stack with dependency ordering |
| `podman_daemon_health_check` | Daemon diagnostics and recovery workflow |

## Resources

| URI | Content |
|-----|---------|
| `resource://podman-mcp/skills` | When to use podman-mcp, workflow order, ports |
| `resource://podman-mcp/capabilities` | Server capabilities summary |

## Transports

| Mode | Config | When |
|------|--------|------|
| stdio | `command` + `args` in MCP config | Claude Desktop, Cursor |
| HTTP SSE | `url: http://127.0.0.1:10807/mcp` | Remote, browser-based clients |
