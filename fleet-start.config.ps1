# Per-repo fleet start config for podman-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'podman-mcp'
    BackendPort  = 11113
    FrontendPort = 11112
    HealthPath   = '/api/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'customization.server:app'
        SyncExtras    = @('dev')
        Env           = @{
            WEB_PORT   = '11113'
            PODMAN_CMD = "$env:LOCALAPPDATA\Programs\Podman\podman.exe"
        }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
