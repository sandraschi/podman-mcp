"""
Mock MCP Server for testing Podman MCP functionality.

This module provides a mock implementation of the MCP server that simulates
real server behavior for testing purposes.
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MockMCPServer")


class MockMCPRequestHandler(BaseHTTPRequestHandler):
    """Request handler for the mock MCP server."""

    def __init__(self, *args, **kwargs):
        self.routes = {
            "GET": {
                "/health": self.handle_health_check,
                "/containers": self.handle_list_containers,
                "/containers/.*/logs": self.handle_container_logs,
                "/images": self.handle_list_images,
            },
            "POST": {
                "/containers/.*/start": self.handle_start_container,
                "/containers/.*/stop": self.handle_stop_container,
                "/containers/.*/restart": self.handle_restart_container,
                "/images/pull": self.handle_pull_image,
            },
            "DELETE": {
                "/containers/.*": self.handle_remove_container,
                "/images/.*": self.handle_remove_image,
            },
        }
        # In-memory storage for mock data
        self.containers = {}
        self.images = [
            {"Id": "sha256:abc123", "RepoTags": ["alpine:latest"], "Size": 12345678},
            {"Id": "sha256:def456", "RepoTags": ["ubuntu:20.04"], "Size": 98765432},
        ]
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger.info("%s - %s", self.address_string(), format % args)

    def do_GET(self):
        """Handle GET requests."""
        self._handle_request("GET")

    def do_POST(self):
        """Handle POST requests."""
        self._handle_request("POST")

    def do_DELETE(self):
        """Handle DELETE requests."""
        self._handle_request("DELETE")

    def _handle_request(self, method: str):
        """Route the request to the appropriate handler."""
        path = self.path.split("?")[0]  # Remove query params

        # Try to find a matching route
        for route_pattern, handler in self.routes.get(method, {}).items():
            if self._path_matches(route_pattern, path):
                handler()
                return

        # No matching route found
        self.send_response(404)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": f"No route found for {method} {path}", "error": "Not Found"}).encode())

    def _path_matches(self, pattern: str, path: str) -> bool:
        """Check if a path matches a route pattern with wildcards."""
        import re

        # Convert route pattern to regex
        regex = pattern.replace(".*", "[^/]+")
        return bool(re.fullmatch(regex, path))

    def _get_path_param(self, pattern: str, path: str) -> str | None:
        """Extract a parameter from the path based on the pattern."""
        import re

        # Convert pattern to regex and extract the parameter
        regex = pattern.replace(".*", "([^/]+)")
        match = re.fullmatch(regex, path)
        return match.group(1) if match else None

    def _read_json_body(self) -> dict[str, Any]:
        """Read and parse JSON request body."""
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}

        body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}

    def _send_json_response(self, status_code: int, data: Any):
        """Send a JSON response with the given status code."""
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    # Request handlers for different endpoints
    def handle_health_check(self):
        """Handle health check endpoint."""
        self._send_json_response(200, {"status": "ok", "version": "1.0.0"})

    def handle_list_containers(self):
        """Handle listing containers."""
        all_containers = list(self.containers.values())
        self._send_json_response(200, all_containers)

    def handle_container_logs(self):
        """Handle getting container logs."""
        container_id = self._get_path_param("/containers/.*/logs", self.path)
        container = self.containers.get(container_id)

        if not container:
            self._send_json_response(404, {"message": f"No such container: {container_id}", "error": "Not Found"})
            return

        # Return mock logs
        logs = f"Mock logs for container {container_id}\n"
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(logs.encode())

    def handle_start_container(self):
        """Handle starting a container."""
        container_id = self._get_path_param("/containers/.*/start", self.path)
        container = self.containers.get(container_id)

        if not container:
            self._send_json_response(404, {"message": f"No such container: {container_id}", "error": "Not Found"})
            return

        # Update container status
        container["State"] = {"Status": "running", "Running": True}
        self._send_json_response(204, {})

    def handle_stop_container(self):
        """Handle stopping a container."""
        container_id = self._get_path_param("/containers/.*/stop", self.path)
        container = self.containers.get(container_id)

        if not container:
            self._send_json_response(404, {"message": f"No such container: {container_id}", "error": "Not Found"})
            return

        # Update container status
        container["State"] = {"Status": "exited", "Running": False}
        self._send_json_response(204, {})

    def handle_restart_container(self):
        """Handle restarting a container."""
        # For simplicity, just call stop and start
        self.handle_stop_container()
        self.handle_start_container()

    def handle_remove_container(self):
        """Handle removing a container."""
        container_id = self._get_path_param("/containers/.*", self.path)

        if container_id in self.containers:
            del self.containers[container_id]
            self._send_json_response(204, {})
        else:
            self._send_json_response(404, {"message": f"No such container: {container_id}", "error": "Not Found"})

    def handle_list_images(self):
        """Handle listing images."""
        self._send_json_response(200, self.images)

    def handle_pull_image(self):
        """Handle pulling an image."""
        body = self._read_json_body()
        image_name = body.get("fromImage", "")

        if not image_name:
            self._send_json_response(400, {"message": "Missing required parameter: fromImage", "error": "Bad Request"})
            return

        # Simulate image pull by adding a new image
        new_image = {
            "Id": f"sha256:{abs(hash(image_name)):x}",
            "RepoTags": [image_name],
            "Size": 12345678,  # Default size
        }
        self.images.append(new_image)

        self._send_json_response(200, new_image)

    def handle_remove_image(self):
        """Handle removing an image."""
        image_id = self._get_path_param("/images/.*", self.path)

        # Find and remove the image
        for i, img in enumerate(self.images):
            if img["Id"] == image_id or any(tag.startswith(image_id) for tag in img.get("RepoTags", [])):
                self.images.pop(i)
                self._send_json_response(200, {"message": "Image removed"})
                return

        self._send_json_response(404, {"message": f"No such image: {image_id}", "error": "Not Found"})


class MockMCPServer:
    """A mock MCP server for testing."""

    def __init__(self, host="localhost", port=8000):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        """Start the mock server in a separate thread."""

        def run():
            self.server = HTTPServer((self.host, self.port), MockMCPRequestHandler)
            logger.info(f"Starting mock MCP server on {self.host}:{self.port}")
            self.server.serve_forever()

        self.thread = threading.Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop the mock server."""
        if self.server:
            logger.info("Stopping mock MCP server")
            self.server.shutdown()
            self.server.server_close()
            self.server = None

        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


if __name__ == "__main__":
    # Run the mock server if this script is executed directly
    server = MockMCPServer()
    try:
        print("Starting mock MCP server on http://localhost:8000")
        print("Press Ctrl+C to stop")
        server.start()
        while True:
            # Keep the main thread alive
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping mock MCP server...")
        server.stop()
