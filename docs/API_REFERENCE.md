# PodmanMCP API Reference

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Endpoints (REST API)](#endpoints-rest-api)
   - [Container Management](#container-management)
   - [Image Management](#image-management)
   - [Network Management](#network-management)
   - [Volume Management](#volume-management)
   - [System Management](#system-management)
   - [Workflow Management](#workflow-management)
4. [MCP Tools](#mcp-tools)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Examples](#examples)

## Introduction

PodmanMCP provides a RESTful API for managing Podman containers, images, networks, volumes, and system resources. This document describes the API endpoints, request/response formats, and usage examples.

## Authentication

All API endpoints require authentication using API keys. Include your API key in the `X-API-Key` header with each request.

```http
GET /api/containers
X-API-Key: your-api-key-here
```

## Endpoints (REST API)

### Compose Management

#### List Compose Projects

```http
GET /api/compose/projects?all=true
```

Returns all Podman Compose projects known to the Podman CLI.

#### Compose PS

```http
GET /api/compose/ps?project=myapp
```

List containers for a compose project.

#### Compose Up

```http
POST /api/compose/up
Content-Type: application/json

{"project": "myapp", "build": false, "detach": true}
```

Start compose services.

#### Compose Down

```http
POST /api/compose/down
Content-Type: application/json

{"project": "myapp", "volumes": false}
```

Stop and remove compose services.

#### Compose Logs

```http
GET /api/compose/logs?project=myapp&tail=50
```

Fetch logs for a compose project.

#### Compose Config

```http
GET /api/compose/config?project=myapp
```

Render and validate compose configuration.

#### Analyze Compose File

```http
POST /api/compose/analyze
Content-Type: application/json

{"file_path": "C:/project/podman-compose.yml"}
```

Parse and analyze a podman-compose YAML file. Returns services, images, volumes, networks, ports, dependencies, build contexts, and healthcheck info.

### Container Management

#### List Containers

```http
GET /api/containers
```

**Query Parameters:**
- `all` (boolean): Show all containers (default: `false`)
- `limit` (integer): Maximum number of containers to return
- `filters` (JSON): Filter containers

**Example Response:**

```json
{
  "status": "success",
  "containers": [
    {
      "id": "a1b2c3d4",
      "name": "web-app",
      "image": "nginx:latest",
      "status": "running",
      "ports": ["80/tcp"],
      "created": "2023-01-01T12:00:00Z"
    }
  ]
}
```

#### Create Container

```http
POST /api/containers
```

**Request Body:**

```json
{
  "image": "nginx:latest",
  "name": "web-app",
  "ports": {"80/tcp": 8080},
  "environment": {"DEBUG": "true"},
  "volumes": {"/host/path": "/container/path"}
}
```

**Response:**

```json
{
  "status": "success",
  "container_id": "a1b2c3d4",
  "warnings": []
}
```

### Image Management

#### List Images

```http
GET /api/images
```

**Query Parameters:**

- `all` (boolean): Show all images (default: `false`)
- `filters` (JSON): Filter images

**Example Response:**

```json
{
  "status": "success",
  "images": [
    {
      "id": "sha256:abc123",
      "tags": ["nginx:latest"],
      "size": 1337000000,
      "created": "2023-01-01T12:00:00Z"
    }
  ]
}
```

### Network Management

#### List Networks

```http
GET /api/networks
```

**Example Response:**

```json
{
  "status": "success",
  "networks": [
    {
      "id": "net1",
      "name": "bridge",
      "driver": "bridge",
      "scope": "local",
      "ipam": {"Driver": "default"}
    }
  ]
}
```

### Volume Management

#### List Volumes

```http
GET /api/volumes
```

**Example Response:**

```json
{
  "status": "success",
  "volumes": [
    {
      "name": "my-volume",
      "driver": "local",
      "mountpoint": "/var/lib/podman/volumes/my-volume/_data",
      "size": 10485760
    }
  ]
}
```

### System Management

#### System Info

```http
GET /api/system/info
```

**Example Response:**

```json
{
  "status": "success",
  "info": {
    "podman_version": "20.10.7",
    "os": "linux",
    "architecture": "x86_64",
    "containers_running": 5,
    "containers_stopped": 2,
    "images": 15,
    "n_cpu": 4,
    "mem_total": 17179869184
  }
}
```

### Workflow Management

#### Create Workflow

```http
POST /api/workflows
```

**Request Body:**
```json
{
  "name": "web-app",
  "services": {
    "web": {
      "image": "nginx:latest",
      "ports": {"80": "8080"}
    },
    "db": {
      "image": "postgres:13",
      "environment": {"POSTGRES_PASSWORD": "example"}
    }
  }
}
```

**Response:**

```json
{
  "status": "success",
  "workflow_id": "workflow_1234567890",
  "message": "Workflow created successfully"
}
```

## MCP Tools

PodmanMCP provides a set of high-level tools via the Model Context Protocol (MCP). These tools are the primary interface for AI agents (like Claude or Gemini) to interact with the Podman CLI.

### Tool Registry

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `list_containers` | List Podman containers with optional filtering. | `all` (bool), `limit` (int), `filters` (dict) |
| `container_management` | Perform lifecycle operations on containers (start, stop, etc.). | `action` (str), `container_id` (str), `**kwargs` |
| `network_management` | Manage Podman networks. | `action` (str), `name` (str), `**kwargs` |
| `volume_management` | Manage Podman volumes. | `action` (str), `name` (str), `**kwargs` |
| `system_management` | Get Podman system information and disk usage. | `action` (str), `**kwargs` |
| `podman_desktop_status` | [Windows] Check status of Podman Machine and daemon. | `refresh` (bool) |
| `podman_daemon_recover` | [Windows] Attempt to recover a hung Podman CLI. | `force` (bool) |
| `agentic_container_workflow` | [SEP-1577] Execute complex multi-step container goals. | `goal` (str) |

### Contextual Discovery

Agents can discover available tools using the `list_tools` operation defined in the MCP specification. Each tool returns a standardized dictionary with `status`, `data`, and optional `message` fields.

---

## Error Handling

All error responses follow this format:

```json
{
  "status": "error",
  "error": "Error message describing what went wrong",
  "code": "ERROR_CODE"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid request format or parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 404 | Not Found - The requested resource was not found |
| 409 | Conflict - Resource already exists or operation not possible |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error - Something went wrong on our end |

## Rate Limiting

API requests are rate limited to 1000 requests per hour per API key. The following headers are included in rate-limited responses:

- `X-RateLimit-Limit`: The maximum number of requests allowed per hour
- `X-RateLimit-Remaining`: The number of requests remaining in the current rate limit window
- `X-RateLimit-Reset`: The time at which the current rate limit window resets (Unix timestamp)

## Examples

### Using cURL

```bash
# List running containers
curl -X GET "http://localhost:8000/api/containers" \
  -H "X-API-Key: your-api-key"

# Create a new container
curl -X POST "http://localhost:8000/api/containers" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"image":"nginx:latest", "name":"web-app"}'
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api"
HEADERS = {"X-API-Key": "your-api-key"}

# List containers
response = requests.get(f"{BASE_URL}/containers", headers=HEADERS)
print(response.json())

# Create a container
data = {
    "image": "nginx:latest",
    "name": "web-app",
    "ports": {"80/tcp": 8080}
}
response = requests.post(
    f"{BASE_URL}/containers",
    json=data,
    headers={"Content-Type": "application/json", **HEADERS}
)
print(response.json())
```
