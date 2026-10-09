"""
Test core Podman functionality without FastMCP dependencies.
"""

import asyncio
import sys

import podman
import pytest


def test_podman_operations():
    """Exercise ping/version/list against a live Podman API; skip when unreachable."""
    try:
        podman.from_env().ping()
    except Exception as e:
        pytest.skip(f"Podman API not reachable via podman.from_env(): {e!s}")
    success, message = asyncio.run(check_podman_operations())
    assert success, message


async def check_podman_operations():
    """Run basic Podman operations; return (success, message)."""
    try:
        # Initialize Podman client
        client = podman.from_env()

        # Test connection
        print("\n=== Testing Podman Connection ===")
        client.ping()
        print("✅ Successfully connected to Podman CLI")

        # Get Podman version
        version = client.version()
        print(f"Podman Version: {version.get('Version', 'Unknown')}")
        print(f"API Version: {version.get('ApiVersion', 'Unknown')}")

        # List containers
        print("\n=== Listing Containers ===")
        containers = client.containers.list(all=True, limit=5)
        print(f"Found {len(containers)} containers")
        for i, container in enumerate(containers, 1):
            print(f"{i}. {container.name} ({container.status})")

        # List images (first 3)
        print("\n=== Listing Images (first 3) ===")
        images = client.images.list()
        print(f"Found {len(images)} total images")
        for i, image in enumerate(images[:3], 1):  # Show first 3 images
            print(f"{i}. {image.tags[0] if image.tags else 'untagged'}")

        return True, "✅ All Podman operations completed successfully"

    except (podman.errors.PodmanError, podman.errors.APIError) as e:
        return False, f"❌ Podman error: {e!s}"
    except Exception as e:
        return False, f"❌ Unexpected error: {e!s}"


if __name__ == "__main__":
    print("Testing core Podman functionality...")

    try:
        success, message = asyncio.run(check_podman_operations())
        print(f"\n{message}")

        if success:
            print("\n✅ Test successful! Core Podman functionality is working correctly.")
            print("This confirms that the Podman CLI is operational.")
        else:
            print("\n❌ Test failed. There was an issue with Podman functionality.")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e!s}")
        sys.exit(1)
