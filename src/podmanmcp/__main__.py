"""
Podman MCP Server - ``python -m podmanmcp`` entry point.

Delegates to podmanmcp.server.main (stdio transport plus the web bridge), the
same entry the MCPB manifest and the podman-mcp console script use. The previous
body (copied from docker-mcp) imported the tools and then idled in a
``while not should_exit: sleep`` loop without ever starting a transport, so this
entry never answered ``initialize``.
"""

import sys

from podmanmcp.server import main

if __name__ == "__main__":
    sys.exit(main())
