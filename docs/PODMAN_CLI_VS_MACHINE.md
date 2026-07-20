# Podman Daemon vs Podman Machine GUI

This document explains the difference between the Podman CLI and Podman Machine GUI, and how the application handles each scenario.

## Key Concepts

### Podman Daemon
- The Podman CLI (`podmand`) is the background service that manages Podman objects like containers, images, networks, and volumes.
- It's the core component that performs the actual work when you run Podman commands.
- The daemon can run without the Podman Machine GUI.

### Podman Machine GUI
- Podman Machine provides a graphical user interface for managing Podman.
- It includes the Podman CLI, Podman CLI client, and additional tools.
- The GUI is optional for the Podman CLI to function.

## Application Behavior

The application is designed to work in both scenarios:

1. **Podman Daemon Only**
   - The application will function normally as long as the Podman CLI is running.
   - All Podman operations (container management, image handling, etc.) will work as expected.
   - The application doesn't require the Podman Machine GUI to be running.

2. **Podman Machine GUI Running**
   - The application will work the same as with just the daemon.
   - Users can use either the application or the GUI to manage Podman resources.

3. **Neither Daemon Nor GUI Running**
   - The application will detect that Podman is not available.
   - Graceful error messages will be shown to the user.
   - The application will suggest starting Podman Machine or the Podman service.

## Troubleshooting

### Podman Daemon Not Starting
If the Podman CLI is not starting:

1. On Windows:
   ```powershell
   # Start the Podman service
   Start-Service com.podman.service
   
   # Or restart Podman Machine
   & 'C:\Program Files\Podman\Podman\Podman Machine.exe'
   ```

2. On Linux:
   ```bash
   # Start the Podman service
   sudo systemctl start podman
   
   # Enable it to start on boot
   sudo systemctl enable podman
   ```

### Checking Podman Status
You can check if the Podman CLI is running with:

```bash
podman info
# or
podman ps
```

## Best Practices

1. **For Servers/Production**
   - Only the Podman CLI is needed.
   - The GUI is not required and should not be installed.

2. **For Development**
   - Podman Machine with GUI is recommended for easier management.
   - The application will work the same regardless of whether the GUI is running.

3. **For CI/CD Pipelines**
   - Only the Podman CLI is needed.
   - The application will work in headless environments.
