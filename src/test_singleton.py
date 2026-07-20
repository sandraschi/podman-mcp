"""
Test script to verify FastMCP singleton behavior.
"""

import sys
import threading
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from podmanmcp.mcp_instance import FastMCPSingleton, get_mcp  # noqa: E402


def test_singleton():
    """Test that only one instance of FastMCP is created."""
    # Get instances in different ways
    mcp1 = get_mcp()
    mcp2 = get_mcp()
    mcp3 = FastMCPSingleton().mcp

    # All should be the same object
    assert mcp1 is mcp2 is mcp3, "Multiple FastMCP instances detected!"

    # Check singleton attributes
    assert hasattr(mcp1, "name"), "FastMCP instance is missing expected attributes"
    assert mcp1.name == "podman-mcp", "Unexpected FastMCP instance name"

    print("✅ Singleton test passed: Only one FastMCP instance exists")


def test_thread_safety():
    """Test that the singleton is thread-safe."""
    instances = []

    def get_instance():
        instances.append(get_mcp())

    # Create multiple threads that try to get the instance
    threads = []
    for _ in range(10):
        t = threading.Thread(target=get_instance)
        threads.append(t)
        t.start()

    # Wait for all threads to complete
    for t in threads:
        t.join()

    # All instances should be the same object
    first = instances[0]
    for instance in instances[1:]:
        assert instance is first, "Thread safety violation: Different instances detected"

    print("✅ Thread safety test passed: Only one instance across threads")


if __name__ == "__main__":
    print("Testing FastMCP singleton implementation...")
    test_singleton()
    test_thread_safety()
    print("\nAll tests passed! 🎉")
