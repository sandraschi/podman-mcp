# Podman Backup & Restore

Podman data is not one monolithic blob. Three distinct layers:

```
Podman Data
├── Images (read-only templates)
│   ├── podman save -o nginx.tar nginx:latest
│   └── podman load -i nginx.tar
├── Volumes (persistent data: DBs, configs, uploads)
│   ├── backup:  alpine tar czf from volume mount
│   └── restore: alpine tar xzf into volume mount
└── Compose Projects (YAML + data)
    └── export: config + container list + images
```

## MCP Tool

`podman_backup` handles all three layers:

| Operation | Input | Output | Size |
|-----------|-------|--------|------|
| `save_image` | image name:tag | .tar file | image size |
| `load_image` | .tar file | registered image | — |
| `backup_volume` | volume name | .tar.gz | volume data |
| `restore_volume` | .tar.gz + volume name | restored volume | — |
| `export_compose` | project name | directory (config + container list + images) | project size |

## Examples

```python
# Export an image
podman_backup("save_image", image="nginx:latest", output_path="C:/backups/nginx.tar")

# Import an image
podman_backup("load_image", input_path="C:/backups/nginx.tar")

# Backup a volume (e.g. postgres data)
podman_backup("backup_volume", volume="postgres_data", output_path="C:/backups/pg_data.tar.gz")

# Restore a volume
podman_backup("restore_volume", volume="postgres_data", input_path="C:/backups/pg_data.tar.gz")

# Full compose project export
podman_backup("export_compose", project="myapp", output_path="C:/backups/myapp-export/")
```
