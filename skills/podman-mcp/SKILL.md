# podman-mcp skill

Use the podman-mcp MCP server whenever the user works with Podman containers,
images, pods, volumes, networks, compose stacks, backups, or Docker-to-Podman
migration on the Goliath Windows host (daemon-less Podman Machine, ports
11112 web / 11113 backend). Prefer it over raw `podman` CLI calls: the tools
validate inputs, return structured JSON, and log every action.

## Tool catalog (15 tools, all dialogic: success + message + data)

Portmanteau tools (one per domain, `operation` discriminator):

- `manage_containers` (12 ops): list, inspect, start, stop, restart, delete,
  create (image, container_name, ports, volumes, env, cmd_args), logs
  (tail_lines), stats, exec (exec_cmd), files (file_op list/read/write,
  container_path, file_content), resources (resource_op get/set, cpu_limit,
  memory_limit)
- `manage_pods` (6): list, inspect, create (pod_name, ports), start, stop, delete
- `manage_images` (6): list, inspect, pull (timeout), delete, build
  (build_tag, build_context), search (search_term)
- `manage_system` (14): status (CLI health gate - call FIRST), info,
  machine_list/init/start/stop, prune, generate_systemd, volume_list/create/delete,
  network_list/create/delete
- `manage_compose` (9): up, down (volumes), ps, logs, build, config, debug.
  Needs `project_path`; `config` before `up` on unfamiliar stacks.
- `manage_backup` (8): save_image, load_image, export_container,
  import_container, save_volume, load_volume, save_compose, list_backups.
  Always back up volumes before migrate/upgrade work.
- `manage_migrate` (9): docker_compose_to_podman, podman_compose_to_docker,
  scan_docker_artifacts, migrate_image (new_name), compatibility_check,
  dockerfile_to_containerfile, export_for_docker
- `manage_agentic` (5, dry_run defaults true): deploy_compose, cleanup,
  diagnose, rollback, health_sweep
- `manage_health` (3): container_analyze (restart loops, OOM, log errors),
  system_overview, recommendations

Cards (Prefab UI, readonly): `podman_containers_card`, `podman_pods_card`,
`podman_machine_status_card`, `podman_images_card`, `podman_system_info_card`.
Utilities: `podman_shutdown` (confirm=true to exit). Prompts:
`podman_deploy_stack` (stack_name), `podman_machine_health_check`.
Resources: `resource://podman-mcp/skills`, `resource://podman-mcp/capabilities`.

## Workflows

1. **Status first**: `manage_system status` before any mutating op. If the
   machine is down, `machine_start` (or the web `/api/podman/recover`).
2. **Compose up**: `config` (resolve) -> `build` (optional) -> `up` ->
   `ps` + `manage_health container_analyze` on failures.
3. **Migration**: `compatibility_check` -> `docker_compose_to_podman` ->
   deploy to a scratch project -> `diagnose`.
4. **Cleanup**: `manage_agentic cleanup` dry_run first, then for real.
5. **Web bridge**: same REST at :11113 (`/api/health`, `/api/skills`,
   `/api/events` for the engine event inbox, `/api/llm/*`, `/api/chat`).

## Gotchas

- Podman Compose lags Docker on `deploy:`/`secrets:`/`configs:` and
  `service_healthy` - `compatibility_check` exists for exactly this.
- `create` needs `image`; most other ops need `container_id`.
- Volume backup paths are Windows paths (`D:/backups/...`) - the server
  translates them for the machine automatically.

## Docker vs Podman (when it matters)

Podman is a daemon-less, OCI-compatible drop-in for most Docker workflows -
same CLI verbs, same image registries (Hub, Quay, ghcr), same compose file
shape. Differences that change tool choice:

| Topic | Docker / Docker Desktop | Podman / Podman Desktop |
|-------|------------------------|-------------------------|
| Daemon | Central `dockerd`; when it wedges, everything hangs until restart | Daemon-less; containers are child processes. No single daemon to wedge (a stuck machine VM is recovered with `machine stop/start`) |
| Privileges | Daemon runs as root (rootless mode is opt-in) | Rootless by default; this server auto-detects it |
| Pods | No native concept (compose is the grouping) | First-class pods (shared net namespace, K8s-like) - use `manage_pods` |
| Kubernetes | Desktop ships a CRI-translated single node | `podman generate kube` / `play kube` speak native K8s YAML; no translation layer |
| Compose | Full spec incl. `deploy:`, `secrets:`, `configs:`, `service_healthy` | `podman-compose` lags exactly there - run `compatibility_check` first |
| Builds | BuildKit (cache mounts, advanced flags) | `podman build` covers the common set; exotic BuildKit syntax may differ |
| Windows containers | Supported (LCOW/Windows) | Linux containers only - needs Docker Desktop instead |
| Registries/catalog | Docker Hub, Scout, Extensions marketplace | Any OCI registry works identically; no Hub lock-in for pulls |
| AI addons | Desktop AI assistant, Gordon | This server's chat + agentic tools against local Ollama/LM Studio cover the same ground with no account |
| Testcontainers | Assumes a Docker socket | Works against the Podman socket in most cases - verify per suite |
| Licensing/cost | Desktop needs a paid subscription for larger companies | Podman + Podman Desktop are free and open source |

Rule of thumb: default to Podman (cheaper to run, easier to recover,
better K8s story); reach for Docker Desktop only for Windows containers,
exotic BuildKit builds, or Testcontainers suites that prove Podman-hostile.
`manage_migrate compatibility_check` answers the compose question per stack.
