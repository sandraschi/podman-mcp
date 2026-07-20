import 'scripts/just/fleet.just'

name := "podman-mcp"
desc := "FastMCP 3.5 server for Podman operations"
ver := "3.5.0"
REPO := justfile_directory()

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ── Build ─

# Sync Python dependencies
build:
    uv sync

# Build webapp
build-webapp:
    cd web_sota && npm install && npm run build

# Tauri native installer (Windows release)
build-native:
    pwsh -NoLogo -File native/build.ps1

build-native-debug:
    Set-Location native
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npx @tauri-apps/cli build --debug

# ── Test ─

# Run test suite
test:
    uv run pytest tests/ -v

# Run tests with coverage
test-cov:
    uv run pytest tests/ --cov=src --cov-report=html

# ── Lint ─

# Run ruff (Python) + biome (webapp)
check:
    uv run ruff check .
    cd web_sota && npx @biomejs/biome ci .

# Auto-fix lint issues
fix:
    uv run ruff check . --fix
    uv run ruff format .
    cd web_sota && npx @biomejs/biome check --write .

# ── Podman ─

# Start the server
run:
    uv run podman-mcp

# Start webapp in dev mode
webapp-dev:
    cd web_sota && npm run dev

# Build Podman image
podman-build:
    podman build -t podman-mcp:latest .

# Podman compose up
up:
    podman compose up -d

# Podman compose down
down:
    podman compose down

# ── Housekeeping ─

# Clean build artifacts
clean:
    Remove-Item -Recurse -Force dist, build, .pytest_cache, .ruff_cache -ErrorAction SilentlyContinue

# View server logs
logs:
    Get-Content logs/podmanmcp.log -Tail 50 -Wait
# ── Playwright E2E ─────────────────────────────────────────────────────

# Install Playwright browsers (one-time)
e2e-install:
    cd {{REPO}}\web_sota
    npx playwright install chromium

# Run Playwright E2E smoke tests (start backend first: just serve)
e2e:
	cd {{REPO}}\web_sota
	npx playwright test

