# Compose Management

## Web Dashboard

The `/compose` page provides:

- **Project list**: All compose projects with running/stopped indicators
- **Per-project view**: Container states, service names, ports
- **Controls**: Up/Down buttons for each project
- **Config viewer**: Rendered `podman-compose.yml`
- **Logs**: Last N lines per project
- **File analysis**: Load any `podman-compose.yml` from disk

### File Picker

Two modes for loading external compose files:

| Mode | How | Where |
|------|-----|-------|
| **Tauri dialog** | `@tauri-apps/plugin-dialog` `open()` | Installed NSIS app |
| **Browser fallback** | `<input type="file">` | Dev mode (`npm run dev`) |
| **Manual path** | Text input + Analyze button | Both |

The file is parsed on the backend by `compose_analysis.py`, which extracts:

- Services (name, image, build context, ports, volumes, depends_on, env keys, restart policy, healthchecks)
- Volumes (name, driver)
- Networks (name, driver)
- Summary: image list, port list, build context detection, dependency graph detection

## MCP Tool

`compose_operations` provides full CRUD:

| Operation | Purpose |
|-----------|---------|
| `list` | All compose projects (running or all) |
| `ps` | Container states for a project |
| `up` | Start services (detach, build flags) |
| `down` | Stop services (remove volumes flag) |
| `logs` | Fetch logs per service or project |
| `build` | Rebuild service images (no-cache flag) |
| `config` | Validate and render YAML |
| `debug` | Inspect states, exit codes, port conflicts |

## REST API

| Endpoint | Method | Body |
|----------|--------|------|
| `/api/compose/projects` | GET | `?all=true` |
| `/api/compose/ps` | GET | `?project=name` |
| `/api/compose/up` | POST | `{"project":"name", "build":false}` |
| `/api/compose/down` | POST | `{"project":"name", "volumes":false}` |
| `/api/compose/logs` | GET | `?project=name&tail=50` |
| `/api/compose/config` | GET | `?project=name` |
| `/api/compose/analyze` | POST | `{"file_path":"C:/podman-compose.yml"}` |
