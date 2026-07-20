# MCPJam Integration for Podman MCP

This guide explains how to set up and use MCPJam with the Podman MCP server for development and testing.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   npm install -g @mcpjam/inspector
   ```

2. **Start the MCPJam Inspector**
   ```bash
   .\test-mcpjam.bat
   ```
   Or on Unix-like systems:
   ```bash
   PYTHONPATH=. npx @mcpjam/inspector@latest --port 8720 --config mcp_config.json
   ```

3. **Access the MCPJam UI**
   Open your browser to: http://localhost:8720

## 📋 Configuration

The MCPJam configuration is stored in `mcp_config.json`:

```json
{
  "command": "python",
  "args": ["-m", "podmanmcp.server"],
  "cwd": ".",
  "env": {
    "PYTHONPATH": "."
  },
  "mcp": {
    "name": "podman-mcp",
    "version": "0.1.0"
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8720
  }
}
```

## 🛠 Development Workflow

### Running with MCPJam

1. Start the MCPJam inspector using the provided script:
   ```bash
   .\test-mcpjam.bat
   ```

2. The server will be available at http://localhost:8720

### Running Directly

You can also run the server directly for development:

```bash
python -m podmanmcp.server --http
```

This will start the server with HTTP interface on port 8000.

## 🧪 Testing

To run tests with MCPJam:

```bash
pytest tests/unit/tools/test_container_lifecycle.py -v
```

## 🔄 Updating MCPJam

To update the MCPJam inspector:

```bash
npm update -g @mcpjam/inspector
```

## 📚 Additional Resources

- [MCPJam Documentation](https://github.com/modelcontextprotocol/mcpjam)
- [FastMCP Documentation](https://fastmcp.readthedocs.io/)
- [Model Context Protocol](https://github.com/modelcontextprotocol/spec)
