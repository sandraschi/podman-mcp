"""
Simple test script to verify FastMCP singleton behavior.
"""

import sys
import threading
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import only what we need to test the singleton
from fastmcp import FastMCP  # noqa: E402


class FastMCPSingleton:
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        if not self._initialized:
            self._initialized = True
            print("Initializing FastMCP singleton instance")
            self.mcp = FastMCP(
                name="test-mcp", version="1.0.0", json_response=True, include_fastmcp_meta=False, log_level="CRITICAL"
            )
            print("FastMCP instance created")


def test_singleton():
    """Test that only one instance of FastMCP is created."""
    # Create singleton instances in different ways
    singleton1 = FastMCPSingleton()
    singleton2 = FastMCPSingleton()
    mcp1 = singleton1.mcp
    mcp2 = singleton2.mcp

    # All should be the same object
    assert singleton1 is singleton2, "Multiple singleton instances detected!"
    assert mcp1 is mcp2, "Multiple FastMCP instances detected!"

    # Check instance attributes
    assert hasattr(mcp1, "name"), "FastMCP instance is missing expected attributes"
    assert mcp1.name == "test-mcp", "Unexpected FastMCP instance name"

    print("✅ Singleton test passed: Only one FastMCP instance exists")


def test_thread_safety():
    """Test that the singleton is thread-safe."""
    instances = []

    def get_instance():
        singleton = FastMCPSingleton()
        instances.append(singleton.mcp)

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
