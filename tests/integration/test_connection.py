"""
Test script to verify Podman connection handling.
"""

import asyncio
import logging
import sys
from pathlib import Path

import podman

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def test_podman_connection():
    """Test the Podman connection handling."""
    try:
        # Try to connect to Podman
        client = podman.from_env()
        client.ping()
        print("✅ Podman is running")
        return True
    except Exception as e:
        print(f"❌ Podman is not available: {e!s}")
        return False


if __name__ == "__main__":
    # Run the test
    print("Testing Podman connection...")
    connected = asyncio.run(test_podman_connection())

    if connected:
        print("\nTo test Podman down scenarios:")
        print("1. Stop Podman Machine")
        print("2. Run this script again")
    else:
        print("\n✅ Test successful! The script correctly detected that Podman is not running.")
        print("\nTo complete testing:")
        print("1. Start Podman Machine")
        print("2. Run this script again to verify it detects when Podman is running")
